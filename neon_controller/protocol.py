"""
MagicLantern / ELK-BLEDOM Protocol Definitions and Packet Builders
Reverse engineered from MagicLantern Android APK (com.easylink.colorful)
"""

SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR_UUID = "0000fff4-0000-1000-8000-00805f9b34fb"

NAME_FILTER_PREFIXES = ("MELK-", "ELK-", "MELK_", "ELK_")

# --- Protocol Packet Builders ---

def make_power_packet(on: bool) -> bytes:
    """Master power ON / OFF command."""
    val = 0x01 if on else 0x00
    return bytes([0x7E, 0x04, 0x04, val, 0x00, val, 0xFF, 0x00, 0xEF])

def make_color_packet(r: int, g: int, b: int) -> bytes:
    """Set static RGB color (0-255 each)."""
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return bytes([0x7E, 0x07, 0x05, 0x03, r, g, b, 0x10, 0xEF])

def make_music_color_packet(r: int, g: int, b: int) -> bytes:
    """Send reactive audio RGB amplitude packet."""
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return bytes([0x7E, 0x07, 0x05, 0x03, r, g, b, 0x20, 0xEF])

def make_brightness_packet(level: int) -> bytes:
    """Set brightness (0-100)."""
    level = max(0, min(100, int(level)))
    return bytes([0x7E, 0x04, 0x01, level, 0xFF, 0xFF, 0xFF, 0x00, 0xEF])

def make_speed_packet(speed: int) -> bytes:
    """Set dynamic effect speed (0-100)."""
    speed = max(0, min(100, int(speed)))
    return bytes([0x7E, 0x04, 0x02, speed, 0xFF, 0xFF, 0xFF, 0x00, 0xEF])

def make_mode_packet(mode_id: int) -> bytes:
    """Set dynamic effect mode (Group 0 to Group 7)."""
    mode_id = int(mode_id) & 0xFF
    return bytes([0x7E, 0x05, 0x03, mode_id, 0x06, 0xFF, 0xFF, 0x00, 0xEF])

def make_scene_packet(scene_id: int) -> bytes:
    """Set preset scene mode (Group 8, 1-28)."""
    scene_id = max(1, min(28, int(scene_id)))
    return bytes([0x7E, 0x05, 0x31, scene_id, 0x07, 0xFF, 0xFF, 0x01, 0xEF])

def make_cct_packet(warm: int, cold: int) -> bytes:
    """Set color temperature (warm white 0-100, cold white 0-100)."""
    warm = max(0, min(100, int(warm)))
    cold = max(0, min(100, int(cold)))
    return bytes([0x7E, 0x06, 0x05, 0x02, warm, cold, 0xFF, 0x08, 0xEF])

def make_single_color_packet(color_idx: int) -> bytes:
    """Set single color preset index."""
    color_idx = int(color_idx) & 0xFF
    return bytes([0x7E, 0x05, 0x05, 0x01, color_idx, 0xFF, 0xFF, 0x08, 0xEF])

def make_external_mic_power_packet(on: bool) -> bytes:
    """Turn physical controller microphone ON/OFF."""
    val = 0x01 if on else 0x00
    return bytes([0x7E, 0x04, 0x07, val, 0xFF, 0xFF, 0xFF, 0x00, 0xEF])

def make_external_mic_sensitivity_packet(sensitivity: int) -> bytes:
    """Set controller microphone sensitivity (0-100)."""
    sensitivity = max(0, min(100, int(sensitivity)))
    return bytes([0x7E, 0x04, 0x06, sensitivity, 0xFF, 0xFF, 0xFF, 0x00, 0xEF])

def make_external_mic_eq_packet(eq_mode: int) -> bytes:
    """Set controller microphone rhythm / EQ mode (0-7, added to 128)."""
    val = (int(eq_mode) & 0x07) + 128
    return bytes([0x7E, 0x07, 0x03, val, 0x04, 0xFF, 0xFF, 0x00, 0xEF])

def make_pin_sequence_packet(r: int, g: int, b: int) -> bytes:
    """Configure RGB channel pin order (0=R, 1=G, 2=B)."""
    return bytes([0x7E, 0x06, 0x81, r & 0xFF, g & 0xFF, b & 0xFF, 0xFF, 0x00, 0xEF])

def make_symphony_points_packet(points: int) -> bytes:
    """Set number of IC points / pixel count for addressable strip."""
    points = max(1, min(1024, int(points)))
    low = points & 0xFF
    high = (points >> 8) & 0xFF
    return bytes([0x7E, 0x07, 0x21, low, high, 0x00, 0xFF, 0x00, 0xEF])

