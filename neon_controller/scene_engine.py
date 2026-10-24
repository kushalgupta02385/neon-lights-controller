"""
Software Scene & Ambient Animation Engine
Provides ultra-smooth 25-28 FPS procedural lighting scenes for all neon light controllers,
with bespoke animation curves for all 28 ambient scenes.
Fully supports MELK-OA and other controllers without hardware opcode 0x31.
"""

import colorsys
import math
import random
import threading
import time
from typing import Callable, Optional, Tuple

from .ble_manager import BLEManager


class SceneEngine:
    def __init__(self, ble_manager: BLEManager):
        self.ble = ble_manager
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._active_scene_name = ""
        self._active_scene_id = 1
        self._speed_multiplier = 1.0  # 0.2 to 3.0
        self._brightness = 1.0        # 0.05 to 1.0

        # UI callback on animated color change: on_frame(r, g, b)
        self.on_frame: Optional[Callable[[int, int, int], None]] = None

    def start_scene(self, scene_name: str, scene_id: int = 1, speed_pct: int = 80, brightness_pct: int = 100):
        """Starts animating the specified scene by ID and name."""
        self.stop()
        self._active_scene_name = scene_name
        self._active_scene_id = scene_id
        self._speed_multiplier = max(0.1, min(3.0, speed_pct / 50.0))
        self._brightness = max(0.05, min(1.0, brightness_pct / 100.0))
        self._running = True
        self._thread = threading.Thread(target=self._scene_worker, name="SceneEngineThread", daemon=True)
        self._thread.start()

    def set_speed(self, speed_pct: int):
        self._speed_multiplier = max(0.1, min(3.0, speed_pct / 50.0))

    def set_brightness(self, brightness_pct: int):
        self._brightness = max(0.05, min(1.0, brightness_pct / 100.0))

    def stop(self):
        """Stops the animation and clears any pending frames."""
        self._running = False
        self.ble.clear_stream()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.4)
        self._thread = None
        self._active_scene_name = ""

    def is_running(self) -> bool:
        return self._running

    def get_active_scene(self) -> str:
        return self._active_scene_name

    def _scene_worker(self):
        scene_id = self._active_scene_id
        scene_name = self._active_scene_name.lower().strip()
        t = 0.0
        fps_interval = 0.038  # ~26 FPS for smooth BLE transmission

        # Persistent state for dynamic simulations
        fw_color = [255, 255, 255]
        fw_intensity = 0.0
        fw_decay = 0.88

        lightning_timer = 0.0
        lightning_stage = 0

        star_twinkle_timer = 0.0
        star_flash = 0.0

        candle_noise = 0.8

        while self._running:
            t += fps_interval * self._speed_multiplier
            r, g, b = 255, 255, 255

            # 1. Sunrise (Warm dark amber -> glowing gold -> bright morning sun)
            if scene_id == 1 or "sunrise" in scene_name:
                progress = (math.sin(t * 0.3) + 1.0) / 2.0
                r = int((200 + 55 * progress) * self._brightness)
                g = int((30 + 190 * progress) * self._brightness)
                b = int((5 + 160 * (progress ** 2)) * self._brightness)

            # 2. Sunset (Crimson purple -> coral -> dusky violet)
            elif scene_id == 2 or "sunset" in scene_name:
                cycle = (math.sin(t * 0.35) + 1.0) / 2.0
                r = int((255 - 40 * cycle) * self._brightness)
                g = int((40 + 90 * (1.0 - cycle)) * self._brightness)
                b = int((190 * cycle + 20) * self._brightness)

            # 3. Birthday (Festive confetti party jumps across cheerful spectrum)
            elif scene_id == 3 or "birthday" in scene_name:
                step = int(t * 1.8) % 7
                palette = [
                    (255, 0, 120), (0, 240, 255), (255, 210, 0),
                    (0, 255, 120), (180, 0, 255), (255, 90, 0), (255, 255, 255)
                ]
                color = palette[step]
                r, g, b = int(color[0] * self._brightness), int(color[1] * self._brightness), int(color[2] * self._brightness)

            # 4. Candlelight (Cozy warm 2200K amber flickering flame)
            elif scene_id == 4 or "candle" in scene_name:
                candle_noise = 0.72 + (0.28 * math.sin(t * 4.2)) * math.cos(t * 2.7)
                candle_noise += random.uniform(-0.06, 0.06)
                candle_noise = max(0.4, min(1.0, candle_noise)) * self._brightness
                r = int(255 * candle_noise)
                g = int(125 * candle_noise)
                b = int(20 * candle_noise)

            # 5. Fireworks (Explosive bursts with organic decay)
            elif scene_id == 5 or "firework" in scene_name:
                if random.random() < (0.07 * self._speed_multiplier):
                    fw_intensity = 1.0
                    colors = [
                        (255, 30, 30), (30, 255, 60), (0, 230, 255),
                        (255, 0, 200), (255, 220, 0), (255, 255, 255), (255, 100, 0)
                    ]
                    fw_color = list(random.choice(colors))
                else:
                    fw_intensity *= fw_decay

                r = int(fw_color[0] * fw_intensity * self._brightness)
                g = int(fw_color[1] * fw_intensity * self._brightness)
                b = int(fw_color[2] * fw_intensity * self._brightness)

            # 6. Party (High-energy strobe & prism jumps)
            elif scene_id == 6 or "party" in scene_name:
                step = int(t * 3.5) % 6
                party_palette = [
                    (255, 0, 100), (0, 255, 220), (255, 240, 0),
                    (160, 0, 255), (0, 255, 80), (255, 50, 0)
                ]
                base = party_palette[step]
                r, g, b = int(base[0] * self._brightness), int(base[1] * self._brightness), int(base[2] * self._brightness)

            # 7. Dating (Intimate soft rose pink & velvet ruby breathing)
            elif scene_id == 7 or "dating" in scene_name:
                breath = (math.sin(t * 0.8) + 1.0) / 2.0
                r = int((200 + 55 * breath) * self._brightness)
                g = int((20 + 60 * breath) * self._brightness)
                b = int((70 + 80 * breath) * self._brightness)

            # 8. Starry sky (Deep midnight indigo with sparkling white stars)
            elif scene_id == 8 or "starry" in scene_name or "sky" in scene_name:
                star_twinkle_timer -= fps_interval
                if star_twinkle_timer <= 0:
                    star_flash = 1.0
                    star_twinkle_timer = random.uniform(0.6, 2.0) / self._speed_multiplier
                star_flash *= 0.82
                r = int((15 + 240 * star_flash) * self._brightness)
                g = int((20 + 235 * star_flash) * self._brightness)
                b = int((65 + 190 * star_flash) * self._brightness)

            # 9. Romantic (Heartbeat double-pulse in ruby & passionate magenta)
            elif scene_id == 9 or "romantic" in scene_name:
                phase = (t * 1.5) % 1.0
                if phase < 0.15:
                    hb = math.sin(phase / 0.15 * math.pi)
                elif 0.25 < phase < 0.40:
                    hb = math.sin((phase - 0.25) / 0.15 * math.pi) * 0.7
                else:
                    hb = 0.15
                hb = max(0.15, min(1.0, hb)) * self._brightness
                r = int(255 * hb)
                g = int(25 * hb)
                b = int((100 + 70 * math.sin(t * 0.5)) * hb)

            # 10. Disco (Retro 80s neon cycle)
            elif scene_id == 10 or "disco" in scene_name:
                step = int(t * 2.8) % 5
                disco_cols = [
                    (0, 240, 255), (255, 0, 180), (255, 230, 0),
                    (0, 255, 100), (170, 0, 255)
                ]
                col = disco_cols[step]
                r, g, b = int(col[0] * self._brightness), int(col[1] * self._brightness), int(col[2] * self._brightness)

            # 11. Rainbow (Silky smooth continuous hue sweep)
            elif scene_id == 11 or "rainbow" in scene_name:
                hue = (t * 0.12) % 1.0
                rgb_f = colorsys.hsv_to_rgb(hue, 1.0, self._brightness)
                r, g, b = int(rgb_f[0] * 255), int(rgb_f[1] * 255), int(rgb_f[2] * 255)

            # 12. Movie (Cinematic warm ambient backlighting)
            elif scene_id == 12 or "movie" in scene_name:
                breathe = (math.sin(t * 0.4) + 1.0) / 2.0
                r = int((200 + 40 * breathe) * self._brightness * 0.7)
                g = int((130 + 35 * breathe) * self._brightness * 0.7)
                b = int((40 + 20 * breathe) * self._brightness * 0.7)

            # 13. Christmas (Festive holly red, emerald green, champagne gold)
            elif scene_id == 13 or "christmas" in scene_name:
                phase = (t * 0.4) % 3.0
                if phase < 1.0:
                    r, g, b = 255, 20, 25  # Holly red
                elif phase < 2.0:
                    r, g, b = 20, 220, 45  # Pine green
                else:
                    r, g, b = 255, 215, 45  # Golden star
                r, g, b = int(r * self._brightness), int(g * self._brightness), int(b * self._brightness)

            # 14. Flowing (Slow chromatic oceanic liquid drift)
            elif scene_id == 14 or "flowing" in scene_name:
                hue = 0.5 + 0.25 * math.sin(t * 0.3)  # Cyan to Blue to Violet
                rgb_f = colorsys.hsv_to_rgb(hue % 1.0, 0.95, self._brightness)
                r, g, b = int(rgb_f[0] * 255), int(rgb_f[1] * 255), int(rgb_f[2] * 255)

            # 15. Sleeping (Ultra-dim warm amber/crimson fading nightlight)
            elif scene_id == 15 or "sleep" in scene_name:
                breath = (math.sin(t * 0.2) + 1.0) / 2.0
                level = (0.2 + 0.25 * breath) * self._brightness
                r = int(255 * level)
                g = int(80 * level)
                b = int(10 * level)

            # 16. Ocean (Deep marine swells & tropical turquoise)
            elif scene_id == 16 or "ocean" in scene_name:
                wave = (math.sin(t * 0.45) + 1.0) / 2.0
                r = int((10 + 30 * wave) * self._brightness)
                g = int((90 + 130 * wave) * self._brightness)
                b = int((190 + 65 * (1.0 - wave)) * self._brightness)

            # 17. Forest (Lush evergreen, moss, sunlit emerald)
            elif scene_id == 17 or "forest" in scene_name:
                canopy = (math.sin(t * 0.5) + 1.0) / 2.0
                r = int((20 + 50 * canopy) * self._brightness)
                g = int((170 + 80 * canopy) * self._brightness)
                b = int((30 + 40 * (1.0 - canopy)) * self._brightness)

            # 18. Reading (Balanced 4500K neutral white for eye comfort)
            elif scene_id == 18 or "reading" in scene_name:
                r = int(255 * self._brightness)
                g = int(220 * self._brightness)
                b = int(180 * self._brightness)

            # 19. Working (Energizing 6000K crisp daylight white)
            elif scene_id == 19 or "working" in scene_name:
                r = int(240 * self._brightness)
                g = int(245 * self._brightness)
                b = int(255 * self._brightness)

            # 20. Dazzle (Prismatic sparkling shifts)
            elif scene_id == 20 or "dazzle" in scene_name:
                hue = (t * 0.45) % 1.0
                rgb_f = colorsys.hsv_to_rgb(hue, 1.0, self._brightness)
                r, g, b = int(rgb_f[0] * 255), int(rgb_f[1] * 255), int(rgb_f[2] * 255)

            # 21. Gentle (Soft pastel peach, lilac, mint breathing)
            elif scene_id == 21 or "gentle" in scene_name:
                hue = (0.75 + 0.3 * math.sin(t * 0.25)) % 1.0
                rgb_f = colorsys.hsv_to_rgb(hue, 0.45, self._brightness)
                r, g, b = int(rgb_f[0] * 255), int(rgb_f[1] * 255), int(rgb_f[2] * 255)

            # 22. Wedding (Champagne gold, pearl white, delicate blush)
            elif scene_id == 22 or "wedding" in scene_name:
                sway = (math.sin(t * 0.3) + 1.0) / 2.0
                r = int((255 - 20 * sway) * self._brightness)
                g = int((225 - 40 * sway) * self._brightness)
                b = int((170 + 50 * sway) * self._brightness)

            # 23. Snow (Crystalline icy blue & diamond-white shimmer)
            elif scene_id == 23 or "snow" in scene_name:
                frost = (math.sin(t * 0.6) + 1.0) / 2.0
                shimmer = random.uniform(0.9, 1.0)
                r = int((150 + 95 * frost) * shimmer * self._brightness)
                g = int((200 + 50 * frost) * shimmer * self._brightness)
                b = int(255 * shimmer * self._brightness)

            # 24. Fire (Roaring campfire flame fluctuations)
            elif scene_id == 24 or "fire" in scene_name:
                flame = (math.sin(t * 5.5) * 0.4 + 0.6) * 0.4 + random.uniform(0.5, 1.0) * 0.6
                r = int(255 * self._brightness)
                g = int(max(20, min(170, 50 + flame * 110)) * self._brightness)
                b = int(random.uniform(5, 25) * self._brightness)

            # 25. Lightning (Thunderstorm ambient twilight + multi-strike flashes)
            elif scene_id == 25 or "lightning" in scene_name:
                lightning_timer -= fps_interval
                if lightning_timer <= 0:
                    lightning_stage = random.choice([2, 3])
                    lightning_timer = random.uniform(1.8, 5.0) / self._speed_multiplier

                if lightning_stage > 0:
                    flash = random.choice([1.0, 0.85, 0.4])
                    r = int(255 * flash * self._brightness)
                    g = int(255 * flash * self._brightness)
                    b = int(255 * flash * self._brightness)
                    lightning_stage -= 1
                else:
                    r = int(12 * self._brightness)
                    g = int(16 * self._brightness)
                    b = int(55 * self._brightness)

            # 26. Valentine's Day (Passionate crimson, ruby, warm blush pink breathing)
            elif scene_id == 26 or "valent" in scene_name or "aurora" in scene_name:
                cycle = (math.sin(t * 0.9) + 1.0) / 2.0
                r = int(255 * self._brightness)
                g = int((15 + 65 * cycle) * self._brightness)
                b = int((70 + 90 * cycle) * self._brightness)

            # 27. Halloween (Jack-o'-Lantern pumpkin orange, witch purple, slime green shifts)
            elif scene_id == 27 or "hallow" in scene_name or "cyber" in scene_name:
                phase = (t * 0.5) % 3.0
                if phase < 1.0:
                    # Pumpkin Orange
                    r, g, b = 255, 95, 0
                elif phase < 2.0:
                    # Witch Purple
                    r, g, b = 140, 0, 220
                else:
                    # Slime Green
                    r, g, b = 30, 240, 20
                r, g, b = int(r * self._brightness), int(g * self._brightness), int(b * self._brightness)

            # 28. Warning (Emergency amber beacon strobe alert)
            elif scene_id == 28 or "warn" in scene_name or "pulse" in scene_name:
                strobe = 1.0 if (int(t * 4.5) % 2 == 0) else 0.05
                r = int(255 * strobe * self._brightness)
                g = int(80 * strobe * self._brightness)
                b = 0

            # Fallback
            else:
                hue = (t * 0.1) % 1.0
                rgb_f = colorsys.hsv_to_rgb(hue, 0.95, self._brightness)
                r, g, b = int(rgb_f[0] * 255), int(rgb_f[1] * 255), int(rgb_f[2] * 255)

            # Clamp
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))

            # Send standard static color packets (byte7=0x10) for maximum full-strip brightness & visual pop
            if self.ble.is_connected():
                self.ble.send_stream_frame(r, g, b, use_music_opcode=False)

            if self.on_frame:
                self.on_frame(r, g, b)

            time.sleep(fps_interval)
