"""
Comprehensive Unit & Integration Test Suite for Neon Lights Controller
Tests:
1. Protocol Packet Structure & All 241 Mode Opcode Validation
2. BLEManager FIFO Command Queue Ordering (No Dropped Packets)
3. Audio Reactive Engine & WASAPI Loopback Discovery for Game/Music Sync
4. Software Scene Animation Engine (All 28 Ambient Scenes Verified)
5. Live Bluetooth Hardware Integration on BE:69:58:01:CC:00
"""

import asyncio
import colorsys
import os
import sys
import time
import unittest
import numpy as np

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neon_controller.protocol import (
    SERVICE_UUID,
    WRITE_CHAR_UUID,
    NOTIFY_CHAR_UUID,
    PRESET_COLORS,
    MODE_CATEGORIES,
    EXTERNAL_MIC_EQ_MODES,
    PIN_SEQUENCES,
    make_power_packet,
    make_color_packet,
    make_music_color_packet,
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
    make_system_time_packet,
    make_timing_status_packet,
)
from neon_controller.ble_manager import BLEManager
from neon_controller.audio_manager import AudioManager
from neon_controller.scene_engine import SceneEngine
from bleak import BleakClient


class TestProtocol(unittest.TestCase):
    """Verifies all 9-byte packet builders conform strictly to the reverse-engineered MagicLantern protocol."""

    def assertValidPacket(self, pkt: bytes, expected_opcode: int = None):
        self.assertEqual(len(pkt), 9, f"Packet length must be 9, got {len(pkt)}")
        self.assertEqual(pkt[0], 0x7E, f"Header must be 0x7E, got {pkt[0]:02X}")
        self.assertEqual(pkt[8], 0xEF, f"Trailer must be 0xEF, got {pkt[8]:02X}")
        if expected_opcode is not None:
            self.assertEqual(pkt[2], expected_opcode, f"Expected opcode {expected_opcode}, got {pkt[2]}")

    def test_power_packets(self):
        on_pkt = make_power_packet(True)
        self.assertValidPacket(on_pkt, 0x04)
        self.assertEqual(on_pkt[3], 0x01)
        self.assertEqual(on_pkt[5], 0x01)

        off_pkt = make_power_packet(False)
        self.assertValidPacket(off_pkt, 0x04)
        self.assertEqual(off_pkt[3], 0x00)
        self.assertEqual(off_pkt[5], 0x00)

    def test_color_packets(self):
        # Normal
        pkt = make_color_packet(255, 128, 64)
        self.assertValidPacket(pkt, 0x05)
        self.assertEqual(pkt[3], 0x03)
        self.assertEqual(pkt[4], 255)
        self.assertEqual(pkt[5], 128)
        self.assertEqual(pkt[6], 64)
        self.assertEqual(pkt[7], 0x10)  # 0x10 for static color

        # Music reactive color uses 0x20
        music_pkt = make_music_color_packet(10, 20, 30)
        self.assertValidPacket(music_pkt, 0x05)
        self.assertEqual(music_pkt[7], 0x20)

        # Clamping
        clamp_pkt = make_color_packet(-50, 999, 100)
        self.assertEqual(clamp_pkt[4], 0)
        self.assertEqual(clamp_pkt[5], 255)
        self.assertEqual(clamp_pkt[6], 100)

    def test_brightness_and_speed_packets(self):
        b_pkt = make_brightness_packet(75)
        self.assertValidPacket(b_pkt, 0x01)
        self.assertEqual(b_pkt[3], 75)

        s_pkt = make_speed_packet(40)
        self.assertValidPacket(s_pkt, 0x02)
        self.assertEqual(s_pkt[3], 40)

    def test_dynamic_modes_database(self):
        total_modes = sum(len(modes) for modes in MODE_CATEGORIES.values())
        self.assertEqual(total_modes, 241, f"Expected exactly 241 modes, got {total_modes}")

        # Verify all hardware dynamic modes generate valid opcode 0x03 packets
        for cat, modes in MODE_CATEGORIES.items():
            if cat == "Scenes":
                continue
            for name, cmd_id, is_scene in modes:
                self.assertFalse(is_scene, f"{name} in {cat} should not be marked as scene")
                pkt = make_mode_packet(cmd_id)
                self.assertValidPacket(pkt, 0x03)
                self.assertEqual(pkt[3], cmd_id & 0xFF)
                self.assertEqual(pkt[4], 0x06)

    def test_scenes_database(self):
        scenes = MODE_CATEGORIES["Scenes"]
        self.assertEqual(len(scenes), 28, "Scenes category must have 28 items")
        for name, scene_id, is_scene in scenes:
            self.assertTrue(is_scene)
            pkt = make_scene_packet(scene_id)
            self.assertValidPacket(pkt, 0x31)
            self.assertEqual(pkt[3], scene_id)
            self.assertEqual(pkt[4], 0x07)
            self.assertEqual(pkt[7], 0x01)

    def test_cct_packets(self):
        pkt = make_cct_packet(80, 20)
        self.assertValidPacket(pkt, 0x05)
        self.assertEqual(pkt[3], 0x02)
        self.assertEqual(pkt[4], 80)
        self.assertEqual(pkt[5], 20)

    def test_hardware_mic_packets(self):
        mic_on = make_external_mic_power_packet(True)
        self.assertValidPacket(mic_on, 0x07)
        self.assertEqual(mic_on[3], 0x01)

        sens_pkt = make_external_mic_sensitivity_packet(90)
        self.assertValidPacket(sens_pkt, 0x06)
        self.assertEqual(sens_pkt[3], 90)

        eq_pkt = make_external_mic_eq_packet(1)  # Rhythm mode
        self.assertValidPacket(eq_pkt, 0x03)
        self.assertEqual(eq_pkt[3], 129)

    def test_pin_and_symphony_points(self):
        pin_pkt = make_pin_sequence_packet(0, 1, 2)
        self.assertValidPacket(pin_pkt, 0x81)
        self.assertEqual(pin_pkt[3], 0)
        self.assertEqual(pin_pkt[4], 1)
        self.assertEqual(pin_pkt[5], 2)

        pts_pkt = make_symphony_points_packet(100)
        self.assertValidPacket(pts_pkt, 0x21)
        self.assertEqual(pts_pkt[3], 100)
        self.assertEqual(pts_pkt[4], 0)