def make_system_time_packet(hour: int, minute: int, second: int, weekday: int) -> bytes:
    """Sync system time to controller."""
    return bytes([0x7E, 0x07, 0x83, hour & 0xFF, minute & 0xFF, second & 0xFF, weekday & 0xFF, 0xFF, 0xEF])

def make_timing_status_packet(hour: int, minute: int, second: int, mode: int, weeks_bitmask: int) -> bytes:
    """Set light schedule timer."""
    return bytes([0x7E, 0x08, 0x82, hour & 0xFF, minute & 0xFF, second & 0xFF, mode & 0xFF, weeks_bitmask & 0xFF, 0xEF])


# --- Preset Data Constants (Extracted from MagicLantern APK) ---

EXTERNAL_MIC_EQ_MODES = [
    ("Energic", 0),
    ("Rhythm", 1),
    ("Spectrum", 2),
    ("Rolling", 3),
    ("Energic II", 4),
    ("Rhythm II", 5),
    ("Spectrum II", 6),
    ("Rolling II", 7),
]

PIN_SEQUENCES = [
    ("R G B", (0, 1, 2)),
    ("R B G", (0, 2, 1)),
    ("G R B", (1, 0, 2)),
    ("G B R", (1, 2, 0)),
    ("B R G", (2, 0, 1)),
    ("B G R", (2, 1, 0)),
]

PRESET_COLORS = [
    ("Red", "#FF0000", (255, 0, 0)),
    ("Green", "#00FF00", (0, 255, 0)),
    ("Blue", "#0000FF", (0, 0, 255)),
    ("Yellow", "#FFFF00", (255, 255, 0)),
    ("Cyan", "#00FFFF", (0, 255, 255)),
    ("Magenta", "#FF00FF", (255, 0, 255)),
    ("Pure White", "#FFFFFF", (255, 255, 255)),
    ("Warm White", "#FFE4CD", (255, 228, 205)),
    ("Neon Orange", "#FF6600", (255, 102, 0)),
    ("Deep Pink", "#FF1493", (255, 20, 147)),
    ("Purple", "#8A2BE2", (138, 43, 226)),
    ("Electric Blue", "#007FFF", (0, 127, 255)),
    ("Spring Green", "#00FF7F", (0, 255, 127)),
    ("Amber Gold", "#FFBF00", (255, 191, 0)),
    ("Turquoise", "#40E0D0", (64, 224, 208)),
    ("Coral Sunset", "#FF7F50", (255, 127, 80)),
]

