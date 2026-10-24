"""
Real-time PC Audio Reactive Manager for Neon Rope Lights
Engineered for:
1. Maximum Neon Output Brightness (Linked to Master Brightness Slider, No Low-Volume Dimming).
2. Multi-Color RGB Reaction Algorithms:
   - Beat Color Jump (7-Color High-Energy Spectrum)
   - Dynamic Rainbow Spectrum (Smooth 360° Hue Velocity Sweep)
   - Frequency Tri-Split (Bass Kicks = Crimson, Mids = Electric Cyan, Highs = Gold)
   - Rolling Wave Simulation (High-speed complementary phase shift)
   - Bass Strobe & Energy (Explosive white bursts on drops)
   - Cyberpunk Neon (Vivid Hot Pink & Cyan)
   - Pulse Beat (Single Color)
3. WASAPI Loopback Digital Sound Capture (Game Audio, YouTube, Spotify, Headphones, HDMI).
4. Smart Noise Gate & Silence Suppression (100% Elimination of idle noise and blinking).
"""

import colorsys
import logging
import math
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple
import numpy as np

# Use pyaudiowpatch for Windows WASAPI Loopback + PyAudio capture
try:
    import pyaudiowpatch as pyaudio
except ImportError:
    import pyaudio  # type: ignore

from .ble_manager import BLEManager

logger = logging.getLogger("AudioManager")

# High-saturation 7-Color Vivid Neon Palette (User-customizable)
VIBRANT_PALETTE = [
    (255, 0, 65),     # Neon Crimson
    (0, 240, 255),    # Electric Cyan
    (255, 215, 0),    # Acid Gold
    (0, 255, 110),    # Emerald Neon Green
    (180, 0, 255),    # Deep Violet Purple
    (255, 85, 0),     # Blaze Orange
    (255, 0, 180),    # Hot Magenta Pink
    (0, 170, 255),    # Sky Blue
]

