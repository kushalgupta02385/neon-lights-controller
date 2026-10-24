const { useState, useEffect, useRef, useCallback } = React;

// --- API Helper ---
const api = {
  get: async (url) => {
    try {
      const res = await fetch(url);
      return await res.json();
    } catch (e) {
      console.error("GET error:", e);
      return null;
    }
  },
  post: async (url, data = {}) => {
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      return await res.json();
    } catch (e) {
      console.error("POST error:", e);
      return null;
    }
  },
};

// --- Main App Component ---
function App() {
  const [activeTab, setActiveTab] = useState("colors");
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCat, setSelectedCat] = useState("All");

  // Fetch full state periodically
  const fetchState = useCallback(async () => {
    const data = await api.get("/api/state");
    if (data) {
      setState(data);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchState();
    const interval = setInterval(fetchState, 1500);
    return () => clearInterval(interval);
  }, [fetchState]);

  if (!state) {
    return (
      <div style={{ display: "flex", height: "100vh", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: "16px" }}>
        <div style={{ width: "40px", height: "40px", border: "3px solid #1A2138", borderTop: "3px solid #00F0FF", borderRadius: "50%" }} className="spin"></div>
        <div style={{ color: "#8292A6", fontSize: "14px", fontWeight: "600" }}>Connecting to Neon Backend...</div>
      </div>
    );
  }

  const isConnected = state.connected;
  const isPower = state.power;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", padding: "14px 18px", gap: "12px" }}>
      {/* 1. Header */}
      <Header state={state} onRefresh={fetchState} onTabChange={setActiveTab} />

      {/* 2. Navigation Tabs */}
      <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid var(--border)", paddingBottom: "8px" }}>
        {[
          { id: "colors", label: "🎨 Colors & White" },
          { id: "modes", label: "⚡ Dynamic Modes (213)" },
          { id: "audio", label: "🔊 Game & Music Sync" },
          { id: "settings", label: "⚙️ Strip & Settings" },
        ].map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: "8px 18px",
                borderRadius: "10px",
                background: isActive ? "rgba(0, 240, 255, 0.12)" : "transparent",
                color: isActive ? "var(--cyan)" : "var(--text-muted)",
                fontWeight: isActive ? "700" : "500",
                fontSize: "13px",
                border: isActive ? "1px solid rgba(0, 240, 255, 0.4)" : "1px solid transparent",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* 3. Main Content Area */}
      <div style={{ flex: 1, overflowY: "auto", paddingRight: "4px" }}>
        {activeTab === "colors" && <ColorsTab state={state} onUpdate={fetchState} />}
        {activeTab === "modes" && (
          <ModesTab
            state={state}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            selectedCat={selectedCat}
            setSelectedCat={setSelectedCat}
            onUpdate={fetchState}
          />
        )}
        {activeTab === "audio" && <AudioTab state={state} onUpdate={fetchState} />}
        {activeTab === "settings" && <SettingsTab state={state} onUpdate={fetchState} />}
      </div>

      {/* 4. Bottom Persistent Deck */}
      <BottomDeck state={state} onUpdate={fetchState} />
    </div>
  );
}

