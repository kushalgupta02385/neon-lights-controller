# ⚡ Neon Lights Studio Pro (React Desktop Edition)

A high-performance, modern Windows desktop controller application for **MagicLantern** compatible Bluetooth Low Energy (BLE) addressable IC Neon Rope Lights (`MELK-OA10`, `MELK-*`, `ELK-*`).

Built with a **React 18 Cyberpunk Glassmorphism UI** hosted inside a native Microsoft Edge WebView2 window, powered by an asynchronous **Python backend**, direct **Windows WASAPI Digital Audio Loopback**, and low-latency **WinRT Bluetooth LE**.

---

## 🌟 Key Highlights

- **React 18 Modern Interface**: Clean Cyberpunk Glassmorphism theme with neon cyan, hot pink, and gold accents. Fully offline with zero external internet dependencies.
- **Direct PC Audio & Game Sync**: Internal Windows WASAPI Loopback capture listens directly to your digital audio stream before it reaches speakers or headphones. Zero room mic noise, microsecond latency.
- **Custom Rolling & Rhythm Modes**:
  - `🌀 ROLLING W/ BLACK GAPS`: Multi-color line sequences separated by black gaps running smoothly across the strip.
  - `📊 BEAT LINES (RHYTHM LAMP)`: Dynamic sound-reactive meter simulating an addressable rhythm lamp strip.
- **213 Hardware Dynamic IC Modes**: Instant search and category filtering across all 213 hardware IC patterns.
- **Dual CCT White Balance**: Warm white (2700K) to Cold white (6500K) balance slider.
- **Interactive HSV Color Wheel**: 2D HTML5 canvas color picker with crosshair and 16 quick preset color chips.
- **Physical Controller Mic Support**: Hardware microphone controls with sensitivity tuning and 8 built-in EQ presets.
- **Addressable IC Strip Calibration**: Symphony points slider (1 to 1024 LEDs) and 6 RGB pin sequence permutations.
- **Zero-Configuration Auto-Connect**: Automatically discovers and connects to your `MELK-OA10 44` (`BE:69:58:01:CC:00`) strip on startup.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│               Microsoft Edge WebView2                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │             React 18 Glassmorphism UI             │  │
│  │   • 2D Canvas HSV Color Wheel                    │  │
│  │   • 213 Dynamic Modes Gallery with Search        │  │
│  │   • Live 60 FPS Audio VU Visualizer Meter        │  │
│  │   • Bluetooth Device Manager & Strip Settings    │  │
│  └──────────────────────────────────────────────────┘  │
└───────────────────────────┬────────────────────────────┘
                            │ REST JSON API (127.0.0.1:8765)
┌───────────────────────────▼────────────────────────────┐
│                  Python Backend Engine                 │
│  ┌───────────────────────┐  ┌───────────────────────┐  │
│  │  pyaudiowpatch WASAPI │  │   Bleak WinRT GATT    │  │
│  │    Audio Loopback     │  │   Bluetooth LE Engine │  │
│  │   • 12 Reactive Modes │  │  • Auto-Connect Logic │  │
│  │   • Silence Hold Gate │  │  • FIFO Command Queue │  │
│  │   • 60 FPS FFT Stream │  │  • Rate-Limited Safe  │  │
│  └───────────────────────┘  └───────────────────────┘  │
└───────────────────────────┬────────────────────────────┘
                            │ Bluetooth LE GATT Packets
                            ▼
               💡 Addressable Neon Rope Light
             (MELK-OA10 44 / BE:69:58:01:CC:00)
