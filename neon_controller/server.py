"""
HTTP and REST API Server for Neon Lights React Application.
Serves static React frontend assets and provides real-time JSON API endpoints
for Bleak Bluetooth LE and WASAPI Audio Loopback control.
"""

import json
import logging
import os
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any, List

from .ble_manager import BLEManager
from .audio_manager import AudioManager, SUPPORTED_AUDIO_MODES
from .protocol import (
    NAME_FILTER_PREFIXES,
    PRESET_COLORS,
    MODE_CATEGORIES,
    EXTERNAL_MIC_EQ_MODES,
    PIN_SEQUENCES,
    make_power_packet,
    make_color_packet,
    make_brightness_packet,
    make_speed_packet,
    make_mode_packet,
    make_cct_packet,
    make_pin_sequence_packet,
    make_symphony_points_packet,
    make_external_mic_power_packet,
    make_external_mic_sensitivity_packet,
    make_external_mic_eq_packet,
)

logger = logging.getLogger("NeonServer")

if hasattr(sys, "_MEIPASS"):
    WEB_DIR = os.path.join(sys._MEIPASS, "neon_controller", "web")
else:
    WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")


class NeonBackend:
    def __init__(self):
        self.ble = BLEManager()
        self.audio = AudioManager(self.ble)

        # Internal State
        self.is_powered_on = True
        self.current_r = 0
        self.current_g = 240
        self.current_b = 255
        self.current_brightness = 100
        self.current_speed = 80
        self.active_mode_name = "Solid Cyan"
        self.active_mode_id = -1
        self.symphony_points = 100
        self.connected = False
        self.connected_mac = None
        self.scanned_devices: List[Dict[str, Any]] = []
        self.hw_mic_on = False
        self.hw_mic_eq = 3
        self.hw_mic_sens = 85
        self.pin_sequence = [0, 1, 2]
        self.audio_mode = "🌀 Rolling Lines (with Black Gaps)"
        self.audio_sensitivity = 1.3
        self.audio_device_id = -1
        self.live_level = 0.0
        self.live_rgb = [0, 240, 255]
        self.logs: List[str] = ["Backend initialized and ready."]

        # Connect callbacks
        self.ble.on_connection_changed = self._on_connection_changed
        self.ble.on_scan_finished = self._on_scan_finished
        self.audio.on_level = self._on_audio_level

        # Auto-scan and connect to default MAC on startup
        self.ble.scan(timeout=3.0)
        threading.Thread(target=self._startup_auto_connect, daemon=True).start()

    def _startup_auto_connect(self):
        time.sleep(5.0)
        if not self.ble.is_connected() and not self.connected:
            self._log("Startup fallback auto-connect to default device (BE:69:58:01:CC:00)...")
            self.ble.connect("BE:69:58:01:CC:00")

    def _log(self, msg: str):
        logger.info(msg)
        self.logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        if len(self.logs) > 50:
            self.logs.pop(0)

    def _on_connection_changed(self, connected: bool, address: str):
        self.connected = connected
        self.connected_mac = address if connected else None
        if connected:
            self._log(f"Connected to Neon Strip ({address})")
        else:
            self._log("Disconnected from light.")

    def _on_scan_finished(self, devices):
        self.scanned_devices = [
            {"name": name, "address": addr, "rssi": rssi}
            for (name, addr, rssi) in devices
        ]
        self._log(f"Scan finished. Found {len(self.scanned_devices)} device(s).")

        # Auto-connect if found and not yet connected
        if not self.ble.is_connected():
            for name, addr, _ in devices:
                if any(name.startswith(p) for p in NAME_FILTER_PREFIXES) or addr == "BE:69:58:01:CC:00":
                    self._log(f"Auto-connecting to detected Neon Light: {name} ({addr})")
                    self.ble.connect(addr)
                    break

    def _on_audio_level(self, level: float, r: int, g: int, b: int):
        self.live_level = level
        self.live_rgb = [r, g, b]

    def get_full_state(self) -> Dict[str, Any]:
        # Filter out "Scenes" category from mode categories
        filtered_categories = {
            k: [
                {"name": name, "id": cmd_id}
                for (name, cmd_id, is_scene) in mode_list
            ]
            for k, mode_list in MODE_CATEGORIES.items()
            if k != "Scenes"
        }

        audio_devices = self.audio.get_audio_devices()

        return {
            "power": self.is_powered_on,
            "connected": self.connected or self.ble.is_connected(),
            "connected_mac": self.connected_mac or self.ble.get_current_address(),
            "color": {"r": self.current_r, "g": self.current_g, "b": self.current_b},
            "brightness": self.current_brightness,
            "speed": self.current_speed,
            "active_mode_name": self.active_mode_name,
            "active_mode_id": self.active_mode_id,
            "symphony_points": self.symphony_points,
            "hw_mic": {
                "on": self.hw_mic_on,
                "eq": self.hw_mic_eq,
                "sensitivity": self.hw_mic_sens,
            },
            "pin_sequence": self.pin_sequence,
            "audio_sync": {
                "running": self.audio.is_running(),
                "mode": self.audio.mode,
                "sensitivity": self.audio.sensitivity,
                "device_id": self.audio.selected_device_id,
            },
            "preset_colors": [
                {"name": name, "hex": hex_c, "r": r, "g": g, "b": b}
                for (name, hex_c, (r, g, b)) in PRESET_COLORS
            ],
            "mode_categories": filtered_categories,
            "eq_modes": [
                {"name": name, "id": eq_id} for (name, eq_id) in EXTERNAL_MIC_EQ_MODES
            ],
            "pin_sequences": [
                {"name": name, "order": list(seq)} for (name, seq) in PIN_SEQUENCES
            ],
            "supported_audio_modes": SUPPORTED_AUDIO_MODES,
            "audio_devices": audio_devices,
            "scanned_devices": self.scanned_devices,
            "logs": self.logs[-20:],
        }

    # Control Operations
    def set_power(self, on: bool):
        self.is_powered_on = on
        if not on:
            self.audio.stop()
            self.ble.disarm_external_mic(0, 0, 0)
            self.ble.set_power(False)
            self.active_mode_name = "Powered OFF"
        else:
            self.ble.set_power(True)
            self.set_color(self.current_r, self.current_g, self.current_b)
            self.active_mode_name = "Solid Light"
        self._log(f"Power toggled: {'ON' if on else 'OFF'}")

    def set_color(self, r: int, g: int, b: int):
        self.current_r = r
        self.current_g = g
        self.current_b = b
        self.active_mode_name = f"RGB({r}, {g}, {b})"
        self.active_mode_id = -1
        if self.audio.is_running():
            self.audio.set_base_color(r, g, b)
        if self.hw_mic_on:
            self.hw_mic_on = False
            self.ble.disarm_external_mic(r, g, b)
        self.ble.set_color(r, g, b)

    def set_brightness(self, level: int):
        level = max(1, min(100, int(level)))
        self.current_brightness = level
        self.audio.set_master_brightness(level / 100.0)
        self.ble.set_brightness(level)

    def set_speed(self, speed: int):
        speed = max(1, min(100, int(speed)))
        self.current_speed = speed
        self.ble.set_speed(speed)

    def set_mode(self, mode_id: int, name: str):
        self.active_mode_id = mode_id
        self.active_mode_name = name
        if self.audio.is_running():
            self.audio.stop()
        if self.hw_mic_on:
            self.hw_mic_on = False
            self.ble.disarm_external_mic(self.current_r, self.current_g, self.current_b)
        self.ble.set_mode(mode_id)
        self._log(f"Activated Dynamic Mode: {name} (ID: {mode_id})")

    def set_cct(self, warm: int, cold: int):
        self.ble.set_cct(warm, cold)
        self.active_mode_name = f"White CCT ({warm}% Warm / {cold}% Cold)"
        self._log(f"CCT White: {warm}% Warm / {cold}% Cold")

    def set_symphony_points(self, points: int):
        points = max(1, min(1024, int(points)))
        self.symphony_points = points
        self.ble.set_symphony_points(points)
        self._log(f"Set strip pixel length (Symphony points): {points}")

    def set_pin_sequence(self, r: int, g: int, b: int):
        self.pin_sequence = [r, g, b]
        self.ble.set_pin_sequence(r, g, b)
        self._log(f"Set RGB channel order: {r}-{g}-{b}")

    def set_hw_mic(self, on: bool, eq: int = 3, sens: int = 85):
        self.hw_mic_on = on
        self.hw_mic_eq = eq
        self.hw_mic_sens = sens
        if on:
            self.audio.stop()
            self.ble.clear_stream()
            self.ble.set_power(True)
            self.ble.set_symphony_points(100)
            self.ble.set_speed(self.current_speed)
            self.ble.set_external_mic_sensitivity(sens)
            self.ble.set_external_mic_power(True)
            self.ble.set_external_mic_eq(eq)
            self.active_mode_name = f"Hardware Mic (EQ {eq})"
            self._log(f"Hardware Mic ON (EQ {eq}, Sens {sens})")
        else:
            self.ble.disarm_external_mic(self.current_r, self.current_g, self.current_b)
            self._log("Hardware Mic Disarmed.")

    def set_audio_sync(self, start: bool, mode: str = None, dev_id: int = None, sensitivity: float = None):
        if mode:
            self.audio_mode = mode
            self.audio.set_mode(mode)
        if dev_id is not None:
            self.audio_device_id = dev_id
            self.audio.set_device(dev_id, is_loopback=(dev_id != -2))
        if sensitivity is not None:
            self.audio_sensitivity = sensitivity
            self.audio.set_sensitivity(sensitivity)

        if start:
            if self.hw_mic_on:
                self.hw_mic_on = False
                self.ble.disarm_external_mic(self.current_r, self.current_g, self.current_b)
            self.audio.set_base_color(self.current_r, self.current_g, self.current_b)
            self.audio.set_master_brightness(self.current_brightness / 100.0)
            self.audio.start()
            self.active_mode_name = f"Audio Sync: {self.audio.mode}"
            self._log(f"Audio Game & Music Sync Started: {self.audio.mode}")
        else:
            self.audio.stop()
            self._log("Audio Game & Music Sync Stopped.")

    def scan_devices(self):
        self.ble.scan(timeout=4.0)

    def connect_device(self, mac: str = None):
        target_mac = mac
        if not target_mac or target_mac in ("undefined", "null", ""):
            for dev in self.scanned_devices:
                name = dev.get("name", "")
                if any(name.startswith(p) for p in NAME_FILTER_PREFIXES) or dev.get("address") == "BE:69:58:01:CC:00":
                    target_mac = dev["address"]
                    break
            if not target_mac:
                target_mac = "BE:69:58:01:CC:00"

        self._log(f"Connecting to {target_mac}...")
        self.ble.connect(target_mac)

    def disconnect_device(self):
        self.audio.stop()
        self.ble.disconnect()

    def close(self):
        self.audio.stop()
        self.ble.close()