// --- Header Component ---
function Header({ state, onRefresh, onTabChange }) {
  const isConnected = state.connected;
  const isPower = state.power;
  const [isScanning, setIsScanning] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  const togglePower = async () => {
    await api.post("/api/power", { on: !isPower });
    onRefresh();
  };

  const scanDevices = async () => {
    setIsScanning(true);
    await api.post("/api/scan");
    onRefresh();
    setTimeout(() => {
      setIsScanning(false);
      onRefresh();
    }, 3500);
  };

  const handleStatusClick = async () => {
    if (!isConnected) {
      setIsConnecting(true);
      await api.post("/api/connect", { mac: "BE:69:58:01:CC:00" });
      onRefresh();
      setTimeout(() => {
        setIsConnecting(false);
        onRefresh();
      }, 3500);
    }
    onTabChange("settings");
  };

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "4px 0" }}>
      {/* Title */}
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "20px" }}>⚡</span>
          <span style={{ fontSize: "18px", fontWeight: "900", letterSpacing: "1px", color: "#FFF" }}>
            NEON LIGHTS STUDIO
          </span>
          <span style={{ background: "rgba(0, 240, 255, 0.15)", color: "var(--cyan)", fontSize: "10px", padding: "2px 8px", borderRadius: "12px", fontWeight: "700", border: "1px solid rgba(0, 240, 255, 0.3)" }}>
            REACT EDITION
          </span>
        </div>
        <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
          MagicLantern BLE Controller • Windows WASAPI Game Audio Sync
        </div>
      </div>

      {/* Center Status Pill */}
      <div
        onClick={handleStatusClick}
        style={{
          cursor: "pointer",
          background: isConnected ? "rgba(5, 255, 161, 0.12)" : (isConnecting ? "rgba(255, 215, 0, 0.12)" : "rgba(255, 71, 87, 0.12)"),
          border: isConnected ? "1px solid rgba(5, 255, 161, 0.3)" : (isConnecting ? "1px solid rgba(255, 215, 0, 0.4)" : "1px solid rgba(255, 71, 87, 0.3)"),
          color: isConnected ? "var(--green)" : (isConnecting ? "#FFD700" : "var(--red)"),
          padding: "6px 14px",
          borderRadius: "20px",
          fontSize: "12px",
          fontWeight: "700",
          display: "flex",
          alignItems: "center",
          gap: "8px",
          transition: "all 0.2s ease",
        }}
        title={isConnected ? "Light Connected - Click to view settings" : "Click to connect to light"}
      >
        <span style={{ fontSize: "10px" }}>{isConnected ? "🟢" : (isConnecting ? "🟡" : "🔴")}</span>
        <span>
          {isConnected 
            ? `Connected: ${state.connected_mac || "MELK-OA10"}` 
            : (isConnecting ? "Connecting to light..." : "Disconnected (Click to Connect)")}
        </span>
      </div>

      {/* Right Actions */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <button
          className="btn-secondary"
          onClick={scanDevices}
          disabled={isScanning}
          style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", opacity: isScanning ? 0.7 : 1 }}
        >
          <span className={isScanning ? "spin" : ""}>🔄</span>
          <span>{isScanning ? "Scanning..." : "Scan"}</span>
        </button>

        <button
          onClick={togglePower}
          style={{
            background: isPower ? "rgba(5, 255, 161, 0.15)" : "rgba(255, 71, 87, 0.15)",
            border: isPower ? "1px solid var(--green)" : "1px solid var(--red)",
            color: isPower ? "var(--green)" : "var(--red)",
            padding: "8px 16px",
            borderRadius: "10px",
            fontWeight: "700",
            fontSize: "12px",
            display: "flex",
            alignItems: "center",
            gap: "6px",
          }}
        >
          <span>{isPower ? "⏻ ON" : "⏻ OFF"}</span>
        </button>
      </div>
    </div>
  );
}