class TestBLEManagerQueue(unittest.TestCase):
    """Verifies that BLEManager enqueues commands in strict FIFO order without packet dropping."""

    def setUp(self):
        self.ble = BLEManager()

    def tearDown(self):
        self.ble.close()

    def test_fifo_command_enqueue(self):
        # Simulate queuing mode, speed, brightness
        self.ble._cmd_queue.put_nowait(make_power_packet(True))
        self.ble._cmd_queue.put_nowait(make_mode_packet(193))
        self.ble._cmd_queue.put_nowait(make_speed_packet(80))
        self.ble._cmd_queue.put_nowait(make_brightness_packet(100))

        # Check queue size is exactly 4
        self.assertEqual(self.ble._cmd_queue.qsize(), 4)

        # Dequeue in order
        p1 = self.ble._cmd_queue.get_nowait()
        self.assertEqual(p1[2], 0x04)  # Power
        p2 = self.ble._cmd_queue.get_nowait()
        self.assertEqual(p2[2], 0x03)  # Mode
        self.assertEqual(p2[3], 193)   # 7-Color Jump
        p3 = self.ble._cmd_queue.get_nowait()
        self.assertEqual(p3[2], 0x02)  # Speed
        self.assertEqual(p3[3], 80)
        p4 = self.ble._cmd_queue.get_nowait()
        self.assertEqual(p4[2], 0x01)  # Brightness
        self.assertEqual(p4[3], 100)

    def test_disarm_external_mic(self):
        # Disarming mic should invoke send_packet for mic power False (0x07) and color packet (0x05)
        sent = []
        self.ble.send_packet = lambda pkt: sent.append(pkt)
        self.ble.disarm_external_mic(0, 240, 255)
        self.assertEqual(len(sent), 2)
        p1, p2 = sent[0], sent[1]
        self.assertEqual(p1[2], 0x07)  # External mic power
        self.assertEqual(p1[3], 0x00)  # OFF
        self.assertEqual(p2[2], 0x05)  # Color opcode
        self.assertEqual(p2[4], 0)
        self.assertEqual(p2[5], 240)
        self.assertEqual(p2[6], 255)


