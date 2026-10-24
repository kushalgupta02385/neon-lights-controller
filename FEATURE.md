# 💡 Neon Lights Studio Pro - Feature Catalog

An exhaustive guide and catalog of all features, capabilities, reactive algorithms, and hardware controls available in **Neon Lights Studio Pro**.

---

## 📋 Feature Overview Table

| Category | Feature | Description |
| :--- | :--- | :--- |
| **User Interface** | **React 18 Glassmorphism UI** | Modern dark theme (`#080A11`), neon cyan/pink/gold accents, frosted glass panels. |
| **User Interface** | **2D Canvas HSV Color Wheel** | Circular hue-saturation picker with interactive draggable crosshair. |
| **User Interface** | **Dual CCT White Balance** | Smooth Warm White (2700K) to Cold White (6500K) temperature adjustment. |
| **User Interface** | **16 Quick Preset Colors** | One-tap chips: Cyan, Purple, Magenta, Gold, Amber, Lime, Red, Blue, etc. |
| **User Interface** | **Persistent Bottom Deck** | Master Brightness (1–100%), Speed (1–100%), and live active color swatch. |
| **Audio Sync** | **WASAPI Loopback Capture** | Internal digital audio capture with zero mic noise and microsecond precision. |
| **Audio Sync** | **🌀 Rolling Lines (w/ Black Gaps)** | Multi-color lines separated by black gaps running smoothly along the strip. |
| **Audio Sync** | **📊 Beat Lines (Rhythm Lamp)** | Transients and bass-reactive bars expanding/contracting from the strip ends. |
| **Audio Sync** | **12 Reactive Algorithms** | Meteor, Energy Race, Rainbow Flow, Frequency Spectrum, Pulse Strobe, etc. |
| **Audio Sync** | **Silence Hold Grace Window** | 1.2s zero-latency hold prevents mid-track or quiet game scene stutter. |
| **Audio Sync** | **60 FPS Live VU Equalizer** | Animated Canvas meter showing real-time amplitude and frequency energy. |
| **Audio Sync** | **Audio Device Selector** | Choose between Auto Active Windows Default, Headphones, Speakers, or HDMI. |
| **Hardware Mic** | **Physical Controller Mic** | Enable/disable the physical microphone built into the USB controller box. |
| **Hardware Mic** | **8 Hardware EQ Modes** | Classical, Soft, Dynamic, Disco, Rock, Pop, Jazz, Ambient EQ profiles. |
| **Dynamic Modes**| **213 Hardware IC Modes** | Searchable library of all 213 hardware-programmed running light patterns. |
| **Dynamic Modes**| **Category Filtering** | Fast filter pills: `All`, `Run`, `Tail`, `Basic`, `Curtain`, `Trans`, `Water`, `Flow`, `RunBack`. |
| **Strip Settings**| **Symphony Points Slider** | Set active addressable LED pixel count from 1 to 1024 LEDs (default: 100). |
| **Strip Settings**| **6 RGB Pin Sequences** | Instant calibration for `RGB`, `RBG`, `GRB`, `GBR`, `BRG`, `BGR` wire order. |
| **Bluetooth LE** | **Startup Auto-Connect** | Automatically detects and pairs with `MELK-OA10 44` (`BE:69:58:01:CC:00`). |
| **Bluetooth LE** | **1-Click Quick Connect** | Instant connect buttons in both the header status pill and the Settings tab. |
| **Bluetooth LE** | **FIFO Command Queue** | Guaranteed in-order packet delivery with 25ms safe hardware pacing. |
| **Offline Mode** | **100% Offline Capability** | Bundled React 18, React-DOM, and Babel scripts — zero internet connection needed. |

---

## 🎨 1. Colors & White Tab

### 2D Canvas HSV Color Wheel
- **Interactive Radial Picker**: Renders a full 360° Hue and Saturation disc on an HTML5 canvas.
- **Draggable Crosshair**: Click or drag anywhere on the disc to instantly update the neon strip's RGB color.
- **Real-Time Coordinates**: Automatically computes normalized RGB values and transmits them over BLE with continuous dragging support.