// --- Colors & White Tab ---
function ColorsTab({ state, onUpdate }) {
  const [warmth, setWarmth] = useState(50);
  const canvasRef = useRef(null);

  const applyColor = async (r, g, b) => {
    await api.post("/api/color", { r, g, b });
    onUpdate();
  };

  const applyCct = async (val) => {
    const warm = parseInt(val);
    const cold = 100 - warm;
    setWarmth(warm);
    await api.post("/api/cct", { warm, cold });
    onUpdate();
  };

  // Render 2D Color Wheel
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(centerX, centerY) - 6;

    for (let x = 0; x < width; x++) {
      for (let y = 0; y < height; y++) {
        const dx = x - centerX;
        const dy = y - centerY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist <= radius) {
          const angle = Math.atan2(dy, dx) + Math.PI;
          const hue = (angle / (Math.PI * 2)) * 360;
          const sat = (dist / radius) * 100;
          ctx.fillStyle = `hsl(${hue}, ${sat}%, 50%)`;
          ctx.fillRect(x, y, 1, 1);
        }
      }
    }
  }, []);

  const handleCanvasClick = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const ctx = canvas.getContext("2d");
    const pixel = ctx.getImageData(x, y, 1, 1).data;
    if (pixel[3] > 0) {
      applyColor(pixel[0], pixel[1], pixel[2]);
    }
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: "16px", height: "100%" }}>
      {/* Left: Interactive Canvas Color Wheel */}
      <div className="glass-panel" style={{ padding: "18px", display: "flex", flexDirection: "column", alignItems: "center", gap: "14px" }}>
        <div style={{ fontWeight: "700", fontSize: "14px", color: "var(--cyan)", alignSelf: "flex-start" }}>
          🎨 Custom Color Spectrum
        </div>
        <canvas
          ref={canvasRef}
          width={280}
          height={280}
          onClick={handleCanvasClick}
          style={{ borderRadius: "50%", cursor: "crosshair", boxShadow: "0 0 20px rgba(0, 0, 0, 0.8)", border: "2px solid rgba(255, 255, 255, 0.1)" }}
        />
        <div style={{ display: "flex", alignItems: "center", gap: "12px", width: "100%", justifyContent: "center" }}>
          <div style={{ width: "36px", height: "36px", borderRadius: "8px", background: `rgb(${state.color.r}, ${state.color.g}, ${state.color.b})`, border: "2px solid #FFF", boxShadow: `0 0 12px rgb(${state.color.r}, ${state.color.g}, ${state.color.b})` }}></div>
          <div style={{ fontSize: "13px", fontWeight: "700", color: "#FFF" }}>
            RGB({state.color.r}, {state.color.g}, {state.color.b})
          </div>
        </div>
      </div>

      {/* Right: Presets & Dual CCT White */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* Preset Palette */}
        <div className="glass-panel" style={{ padding: "18px" }}>
          <div style={{ fontWeight: "700", fontSize: "14px", color: "var(--cyan)", marginBottom: "12px" }}>
            💎 Vibrant Neon Presets
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(130px, 1fr))", gap: "10px" }}>
            {state.preset_colors.map((c) => {
              const isSelected = state.color.r === c.r && state.color.g === c.g && state.color.b === c.b;
              return (
                <button
                  key={c.name}
                  onClick={() => applyColor(c.r, c.g, c.b)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    background: isSelected ? "rgba(0, 240, 255, 0.15)" : "#131828",
                    border: isSelected ? "1px solid var(--cyan)" : "1px solid var(--border)",
                    padding: "8px 12px",
                    borderRadius: "10px",
                    color: isSelected ? "var(--cyan)" : "#CBD5E1",
                    fontSize: "12px",
                    fontWeight: isSelected ? "700" : "500",
                    textAlign: "left",
                  }}
                >
                  <span style={{ width: "16px", height: "16px", borderRadius: "50%", background: c.hex, boxShadow: `0 0 8px ${c.hex}` }}></span>
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Dual CCT White Slider */}
        <div className="glass-panel" style={{ padding: "18px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <div style={{ fontWeight: "700", fontSize: "14px", color: "var(--gold)" }}>
              🕯️ Dual CCT White Balance (Warm / Cold)
            </div>
            <div style={{ fontSize: "12px", fontWeight: "700", color: "#CBD5E1" }}>
              {warmth}% Warm / {100 - warmth}% Cold
            </div>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={warmth}
            onChange={(e) => applyCct(e.target.value)}
            style={{ marginBottom: "14px" }}
          />
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-muted)" }}>
            <span>❄️ Cool Daylight (6500K)</span>
            <span>⚖️ Neutral White</span>
            <span>🔥 Warm Candlelight (2700K)</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- Dynamic Modes Tab ---
function ModesTab({ state, searchQuery, setSearchQuery, selectedCat, setSelectedCat, onUpdate }) {
  const categories = ["All", ...Object.keys(state.mode_categories)];

  // Aggregate cards
  const allCards = [];
  Object.entries(state.mode_categories).forEach(([cat, modes]) => {
    modes.forEach((m) => {
      allCards.push({ ...m, category: cat });
    });
  });

  const filteredCards = allCards.filter((c) => {
    const matchCat = selectedCat === "All" || c.category === selectedCat;
    const matchSearch =
      !searchQuery ||
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
      String(c.id).includes(searchQuery);
    return matchCat && matchSearch;
  });

  const setMode = async (id, name) => {
    await api.post("/api/mode", { mode_id: id, name });
    onUpdate();
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px", height: "100%" }}>
      {/* Controls Bar */}
      <div className="glass-panel" style={{ padding: "12px 16px", display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
        {/* Search */}
        <input
          type="text"
          placeholder="🔍 Search all 213 modes by name or ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            flex: 1,
            minWidth: "220px",
            background: "#121626",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "8px 14px",
            color: "#FFF",
            fontSize: "13px",
            outline: "none",
          }}
        />

        {/* Categories */}
        <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCat(cat)}
              style={{
                padding: "6px 12px",
                borderRadius: "8px",
                fontSize: "11px",
                fontWeight: selectedCat === cat ? "700" : "500",
                background: selectedCat === cat ? "var(--cyan)" : "#161D2E",
                color: selectedCat === cat ? "#000" : "#94A3B8",
                border: "1px solid var(--border)",
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Mode Grid */}
      <div style={{ flex: 1, overflowY: "auto", display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "10px", paddingBottom: "10px" }}>
        {filteredCards.map((m) => {
          const isActive = state.active_mode_id === m.id;
          return (
            <div
              key={`${m.category}-${m.id}`}
              onClick={() => setMode(m.id, m.name)}
              className="glass-panel"
              style={{
                padding: "12px",
                cursor: "pointer",
                background: isActive ? "rgba(0, 240, 255, 0.15)" : "var(--bg-card)",
                borderColor: isActive ? "var(--cyan)" : "var(--border)",
                boxShadow: isActive ? "0 0 14px rgba(0, 240, 255, 0.3)" : "none",
                display: "flex",
                flexDirection: "column",
                gap: "6px",
                transition: "all 0.15s ease",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", color: "var(--text-muted)" }}>
                <span>{m.category}</span>
                <span style={{ fontWeight: "700", color: isActive ? "var(--cyan)" : "inherit" }}>#{m.id}</span>
              </div>
              <div style={{ fontSize: "13px", fontWeight: "700", color: isActive ? "#FFF" : "#CBD5E1", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {m.name}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// --- Game & Music Sync Tab ---
function AudioTab({ state, onUpdate }) {
  const [liveLevel, setLiveLevel] = useState(0.0);
  const [liveRgb, setLiveRgb] = useState([0, 240, 255]);
  const canvasRef = useRef(null);

  const isRunning = state.audio_sync.running;

  // Poll live VU level at 30 FPS
  useEffect(() => {
    let animId;
    const fetchLevel = async () => {
      const res = await api.get("/api/audio/level");
      if (res) {
        setLiveLevel(res.level || 0);
        setLiveRgb(res.rgb || [0, 240, 255]);
      }
      animId = setTimeout(fetchLevel, 33);
    };
    fetchLevel();
    return () => clearTimeout(animId);
  }, []);

  // Draw Animated Canvas VU Meter
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#0C0E16";
    ctx.fillRect(0, 0, w, h);

    if (liveLevel > 0.01) {
      const fillW = Math.max(10, Math.min(w, w * liveLevel));
      const grad = ctx.createLinearGradient(0, 0, fillW, 0);
      grad.addColorStop(0, "#00F0FF");
      grad.addColorStop(0.5, "#9D4EDD");
      grad.addColorStop(0.85, "#FF2A6D");
      grad.addColorStop(1, "#FF4757");

      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, fillW, h);

      // White peak cap
      ctx.fillStyle = "#FFFFFF";
      ctx.fillRect(Math.max(0, fillW - 4), 0, 4, h);
    }
  }, [liveLevel]);

  const toggleSync = async () => {
    if (isRunning) {
      await api.post("/api/audio/stop");
    } else {
      await api.post("/api/audio/start", {
        mode: state.audio_sync.mode,
        device_id: state.audio_sync.device_id,
        sensitivity: state.audio_sync.sensitivity,
      });
    }
    onUpdate();
  };

  const quickLaunchMode = async (modeName) => {
    await api.post("/api/brightness", { level: 100 });
    await api.post("/api/audio/start", { mode: modeName });
    onUpdate();
  };

  const setAudioMode = async (m) => {
    await api.post("/api/audio/mode", { mode: m });
    onUpdate();
  };

  const setSensitivity = async (s) => {
    await api.post("/api/audio/sensitivity", { sensitivity: parseFloat(s) });
    onUpdate();
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "16px", height: "100%" }}>
      {/* Left: PC Audio Loopback Sync */}
      <div className="glass-panel" style={{ padding: "18px", display: "flex", flexDirection: "column", gap: "14px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: "700", fontSize: "14px", color: "var(--cyan)" }}>
          <span>💻</span>
          <span>Laptop Game & Music Sound Capture (WASAPI Loopback)</span>
        </div>

        {/* Device Menu */}
        <div>
          <label style={{ fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
            Playback Capture Device:
          </label>
          <select
            value={state.audio_sync.device_id ?? -1}
            onChange={(e) => api.post("/api/audio/start", { device_id: parseInt(e.target.value) }).then(onUpdate)}
            style={{ width: "100%", background: "#131828", border: "1px solid var(--border)", color: "#FFF", padding: "8px 12px", borderRadius: "8px", outline: "none", fontSize: "12px" }}
          >
            {state.audio_devices.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </div>

        {/* Algorithm Menu */}
        <div>
          <label style={{ fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
            Lighting Reaction Algorithm:
          </label>
          <select
            value={state.audio_sync.mode}
            onChange={(e) => setAudioMode(e.target.value)}
            style={{ width: "100%", background: "#131828", border: "1px solid var(--border)", color: "#FFF", padding: "8px 12px", borderRadius: "8px", outline: "none", fontSize: "12px" }}
          >
            {state.supported_audio_modes.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        {/* 2 Dedicated 1-Click Launch Buttons */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
          <button
            onClick={() => quickLaunchMode("🌀 Rolling Lines (with Black Gaps)")}
            style={{
              background: "#161D2E",
              border: "1px solid var(--cyan)",
              color: "var(--cyan)",
              padding: "10px",
              borderRadius: "8px",
              fontWeight: "700",
              fontSize: "11px",
            }}
          >
            🌀 ROLLING W/ BLACK GAPS
          </button>

          <button
            onClick={() => quickLaunchMode("📊 Beat Lines (VU Rhythm Lamp Bar)")}
            style={{
              background: "#161D2E",
              border: "1px solid var(--gold)",
              color: "var(--gold)",
              padding: "10px",
              borderRadius: "8px",
              fontWeight: "700",
              fontSize: "11px",
            }}
          >
            📊 BEAT LINES (RHYTHM LAMP)
          </button>
        </div>

        {/* Sensitivity */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", fontWeight: "700", marginBottom: "4px" }}>
            <span style={{ color: "var(--text-muted)" }}>Sound & Beat Sensitivity:</span>
            <span style={{ color: "var(--cyan)" }}>{state.audio_sync.sensitivity}x</span>
          </div>
          <input
            type="range"
            min="0.2"
            max="3.5"
            step="0.05"
            value={state.audio_sync.sensitivity}
            onChange={(e) => setSensitivity(e.target.value)}
          />
        </div>

        {/* Canvas VU Meter */}
        <div>
          <label style={{ fontSize: "11px", fontWeight: "700", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
            Live Audio Level Visualizer:
          </label>
          <canvas
            ref={canvasRef}
            width={480}
            height={24}
            style={{ width: "100%", height: "24px", borderRadius: "6px", border: "1px solid var(--border)" }}
          />
        </div>

        {/* Main Activate Button */}
        <button
          onClick={toggleSync}
          className={isRunning ? "btn-danger" : "btn-primary"}
          style={{ padding: "14px", fontSize: "14px", marginTop: "auto" }}
        >
          {isRunning ? "⏹️ STOP AUDIO SYNC" : "▶️ ACTIVATE GAME & MUSIC SYNC"}
        </button>
      </div>

      {/* Right: Controller Physical Mic */}
      <div className="glass-panel" style={{ padding: "18px", display: "flex", flexDirection: "column", gap: "14px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: "700", fontSize: "14px", color: "var(--pink)" }}>
            <span>🎙️</span>
            <span>Controller Physical Mic</span>
          </div>
          <button
            onClick={() => api.post("/api/hw_mic", { on: !state.hw_mic.on, eq: state.hw_mic.eq }).then(onUpdate)}
            style={{
              padding: "4px 12px",
              borderRadius: "16px",
              fontSize: "11px",
              fontWeight: "700",
              background: state.hw_mic.on ? "rgba(5, 255, 161, 0.2)" : "#1E2538",
              color: state.hw_mic.on ? "var(--green)" : "#94A3B8",
              border: state.hw_mic.on ? "1px solid var(--green)" : "1px solid var(--border)",
            }}
          >
            {state.hw_mic.on ? "MIC ON" : "MIC OFF"}
          </button>
        </div>

        <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
          Runs the controller's internal chip for addressable multi-color running & rolling waves via the inline physical mic:
        </div>

        {/* 8 EQ Mode Buttons */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "8px" }}>
          {state.eq_modes.map((eq) => {
            const isEqActive = state.hw_mic.on && state.hw_mic.eq === eq.id;
            return (
              <button
                key={eq.id}
                onClick={() => api.post("/api/hw_mic", { on: true, eq: eq.id }).then(onUpdate)}
                style={{
                  padding: "10px",
                  borderRadius: "8px",
                  fontSize: "12px",
                  fontWeight: isEqActive ? "700" : "500",
                  background: isEqActive ? "rgba(255, 42, 109, 0.2)" : "#131828",
                  border: isEqActive ? "1px solid var(--pink)" : "1px solid var(--border)",
                  color: isEqActive ? "#FFF" : "#CBD5E1",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <span>{eq.id % 2 === 0 ? "⚡" : "🌊"}</span>
                <span>{eq.name}</span>
              </button>
            );
          })}
        </div>

        {/* Disarm Mic Button */}
        <button
          onClick={() => api.post("/api/hw_mic/disarm").then(onUpdate)}
          className="btn-secondary"
          style={{ marginTop: "auto", padding: "10px", color: "var(--pink)", borderColor: "rgba(255, 42, 109, 0.3)" }}
        >
          🛑 Disarm Controller Physical Mic
        </button>
      </div>
    </div>
  );
}

// --- Strip & Settings Tab ---
function SettingsTab({ state, onUpdate }) {
  const [points, setPoints] = useState(state.symphony_points);
  const [isScanning, setIsScanning] = useState(false);
  const [connectingMac, setConnectingMac] = useState(null);

  const applyPoints = async (val) => {
    const p = parseInt(val);
    setPoints(p);
    await api.post("/api/points", { points: p });
    onUpdate();
  };

  const applyPinSeq = async (seq) => {
    await api.post("/api/pin_sequence", { sequence: seq });
    onUpdate();
  };

  const connectDevice = async (mac) => {
    const target = mac || "BE:69:58:01:CC:00";
    setConnectingMac(target);
    await api.post("/api/connect", { mac: target });
    onUpdate();
    setTimeout(() => {
      setConnectingMac(null);
      onUpdate();
    }, 4000);
  };

  const disconnectDevice = async () => {
    await api.post("/api/disconnect");
    onUpdate();
  };

  const handleScan = async () => {
    setIsScanning(true);
    await api.post("/api/scan");
    onUpdate();
    setTimeout(() => {
      setIsScanning(false);
      onUpdate();
    }, 3500);
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", height: "100%" }}>
      {/* Left: Pixel Points & Pin Order */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* Symphony Points */}
        <div className="glass-panel" style={{ padding: "18px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
            <div style={{ fontWeight: "700", fontSize: "14px", color: "var(--cyan)" }}>
              📏 Strip Length (Symphony Pixel Points)
            </div>
            <div style={{ fontSize: "13px", fontWeight: "700", color: "#FFF" }}>
              {points} Points
            </div>
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "12px" }}>
            Controls active addressable LED count on your neon strip (1 to 1024 LEDs):
          </div>
          <input
            type="range"
            min="1"
            max="200"
            value={points}
            onChange={(e) => applyPoints(e.target.value)}
          />
        </div>

        {/* RGB Pin Calibration */}
        <div className="glass-panel" style={{ padding: "18px" }}>
          <div style={{ fontWeight: "700", fontSize: "14px", color: "var(--gold)", marginBottom: "8px" }}>
            🔀 RGB Hardware Channel Calibration
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "12px" }}>
            If red and green appear swapped, select the matching sequence:
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px" }}>
            {state.pin_sequences.map((pin) => {
              const isPinActive = JSON.stringify(state.pin_sequence) === JSON.stringify(pin.order);
              return (
                <button
                  key={pin.name}
                  onClick={() => applyPinSeq(pin.order)}
                  style={{
                    padding: "10px",
                    borderRadius: "8px",
                    fontSize: "12px",
                    fontWeight: isPinActive ? "700" : "500",
                    background: isPinActive ? "rgba(251, 191, 36, 0.2)" : "#131828",
                    border: isPinActive ? "1px solid var(--gold)" : "1px solid var(--border)",
                    color: isPinActive ? "var(--gold)" : "#CBD5E1",
                  }}
                >
                  {pin.name}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Right: Bluetooth Device Scanner & Manager */}
      <div className="glass-panel" style={{ padding: "18px", display: "flex", flexDirection: "column", gap: "14px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ fontWeight: "700", fontSize: "14px", color: "var(--cyan)" }}>
            📡 Bluetooth Nearby Devices
          </div>
          <button
            onClick={handleScan}
            disabled={isScanning}
            className="btn-secondary"
            style={{ fontSize: "11px", padding: "6px 12px", display: "flex", alignItems: "center", gap: "6px" }}
          >
            <span className={isScanning ? "spin" : ""}>🔄</span>
            <span>{isScanning ? "Scanning..." : "Scan Now"}</span>
          </button>
        </div>

        {/* 1-Click Direct Connect Card */}
        <div style={{ display: "flex", gap: "10px" }}>
          <button
            onClick={() => connectDevice("BE:69:58:01:CC:00")}
            disabled={connectingMac === "BE:69:58:01:CC:00"}
            style={{
              flex: 1,
              background: state.connected ? "rgba(5, 255, 161, 0.12)" : "linear-gradient(135deg, rgba(0, 240, 255, 0.2), rgba(168, 85, 247, 0.2))",
              border: state.connected ? "1px solid var(--green)" : "1px solid var(--cyan)",
              color: state.connected ? "var(--green)" : "#FFF",
              padding: "10px 14px",
              borderRadius: "10px",
              fontSize: "12px",
              fontWeight: "700",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
            }}
          >
            <span>{state.connected ? "🟢 Light Connected (BE:69:58:01:CC:00)" : (connectingMac ? "🟡 Connecting to MELK-OA10 44..." : "⚡ Quick Connect to MELK-OA10 44")}</span>
          </button>
        </div>

        {/* Device List */}
        <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "8px" }}>
          {state.scanned_devices.length === 0 ? (
            <div style={{ textAlign: "center", color: "var(--text-muted)", fontSize: "12px", margin: "auto" }}>
              {isScanning ? "Scanning for nearby Bluetooth devices..." : "Click \"Scan Now\" or use Quick Connect above."}
            </div>
          ) : (
            state.scanned_devices.map((dev) => {
              const isDevConnected = state.connected && state.connected_mac === dev.address;
              const isMelk = dev.name.startsWith("MELK") || dev.name.startsWith("ELK") || dev.address === "BE:69:58:01:CC:00";
              const isThisConnecting = connectingMac === dev.address;
              return (
                <div
                  key={dev.address}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "12px 14px",
                    background: isDevConnected ? "rgba(5, 255, 161, 0.1)" : (isMelk ? "#141A2D" : "#131828"),
                    border: isDevConnected ? "1px solid var(--green)" : (isMelk ? "1px solid rgba(0, 240, 255, 0.3)" : "1px solid var(--border)"),
                    borderRadius: "10px",
                  }}
                >
                  <div>
                    <div style={{ fontSize: "13px", fontWeight: "700", color: isMelk ? "var(--cyan)" : "#FFF", display: "flex", alignItems: "center", gap: "6px" }}>
                      <span>{isMelk ? "✨ " : ""}{dev.name}</span>
                      {isMelk && (
                        <span style={{ fontSize: "9px", padding: "1px 6px", borderRadius: "4px", background: "rgba(0, 240, 255, 0.2)", color: "var(--cyan)", fontWeight: "700" }}>
                          NEON STRIP
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{dev.address} ({dev.rssi} dBm)</div>
                  </div>
                  {isDevConnected ? (
                    <button
                      onClick={disconnectDevice}
                      style={{ background: "var(--red)", color: "#FFF", padding: "6px 14px", borderRadius: "8px", fontSize: "12px", fontWeight: "700" }}
                    >
                      Disconnect
                    </button>
                  ) : (
                    <button
                      onClick={() => connectDevice(dev.address)}
                      disabled={isThisConnecting}
                      style={{
                        background: isMelk ? "var(--cyan)" : "#1E2438",
                        color: isMelk ? "#000" : "#FFF",
                        padding: "6px 14px",
                        borderRadius: "8px",
                        fontSize: "12px",
                        fontWeight: "700",
                        opacity: isThisConnecting ? 0.7 : 1,
                      }}
                    >
                      {isThisConnecting ? "Connecting..." : "Connect"}
                    </button>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

// --- Persistent Bottom Deck Component ---
function BottomDeck({ state, onUpdate }) {
  const setBrightness = async (val) => {
    await api.post("/api/brightness", { level: parseInt(val) });
    onUpdate();
  };

  const setSpeed = async (val) => {
    await api.post("/api/speed", { speed: parseInt(val) });
    onUpdate();
  };

  return (
    <div
      className="glass-panel"
      style={{
        padding: "10px 18px",
        display: "grid",
        gridTemplateColumns: "220px 1fr 1fr",
        gap: "20px",
        alignItems: "center",
        borderTop: "1px solid var(--border)",
      }}
    >
      {/* Left: Active Mode / Color Status */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <div
          style={{
            width: "32px",
            height: "32px",
            borderRadius: "8px",
            background: `rgb(${state.color.r}, ${state.color.g}, ${state.color.b})`,
            boxShadow: `0 0 10px rgb(${state.color.r}, ${state.color.g}, ${state.color.b})`,
            border: "2px solid #FFF",
          }}
        ></div>
        <div style={{ overflow: "hidden" }}>
          <div style={{ fontSize: "12px", fontWeight: "700", color: "#FFF", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {state.active_mode_name}
          </div>
          <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
            {state.power ? "Active Mode" : "Powered Off"}
          </div>
        </div>
      </div>

      {/* Center: Master Brightness Slider */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", fontWeight: "700", marginBottom: "4px" }}>
          <span style={{ color: "var(--text-muted)" }}>Brightness:</span>
          <span style={{ color: "var(--cyan)" }}>{state.brightness}%</span>
        </div>
        <input
          type="range"
          min="1"
          max="100"
          value={state.brightness}
          onChange={(e) => setBrightness(e.target.value)}
        />
      </div>

      {/* Right: Dynamic Speed Slider */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", fontWeight: "700", marginBottom: "4px" }}>
          <span style={{ color: "var(--text-muted)" }}>Effect Speed:</span>
          <span style={{ color: "var(--pink)" }}>{state.speed}%</span>
        </div>
        <input
          type="range"
          min="1"
          max="100"
          value={state.speed}
          onChange={(e) => setSpeed(e.target.value)}
        />
      </div>
    </div>
  );
}

// Mount Root Component
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