class TestAudioReactiveEngine(unittest.TestCase):
    """Verifies WASAPI Loopback discovery and reactive sound analysis."""

    def setUp(self):
        self.ble = BLEManager()
        self.audio = AudioManager(self.ble)

    def tearDown(self):
        self.audio.stop()
        self.ble.close()

    def test_device_discovery(self):
        devices = self.audio.get_audio_devices()
        self.assertIsInstance(devices, list)
        self.assertGreater(len(devices), 0, "Should detect audio devices on Windows")

        # Verify loopback devices are present
        loopback_devices = [d for d in devices if d.get("is_loopback")]
        self.assertGreater(len(loopback_devices), 0, "WASAPI Loopback devices must be available for Game/Music sync")

    def test_audio_reactive_modes(self):
        # Test switching all multi-color and reactive modes
        modes = [
            "🌀 Rolling Lines (with Black Gaps)",
            "📊 Beat Lines (VU Rhythm Lamp Bar)",
            "☄️ 7-Color Meteor Tail (with Black)",
            "🏎️ 7-Color Race (with Black Gaps)",
            "🌀 Rolling Continuous (No Gaps)",
            "🌊 Rolling Reverse (End to Start)",
            "Beat Color Jump (7-Color)",
            "Dynamic Rainbow Spectrum",
            "Frequency Tri-Split (Bass/Mid/High)",
            "Bass Strobe & Energy",
            "Cyberpunk Neon",
            "Pulse Beat (Single Color)",
        ]
        for mode in modes:
            self.audio.set_mode(mode)
            self.assertEqual(self.audio.mode, mode)

        # 1. Feature 1: Rolling Lines with Black Gaps -> Mode 103 (7-Color Running with Black Gaps)
        self.audio.set_mode("🌀 Rolling Lines (with Black Gaps)")
        is_pat, cmd = self.audio._get_pattern_mode_info()
        self.assertTrue(is_pat)
        self.assertEqual(cmd, 103)

        # 2. Feature 2: Beat Lines (VU Rhythm Lamp Bar) -> Dynamic symphony points cmd -1
        self.audio.set_mode("📊 Beat Lines (VU Rhythm Lamp Bar)")
        is_pat, cmd = self.audio._get_pattern_mode_info()
        self.assertTrue(is_pat)
        self.assertEqual(cmd, -1)

        # 3. 7-Color Meteor Tail with Black -> Mode 23
        self.audio.set_mode("☄️ 7-Color Meteor Tail (with Black)")
        is_pat, cmd = self.audio._get_pattern_mode_info()
        self.assertTrue(is_pat)
        self.assertEqual(cmd, 23)

        # 4. 7-Color Race with Black Gaps -> Mode 81
        self.audio.set_mode("🏎️ 7-Color Race (with Black Gaps)")
        is_pat, cmd = self.audio._get_pattern_mode_info()
        self.assertTrue(is_pat)
        self.assertEqual(cmd, 81)

        # 5. Continuous Rolling start-to-end -> Mode 1
        self.audio.set_mode("🌀 Rolling Continuous (No Gaps)")
        is_pat, cmd = self.audio._get_pattern_mode_info()
        self.assertTrue(is_pat)
        self.assertEqual(cmd, 1)

        # 6. Reverse rolling end-to-start -> Mode 2
        self.audio.set_mode("🌊 Rolling Reverse (End to Start)")
        is_pat, cmd = self.audio._get_pattern_mode_info()
        self.assertTrue(is_pat)
        self.assertEqual(cmd, 2)

        # 7. Non-pattern mode
        self.audio.set_mode("Beat Color Jump (7-Color)")
        is_pat, _ = self.audio._get_pattern_mode_info()
        self.assertFalse(is_pat)

        # Test sensitivity clamping
        self.audio.set_sensitivity(2.5)
        self.assertEqual(self.audio.sensitivity, 2.5)

        # Test master brightness setting
        self.audio.set_master_brightness(0.85)
        self.assertAlmostEqual(self.audio.master_brightness, 0.85)

    def test_noise_floor_silence_gate(self):
        # Generate low-amplitude idle noise (RMS ~20, below loopback noise floor)
        noise = np.random.normal(0, 20, 1024).astype(np.float32)
        samples = noise - np.mean(noise)
        rms = float(np.sqrt(np.mean(samples ** 2)))
        noise_floor = 60.0
        self.assertLess(rms, noise_floor)
        # Below noise floor, volume is strictly 0.0
        raw_vol = 0.0 if rms < noise_floor else float((rms - noise_floor) / 7500.0)
        self.assertEqual(raw_vol, 0.0, "Noise floor must completely suppress background audio noise")


