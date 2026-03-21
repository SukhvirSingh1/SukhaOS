"""
layout.py
=========
Defines the SkillUI class — the entire user interface for SukhaOS.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from heatmap import show_heatmap

PERIOD_REWARDS = {
    "daily":   {"gold": 20,  "oxp": 20,  "sxp": 10},
    "weekly":  {"gold": 50,  "oxp": 60,  "sxp": 25},
    "monthly": {"gold": 120, "oxp": 150, "sxp": 60},
    "yearly":  {"gold": 500, "oxp": 500, "sxp": 200}
}

# Boss art drawn with tkinter Canvas shapes
# Each boss tier has a unique design
BOSS_ART = {
    "easy": [
        # The Slacker / Brain Fog / The Distraction — round blob, sleepy eyes
        ("oval",    50, 60, 250, 220, "#4a4a6a"),   # body
        ("oval",    90, 90, 160, 140, "#6a6a8a"),   # face highlight
        ("oval",    85, 105, 115, 125, "#ffcc00"),  # left eye
        ("oval",    145, 105, 175, 125, "#ffcc00"), # right eye
        ("oval",    95, 110, 105, 120, "#000000"),  # left pupil
        ("oval",    155, 110, 165, 120, "#000000"), # right pupil
        ("arc",     100, 150, 160, 180, "#ff6666"),  # sleepy mouth
    ],
    "medium": [
        # The Procrastinator / Doubt / Entropy — hourglass, sharp edges
        ("polygon", [150, 30, 230, 120, 200, 200, 100, 200, 70, 120], "#6a3a8a"),  # body
        ("oval",    110, 80, 190, 140, "#8a4aaa"),   # face
        ("oval",    120, 95, 145, 115, "#ff3300"),   # left eye
        ("oval",    155, 95, 180, 115, "#ff3300"),   # right eye
        ("oval",    128, 100, 137, 110, "#000000"),  # left pupil
        ("oval",    163, 100, 172, 110, "#000000"),  # right pupil
        ("line",    115, 160, 185, 160, "#ff3300"),  # flat menacing mouth
        ("line",    120, 155, 115, 160, "#ff3300"),  # left mouth corner
        ("line",    180, 155, 185, 160, "#ff3300"),  # right mouth corner
    ],
    "hard": [
        # Lord Chaos / The Void / The Final Exam — crystalline, jagged
        ("polygon", [150, 20, 220, 80, 250, 180, 200, 240, 100, 240, 50, 180, 80, 80], "#1a0a2a"),  # dark body
        ("polygon", [150, 40, 210, 90, 230, 170, 190, 220, 110, 220, 70, 170, 90, 90], "#3a1a5a"),  # inner body
        ("oval",    110, 95, 145, 125, "#cc0000"),   # left eye glow
        ("oval",    155, 95, 190, 125, "#cc0000"),   # right eye glow
        ("oval",    118, 103, 137, 117, "#ff0000"),  # left eye bright
        ("oval",    163, 103, 182, 117, "#ff0000"),  # right eye bright
        ("oval",    124, 107, 131, 113, "#ffffff"),  # left pupil
        ("oval",    169, 107, 176, 113, "#ffffff"),  # right pupil
        ("polygon", [120, 175, 130, 165, 145, 175, 155, 165, 170, 175, 180, 165, 185, 180, 115, 180], "#cc0000"),  # jagged mouth
        # Crown spikes
        ("polygon", [100, 80, 110, 40, 120, 80], "#5a2a8a"),
        ("polygon", [140, 80, 150, 20, 160, 80], "#5a2a8a"),
        ("polygon", [180, 80, 190, 40, 200, 80], "#5a2a8a"),
    ]
}


def draw_boss_art(canvas, tier, x_offset=0, y_offset=0):
    """
    Draw boss art on a tkinter Canvas using pre-defined shape data.

    Args:
        canvas: tkinter Canvas widget to draw on.
        tier (str): 'easy', 'medium', or 'hard'.
        x_offset (int): Horizontal offset for positioning.
        y_offset (int): Vertical offset for positioning.
    """
    shapes = BOSS_ART.get(tier, BOSS_ART["easy"])

    for shape in shapes:
        kind = shape[0]

        if kind == "oval":
            _, x1, y1, x2, y2, color = shape
            canvas.create_oval(
                x1 + x_offset, y1 + y_offset,
                x2 + x_offset, y2 + y_offset,
                fill=color, outline=""
            )

        elif kind == "polygon":
            _, points, color = shape
            offset_points = []
            for i, p in enumerate(points):
                offset_points.append(p + (x_offset if i % 2 == 0 else y_offset))
            canvas.create_polygon(offset_points, fill=color, outline="")

        elif kind == "arc":
            _, x1, y1, x2, y2, color = shape
            canvas.create_arc(
                x1 + x_offset, y1 + y_offset,
                x2 + x_offset, y2 + y_offset,
                start=200, extent=140,
                style="arc", outline=color, width=3
            )

        elif kind == "line":
            _, x1, y1, x2, y2, color = shape
            canvas.create_line(
                x1 + x_offset, y1 + y_offset,
                x2 + x_offset, y2 + y_offset,
                fill=color, width=3
            )


class SkillUI:
    def __init__(self, root, db, engine):
        self.root = root
        self.db = db
        self.engine = engine
        self.current_period = "daily"
        self._tooltip = None
        self.build_ui()

    # -------------------------------------------------------------------------
    # UI CONSTRUCTION
    # -------------------------------------------------------------------------

    def build_ui(self):
        """Build the full application layout."""
        self.root.rowconfigure(0, weight=3, minsize=200)
        self.root.rowconfigure(1, weight=1, minsize=150)
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=7)

        # ── TOP LEFT: Skills Panel ────────────────────────────────────────────
        chrctr_frame = tk.Frame(self.root, bg="#00254d", bd=2, relief="ridge")
        chrctr_frame.grid(row=0, column=0, sticky="nsew")

        tk.Label(chrctr_frame, text="Skills",
                 bg="#00254d", fg="#E0E0E0",
                 font=("Arial", 14, "bold")
                 ).grid(row=0, column=0, columnspan=2, pady=(15, 5))

        # Stats block: HP, Attack, Gold
        stats_frame = tk.Frame(chrctr_frame, bg="#00254d")
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 5))
        stats_frame.columnconfigure(0, weight=1)

        self.hp_label = tk.Label(stats_frame, text="HP: 100 / 100",
                                 bg="#00254d", fg="#ff6666",
                                 font=("Arial", 9, "bold"))
        self.hp_label.grid(row=0, column=0, sticky="w")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("HP.Horizontal.TProgressbar",
                        troughcolor="#001833", background="#ff4444",
                        thickness=12, bordercolor="#001833",
                        lightcolor="#ff4444", darkcolor="#ff4444")

        self.hp_bar = ttk.Progressbar(stats_frame, orient="horizontal",
                                      mode="determinate",
                                      style="HP.Horizontal.TProgressbar")
        self.hp_bar.grid(row=1, column=0, sticky="ew", pady=(2, 6))

        self.attack_label = tk.Label(stats_frame, text="⚔️ Attack: 0",
                                     bg="#00254d", fg="#ff9900",
                                     font=("Arial", 9, "bold"))
        self.attack_label.grid(row=2, column=0, sticky="w", pady=(0, 3))

        self.gold_label = tk.Label(stats_frame, text="💰 Gold: 0",
                                   bg="#00254d", fg="gold",
                                   font=("Arial", 9, "bold"))
        self.gold_label.grid(row=3, column=0, sticky="w", pady=(0, 5))

        # Boss alert label — hidden until a boss is active
        self.boss_alert_label = tk.Label(stats_frame,
                                         text="",
                                         bg="#00254d", fg="#ff0000",
                                         font=("Arial", 9, "bold"),
                                         cursor="hand2")
        self.boss_alert_label.grid(row=4, column=0, sticky="w", pady=(0, 3))

        tk.Frame(chrctr_frame, bg="#003366", height=1
                 ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 5))

        # Scrollable skill list
        self.skills_canvas = tk.Canvas(chrctr_frame, bg="#00254d", highlightthickness=0)
        self.skills_canvas.grid(row=3, column=0, sticky="nsew", padx=(10, 0))

        skills_scrollbar = ttk.Scrollbar(chrctr_frame, orient="vertical",
                                         command=self.skills_canvas.yview)
        skills_scrollbar.grid(row=3, column=1, sticky="ns")
        self.skills_canvas.configure(yscrollcommand=skills_scrollbar.set)

        self.skills_container = tk.Frame(self.skills_canvas, bg="#00254d")
        self.skills_canvas_window = self.skills_canvas.create_window(
            (0, 0), window=self.skills_container, anchor="nw"
        )

        self.skills_container.bind("<Configure>", lambda e: self.skills_canvas.configure(
            scrollregion=self.skills_canvas.bbox("all")
        ))
        self.skills_canvas.bind("<Configure>", lambda e: self.skills_canvas.itemconfig(
            self.skills_canvas_window, width=e.width
        ))
        self.skills_canvas.bind("<MouseWheel>", lambda e: self.skills_canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))

        tk.Button(chrctr_frame, text="+ Add Skill",
                  bg="#003366", fg="#E0E0E0",
                  font=("Arial", 9, "bold"),
                  command=self.open_add_skill_popup
                  ).grid(row=4, column=0, columnspan=2, pady=(0, 10))

        chrctr_frame.rowconfigure(3, weight=1)
        chrctr_frame.columnconfigure(0, weight=1)
        chrctr_frame.columnconfigure(1, weight=0)

        # ── TOP RIGHT: Player Info ────────────────────────────────────────────
        info_frame = tk.Frame(self.root, bg="#00254d", bd=2, relief="ridge")
        info_frame.grid(row=0, column=1, sticky="nsew")

        for i in range(5):
            info_frame.rowconfigure(i, weight=0)
        info_frame.rowconfigure(5, weight=1)
        info_frame.columnconfigure(0, weight=1)

        self.level_label = tk.Label(info_frame, text="Hero  |  lvl 1",
                                    bg="#00254d", fg="#E0E0E0",
                                    font=("Arial", 16, "bold"))
        self.level_label.grid(row=0, column=0, pady=20)

        self.xp_bar = ttk.Progressbar(info_frame, orient="horizontal",
                                      mode="determinate",
                                      style="XP.Horizontal.TProgressbar")
        self.xp_bar.grid(row=1, column=0, padx=40, sticky="ew", pady=(0, 10))

        self.xp_label = tk.Label(info_frame, text="0 / 100 OXP",
                                 bg="#00254d", fg="#aaaaaa",
                                 font=("Arial", 9, "bold"))
        self.xp_label.grid(row=2, column=0)

        tk.Button(info_frame, text="Add Task",
                  bg="#003366", fg="#E0E0E0",
                  font=("Arial", 12, "bold"),
                  command=self.open_add_task_popup
                  ).grid(row=3, column=0, pady=15)

        tk.Button(info_frame, text="Stats",
                  bg="#003366", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.show_stats
                  ).grid(row=4, column=0, pady=(0, 10))

        tk.Button(info_frame, text="Habit Map",
                  bg="#003366", fg="white",
                  font=("Arial", 11, "bold"),
                  command=self.show_heatmap
                  ).grid(row=5, column=0, pady=(0, 15))

        # ── BOTTOM: Task Area ─────────────────────────────────────────────────
        tasks_frame = tk.Frame(self.root, bg="#001833", bd=2, relief="ridge")
        tasks_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        tasks_frame.rowconfigure(0, weight=1)
        tasks_frame.columnconfigure(0, weight=0)
        tasks_frame.columnconfigure(1, weight=1)

        side_bar = tk.Frame(tasks_frame, bg="#003366")
        side_bar.grid(row=0, column=0, sticky="ns", padx=15)

        self.bottons = {}
        for i, (name, label) in enumerate(zip(
            ["daily", "weekly", "monthly", "yearly"], ["D", "W", "M", "Y"]
        )):
            btn = tk.Button(side_bar, text=label,
                            bg="#003366", fg="#E0E0E0",
                            font=("Arial", 10, "bold"),
                            command=lambda n=name: self.switch_menu(n))
            btn.grid(row=i, column=0, pady=10)
            self.bottons[name] = btn

        tk.Button(side_bar, text="Log",
                  bg="#003366", fg="white",
                  font=("Arial", 10, "bold"),
                  command=self.show_history
                  ).grid(row=4, column=0, pady=10)

        tk.Button(side_bar, text="Shop",
                  bg="#003366", fg="white",
                  font=("Arial", 10, "bold"),
                  command=self.show_shop
                  ).grid(row=5, column=0, pady=10)

        # Boss fight button — only visible when a boss is active
        self.boss_btn = tk.Button(side_bar, text="⚔️ BOSS",
                                  bg="#8b0000", fg="#ffcc00",
                                  font=("Arial", 10, "bold"),
                                  command=self.open_boss_fight)
        # Not gridded yet — shown only when boss is active

        self.task_container = tk.Frame(tasks_frame, bg="#001833")
        self.task_container.grid(row=0, column=1, sticky="nsew", padx=20)

        for i in range(2):
            self.task_container.grid_rowconfigure(i, weight=1)
            self.task_container.grid_columnconfigure(i, weight=1)

        style.configure("TProgressbar",
                        troughcolor="#001833", background="#00ccff",
                        thickness=18, bordercolor="#001833",
                        lightcolor="#00ccff", darkcolor="#00ccff")

        self.switch_menu("daily")
        self.refresh_player_ui()
        self.refresh_skill_ui()
        self._update_boss_ui()

    # -------------------------------------------------------------------------
    # BOSS UI HELPERS
    # -------------------------------------------------------------------------

    def _update_boss_ui(self):
        """
        Show or hide the boss button and alert label based on active boss.
        Called on startup and after any boss state change.
        """
        boss = self.db.get_active_boss()
        if boss:
            tier_colors = {"easy": "#ff8800", "medium": "#ff4400", "hard": "#ff0000"}
            color = tier_colors.get(boss["tier"], "#ff0000")
            self.boss_alert_label.config(
                text=f"⚠️ {boss['name']} is waiting!",
                fg=color
            )
            self.boss_alert_label.bind("<Button-1>", lambda e: self.open_boss_fight())
            # Show boss button in sidebar
            self.boss_btn.grid(row=6, column=0, pady=10)
        else:
            self.boss_alert_label.config(text="")
            # Hide boss button
            self.boss_btn.grid_remove()

    def show_boss_alert(self, boss):
        """Show a non-blocking banner when a boss spawns."""
        tier_labels = {"easy": "EASY", "medium": "MEDIUM", "hard": "HARD ☠️"}
        tier_colors = {"easy": "#ff8800", "medium": "#ff4400", "hard": "#ff0000"}

        popup = tk.Toplevel(self.root)
        popup.title("Boss Appeared!")
        popup.geometry("400x200")
        popup.config(bg="#1a0a0a")
        popup.grab_set()

        tk.Label(popup, text="⚠️  BOSS APPEARED  ⚠️",
                 bg="#1a0a0a", fg="#ff0000",
                 font=("Arial", 14, "bold")
                 ).pack(pady=(20, 5))

        tier_color = tier_colors.get(boss["tier"], "#ff0000")
        tk.Label(popup,
                 text=f"{boss['name']}  [{tier_labels.get(boss['tier'], boss['tier'].upper())}]",
                 bg="#1a0a0a", fg=tier_color,
                 font=("Arial", 13, "bold")
                 ).pack(pady=5)

        tk.Label(popup,
                 text=f'"{boss["taunt"]}"',
                 bg="#1a0a0a", fg="#aaaaaa",
                 font=("Arial", 9, "italic"),
                 wraplength=360
                 ).pack(pady=5)

        tk.Label(popup,
                 text=f"Deals {boss['attack_damage']} HP damage per day if ignored!",
                 bg="#1a0a0a", fg="#ff6666",
                 font=("Arial", 9)
                 ).pack(pady=3)

        def on_close():
            popup.destroy()
            self._update_boss_ui()
            self.refresh_player_ui()

        tk.Button(popup, text="Face the Boss  ⚔️",
                  bg="#8b0000", fg="#ffcc00",
                  font=("Arial", 11, "bold"),
                  command=lambda: [popup.destroy(), self.open_boss_fight()]
                  ).pack(side="left", padx=20, pady=15)

        tk.Button(popup, text="Not Yet",
                  bg="#003366", fg="white",
                  font=("Arial", 10),
                  command=on_close
                  ).pack(side="right", padx=20, pady=15)

    def show_boss_damage_warning(self, damage_info, on_close=None):
        """Show a warning popup when passive boss damage was applied on launch."""
        popup = tk.Toplevel(self.root)
        popup.title("Boss Attack!")
        popup.geometry("380x200")
        popup.config(bg="#1a0a0a")
        popup.grab_set()

        tk.Label(popup, text="⚠️  BOSS PASSIVE DAMAGE  ⚠️",
                 bg="#1a0a0a", fg="#ff4400",
                 font=("Arial", 13, "bold")
                 ).pack(pady=(20, 5))

        tk.Label(popup,
                 text=f"{damage_info['boss_name']} has been attacking while you were away!",
                 bg="#1a0a0a", fg="#E0E0E0",
                 font=("Arial", 10),
                 wraplength=350
                 ).pack(pady=5)

        tk.Label(popup,
                 text=f"- {damage_info['damage']} HP  ({damage_info['days']} day(s) ignored)",
                 bg="#1a0a0a", fg="#ff6666",
                 font=("Arial", 12, "bold")
                 ).pack(pady=5)

        tk.Label(popup,
                 text=f"HP remaining: {damage_info['remaining_hp']}",
                 bg="#1a0a0a", fg="#ffcc00",
                 font=("Arial", 10)
                 ).pack(pady=3)

        def close():
            popup.destroy()
            self.refresh_player_ui()
            if on_close:
                on_close()

        tk.Button(popup, text="Defeat the Boss Now  ⚔️",
                  bg="#8b0000", fg="#ffcc00",
                  font=("Arial", 11, "bold"),
                  command=lambda: [popup.destroy(), self.open_boss_fight()]
                  ).pack(side="left", padx=15, pady=15)

        tk.Button(popup, text="OK",
                  bg="#003366", fg="white",
                  font=("Arial", 10),
                  command=close
                  ).pack(side="right", padx=15, pady=15)

    def open_boss_fight(self):
        """
        Open the full-screen boss fight window.
        Shows boss art, HP bars, taunt text, attack button,
        and handles the full combat loop.
        """
        boss = self.db.get_active_boss()
        if not boss:
            messagebox.showinfo("No Boss", "No active boss right now.")
            return

        # Full screen toplevel window
        fight = tk.Toplevel(self.root)
        fight.title(f"Boss Fight — {boss['name']}")
        fight.state("zoomed")
        fight.config(bg="#0d0d1a")
        fight.grab_set()

        tier_colors = {"easy": "#ff8800", "medium": "#ff4400", "hard": "#ff0000"}
        tier_color  = tier_colors.get(boss["tier"], "#ff0000")

        # ── Boss name and tier ─────────────────────────────────────────────
        tk.Label(fight,
                 text=f"⚔️  {boss['name'].upper()}  ⚔️",
                 bg="#0d0d1a", fg=tier_color,
                 font=("Arial", 22, "bold")
                 ).pack(pady=(20, 5))

        tk.Label(fight,
                 text=f'"{boss["taunt"]}"',
                 bg="#0d0d1a", fg="#888888",
                 font=("Arial", 11, "italic"),
                 wraplength=700
                 ).pack(pady=(0, 15))

        # ── Main fight area: boss art left, stats right ────────────────────
        fight_frame = tk.Frame(fight, bg="#0d0d1a")
        fight_frame.pack(fill="both", expand=True, padx=40)
        fight_frame.columnconfigure(0, weight=1)
        fight_frame.columnconfigure(1, weight=1)
        fight_frame.rowconfigure(0, weight=1)

        # Boss art canvas — left side
        art_canvas = tk.Canvas(fight_frame, bg="#0d0d1a",
                               width=300, height=280,
                               highlightthickness=0)
        art_canvas.grid(row=0, column=0, sticky="nsew", padx=20)
        draw_boss_art(art_canvas, boss["tier"])

        # Stats panel — right side
        stats_frame = tk.Frame(fight_frame, bg="#0d0d1a")
        stats_frame.grid(row=0, column=1, sticky="nsew", padx=20)
        stats_frame.columnconfigure(0, weight=1)

        # Boss HP
        tk.Label(stats_frame, text="BOSS HP",
                 bg="#0d0d1a", fg=tier_color,
                 font=("Arial", 11, "bold")
                 ).grid(row=0, column=0, sticky="w", pady=(20, 2))

        boss_hp_label = tk.Label(stats_frame,
                                  text=f"{boss['hp']} / {boss['max_hp']}",
                                  bg="#0d0d1a", fg=tier_color,
                                  font=("Arial", 10))
        boss_hp_label.grid(row=1, column=0, sticky="w")

        style = ttk.Style()
        style.configure("Boss.Horizontal.TProgressbar",
                        troughcolor="#1a0a0a", background=tier_color,
                        thickness=20, bordercolor="#1a0a0a",
                        lightcolor=tier_color, darkcolor=tier_color)

        boss_hp_bar = ttk.Progressbar(stats_frame,
                                       orient="horizontal",
                                       mode="determinate",
                                       style="Boss.Horizontal.TProgressbar",
                                       length=350)
        boss_hp_bar["maximum"] = boss["max_hp"]
        boss_hp_bar["value"]   = boss["hp"]
        boss_hp_bar.grid(row=2, column=0, sticky="ew", pady=(0, 20))

        # Player HP
        player = self.db.get_player()
        tk.Label(stats_frame, text="YOUR HP",
                 bg="#0d0d1a", fg="#ff6666",
                 font=("Arial", 11, "bold")
                 ).grid(row=3, column=0, sticky="w", pady=(0, 2))

        player_hp_label = tk.Label(stats_frame,
                                    text=f"{player['current_hp']} / {player['max_hp']}",
                                    bg="#0d0d1a", fg="#ff6666",
                                    font=("Arial", 10))
        player_hp_label.grid(row=4, column=0, sticky="w")

        style.configure("PlayerFight.Horizontal.TProgressbar",
                        troughcolor="#1a0a0a", background="#ff4444",
                        thickness=20, bordercolor="#1a0a0a",
                        lightcolor="#ff4444", darkcolor="#ff4444")

        player_hp_bar = ttk.Progressbar(stats_frame,
                                         orient="horizontal",
                                         mode="determinate",
                                         style="PlayerFight.Horizontal.TProgressbar",
                                         length=350)
        player_hp_bar["maximum"] = player["max_hp"]
        player_hp_bar["value"]   = player["current_hp"]
        player_hp_bar.grid(row=5, column=0, sticky="ew", pady=(0, 20))

        # Attack points available
        atk_available_label = tk.Label(stats_frame,
                                        text=f"⚔️ Attack Points: {player['attack_points']}",
                                        bg="#0d0d1a", fg="#ff9900",
                                        font=("Arial", 11, "bold"))
        atk_available_label.grid(row=6, column=0, sticky="w", pady=(0, 5))

        atk_per_hit_label = tk.Label(stats_frame,
                                      text=f"Damage per hit: {self.engine.get_attack_damage()}",
                                      bg="#0d0d1a", fg="#ff9900",
                                      font=("Arial", 10))
        atk_per_hit_label.grid(row=7, column=0, sticky="w")

        boss_atk_label = tk.Label(stats_frame,
                                   text=f"Boss strikes back: {boss['attack_damage']} HP per hit",
                                   bg="#0d0d1a", fg="#ff6666",
                                   font=("Arial", 10))
        boss_atk_label.grid(row=8, column=0, sticky="w", pady=(0, 15))

        # Combat log — shows last action result
        combat_log = tk.Label(stats_frame,
                               text="Press Attack to fight!",
                               bg="#0d0d1a", fg="#aaaaaa",
                               font=("Arial", 10, "italic"),
                               wraplength=350)
        combat_log.grid(row=9, column=0, sticky="w", pady=(0, 20))

        # ── Attack button ──────────────────────────────────────────────────
        def do_attack():
            """Execute one round of combat."""
            current_player = self.db.get_player()

            if current_player["attack_points"] <= 0:
                combat_log.config(
                    text="Not enough attack points! Complete tasks to earn more.",
                    fg="#ff6666"
                )
                return

            result = self.engine.attack_boss(boss["id"])
            if result is None:
                return

            # Update boss HP bar
            boss_hp_bar["value"] = result["boss_hp"]
            boss_hp_label.config(text=f"{result['boss_hp']} / {boss['max_hp']}")

            # Update player HP bar
            updated_player = self.db.get_player()
            player_hp_bar["value"] = result["player_hp"]
            player_hp_label.config(
                text=f"{result['player_hp']} / {updated_player['max_hp']}"
            )
            atk_available_label.config(
                text=f"⚔️ Attack Points: {updated_player['attack_points']}"
            )

            # Flash boss art red on hit
            art_canvas.config(bg="#3a0000")
            fight.after(150, lambda: art_canvas.config(bg="#0d0d1a"))

            # Update combat log
            if result["boss_defeated"]:
                rewards = result["rewards"]
                combat_log.config(
                    text=f"BOSS DEFEATED! 🎉 +{rewards['gold']} Gold, +{rewards['oxp']} OXP, +{rewards['attack']} ATK",
                    fg="#ffcc00"
                )
                attack_btn.config(state="disabled")
                fight.after(2000, lambda: [fight.destroy(),
                                           self._update_boss_ui(),
                                           self.refresh_player_ui()])
                return

            if result["player_near_death"]:
                combat_log.config(
                    text=f"You dealt {result['player_damage']} damage! Boss struck back — you're near death! Lost gold!",
                    fg="#ff4444"
                )
            else:
                combat_log.config(
                    text=f"You dealt {result['player_damage']} damage! Boss struck back for {result['boss_damage']} HP.",
                    fg="#aaaaaa"
                )

            self.refresh_player_ui()

        attack_btn = tk.Button(fight,
                                text="⚔️  ATTACK",
                                bg="#8b0000", fg="#ffcc00",
                                font=("Arial", 16, "bold"),
                                padx=30, pady=10,
                                command=do_attack)
        attack_btn.pack(pady=10)

        # Flee button — close fight window without penalty
        tk.Button(fight,
                  text="Flee (come back later)",
                  bg="#003366", fg="#aaaaaa",
                  font=("Arial", 10),
                  command=fight.destroy
                  ).pack(pady=(0, 20))

    # -------------------------------------------------------------------------
    # SKILL PANEL
    # -------------------------------------------------------------------------

    def refresh_skill_ui(self):
        """Redraw skills list. Core skills show 🔒, custom skills show x."""
        for widget in self.skills_container.winfo_children():
            widget.destroy()

        skills = self.db.get_all_skills()

        if not skills:
            tk.Label(self.skills_container, text="No skills yet",
                     bg="#00254d", fg="#E0E0E0", font=("Arial", 10)
                     ).grid(row=0, column=0)
            return

        for index, skill in enumerate(skills):
            required   = self.get_required_sxp(skill["level"])
            skill_text = f"{skill['name']} | Lv {skill['level']}  {skill['xp']} / {required}"

            tk.Label(self.skills_container, text=skill_text,
                     bg="#00254d", fg="#E0E0E0",
                     anchor="w", font=("Arial", 10)
                     ).grid(row=index, column=0, sticky="ew", pady=3)

            if skill.get("is_core"):
                lock_label = tk.Label(self.skills_container, text="🔒",
                                      bg="#00254d", fg="#aaaaaa",
                                      font=("Arial", 8), cursor="question_arrow")
                lock_label.grid(row=index, column=1, padx=(5, 0), pady=3)
                lock_label.bind("<Enter>", lambda e, n=skill["name"]: self._show_lock_tooltip(e, n))
                lock_label.bind("<Leave>", self._hide_lock_tooltip)
            else:
                tk.Button(self.skills_container, text="x",
                          bg="#00254d", fg="#ff4444",
                          font=("Arial", 8, "bold"),
                          bd=0, cursor="hand2",
                          command=lambda n=skill["name"]: self.delete_skill(n)
                          ).grid(row=index, column=1, padx=(5, 0), pady=3)

        self.skills_container.columnconfigure(0, weight=1)
        self.skills_container.columnconfigure(1, weight=0)

    def _show_lock_tooltip(self, event, skill_name):
        messages = {
            "Health":   "Health powers your HP system",
            "Strength": "Strength powers your attack damage",
            "Mind":     "Mind is required for achievements",
        }
        self._tooltip = tk.Toplevel()
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
        tk.Label(self._tooltip,
                 text=messages.get(skill_name, "Core skill — cannot be deleted"),
                 bg="#ffcc00", fg="#000000",
                 font=("Arial", 8), padx=6, pady=3
                 ).pack()

    def _hide_lock_tooltip(self, event):
        if hasattr(self, "_tooltip") and self._tooltip:
            self._tooltip.destroy()
            self._tooltip = None

    def delete_skill(self, skill_name):
        if messagebox.askyesno("Delete Skill",
                               f"Delete '{skill_name}'? This won't affect existing tasks."):
            self.db.delete_skill(skill_name)
            self.refresh_skill_ui()

    # -------------------------------------------------------------------------
    # TASK CARDS
    # -------------------------------------------------------------------------

    def create_task_card(self, row, col, task_id, title, description, status, streak, difficulty):
        card = tk.Frame(self.task_container, bg="#003366", bd=0)
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

        tk.Label(card, text=title, bg="#003366", fg="#E0E0E0",
                 font=("Arial", 12, "bold")
                 ).grid(row=0, column=1, sticky="w", padx=10, pady=(10, 0))

        tk.Label(card, text=description, bg="#003366", fg="#E0E0E0",
                 font=("Arial", 10)
                 ).grid(row=1, column=1, sticky="w", padx=10)

        status_color = "green" if status == "Completed" else "orange"
        status_label = tk.Label(card, text=status, bg="#003366", fg=status_color,
                                font=("Arial", 9, "italic"), cursor="hand2")
        status_label.grid(row=2, column=1, sticky="e", padx=10, pady=(5, 10))
        status_label.bind("<Button-1>", lambda e, tid=task_id: self.complete_task(tid))

        tk.Label(card, text=f"Streak: {streak}", bg="#003366", fg="orange",
                 font=("Arial", 9, "italic")
                 ).grid(row=0, column=2, padx=10)

        tk.Label(card, text=f"Difficulty: {difficulty}", bg="#003366", fg="#cccccc",
                 font=("Arial", 9)
                 ).grid(row=1, column=2)

        tk.Button(card, text="Edit", bg="#004080", fg="white", font=("Arial", 8),
                  command=lambda tid=task_id: self.open_edit_task_popup(tid)
                  ).grid(row=2, column=0, padx=10)

        tk.Button(card, text="Delete", bg="#800000", fg="white", font=("Arial", 8),
                  command=lambda tid=task_id: self.delete_task(tid)
                  ).grid(row=2, column=2, padx=10, pady=5)

    # -------------------------------------------------------------------------
    # MAIN SCREENS
    # -------------------------------------------------------------------------

    def show_tasks(self, period):
        for widget in self.task_container.winfo_children():
            widget.destroy()

        for i in range(10):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i, weight=0)

        self.task_container.grid_rowconfigure(0, weight=0)
        self.task_container.grid_rowconfigure(1, weight=0)
        self.task_container.grid_rowconfigure(2, weight=1)
        self.task_container.grid_rowconfigure(3, weight=1)
        self.task_container.grid_columnconfigure(0, weight=1)
        self.task_container.grid_columnconfigure(1, weight=1)

        tasks     = self.db.get_tasks_by_period(period)
        completed = sum(1 for t in tasks if t["status"] == "Completed")
        total     = len(tasks)

        tk.Label(self.task_container,
                 text=f"{completed} / {total} tasks completed",
                 bg="#001833", fg="white", font=("Arial", 11, "bold")
                 ).grid(row=0, column=0, columnspan=2, pady=5)

        ttk.Progressbar(self.task_container,
                        length=250,
                        maximum=total if total > 0 else 1,
                        value=completed
                        ).grid(row=1, column=0, columnspan=2, pady=5)

        for task, pos in zip(tasks, [(2, 0), (2, 1), (3, 0), (3, 1)]):
            self.create_task_card(
                pos[0], pos[1],
                task["id"], task["title"], task["description"],
                task["status"], task["streak"], task["difficulty"]
            )

        tk.Button(self.task_container,
                  text="Show Graph", bg="#001833", fg="white",
                  command=self.show_task_graph
                  ).grid(row=4, column=1, pady=10)

    def show_stats(self):
        self.clear_content()

        for i in range(10):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i, weight=0)

        self.task_container.grid_rowconfigure(1, weight=1)
        self.task_container.grid_columnconfigure(0, weight=1)
        self.task_container.grid_columnconfigure(1, weight=1)

        tk.Button(self.task_container, text="<- Back", bg="#003366", fg="white",
                  command=lambda: self.switch_menu(self.current_period)
                  ).grid(row=0, column=0, sticky="w", pady=5)

        player = self.db.get_player()

        tk.Label(self.task_container, text="Character Stats",
                 bg="#001833", fg="white", font=("Arial", 16, "bold")
                 ).grid(row=0, column=0, columnspan=2, pady=10)

        stats = [
            (f"Name: {player['name']}",                          "white"),
            (f"Level: {player['level']}",                        "white"),
            (f"HP: {player['current_hp']} / {player['max_hp']}", "#ff6666"),
            (f"⚔️ Attack Points: {player['attack_points']}",     "#ff9900"),
            (f"⚔️ ATK per hit: {self.engine.get_attack_damage()}","#ff9900"),
            (f"💰 Gold: {player['gold']}",                       "gold"),
            (f"OXP: {player['oxp']}",                            "white"),
        ]

        for i, (text, color) in enumerate(stats):
            tk.Label(self.task_container, text=text,
                     bg="#001833", fg=color
                     ).grid(row=i + 1, column=0, sticky="w", padx=20)

        # Active boss info
        boss = self.db.get_active_boss()
        if boss:
            tk.Label(self.task_container,
                     text=f"⚠️ Active Boss: {boss['name']} ({boss['hp']}/{boss['max_hp']} HP)",
                     bg="#001833", fg="#ff4400",
                     font=("Arial", 10, "bold")
                     ).grid(row=9, column=0, sticky="w", padx=20)

        self.show_skill_stats()

        achievement = self.db.get_achievement()
        start_row   = 20

        tk.Label(self.task_container, text="Achievements",
                 bg="#001833", fg="white", font=("Arial", 14, "bold")
                 ).grid(row=start_row, column=1, sticky="w", padx=20)

        for i, ach in enumerate(achievement):
            color = "gold" if ach["unlocked"] else "#555555"
            tk.Label(self.task_container,
                     text=f"{ach['title']} - {ach['description']}",
                     bg="#001833", fg=color
                     ).grid(row=start_row + 1 + i, column=0, sticky="w", padx=20)

    def show_skill_stats(self):
        start_row = 11
        for index, skill in enumerate(self.db.get_all_skills()):
            required = 50 + (skill["level"] - 1) * 25
            tk.Label(self.task_container,
                     text=f"{skill['name']} - Lv {skill['level']}",
                     bg="#001833", fg="white", font=("Arial", 11, "bold")
                     ).grid(row=start_row + index * 2, column=0, sticky="w", padx=20)
            ttk.Progressbar(self.task_container,
                            length=250, maximum=required, value=skill["xp"],
                            style="TProgressbar"
                            ).grid(row=start_row + index * 2 + 1, column=0,
                                   sticky="w", padx=20, pady=5)

    def show_shop(self):
        self.clear_content()
        tk.Label(self.task_container, text="Skill Boost Shop",
                 bg="#001833", fg="white", font=("Arial", 16, "bold")
                 ).grid(row=0, column=0, pady=10)
        row = 1
        for skill in self.db.get_all_skills():
            tk.Label(self.task_container,
                     text=f"{skill['name']} (Lvl {skill['level']})",
                     bg="#001833", fg="white"
                     ).grid(row=row, column=0, sticky="w")
            tk.Button(self.task_container,
                      text="Buy +20 XP (100 GOLD)",
                      command=lambda s=skill["name"]: self.buy_skill(s)
                      ).grid(row=row, column=1, padx=10)
            row += 1
        tk.Button(self.task_container, text="<- Back",
                  command=lambda: self.switch_menu(self.current_period)
                  ).grid(row=row + 1, column=0, pady=20)

    def show_history(self):
        self.clear_content()

        for i in range(10):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i, weight=0)

        self.task_container.grid_rowconfigure(1, weight=1)
        self.task_container.grid_columnconfigure(0, weight=1)
        self.task_container.grid_columnconfigure(1, weight=1)
        self.task_container.grid_columnconfigure(2, weight=0)

        tk.Label(self.task_container, text="Task History",
                 bg="#001833", fg="white", font=("Arial", 16, "bold")
                 ).grid(row=0, column=0, pady=10)

        tk.Button(self.task_container, text="<- Back", bg="#003366", fg="white",
                  command=lambda: self.switch_menu(self.current_period)
                  ).grid(row=0, column=1, sticky="e", padx=20)

        canvas = tk.Canvas(self.task_container, bg="#001833", highlightthickness=0)
        canvas.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10)

        scrollbar = ttk.Scrollbar(self.task_container, orient="vertical",
                                  command=canvas.yview)
        scrollbar.grid(row=1, column=2, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        history_frame = tk.Frame(canvas, bg="#001833")
        canvas_window = canvas.create_window((0, 0), window=history_frame, anchor="nw")

        history_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        ))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(
            canvas_window, width=e.width
        ))
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))

        history = self.db.get_task_history()

        if not history:
            tk.Label(history_frame, text="No completed tasks yet. Get to work!",
                     bg="#001833", fg="#aaaaaa", font=("Arial", 11)
                     ).pack(pady=20)
            return

        for col, header in enumerate(["Date", "Task", "Difficulty"]):
            tk.Label(history_frame, text=header,
                     bg="#001833", fg="#aaaaaa", font=("Arial", 10, "bold")
                     ).grid(row=0, column=col, padx=20, pady=(10, 5), sticky="w")

        diff_colors = {"easy": "#00cc66", "medium": "#ffcc00", "hard": "#ff4444"}

        for index, (title, difficulty, date_str) in enumerate(history):
            diff_color = diff_colors.get((difficulty or "medium").lower(), "#aaaaaa")
            tk.Label(history_frame, text=date_str or "—",
                     bg="#001833", fg="#aaaaaa", font=("Arial", 10)
                     ).grid(row=index + 1, column=0, padx=20, pady=3, sticky="w")
            tk.Label(history_frame, text=title,
                     bg="#001833", fg="#E0E0E0", font=("Arial", 10)
                     ).grid(row=index + 1, column=1, padx=20, pady=3, sticky="w")
            tk.Label(history_frame, text=(difficulty or "Medium").capitalize(),
                     bg="#001833", fg=diff_color, font=("Arial", 10, "bold")
                     ).grid(row=index + 1, column=2, padx=20, pady=3, sticky="w")

        tk.Label(history_frame,
                 text=f"Total completions: {len(history)}",
                 bg="#001833", fg="#aaaaaa", font=("Arial", 10, "italic")
                 ).grid(row=len(history) + 1, column=0, columnspan=3, pady=15)

    # -------------------------------------------------------------------------
    # POPUPS
    # -------------------------------------------------------------------------

    def open_name_setup_popup(self, on_complete=None):
        popup = tk.Toplevel(self.root)
        popup.title("Welcome to SukhaOS")
        popup.geometry("380x250")
        popup.config(bg="#00254d")
        popup.grab_set()
        popup.resizable(False, False)

        tk.Label(popup, text="Welcome to SukhaOS!",
                 bg="#00254d", fg="#ffcc00", font=("Arial", 15, "bold")
                 ).pack(pady=(25, 5))
        tk.Label(popup, text="Enter your character name to begin:",
                 bg="#00254d", fg="#E0E0E0", font=("Arial", 10)
                 ).pack(pady=5)

        name_entry = tk.Entry(popup, font=("Arial", 13), justify="center", width=20)
        name_entry.pack(pady=15)
        name_entry.focus()

        def save_name():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a name", parent=popup); return
            if len(name) > 20:
                messagebox.showerror("Error", "Name too long (max 20 chars)", parent=popup); return
            self.db.set_player_name(name)
            self.refresh_player_ui()
            popup.destroy()
            if on_complete:
                on_complete()

        name_entry.bind("<Return>", lambda e: save_name())
        tk.Button(popup, text="Start Game!",
                  bg="#003366", fg="#ffcc00", font=("Arial", 12, "bold"),
                  command=save_name
                  ).pack(pady=5)

    def open_add_task_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add New Task")
        popup.geometry("400x400")

        tk.Label(popup, text="Title:", bg="#00254d", fg="#E0E0E0").grid(row=0, column=0, pady=5)
        title_entry = tk.Entry(popup)
        title_entry.grid(row=0, column=1)

        tk.Label(popup, text="Description:", bg="#00254d", fg="#E0E0E0").grid(row=1, column=0, pady=5)
        desc_entry = tk.Entry(popup)
        desc_entry.grid(row=1, column=1)

        tk.Label(popup, text="Period:", bg="#00254d", fg="#E0E0E0").grid(row=2, column=0, pady=5)
        period_var = tk.StringVar(value="daily")
        ttk.Combobox(popup, textvariable=period_var,
                     values=["daily", "weekly", "monthly", "yearly"],
                     state="readonly").grid(row=2, column=1)

        tk.Label(popup, text="Difficulty:", bg="#00254d", fg="#E0E0E0").grid(row=3, column=0)
        difficulty_var = tk.StringVar(value="Medium")
        ttk.Combobox(popup, textvariable=difficulty_var,
                     values=["Easy", "Medium", "Hard"],
                     state="readonly").grid(row=3, column=1)

        skills = [s["name"] for s in self.db.get_all_skills()]

        tk.Label(popup, text="Skill 1", bg="#00254d", fg="#E0E0E0").grid(row=4, column=0)
        skill1_var   = tk.StringVar()
        skill1_entry = ttk.Combobox(popup, values=skills,
                                    textvariable=skill1_var, state="readonly")
        skill1_entry.grid(row=4, column=1)

        tk.Label(popup, text="Skill 2 (OPTIONAL)", bg="#00254d", fg="#E0E0E0").grid(row=5, column=0)
        skill2_var   = tk.StringVar()
        skill2_entry = ttk.Combobox(popup, values=skills,
                                    textvariable=skill2_var, state="readonly")
        skill2_entry.grid(row=5, column=1)

        def save_task():
            title       = title_entry.get().strip()
            description = desc_entry.get().strip()
            period      = period_var.get()
            skill1      = skill1_entry.get()
            skill2      = skill2_entry.get()
            difficulty  = difficulty_var.get()

            if not title:
                messagebox.showerror("Error", "Title is required"); return
            if not description:
                messagebox.showerror("Error", "Description is required"); return
            if not skill1:
                messagebox.showerror("Error", "At least one skill must be selected"); return

            DIFF    = {"Easy": 0.8, "Medium": 1.0, "Hard": 1.5}
            rewards = PERIOD_REWARDS[period]
            mult    = DIFF[difficulty]

            task_id = self.db.add_task(
                title, description, period, difficulty,
                int(rewards["oxp"] * mult), int(rewards["gold"] * mult)
            )
            self.db.add_task_reward(task_id, skill1, int(rewards["sxp"] * mult))
            if skill2:
                self.db.add_task_reward(task_id, skill2, int(rewards["sxp"] * mult))
            popup.destroy()
            self.show_tasks(self.current_period)

        tk.Button(popup, text="Save Task", command=save_task
                  ).grid(row=6, column=0, columnspan=2, pady=20)

    def open_edit_task_popup(self, task_id):
        task = self.db.get_task(task_id)
        popup = tk.Toplevel(self.root)
        popup.title("Edit Task")
        popup.geometry("400x300")

        tk.Label(popup, text="Title").grid(row=0, column=0, pady=10)
        title_entry = tk.Entry(popup)
        title_entry.insert(0, task["title"])
        title_entry.grid(row=0, column=1)

        tk.Label(popup, text="Description").grid(row=1, column=0, pady=10)
        desc_entry = tk.Entry(popup)
        desc_entry.insert(0, task["description"])
        desc_entry.grid(row=1, column=1)

        tk.Label(popup, text="Period").grid(row=2, column=0, pady=10)
        period_var = tk.StringVar(value=task["period"])
        ttk.Combobox(popup, textvariable=period_var,
                     values=["daily", "weekly", "monthly", "yearly"],
                     state="readonly").grid(row=2, column=1)

        def save_changes():
            self.db.update_task(task_id, title_entry.get(),
                                desc_entry.get(), period_var.get())
            popup.destroy()
            self.show_tasks(self.current_period)

        tk.Button(popup, text="Save Changes", command=save_changes
                  ).grid(row=3, column=0, columnspan=2, pady=20)

    def open_add_skill_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add New Skill")
        popup.geometry("300x150")
        popup.config(bg="#00254d")

        tk.Label(popup, text="Skill Name:",
                 bg="#00254d", fg="#E0E0E0", font=("Arial", 11)
                 ).grid(row=0, column=0, padx=20, pady=20)

        name_entry = tk.Entry(popup, font=("Arial", 11))
        name_entry.grid(row=0, column=1, padx=10, pady=20)
        name_entry.focus()

        def save_skill():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Skill name cannot be empty"); return
            if len(name) > 20:
                messagebox.showerror("Error", "Skill name too long (max 20 chars)"); return
            if not self.db.add_skill(name):
                messagebox.showerror("Error", f"'{name}' already exists"); return
            popup.destroy()
            self.refresh_skill_ui()
            self.show_notification("Skill Added", f"{name} is now tracking!")

        name_entry.bind("<Return>", lambda e: save_skill())
        tk.Button(popup, text="Add Skill",
                  bg="#003366", fg="#E0E0E0", font=("Arial", 11, "bold"),
                  command=save_skill
                  ).grid(row=1, column=0, columnspan=2, pady=10)

    # -------------------------------------------------------------------------
    # TASK ACTIONS
    # -------------------------------------------------------------------------

    def complete_task(self, task_id):
        """Handle task completion. Now also handles boss spawn notification."""
        result = self.engine.complete_task(task_id)

        if result is False:
            messagebox.showinfo("Task", "Task already completed")
            return

        if result.get("leveled_up"):
            level = result["new_level"]
            msg   = f"You reached level {level}!\n+{self.engine.ATTACK_PER_LEVEL_UP} attack points!"
            messagebox.showinfo("Level Up!", msg)

        # Check if a boss spawned from this level up
        if result.get("boss"):
            boss = result["boss"]
            self.root.after(500, lambda: self.show_boss_alert(boss))

        self.refresh_player_ui()
        self.refresh_skill_ui()
        self._update_boss_ui()
        self.show_tasks(self.current_period)
        self.show_notification("Task Completed", "Great work! Rewards added.")

    def delete_task(self, task_id):
        if messagebox.askyesno("Confirm Deletion",
                               "This task will be permanently deleted.\n\nContinue?"):
            self.db.delete_task(task_id)
            self.show_tasks(self.current_period)

    def buy_skill(self, skill_name):
        if self.engine.buy_skill_boost(skill_name):
            self.refresh_player_ui()
            self.refresh_skill_ui()
            self.show_shop()
        else:
            messagebox.showerror("Error", "Not enough Gold")

    # -------------------------------------------------------------------------
    # NAVIGATION
    # -------------------------------------------------------------------------

    def switch_menu(self, period):
        self.current_period = period
        self.highlight_button(period)
        self.show_tasks(period)

    def highlight_button(self, period):
        for name, btn in self.bottons.items():
            btn.config(bg="#0059b3" if name == period else "#003366")

    def clear_content(self):
        for widget in self.task_container.winfo_children():
            widget.destroy()

    # -------------------------------------------------------------------------
    # PLAYER UI REFRESH
    # -------------------------------------------------------------------------

    def refresh_player_ui(self):
        player   = self.db.get_player()
        required = self.get_required_oxp(player["level"])
        current  = player["oxp"]

        name = player.get("name") or "Hero"
        self.level_label.config(text=f"{name}  |  lvl {player['level']}")
        self.xp_label.config(text=f"{current} / {required} OXP")

        self.xp_bar["maximum"] = required
        self.animate_bar(current)

        xp_color = "#00ff88" if player["level"] >= 10 else "#00ccff" if player["level"] >= 5 else "#ffcc00"
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("XP.Horizontal.TProgressbar",
                        background=xp_color, lightcolor=xp_color, darkcolor=xp_color)

        current_hp = player.get("current_hp", 100)
        max_hp     = player.get("max_hp", 100)
        self.hp_label.config(text=f"HP: {current_hp} / {max_hp}")
        self.hp_bar["maximum"] = max_hp
        self.hp_bar["value"]   = current_hp

        hp_pct   = current_hp / max_hp if max_hp > 0 else 1
        hp_color = "#ff4444" if hp_pct > 0.6 else "#ff8800" if hp_pct > 0.3 else "#ffcc00"
        style.configure("HP.Horizontal.TProgressbar",
                        background=hp_color, lightcolor=hp_color, darkcolor=hp_color)

        self.attack_label.config(text=f"⚔️ Attack: {player.get('attack_points', 0)}")
        self.gold_label.config(text=f"💰 Gold: {player['gold']}")

    def animate_bar(self, target):
        current = self.xp_bar["value"]
        if current < target:
            self.xp_bar["value"] = current + 1
            self.root.after(5, lambda: self.animate_bar(target))

    # -------------------------------------------------------------------------
    # GRAPHS & VISUALISATIONS
    # -------------------------------------------------------------------------

    def show_heatmap(self):
        show_heatmap(self.db)

    def show_task_graph(self):
        tasks = self.db.get_tasks_by_period(self.current_period)
        difficulty_count = {"Easy": 0, "Medium": 0, "Hard": 0}
        for task in tasks:
            diff = task["difficulty"].capitalize()
            if diff in difficulty_count:
                difficulty_count[diff] += 1
        plt.figure()
        plt.bar(list(difficulty_count.keys()), list(difficulty_count.values()))
        plt.title("Tasks by Difficulty")
        plt.xlabel("Difficulty")
        plt.ylabel("Number of tasks")
        plt.show()

    # -------------------------------------------------------------------------
    # NOTIFICATIONS
    # -------------------------------------------------------------------------

    def show_notification(self, title, message):
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("250x120")
        tk.Label(popup, text=title, font=("Arial", 12, "bold")).pack(pady=5)
        tk.Label(popup, text=message, font=("Arial", 10)).pack(pady=5)
        popup.after(2000, popup.destroy)

    def show_login_reward(self, reward, on_close=None):
        """Show daily login reward popup. Calls on_close after claiming."""
        popup = tk.Toplevel(self.root)
        popup.title("Daily Reward")
        popup.geometry("320x270")
        popup.config(bg="#00254d")
        popup.grab_set()

        tk.Label(popup, text="Daily Login Reward!",
                 bg="#00254d", fg="#ffcc00", font=("Arial", 14, "bold")
                 ).pack(pady=(20, 5))
        tk.Label(popup, text=reward["message"],
                 bg="#00254d", fg="#E0E0E0", font=("Arial", 10)
                 ).pack(pady=5)
        tk.Label(popup, text=f"+ {reward['gold']} Gold     + {reward['oxp']} OXP",
                 bg="#00254d", fg="#00ccff", font=("Arial", 12, "bold")
                 ).pack(pady=5)
        tk.Label(popup, text=f"⚔️ + {reward.get('bonus_atk', 0)} Attack Points",
                 bg="#00254d", fg="#ff9900", font=("Arial", 11)
                 ).pack(pady=2)
        if reward.get("hp_restored", 0) > 0:
            tk.Label(popup, text=f"+ {reward['hp_restored']} HP restored",
                     bg="#00254d", fg="#ff6666", font=("Arial", 10)
                     ).pack(pady=2)
        tk.Label(popup, text=f"Login Streak: {reward['streak']} days 🔥",
                 bg="#00254d", fg="orange", font=("Arial", 11)
                 ).pack(pady=5)

        def claim():
            popup.destroy()
            self.refresh_player_ui()
            if on_close:
                on_close()

        tk.Button(popup, text="Claim!",
                  bg="#003366", fg="white", font=("Arial", 11, "bold"),
                  command=claim
                  ).pack(pady=10)

    # -------------------------------------------------------------------------
    # HELPER FORMULAS
    # -------------------------------------------------------------------------

    def get_required_oxp(self, level):
        return 100 + (level - 1) * 50

    def get_required_sxp(self, level):
        return 50 + (level - 1) * 25