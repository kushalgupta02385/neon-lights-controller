import json
import socket
import time
import unittest
import urllib.request
import urllib.parse

from neon_controller.server import backend, NeonHttpServer

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

class TestReactServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = get_free_port()
        cls.server = NeonHttpServer(host='127.0.0.1', port=cls.port)
        cls.server.start()
        time.sleep(0.5)
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        if backend.audio.is_running():
            backend.audio.stop()
        cls.server.stop()

    def _get(self, path):
        req = urllib.request.Request(f"{self.base_url}{path}")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode('utf-8')

    def _post_json(self, path, data):
        json_bytes = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json_bytes,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))

    def test_01_static_index_html(self):
        status, html = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn("Neon Lights Studio", html)
        self.assertIn('id="root"', html)
        self.assertIn("app.jsx", html)

    def test_02_static_css_and_jsx(self):
        status, css = self._get("/style.css")
        self.assertEqual(status, 200)
        self.assertIn("font-family", css)

        status, jsx = self._get("/app.jsx")
        self.assertEqual(status, 200)
        self.assertIn("function App()", jsx)

    def test_03_static_vendor_scripts(self):
        status, react = self._get("/vendor/react.production.min.js")
        self.assertEqual(status, 200)
        self.assertGreater(len(react), 5000)

        status, bbl = self._get("/vendor/babel.min.js")
        self.assertEqual(status, 200)
        self.assertGreater(len(bbl), 100000)

    def test_04_get_state_endpoint(self):
        status, data = self._get("/api/state")
        self.assertEqual(status, 200)
        state = json.loads(data)
        self.assertIn("power", state)
        self.assertIn("brightness", state)
        self.assertIn("speed", state)
        self.assertIn("color", state)
        self.assertIn("audio_sync", state)
        self.assertIn("mode_categories", state)
        self.assertIn("preset_colors", state)
        self.assertIn("supported_audio_modes", state)
        self.assertIn("symphony_points", state)
        # Verify Scenes category was removed per user instruction
        self.assertNotIn("Scenes", state["mode_categories"])

    def test_05_power_endpoint(self):
        status, resp = self._post_json("/api/power", {"on": False})
        self.assertEqual(status, 200)
        self.assertTrue(resp.get("ok"))
        self.assertFalse(backend.is_powered_on)

        status, resp = self._post_json("/api/power", {"on": True})
        self.assertEqual(status, 200)
        self.assertTrue(resp.get("ok"))
        self.assertTrue(backend.is_powered_on)

    def test_06_brightness_endpoint(self):
        status, resp = self._post_json("/api/brightness", {"level": 77})
        self.assertEqual(status, 200)
        self.assertTrue(resp.get("ok"))
        self.assertEqual(backend.current_brightness, 77)

    def test_07_speed_endpoint(self):
        status, resp = self._post_json("/api/speed", {"speed": 42})
        self.assertEqual(status, 200)
        self.assertTrue(resp.get("ok"))
        self.assertEqual(backend.current_speed, 42)

    def test_08_color_endpoint(self):
        status, resp = self._post_json("/api/color", {"r": 255, "g": 128, "b": 0})
        self.assertEqual(status, 200)
        self.assertTrue(resp.get("ok"))
        self.assertEqual(backend.current_r, 255)
        self.assertEqual(backend.current_g, 128)
        self.assertEqual(backend.current_b, 0)

    def test_09_cct_endpoint(self):
        status, resp = self._post_json("/api/cct", {"warm": 200, "cold": 50})
        self.assertEqual(status, 200)
        self.assertTrue(resp.get("ok"))

    def test_10_mode_endpoint(self):
        status, resp = self._post_json("/api/mode", {"mode_id": 103, "name": "7-Color Running"})
        self.assertEqual(status, 200)
        self.assertTrue(resp.get("ok"))
        self.assertEqual(backend.active_mode_id, 103)
        self.assertEqual(backend.active_mode_name, "7-Color Running")

    def test_11_audio_settings(self):
        status, resp = self._post_json("/api/audio/mode", {"mode": "🌀 Rolling Lines (with Black Gaps)"})
        self.assertEqual(status, 200)
        self.assertTrue(resp.get("ok"))
        self.assertEqual(backend.audio.mode, "🌀 Rolling Lines (with Black Gaps)")

        status, resp = self._post_json("/api/audio/sensitivity", {"sensitivity": 2.2})
        self.assertEqual(status, 200)
        self.assertTrue(resp.get("ok"))
        self.assertAlmostEqual(backend.audio.sensitivity, 2.2, places=2)

    def test_12_points_and_pin_sequence(self):
        status, resp = self._post_json("/api/points", {"points": 150})
        self.assertEqual(status, 200)
        self.assertTrue(resp.get("ok"))
        self.assertEqual(backend.symphony_points, 150)

        status, resp = self._post_json("/api/pin_sequence", {"sequence": [1, 0, 2]})
        self.assertEqual(status, 200)
        self.assertTrue(resp.get("ok"))
        self.assertEqual(backend.pin_sequence, [1, 0, 2])

    def test_13_hardware_mic(self):
        status, resp = self._post_json("/api/hw_mic", {"on": True, "eq": 4, "sensitivity": 90})
        self.assertEqual(status, 200)
        self.assertTrue(backend.hw_mic_on)
        self.assertEqual(backend.hw_mic_sens, 90)
        self.assertEqual(backend.hw_mic_eq, 4)

        status, resp = self._post_json("/api/hw_mic/disarm", {})
        self.assertEqual(status, 200)
        self.assertFalse(backend.hw_mic_on)

if __name__ == "__main__":
    unittest.main()