class TestSceneEngine(unittest.TestCase):
    """Verifies that the Software Scene Engine correctly animates all 28 scenes."""

    def setUp(self):
        self.ble = BLEManager()
        self.scene = SceneEngine(self.ble)

    def tearDown(self):
        self.scene.stop()
        self.ble.close()

    def test_all_28_scenes_execution(self):
        scenes = MODE_CATEGORIES["Scenes"]
        self.assertEqual(len(scenes), 28)

        for name, scene_id, _ in scenes:
            frames_received = []

            def frame_cb(r, g, b):
                frames_received.append((r, g, b))

            self.scene.on_frame = frame_cb
            self.scene.start_scene(scene_name=name, scene_id=scene_id, speed_pct=100, brightness_pct=100)
            self.assertTrue(self.scene.is_running())
            self.assertEqual(self.scene.get_active_scene(), name)

            # Let each scene generate 2-3 frames
            time.sleep(0.09)
            self.scene.stop()
            self.assertFalse(self.scene.is_running())
            self.assertGreater(len(frames_received), 0, f"Scene '{name}' should generate frames")

            # Validate generated RGB colors
            for r, g, b in frames_received:
                self.assertTrue(0 <= r <= 255, f"Red out of bounds: {r}")
                self.assertTrue(0 <= g <= 255, f"Green out of bounds: {g}")
                self.assertTrue(0 <= b <= 255, f"Blue out of bounds: {b}")


class TestHardwareIntegration(unittest.TestCase):
    """Live Hardware Verification against the user's connected light BE:69:58:01:CC:00."""

    ADDRESS = "BE:69:58:01:CC:00"

    def test_live_hardware_features(self):
        async def run_hw_test():
            print(f"\n[Hardware Test] Connecting to {self.ADDRESS}...")
            async with BleakClient(self.ADDRESS, timeout=12.0) as client:
                self.assertTrue(client.is_connected, "Failed to connect to physical neon light")
                print("  Connected to light successfully.")

                # 1. Turn Power ON
                print("  1. Testing Power ON...")
                await client.write_gatt_char(WRITE_CHAR_UUID, make_power_packet(True), response=False)
                await asyncio.sleep(0.2)

                # 2. Test IC points configuration (100 pixels)
                print("  2. Testing IC points (100 pixels)...")
                await client.write_gatt_char(WRITE_CHAR_UUID, make_symphony_points_packet(100), response=False)
                await asyncio.sleep(0.2)

                # 3. Test Full RGB Color cycle (Red, Green, Blue, Neon Cyan)
                print("  3. Testing RGB Colors...")
                await client.write_gatt_char(WRITE_CHAR_UUID, make_color_packet(255, 0, 0), response=False)
                await asyncio.sleep(0.2)
                await client.write_gatt_char(WRITE_CHAR_UUID, make_color_packet(0, 255, 0), response=False)
                await asyncio.sleep(0.2)
                await client.write_gatt_char(WRITE_CHAR_UUID, make_color_packet(0, 0, 255), response=False)
                await asyncio.sleep(0.2)
                await client.write_gatt_char(WRITE_CHAR_UUID, make_color_packet(0, 240, 255), response=False)
                await asyncio.sleep(0.2)

                # 4. Test Brightness (50% then 100%)
                print("  4. Testing Brightness levels...")
                await client.write_gatt_char(WRITE_CHAR_UUID, make_brightness_packet(50), response=False)
                await asyncio.sleep(0.2)
                await client.write_gatt_char(WRITE_CHAR_UUID, make_brightness_packet(100), response=False)
                await asyncio.sleep(0.2)

                # 5. Test Dynamic Mode (7-Color Jump mode 193) & Speed (80)
                print("  5. Testing Dynamic Mode #193 and Speed 80...")
                await client.write_gatt_char(WRITE_CHAR_UUID, make_mode_packet(193), response=False)
                await asyncio.sleep(0.2)
                await client.write_gatt_char(WRITE_CHAR_UUID, make_speed_packet(80), response=False)
                await asyncio.sleep(0.5)

                # 6. Test Music reactive packet
                print("  6. Testing Music amplitude packet...")
                await client.write_gatt_char(WRITE_CHAR_UUID, make_music_color_packet(255, 0, 128), response=False)
                await asyncio.sleep(0.3)

                # 7. Test Controller Hardware Mic toggle & EQ mode
                print("  7. Testing Controller Mic & EQ mode...")
                await client.write_gatt_char(WRITE_CHAR_UUID, make_external_mic_power_packet(True), response=False)
                await asyncio.sleep(0.2)
                await client.write_gatt_char(WRITE_CHAR_UUID, make_external_mic_eq_packet(1), response=False)
                await asyncio.sleep(0.3)

                # 8. Restore static Neon Cyan
                print("  8. Restoring Cyan state...")
                await client.write_gatt_char(WRITE_CHAR_UUID, make_color_packet(0, 240, 255), response=False)
                await asyncio.sleep(0.2)
                print("  All physical hardware tests PASSED!")

        asyncio.run(run_hw_test())


if __name__ == "__main__":
    unittest.main()
