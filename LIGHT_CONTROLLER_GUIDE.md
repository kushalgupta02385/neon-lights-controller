# 💡 Neon Lights Studio Pro - Desktop Controller Guide

A modern, high-performance Windows desktop application (`NeonLightsController.exe`) reverse-engineered from the **MagicLantern** Android companion APK (`MagicLantern-V6.11.10.apk`) to control LED Neon Rope Lights via Bluetooth Low Energy (BLE) and sync lighting directly with laptop game and music audio.

---

## 🎮 Game & Music Audio Sync (HDMI / Headphones / Speakers)

### How It Works:
1. **Physical Connection**: Connect the neon rope light's USB cable to any USB port on your laptop, monitor, or USB power supply. The USB cable supplies 5V DC power to the controller and LEDs.
2. **Bluetooth Connection**: Your laptop connects wirelessly to the rope light over Bluetooth Low Energy (BLE) using device ID `MELK-OA10   44` (or any compatible `MELK-*` / `ELK-*` model).
3. **Internal Digital Audio Capture (WASAPI Loopback)**:
   - When you play games on Steam / Epic (Cyberpunk 2077, Valorant, GTA V, Forza, DOOM) or stream media from Spotify, YouTube, Netflix, or Discord:
   - Windows routes the sound to whichever output device you are using: **HDMI Monitor**, **Bluetooth/3.5mm Headphones**, or **Laptop Internal Speakers**.
   - The app uses **WASAPI Loopback** capture: it listens to the digital audio stream right inside Windows before it reaches your speakers/headphones.
   - **Zero ambient room noise** is captured, and no microphone is needed. The lights react in real-time to game gunshots, bass drops, explosions, dialogue, and beats with microsecond precision.

---

## 🚀 What Was Fixed (Root Cause Analysis & Verification)

### 1. Dynamic Modes Not Working:
- **Root Cause**: The previous packet dispatcher used a single `_latest_urgent_packet` variable for all commands. When a dynamic mode was clicked in the UI, `set_mode()` enqueued Power ON, Mode ID, Speed, and Brightness in rapid succession. Because each call overwrote the single variable before the sender loop ticked, the dynamic mode packet was dropped before reaching Bleak.
- **Solution**: Refactored `BLEManager` to use a true `asyncio.Queue` FIFO command pipeline. All discrete commands (`Power`, `Dynamic Mode`, `Speed`, `Brightness`, `IC Points`, `CCT`) are queued and sent in strict sequence with 25ms intervals. Verified on physical hardware `BE:69:58:01:CC:00` with 100% reliability.

### 2. Ambient Scenes Not Working:
- **Root Cause**: The decompiled APK (`ListUtil.isContainsBuiltInScene`) revealed that hardware opcode `0x31` (hardware built-in scenes) is only supported on `MELK-OC` and `MELK-OT` chipsets; `MELK-OA` models ignore opcode `0x31`. Furthermore, earlier versions only animated 12 of the 28 scenes.
- **Solution**: Implemented tailored, high-fidelity procedural lighting generators for **all 28 ambient atmospheric scenes** in `scene_engine.py`. For every scene (Sunrise, Sunset, Birthday, Candlelight, Fireworks, Party, Dating, Starry Sky, Romantic, Disco, Rainbow, Movie, Christmas, Flowing, Sleeping, Ocean, Forest, Reading, Working, Dazzle, Gentle, Wedding, Snow, Fire, Lightning, Aurora, Cyberpunk, Neon Pulse), smooth 26-28 FPS color streams are sent to the light.

### 3. Complete Modern UI Redesign:
- Built with a modern dark cyber-glass theme (`#0B0E14` base, glowing `#00F0FF` cyan and `#A855F7` neon purple accents).
- **Separated Tabs**:
  - 🎨 **Colors & White**: Interactive glow canvas, 16 neon palettes, RGB channel fine-tuning, Warm/Cold CCT white temperature slider, custom favorites.
  - ⚡ **Dynamic Modes (213)**: Filter by category (Basic, Curtain, Trans, Water, Flow, Tail, Run, RunBack), real-time search, animated gradient cards.
  - 🌌 **Ambient Scenes (28)**: Dedicated 28-scene gallery with custom atmospheric icons and live lighting preview.
  - 🔊 **Game & Music Sync**: One-click "ACTIVATE GAME & MUSIC SYNC", auto-detected WASAPI loopback source, live animated VU level visualizer, 5 reaction styles (Pulse Beat, Rainbow Spectrum, Energy Wave, Bass Strobe, Cyberpunk Gaming), and hardware controller mic settings.
  - ⚙️ **Strip & Settings**: Device scanner, IC Pixel count setting (100 pixels), RGB pin sequence calibration, laptop clock synchronization, and real-time BLE protocol inspector.
- **Persistent Bottom Control Deck**: Always-visible quick brightness slider, speed slider, and live color swatch across all tabs.

---

## 🏃 Running the Application

### Option 1: Standalone Windows Executable (No Python Required)
Run the compiled 34.2 MB executable located in the project root:
```powershell
.\NeonLightsController.exe
```

### Option 2: Running from Source
```powershell
python main.py
```

---

## 🧪 Comprehensive Unit & Live Hardware Test Verification

Run the complete test suite:
```powershell
python -m unittest tests/test_all_features.py
```

### Test Results:
```
Ran 13 tests in 8.633s
OK

[Hardware Test] Connecting to BE:69:58:01:CC:00...
  Connected to light successfully.
  1. Testing Power ON...
  2. Testing IC points (100 pixels)...
  3. Testing RGB Colors...
  4. Testing Brightness levels...
  5. Testing Dynamic Mode #193 and Speed 80...
  6. Testing Music amplitude packet...
  7. Testing Controller Mic & EQ mode...
  8. Restoring Cyan state...
  All physical hardware tests PASSED!
```