# Global Singleton Backend Instance
backend = NeonBackend()


class NeonRequestHandler(SimpleHTTPRequestHandler):
    """Handles both static React web files and JSON API requests."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/api/state":
            self._send_json(backend.get_full_state())
        elif self.path == "/api/audio/level":
            self._send_json({
                "level": backend.live_level,
                "rgb": backend.live_rgb,
                "running": backend.audio.is_running()
            })
        elif self.path == "/api/devices":
            self._send_json(backend.scanned_devices)
        elif self.path == "/api/audio_devices":
            self._send_json(backend.audio.get_audio_devices())
        else:
            # Fall back to serving static web files from neon_controller/web
            super().do_GET()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            body = {}

        path = self.path

        if path == "/api/power":
            backend.set_power(bool(body.get("on", True)))
        elif path == "/api/color":
            backend.set_color(int(body.get("r", 0)), int(body.get("g", 240)), int(body.get("b", 255)))
        elif path == "/api/brightness":
            backend.set_brightness(int(body.get("level", 100)))
        elif path == "/api/speed":
            backend.set_speed(int(body.get("speed", 80)))
        elif path == "/api/mode":
            backend.set_mode(int(body.get("mode_id", 1)), str(body.get("name", "Dynamic Mode")))
        elif path == "/api/cct":
            backend.set_cct(int(body.get("warm", 50)), int(body.get("cold", 50)))
        elif path == "/api/points":
            backend.set_symphony_points(int(body.get("points", 100)))
        elif path == "/api/pin_sequence":
            seq = body.get("sequence", [0, 1, 2])
            backend.set_pin_sequence(seq[0], seq[1], seq[2])
        elif path == "/api/hw_mic":
            backend.set_hw_mic(
                bool(body.get("on", True)),
                int(body.get("eq", 3)),
                int(body.get("sensitivity", 85))
            )
        elif path == "/api/hw_mic/disarm":
            backend.set_hw_mic(False)
        elif path == "/api/audio/start":
            backend.set_audio_sync(
                start=True,
                mode=body.get("mode"),
                dev_id=body.get("device_id"),
                sensitivity=body.get("sensitivity")
            )
        elif path == "/api/audio/stop":
            backend.set_audio_sync(start=False)
        elif path == "/api/audio/mode":
            backend.audio.set_mode(str(body.get("mode")))
        elif path == "/api/audio/sensitivity":
            backend.audio.set_sensitivity(float(body.get("sensitivity", 1.3)))
        elif path == "/api/scan":
            backend.scan_devices()
        elif path == "/api/connect":
            backend.connect_device(str(body.get("mac")))
        elif path == "/api/disconnect":
            backend.disconnect_device()

        self._send_json({"ok": True, "state": backend.get_full_state()})

    def _send_json(self, data: Any):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        # Suppress spammy HTTP request logs in console
        pass


class NeonHttpServer:
    def __init__(self, host="127.0.0.1", port=8765):
        self.host = host
        self.port = port
        self.httpd = None
        self._thread = None

    def start(self):
        self.httpd = HTTPServer((self.host, self.port), NeonRequestHandler)
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self._thread.start()
        logger.info(f"Neon Lights React Server running at http://{self.host}:{self.port}")

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        backend.close()