# Mode database by group: (name, command_id, is_scene)
MODE_CATEGORIES = {
    "Basic": [
        ("Auto Play", 0, False),
        ("Magic Forward", 1, False),
        ("Magic Back", 2, False),
        ("7-Color Energy", 212, False),
        ("7-Color Jump", 193, False),
        ("R-G-B Jump", 194, False),
        ("Y-C-P Jump", 195, False),
        ("7-Color Strobe", 196, False),
        ("R-G-B Strobe", 197, False),
        ("Y-C-P Strobe", 198, False),
        ("7-Color Gradual", 199, False),
        ("R-Y Gradual", 200, False),
        ("R-P Gradual", 201, False),
        ("G-C Gradual", 202, False),
        ("G-Y Gradual", 203, False),
        ("B-P Gradual", 204, False),
        ("Red Marquee", 205, False),
        ("Green Marquee", 206, False),
        ("Blue Marquee", 207, False),
        ("Yellow Marquee", 208, False),
        ("Cyan Marquee", 209, False),
        ("Purple Marquee", 210, False),
        ("White Marquee", 211, False),
        ("7-Color Race", 77, False),
        ("7-Color Race Back", 78, False),
        ("R-G-B Race", 79, False),
        ("R-G-B Race Back", 80, False),
        ("Y-C-P Race", 81, False),
        ("Y-C-P Race Back", 82, False),
        ("7-Color Wave", 83, False),
        ("7-Color Wave Back", 84, False),
        ("R-G-B Wave", 85, False),
        ("R-G-B Wave Back", 86, False),
        ("Y-C-P Wave", 87, False),
        ("Y-C-P Wave Back", 88, False),
        ("7-Color Flush", 181, False),
        ("7-Color Flush Back", 182, False),
        ("R-G-B Flush", 183, False),
        ("R-G-B Flush Back", 184, False),
        ("Y-C-P Flush", 185, False),
        ("Y-C-P Flush Back", 186, False),
        ("7-Color Flush Close", 187, False),
        ("7-Color Flush Open", 188, False),
        ("R-G-B Flush Close", 189, False),
        ("R-G-B Flush Open", 190, False),
        ("Y-C-P Flush Close", 191, False),
        ("Y-C-P Flush Open", 192, False),
    ],
    "Curtain": [
        ("7-Color Close", 57, False),
        ("7-Color Open", 58, False),
        ("R-G-B Close", 59, False),
        ("R-G-B Open", 60, False),
        ("Y-C-P Close", 61, False),
        ("Y-C-P Open", 62, False),
        ("Red Close", 63, False),
        ("Red Open", 64, False),
        ("Green Close", 65, False),
        ("Green Open", 66, False),
        ("Blue Close", 67, False),
        ("Blue Open", 68, False),
        ("Yellow Close", 69, False),
        ("Yellow Open", 70, False),
        ("Cyan Close", 71, False),
        ("Cyan Open", 72, False),
        ("Purple Close", 73, False),
        ("Purple Open", 74, False),
        ("White Close", 75, False),
        ("White Open", 76, False),
    ],
    "Trans": [
        ("7-Color Trans", 3, False),
        ("7-Color Trans Back", 4, False),
        ("R-G-B Trans", 5, False),
        ("R-G-B Trans Back", 6, False),
        ("Y-C-P Trans", 7, False),
        ("Y-C-P Trans Back", 8, False),
        ("6-Color to Red", 9, False),
        ("6-Color to Red Back", 10, False),
        ("6-Color to Green", 11, False),
        ("6-Color to Green Back", 12, False),
        ("6-Color to Blue", 13, False),
        ("6-Color to Blue Back", 14, False),
        ("6-Color to Cyan", 15, False),
        ("6-Color to Cyan Back", 16, False),
        ("6-Color to Yellow", 17, False),
        ("6-Color to Yellow Back", 18, False),
        ("6-Color to Purple", 19, False),
        ("6-Color to Purple Back", 20, False),
        ("6-Color to White", 21, False),
        ("6-Color to White Back", 22, False),
    ],
    "Water": [
        ("7-Color Water", 39, False),
        ("7-Color Water Back", 40, False),
        ("R-G-B Water", 41, False),
        ("R-G-B Water Back", 42, False),
        ("Y-C-P Water", 43, False),
        ("Y-C-P Water Back", 44, False),
        ("R-G Water", 45, False),
        ("R-G Water Back", 46, False),
        ("G-B Water", 47, False),
        ("G-B Water Back", 48, False),
        ("Y-B Water", 49, False),
        ("Y-B Water Back", 50, False),
        ("Y-C Water", 51, False),
        ("Y-C Water Back", 52, False),
        ("C-P Water", 53, False),
        ("C-P Water Back", 54, False),
        ("White Water", 55, False),
        ("White Water Back", 56, False),
    ],
    "Flow": [
        ("W-R-W Flow", 143, False),
        ("W-R-W Flow Back", 144, False),
        ("W-G-W Flow", 145, False),
        ("W-G-W Flow Back", 146, False),
        ("W-B-W Flow", 147, False),
        ("W-B-W Flow Back", 148, False),
        ("W-Y-W Flow", 149, False),
        ("W-Y-W Flow Back", 150, False),
        ("W-C-W Flow", 151, False),
        ("W-C-W Flow Back", 152, False),
        ("W-P-W Flow", 153, False),
        ("W-P-W Flow Back", 154, False),
        ("R-W-R Flow", 155, False),
        ("R-W-R Flow Back", 156, False),
        ("G-W-G Flow", 157, False),
        ("G-W-G Flow Back", 158, False),
        ("B-W-B Flow", 159, False),
        ("B-W-B Flow Back", 160, False),
        ("Y-W-Y Flow", 161, False),
        ("Y-W-Y Flow Back", 162, False),
        ("C-W-C Flow", 163, False),
        ("C-W-C Flow Back", 164, False),
        ("P-W-P Flow", 165, False),
        ("P-W-P Flow Back", 166, False),
    ],
    "Tail": [
        ("7-Color Tail", 23, False),
        ("7-Color Tail Back", 24, False),
        ("Red Tail", 25, False),
        ("Red Tail Back", 26, False),
        ("Green Tail", 27, False),
        ("Green Tail Back", 28, False),
        ("Blue Tail", 29, False),
        ("Blue Tail Back", 30, False),
        ("Yellow Tail", 31, False),
        ("Yellow Tail Back", 32, False),
        ("Cyan Tail", 33, False),
        ("Cyan Tail Back", 34, False),
        ("Purple Tail", 35, False),
        ("Purple Tail Back", 36, False),
        ("White Tail", 37, False),
        ("White Tail Back", 38, False),
    ],
    "Run": [
        ("Red Running", 89, False),
        ("Green Running", 91, False),
        ("Blue Running", 93, False),
        ("Yellow Running", 95, False),
        ("Cyan Running", 97, False),
        ("Purple Running", 99, False),
        ("White Running", 101, False),
        ("7-Color Running", 103, False),
        ("R-G-B Running", 105, False),
        ("Y-C-P Running", 107, False),
        ("B-P-C-Y Running", 109, False),
        ("B-G-C-Y Running", 111, False),
        ("Red-Dot in White Running", 113, False),
        ("Green-Dot in Red Running", 115, False),
        ("Blue-Dot in Green Running", 117, False),
        ("Yellow-Dot in Blue Running", 119, False),
        ("Cyan-Dot in Yellow Running", 121, False),
        ("Purple-Dot in Cyan Running", 123, False),
        ("White-Dot in Purple Running", 125, False),
        ("White-Dot in Red Running", 127, False),
        ("7-Color in Red Running", 129, False),
        ("7-Color in Green Running", 131, False),
        ("7-Color in Blue Running", 133, False),
        ("7-Color in Yellow Running", 135, False),
        ("7-Color in Cyan Running", 137, False),
        ("7-Color in Purple Running", 139, False),
        ("7-Color in White Running", 141, False),
        ("Green-Dot in Blue Running", 167, False),
        ("Green-Dot in Red Running", 169, False),
        ("Red-Dot in Blue Running", 171, False),
        ("Cyan-Dot in Yellow Running", 173, False),
        ("Yellow-Dot in Purple Running", 175, False),
        ("White-Dot in Yellow Running", 177, False),
        ("Yellow-Dot in White Running", 179, False),
    ],
    "RunBack": [
        ("Red Run Back", 90, False),
        ("Green Run Back", 92, False),
        ("Blue Run Back", 94, False),
        ("Yellow Run Back", 96, False),
        ("Cyan Run Back", 98, False),
        ("Purple Run Back", 100, False),
        ("White Run Back", 102, False),
        ("7-Color Run Back", 104, False),
        ("R-G-B Run Back", 106, False),
        ("Y-C-P Run Back", 108, False),
        ("B-P-C-Y Run Back", 110, False),
        ("B-G-C-Y Run Back", 112, False),
        ("Red-Dot in White Run Back", 114, False),
        ("Green-Dot in Red Run Back", 116, False),
        ("Blue-Dot in Green Run Back", 118, False),
        ("Yellow-Dot in Blue Run Back", 120, False),
        ("Cyan-Dot in Yellow Run Back", 122, False),
        ("Purple-Dot in Cyan Run Back", 124, False),
        ("White-Dot in Purple Run Back", 126, False),
        ("White-Dot in Red Run Back", 128, False),
        ("7-Color in Red Run Back", 130, False),
        ("7-Color in Green Run Back", 132, False),
        ("7-Color in Blue Run Back", 134, False),
        ("7-Color in Yellow Run Back", 136, False),
        ("7-Color in Cyan Run Back", 138, False),
        ("7-Color in Purple Run Back", 140, False),
        ("7-Color in White Run Back", 142, False),
        ("Green-Dot in Blue Run Back", 168, False),
        ("Green-Dot in Red Run Back", 170, False),
        ("Red-Dot in Blue Run Back", 172, False),
        ("Cyan-Dot in Yellow Run Back", 174, False),
        ("Yellow-Dot in Purple Run Back", 176, False),
        ("White-Dot in Yellow Run Back", 178, False),
        ("Yellow-Dot in White Run Back", 180, False),
    ],
    "Scenes": [
        ("Sunrise", 1, True),
        ("Sunset", 2, True),
        ("Birthday", 3, True),
        ("Candlelight", 4, True),
        ("Fireworks", 5, True),
        ("Party", 6, True),
        ("Dating", 7, True),
        ("Starry sky", 8, True),
        ("Romantic", 9, True),
        ("Disco", 10, True),
        ("Rainbow", 11, True),
        ("Movie", 12, True),
        ("Christmas", 13, True),
        ("Flowing", 14, True),
        ("Sleeping", 15, True),
        ("Ocean", 16, True),
        ("Forest", 17, True),
        ("Reading", 18, True),
        ("Working", 19, True),
        ("Dazzle", 20, True),
        ("Gentle", 21, True),
        ("Wedding", 22, True),
        ("Snow", 23, True),
        ("Fire", 24, True),
        ("Lightning", 25, True),
        ("Valentine's Day", 26, True),
        ("Halloween", 27, True),
        ("Warning", 28, True),
    ]
}
