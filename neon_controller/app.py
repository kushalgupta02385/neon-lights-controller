"""
Neon Lights Studio - Modern Desktop Controller for MagicLantern & LED Neon Rope Lights
Engineered with Reverse-Engineered 9-Byte BLE Protocol, Windows WASAPI Loopback Audio Capture,
and 241 Dynamic Lighting Modes & Procedural Ambient Scenes.
"""

import colorsys
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

from .ble_manager import BLEManager
from .audio_manager import AudioManager
from .scene_engine import SceneEngine
from .protocol import (
    PRESET_COLORS,
    MODE_CATEGORIES,
    EXTERNAL_MIC_EQ_MODES,
    PIN_SEQUENCES,
    NAME_FILTER_PREFIXES,
)

# Configure modern dark cyber theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class NeonApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Neon Lights Studio Pro  •  MagicLantern BLE Controller")
        self.geometry("1180x800")
        self.minsize(980, 680)
        self.configure(fg_color="#0B0E14")

        # Set Window Icon if present
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # State Variables
        self.is_powered_on = True
        self.current_r = 0
        self.current_g = 240
        self.current_b = 255
        self.current_brightness = 100
        self.current_speed = 80
        self.active_mode_name = "Solid Neon Cyan"
        self.custom_colors = [
            (255, 0, 85), (0, 240, 255), (170, 0, 255), (0, 255, 120),
            (255, 230, 0), (255, 100, 0), (255, 255, 255), (40, 40, 40)
        ]
        self.log_messages = []
        self._last_ui_frame_time = 0.0
        self._last_vu_time = 0.0
        self._device_cards: Dict[str, dict] = {}

        # Backend Controllers
        self.ble = BLEManager()
        self.audio = AudioManager(self.ble)
        self.audio.set_master_brightness(self.current_brightness / 100.0)
        self.scene_engine = SceneEngine(self.ble)

        # Wire Up Callbacks
        self.ble.on_connection_changed = self._on_ble_connection_changed
        self.ble.on_scan_finished = self._on_ble_scan_finished
        self.ble.on_error = self._on_ble_error
        self.ble.on_packet_sent = self._on_ble_packet_sent
        self.audio.on_level = self._on_audio_level
        self.audio.on_status_change = self._on_audio_status_change
        self.scene_engine.on_frame = self._on_scene_frame

        # Build Complete Modern GUI
        self._setup_ui()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Auto scan & connect to rope lights on startup
        self.after(400, self._auto_connect_startup)

    def _setup_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # =====================================================================
        # TOP CYBER-STUDIO HEADER
        # =====================================================================
        self.header_frame = ctk.CTkFrame(
            self,
            corner_radius=14,
            fg_color="#121624",
            border_width=1,
            border_color="#1F263D"
        )
        self.header_frame.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)

        # Left Branding Title
        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=18, pady=10, sticky="w")

        title_row = ctk.CTkFrame(title_box, fg_color="transparent")
        title_row.pack(anchor="w")

        self.title_label = ctk.CTkLabel(
            title_row,
            text="✨ NEON STUDIO",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#00F0FF",
        )
        self.title_label.pack(side="left")

        pro_badge = ctk.CTkLabel(
            title_row,
            text="PRO v6.11",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#A855F7",
            fg_color="#201533",
            corner_radius=6,
            padx=6,
            pady=1,
        )
        pro_badge.pack(side="left", padx=(8, 0))

        self.subtitle_label = ctk.CTkLabel(
            title_box,
            text="MagicLantern BLE Light Controller • WASAPI Game Audio Sync",
            font=ctk.CTkFont(size=11),
            text_color="#8292A6",
        )
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        # Center Status Pill
        center_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        center_box.grid(row=0, column=1, padx=10, pady=10)

        self.status_pill = ctk.CTkButton(
            center_box,
            text="🔴 Disconnected",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2D151D",
            hover_color="#3D1D28",
            text_color="#FF4757",
            corner_radius=18,
            height=32,
            border_width=1,
            border_color="#4D1D2B",
            command=self._open_device_tab,
        )
        self.status_pill.pack(side="left", padx=6)

        # Right Power Toggle & Scan
        right_header = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        right_header.grid(row=0, column=2, padx=18, pady=10, sticky="e")

        self.quick_scan_btn = ctk.CTkButton(
            right_header,
            text="🔄 Scan",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1D2438",
            hover_color="#2B3654",
            text_color="#CBD5E1",
            width=68,
            height=34,
            corner_radius=8,
            command=self._quick_scan_and_connect,
        )
        self.quick_scan_btn.pack(side="left", padx=(0, 8))

        self.power_btn = ctk.CTkButton(
            right_header,
            text="⚡ POWER ON",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#059669",
            hover_color="#10B981",
            text_color="#FFFFFF",
            width=130,
            height=36,
            corner_radius=18,
            border_width=1,
            border_color="#047857",
            command=self._toggle_power,
        )
        self.power_btn.pack(side="left")

        # =====================================================================
        # MAIN TAB VIEW (MODERN STYLED SEGMENTED NAVIGATION)
        # =====================================================================
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=14,
            fg_color="#101420",
            segmented_button_fg_color="#151B2B",
            segmented_button_selected_color="#00F0FF",
            segmented_button_selected_hover_color="#00D0DF",
            text_color="#FFFFFF",
        )
        self.tabview.grid(row=1, column=0, padx=16, pady=4, sticky="nsew")

        # Add Dedicated Tabs
        self.tab_color = self.tabview.add("🎨 Colors & White")
        self.tab_modes = self.tabview.add("⚡ Dynamic Modes (213)")
        self.tab_audio = self.tabview.add("🔊 Game & Music Sync")
        self.tab_device = self.tabview.add("⚙️ Strip & Settings")

        # Build Each Tab Content
        self._build_color_tab()
        self._build_modes_tab()
        self._build_audio_tab()
        self._build_device_tab()

        # =====================================================================
        # BOTTOM PERSISTENT CONTROL DECK
        # =====================================================================
        self.dock_frame = ctk.CTkFrame(
            self,
            corner_radius=14,
            fg_color="#121624",
            border_width=1,
            border_color="#1F263D",
            height=64
        )
        self.dock_frame.grid(row=2, column=0, padx=16, pady=(4, 10), sticky="ew")
        self.dock_frame.grid_columnconfigure(1, weight=1)
        self.dock_frame.grid_columnconfigure(2, weight=1)

        # Left: Live Preview Swatch & Active Name
        dock_preview_box = ctk.CTkFrame(self.dock_frame, fg_color="transparent")
        dock_preview_box.grid(row=0, column=0, padx=16, pady=8, sticky="w")

        self.dock_preview_swatch = tk.Canvas(
            dock_preview_box,
            width=38,
            height=38,
            bg="#00F0FF",
            highlightthickness=0,
            relief="flat",
        )
        self.dock_preview_swatch.pack(side="left", padx=(0, 10))

        dock_text_box = ctk.CTkFrame(dock_preview_box, fg_color="transparent")
        dock_text_box.pack(side="left")

        self.dock_active_label = ctk.CTkLabel(
            dock_text_box,
            text="Solid Neon Cyan",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#FFFFFF",
        )
        self.dock_active_label.pack(anchor="w")

        self.dock_hex_label = ctk.CTkLabel(
            dock_text_box,
            text="HEX: #00F0FF  |  RGB: (0, 240, 255)",
            font=ctk.CTkFont(size=10),
            text_color="#8292A6",
        )
        self.dock_hex_label.pack(anchor="w")

        # Middle: Persistent Brightness Quick Slider
        dock_bright_box = ctk.CTkFrame(self.dock_frame, fg_color="transparent")
        dock_bright_box.grid(row=0, column=1, padx=14, pady=8, sticky="ew")
        dock_bright_box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            dock_bright_box,
            text="☀️ Brightness:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#E2E8F0"
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        self.dock_brightness_slider = ctk.CTkSlider(
            dock_bright_box,
            from_=1,
            to=100,
            number_of_steps=99,
            progress_color="#00F0FF",
            command=self._on_brightness_slide,
        )
        self.dock_brightness_slider.set(self.current_brightness)
        self.dock_brightness_slider.grid(row=0, column=1, padx=4, sticky="ew")

        self.dock_brightness_lbl = ctk.CTkLabel(
            dock_bright_box,
            text="100%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00F0FF",
            width=36
        )
        self.dock_brightness_lbl.grid(row=0, column=2, padx=(4, 0), sticky="e")

        # Right: Persistent Speed Quick Slider
        dock_speed_box = ctk.CTkFrame(self.dock_frame, fg_color="transparent")
        dock_speed_box.grid(row=0, column=2, padx=14, pady=8, sticky="ew")
        dock_speed_box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            dock_speed_box,
            text="⚡ Speed:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#E2E8F0"
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        self.dock_speed_slider = ctk.CTkSlider(
            dock_speed_box,
            from_=1,
            to=100,
            number_of_steps=99,
            progress_color="#A855F7",
            command=self._on_speed_slide,
        )
        self.dock_speed_slider.set(self.current_speed)
        self.dock_speed_slider.grid(row=0, column=1, padx=4, sticky="ew")

        self.dock_speed_lbl = ctk.CTkLabel(
            dock_speed_box,
            text="80%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#A855F7",
            width=36
        )
        self.dock_speed_lbl.grid(row=0, column=2, padx=(4, 0), sticky="e")

        # Far Right: Status Message
        self.footer_status = ctk.CTkLabel(
            self.dock_frame,
            text="Ready.",
            font=ctk.CTkFont(size=10),
            text_color="#8292A6",
            width=110
        )
        self.footer_status.grid(row=0, column=3, padx=(4, 16), sticky="e")

    # =========================================================================
    # TAB 1: COLOR & LIGHTING
    # =========================================================================
    def _build_color_tab(self):
        tab = self.tab_color
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # Left Column: Sliders & Color Temperature
        left_col = ctk.CTkFrame(tab, corner_radius=12, fg_color="#141826", border_width=1, border_color="#1F253B")
        left_col.grid(row=0, column=0, padx=(8, 5), pady=8, sticky="nsew")
        left_col.grid_columnconfigure(1, weight=1)

        # Large Live Color Glow Canvas
        self.preview_canvas = tk.Canvas(
            left_col,
            height=75,
            bg="#00F0FF",
            highlightthickness=0,
            relief="flat",
        )
        self.preview_canvas.grid(row=0, column=0, columnspan=2, padx=18, pady=(16, 6), sticky="ew")

        self.preview_label = ctk.CTkLabel(
            left_col,
            text="HEX: #00F0FF  |  RGB: (0, 240, 255)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#94A3B8",
        )
        self.preview_label.grid(row=1, column=0, columnspan=2, padx=18, pady=(0, 12))

        # Brightness Slider
        ctk.CTkLabel(left_col, text="Brightness Level", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=2, column=0, padx=(18, 8), pady=3, sticky="w"
        )
        self.brightness_label = ctk.CTkLabel(left_col, text="100%", font=ctk.CTkFont(size=12, weight="bold"), text_color="#00F0FF")
        self.brightness_label.grid(row=2, column=1, padx=(0, 18), pady=3, sticky="e")

        self.brightness_slider = ctk.CTkSlider(
            left_col,
            from_=1,
            to=100,
            number_of_steps=99,
            progress_color="#00F0FF",
            command=self._on_brightness_slide,
        )
        self.brightness_slider.set(100)
        self.brightness_slider.grid(row=3, column=0, columnspan=2, padx=18, pady=(0, 4), sticky="ew")

        # Quick Brightness Buttons
        quick_bright_box = ctk.CTkFrame(left_col, fg_color="transparent")
        quick_bright_box.grid(row=4, column=0, columnspan=2, padx=18, pady=(0, 12), sticky="ew")
        for pct in [10, 25, 50, 75, 100]:
            btn = ctk.CTkButton(
                quick_bright_box,
                text=f"{pct}%",
                width=48,
                height=26,
                fg_color="#1E2438",
                hover_color="#2A334E",
                font=ctk.CTkFont(size=11),
                command=lambda p=pct: self._set_brightness_preset(p),
            )
            btn.pack(side="left", expand=True, padx=2)

        # Red Channel
        ctk.CTkLabel(left_col, text="🔴 Red Channel", text_color="#FF4565", font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=5, column=0, padx=(18, 8), pady=2, sticky="w"
        )
        self.r_val_label = ctk.CTkLabel(left_col, text=str(self.current_r), font=ctk.CTkFont(size=11))
        self.r_val_label.grid(row=5, column=1, padx=(0, 18), pady=2, sticky="e")
        self.r_slider = ctk.CTkSlider(left_col, from_=0, to=255, number_of_steps=255, progress_color="#FF4565", command=self._on_rgb_slide)
        self.r_slider.set(self.current_r)
        self.r_slider.grid(row=6, column=0, columnspan=2, padx=18, pady=(0, 4), sticky="ew")

        # Green Channel
        ctk.CTkLabel(left_col, text="🟢 Green Channel", text_color="#00E676", font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=7, column=0, padx=(18, 8), pady=2, sticky="w"
        )
        self.g_val_label = ctk.CTkLabel(left_col, text=str(self.current_g), font=ctk.CTkFont(size=11))
        self.g_val_label.grid(row=7, column=1, padx=(0, 18), pady=2, sticky="e")
        self.g_slider = ctk.CTkSlider(left_col, from_=0, to=255, number_of_steps=255, progress_color="#00E676", command=self._on_rgb_slide)
        self.g_slider.set(self.current_g)
        self.g_slider.grid(row=8, column=0, columnspan=2, padx=18, pady=(0, 4), sticky="ew")

        # Blue Channel
        ctk.CTkLabel(left_col, text="🔵 Blue Channel", text_color="#2979FF", font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=9, column=0, padx=(18, 8), pady=2, sticky="w"
        )
        self.b_val_label = ctk.CTkLabel(left_col, text=str(self.current_b), font=ctk.CTkFont(size=11))
        self.b_val_label.grid(row=9, column=1, padx=(0, 18), pady=2, sticky="e")
        self.b_slider = ctk.CTkSlider(left_col, from_=0, to=255, number_of_steps=255, progress_color="#2979FF", command=self._on_rgb_slide)
        self.b_slider.set(self.current_b)
        self.b_slider.grid(row=10, column=0, columnspan=2, padx=18, pady=(0, 12), sticky="ew")

        # Color Temperature CCT
        ctk.CTkLabel(left_col, text="☀️ CCT White Temperature (Warm / Cold)", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=11, column=0, padx=(18, 8), pady=2, sticky="w"
        )
        self.cct_slider = ctk.CTkSlider(
            left_col,
            from_=0,
            to=100,
            number_of_steps=100,
            progress_color="#FFB300",
            command=self._on_cct_slide,
        )
        self.cct_slider.set(50)
        self.cct_slider.grid(row=12, column=0, columnspan=2, padx=18, pady=(0, 16), sticky="ew")

        # Right Column: Color Swatches & Custom Saved Palettes
        right_col = ctk.CTkFrame(tab, corner_radius=12, fg_color="#141826", border_width=1, border_color="#1F253B")
        right_col.grid(row=0, column=1, padx=(5, 8), pady=8, sticky="nsew")

        ctk.CTkLabel(
            right_col,
            text="✨ Studio Cyber-Neon Palettes",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F1F5F9",
        ).pack(anchor="w", padx=18, pady=(16, 8))

        # 4x4 Grid of Presets
        swatch_grid = ctk.CTkFrame(right_col, fg_color="transparent")
        swatch_grid.pack(fill="x", padx=14, pady=4)

        for i, (name, hex_code, (r, g, b)) in enumerate(PRESET_COLORS):
            row = i // 4
            col = i % 4
            btn = ctk.CTkButton(
                swatch_grid,
                text=name,
                fg_color=hex_code,
                hover_color=hex_code,
                text_color="#000000" if sum((r, g, b)) > 380 else "#FFFFFF",
                font=ctk.CTkFont(size=9, weight="bold"),
                width=52,
                height=42,
                corner_radius=10,
                border_width=1,
                border_color="#2D354E",
                command=lambda r=r, g=g, b=b: self._apply_color(r, g, b),
            )
            btn.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            swatch_grid.grid_columnconfigure(col, weight=1)

        # Custom Favorites
        ctk.CTkLabel(
            right_col,
            text="⭐ Custom Favorites",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F1F5F9",
        ).pack(anchor="w", padx=18, pady=(18, 6))

        self.custom_swatches_box = ctk.CTkFrame(right_col, fg_color="transparent")
        self.custom_swatches_box.pack(fill="x", padx=14, pady=4)
        self._refresh_custom_swatches()

        save_fav_btn = ctk.CTkButton(
            right_col,
            text="💾 Save Active Color to Favorites",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1E2438",
            hover_color="#2A334E",
            height=34,
            corner_radius=8,
            command=self._save_to_favorites,
        )
        save_fav_btn.pack(fill="x", padx=18, pady=(12, 16))

    def _refresh_custom_swatches(self):
        for widget in self.custom_swatches_box.winfo_children():
            widget.destroy()

        for idx, (r, g, b) in enumerate(self.custom_colors):
            hex_c = f"#{r:02x}{g:02x}{b:02x}"
            btn = ctk.CTkButton(
                self.custom_swatches_box,
                text="",
                fg_color=hex_c,
                hover_color=hex_c,
                width=44,
                height=36,
                corner_radius=8,
                border_width=1,
                border_color="#364062",
                command=lambda r=r, g=g, b=b: self._apply_color(r, g, b),
            )
            btn.pack(side="left", expand=True, padx=3)

    def _save_to_favorites(self):
        color = (self.current_r, self.current_g, self.current_b)
        self.custom_colors.pop(0)
        self.custom_colors.append(color)
        self._refresh_custom_swatches()
        self._log(f"Saved {color} to favorites.")

    # =========================================================================
    # TAB 2: DYNAMIC MODES (213 HARDWARE EFFECTS)
    # =========================================================================
    def _build_modes_tab(self):
        tab = self.tab_modes
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Top Bar: Category Filter Pills, Search Bar
        top_bar = ctk.CTkFrame(tab, corner_radius=12, fg_color="#141826", border_width=1, border_color="#1F253B")
        top_bar.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="ew")

        # Category pills
        cat_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        cat_box.pack(fill="x", padx=14, pady=(10, 6))

        # Hardware mode categories (excluding Scenes, which have their own dedicated tab)
        hw_categories = ["All (213)"] + [k for k in MODE_CATEGORIES.keys() if k != "Scenes"]
        self.cat_var = ctk.StringVar(value="All (213)")

        ctk.CTkLabel(cat_box, text="Category:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6))

        self.cat_menu = ctk.CTkOptionMenu(
            cat_box,
            values=hw_categories,
            variable=self.cat_var,
            width=160,
            command=self._on_category_changed,
        )
        self.cat_menu.pack(side="left", padx=(0, 14))

        ctk.CTkLabel(cat_box, text="🔍 Search:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6))
        self.search_entry = ctk.CTkEntry(cat_box, placeholder_text="e.g. 7-color, water, flow, tail, run, jump...", width=240)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_modes())

        # Scrollable Mode Card Grid
        self.modes_scroll = ctk.CTkScrollableFrame(tab, corner_radius=12, fg_color="#141826")
        self.modes_scroll.grid(row=1, column=0, padx=8, pady=4, sticky="nsew")
        self.modes_scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._populate_mode_cards()

    def _populate_mode_cards(self):
        for widget in self.modes_scroll.winfo_children():
            widget.destroy()

        category = self.cat_var.get()
        search_query = self.search_entry.get().strip().lower()

        cards = []
        for cat_name, mode_list in MODE_CATEGORIES.items():
            if cat_name == "Scenes":
                continue  # Displayed in Dedicated Scenes Tab
            if category != "All (213)" and category != cat_name:
                continue
            for name, cmd_id, is_scene in mode_list:
                if search_query and (search_query not in name.lower() and search_query not in cat_name.lower()):
                    continue
                cards.append((cat_name, name, cmd_id))

        for idx, (cat_name, name, cmd_id) in enumerate(cards):
            row = idx // 4
            col = idx % 4

            icon = "⚡"
            if "Water" in cat_name:
                icon = "🌊"
            elif "Flow" in cat_name:
                icon = "💫"
            elif "Tail" in cat_name or "Run" in cat_name:
                icon = "🏎️"
            elif "Curtain" in cat_name:
                icon = "🎪"

            is_active = (self.active_mode_name == name)
            card = ctk.CTkButton(
                self.modes_scroll,
                text=f"{icon} {name}\n[{cat_name} • #{cmd_id}]",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#00F0FF" if is_active else "#1B2133",
                hover_color="#00D0DF" if is_active else "#27304A",
                text_color="#000000" if is_active else "#E2E8F0",
                border_width=1,
                border_color="#00F0FF" if is_active else "#2A3350",
                height=52,
                corner_radius=10,
                command=lambda n=name, c=cmd_id: self._select_hardware_mode(n, c),
            )
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

    def _on_category_changed(self, choice):
        self._populate_mode_cards()

    def _filter_modes(self):
        self._populate_mode_cards()

    def _select_hardware_mode(self, name: str, cmd_id: int):
        """Activates a hardware dynamic mode (Group 0 to 7) with power waking and speed setting."""
        self.active_mode_name = name
        self.audio.stop()
        self.scene_engine.stop()

        # Disarm hardware mic if it was active
        if hasattr(self, "hw_mic_switch"):
            self.hw_mic_switch.deselect()
        self.ble.disarm_external_mic(self.current_r, self.current_g, self.current_b)

        # Update power button if needed
        self.is_powered_on = True
        self.power_btn.configure(text="⚡ POWER ON", fg_color="#059669")

        # Send Mode to hardware (BLEManager enqueues power ON, mode packet, speed, brightness)
        self.ble.set_mode(cmd_id)
        self.ble.set_speed(self.current_speed)
        self.ble.set_brightness(self.current_brightness)

        self._log(f"Activated Dynamic Mode #{cmd_id}: {name}")
        self.footer_status.configure(text=f"Mode: #{cmd_id} {name}")
        self.dock_active_label.configure(text=name)
        self.dock_hex_label.configure(text=f"Hardware Mode #{cmd_id}")
        self._populate_mode_cards()

    # =========================================================================
    # TAB 3: AMBIENT SCENES (28 ATMOSPHERIC SCENES)
    # =========================================================================
    def _build_scenes_tab(self):
        tab = self.tab_scenes
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Header card explaining ambient scenes
        info_bar = ctk.CTkFrame(tab, corner_radius=12, fg_color="#141826", border_width=1, border_color="#1F253B")
        info_bar.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="ew")

        ctk.CTkLabel(
            info_bar,
            text="🌌 Ambient Cinematic Scenes  (28 Procedural & Hardware Atmospheres)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#A855F7",
        ).pack(anchor="w", padx=16, pady=(10, 2))

        ctk.CTkLabel(
            info_bar,
            text="Simulates living atmospheric lighting with bespoke color gradients, realistic flame flickers, auroras, and party pulses. Works on all light models including MELK-OA.",
            font=ctk.CTkFont(size=11),
            text_color="#8292A6",
        ).pack(anchor="w", padx=16, pady=(0, 10))

        # Scrollable Scene Grid
        self.scenes_scroll = ctk.CTkScrollableFrame(tab, corner_radius=12, fg_color="#141826")
        self.scenes_scroll.grid(row=1, column=0, padx=8, pady=4, sticky="nsew")
        self.scenes_scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._populate_scene_cards()

    def _populate_scene_cards(self):
        for widget in self.scenes_scroll.winfo_children():
            widget.destroy()

        scene_icons = {
            "Sunrise": "🌅", "Sunset": "🌇", "Birthday": "🎂", "Candlelight": "🕯️",
            "Fireworks": "🎆", "Party": "🎉", "Dating": "🌹", "Starry sky": "✨",
            "Romantic": "💖", "Disco": "🪩", "Rainbow": "🌈", "Movie": "🎬",
            "Christmas": "🎄", "Flowing": "🌊", "Sleeping": "🌙", "Ocean": "🐬",
            "Forest": "🌲", "Reading": "📖", "Working": "💻", "Dazzle": "💎",
            "Gentle": "🌸", "Wedding": "💍", "Snow": "❄️", "Fire": "🔥",
            "Lightning": "⚡", "Aurora": "🌌", "Cyberpunk": "🌆", "Neon Pulse": "💫",
        }

        scene_list = MODE_CATEGORIES.get("Scenes", [])
        for idx, (name, cmd_id, is_scene) in enumerate(scene_list):
            row = idx // 4
            col = idx % 4

            icon = scene_icons.get(name, "🎭")
            is_active = (self.active_mode_name == name and self.scene_engine.is_running())

            card = ctk.CTkButton(
                self.scenes_scroll,
                text=f"{icon} {name}\n[Scene #{cmd_id}]",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#A855F7" if is_active else "#1B2133",
                hover_color="#9333EA" if is_active else "#27304A",
                text_color="#FFFFFF" if is_active else "#E2E8F0",
                border_width=1,
                border_color="#A855F7" if is_active else "#2A3350",
                height=56,
                corner_radius=10,
                command=lambda n=name, c=cmd_id: self._select_ambient_scene(n, c),
            )
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

    def _select_ambient_scene(self, name: str, cmd_id: int):
        """Activates an ambient scene via hardware scene opcode + software procedural engine."""
        self.active_mode_name = name
        self.audio.stop()
        self.scene_engine.stop()

        # Disarm hardware mic if it was active
        if hasattr(self, "hw_mic_switch"):
            self.hw_mic_switch.deselect()
        self.ble.disarm_external_mic(self.current_r, self.current_g, self.current_b)

        self.is_powered_on = True
        self.power_btn.configure(text="⚡ POWER ON", fg_color="#059669")

        # Send hardware opcode 0x31 for MELK-OC/OT devices
        self.ble.set_scene(cmd_id)

        # Run ultra-smooth software procedural scene engine (guaranteeing it works on MELK-OA as well!)
        self.scene_engine.start_scene(scene_name=name, scene_id=cmd_id, speed_pct=self.current_speed, brightness_pct=self.current_brightness)

        self._log(f"Activated Ambient Scene #{cmd_id}: {name}")
        self.footer_status.configure(text=f"Scene: {name}")
        self.dock_active_label.configure(text=f"Scene: {name}")
        self.dock_hex_label.configure(text=f"Atmospheric Scene #{cmd_id}")
        self._populate_scene_cards()

    def _on_scene_frame(self, r: int, g: int, b: int):
        """Throttled UI callback when scene frame generates colors."""
        now = time.time()
        if now - self._last_ui_frame_time < 0.05:  # Cap at 20 FPS for UI canvas
            return
        self._last_ui_frame_time = now

        def update():
            try:
                hex_c = f"#{r:02x}{g:02x}{b:02x}"
                self.preview_canvas.configure(bg=hex_c)
                self.dock_preview_swatch.configure(bg=hex_c)
                self.preview_label.configure(text=f"SCENE: {self.active_mode_name} | RGB: ({r}, {g}, {b})")
                self.dock_hex_label.configure(text=f"HEX: {hex_c.upper()}  |  RGB: ({r}, {g}, {b})")
            except Exception:
                pass

        try:
            self.after(0, update)
        except Exception:
            pass

    # =========================================================================
    # TAB 4: GAME & MUSIC AUDIO SYNC (WASAPI LOOPBACK + MIC)
    # =========================================================================
    def _build_audio_tab(self):
        tab = self.tab_audio
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # Left Card: PC Game & Music Audio Reactive (WASAPI Loopback)
        pc_card = ctk.CTkFrame(tab, corner_radius=12, fg_color="#141826", border_width=1, border_color="#1F253B")
        pc_card.grid(row=0, column=0, padx=(8, 5), pady=8, sticky="nsew")
        pc_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            pc_card,
            text="🎮 PC Game & Laptop Audio Sync (WASAPI Loopback)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00F0FF",
        ).pack(anchor="w", padx=18, pady=(16, 4))

        ctk.CTkLabel(
            pc_card,
            text="Directly captures digital sound played by Games (Steam, Valorant, GTA), Spotify, YouTube, or Movies to your HDMI Monitor, Headphones, or Laptop Speakers with zero background noise.",
            font=ctk.CTkFont(size=11),
            text_color="#8E9AA8",
            wraplength=420,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 14))

        # Audio Output / Input Device Selector
        ctk.CTkLabel(pc_card, text="Audio Playback Source:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=18, pady=(0, 4))

        self.audio_devices = self.audio.get_audio_devices()
        dev_names = [d["name"] for d in self.audio_devices] or ["Default System Audio [Loopback]"]
        self.audio_dev_menu = ctk.CTkOptionMenu(
            pc_card,
            values=dev_names,
            width=380,
            command=self._on_audio_device_changed,
        )
        if dev_names:
            self.audio_dev_menu.set(dev_names[0])
        self.audio_dev_menu.pack(fill="x", padx=18, pady=(0, 12))

        # Reactive Algorithm
        ctk.CTkLabel(pc_card, text="Lighting Reaction Algorithm:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=18, pady=(0, 4))
        self.audio_mode_menu = ctk.CTkOptionMenu(
            pc_card,
            values=[
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
            ],
            command=lambda m: self.audio.set_mode(m),
        )
        self.audio_mode_menu.set("🌀 Rolling Lines (with Black Gaps)")
        self.audio_mode_menu.pack(fill="x", padx=18, pady=(0, 12))

        # Audio Sensitivity Slider
        ctk.CTkLabel(pc_card, text="Sound & Beat Sensitivity:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=18, pady=(0, 4))
        self.pc_sens_slider = ctk.CTkSlider(pc_card, from_=0.2, to=3.5, number_of_steps=66, command=lambda v: self.audio.set_sensitivity(v))
        self.pc_sens_slider.set(1.3)
        self.pc_sens_slider.pack(fill="x", padx=18, pady=(0, 14))

        # Live Animated VU Meter Canvas
        ctk.CTkLabel(pc_card, text="Live Audio Level Visualizer:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=18, pady=(0, 4))
        self.meter_canvas = tk.Canvas(pc_card, height=22, bg="#0C0E16", highlightthickness=0)
        self.meter_canvas.pack(fill="x", padx=18, pady=(0, 16))

        # Quick 1-Click Actions for the 2 New Music Sync Features
        quick_btn_frame = ctk.CTkFrame(pc_card, fg_color="transparent")
        quick_btn_frame.pack(fill="x", padx=18, pady=(0, 10))
        quick_btn_frame.grid_columnconfigure((0, 1), weight=1)

        self.quick_rolling_black_btn = ctk.CTkButton(
            quick_btn_frame,
            text="🌀 ROLLING W/ BLACK GAPS",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1E2438",
            hover_color="#00F0FF",
            text_color="#00F0FF",
            border_width=1,
            border_color="#00F0FF",
            height=34,
            corner_radius=8,
            command=self._quick_launch_rolling_black_sync,
        )
        self.quick_rolling_black_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.quick_beat_lines_btn = ctk.CTkButton(
            quick_btn_frame,
            text="📊 BEAT LINES (RHYTHM LAMP)",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1E2438",
            hover_color="#FFBF00",
            text_color="#FFBF00",
            border_width=1,
            border_color="#FFBF00",
            height=34,
            corner_radius=8,
            command=self._quick_launch_beat_lines_sync,
        )
        self.quick_beat_lines_btn.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        # Backward compatibility alias
        self.quick_rolling_btn = self.quick_rolling_black_btn

        # Big Action Button
        self.audio_sync_btn = ctk.CTkButton(
            pc_card,
            text="▶️ ACTIVATE GAME & MUSIC SYNC",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#00F0FF",
            hover_color="#00D0DF",
            text_color="#000000",
            height=42,
            corner_radius=10,
            command=self._toggle_pc_audio_sync,
        )
        self.audio_sync_btn.pack(fill="x", padx=18, pady=(0, 16))

        # Right Card: Hardware Controller Microphone
        hw_card = ctk.CTkFrame(tab, corner_radius=12, fg_color="#141826", border_width=1, border_color="#1F253B")
        hw_card.grid(row=0, column=1, padx=(5, 8), pady=8, sticky="nsew")
        hw_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hw_card,
            text="🎙️ Rope Light Controller Physical Mic",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FF4565",
        ).pack(anchor="w", padx=18, pady=(16, 4))

        ctk.CTkLabel(
            hw_card,
            text="Controls the physical microphone located on the rope light USB controller for standalone sound rhythm.",
            font=ctk.CTkFont(size=11),
            text_color="#8E9AA8",
            wraplength=420,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 14))

        self.hw_mic_switch = ctk.CTkSwitch(
            hw_card,
            text="Physical Controller Mic Enabled",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_hw_mic_toggle,
        )
        self.hw_mic_switch.pack(anchor="w", padx=18, pady=(0, 10))

        # Explicit disarm & unlock button
        self.hw_mic_disarm_btn = ctk.CTkButton(
            hw_card,
            text="🛑 Disarm & Exit Hardware Mic Mode",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#FF4757",
            hover_color="#E03A58",
            text_color="#FFFFFF",
            height=34,
            corner_radius=8,
            command=self._disarm_hw_mic_action,
        )
        self.hw_mic_disarm_btn.pack(fill="x", padx=18, pady=(0, 14))

        ctk.CTkLabel(hw_card, text="Hardware Mic Sensitivity:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=18, pady=(0, 4))
        self.hw_sens_slider = ctk.CTkSlider(hw_card, from_=0, to=100, number_of_steps=100, command=self._on_hw_sens_slide)
        self.hw_sens_slider.set(80)
        self.hw_sens_slider.pack(fill="x", padx=18, pady=(0, 16))

        ctk.CTkLabel(hw_card, text="Hardware Rhythm Modes (Onboard IC Chip):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=18, pady=(0, 2))
        ctk.CTkLabel(
            hw_card,
            text="Runs the controller's internal chip for addressable multi-color running & rolling waves along the rope light via the physical microphone:",
            font=ctk.CTkFont(size=10),
            text_color="#8E9AA8",
            wraplength=420,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 8))

        eq_grid = ctk.CTkFrame(hw_card, fg_color="transparent")
        eq_grid.pack(fill="x", padx=14, pady=4)
        eq_grid.grid_columnconfigure((0, 1), weight=1)

        self._hw_eq_buttons = {}
        eq_icons = {
            "Rolling": "🌀",
            "Rolling II": "🌊",
            "Energic": "⚡",
            "Energic II": "💥",
            "Rhythm": "🎵",
            "Rhythm II": "🎶",
            "Spectrum": "🌈",
            "Spectrum II": "✨",
        }

        for i, (eq_name, eq_id) in enumerate(EXTERNAL_MIC_EQ_MODES):
            row = i // 2
            col = i % 2
            icon = eq_icons.get(eq_name, "🎵")
            btn = ctk.CTkButton(
                eq_grid,
                text=f"{icon} {eq_name}",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#1E2438",
                hover_color="#2B3450",
                height=34,
                corner_radius=8,
                command=lambda e_id=eq_id, n=eq_name: self._set_hw_eq(e_id, n),
            )
            btn.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            self._hw_eq_buttons[eq_id] = btn

    def _on_audio_device_changed(self, choice):
        for dev in self.audio_devices:
            if dev["name"] == choice:
                self.audio.set_device(dev["id"], dev["is_loopback"])
                self._log(f"Selected audio source: {choice}")
                break

    def _toggle_pc_audio_sync(self):
        if self.audio.is_running():
            self.audio.stop()
            self.audio_sync_btn.configure(
                text="▶️ ACTIVATE GAME & MUSIC SYNC",
                fg_color="#00F0FF",
                hover_color="#00D0DF",
                text_color="#000000",
            )
            if hasattr(self, "quick_game_sync_btn"):
                self.quick_game_sync_btn.configure(fg_color="#182033", text_color="#00F0FF")
            self._log("Game & Music Sync deactivated.")
        else:
            self.scene_engine.stop()
            if hasattr(self, "hw_mic_switch"):
                self.hw_mic_switch.deselect()
            self.ble.disarm_external_mic(self.current_r, self.current_g, self.current_b)

            self.audio.set_base_color(self.current_r, self.current_g, self.current_b)
            self.audio.start()
            self.audio_sync_btn.configure(
                text="⏹️ STOP AUDIO SYNC",
                fg_color="#FF4565",
                hover_color="#E03A58",
                text_color="#FFFFFF",
            )
            if hasattr(self, "quick_game_sync_btn"):
                self.quick_game_sync_btn.configure(fg_color="#FF4565", text_color="#FFFFFF")
            self._log("Game & Music Sync activated!")

    def _quick_launch_rolling_black_sync(self):
        """1-Click quick launch for Rolling Lines with Black Gaps (Feature 1)."""
        mode_name = "🌀 Rolling Lines (with Black Gaps)"
        self.audio_mode_menu.set(mode_name)
        self.audio.set_mode(mode_name)
        self.audio.set_master_brightness(1.0)
        self.brightness_slider.set(100)
        if hasattr(self, "dock_brightness_slider"):
            self.dock_brightness_slider.set(100)
        if hasattr(self, "dock_brightness_lbl"):
            self.dock_brightness_lbl.configure(text="100%")
        if not self.audio.is_running():
            self._toggle_pc_audio_sync()
        self._log("Activated Rolling Lines (with Black Gaps): Multi-color lines with black spaces roll across rope light!")
        self.footer_status.configure(text="Music Sync: Rolling Lines with Black Gaps")

    def _quick_launch_beat_lines_sync(self):
        """1-Click quick launch for Beat Lines (VU Rhythm Lamp Bar) (Feature 2)."""
        mode_name = "📊 Beat Lines (VU Rhythm Lamp Bar)"
        self.audio_mode_menu.set(mode_name)
        self.audio.set_mode(mode_name)
        self.audio.set_master_brightness(1.0)
        self.brightness_slider.set(100)
        if hasattr(self, "dock_brightness_slider"):
            self.dock_brightness_slider.set(100)
        if hasattr(self, "dock_brightness_lbl"):
            self.dock_brightness_lbl.configure(text="100%")
        if not self.audio.is_running():
            self._toggle_pc_audio_sync()
        self._log("Activated Beat Lines (VU Rhythm Lamp Bar): Equalizer light shoots up and down with game/music beats!")
        self.footer_status.configure(text="Music Sync: Beat Lines Rhythm Lamp")

    def _quick_launch_rolling_music_sync(self):
        """Backwards compatible alias for Rolling Lines quick launch."""
        self._quick_launch_rolling_black_sync()

    def _quick_toggle_game_sync(self):
        self._toggle_pc_audio_sync()

    def _on_audio_status_change(self, running: bool, status_msg: str):
        def update():
            self.footer_status.configure(text=status_msg)
        self.after(0, update)

    def _on_audio_level(self, level: float, r: int, g: int, b: int):
        now = time.time()
        if now - self._last_vu_time < 0.04:  # Throttle VU redraw at ~25 FPS
            return
        self._last_vu_time = now

        def update():
            if not hasattr(self, "meter_canvas") or not self.meter_canvas.winfo_exists():
                return
            width = self.meter_canvas.winfo_width()
            self.meter_canvas.delete("all")
            if level > 0.02 and width > 0:
                bar_w = int(width * min(1.0, level))
                color_hex = f"#{r:02x}{g:02x}{b:02x}"
                self.meter_canvas.create_rectangle(0, 0, bar_w, 22, fill=color_hex, outline="")
                self.dock_preview_swatch.configure(bg=color_hex)
            else:
                # Idle state: clear meter and dark preview
                self.dock_preview_swatch.configure(bg="#0C0E16")
        self.after(0, update)

    def _on_hw_mic_toggle(self):
        is_on = self.hw_mic_switch.get() == 1
        if is_on:
            self.audio.stop()
            self.scene_engine.stop()
            self.ble.clear_stream()
            self.ble.set_power(True)
            self.ble.set_symphony_points(100)
            self.ble.set_speed(self.current_speed)
            sens_val = int(self.hw_sens_slider.get()) if hasattr(self, "hw_sens_slider") else 85
            self.ble.set_external_mic_sensitivity(sens_val)
            self.ble.set_external_mic_power(True)
            # Default to Rolling (mode 3)
            self.ble.set_external_mic_eq(3)
            self._log("Controller Physical Microphone: ON (Rolling Multi-Color Line Formation)")
            if hasattr(self, "_hw_eq_buttons"):
                for b_id, btn in self._hw_eq_buttons.items():
                    if b_id == 3:
                        btn.configure(fg_color="#00F0FF", text_color="#000000", hover_color="#00D0DF")
                    else:
                        btn.configure(fg_color="#1E2438", text_color="#FFFFFF", hover_color="#2B3450")
        else:
            self.ble.disarm_external_mic(self.current_r, self.current_g, self.current_b)
            self._log("Controller Physical Microphone: DISARMED & OFF (Restored static light)")
            if hasattr(self, "_hw_eq_buttons"):
                for btn in self._hw_eq_buttons.values():
                    btn.configure(fg_color="#1E2438", text_color="#FFFFFF", hover_color="#2B3450")

    def _disarm_hw_mic_action(self):
        if hasattr(self, "hw_mic_switch"):
            self.hw_mic_switch.deselect()
        self.ble.disarm_external_mic(self.current_r, self.current_g, self.current_b)
        self.active_mode_name = f"Solid #{self.current_r:02x}{self.current_g:02x}{self.current_b:02x}".upper()
        self.dock_active_label.configure(text=self.active_mode_name)
        self.dock_hex_label.configure(text=f"HEX: #{self.current_r:02x}{self.current_g:02x}{self.current_b:02x}".upper())
        self._log("Disarmed hardware microphone. Light state machine unlocked from mic loop.")
        self.footer_status.configure(text="Hardware Mic Disarmed")
        if hasattr(self, "_hw_eq_buttons"):
            for btn in self._hw_eq_buttons.values():
                btn.configure(fg_color="#1E2438", text_color="#FFFFFF", hover_color="#2B3450")

    def _on_hw_sens_slide(self, val):
        self.ble.set_external_mic_sensitivity(int(val))

    def _set_hw_eq(self, eq_id: int, name: str):
        self.hw_mic_switch.select()
        self.audio.stop()
        self.scene_engine.stop()
        self.ble.clear_stream()
        self.ble.set_power(True)
        self.ble.set_symphony_points(100)
        self.ble.set_speed(self.current_speed)
        sens_val = int(self.hw_sens_slider.get()) if hasattr(self, "hw_sens_slider") else 85
        self.ble.set_external_mic_sensitivity(sens_val)
        self.ble.set_external_mic_power(True)
        self.ble.set_external_mic_eq(eq_id)
        self.active_mode_name = f"Hardware Mic: {name}"
        self.dock_active_label.configure(text=self.active_mode_name)
        self.dock_hex_label.configure(text=f"Hardware IC Sound Mode #{eq_id}")
        self._log(f"Activated Hardware IC Rhythm Mode: {name} (#{eq_id})")
        self.footer_status.configure(text=f"Hardware Mic: {name}")

        # Highlight selected EQ button
        if hasattr(self, "_hw_eq_buttons"):
            for b_id, btn in self._hw_eq_buttons.items():
                if b_id == eq_id:
                    btn.configure(fg_color="#00F0FF", text_color="#000000", hover_color="#00D0DF")
                else:
                    btn.configure(fg_color="#1E2438", text_color="#FFFFFF", hover_color="#2B3450")

    # =========================================================================
    # TAB 5: STRIP CONFIGURATION & SETTINGS
    # =========================================================================
    def _build_device_tab(self):
        tab = self.tab_device
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(tab, corner_radius=12, fg_color="#141826")
        scroll.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # Discovered Bluetooth Devices
        conn_box = ctk.CTkFrame(scroll, corner_radius=10, fg_color="#1A2033")
        conn_box.pack(fill="x", padx=18, pady=(16, 14))

        head_row = ctk.CTkFrame(conn_box, fg_color="transparent")
        head_row.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            head_row,
            text="📡 Bluetooth Low Energy (BLE) Light Connections",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00F0FF",
        ).pack(side="left")

        self.scan_action_btn = ctk.CTkButton(
            head_row,
            text="🔄 Scan for Devices",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#00F0FF",
            hover_color="#00D0DF",
            text_color="#000000",
            width=130,
            command=self._start_scan,
        )
        self.scan_action_btn.pack(side="right")

        self.device_list_frame = ctk.CTkFrame(scroll, corner_radius=10, fg_color="#0F121C")
        self.device_list_frame.pack(fill="x", padx=18, pady=(0, 16))
        self.device_list_frame.grid_columnconfigure(0, weight=1)

        self.device_status_lbl = ctk.CTkLabel(
            self.device_list_frame,
            text="Searching for devices... Click 'Scan for Devices' to refresh.",
            font=ctk.CTkFont(size=11),
            text_color="#8E9AA8",
        )
        self.device_status_lbl.pack(padx=14, pady=16)

        # Pin Sequence Calibration
        pin_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color="#1A2033")
        pin_card.pack(fill="x", padx=18, pady=(0, 14))

        ctk.CTkLabel(
            pin_card,
            text="🎨 RGB Pin Sequence Calibration",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            pin_card,
            text="If Red displays as Green or Blue, adjust the channel wiring order below:",
            font=ctk.CTkFont(size=11),
            text_color="#8E9AA8",
        ).pack(anchor="w", padx=16, pady=(0, 8))

        pin_box = ctk.CTkFrame(pin_card, fg_color="transparent")
        pin_box.pack(anchor="w", padx=16, pady=(0, 14))

        self.pin_menu = ctk.CTkOptionMenu(
            pin_box,
            values=[name for name, _ in PIN_SEQUENCES],
            width=130,
        )
        self.pin_menu.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            pin_box,
            text="Apply Pin Sequence",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1E2438",
            hover_color="#2A334E",
            command=self._apply_pin_sequence,
        ).pack(side="left")

        # Strip Length IC Points
        strip_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color="#1A2033")
        strip_card.pack(fill="x", padx=18, pady=(0, 14))

        ctk.CTkLabel(
            strip_card,
            text="📏 LED Strip Length (IC Pixels / Points)",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(12, 4))

        strip_box = ctk.CTkFrame(strip_card, fg_color="transparent")
        strip_box.pack(anchor="w", padx=16, pady=(0, 14))

        ctk.CTkLabel(strip_box, text="LED Pixel Count: ").pack(side="left")
        self.strip_points_entry = ctk.CTkEntry(strip_box, width=75)
        self.strip_points_entry.insert(0, "100")
        self.strip_points_entry.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            strip_box,
            text="Set LED Length",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1E2438",
            hover_color="#2A334E",
            command=self._apply_strip_length,
        ).pack(side="left")

        # Clock Sync
        clock_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color="#1A2033")
        clock_card.pack(fill="x", padx=18, pady=(0, 14))

        ctk.CTkLabel(
            clock_card,
            text="⏰ Controller Clock Synchronization",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(12, 4))

        clock_box = ctk.CTkFrame(clock_card, fg_color="transparent")
        clock_box.pack(anchor="w", padx=16, pady=(0, 14))

        ctk.CTkButton(
            clock_box,
            text="Sync Laptop Time to Light",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1E2438",
            hover_color="#2A334E",
            command=self._sync_time,
        ).pack(side="left")

        # Live Protocol Packet Inspector
        log_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color="#0C0E16")
        log_card.pack(fill="x", padx=18, pady=(0, 16))

        log_head = ctk.CTkFrame(log_card, fg_color="transparent")
        log_head.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(log_head, text="📝 Live BLE Protocol Inspector:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")

        ctk.CTkButton(
            log_head,
            text="Clear",
            width=50,
            height=22,
            font=ctk.CTkFont(size=10),
            fg_color="#1E2438",
            command=self._clear_logs,
        ).pack(side="right")

        self.log_textbox = ctk.CTkTextbox(log_card, height=120, font=ctk.CTkFont(family="Consolas", size=10))
        self.log_textbox.pack(fill="x", padx=14, pady=(0, 14))

    def _sync_time(self):
        self.ble.sync_system_time()
        self._log("Synchronized laptop time to light controller.")
        messagebox.showinfo("Time Sync", "Controller clock synchronized with Windows system time.")

    def _clear_logs(self):
        self.log_textbox.delete("1.0", "end")

    def _apply_pin_sequence(self):
        choice = self.pin_menu.get()
        mapping = dict(PIN_SEQUENCES)
        order = mapping.get(choice, (0, 1, 2))
        self.ble.set_pin_sequence(order[0], order[1], order[2])
        self._log(f"Applied RGB Pin Sequence: {choice} {order}")
        messagebox.showinfo("Pin Sequence", f"Pin sequence set to {choice}.")

    def _apply_strip_length(self):
        try:
            pts = int(self.strip_points_entry.get())
            self.ble.set_symphony_points(pts)
            self._log(f"Configured strip pixel length: {pts}")
            messagebox.showinfo("Strip Length", f"Set addressable strip to {pts} LEDs.")
        except Exception as e:
            messagebox.showerror("Error", f"Invalid LED count: {e}")

    # =========================================================================
    # CORE COLOR & LIGHTING LOGIC
    # =========================================================================
    def _apply_color(self, r: int, g: int, b: int):
        self.current_r = r
        self.current_g = g
        self.current_b = b

        self.r_slider.set(r)
        self.g_slider.set(g)
        self.b_slider.set(b)
        self.r_val_label.configure(text=str(r))
        self.g_val_label.configure(text=str(g))
        self.b_val_label.configure(text=str(b))

        hex_c = f"#{r:02x}{g:02x}{b:02x}"
        self.preview_canvas.configure(bg=hex_c)
        self.dock_preview_swatch.configure(bg=hex_c)
        self.preview_label.configure(text=f"HEX: {hex_c.upper()}  |  RGB: ({r}, {g}, {b})")
        self.dock_hex_label.configure(text=f"HEX: {hex_c.upper()}  |  RGB: ({r}, {g}, {b})")
        self.dock_active_label.configure(text=f"Solid {hex_c.upper()}")

        # Stop active scene or audio if manual color clicked
        self.scene_engine.stop()
        if self.audio.is_running():
            self.audio.set_base_color(r, g, b)

        # Disarm hardware mic if it was active
        if hasattr(self, "hw_mic_switch"):
            self.hw_mic_switch.deselect()
        self.ble.disarm_external_mic(r, g, b)

        # Wake power if off
        if not self.is_powered_on:
            self._toggle_power()

        self.ble.set_color(r, g, b)
        self.active_mode_name = f"Solid {hex_c.upper()}"
        self.footer_status.configure(text=f"Color: RGB({r}, {g}, {b})")

    def _on_rgb_slide(self, _=None):
        r = int(self.r_slider.get())
        g = int(self.g_slider.get())
        b = int(self.b_slider.get())
        self._apply_color(r, g, b)

    def _on_brightness_slide(self, val):
        val = int(val)
        self.current_brightness = val
        self.brightness_label.configure(text=f"{val}%")
        self.brightness_slider.set(val)
        self.dock_brightness_slider.set(val)
        self.dock_brightness_lbl.configure(text=f"{val}%")

        self.ble.set_brightness(val)
        self.scene_engine.set_brightness(val)
        self.audio.set_master_brightness(val / 100.0)
        self._log(f"Set brightness: {val}%")

    def _set_brightness_preset(self, pct: int):
        self._on_brightness_slide(pct)

    def _on_speed_slide(self, val):
        val = int(val)
        self.current_speed = val
        self.dock_speed_slider.set(val)
        self.dock_speed_lbl.configure(text=f"{val}%")

        self.ble.set_speed(val)
        self.scene_engine.set_speed(val)
        self._log(f"Set speed: {val}%")

    def _on_cct_slide(self, val):
        warm = int(val)
        cold = 100 - warm
        self.ble.set_cct(warm, cold)
        self._log(f"Set CCT Warm: {warm}%, Cold: {cold}%")

    def _preset_night(self):
        # Warm dim amber 10% brightness
        self._apply_color(255, 120, 20)
        self._on_brightness_slide(10)
        self._log("Activated Ambient Night Mode.")

    def _preset_max_glow(self):
        # Full 100% Daylight White
        self._apply_color(255, 255, 255)
        self._on_brightness_slide(100)
        self._log("Activated Maximum Glow Daylight.")

    def _toggle_power(self):
        self.is_powered_on = not self.is_powered_on
        if not self.is_powered_on:
            self.audio.stop()
            self.scene_engine.stop()
            if hasattr(self, "hw_mic_switch"):
                self.hw_mic_switch.deselect()
            self.ble.disarm_external_mic(0, 0, 0)
            self.ble.set_power(False)
            self.power_btn.configure(
                text="⭕ POWER OFF",
                fg_color="#374151",
                hover_color="#4B5563",
                border_color="#1F2937",
            )
            self._log("Light Power: OFF (Microphone disarmed)")
        else:
            self.ble.set_power(True)
            self.power_btn.configure(
                text="⚡ POWER ON",
                fg_color="#059669",
                hover_color="#10B981",
                border_color="#047857",
            )
            self._log("Light Power: ON")

    def _open_device_tab(self):
        self.tabview.set("⚙️ Strip & Settings")

    # =========================================================================
    # BLUETOOTH LE SCAN & CONNECTION
    # =========================================================================
    def _quick_scan_and_connect(self):
        self._log("Scanning for neon rope lights...")
        self.quick_scan_btn.configure(text="Scanning...", state="disabled")
        self.ble.scan(timeout=3.5)

    def _start_scan(self):
        self._log("Scanning for Bluetooth devices...")
        self.scan_action_btn.configure(text="Scanning...", state="disabled")
        self.ble.scan(timeout=3.5)

    def _auto_connect_startup(self):
        self._log("Auto-scanning for rope lights on startup...")
        self.ble.scan(timeout=3.0)

    def _update_device_list_buttons(self):
        is_conn = self.ble.is_connected()
        current_addr = self.ble.get_current_address()
        for addr, item in list(self._device_cards.items()):
            btn = item.get("btn")
            is_melk = item.get("is_melk", False)
            if not btn:
                continue
            try:
                if not btn.winfo_exists():
                    continue
            except Exception:
                continue

            if is_conn and addr == current_addr:
                btn.configure(
                    text="Disconnect",
                    fg_color="#FF4757",
                    hover_color="#E03A58",
                    text_color="#FFFFFF",
                    command=self._disconnect_device,
                )
            else:
                btn.configure(
                    text="Connect",
                    fg_color="#00F0FF" if is_melk else "#1E2438",
                    hover_color="#00D0DF" if is_melk else "#2A334E",
                    text_color="#000000" if is_melk else "#FFFFFF",
                    command=lambda a=addr: self._connect_device(a),
                )

    def _on_ble_scan_finished(self, devices: List[Tuple[str, str, int]]):
        def update():
            self.quick_scan_btn.configure(text="🔄 Scan", state="normal")
            self.scan_action_btn.configure(text="🔄 Scan for Devices", state="normal")

            self._device_cards.clear()
            for widget in self.device_list_frame.winfo_children():
                widget.destroy()

            if not devices:
                lbl = ctk.CTkLabel(
                    self.device_list_frame,
                    text="No Bluetooth LE devices discovered. Make sure Bluetooth is ON in Windows.",
                    font=ctk.CTkFont(size=11),
                    text_color="#8E9AA8",
                )
                lbl.pack(padx=14, pady=16)
                return

            for name, addr, rssi in devices:
                is_melk = any(name.startswith(p) for p in NAME_FILTER_PREFIXES)
                row_frame = ctk.CTkFrame(
                    self.device_list_frame,
                    fg_color="#181E30" if is_melk else "#111420",
                    corner_radius=8,
                    border_width=1,
                    border_color="#252D48" if is_melk else "#171B2B",
                )
                row_frame.pack(fill="x", padx=6, pady=3)
                row_frame.grid_columnconfigure(0, weight=1)

                info_box = ctk.CTkFrame(row_frame, fg_color="transparent")
                info_box.grid(row=0, column=0, padx=14, pady=8, sticky="w")

                dev_title = ctk.CTkLabel(
                    info_box,
                    text=f"{'✨ ' if is_melk else ''}{name}",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#00F0FF" if is_melk else "#E2E8F0",
                )
                dev_title.pack(anchor="w")

                dev_sub = ctk.CTkLabel(
                    info_box,
                    text=f"MAC: {addr}  |  Signal: {rssi} dBm",
                    font=ctk.CTkFont(size=10),
                    text_color="#8E9AA8",
                )
                dev_sub.pack(anchor="w")

                is_connected_here = self.ble.is_connected() and self.ble.get_current_address() == addr
                btn_txt = "Disconnect" if is_connected_here else "Connect"
                conn_btn = ctk.CTkButton(
                    row_frame,
                    text=btn_txt,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color="#FF4757" if is_connected_here else ("#00F0FF" if is_melk else "#1E2438"),
                    hover_color="#E03A58" if is_connected_here else ("#00D0DF" if is_melk else "#2A334E"),
                    text_color="#FFFFFF" if (is_connected_here or not is_melk) else "#000000",
                    width=95,
                    height=30,
                    corner_radius=8,
                    command=self._disconnect_device if is_connected_here else (lambda a=addr: self._connect_device(a)),
                )
                conn_btn.grid(row=0, column=1, padx=14, pady=8)
                self._device_cards[addr] = {"btn": conn_btn, "is_melk": is_melk}

            self._update_device_list_buttons()

            # Auto-connect if found and not yet connected
            if not self.ble.is_connected():
                for name, addr, _ in devices:
                    if any(name.startswith(p) for p in NAME_FILTER_PREFIXES):
                        self._log(f"Auto-connecting to detected Neon Light: {name} ({addr})")
                        self.ble.connect(addr)
                        break

        self.after(0, update)

    def _connect_device(self, address: str):
        self._log(f"Connecting to {address}...")
        self.status_pill.configure(
            text="🟡 Connecting...",
            fg_color="#2D2415",
            hover_color="#3D301D",
            text_color="#FBBF24",
            border_color="#4D3D1F",
        )
        if address in self._device_cards:
            btn = self._device_cards[address].get("btn")
            if btn and btn.winfo_exists():
                btn.configure(text="Connecting...", fg_color="#FBBF24", text_color="#000000")
        self.ble.connect(address)

    def _disconnect_device(self):
        self._log("Disconnecting from rope lights...")
        self.audio.stop()
        self.scene_engine.stop()
        self.ble.disconnect()

    def _on_ble_connection_changed(self, connected: bool, address: Optional[str]):
        def update():
            if connected:
                self.status_pill.configure(
                    text="🟢 Online",
                    fg_color="#132B1E",
                    hover_color="#1B3D2B",
                    text_color="#10B981",
                    border_color="#1B4D33",
                )
                self.footer_status.configure(text=f"Connected: {address}")
                self._log(f"Connected to {address} successfully! Initialized IC points and power.")
            else:
                self.status_pill.configure(
                    text="🔴 Disconnected",
                    fg_color="#2D151D",
                    hover_color="#3D1D28",
                    text_color="#FF4757",
                    border_color="#4D1D2B",
                )
                self.footer_status.configure(text="Disconnected")
                self._log("Device disconnected.")
            self._update_device_list_buttons()
        self.after(0, update)

    def _on_ble_error(self, err_msg: str):
        def update():
            self._log(f"BLE Error: {err_msg}")
        self.after(0, update)

    def _on_ble_packet_sent(self, packet: bytes):
        hex_str = " ".join(f"{b:02X}" for b in packet)
        self._log(f"TX >> {hex_str}")

    def _log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        formatted = f"[{ts}] {msg}"
        self.log_messages.append(formatted)
        if len(self.log_messages) > 120:
            self.log_messages.pop(0)

        def update():
            if hasattr(self, "log_textbox"):
                self.log_textbox.insert("end", formatted + "\n")
                self.log_textbox.see("end")
        self.after(0, update)

    def _on_close(self):
        self.scene_engine.stop()
        self.audio.stop()
        self.ble.close()
        self.destroy()


def run():
    app = NeonApp()
    app.mainloop()


if __name__ == "__main__":
    run()
