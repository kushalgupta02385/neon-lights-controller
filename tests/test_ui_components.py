"""
Unit Tests for NeonApp GUI State & User Interaction Logic
Validates:
1. Dynamic Connect / Disconnect button toggling and styling in device list.
2. Ambient Scenes activation with accurate scene_id (e.g. Valentine's Day #26).
3. Hardware mic disarm on mode/power/scene changes and dedicated disarm button.
4. Audio Game Sync default device and silence level meter clearance.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neon_controller.app import NeonApp


class TestNeonAppUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Instantiate App in hidden mode
        cls.app = NeonApp()
        cls.app.withdraw()  # Keep window hidden during test

    @classmethod
    def tearDownClass(cls):
        try:
            cls.app._on_close()
        except Exception:
            pass

    def test_01_audio_device_defaults_to_auto(self):
        """Verify Audio Game Sync defaults to Auto Active Windows Playback Device."""
        val = self.app.audio_dev_menu.get()
        self.assertIn("Auto", val, "Default audio device must be Auto Active Windows Playback Device")
        self.assertEqual(self.app.audio.selected_device_id, -1)

    def test_02_device_list_connect_to_disconnect_toggle(self):
        """Verify device Connect button changes to Disconnect upon connection and toggles properly."""
        test_mac = "BE:69:58:01:CC:00"
        devices = [("MELK-OA10   44", test_mac, -60)]

        # Simulate scan finished
        self.app._on_ble_scan_finished(devices)
        self.app.update()

        self.assertIn(test_mac, self.app._device_cards)
        card_btn = self.app._device_cards[test_mac]["btn"]

        # Before connection: Button must say 'Connect'
        self.assertEqual(card_btn.cget("text"), "Connect")

        # Mock ble manager methods
        self.app.ble.is_connected = MagicMock(return_value=True)
        self.app.ble.get_current_address = MagicMock(return_value=test_mac)
        disconnect_mock = MagicMock()
        self.app.ble.disconnect = disconnect_mock

        # Simulate BLE connection established
        self.app._on_ble_connection_changed(True, test_mac)
        self.app.update()

        # After connection: Button text MUST change to 'Disconnect' with red color
        self.assertEqual(card_btn.cget("text"), "Disconnect")
        self.assertEqual(card_btn.cget("fg_color"), "#FF4757")

        # Simulate user clicking the 'Disconnect' button
        card_btn.invoke()
        disconnect_mock.assert_called_once()

        # Simulate BLE disconnected
        self.app.ble.is_connected = MagicMock(return_value=False)
        self.app.ble.get_current_address = MagicMock(return_value=None)
        self.app._on_ble_connection_changed(False, None)
        self.app.update()

        # After disconnect: Button must revert back to 'Connect'
        self.assertEqual(card_btn.cget("text"), "Connect")

    def test_03_ambient_scenes_tab_and_header_buttons_removed(self):
        """Verify Ambient Scenes tab and header buttons are cleanly removed as requested."""
        # 1. Top header buttons removed
        self.assertFalse(hasattr(self.app, "quick_game_sync_btn") and self.app.quick_game_sync_btn.winfo_exists())
        self.assertFalse(hasattr(self.app, "quick_night_btn") and self.app.quick_night_btn.winfo_exists())
        self.assertFalse(hasattr(self.app, "quick_max_btn") and self.app.quick_max_btn.winfo_exists())

        # 2. Ambient Scenes tab removed from tabview
        self.assertFalse(hasattr(self.app, "tab_scenes"))

    def test_04_hardware_mic_disarm_on_color_or_power(self):
        """Verify Hardware Mic is safely disarmed whenever another color, mode, or power is selected."""
        disarm_mock = MagicMock()
        self.app.ble.disarm_external_mic = disarm_mock

        # Arm mic
        self.app.hw_mic_switch.select()
        self.assertEqual(self.app.hw_mic_switch.get(), 1)

        # 1. Switch color -> must disarm mic
        self.app._apply_color(255, 0, 0)
        self.assertEqual(self.app.hw_mic_switch.get(), 0)
        disarm_mock.assert_called()

        # 2. Arm mic again and test dedicated Disarm button
        self.app.hw_mic_switch.select()
        self.app._disarm_hw_mic_action()
        self.assertEqual(self.app.hw_mic_switch.get(), 0)

        # 3. Test Power OFF disarm
        self.app.is_powered_on = True
        self.app._toggle_power()  # Turn off
        self.assertFalse(self.app.is_powered_on)
        self.assertEqual(self.app.hw_mic_switch.get(), 0)

    def test_05_audio_level_silence_meter(self):
        """Verify that zero/silent audio clears the VU meter and doesn't blink."""
        # Send zero volume level
        self.app._on_audio_level(0.0, 0, 0, 0)
        self.app.update_idletasks()
        items = self.app.meter_canvas.find_all()
        # On silence, no rectangle items drawn on canvas
        self.assertEqual(len(items), 0)

    def test_06_hardware_rhythm_rolling_and_brightness(self):
        """Verify Hardware Rolling Mode (EQ 3) can be activated and brightness slider updates audio manager."""
        # 1. Test hardware rolling mode (Mode 3)
        self.app.ble.set_external_mic_eq = MagicMock()
        self.app._set_hw_eq(3, "Rolling")
        self.app.ble.set_external_mic_eq.assert_called_with(3)
        self.assertEqual(self.app.hw_mic_switch.get(), 1)
        self.assertIn("Rolling", self.app.dock_active_label.cget("text"))

        # 2. Test brightness slider updating audio manager
        self.app._on_brightness_slide(90)
        self.assertAlmostEqual(self.app.audio.master_brightness, 0.90)

    def test_07_rolling_black_gaps_quick_launch(self):
        """Verify 1-Click Rolling Lines with Black Gaps (Feature 1) configures mode and starts audio sync."""
        self.app._toggle_pc_audio_sync = MagicMock()
        self.app._quick_launch_rolling_black_sync()
        self.assertEqual(self.app.audio.mode, "🌀 Rolling Lines (with Black Gaps)")
        self.assertEqual(self.app.audio_mode_menu.get(), "🌀 Rolling Lines (with Black Gaps)")
        self.assertEqual(self.app.audio.master_brightness, 1.0)
        self.app._toggle_pc_audio_sync.assert_called_once()

    def test_08_beat_lines_rhythm_lamp_quick_launch(self):
        """Verify 1-Click Beat Lines (VU Rhythm Lamp Bar) (Feature 2) configures mode and starts audio sync."""
        self.app._toggle_pc_audio_sync = MagicMock()
        self.app._quick_launch_beat_lines_sync()
        self.assertEqual(self.app.audio.mode, "📊 Beat Lines (VU Rhythm Lamp Bar)")
        self.assertEqual(self.app.audio_mode_menu.get(), "📊 Beat Lines (VU Rhythm Lamp Bar)")
        self.assertEqual(self.app.audio.master_brightness, 1.0)
        self.app._toggle_pc_audio_sync.assert_called_once()


if __name__ == "__main__":
    unittest.main()