```

---

## 🚀 Getting Started

### Option 1: Standalone Windows Executable (Recommended)

No Python, Node.js, or external dependencies required. Simply launch:

```powershell
.\NeonLightsController.exe
```

The application will start, open a native window, and automatically connect to your neon strip within 3 seconds.

---

### Option 2: Running from Python Source

#### 1. Requirements
- Windows 10 or Windows 11
- Python 3.10+
- Microsoft Edge WebView2 Runtime (installed by default on Windows 10/11)

#### 2. Install Python Dependencies
```powershell
pip install bleak pywebview pyaudiowpatch numpy
```

#### 3. Run Application
```powershell
python main.py
```

---

## 🎮 Game & Music Audio Sync (How It Works)

### 1. Digital Loopback Audio Capture
Unlike mobile apps that rely on phone microphones (which capture ambient room noise, typing, or fan sounds), this desktop app taps directly into Windows's **WASAPI Digital Audio Stream**.

- **Hardware Setup**: Plug the neon strip's USB power cable into any 5V USB port (laptop, monitor, or USB adapter).
- **Sound Source**: Audio played by games (Steam, Epic, Cyberpunk 2077, Valorant, GTA V, Forza) or media players (Spotify, YouTube, Discord, VLC) is captured digitally with zero latency before being sent to your speakers, headphones, or HDMI monitor.
- **Intelligent Silence Hold Gate**: A built-in 1.2-second grace hold window keeps the lighting steady during quiet game moments or pauses, preventing annoying blinking or stuttering between tracks.

---

## ⚙️ Project File Structure

```
c:\Work\Neon-Lights\
├── NeonLightsController.exe   # Compiled single-file desktop binary (37.9 MB)
├── icon.ico                   # Application window icon
├── main.py                    # Entry point launching HTTP server & pywebview
├── NeonLightsController.spec  # PyInstaller packaging configuration
├── README.md                  # Complete documentation guide
├── FEATURE.md                 # Detailed exhaustive feature catalog
├── LIGHT_CONTROLLER_GUIDE.md  # Protocol and hardware reverse engineering guide
│
├── neon_controller/           # Main application package
│   ├── ble_manager.py         # Asynchronous Bleak BLE GATT driver & FIFO queue
│   ├── audio_manager.py       # WASAPI loopback audio stream & 12 reactive modes
│   ├── protocol.py            # Hardware packet encodings & dynamic mode definitions
│   ├── server.py              # REST API & static web server (127.0.0.1:8765)
│   │
│   └── web/                   # 100% Offline React 18 frontend
│       ├── index.html         # HTML shell mounting React root
│       ├── style.css          # Cyberpunk glassmorphism design system
│       ├── app.jsx            # React 18 modular application components
│       └── vendor/            # Bundled offline dependencies (zero internet needed)
│           ├── react.production.min.js
│           ├── react-dom.production.min.js
│           └── babel.min.js
│
└── tests/                     # Automated regression test suite
    ├── test_all_features.py   # Protocol, packets, audio algorithms & hardware tests
    ├── test_react_server.py   # REST API endpoints & static asset delivery tests
    └── test_ui_components.py  # Audio loopback and UI logic unit tests
```

---

## 🧪 Testing & Verification

Run the full automated test suite (including live hardware tests if your light is nearby):

```powershell
python -m unittest tests/test_all_features.py tests/test_react_server.py
```

### Test Coverage:
- **28 Automated Tests**:
  - `test_all_features.py` (15 tests): Verifies power packets, RGB colors, brightness, speed, dynamic mode 103 black gaps, IC points, WASAPI loopback modes, controller mic settings, and physical hardware communication with `MELK-OA10 44`.
  - `test_react_server.py` (13 tests): Verifies offline React vendor file delivery, HTML shell, CSS, and all JSON REST endpoints (`/api/state`, `/api/power`, `/api/color`, `/api/brightness`, `/api/speed`, `/api/mode`, `/api/audio/*`, `/api/hw_mic/*`, `/api/points`, `/api/pin_sequence`, `/api/connect`).

---

## 📦 Building Standalone Executable

To rebuild the standalone `.exe` after making changes to the source:

```powershell
python -m PyInstaller NeonLightsController.spec --noconfirm
Copy-Item -Path "dist\NeonLightsController.exe" -Destination ".\NeonLightsController.exe" -Force
```

---

## 🔧 Bluetooth Troubleshooting

- **Make sure Bluetooth is ON** in Windows Settings.
- **Do not pair the light in Windows Bluetooth Settings**: Bleak communicates directly with the GATT service over BLE advertisement; Windows Bluetooth device pairing is not required.
- **One Connection at a Time**: The physical neon controller accepts only one active BLE connection. If another device (e.g. mobile app) is connected, disconnect it first.
- **Quick Connect Button**: If disconnected, click the **`⚡ Quick Connect to MELK-OA10 44`** button in the **Strip & Settings** tab or click the **`🔴 Disconnected (Click to Connect)`** status pill in the top header.
