"""
Asynchronous Bluetooth Low Energy (BLE) Manager for MagicLantern / Neon Lights
Runs an asyncio event loop in a dedicated background daemon thread.
Guarantees reliable sequential delivery of all discrete commands (Power, Modes, Speeds)
while supporting high-frequency non-blocking streaming for Audio & Scene animations.
"""

import asyncio
import logging
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple
from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .protocol import (
    SERVICE_UUID,
    WRITE_CHAR_UUID,
    NOTIFY_CHAR_UUID,
    NAME_FILTER_PREFIXES,
    make_power_packet,
    make_color_packet,
    make_brightness_packet,
    make_speed_packet,
    make_mode_packet,
    make_scene_packet,
    make_cct_packet,
    make_external_mic_power_packet,
    make_external_mic_sensitivity_packet,
    make_external_mic_eq_packet,
    make_pin_sequence_packet,
    make_symphony_points_packet,
    make_music_color_packet,
    make_system_time_packet,
    make_timing_status_packet,
)

logger = logging.getLogger("BLEManager")


class BLEManager:
    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._client: Optional[BleakClient] = None
        self._connected = False
        self._current_device: Optional[BLEDevice] = None
        self._current_address: Optional[str] = None
        self._auto_reconnect = True
        self._stop_event = threading.Event()
        self._loop_ready_event = threading.Event()

        # Callbacks for UI updates
        self.on_connection_changed: Optional[Callable[[bool, Optional[str]], None]] = None
        self.on_scan_found: Optional[Callable[[str, str, int], None]] = None
        self.on_scan_finished: Optional[Callable[[List[Tuple[str, str, int]]], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_packet_sent: Optional[Callable[[bytes], None]] = None

        # Command Queue for discrete packets (Power, Mode, Speed, Brightness, Config)
        # Guarantees FIFO in-order delivery without packet drops.
        self._cmd_queue: Optional[asyncio.Queue] = None

        # Dedicated slot for high-frequency streaming frames (Audio reactive / Scene engine).
        # Replaced on each frame to prevent backlog, sent only when command queue is idle.
        self._stream_frame: Optional[bytes] = None

        self._start_thread()

    def _start_thread(self):
        self._thread = threading.Thread(target=self._run_loop, name="BLE-Loop-Thread", daemon=True)
        self._thread.start()
        # Wait up to 3 seconds for loop initialization
        self._loop_ready_event.wait(timeout=3.0)

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._cmd_queue = asyncio.Queue()
        self._loop_ready_event.set()
        self._loop.create_task(self._packet_sender_worker())
        try:
            self._loop.run_forever()
        finally:
            self._loop.close()

    async def _packet_sender_worker(self):
        """
        Worker that sends packets with rate-limiting to prevent BLE link congestion.
        Prioritizes discrete commands from _cmd_queue so modes/power/speed are NEVER dropped,
        then sends latest streaming frame if available.
        """
        last_send_time = 0.0
        min_cmd_interval = 0.025  # ~25ms between discrete commands
        min_stream_interval = 0.035  # ~28 fps for streaming color frames

        while not self._stop_event.is_set():
            try:
                # 1. Process discrete command if available (highest priority, guaranteed delivery)
                if self._cmd_queue and not self._cmd_queue.empty():
                    packet = await self._cmd_queue.get()
                    if self._client and self._client.is_connected:
                        elapsed = time.time() - last_send_time
                        if elapsed < min_cmd_interval:
                            await asyncio.sleep(min_cmd_interval - elapsed)
                        try:
                            await self._client.write_gatt_char(WRITE_CHAR_UUID, packet, response=False)
                            last_send_time = time.time()
                            if self.on_packet_sent:
                                self.on_packet_sent(packet)
                        except Exception as e:
                            logger.error(f"Failed to write command packet: {e}")
                    continue

                # 2. Process streaming frame if available
                if self._stream_frame is not None:
                    packet = self._stream_frame
                    self._stream_frame = None
                    if self._client and self._client.is_connected:
                        elapsed = time.time() - last_send_time
                        if elapsed < min_stream_interval:
                            await asyncio.sleep(min_stream_interval - elapsed)
                        try:
                            await self._client.write_gatt_char(WRITE_CHAR_UUID, packet, response=False)
                            last_send_time = time.time()
                            if self.on_packet_sent:
                                self.on_packet_sent(packet)
                        except Exception as e:
                            logger.debug(f"Failed to write stream packet: {e}")
                    continue

                # Idle sleep
                await asyncio.sleep(0.01)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in packet worker: {e}")
                await asyncio.sleep(0.05)

    def is_connected(self) -> bool:
        return self._connected and self._client is not None and self._client.is_connected

    def get_current_address(self) -> Optional[str]:
        return self._current_address

    def scan(self, timeout: float = 4.0):
        """Trigger scan asynchronously."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._async_scan(timeout), self._loop)

    async def _async_scan(self, timeout: float):
        found_devices: Dict[str, Tuple[str, str, int]] = {}

        def detection_callback(device: BLEDevice, adv: AdvertisementData):
            name = device.name or adv.local_name or "Unknown Device"
            rssi = adv.rssi
            found_devices[device.address] = (name, device.address, rssi)
            if self.on_scan_found:
                self.on_scan_found(name, device.address, rssi)

        try:
            scanner = BleakScanner(detection_callback=detection_callback)
            await scanner.start()
            await asyncio.sleep(timeout)
            await scanner.stop()
        except Exception as e:
            logger.error(f"Scan error: {e}")
            if self.on_error:
                self.on_error(f"Bluetooth scan failed: {e}")

        result_list = list(found_devices.values())
        # Sort so MELK/ELK devices appear at top, then by RSSI descending
        def sort_key(item):
            name, addr, rssi = item
            is_melk = any(name.startswith(p) for p in NAME_FILTER_PREFIXES)
            return (0 if is_melk else 1, -rssi)

        result_list.sort(key=sort_key)
        if self.on_scan_finished:
            self.on_scan_finished(result_list)

    def connect(self, address: str):
        """Connect to device address asynchronously."""
        self._current_address = address
        self._auto_reconnect = True
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._async_connect(address), self._loop)

    def connect_device(self, address: str):
        """Alias for connect() for API compatibility."""
        self.connect(address)

    async def _async_connect(self, address: str):
        if self._client and self._client.is_connected:
            await self._async_disconnect()

        logger.info(f"Connecting to {address}...")
        
        def disconnected_callback(client: BleakClient):
            logger.info("Device disconnected unexpectedly.")
            self._connected = False
            if self.on_connection_changed:
                self.on_connection_changed(False, None)
            if self._auto_reconnect and not self._stop_event.is_set():
                asyncio.create_task(self._attempt_reconnect())

        try:
            client = BleakClient(address, disconnected_callback=disconnected_callback)
            await client.connect(timeout=10.0)
            if client.is_connected:
                self._client = client
                self._connected = True
                self._current_address = address
                logger.info("Connected successfully.")

                # Initialization sequence: Power ON, configure 100 IC pixels, default brightness
                try:
                    await client.write_gatt_char(WRITE_CHAR_UUID, make_power_packet(True), response=False)
                    await asyncio.sleep(0.04)
                    await client.write_gatt_char(WRITE_CHAR_UUID, make_symphony_points_packet(100), response=False)
                    await asyncio.sleep(0.04)
                    await client.write_gatt_char(WRITE_CHAR_UUID, make_brightness_packet(100), response=False)
                    await asyncio.sleep(0.04)
                    await client.write_gatt_char(WRITE_CHAR_UUID, make_speed_packet(80), response=False)
                except Exception as ex:
                    logger.debug(f"Init sequence error: {ex}")

                if self.on_connection_changed:
                    self.on_connection_changed(True, address)
                return
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._connected = False
            if self.on_error:
                self.on_error(f"Could not connect to {address}: {e}")
            if self.on_connection_changed:
                self.on_connection_changed(False, None)

    async def _attempt_reconnect(self):
        if not self._current_address or self._stop_event.is_set():
            return
        logger.info("Attempting auto-reconnect in 2 seconds...")
        await asyncio.sleep(2.0)
        if not self._connected and self._current_address:
            await self._async_connect(self._current_address)

    def disconnect(self):
        """Disconnect current device."""
        self._auto_reconnect = False
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._async_disconnect(), self._loop)

    async def _async_disconnect(self):
        if self._client:
            try:
                await self._client.disconnect()
            except Exception as e:
                logger.debug(f"Disconnect error: {e}")
            finally:
                self._client = None
                self._connected = False
                if self.on_connection_changed:
                    self.on_connection_changed(False, None)

    def send_packet(self, packet: bytes):
        """Thread-safe enqueue discrete packet with guaranteed FIFO delivery."""
        if not self.is_connected():
            return
        if self._cmd_queue and self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._cmd_queue.put_nowait, packet)

    def send_stream_frame(self, r: int, g: int, b: int, use_music_opcode: bool = False):
        """
        Thread-safe send streaming color update (for Audio reactive & Scene animations).
        Non-blocking: holds the single latest frame so it never lags the connection.
        """
        if not self.is_connected():
            return
        if use_music_opcode:
            self._stream_frame = make_music_color_packet(r, g, b)
        else:
            self._stream_frame = make_color_packet(r, g, b)

    def clear_stream(self):
        """Discard any pending streaming frame immediately."""
        self._stream_frame = None

    # High-level controls
    def set_power(self, on: bool):
        self.clear_stream()
        if not on:
            # Disarm hardware mic first so room sound doesn't trigger microcontroller wake-up
            self.send_packet(make_external_mic_power_packet(False))
            self.send_packet(make_color_packet(0, 0, 0))
        self.send_packet(make_power_packet(on))

    def set_color(self, r: int, g: int, b: int):
        self.clear_stream()
        self.send_packet(make_color_packet(r, g, b))

    def set_music_color(self, r: int, g: int, b: int):
        self.send_stream_frame(r, g, b, use_music_opcode=True)

    def disarm_external_mic(self, fallback_r: int = 0, fallback_g: int = 240, fallback_b: int = 255):
        """
        Completely disarms the physical USB controller mic and releases the microcontroller
        from the sound-listening loop by sending Mic OFF + Static Color.
        """
        self.clear_stream()
        self.send_packet(make_external_mic_power_packet(False))
        self.send_packet(make_color_packet(fallback_r, fallback_g, fallback_b))

    def set_brightness(self, level: int):
        self.send_packet(make_brightness_packet(level))

    def set_speed(self, speed: int):
        self.send_packet(make_speed_packet(speed))

    def set_mode(self, mode_id: int):
        """
        Selects dynamic mode.
        Clears streaming frames to prevent color packets from canceling the dynamic mode.
        """
        self.clear_stream()
        self.send_packet(make_power_packet(True))
        self.send_packet(make_mode_packet(mode_id))

    def set_scene(self, scene_id: int):
        """
        Sends hardware scene opcode 0x31 (supported on MELK-OC/OT devices).
        """
        self.clear_stream()
        self.send_packet(make_power_packet(True))
        self.send_packet(make_scene_packet(scene_id))

    def set_cct(self, warm: int, cold: int):
        self.clear_stream()
        self.send_packet(make_cct_packet(warm, cold))

    def set_external_mic_power(self, on: bool):
        self.send_packet(make_external_mic_power_packet(on))

    def set_external_mic_sensitivity(self, sensitivity: int):
        self.send_packet(make_external_mic_sensitivity_packet(sensitivity))

    def set_external_mic_eq(self, eq_mode: int):
        self.send_packet(make_external_mic_eq_packet(eq_mode))

    def set_pin_sequence(self, r: int, g: int, b: int):
        self.send_packet(make_pin_sequence_packet(r, g, b))

    def set_symphony_points(self, points: int):
        self.send_packet(make_symphony_points_packet(points))

    def sync_system_time(self):
        now = time.localtime()
        wday = (now.tm_wday + 1) % 7
        self.send_packet(make_system_time_packet(now.tm_hour, now.tm_min, now.tm_sec, wday))

    def set_timing_schedule(self, hour: int, minute: int, second: int, mode: int, weeks_bitmask: int):
        self.send_packet(make_timing_status_packet(hour, minute, second, mode, weeks_bitmask))

    def close(self):
        self._stop_event.set()
        self.clear_stream()
        if self._loop and self._loop.is_running():
            try:
                fut = asyncio.run_coroutine_threadsafe(self._async_disconnect(), self._loop)
                fut.result(timeout=1.0)
            except Exception:
                pass
            self._loop.call_soon_threadsafe(self._loop.stop)