SUPPORTED_AUDIO_MODES = [
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


class AudioManager:
    def __init__(self, ble_manager: BLEManager):
        self.ble = ble_manager
        self._thread: Optional[threading.Thread] = None
        self._running = False

        # Audio configuration
        self.selected_device_id: Optional[int] = -1  # -1 = Auto (Active Default Windows Output)
        self.is_loopback: bool = True
        self.sensitivity: float = 1.3   # Multiplier (0.2 to 3.5)
        self.gain: float = 1.5
        self.mode: str = "🌀 Rolling Lines (with Black Gaps)"
        self.base_color: Tuple[int, int, int] = (0, 240, 255)  # Default Neon Cyan
        self.master_brightness: float = 1.0  # 0.05 to 1.0 (controlled by UI slider)

        # Rate-limiting & Beat Detection State
        self._hue_offset = 0.0
        self._smooth_vol = 0.0
        self._strobe_decay = 0.0
        self._last_send_time = 0.0
        self._last_sent_rgb: Tuple[int, int, int] = (-1, -1, -1)
        self._min_send_interval = 0.035  # ~28 updates/sec max

        # Addressable IC Pattern & Symphony Points mode tracking
        self._pattern_active: bool = False
        self._last_sent_speed: int = -1
        self._last_speed_time: float = 0.0
        self._last_sent_points: int = 100
        self._last_points_time: float = 0.0

        # Beat detection tracking
        self._color_index = 0
        self._last_beat_time = 0.0
        self._recent_bass_history: List[float] = []
        self._curr_target_color = list(VIBRANT_PALETTE[0])
        self._curr_display_color = list(VIBRANT_PALETTE[0])

        # Callbacks
        self.on_level: Optional[Callable[[float, int, int, int], None]] = None
        self.on_status_change: Optional[Callable[[bool, str], None]] = None

    def get_audio_devices(self) -> List[Dict[str, any]]:
        """
        Enumerates all available audio devices on Windows:
        - Auto-tracking loopback (always uses active default playback device)
        - Specific System Audio Loopback devices (Speakers, Headphones, HDMI Monitors)
        - Standard Input devices (Microphone Array, Headset Mics, Line In)
        """
        devices = []
        p = pyaudio.PyAudio()
        try:
            # 1. Primary: Auto Active Device
            devices.append({
                "id": -1,
                "name": "🔊 [Auto] Active Windows Playback Device",
                "raw_name": "Auto Active Device",
                "is_loopback": True,
                "channels": 2,
                "rate": 48000,
            })

            # 2. Specific WASAPI loopback devices
            if hasattr(p, "get_loopback_device_info_generator"):
                for dev in p.get_loopback_device_info_generator():
                    name = dev["name"]
                    devices.append({
                        "id": dev["index"],
                        "name": f"🔊 [Game/Music] {name}",
                        "raw_name": name,
                        "is_loopback": True,
                        "channels": dev.get("maxInputChannels", 2),
                        "rate": int(dev.get("defaultSampleRate", 48000)),
                    })

            # 3. Standard Microphone / Input devices
            for i in range(p.get_device_count()):
                try:
                    dev = p.get_device_info_by_index(i)
                    if dev.get("maxInputChannels", 0) > 0 and not dev.get("isLoopbackDevice", False):
                        name = dev["name"]
                        devices.append({
                            "id": dev["index"],
                            "name": f"🎙️ [Microphone] {name}",
                            "raw_name": name,
                            "is_loopback": False,
                            "channels": dev.get("maxInputChannels", 1),
                            "rate": int(dev.get("defaultSampleRate", 44100)),
                        })
                except Exception:
                    continue

        finally:
            p.terminate()

        return devices

    def set_device(self, device_id: Optional[int], is_loopback: bool = True):
        was_running = self._running
        if was_running:
            self.stop()
        self.selected_device_id = device_id
        self.is_loopback = is_loopback
        if was_running:
            self.start()

    def _get_pattern_mode_info(self) -> Tuple[bool, int]:
        """
        Determines if the active mode is an addressable IC multi-color running pattern or beat rhythm line.
        Returns (is_pattern, hardware_mode_cmd_id).
        cmd == -1: Dynamic VU Rhythm Lamp Bar (modulates active strip length via symphony points).
        cmd == 103: Mode 103 7-Color Running (segmented colored lines with distinct black unlit gaps).
        cmd == 23: Mode 23 7-Color Tail (Meteor Tail chaser trailing into black background).
        cmd == 81: Mode 81 7-Color Race (High-speed racing dots over black background).
        cmd == 1: Mode 1 Magic Forward (continuous rainbow rolling start to end).
        cmd == 2: Mode 2 Magic Back (continuous rainbow rolling end to start).
        """
        m = self.mode.lower()
        if "beat line" in m or "rhythm lamp" in m or "lamp" in m or "vu" in m:
            return True, -1   # Dynamic VU rhythm lamp bar (grow/shrink line using symphony points)
        elif "tail" in m or "meteor" in m:
            return True, 23   # Mode 23: 7-Color Tail (Meteor chaser trailing into black)
        elif "race" in m:
            return True, 81   # Mode 81: 7-Color Race (Racing chasers over black)
        elif "black" in m or "running" in m or "run" in m:
            return True, 103  # Mode 103: 7-Color Running (Segmented colored lines with distinct black gaps!)
        elif "reverse" in m or "back" in m:
            return True, 2    # Mode 2: Magic Back (multi-color line rolls end to start)
        elif "rolling" in m or "forward" in m:
            return True, 1    # Mode 1: Magic Forward (continuous rainbow rolling start to end)
        return False, 0

    def set_mode(self, mode_name: str):
        if self._pattern_active and mode_name != self.mode:
            self._pattern_active = False
        self.mode = mode_name

    def set_base_color(self, r: int, g: int, b: int):
        self.base_color = (r, g, b)

    def set_sensitivity(self, sens: float):
        self.sensitivity = max(0.1, min(4.0, float(sens)))

    def set_master_brightness(self, level: float):
        """Sets the maximum ceiling brightness for audio sync (0.05 to 1.0)."""
        self.master_brightness = max(0.05, min(1.0, float(level)))

    def start(self):
        if self._running:
            return
        self._running = True
        self._last_sent_rgb = (-1, -1, -1)
        self._pattern_active = False
        self._last_sent_speed = -1
        self._last_speed_time = 0.0
        self._last_sent_points = 100
        self._last_points_time = 0.0
        self._smooth_vol = 0.0
        self._recent_bass_history.clear()
        self._thread = threading.Thread(target=self._audio_capture_worker, name="AudioCaptureThread", daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._pattern_active:
            self._pattern_active = False
            if self.ble.is_connected():
                if self._last_sent_points != 100:
                    self.ble.set_symphony_points(100)
                    self._last_sent_points = 100
                self.ble.send_stream_frame(0, 0, 0, use_music_opcode=False)
        self.ble.clear_stream()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        self._smooth_vol = 0.0
        if self.on_status_change:
            self.on_status_change(False, "Audio sync stopped.")

    def is_running(self) -> bool:
        return self._running

    def _audio_capture_worker(self):
        """Worker thread that continuously reads audio buffers and drives neon colors at high brightness."""
        p = pyaudio.PyAudio()
        stream = None
        try:
            device_info = None

            # 1. If Auto or not specified, use active default WASAPI loopback device
            if self.selected_device_id is None or self.selected_device_id == -1:
                try:
                    if hasattr(p, "get_default_wasapi_loopback"):
                        device_info = p.get_default_wasapi_loopback()
                except Exception as ex:
                    logger.debug(f"Default loopback lookup error: {ex}")

            # 2. Specific device lookup
            if device_info is None and self.selected_device_id is not None and self.selected_device_id >= 0:
                try:
                    device_info = p.get_device_info_by_index(self.selected_device_id)
                except Exception:
                    device_info = None

            # 3. Fallback: match by default output name
            if device_info is None:
                try:
                    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
                    def_out_idx = wasapi_info["defaultOutputDevice"]
                    def_out = p.get_device_info_by_index(def_out_idx)
                    if hasattr(p, "get_loopback_device_info_generator"):
                        for loopback in p.get_loopback_device_info_generator():
                            if def_out["name"] in loopback["name"]:
                                device_info = loopback
                                break
                except Exception as ex:
                    logger.debug(f"WASAPI fallback error: {ex}")

            if device_info is None:
                if self.on_status_change:
                    self.on_status_change(False, "No playback device found.")
                return

            channels = int(device_info.get("maxInputChannels", 2))
            rate = int(device_info.get("defaultSampleRate", 48000))
            device_idx = device_info["index"]

            # Open 16-bit PCM audio stream with small buffer for minimum latency
            chunk_size = 1024
            stream = p.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=device_idx,
                frames_per_buffer=chunk_size,
            )

            if self.on_status_change:
                self.on_status_change(True, f"Capturing: {device_info['name']}")

            last_sound_time = time.time()
            bytes_per_sample = 2 * channels
            needed_bytes = chunk_size * bytes_per_sample

            while self._running:
                try:
                    # 1. Read a block of audio frames synchronously for steady ~47 FPS pacing
                    try:
                        raw_data = stream.read(chunk_size, exception_on_overflow=False)
                    except Exception as e:
                        time.sleep(0.015)
                        continue

                    if not raw_data or len(raw_data) < needed_bytes:
                        time.sleep(0.01)
                        continue

                    # Convert to numpy array
                    raw = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)
                    if len(raw) == 0:
                        time.sleep(0.01)
                        continue

                    if channels > 1:
                        # Downmix stereo to mono
                        raw = raw.reshape(-1, channels).mean(axis=1)

                    # 2. Remove DC Offset (crucial for accurate zero-noise measurement)
                    samples = raw - np.mean(raw)

                    # 3. Compute RMS Amplitude
                    rms = float(np.sqrt(np.mean(samples ** 2)))

                    # 4. Realistic Noise Gate
                    # In WASAPI Loopback, pure digital idle is < 30. Any music/sound is > 150.
                    noise_floor = 60.0 if self.is_loopback else 250.0
                    if rms < noise_floor:
                        raw_vol = 0.0
                    else:
                        # Normalize volume above the noise floor
                        raw_vol = float((rms - noise_floor) / 7500.0) * self.sensitivity
                        raw_vol = max(0.0, min(1.0, raw_vol))

                    now_t = time.time()
                    if raw_vol > 0.008:
                        last_sound_time = now_t

                    # 5. Fast Attack, Smooth Musical Decay
                    # Prevents stuttering / jumping / turning off between beats or during bridges
                    if raw_vol > self._smooth_vol:
                        self._smooth_vol = (self._smooth_vol * 0.35) + (raw_vol * 0.65)
                    else:
                        self._smooth_vol = (self._smooth_vol * 0.88) + (raw_vol * 0.12)
                        if self._smooth_vol < 0.005:
                            self._smooth_vol = 0.0

                    vol = self._smooth_vol
                    mb = self.master_brightness
                    is_pat, target_cmd = self._get_pattern_mode_info()

                    # Sound is considered active if audio was heard within the last 1.2s grace window
                    is_sound_active = (now_t - last_sound_time < 1.2) or (vol > 0.01)

                    # 6. Silence Handling: ONLY when silence is sustained for >= 1.2 seconds
                    if not is_sound_active:
                        if is_pat:
                            if self._pattern_active:
                                self._pattern_active = False
                                self._last_sent_rgb = (0, 0, 0)
                                if self.ble.is_connected():
                                    if target_cmd == -1 and self._last_sent_points != 100:
                                        self.ble.set_symphony_points(100)
                                        self._last_sent_points = 100
                                    self.ble.send_stream_frame(0, 0, 0, use_music_opcode=False)
                            if self.on_level:
                                self.on_level(0.0, 0, 0, 0)
                            time.sleep(0.015)
                            continue
                        else:
                            r, g, b = 0, 0, 0
                    else:
                        # Active Sound Processing: Frequency decomposition & Beat detection
                        if len(samples) >= 64:
                            fft_data = np.abs(np.fft.rfft(samples))
                            num_bins = len(fft_data)
                            bass_end = max(1, int(num_bins * 0.10))    # ~0 to 240 Hz
                            mid_end = max(bass_end + 1, int(num_bins * 0.42))  # ~240 to 2500 Hz

                            bass = float(np.mean(fft_data[:bass_end])) if bass_end > 0 else 0.0
                            mids = float(np.mean(fft_data[bass_end:mid_end])) if mid_end > bass_end else 0.0
                            treb = float(np.mean(fft_data[mid_end:])) if num_bins > mid_end else 0.0
                        else:
                            bass = float(rms)
                            mids = float(rms)
                            treb = float(rms)

                        # Rolling average for beat onset detection
                        self._recent_bass_history.append(bass)
                        if len(self._recent_bass_history) > 16:
                            self._recent_bass_history.pop(0)
                        avg_bass = np.mean(self._recent_bass_history) if self._recent_bass_history else 1.0

                        is_beat = (bass > (avg_bass * 1.35)) and (now_t - self._last_beat_time > 0.16) and (vol > 0.08)
                        if is_beat:
                            self._last_beat_time = now_t
                            self._color_index = (self._color_index + 1) % len(VIBRANT_PALETTE)
                            self._curr_target_color = list(VIBRANT_PALETTE[self._color_index])

                        if is_pat:
                            # -------------------------------------------------------------
                            # ADDRESSABLE IC MODES (Rolling with Black Gaps, Tail, Race, etc.)
                            # Keeps running continuously without stopping or stuttering!
                            # -------------------------------------------------------------
                            if not self._pattern_active:
                                self._pattern_active = True
                                self._last_sent_rgb = (255, 255, 255)
                                if self.ble.is_connected():
                                    self.ble.set_brightness(int(mb * 100))
                                    if target_cmd == -1:
                                        self.ble.set_mode(199)
                                        self.ble.set_speed(80)
                                        init_pts = max(8, min(100, int(8 + math.pow(vol, 0.70) * 92)))
                                        self.ble.set_symphony_points(init_pts)
                                        self._last_sent_points = init_pts
                                        self._last_points_time = now_t
                                    else:
                                        if self._last_sent_points != 100:
                                            self.ble.set_symphony_points(100)
                                            self._last_sent_points = 100
                                        self.ble.set_mode(target_cmd)
                                        init_spd = int(45 + (vol * 55))
                                        self.ble.set_speed(init_spd)
                                        self._last_sent_speed = init_spd
                                        self._last_speed_time = now_t

                            if target_cmd == -1:
                                # Feature 2: Rhythm Lamp Bar (modulate symphony points)
                                pts = max(8, min(100, int(8 + math.pow(vol, 0.70) * 92)))
                                if is_beat:
                                    pts = min(100, pts + 20)

                                if (abs(pts - self._last_sent_points) >= 4 and (now_t - self._last_points_time >= 0.035)) or (now_t - self._last_points_time >= 0.25):
                                    self._last_sent_points = pts
                                    self._last_points_time = now_t
                                    if self.ble.is_connected():
                                        self.ble.set_symphony_points(pts)
                            else:
                                # Feature 1: Mode 103 (Rolling with Black Gaps) & other IC modes
                                # Dynamically modulate speed with volume & beats while strip runs continuously!
                                desired_spd = int(45 + (vol * 55))
                                if is_beat:
                                    desired_spd = min(100, desired_spd + 25)

                                if abs(desired_spd - self._last_sent_speed) >= 8 and (now_t - self._last_speed_time >= 0.15):
                                    self._last_sent_speed = desired_spd
                                    self._last_speed_time = now_t
                                    if self.ble.is_connected():
                                        self.ble.set_speed(desired_spd)

                            # UI visualizer: rainbow cycling roll for VU display
                            self._hue_offset = (self._hue_offset + 0.020 + vol * 0.03) % 1.0
                            vu_rgb = [int(c * 255) for c in colorsys.hsv_to_rgb(self._hue_offset, 1.0, 1.0)]
                            if self.on_level:
                                self.on_level(max(vol, 0.08), vu_rgb[0], vu_rgb[1], vu_rgb[2])

                            time.sleep(0.015)
                            continue

                        # -------------------------------------------------------------
                        # ALGORITHM 1: Beat Color Jump (7-Color High-Energy Spectrum)
                        # Full 100% saturation and brightness, leaping across vibrant colors on beats!
                        # -------------------------------------------------------------
                        if "Beat Color Jump" in self.mode:
                            # Smoothly morph towards the active target color
                            for i_c in range(3):
                                self._curr_display_color[i_c] += (self._curr_target_color[i_c] - self._curr_display_color[i_c]) * 0.45

                            r = int(self._curr_display_color[0] * mb)
                            g = int(self._curr_display_color[1] * mb)
                            b = int(self._curr_display_color[2] * mb)

                        # -------------------------------------------------------------
                        # ALGORITHM 2: Dynamic Rainbow Spectrum
                        # Full continuous 360° HSV hue rotation modulated by music tempo & energy
                        # -------------------------------------------------------------
                        elif "Dynamic Rainbow Spectrum" in self.mode or "Rainbow" in self.mode:
                            self._hue_offset = (self._hue_offset + 0.012 + (vol * 0.040)) % 1.0
                            rgb_f = colorsys.hsv_to_rgb(self._hue_offset, 1.0, mb)
                            r, g, b = int(rgb_f[0] * 255), int(rgb_f[1] * 255), int(rgb_f[2] * 255)

                        # -------------------------------------------------------------
                        # ALGORITHM 3: Frequency Tri-Split (Bass / Mid / High)
                        # Heavy bass kicks = Crimson, Mids/Vocals = Electric Cyan, Highs = Gold
                        # -------------------------------------------------------------
                        elif "Frequency Tri-Split" in self.mode:
                            total_e = bass * 1.6 + mids * 1.0 + treb * 1.2 + 1e-5
                            w_bass = (bass * 1.6) / total_e
                            w_mids = (mids * 1.0) / total_e
                            w_treb = (treb * 1.2) / total_e

                            # Bass: Crimson (255, 0, 45) | Mid: Cyan (0, 240, 255) | Treble: Gold (255, 215, 0)
                            calc_r = (255 * w_bass) + (0 * w_mids) + (255 * w_treb)
                            calc_g = (0 * w_bass) + (240 * w_mids) + (215 * w_treb)
                            calc_b = (45 * w_bass) + (255 * w_mids) + (0 * w_treb)

                            r = int(min(255, calc_r) * mb)
                            g = int(min(255, calc_g) * mb)
                            b = int(min(255, calc_b) * mb)

                        # -------------------------------------------------------------
                        # ALGORITHM 4: Rolling Wave Simulation
                        # High-speed complementary phase shifts that roll across color pairs with rhythm
                        # -------------------------------------------------------------
                        elif "Rolling Wave" in self.mode:
                            phase = (time.time() * (2.8 + vol * 3.0)) % (math.pi * 2)
                            blend = (math.sin(phase) + 1.0) / 2.0
                            # Cross-fade between Hot Pink (255, 0, 140) and Electric Cyan (0, 240, 255)
                            r = int(((255 * blend) + (0 * (1.0 - blend))) * mb)
                            g = int(((0 * blend) + (240 * (1.0 - blend))) * mb)
                            b = int(((140 * blend) + (255 * (1.0 - blend))) * mb)

                        # -------------------------------------------------------------
                        # ALGORITHM 5: Bass Strobe & Energy
                        # Clean calm background with punchy 100% full-brightness flashes on drops
                        # -------------------------------------------------------------
                        elif "Bass Strobe" in self.mode:
                            if is_beat or vol > 0.70:
                                self._strobe_decay = 1.0

                            if self._strobe_decay > 0.05:
                                flash = self._strobe_decay * mb
                                r = int(255 * flash)
                                g = int(255 * flash)
                                b = int(255 * flash)
                                self._strobe_decay *= 0.82
                            else:
                                r = int(self.base_color[0] * 0.45 * mb)
                                g = int(self.base_color[1] * 0.45 * mb)
                                b = int(self.base_color[2] * 0.45 * mb)

                        # -------------------------------------------------------------
                        # ALGORITHM 6: Cyberpunk Neon
                        # High-energy alternating Neon Cyan and Hot Pink
                        # -------------------------------------------------------------
                        elif "Cyberpunk" in self.mode:
                            blend = min(1.0, max(0.0, vol * 1.6))
                            r = int(((255 * blend) + (0 * (1.0 - blend))) * mb)
                            g = int(((0 * blend) + (240 * (1.0 - blend))) * mb)
                            b = int(((180 * blend) + (255 * (1.0 - blend))) * mb)

                        # -------------------------------------------------------------
                        # ALGORITHM 7: Pulse Beat (Single Color)
                        # Pulses user's selected base color at high brightness
                        # -------------------------------------------------------------
                        else:
                            br = max(0.40, min(1.0, 0.40 + vol * 0.60)) * mb
                            r = int(self.base_color[0] * br)
                            g = int(self.base_color[1] * br)
                            b = int(self.base_color[2] * br)

                    # Clamp strictly to valid 8-bit bounds
                    r = max(0, min(255, int(r)))
                    g = max(0, min(255, int(g)))
                    b = max(0, min(255, int(b)))

                    # 6. Transmit to light over BLE
                    # Use standard color packets (use_music_opcode=False) for maximum blinding 100% LED output!
                    now = time.time()
                    elapsed = now - self._last_send_time
                    is_changed = (r, g, b) != self._last_sent_rgb

                    # Instant cutoff on silence, or rate-limited streaming updates during playback
                    if is_changed and (r, g, b) == (0, 0, 0):
                        self._last_send_time = now
                        self._last_sent_rgb = (0, 0, 0)
                        if self.ble.is_connected():
                            self.ble.send_stream_frame(0, 0, 0, use_music_opcode=False)
                    elif elapsed >= self._min_send_interval and (is_changed or elapsed >= 1.5):
                        self._last_send_time = now
                        self._last_sent_rgb = (r, g, b)
                        if self.ble.is_connected():
                            self.ble.send_stream_frame(r, g, b, use_music_opcode=False)

                    # Visual feedback to UI VU meter
                    if self.on_level:
                        self.on_level(vol, r, g, b)

                except Exception as e:
                    logger.debug(f"Stream read error: {e}")
                    time.sleep(0.02)

        except Exception as e:
            logger.error(f"Failed to run audio capture worker: {e}")
            if self.on_status_change:
                self.on_status_change(False, f"Audio error: {e}")
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            p.terminate()
            self._running = False