### Dual CCT White Balance Slider
- **Range**: 2700K (Warm Cozy Amber White) to 6500K (Cool Crisp Daylight White).
- **Dual-Channel Protocol**: Sends hardware opcode `0x05` with dual warm/cold byte interpolation for natural white illumination.

### 16 Quick Neon Preset Chips
- One-click instant color switching:
  - `Neon Cyan` (`#00F0FF`)
  - `Electric Purple` (`#A855F7`)
  - `Hot Pink` (`#FF2A85`)
  - `Cyber Gold` (`#FFD700`)
  - `Laser Green` (`#05FFA1`)
  - `Sunset Orange` (`#FF7B00`)
  - `Deep Blue` (`#0055FF`)
  - `Crimson Red` (`#FF1744`)
  - And 8 additional modern pastel and vivid shades.

---

## 🔊 2. Game & Music Audio Reactive Engine

### Windows WASAPI Digital Loopback Capture
- **Internal Loopback**: Directly taps Windows Core Audio (WASAPI) playback buffers.
- **Microsecond Latency**: Reacts in real time to in-game gunshots, footsteps, bass drops, synth lines, and dialogue.
- **Zero Room Noise**: Captures audio digitally from your PC; completely immune to fan noise, keyboard typing, or room chatter.
- **Output Device Switching**: Dynamically switch capture between your active Windows default output, plugged-in headphones, laptop speakers, or external monitors.

### Specialized Audio Algorithms

#### 1. 🌀 Rolling Lines with Black Gaps (Mode 103 Hardware-Mapped)
- **Visual Effect**: Sequences of vivid multi-color line segments travel from start to end of the strip, separated by dark black gap intervals.
- **Dynamic Response**: Audio volume and transients modulate the flow speed and brightness of the running color segments.
- **1-Click Launch**: Dedicated prominent button on the Audio Tab.

#### 2. 📊 Beat Lines (Rhythm Lamp)
- **Visual Effect**: Simulates a physical addressable desktop rhythm light bar.
- **Dynamic Response**: Low-frequency kicks and mid-range beats cause color columns to shoot from the ends toward the center, decaying dynamically with volume.
- **1-Click Launch**: Dedicated prominent button on the Audio Tab.

#### 3. Additional WASAPI Reactive Modes (12 Total)
- **Meteor Tail**: High-speed audio-reactive comets leaving fading color trails.
- **Energy Race**: Racing energy pulses that accelerate during intense music drops.
- **Rainbow Flow**: Smooth chromatic spectrum shifting along the strip driven by audio energy.
- **Frequency Spectrum**: FFT band analysis mapping bass to reds, mids to greens/yellows, and highs to cyans/blues.
- **Pulse Beat**: Solid strip pulsing that matches drum kicks and beat transients.
- **Bass Strobe**: High-energy bass kick flashes for electronic and dance music.
- **Dynamic Wave**: Symmetrical wave pulses propagating outward from the center.
- **Calm Ambient**: Soft, gentle breathing illumination for movies and background study music.

### Audio Sensitivity Multiplier
- **Range**: `0.2x` (low sensitivity for loud games/movies) to `3.5x` (high sensitivity for quiet music).
- Adjusts the FFT amplitude threshold in real time without restarting the audio stream.

### Intelligent Silence Hold Grace Window
- **Zero-Stutter Playback**: A 1.2-second smooth hold window prevents the strip from shutting off or flickering during quiet game dialogue, track transitions, or breath pauses in music.

### 60 FPS Real-Time Canvas VU Equalizer
- Live animated graphic equalizer displaying frequency spectrum bars and peak amplitude level indicators reacting directly to laptop sound.

---

## 🎙️ 3. Physical Controller Microphone & Hardware EQ

For situations where laptop audio is not playing (e.g. room conversations or acoustic instruments), you can activate the microphone built directly into the physical USB controller box.

- **Hardware Mic Toggle**: Turns the physical controller mic on or off.
- **Hardware Sensitivity Slider**: Sets controller mic gain from `1%` to `100%`.
- **8 Hardware EQ Modes**:
  1. `Classical` (Balanced acoustic response)
  2. `Soft` (Gentle volume modulation)
  3. `Dynamic` (High contrast between loud and soft)
  4. `Disco` (Fast tempo rhythm flashes)
  5. `Rock` (Enhanced bass kick sensitivity)
  6. `Pop` (Vocal-centric mid-range response)
  7. `Jazz` (Smooth dynamic swell)
  8. `Ambient` (Slow color transitions)
- **Hardware Disarm**: Dedicated one-click button to cleanly disarm the hardware mic and restore normal digital operation.

---

## ⚡ 4. Dynamic Modes Gallery (213 Modes)

The strip controller features 213 built-in hardware IC running patterns, all organized and instantly accessible.

- **Instant Search**: Type any mode name or number to filter in real time.
- **Category Filter Tabs**:
  - `All`: Browse all 213 modes.
  - `Run`: Multi-color running segments and traveling dots.
  - `Tail`: Fading comet tails and meteor effects.
  - `Basic`: Solid alternating blocks and steady pulses.
  - `Curtain`: Curtain opening and closing effects.
  - `Trans`: Color crossfades and multi-color transitions.
  - `Water`: Flowing stream and waterfall effects.
  - `Flow`: Bi-directional and circular wave flows.
  - `RunBack`: Bouncing and rebounding runners.
- **Live Active Indicator**: Highlighted card border and indicator showing which mode is currently running.
- **Speed & Brightness Control**: Adjust the speed and brightness of any dynamic mode in real time.

*(Note: Ambient Scenes section was cleanly removed per user specification to streamline the interface).*

---

## ⚙️ 5. Strip Length & Calibration Settings

### Symphony Points Slider (IC Pixel Count)
- **Range**: 1 to 1024 points (default: 100).
- Configures how many addressable IC pixel points your light strip has. Ensures animations and running lines cover the entire physical length of your strip without stopping short or clipping.

### RGB Pin Sequencing Calibration
- Some manufacturers wire physical LED strips differently (`RGB`, `GRB`, `BRG`, etc.).
- The Settings tab provides 6 instant calibration buttons:
  - `RGB` (Standard)
  - `RBG`
  - `GRB` (Common on WS2812B strips)
  - `GBR`
  - `BRG`
  - `BGR`
- Immediately re-maps all color commands so clicking Red produces true Red on your physical strip.

---

## 📡 6. Bluetooth Low Energy (BLE) Engine

- **Windows WinRT GATT Client**: Communicates directly through Windows 10/11 native Bluetooth Low Energy APIs.
- **Automatic Startup Connect**: As soon as the application opens, it scans and automatically pairs with `MELK-OA10 44` (`BE:69:58:01:CC:00`).
- **Safety Fallback Timer**: Automatically attempts direct connection if initial BLE advertisement discovery takes longer than normal.
- **1-Click Quick Connect**:
  - Click the **`🔴 Disconnected (Click to Connect)`** status pill in the header to connect immediately.
  - Click **`⚡ Quick Connect to MELK-OA10 44`** in the Settings tab.
- **Nearby Device Discovery**: Scans for all nearby BLE devices and displays signal strength (RSSI in dBm) with glowing **`✨ NEON STRIP`** badges on detected MagicLantern lights.
- **FIFO Command Queue**: Commands (Power, Color, Mode, Speed, Brightness, IC Points) are sequenced through an asynchronous FIFO queue with 25ms spacing, completely preventing dropped packets or BLE buffer overflows.

---

## 🎛️ 7. Master System Controls

- **Glowing Master Power Button**: Located in the top header (`⏻ ON` / `⏻ OFF`). Gracefully shuts down audio sync, disarms microphones, and powers off the strip while preserving your last-used color and mode.
- **Master Brightness**: Slider located in the persistent bottom deck controlling overall light output from `1%` to `100%`.
- **Master Speed**: Slider located in the persistent bottom deck controlling dynamic mode and audio sync animation speed from `1%` to `100%`.

---

## 🔒 8. 100% Offline & Standalone

- **Zero Cloud / Zero Internet**: Runs entirely on your local machine. Does not send telemetry, require accounts, or fetch online assets.
- **Embedded Vendor Bundles**: React 18, React-DOM, and Babel UMD are bundled locally inside the executable.
- **Single Executable**: Shipped as a self-contained 37.9 MB Windows binary (`NeonLightsController.exe`).
