"""
layout.py
=========
Defines the SkillUI class — the entire user interface for SukhaOS.
Fully migrated to CustomTkinter for a modern dark UI.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from heatmap import show_heatmap

PERIOD_REWARDS = {
    "daily":   {"gold": 20,  "oxp": 20,  "sxp": 10},
    "weekly":  {"gold": 50,  "oxp": 60,  "sxp": 25},
    "monthly": {"gold": 120, "oxp": 150, "sxp": 60},
    "yearly":  {"gold": 500, "oxp": 500, "sxp": 200}
}

QUEST_DIFFICULTY_MULTIPLIER = {
    "easy": 0.20,
    "medium": 0.30,
    "hard": 0.45,
}

BOSS_ART = {
    "easy": [
        ("oval",    50, 60, 250, 220, "#4a4a6a"),
        ("oval",    90, 90, 160, 140, "#6a6a8a"),
        ("oval",    85, 105, 115, 125, "#ffcc00"),
        ("oval",    145, 105, 175, 125, "#ffcc00"),
        ("oval",    95, 110, 105, 120, "#000000"),
        ("oval",    155, 110, 165, 120, "#000000"),
        ("arc",     100, 150, 160, 180, "#ff6666"),
    ],
    "medium": [
        ("polygon", [150, 30, 230, 120, 200, 200, 100, 200, 70, 120], "#6a3a8a"),
        ("oval",    110, 80, 190, 140, "#8a4aaa"),
        ("oval",    120, 95, 145, 115, "#ff3300"),
        ("oval",    155, 95, 180, 115, "#ff3300"),
        ("oval",    128, 100, 137, 110, "#000000"),
        ("oval",    163, 100, 172, 110, "#000000"),
        ("line",    115, 160, 185, 160, "#ff3300"),
        ("line",    120, 155, 115, 160, "#ff3300"),
        ("line",    180, 155, 185, 160, "#ff3300"),
    ],
    "hard": [
        ("polygon", [150, 20, 220, 80, 250, 180, 200, 240, 100, 240, 50, 180, 80, 80], "#1a0a2a"),
        ("polygon", [150, 40, 210, 90, 230, 170, 190, 220, 110, 220, 70, 170, 90, 90], "#3a1a5a"),
        ("oval",    110, 95, 145, 125, "#cc0000"),
        ("oval",    155, 95, 190, 125, "#cc0000"),
        ("oval",    118, 103, 137, 117, "#ff0000"),
        ("oval",    163, 103, 182, 117, "#ff0000"),
        ("oval",    124, 107, 131, 113, "#ffffff"),
        ("oval",    169, 107, 176, 113, "#ffffff"),
        ("polygon", [120, 175, 130, 165, 145, 175, 155, 165, 170, 175, 180, 165, 185, 180, 115, 180], "#cc0000"),
        ("polygon", [100, 80, 110, 40, 120, 80], "#5a2a8a"),
        ("polygon", [140, 80, 150, 20, 160, 80], "#5a2a8a"),
        ("polygon", [180, 80, 190, 40, 200, 80], "#5a2a8a"),
    ]
}

CATEGORY_CONFIG = {
    "tasks":   {"label": "📋 Tasks",    "color": "#00ccff"},
    "streaks": {"label": "🔥 Streaks",  "color": "#ff9900"},
    "levels":  {"label": "⬆️ Levels",   "color": "#aa44ff"},
    "gold":    {"label": "💰 Gold",     "color": "#ffd700"},
    "skills":  {"label": "🧠 Skills",   "color": "#00ff88"},
    "bosses":  {"label": "⚔️ Bosses",   "color": "#ff4444"},
}


def draw_boss_art(canvas, tier, x_offset=0, y_offset=0):
    for shape in BOSS_ART.get(tier, BOSS_ART["easy"]):
        kind = shape[0]
        if kind == "oval":
            _, x1, y1, x2, y2, color = shape
            canvas.create_oval(x1+x_offset, y1+y_offset,
                               x2+x_offset, y2+y_offset,
                               fill=color, outline="")
        elif kind == "polygon":
            _, points, color = shape
            offset_points = [p+(x_offset if i%2==0 else y_offset)
                             for i, p in enumerate(points)]
            canvas.create_polygon(offset_points, fill=color, outline="")
        elif kind == "arc":
            _, x1, y1, x2, y2, color = shape
            canvas.create_arc(x1+x_offset, y1+y_offset,
                              x2+x_offset, y2+y_offset,
                              start=200, extent=140,
                              style="arc", outline=color, width=3)
        elif kind == "line":
            _, x1, y1, x2, y2, color = shape
            canvas.create_line(x1+x_offset, y1+y_offset,
                               x2+x_offset, y2+y_offset,
                               fill=color, width=3)


class SkillUI:
    def __init__(self, root, db, engine):
        self.root    = root
        self.db      = db
        self.engine  = engine
        self.current_period = "daily"
        self._tooltip = None
        self.build_ui()

    # -------------------------------------------------------------------------
    # UI CONSTRUCTION
    # -------------------------------------------------------------------------

    def build_ui(self):
        self.root.rowconfigure(0, weight=3, minsize=200)
        self.root.rowconfigure(1, weight=1, minsize=150)
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=7)

        # ── TOP LEFT: Skills Panel ────────────────────────────────────────────
        chrctr_frame = ctk.CTkFrame(self.root, corner_radius=10)
        chrctr_frame.grid(row=0, column=0, sticky="nsew", padx=(8,4), pady=(8,4))
        chrctr_frame.rowconfigure(3, weight=1)
        chrctr_frame.columnconfigure(0, weight=1)
        chrctr_frame.columnconfigure(1, weight=0)

        ctk.CTkLabel(chrctr_frame, text="Skills",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, pady=(15,8))

        stats_frame = ctk.CTkFrame(chrctr_frame, fg_color="transparent")
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0,6))
        stats_frame.columnconfigure(0, weight=1)

        self.hp_label = ctk.CTkLabel(stats_frame, text="HP: 100 / 100",
                                     text_color="#ff6666",
                                     font=ctk.CTkFont(size=11, weight="bold"))
        self.hp_label.grid(row=0, column=0, sticky="w")

        self.hp_bar = ctk.CTkProgressBar(stats_frame, height=10,
                                          progress_color="#ff4444", corner_radius=4)
        self.hp_bar.set(1.0)
        self.hp_bar.grid(row=1, column=0, sticky="ew", pady=(2,8))

        self.attack_label = ctk.CTkLabel(stats_frame, text="⚔️ Attack: 0",
                                          text_color="#ff9900",
                                          font=ctk.CTkFont(size=11, weight="bold"))
        self.attack_label.grid(row=2, column=0, sticky="w", pady=(0,3))

        self.gold_label = ctk.CTkLabel(stats_frame, text="💰 Gold: 0",
                                        text_color="#ffd700",
                                        font=ctk.CTkFont(size=11, weight="bold"))
        self.gold_label.grid(row=3, column=0, sticky="w", pady=(0,3))

        self.gear_label = ctk.CTkLabel(stats_frame,
                                        text="Cloth Armor | Training Sword",
                                        text_color="#aaaaaa",
                                        font=ctk.CTkFont(size=10))
        self.gear_label.grid(row=4, column=0, sticky="w", pady=(0,3))

        self.boss_alert_label = ctk.CTkLabel(stats_frame, text="",
                                              text_color="#ff4444",
                                              font=ctk.CTkFont(size=10, weight="bold"),
                                              cursor="hand2")
        self.boss_alert_label.grid(row=5, column=0, sticky="w", pady=(0,4))

        ctk.CTkFrame(chrctr_frame, height=2, fg_color="#333355"
                     ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0,6))

        self.skills_canvas = tk.Canvas(chrctr_frame, bg="#2b2b2b", highlightthickness=0)
        self.skills_canvas.grid(row=3, column=0, sticky="nsew", padx=(10,0))

        skills_scrollbar = ctk.CTkScrollbar(chrctr_frame, command=self.skills_canvas.yview)
        skills_scrollbar.grid(row=3, column=1, sticky="ns", padx=(0,4))
        self.skills_canvas.configure(yscrollcommand=skills_scrollbar.set)

        self.skills_container = tk.Frame(self.skills_canvas, bg="#2b2b2b")
        self.skills_canvas_window = self.skills_canvas.create_window(
            (0,0), window=self.skills_container, anchor="nw"
        )
        self.skills_container.bind("<Configure>", lambda e: self.skills_canvas.configure(
            scrollregion=self.skills_canvas.bbox("all")
        ))
        self.skills_canvas.bind("<Configure>", lambda e: self.skills_canvas.itemconfig(
            self.skills_canvas_window, width=e.width
        ))
        self.skills_canvas.bind("<MouseWheel>", lambda e: self.skills_canvas.yview_scroll(
            int(-1*(e.delta/120)), "units"
        ))

        ctk.CTkButton(chrctr_frame, text="+ Add Skill", height=30,
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=self.open_add_skill_popup
                      ).grid(row=4, column=0, columnspan=2, padx=12, pady=(6,10), sticky="ew")

        # ── TOP RIGHT: Player Info ────────────────────────────────────────────
        info_frame = ctk.CTkFrame(self.root, corner_radius=10)
        info_frame.grid(row=0, column=1, sticky="nsew", padx=(4,8), pady=(8,4))

        for i in range(9):
            info_frame.rowconfigure(i, weight=0)
        info_frame.rowconfigure(9, weight=1)
        info_frame.columnconfigure(0, weight=1)

        self.level_label = ctk.CTkLabel(info_frame, text="Hero  |  lvl 1",
                                         font=ctk.CTkFont(size=18, weight="bold"))
        self.level_label.grid(row=0, column=0, pady=(20,8))

        self.xp_bar = ctk.CTkProgressBar(info_frame, height=14,
                                           progress_color="#ffcc00", corner_radius=6)
        self.xp_bar.set(0)
        self.xp_bar.grid(row=1, column=0, padx=40, sticky="ew", pady=(0,4))

        self.xp_label = ctk.CTkLabel(info_frame, text="0 / 100 OXP",
                                      text_color="#aaaaaa",
                                      font=ctk.CTkFont(size=10))
        self.xp_label.grid(row=2, column=0, pady=(0,12))

        ctk.CTkButton(info_frame, text="Dashboard", height=36,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.show_dashboard
                      ).grid(row=3, column=0, pady=(0,10))

        ctk.CTkButton(info_frame, text="Add Task", height=36,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.open_add_task_popup
                      ).grid(row=4, column=0, pady=(0,10))

        ctk.CTkButton(info_frame, text="Stats", height=32,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self.show_stats
                      ).grid(row=7, column=0, pady=(0,8))

        ctk.CTkButton(info_frame, text="Quests", height=32,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self.show_quests
                      ).grid(row=6, column=0, pady=(0,8))

        ctk.CTkButton(info_frame, text="🏆 Achievements", height=32,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self.show_achievements
                      ).grid(row=5, column=0, pady=(0,8))

        ctk.CTkButton(info_frame, text="Habit Map", height=32,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self.show_heatmap
                      ).grid(row=8, column=0, pady=(0,12))

        # ── BOTTOM: Task Area ─────────────────────────────────────────────────
        tasks_frame = ctk.CTkFrame(self.root, corner_radius=10)
        tasks_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=(4,8))
        tasks_frame.rowconfigure(0, weight=1)
        tasks_frame.columnconfigure(0, weight=0)
        tasks_frame.columnconfigure(1, weight=1)

        side_bar = ctk.CTkFrame(tasks_frame, width=60, corner_radius=8)
        side_bar.grid(row=0, column=0, sticky="ns", padx=(8,4), pady=8)

        self.bottons = {}
        for i, (name, label) in enumerate(zip(
            ["daily","weekly","monthly","yearly"], ["D","W","M","Y"]
        )):
            btn = ctk.CTkButton(side_bar, text=label, width=48, height=36,
                                font=ctk.CTkFont(size=12, weight="bold"),
                                command=lambda n=name: self.switch_menu(n))
            btn.grid(row=i, column=0, pady=(8,0), padx=6)
            self.bottons[name] = btn

        ctk.CTkButton(side_bar, text="Log", width=48, height=36,
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=self.show_history
                      ).grid(row=4, column=0, pady=(8,0), padx=6)

        ctk.CTkButton(side_bar, text="Shop", width=48, height=36,
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=self.show_shop
                      ).grid(row=5, column=0, pady=(8,8), padx=6)

        self.boss_btn = ctk.CTkButton(side_bar, text="⚔️\nBOSS",
                                       width=48, height=48,
                                       font=ctk.CTkFont(size=10, weight="bold"),
                                       fg_color="#8b0000", hover_color="#aa0000",
                                       text_color="#ffcc00",
                                       command=self.open_boss_fight)

        self.task_container = ctk.CTkFrame(tasks_frame, fg_color="transparent")
        self.task_container.grid(row=0, column=1, sticky="nsew", padx=(4,8), pady=8)
        self.task_container.rowconfigure(0, weight=0)
        self.task_container.rowconfigure(1, weight=0)
        self.task_container.rowconfigure(2, weight=1)
        self.task_container.columnconfigure(0, weight=1)

        self.show_dashboard()
        self.refresh_player_ui()
        self.refresh_skill_ui()
        self._update_boss_ui()

    # -------------------------------------------------------------------------
    # RICH REWARD POPUPS
    # -------------------------------------------------------------------------

    def show_task_reward_popup(self, result):
        """
        Show a rich popup after task completion showing everything earned.
        Includes base rewards, skill XP, streak info.
        """
        popup = ctk.CTkToplevel(self.root)
        popup.title("Task Complete!")
        popup.geometry("380x420")
        popup.grab_set()
        popup.resizable(False, False)

        diff_colors = {"easy":"#00cc66","medium":"#ffcc00","hard":"#ff4444"}
        diff_color  = diff_colors.get(result["task_difficulty"].lower(), "#aaaaaa")

        # Header
        ctk.CTkLabel(popup, text="✅  Task Completed!",
                     text_color="#44ff88",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(pady=(20,4))

        ctk.CTkLabel(popup, text=result["task_title"],
                     text_color="#E0E0E0",
                     font=ctk.CTkFont(size=13)
                     ).pack(pady=(0,4))

        ctk.CTkLabel(popup,
                     text=f"{result['task_period'].capitalize()}  •  {result['task_difficulty']}",
                     text_color=diff_color,
                     font=ctk.CTkFont(size=11)
                     ).pack(pady=(0,12))

        # Divider
        ctk.CTkFrame(popup, height=1, fg_color="#333355").pack(fill="x", padx=20, pady=(0,12))

        # Rewards section
        ctk.CTkLabel(popup, text="Rewards",
                     text_color="#aaaaaa",
                     font=ctk.CTkFont(size=11, weight="bold")
                     ).pack(anchor="w", padx=24)

        rewards_frame = ctk.CTkFrame(popup, fg_color="#1e1e2e", corner_radius=8)
        rewards_frame.pack(fill="x", padx=20, pady=(4,12))

        rewards_data = [
            (f"+ {result['oxp_earned']} OXP",    "#00ccff"),
            (f"+ {result['gold_earned']} Gold",   "#ffd700"),
            (f"+ {result['atk_earned']} ATK pts", "#ff9900"),
        ]
        for text, color in rewards_data:
            ctk.CTkLabel(rewards_frame, text=text,
                         text_color=color,
                         font=ctk.CTkFont(size=13, weight="bold")
                         ).pack(anchor="w", padx=16, pady=3)

        # Streak
        if result["streak"] > 1:
            ctk.CTkLabel(popup,
                         text=f"🔥 Streak: {result['streak']} days!",
                         text_color="#ff9900",
                         font=ctk.CTkFont(size=12, weight="bold")
                         ).pack(pady=(0,8))

        # Skill XP gained
        skill_events = [s for s in result.get("skill_events", []) if not s["leveled_up"]]
        if skill_events:
            ctk.CTkLabel(popup, text="Skill XP",
                         text_color="#aaaaaa",
                         font=ctk.CTkFont(size=11, weight="bold")
                         ).pack(anchor="w", padx=24)
            skills_frame = ctk.CTkFrame(popup, fg_color="#1e1e2e", corner_radius=8)
            skills_frame.pack(fill="x", padx=20, pady=(4,12))
            for s in skill_events:
                ctk.CTkLabel(skills_frame,
                             text=f"🧠 {s['name']}  + {s['xp_gained']} XP",
                             text_color="#00ff88",
                             font=ctk.CTkFont(size=11)
                             ).pack(anchor="w", padx=16, pady=2)

        ctk.CTkButton(popup, text="Collect!", height=36,
                      text_color="#44ff88",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=popup.destroy
                      ).pack(pady=8)

    def show_quest_complete_popup(self, quest):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Quest Complete!")
        popup.geometry("380x320")
        popup.grab_set()
        popup.resizable(False, False)

        ctk.CTkLabel(popup, text="Quest Completed!",
                     text_color="#66ccff",
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).pack(pady=(24,6))

        ctk.CTkLabel(popup, text=quest["title"],
                     text_color="#ffffff",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(pady=(0,6))

        ctk.CTkLabel(popup, text=quest.get("description", ""),
                     text_color="#aaaaaa",
                     wraplength=320,
                     font=ctk.CTkFont(size=11)
                     ).pack(pady=(0,12))

        rewards_frame = ctk.CTkFrame(popup, fg_color="#1e1e2e", corner_radius=8)
        rewards_frame.pack(fill="x", padx=20, pady=(0,16))

        reward_lines = [
            (f"+ {quest.get('oxp_reward', 0)} OXP", "#00ccff"),
            (f"+ {quest.get('gold_reward', 0)} Gold", "#ffd700"),
            (f"+ {quest.get('attack_reward', 0)} Attack Points", "#ff9900"),
        ]
        for text, color in reward_lines:
            ctk.CTkLabel(rewards_frame, text=text,
                         text_color=color,
                         font=ctk.CTkFont(size=13, weight="bold")
                         ).pack(anchor="w", padx=16, pady=4)

        ctk.CTkButton(popup, text="Claim", height=36,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=popup.destroy
                      ).pack(pady=6)

    def show_level_up_popup(self, level_event):
        """
        Show a big celebration popup for character level up.
        One popup per level gained.
        """
        popup = ctk.CTkToplevel(self.root)
        popup.title("Level Up!")
        popup.geometry("360x340")
        popup.grab_set()
        popup.resizable(False, False)

        # Big level number
        ctk.CTkLabel(popup, text="⬆️  LEVEL UP!",
                     text_color="#ffcc00",
                     font=ctk.CTkFont(size=20, weight="bold")
                     ).pack(pady=(24,8))

        ctk.CTkLabel(popup,
                     text=f"Level {level_event['new_level']}",
                     text_color="#ffffff",
                     font=ctk.CTkFont(size=36, weight="bold")
                     ).pack(pady=(0,16))

        ctk.CTkFrame(popup, height=1, fg_color="#333355").pack(fill="x", padx=20, pady=(0,16))

        bonuses_frame = ctk.CTkFrame(popup, fg_color="#1e1e2e", corner_radius=8)
        bonuses_frame.pack(fill="x", padx=20, pady=(0,16))

        bonuses = [
            (f"❤️  + {level_event['hp_gained']} Max HP",       "#ff6666"),
            (f"⚔️  + {level_event['atk_gained']} Attack Pts",  "#ff9900"),
            (f"💚  Full HP Restored!",                          "#44ff88"),
        ]
        for text, color in bonuses:
            ctk.CTkLabel(bonuses_frame, text=text,
                         text_color=color,
                         font=ctk.CTkFont(size=13, weight="bold")
                         ).pack(anchor="w", padx=16, pady=4)

        ctk.CTkLabel(popup,
                     text=f"Max HP: {level_event['max_hp']}",
                     text_color="#aaaaaa",
                     font=ctk.CTkFont(size=11)
                     ).pack(pady=(0,12))

        ctk.CTkButton(popup, text="Let's Go! 💪", height=36,
                      text_color="#ffcc00",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=popup.destroy
                      ).pack(pady=4)

    def show_skill_level_up_popup(self, skill_event):
        """
        Show a popup when a skill levels up.
        One popup per skill that leveled up.
        """
        popup = ctk.CTkToplevel(self.root)
        popup.title("Skill Level Up!")
        popup.geometry("340x280")
        popup.grab_set()
        popup.resizable(False, False)

        ctk.CTkLabel(popup, text="🧠  Skill Level Up!",
                     text_color="#00ff88",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(pady=(24,8))

        ctk.CTkLabel(popup,
                     text=skill_event["name"],
                     text_color="#ffffff",
                     font=ctk.CTkFont(size=24, weight="bold")
                     ).pack(pady=(0,4))

        ctk.CTkLabel(popup,
                     text=f"Level {skill_event['old_level']}  →  Level {skill_event['new_level']}",
                     text_color="#00ff88",
                     font=ctk.CTkFont(size=16)
                     ).pack(pady=(0,16))

        ctk.CTkFrame(popup, height=1, fg_color="#333355").pack(fill="x", padx=20, pady=(0,16))

        # Special message for core skills
        special = {
            "Health":   "❤️  Max HP increased!",
            "Strength": "⚔️  Attack damage increased!",
            "Mind":     "🧠  Intelligence grows!",
        }
        if skill_event["name"] in special:
            ctk.CTkLabel(popup,
                         text=special[skill_event["name"]],
                         text_color="#ffcc00",
                         font=ctk.CTkFont(size=12)
                         ).pack(pady=(0,12))

        next_required = 50 + (skill_event["new_level"] - 1) * 25
        ctk.CTkLabel(popup,
                     text=f"Next level: {next_required} XP required",
                     text_color="#aaaaaa",
                     font=ctk.CTkFont(size=11)
                     ).pack(pady=(0,16))

        ctk.CTkButton(popup, text="Nice! 🔥", height=36,
                      text_color="#00ff88",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=popup.destroy
                      ).pack(pady=4)

    def show_achievement_unlock_popup(self, title):
        """
        Show a popup for a single newly unlocked achievement.
        """
        # Get achievement details
        achievements = self.db.get_achievement()
        ach = next((a for a in achievements if a["title"] == title), None)
        if not ach:
            return

        cat_config = CATEGORY_CONFIG.get(ach.get("category","general"),
                                          {"label":"General","color":"#aaaaaa"})

        popup = ctk.CTkToplevel(self.root)
        popup.title("Achievement Unlocked!")
        popup.geometry("340x260")
        popup.grab_set()
        popup.resizable(False, False)

        ctk.CTkLabel(popup, text="🏆  Achievement Unlocked!",
                     text_color="#ffd700",
                     font=ctk.CTkFont(size=15, weight="bold")
                     ).pack(pady=(24,8))

        ctk.CTkLabel(popup,
                     text=cat_config["label"],
                     text_color=cat_config["color"],
                     font=ctk.CTkFont(size=11)
                     ).pack(pady=(0,8))

        ach_frame = ctk.CTkFrame(popup, fg_color="#1e1e2e", corner_radius=10)
        ach_frame.pack(fill="x", padx=24, pady=(0,16))

        ctk.CTkLabel(ach_frame,
                     text=f"✅  {ach['title']}",
                     text_color=cat_config["color"],
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).pack(padx=16, pady=(12,4))

        ctk.CTkLabel(ach_frame,
                     text=ach["description"],
                     text_color="#aaaaaa",
                     font=ctk.CTkFont(size=11),
                     wraplength=280
                     ).pack(padx=16, pady=(0,12))

        unlocked, total = self.db.get_achievement_count()
        ctk.CTkLabel(popup,
                     text=f"{unlocked} / {total} achievements unlocked",
                     text_color="#555555",
                     font=ctk.CTkFont(size=10)
                     ).pack(pady=(0,8))

        ctk.CTkButton(popup, text="Awesome! 🏆", height=36,
                      text_color="#ffd700",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=popup.destroy
                      ).pack(pady=4)

    def show_boss_victory_popup(self, result):
        """
        Show a victory screen after defeating a boss.
        Shows all rewards and any achievements unlocked.
        """
        boss    = result.get("boss", {})
        rewards = result.get("rewards", {})

        tier_colors = {"easy":"#ff8800","medium":"#ff4400","hard":"#ff0000"}
        tier_color  = tier_colors.get(boss.get("tier","easy"), "#ff8800")

        popup = ctk.CTkToplevel(self.root)
        popup.title("Boss Defeated!")
        popup.geometry("380x420")
        popup.grab_set()
        popup.resizable(False, False)

        ctk.CTkLabel(popup, text="⚔️  BOSS DEFEATED!",
                     text_color="#ffcc00",
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).pack(pady=(20,4))

        ctk.CTkLabel(popup,
                     text=boss.get("name","Boss"),
                     text_color=tier_color,
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).pack(pady=(0,4))

        ctk.CTkLabel(popup,
                     text=boss.get("tier","").upper(),
                     text_color=tier_color,
                     font=ctk.CTkFont(size=11)
                     ).pack(pady=(0,12))

        ctk.CTkFrame(popup, height=1, fg_color="#333355").pack(fill="x", padx=20, pady=(0,12))

        ctk.CTkLabel(popup, text="Victory Rewards",
                     text_color="#aaaaaa",
                     font=ctk.CTkFont(size=11, weight="bold")
                     ).pack(anchor="w", padx=24)

        rewards_frame = ctk.CTkFrame(popup, fg_color="#1e1e2e", corner_radius=8)
        rewards_frame.pack(fill="x", padx=20, pady=(4,12))

        reward_items = [
            (f"+ {rewards.get('gold',0)} Gold",   "#ffd700"),
            (f"+ {rewards.get('oxp',0)} OXP",     "#00ccff"),
            (f"+ {rewards.get('attack',0)} ATK",  "#ff9900"),
        ]
        for text, color in reward_items:
            ctk.CTkLabel(rewards_frame, text=text,
                         text_color=color,
                         font=ctk.CTkFont(size=14, weight="bold")
                         ).pack(anchor="w", padx=16, pady=4)

        # Achievements unlocked from this fight
        newly_unlocked = result.get("newly_unlocked", [])
        if newly_unlocked:
            ctk.CTkLabel(popup, text="Achievements Unlocked",
                         text_color="#ffd700",
                         font=ctk.CTkFont(size=11, weight="bold")
                         ).pack(anchor="w", padx=24, pady=(4,0))
            for title in newly_unlocked:
                ctk.CTkLabel(popup, text=f"🏆 {title}",
                             text_color="#ffd700",
                             font=ctk.CTkFont(size=11)
                             ).pack(anchor="w", padx=28, pady=1)

        ctk.CTkButton(popup, text="Victory! 🎉", height=36,
                      text_color="#ffcc00",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=popup.destroy
                      ).pack(pady=12)

    def show_shop_skill_up_popup(self, result):
        """
        Show a popup when buying a skill boost causes a skill level up.
        """
        if not result.get("leveled_up"):
            return

        skill_event = {
            "name":      result["skill_name"],
            "old_level": result["old_level"],
            "new_level": result["new_level"],
            "xp_gained": 20,
            "leveled_up": True,
        }
        self.show_skill_level_up_popup(skill_event)

    def _show_popups_in_sequence(self, popups):
        """
        Show a list of popup-creating functions one after another.
        Each popup must be closed before the next one appears.
        This prevents popup overlap.

        Args:
            popups (list): List of callables, each creates and shows one popup.
        """
        if not popups:
            return

        def show_next(index):
            if index >= len(popups):
                return
            # Wait for previous popup to close by checking after 200ms
            popups[index]()
            # Chain: after this popup is created, monitor for it to close
            # then show the next one
            self.root.after(500, lambda: show_next(index + 1))

        show_next(0)

    # -------------------------------------------------------------------------
    # BOSS UI
    # -------------------------------------------------------------------------

    def _update_boss_ui(self):
        boss = self.db.get_active_boss()
        if boss:
            tier_colors = {"easy":"#ff8800","medium":"#ff4400","hard":"#ff0000"}
            self.boss_alert_label.configure(
                text=f"⚠️ {boss['name']} is waiting!",
                text_color=tier_colors.get(boss["tier"],"#ff0000")
            )
            self.boss_alert_label.bind("<Button-1>", lambda e: self.open_boss_fight())
            self.boss_btn.grid(row=7, column=0, pady=(0,8), padx=6)
        else:
            self.boss_alert_label.configure(text="")
            self.boss_btn.grid_remove()

    def show_boss_alert(self, boss):
        tier_colors = {"easy":"#ff8800","medium":"#ff4400","hard":"#ff0000"}
        tier_labels = {"easy":"EASY","medium":"MEDIUM","hard":"HARD ☠️"}

        popup = ctk.CTkToplevel(self.root)
        popup.title("Boss Appeared!")
        popup.geometry("420x230")
        popup.grab_set()

        ctk.CTkLabel(popup, text="⚠️  BOSS APPEARED  ⚠️",
                     text_color="#ff0000",
                     font=ctk.CTkFont(size=15, weight="bold")
                     ).pack(pady=(20,5))
        ctk.CTkLabel(popup,
                     text=f"{boss['name']}  [{tier_labels.get(boss['tier'],boss['tier'].upper())}]",
                     text_color=tier_colors.get(boss["tier"],"#ff0000"),
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).pack(pady=4)
        ctk.CTkLabel(popup, text=f'"{boss["taunt"]}"',
                     text_color="#aaaaaa", font=ctk.CTkFont(size=10), wraplength=380
                     ).pack(pady=4)
        ctk.CTkLabel(popup,
                     text=f"Deals {boss['attack_damage']} HP damage per day if ignored!",
                     text_color="#ff6666", font=ctk.CTkFont(size=10)
                     ).pack(pady=2)

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=12)

        def on_close():
            popup.destroy()
            self._update_boss_ui()
            self.refresh_player_ui()

        ctk.CTkButton(btn_frame, text="⚔️ Fight Now",
                      fg_color="#8b0000", hover_color="#aa0000",
                      text_color="#ffcc00",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=lambda: [popup.destroy(), self.open_boss_fight()]
                      ).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Not Yet",
                      font=ctk.CTkFont(size=11), command=on_close
                      ).pack(side="right", padx=10)

    def show_boss_damage_warning(self, damage_info, on_close=None):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Boss Attack!")
        popup.geometry("400x230")
        popup.grab_set()

        ctk.CTkLabel(popup, text="⚠️  BOSS PASSIVE DAMAGE  ⚠️",
                     text_color="#ff4400",
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).pack(pady=(20,5))
        ctk.CTkLabel(popup,
                     text=f"{damage_info['boss_name']} attacked while you were away!",
                     text_color="#E0E0E0", font=ctk.CTkFont(size=11), wraplength=360
                     ).pack(pady=4)
        ctk.CTkLabel(popup,
                     text=f"- {damage_info['damage']} HP  ({damage_info['days']} day(s) ignored)",
                     text_color="#ff6666", font=ctk.CTkFont(size=13, weight="bold")
                     ).pack(pady=4)
        ctk.CTkLabel(popup,
                     text=f"HP remaining: {damage_info['remaining_hp']}",
                     text_color="#ffcc00", font=ctk.CTkFont(size=11)
                     ).pack(pady=3)

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=12)

        def close():
            popup.destroy()
            self.refresh_player_ui()
            if on_close:
                on_close()

        ctk.CTkButton(btn_frame, text="⚔️ Fight Now",
                      fg_color="#8b0000", hover_color="#aa0000",
                      text_color="#ffcc00",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=lambda: [popup.destroy(), self.open_boss_fight()]
                      ).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="OK",
                      font=ctk.CTkFont(size=11), command=close
                      ).pack(side="right", padx=10)

    def open_boss_fight(self):
        boss = self.db.get_active_boss()
        if not boss:
            messagebox.showinfo("No Boss","No active boss right now.")
            return

        fight = ctk.CTkToplevel(self.root)
        fight.title(f"Boss Fight — {boss['name']}")
        fight.state("zoomed")
        fight.grab_set()

        tier_colors = {"easy":"#ff8800","medium":"#ff4400","hard":"#ff0000"}
        tier_color  = tier_colors.get(boss["tier"],"#ff0000")

        ctk.CTkLabel(fight, text=f"⚔️  {boss['name'].upper()}  ⚔️",
                     text_color=tier_color,
                     font=ctk.CTkFont(size=24, weight="bold")
                     ).pack(pady=(20,4))
        ctk.CTkLabel(fight, text=f'"{boss["taunt"]}"',
                     text_color="#888888", font=ctk.CTkFont(size=12), wraplength=700
                     ).pack(pady=(0,16))

        fight_frame = ctk.CTkFrame(fight, fg_color="transparent")
        fight_frame.pack(fill="both", expand=True, padx=40)
        fight_frame.columnconfigure(0, weight=1)
        fight_frame.columnconfigure(1, weight=1)
        fight_frame.rowconfigure(0, weight=1)

        art_canvas = tk.Canvas(fight_frame, bg="#1a1a2e",
                               width=300, height=280, highlightthickness=0)
        art_canvas.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)
        draw_boss_art(art_canvas, boss["tier"])

        stats_frame = ctk.CTkFrame(fight_frame)
        stats_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=10)
        stats_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(stats_frame, text="BOSS HP", text_color=tier_color,
                     font=ctk.CTkFont(size=12, weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=20, pady=(20,2))
        boss_hp_label = ctk.CTkLabel(stats_frame,
                                      text=f"{boss['hp']} / {boss['max_hp']}",
                                      text_color=tier_color, font=ctk.CTkFont(size=11))
        boss_hp_label.grid(row=1, column=0, sticky="w", padx=20)
        boss_hp_bar = ctk.CTkProgressBar(stats_frame, height=18,
                                          progress_color=tier_color, corner_radius=6)
        boss_hp_bar.set(boss["hp"] / boss["max_hp"])
        boss_hp_bar.grid(row=2, column=0, sticky="ew", padx=20, pady=(2,16))

        player = self.db.get_player()
        ctk.CTkLabel(stats_frame, text="YOUR HP", text_color="#ff6666",
                     font=ctk.CTkFont(size=12, weight="bold")
                     ).grid(row=3, column=0, sticky="w", padx=20, pady=(0,2))
        player_hp_label = ctk.CTkLabel(stats_frame,
                                        text=f"{player['current_hp']} / {player['max_hp']}",
                                        text_color="#ff6666", font=ctk.CTkFont(size=11))
        player_hp_label.grid(row=4, column=0, sticky="w", padx=20)
        player_hp_bar = ctk.CTkProgressBar(stats_frame, height=18,
                                            progress_color="#ff4444", corner_radius=6)
        player_hp_bar.set(player["current_hp"] / player["max_hp"])
        player_hp_bar.grid(row=5, column=0, sticky="ew", padx=20, pady=(2,16))

        atk_label = ctk.CTkLabel(stats_frame,
                                  text=f"⚔️ Attack Points: {player['attack_points']}",
                                  text_color="#ff9900",
                                  font=ctk.CTkFont(size=12, weight="bold"))
        atk_label.grid(row=6, column=0, sticky="w", padx=20, pady=(0,4))
        ctk.CTkLabel(stats_frame,
                     text=f"Damage per hit: {self.engine.get_attack_damage(player)}  |  Cost: 1 ATK point",
                     text_color="#ff9900", font=ctk.CTkFont(size=11)
                     ).grid(row=7, column=0, sticky="w", padx=20)
        ctk.CTkLabel(stats_frame,
                     text=f"Armor: {player.get('armor_name', 'Cloth Armor')} (+{player.get('armor_bonus_hp', 0)} HP)",
                     text_color="#ff8888", font=ctk.CTkFont(size=11)
                     ).grid(row=8, column=0, sticky="w", padx=20, pady=(0,4))
        ctk.CTkLabel(stats_frame,
                     text=f"Sword: {player.get('sword_name', 'Training Sword')} (+{player.get('sword_bonus_damage', 0)} DMG)",
                     text_color="#ffbb66", font=ctk.CTkFont(size=11)
                     ).grid(row=9, column=0, sticky="w", padx=20, pady=(0,4))
        ctk.CTkLabel(stats_frame,
                     text=f"Boss strikes back: {boss['attack_damage']} HP per hit",
                     text_color="#ff6666", font=ctk.CTkFont(size=11)
                     ).grid(row=10, column=0, sticky="w", padx=20, pady=(0,4))
        ctk.CTkLabel(stats_frame,
                     text="Near death penalty: -50 gold, -20 ATK points",
                     text_color="#888888", font=ctk.CTkFont(size=10)
                     ).grid(row=11, column=0, sticky="w", padx=20, pady=(0,12))

        combat_log = ctk.CTkLabel(stats_frame, text="Press Attack to fight!",
                                   text_color="#aaaaaa", font=ctk.CTkFont(size=11),
                                   wraplength=340)
        combat_log.grid(row=12, column=0, sticky="w", padx=20, pady=(0,16))

        def do_attack():
            current_player = self.db.get_player()
            if current_player["attack_points"] <= 0:
                combat_log.configure(
                    text="Not enough attack points! Complete tasks to earn more.",
                    text_color="#ff6666"
                )
                return

            result = self.engine.attack_boss(boss["id"])
            if result is None:
                return

            boss_hp_bar.set(result["boss_hp"] / boss["max_hp"])
            boss_hp_label.configure(text=f"{result['boss_hp']} / {boss['max_hp']}")

            updated  = self.db.get_player()
            hp_ratio = result["player_hp"] / updated["max_hp"]
            player_hp_bar.set(max(0, hp_ratio))
            player_hp_label.configure(text=f"{result['player_hp']} / {updated['max_hp']}")
            atk_label.configure(text=f"⚔️ Attack Points: {result['attack_points']}")

            art_canvas.config(bg="#3a0000")
            fight.after(150, lambda: art_canvas.config(bg="#1a1a2e"))

            if result["boss_defeated"]:
                attack_btn.configure(state="disabled")
                fight.after(1000, lambda: [
                    fight.destroy(),
                    self._update_boss_ui(),
                    self.refresh_player_ui(),
                    self.show_boss_victory_popup(result)
                ])
                return

            if result["player_near_death"]:
                combat_log.configure(
                    text=f"You dealt {result['player_damage']} dmg! NEAR DEATH — HP=1, lost 50 gold & 20 ATK!",
                    text_color="#ff4444"
                )
            else:
                combat_log.configure(
                    text=f"You dealt {result['player_damage']} dmg! Boss hit back for {result['boss_damage']} HP.",
                    text_color="#aaaaaa"
                )
            self.refresh_player_ui()

        attack_btn = ctk.CTkButton(fight, text="⚔️  ATTACK",
                                    height=52, width=200,
                                    fg_color="#8b0000", hover_color="#aa0000",
                                    text_color="#ffcc00",
                                    font=ctk.CTkFont(size=18, weight="bold"),
                                    command=do_attack)
        attack_btn.pack(pady=10)

        ctk.CTkButton(fight, text="Flee (come back later)",
                      fg_color="transparent", hover_color="#333333",
                      text_color="#aaaaaa", font=ctk.CTkFont(size=11),
                      command=fight.destroy
                      ).pack(pady=(0,16))

    # -------------------------------------------------------------------------
    # SKILL PANEL
    # -------------------------------------------------------------------------

    def refresh_skill_ui(self):
        for widget in self.skills_container.winfo_children():
            widget.destroy()

        skills = self.db.get_all_skills()
        if not skills:
            tk.Label(self.skills_container, text="No skills yet",
                     bg="#2b2b2b", fg="#E0E0E0", font=("Arial",10)
                     ).grid(row=0, column=0)
            return

        for index, skill in enumerate(skills):
            required   = self.get_required_sxp(skill["level"])
            skill_text = f"{skill['name']} | Lv {skill['level']}  {skill['xp']} / {required}"

            tk.Label(self.skills_container, text=skill_text,
                     bg="#2b2b2b", fg="#E0E0E0",
                     anchor="w", font=("Arial",10)
                     ).grid(row=index, column=0, sticky="ew", pady=3, padx=4)

            if skill.get("is_core"):
                lock = tk.Label(self.skills_container, text="🔒",
                                bg="#2b2b2b", fg="#aaaaaa",
                                font=("Arial",8), cursor="question_arrow")
                lock.grid(row=index, column=1, padx=(4,4), pady=3)
                lock.bind("<Enter>", lambda e, n=skill["name"]: self._show_lock_tooltip(e, n))
                lock.bind("<Leave>", self._hide_lock_tooltip)
            else:
                tk.Button(self.skills_container, text="x",
                          bg="#2b2b2b", fg="#ff4444",
                          font=("Arial",8,"bold"), bd=0, cursor="hand2",
                          activebackground="#2b2b2b",
                          command=lambda n=skill["name"]: self.delete_skill(n)
                          ).grid(row=index, column=1, padx=(4,4), pady=3)

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
        self._tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        tk.Label(self._tooltip,
                 text=messages.get(skill_name,"Core skill — cannot be deleted"),
                 bg="#ffcc00", fg="#000000", font=("Arial",8), padx=6, pady=3
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
    # TASK DISPLAY — scrollable, unlimited
    # -------------------------------------------------------------------------

    def show_tasks(self, period):
        for widget in self.task_container.winfo_children():
            widget.destroy()

        for i in range(10):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i, weight=0)

        self.task_container.grid_rowconfigure(2, weight=1)
        self.task_container.grid_columnconfigure(0, weight=1)

        tasks     = self.db.get_tasks_by_period(period)
        completed = sum(1 for t in tasks if t["status"] == "Completed")
        total     = len(tasks)

        ctk.CTkLabel(self.task_container,
                     text=f"{completed} / {total} tasks completed",
                     font=ctk.CTkFont(size=12, weight="bold")
                     ).grid(row=0, column=0, pady=(8,2), sticky="ew")

        prog = ctk.CTkProgressBar(self.task_container, height=10, corner_radius=4)
        prog.set(completed / total if total > 0 else 0)
        prog.grid(row=1, column=0, pady=(0,6), padx=20, sticky="ew")

        tasks_canvas = tk.Canvas(self.task_container, bg="#1e1e2e", highlightthickness=0)
        tasks_canvas.grid(row=2, column=0, sticky="nsew")

        tasks_scrollbar = ctk.CTkScrollbar(self.task_container, command=tasks_canvas.yview)
        tasks_scrollbar.grid(row=2, column=1, sticky="ns")
        tasks_canvas.configure(yscrollcommand=tasks_scrollbar.set)
        self.task_container.grid_columnconfigure(1, weight=0)

        cards_frame = ctk.CTkFrame(tasks_canvas, fg_color="transparent")
        cards_window = tasks_canvas.create_window((0,0), window=cards_frame, anchor="nw")

        cards_frame.bind("<Configure>", lambda e: tasks_canvas.configure(
            scrollregion=tasks_canvas.bbox("all")
        ))
        tasks_canvas.bind("<Configure>", lambda e: tasks_canvas.itemconfig(
            cards_window, width=e.width
        ))
        tasks_canvas.bind("<MouseWheel>", lambda e: tasks_canvas.yview_scroll(
            int(-1*(e.delta/120)), "units"
        ))

        if not tasks:
            ctk.CTkLabel(cards_frame,
                         text="No tasks yet. Click Add Task to get started!",
                         text_color="#aaaaaa", font=ctk.CTkFont(size=12)
                         ).pack(pady=30)
        else:
            for task in tasks:
                self._create_task_card(cards_frame, task)

        ctk.CTkButton(self.task_container, text="Show Graph", height=28,
                      font=ctk.CTkFont(size=11), command=self.show_task_graph
                      ).grid(row=3, column=0, pady=6)

    def _get_next_boss_milestone(self, level):
        candidates = []
        for divisor, tier in [(10, "easy"), (25, "medium"), (50, "hard")]:
            next_level = ((level // divisor) + 1) * divisor
            candidates.append((next_level, tier))
        return min(candidates, key=lambda item: item[0])

    def _create_dashboard_card(self, parent, title, body, accent, row, column):
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
        card.columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text=title,
                     text_color=accent,
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(14,6))
        ctk.CTkLabel(card, text=body,
                     justify="left",
                     anchor="w",
                     wraplength=280,
                     text_color="#dddddd",
                     font=ctk.CTkFont(size=11)
                     ).grid(row=1, column=0, sticky="w", padx=16, pady=(0,14))
        return card

    def show_dashboard(self):
        self.clear_content()

        for i in range(8):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i, weight=0)

        self.task_container.grid_columnconfigure(0, weight=1)
        self.task_container.grid_columnconfigure(1, weight=1)
        self.task_container.grid_rowconfigure(3, weight=1)

        player = self.db.get_player()
        daily_tasks = self.db.get_tasks_by_period("daily")
        pending_daily = [task for task in daily_tasks if task["status"] != "Completed"]
        completed_daily = len(daily_tasks) - len(pending_daily)
        next_task = pending_daily[0]["title"] if pending_daily else "All daily tasks are complete"
        tasks_today = self.db.get_tasks_completed_today()
        max_streak = self.db.get_max_task_streak()
        quests = self.db.get_quests_with_progress()
        active_quests = [quest for quest in quests if quest["status"] == "Active"]
        active_boss = self.db.get_active_boss()
        next_boss_level, next_boss_tier = self._get_next_boss_milestone(player["level"])
        required_oxp = self.get_required_oxp(player["level"])

        ctk.CTkLabel(self.task_container, text="Command Center",
                     font=ctk.CTkFont(size=20, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, pady=(6,2))
        ctk.CTkLabel(
            self.task_container,
            text="See what matters today and jump straight into meaningful progress.",
            text_color="#aaaaaa",
            font=ctk.CTkFont(size=11)
        ).grid(row=1, column=0, columnspan=2, pady=(0,8))

        summary_frame = ctk.CTkFrame(self.task_container, fg_color="transparent")
        summary_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        summary_frame.grid_columnconfigure(0, weight=1)
        summary_frame.grid_columnconfigure(1, weight=1)
        summary_frame.grid_columnconfigure(2, weight=1)

        self._create_dashboard_card(
            summary_frame,
            "Today's Focus",
            f"Daily tasks: {completed_daily}/{len(daily_tasks)} done\n"
            f"Pending now: {len(pending_daily)}\n"
            f"Next best task: {next_task}",
            "#66ccff",
            0, 0
        )
        self._create_dashboard_card(
            summary_frame,
            "Momentum",
            f"Login streak: {player.get('login_streak', 0)} day(s)\n"
            f"Tasks completed today: {tasks_today}\n"
            f"Best task streak: {max_streak}",
            "#ff9900",
            0, 1
        )
        boss_body = (
            f"Active boss: {active_boss['name']} [{active_boss['tier'].title()}]\n"
            f"HP: {active_boss['hp']} / {active_boss['max_hp']}"
            if active_boss else
            f"Next boss milestone: Level {next_boss_level}\n"
            f"Expected tier: {next_boss_tier.title()}"
        )
        self._create_dashboard_card(
            summary_frame,
            "Boss Watch",
            boss_body,
            "#ff6666",
            0, 2
        )

        lower_frame = ctk.CTkFrame(self.task_container, fg_color="transparent")
        lower_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")
        lower_frame.grid_columnconfigure(0, weight=3)
        lower_frame.grid_columnconfigure(1, weight=2)
        lower_frame.grid_rowconfigure(0, weight=1)

        quest_panel = ctk.CTkFrame(lower_frame, corner_radius=10)
        quest_panel.grid(row=0, column=0, sticky="nsew", padx=(0,8), pady=(4,0))
        quest_panel.columnconfigure(0, weight=1)

        ctk.CTkLabel(quest_panel, text="Active Quests",
                     font=ctk.CTkFont(size=15, weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(14,6))

        if not active_quests:
            ctk.CTkLabel(quest_panel,
                         text="No active quests yet. Build a bigger mission from your tasks.",
                         text_color="#aaaaaa",
                         font=ctk.CTkFont(size=11)
                         ).grid(row=1, column=0, sticky="w", padx=16, pady=(4,12))
        else:
            for index, quest in enumerate(active_quests[:3], start=1):
                progress = quest.get("progress") or {"progress_value": 0, "target_value": 1, "ratio": 0}
                block = ctk.CTkFrame(quest_panel, fg_color="#1e1e2e", corner_radius=8)
                block.grid(row=index, column=0, sticky="ew", padx=14, pady=6)
                block.columnconfigure(0, weight=1)
                ctk.CTkLabel(block, text=quest["title"],
                             font=ctk.CTkFont(size=12, weight="bold")
                             ).grid(row=0, column=0, sticky="w", padx=12, pady=(10,2))
                ctk.CTkLabel(
                    block,
                    text=f"{progress['progress_value']} / {progress['target_value']}  |  {quest['category'].title()}",
                    text_color="#aaaaaa",
                    font=ctk.CTkFont(size=10)
                ).grid(row=1, column=0, sticky="w", padx=12)
                bar = ctk.CTkProgressBar(block, height=8, corner_radius=4, progress_color="#66ccff")
                bar.set(progress["ratio"])
                bar.grid(row=2, column=0, sticky="ew", padx=12, pady=(6,10))

        side_panel = ctk.CTkFrame(lower_frame, corner_radius=10)
        side_panel.grid(row=0, column=1, sticky="nsew", padx=(8,0), pady=(4,0))
        side_panel.columnconfigure(0, weight=1)

        ctk.CTkLabel(side_panel, text="Progress Snapshot",
                     font=ctk.CTkFont(size=15, weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(14,6))
        snapshot = [
            f"Level: {player['level']}",
            f"OXP: {player['oxp']} / {required_oxp}",
            f"HP: {player['current_hp']} / {player['max_hp']}",
            f"Attack points: {player['attack_points']}",
            f"Damage per hit: {self.engine.get_attack_damage(player)}",
            f"Gear: {player.get('armor_name', 'Cloth Armor')} | {player.get('sword_name', 'Training Sword')}",
        ]
        for row_index, line in enumerate(snapshot, start=1):
            ctk.CTkLabel(side_panel, text=line,
                         text_color="#dddddd",
                         font=ctk.CTkFont(size=11)
                         ).grid(row=row_index, column=0, sticky="w", padx=16, pady=2)

        ctk.CTkLabel(side_panel, text="Quick Actions",
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).grid(row=8, column=0, sticky="w", padx=16, pady=(16,8))

        action_frame = ctk.CTkFrame(side_panel, fg_color="transparent")
        action_frame.grid(row=9, column=0, sticky="ew", padx=12, pady=(0,14))
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(action_frame, text="Add Task", height=32,
                      command=self.open_add_task_popup
                      ).grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(action_frame, text="Daily Tasks", height=32,
                      command=lambda: self.switch_menu("daily")
                      ).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(action_frame, text="Quests", height=32,
                      command=self.show_quests
                      ).grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(action_frame, text="Shop", height=32,
                      command=self.show_shop
                      ).grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        final_action = ctk.CTkButton(
            action_frame,
            text="Fight Boss" if active_boss else "Stats",
            height=32,
            command=self.open_boss_fight if active_boss else self.show_stats
        )
        if active_boss:
            final_action.configure(fg_color="#8b0000", hover_color="#aa0000")
        final_action.grid(row=2, column=0, columnspan=2, padx=4, pady=4, sticky="ew")

    def _create_task_card(self, parent, task):
        card = ctk.CTkFrame(parent, corner_radius=8)
        card.pack(fill="x", padx=10, pady=6)
        card.columnconfigure(1, weight=1)

        diff_colors = {"easy":"#00cc66","medium":"#ffcc00","hard":"#ff4444"}
        diff_color  = diff_colors.get(task["difficulty"].lower(),"#aaaaaa")

        ctk.CTkLabel(card, text="●", text_color=diff_color,
                     font=ctk.CTkFont(size=14)
                     ).grid(row=0, column=0, rowspan=2, padx=(12,4), pady=10)

        ctk.CTkLabel(card, text=task["title"],
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
                     ).grid(row=0, column=1, sticky="w", padx=4, pady=(10,0))

        ctk.CTkLabel(card, text=task["description"],
                     font=ctk.CTkFont(size=11), text_color="#aaaaaa", anchor="w"
                     ).grid(row=1, column=1, sticky="w", padx=4, pady=(0,4))

        quest_names = [quest["title"] for quest in self.db.get_task_quests(task["id"])]
        if quest_names:
            ctk.CTkLabel(
                card,
                text=f"Quest: {', '.join(quest_names[:2])}" + ("..." if len(quest_names) > 2 else ""),
                font=ctk.CTkFont(size=10),
                text_color="#66ccff",
                anchor="w"
            ).grid(row=2, column=1, sticky="w", padx=4, pady=(0,8))

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=2, rowspan=3, padx=8, pady=6)

        status_color = "#44ff88" if task["status"] == "Completed" else "#ffaa00"
        status_label = ctk.CTkLabel(info_frame, text=task["status"],
                                     text_color=status_color,
                                     font=ctk.CTkFont(size=10), cursor="hand2")
        status_label.pack(anchor="e")
        status_label.bind("<Button-1>", lambda e, tid=task["id"]: self.complete_task(tid))

        ctk.CTkLabel(info_frame,
                     text=f"🔥 {task['streak']}  |  {task['difficulty']}",
                     text_color="#888888", font=ctk.CTkFont(size=10)
                     ).pack(anchor="e", pady=2)

        btn_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        btn_frame.pack(anchor="e", pady=2)

        ctk.CTkButton(btn_frame, text="Edit", width=44, height=24,
                      font=ctk.CTkFont(size=10),
                      command=lambda tid=task["id"]: self.open_edit_task_popup(tid)
                      ).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Del", width=44, height=24,
                      font=ctk.CTkFont(size=10),
                      fg_color="#8b0000", hover_color="#aa0000",
                      command=lambda tid=task["id"]: self.delete_task(tid)
                      ).pack(side="left", padx=2)

    # -------------------------------------------------------------------------
    # MAIN SCREENS
    # -------------------------------------------------------------------------

    def show_stats(self):
        self.clear_content()

        for i in range(10):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i, weight=0)

        self.task_container.grid_rowconfigure(1, weight=1)
        self.task_container.grid_columnconfigure(0, weight=1)
        self.task_container.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(self.task_container, text="← Back",
                      width=80, height=28, font=ctk.CTkFont(size=11),
                      command=lambda: self.switch_menu(self.current_period)
                      ).grid(row=0, column=0, sticky="w", pady=6, padx=8)

        player = self.db.get_player()
        unlocked, total = self.db.get_achievement_count()

        ctk.CTkLabel(self.task_container, text="Character Stats",
                     font=ctk.CTkFont(size=17, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, pady=8)

        stats = [
            (f"Name: {player['name']}",                           "#E0E0E0"),
            (f"Level: {player['level']}",                         "#E0E0E0"),
            (f"HP: {player['current_hp']} / {player['max_hp']}",  "#ff6666"),
            (f"Armor: {player.get('armor_name', 'Cloth Armor')} (+{player.get('armor_bonus_hp', 0)} HP)", "#ff8888"),
            (f"⚔️ Attack Points: {player['attack_points']}",      "#ff9900"),
            (f"Sword: {player.get('sword_name', 'Training Sword')} (+{player.get('sword_bonus_damage', 0)} DMG)", "#ffbb66"),
            (f"⚔️ ATK per hit: {self.engine.get_attack_damage(player)}", "#ff9900"),
            (f"💰 Gold: {player['gold']}",                        "#ffd700"),
            (f"OXP: {player['oxp']}",                             "#E0E0E0"),
            (f"🏆 Achievements: {unlocked} / {total}",            "#ffd700"),
        ]

        for i, (text, color) in enumerate(stats):
            ctk.CTkLabel(self.task_container, text=text,
                         text_color=color, font=ctk.CTkFont(size=12)
                         ).grid(row=i+1, column=0, sticky="w", padx=20, pady=2)

        boss = self.db.get_active_boss()
        if boss:
            ctk.CTkLabel(self.task_container,
                         text=f"⚠️ Active Boss: {boss['name']} ({boss['hp']}/{boss['max_hp']} HP)",
                         text_color="#ff4400", font=ctk.CTkFont(size=11, weight="bold")
                         ).grid(row=10, column=0, sticky="w", padx=20, pady=4)

        self.show_skill_stats()

    def show_skill_stats(self):
        start_row = 12
        for index, skill in enumerate(self.db.get_all_skills()):
            required = 50 + (skill["level"]-1) * 25
            ctk.CTkLabel(self.task_container,
                         text=f"{skill['name']} — Lv {skill['level']}",
                         font=ctk.CTkFont(size=12, weight="bold")
                         ).grid(row=start_row+index*2, column=0, sticky="w", padx=20, pady=(6,0))
            bar = ctk.CTkProgressBar(self.task_container, height=10, corner_radius=4)
            bar.set(skill["xp"] / required if required > 0 else 0)
            bar.grid(row=start_row+index*2+1, column=0, sticky="ew", padx=20, pady=(0,4))

    def show_quests(self):
        self.clear_content()

        for i in range(12):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i, weight=0)

        self.task_container.grid_rowconfigure(3, weight=1)
        self.task_container.grid_columnconfigure(0, weight=1)

        quests = self.db.get_quests_with_progress()
        active = [quest for quest in quests if quest["status"] == "Active"]
        completed = [quest for quest in quests if quest["status"] == "Completed"]

        ctk.CTkLabel(self.task_container, text="Quest Board",
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).grid(row=0, column=0, pady=(8,2))

        ctk.CTkLabel(
            self.task_container,
            text=f"{len(active)} active  |  {len(completed)} completed",
            text_color="#aaaaaa",
            font=ctk.CTkFont(size=11)
        ).grid(row=1, column=0, pady=(0,4))

        top_actions = ctk.CTkFrame(self.task_container, fg_color="transparent")
        top_actions.grid(row=2, column=0, pady=(0,8))
        ctk.CTkButton(top_actions, text="+ Create Quest", height=30,
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=self.open_add_quest_popup
                      ).pack(side="left", padx=4)
        ctk.CTkButton(top_actions, text="Back", height=30,
                      font=ctk.CTkFont(size=11),
                      command=lambda: self.switch_menu(self.current_period)
                      ).pack(side="left", padx=4)

        quest_canvas = tk.Canvas(self.task_container, bg="#1e1e2e", highlightthickness=0)
        quest_canvas.grid(row=3, column=0, sticky="nsew", padx=6)

        quest_scrollbar = ctk.CTkScrollbar(self.task_container, command=quest_canvas.yview)
        quest_scrollbar.grid(row=3, column=1, sticky="ns")
        quest_canvas.configure(yscrollcommand=quest_scrollbar.set)
        self.task_container.grid_columnconfigure(1, weight=0)

        quest_frame = ctk.CTkFrame(quest_canvas, fg_color="transparent")
        quest_window = quest_canvas.create_window((0,0), window=quest_frame, anchor="nw")

        quest_frame.bind("<Configure>", lambda e: quest_canvas.configure(
            scrollregion=quest_canvas.bbox("all")
        ))
        quest_canvas.bind("<Configure>", lambda e: quest_canvas.itemconfig(
            quest_window, width=e.width
        ))
        quest_canvas.bind("<MouseWheel>", lambda e: quest_canvas.yview_scroll(
            int(-1*(e.delta/120)), "units"
        ))

        if not quests:
            ctk.CTkLabel(quest_frame,
                         text="No quests yet. Build a bigger life goal and link tasks to it.",
                         text_color="#aaaaaa",
                         font=ctk.CTkFont(size=12)
                         ).pack(pady=30)
            return

        for quest in quests:
            self._create_quest_card(quest_frame, quest)

    def _create_quest_card(self, parent, quest):
        card = ctk.CTkFrame(parent, corner_radius=8)
        card.pack(fill="x", padx=10, pady=6)
        card.columnconfigure(0, weight=1)

        progress = quest.get("progress") or {"progress_value": 0, "target_value": 1, "ratio": 0}
        status_color = "#44ff88" if quest["status"] == "Completed" else "#66ccff"
        mode_label = "Complete all linked tasks" if quest["progress_mode"] == "all_tasks" else "Reach total task completions"

        ctk.CTkLabel(card, text=quest["title"],
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#ffffff",
                     anchor="w"
                     ).grid(row=0, column=0, sticky="w", padx=14, pady=(12,2))
        ctk.CTkLabel(card, text=quest.get("description", ""),
                     font=ctk.CTkFont(size=11),
                     text_color="#aaaaaa",
                     wraplength=520,
                     anchor="w",
                     justify="left"
                     ).grid(row=1, column=0, sticky="w", padx=14)
        ctk.CTkLabel(card,
                     text=f"{quest['category'].title()}  |  {quest['difficulty'].title()}  |  {mode_label}",
                     text_color=status_color,
                     font=ctk.CTkFont(size=10, weight="bold")
                     ).grid(row=2, column=0, sticky="w", padx=14, pady=(4,2))
        ctk.CTkLabel(card,
                     text=f"Progress: {progress['progress_value']} / {progress['target_value']}  |  Linked tasks: {progress['linked_tasks']}",
                     text_color="#cccccc",
                     font=ctk.CTkFont(size=10)
                     ).grid(row=3, column=0, sticky="w", padx=14)

        bar = ctk.CTkProgressBar(card, height=10, corner_radius=5,
                                 progress_color="#66ccff" if quest["status"] == "Active" else "#44ff88")
        bar.set(progress["ratio"])
        bar.grid(row=4, column=0, sticky="ew", padx=14, pady=(6,8))

        task_names = [task["title"] for task in quest.get("tasks", [])]
        ctk.CTkLabel(card,
                     text="Tasks: " + (", ".join(task_names[:4]) if task_names else "No tasks linked"),
                     text_color="#888888",
                     font=ctk.CTkFont(size=10),
                     anchor="w"
                     ).grid(row=5, column=0, sticky="w", padx=14, pady=(0,6))

        rewards = (
            f"Rewards: +{quest.get('oxp_reward', 0)} OXP, "
            f"+{quest.get('gold_reward', 0)} Gold, "
            f"+{quest.get('attack_reward', 0)} ATK"
        )
        ctk.CTkLabel(card, text=rewards,
                     text_color="#ffd700",
                     font=ctk.CTkFont(size=10, weight="bold")
                     ).grid(row=6, column=0, sticky="w", padx=14, pady=(0,8))

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=0, column=1, rowspan=7, padx=10, pady=10, sticky="ne")
        ctk.CTkButton(actions, text="Edit", width=52, height=26,
                      font=ctk.CTkFont(size=10),
                      command=lambda qid=quest["id"]: self.open_edit_quest_popup(qid)
                      ).pack(pady=2)
        ctk.CTkButton(actions, text="Delete", width=52, height=26,
                      font=ctk.CTkFont(size=10),
                      fg_color="#8b0000", hover_color="#aa0000",
                      command=lambda qid=quest["id"]: self.delete_quest(qid)
                      ).pack(pady=2)

    def show_achievements(self):
        self.clear_content()

        for i in range(10):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i, weight=0)

        self.task_container.grid_rowconfigure(3, weight=1)
        self.task_container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.task_container, text="🏆  Achievements",
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, pady=(8,2))

        unlocked, total = self.db.get_achievement_count()

        ctk.CTkLabel(self.task_container,
                     text=f"{unlocked} / {total} unlocked",
                     text_color="#aaaaaa", font=ctk.CTkFont(size=12)
                     ).grid(row=1, column=0, columnspan=2, pady=(0,4))

        overall_bar = ctk.CTkProgressBar(self.task_container,
                                          height=12, corner_radius=6,
                                          progress_color="#ffd700")
        overall_bar.set(unlocked / total if total > 0 else 0)
        overall_bar.grid(row=2, column=0, columnspan=2, padx=60,
                         sticky="ew", pady=(0,8))

        ach_canvas = tk.Canvas(self.task_container, bg="#1e1e2e", highlightthickness=0)
        ach_canvas.grid(row=3, column=0, sticky="nsew")

        ach_scrollbar = ctk.CTkScrollbar(self.task_container, command=ach_canvas.yview)
        ach_scrollbar.grid(row=3, column=1, sticky="ns")
        ach_canvas.configure(yscrollcommand=ach_scrollbar.set)
        self.task_container.grid_columnconfigure(1, weight=0)

        ach_frame = ctk.CTkFrame(ach_canvas, fg_color="transparent")
        ach_window = ach_canvas.create_window((0,0), window=ach_frame, anchor="nw")

        ach_frame.bind("<Configure>", lambda e: ach_canvas.configure(
            scrollregion=ach_canvas.bbox("all")
        ))
        ach_canvas.bind("<Configure>", lambda e: ach_canvas.itemconfig(
            ach_window, width=e.width
        ))
        ach_canvas.bind("<MouseWheel>", lambda e: ach_canvas.yview_scroll(
            int(-1*(e.delta/120)), "units"
        ))

        achievements    = self.db.get_achievement()
        categories      = {}
        for ach in achievements:
            cat = ach.get("category","general")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(ach)

        for cat in ["tasks","streaks","levels","gold","skills","bosses"]:
            if cat not in categories:
                continue

            ach_list     = categories[cat]
            cat_config   = CATEGORY_CONFIG.get(cat, {"label":cat.title(),"color":"#aaaaaa"})
            cat_unlocked = sum(1 for a in ach_list if a["unlocked"])
            cat_total    = len(ach_list)

            cat_header = ctk.CTkFrame(ach_frame, corner_radius=8, fg_color="#252535")
            cat_header.pack(fill="x", padx=12, pady=(10,2))
            cat_header.columnconfigure(1, weight=1)

            ctk.CTkLabel(cat_header, text=cat_config["label"],
                         text_color=cat_config["color"],
                         font=ctk.CTkFont(size=14, weight="bold")
                         ).grid(row=0, column=0, padx=12, pady=8, sticky="w")

            ctk.CTkLabel(cat_header, text=f"{cat_unlocked}/{cat_total}",
                         text_color="#aaaaaa", font=ctk.CTkFont(size=11)
                         ).grid(row=0, column=1, padx=12, pady=8, sticky="e")

            cat_bar = ctk.CTkProgressBar(cat_header, height=6, corner_radius=3,
                                          progress_color=cat_config["color"])
            cat_bar.set(cat_unlocked / cat_total if cat_total > 0 else 0)
            cat_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0,8))

            for ach in ach_list:
                row_frame = ctk.CTkFrame(ach_frame, corner_radius=6,
                                          fg_color="#1e1e2e" if ach["unlocked"] else "#181825")
                row_frame.pack(fill="x", padx=12, pady=2)
                row_frame.columnconfigure(1, weight=1)

                icon  = "✅" if ach["unlocked"] else "🔒"
                color = cat_config["color"] if ach["unlocked"] else "#555555"

                ctk.CTkLabel(row_frame, text=icon, font=ctk.CTkFont(size=16)
                             ).grid(row=0, column=0, padx=(12,8), pady=10)

                ctk.CTkLabel(row_frame, text=ach["title"],
                             text_color=color,
                             font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
                             ).grid(row=0, column=1, sticky="w", pady=(10,2))

                ctk.CTkLabel(row_frame, text=ach["description"],
                             text_color="#888888", font=ctk.CTkFont(size=10), anchor="w"
                             ).grid(row=1, column=1, sticky="w", pady=(0,8))

        ctk.CTkButton(self.task_container, text="← Back", height=28, width=80,
                      font=ctk.CTkFont(size=11),
                      command=lambda: self.switch_menu(self.current_period)
                      ).grid(row=4, column=0, pady=6)

    def show_shop(self):
        self.clear_content()
        player = self.db.get_player()

        ctk.CTkLabel(self.task_container, text="Armory and Skill Shop",
                     font=ctk.CTkFont(size=17, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, pady=12)

        ctk.CTkLabel(self.task_container,
                     text=f"Equipped: {player.get('armor_name', 'Cloth Armor')}  |  {player.get('sword_name', 'Training Sword')}",
                     text_color="#aaaaaa",
                     font=ctk.CTkFont(size=11)
                     ).grid(row=1, column=0, columnspan=2, pady=(0,10))

        row = 2
        ctk.CTkLabel(self.task_container, text="Armor",
                     text_color="#ff8888",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=row, column=0, sticky="w", padx=20, pady=(0,4))
        row += 1

        for armor in self.engine.ARMOR_SHOP:
            owned = player.get("armor_name") == armor["name"]
            weaker = armor["hp_bonus"] <= player.get("armor_bonus_hp", 0)
            ctk.CTkLabel(self.task_container,
                         text=armor["name"],
                         font=ctk.CTkFont(size=12)
                         ).grid(row=row, column=0, sticky="w", padx=20)
            ctk.CTkButton(
                self.task_container,
                text="Equipped" if owned else "Owned Better" if weaker else f"Buy +{armor['hp_bonus']} HP ({armor['cost']} Gold)",
                height=30,
                font=ctk.CTkFont(size=11),
                state="disabled" if owned or weaker else "normal",
                command=lambda key=armor["key"]: self.buy_armor(key)
            ).grid(row=row, column=1, padx=10, pady=4)
            row += 1

        ctk.CTkLabel(self.task_container, text="Swords",
                     text_color="#ffbb66",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=row, column=0, sticky="w", padx=20, pady=(10,4))
        row += 1

        for sword in self.engine.SWORD_SHOP:
            owned = player.get("sword_name") == sword["name"]
            weaker = sword["damage_bonus"] <= player.get("sword_bonus_damage", 0)
            ctk.CTkLabel(self.task_container,
                         text=sword["name"],
                         font=ctk.CTkFont(size=12)
                         ).grid(row=row, column=0, sticky="w", padx=20)
            ctk.CTkButton(
                self.task_container,
                text="Equipped" if owned else "Owned Better" if weaker else f"Buy +{sword['damage_bonus']} DMG ({sword['cost']} Gold)",
                height=30,
                font=ctk.CTkFont(size=11),
                state="disabled" if owned or weaker else "normal",
                command=lambda key=sword["key"]: self.buy_sword(key)
            ).grid(row=row, column=1, padx=10, pady=4)
            row += 1

        ctk.CTkLabel(self.task_container, text="Skill Boosts",
                     text_color="#00ff88",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=row, column=0, sticky="w", padx=20, pady=(10,4))
        row += 1

        for skill in self.db.get_all_skills():
            ctk.CTkLabel(self.task_container,
                         text=f"{skill['name']} (Lvl {skill['level']})",
                         font=ctk.CTkFont(size=12)
                         ).grid(row=row, column=0, sticky="w", padx=20)
            ctk.CTkButton(self.task_container, text="Buy +20 XP (100 Gold)", height=30,
                          font=ctk.CTkFont(size=11),
                          command=lambda s=skill["name"]: self.buy_skill(s)
                          ).grid(row=row, column=1, padx=10, pady=4)
            row += 1

        ctk.CTkButton(self.task_container, text="← Back", height=30,
                      font=ctk.CTkFont(size=11),
                      command=lambda: self.switch_menu(self.current_period)
                      ).grid(row=row+1, column=0, pady=16)

    def show_history(self):
        self.clear_content()

        for i in range(10):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i, weight=0)

        self.task_container.grid_rowconfigure(1, weight=1)
        self.task_container.grid_columnconfigure(0, weight=1)
        self.task_container.grid_columnconfigure(1, weight=1)
        self.task_container.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(self.task_container, text="Task History",
                     font=ctk.CTkFont(size=17, weight="bold")
                     ).grid(row=0, column=0, pady=10)
        ctk.CTkButton(self.task_container, text="← Back",
                      width=80, height=28, font=ctk.CTkFont(size=11),
                      command=lambda: self.switch_menu(self.current_period)
                      ).grid(row=0, column=1, sticky="e", padx=16)

        canvas = tk.Canvas(self.task_container, bg="#2b2b2b", highlightthickness=0)
        canvas.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10)

        scrollbar = ctk.CTkScrollbar(self.task_container, command=canvas.yview)
        scrollbar.grid(row=1, column=2, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        history_frame = tk.Frame(canvas, bg="#2b2b2b")
        canvas_window = canvas.create_window((0,0), window=history_frame, anchor="nw")

        history_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        ))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(
            int(-1*(e.delta/120)), "units"
        ))

        history = self.db.get_task_history()
        if not history:
            tk.Label(history_frame, text="No completed tasks yet. Get to work!",
                     bg="#2b2b2b", fg="#aaaaaa", font=("Arial",11)).pack(pady=20)
            return

        for col, header in enumerate(["Date","Task","Difficulty"]):
            tk.Label(history_frame, text=header,
                     bg="#2b2b2b", fg="#aaaaaa", font=("Arial",10,"bold")
                     ).grid(row=0, column=col, padx=20, pady=(10,5), sticky="w")

        diff_colors = {"easy":"#00cc66","medium":"#ffcc00","hard":"#ff4444"}
        for index, (title, difficulty, date_str) in enumerate(history):
            diff_color = diff_colors.get((difficulty or "medium").lower(),"#aaaaaa")
            tk.Label(history_frame, text=date_str or "—",
                     bg="#2b2b2b", fg="#aaaaaa", font=("Arial",10)
                     ).grid(row=index+1, column=0, padx=20, pady=3, sticky="w")
            tk.Label(history_frame, text=title,
                     bg="#2b2b2b", fg="#E0E0E0", font=("Arial",10)
                     ).grid(row=index+1, column=1, padx=20, pady=3, sticky="w")
            tk.Label(history_frame, text=(difficulty or "Medium").capitalize(),
                     bg="#2b2b2b", fg=diff_color, font=("Arial",10,"bold")
                     ).grid(row=index+1, column=2, padx=20, pady=3, sticky="w")

        tk.Label(history_frame,
                 text=f"Total completions: {len(history)}",
                 bg="#2b2b2b", fg="#aaaaaa", font=("Arial",10,"italic")
                 ).grid(row=len(history)+1, column=0, columnspan=3, pady=15)

    # -------------------------------------------------------------------------
    # POPUPS
    # -------------------------------------------------------------------------

    def open_name_setup_popup(self, on_complete=None):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Welcome to SukhaOS")
        popup.geometry("400x260")
        popup.grab_set()
        popup.resizable(False, False)

        ctk.CTkLabel(popup, text="Welcome to SukhaOS!",
                     text_color="#ffcc00", font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(pady=(28,6))
        ctk.CTkLabel(popup, text="Enter your character name to begin:",
                     font=ctk.CTkFont(size=11)).pack(pady=4)

        name_entry = ctk.CTkEntry(popup, width=200, height=36,
                                   font=ctk.CTkFont(size=13), justify="center")
        name_entry.pack(pady=14)
        name_entry.focus()

        def save_name():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error","Please enter a name"); return
            if len(name) > 20:
                messagebox.showerror("Error","Name too long (max 20 chars)"); return
            self.db.set_player_name(name)
            self.refresh_player_ui()
            popup.destroy()
            if on_complete:
                on_complete()

        name_entry.bind("<Return>", lambda e: save_name())
        ctk.CTkButton(popup, text="Start Game!", height=38,
                      text_color="#ffcc00", font=ctk.CTkFont(size=13, weight="bold"),
                      command=save_name).pack(pady=6)

    def open_add_task_popup(self):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Add New Task")
        popup.geometry("420x420")
        popup.grab_set()

        ctk.CTkLabel(popup, text="Title:", font=ctk.CTkFont(size=12)
                     ).grid(row=0, column=0, padx=20, pady=8, sticky="w")
        title_entry = ctk.CTkEntry(popup, width=220)
        title_entry.grid(row=0, column=1, padx=10, pady=8)

        ctk.CTkLabel(popup, text="Description:", font=ctk.CTkFont(size=12)
                     ).grid(row=1, column=0, padx=20, pady=8, sticky="w")
        desc_entry = ctk.CTkEntry(popup, width=220)
        desc_entry.grid(row=1, column=1, padx=10, pady=8)

        ctk.CTkLabel(popup, text="Period:", font=ctk.CTkFont(size=12)
                     ).grid(row=2, column=0, padx=20, pady=8, sticky="w")
        period_var = ctk.StringVar(value="daily")
        ctk.CTkComboBox(popup, variable=period_var,
                        values=["daily","weekly","monthly","yearly"],
                        state="readonly").grid(row=2, column=1, padx=10, pady=8)

        ctk.CTkLabel(popup, text="Difficulty:", font=ctk.CTkFont(size=12)
                     ).grid(row=3, column=0, padx=20, pady=8, sticky="w")
        difficulty_var = ctk.StringVar(value="Medium")
        ctk.CTkComboBox(popup, variable=difficulty_var,
                        values=["Easy","Medium","Hard"],
                        state="readonly").grid(row=3, column=1, padx=10, pady=8)

        skills = [s["name"] for s in self.db.get_all_skills()]

        ctk.CTkLabel(popup, text="Skill 1:", font=ctk.CTkFont(size=12)
                     ).grid(row=4, column=0, padx=20, pady=8, sticky="w")
        skill1_var   = ctk.StringVar()
        skill1_entry = ctk.CTkComboBox(popup, variable=skill1_var,
                                        values=skills, state="readonly")
        skill1_entry.grid(row=4, column=1, padx=10, pady=8)

        ctk.CTkLabel(popup, text="Skill 2 (opt):", font=ctk.CTkFont(size=12)
                     ).grid(row=5, column=0, padx=20, pady=8, sticky="w")
        skill2_var   = ctk.StringVar()
        skill2_entry = ctk.CTkComboBox(popup, variable=skill2_var,
                                        values=skills, state="readonly")
        skill2_entry.grid(row=5, column=1, padx=10, pady=8)

        def save_task():
            title       = title_entry.get().strip()
            description = desc_entry.get().strip()
            period      = period_var.get()
            skill1      = skill1_var.get()
            skill2      = skill2_var.get()
            difficulty  = difficulty_var.get()

            if not title:
                messagebox.showerror("Error","Title is required"); return
            if not description:
                messagebox.showerror("Error","Description is required"); return
            if not skill1:
                messagebox.showerror("Error","At least one skill must be selected"); return

            DIFF    = {"Easy":0.8,"Medium":1.0,"Hard":1.5}
            rewards = PERIOD_REWARDS[period]
            mult    = DIFF[difficulty]

            task_id = self.db.add_task(
                title, description, period, difficulty,
                int(rewards["oxp"]*mult), int(rewards["gold"]*mult)
            )
            self.db.add_task_reward(task_id, skill1, int(rewards["sxp"]*mult))
            if skill2:
                self.db.add_task_reward(task_id, skill2, int(rewards["sxp"]*mult))
            self.engine.check_all_achievements()
            popup.destroy()
            self.show_tasks(self.current_period)

        ctk.CTkButton(popup, text="Save Task", height=36,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=save_task).grid(row=6, column=0, columnspan=2, pady=16)

    def open_edit_task_popup(self, task_id):
        task = self.db.get_task(task_id)
        popup = ctk.CTkToplevel(self.root)
        popup.title("Edit Task")
        popup.geometry("400x300")
        popup.grab_set()

        ctk.CTkLabel(popup, text="Title:", font=ctk.CTkFont(size=12)
                     ).grid(row=0, column=0, padx=20, pady=12, sticky="w")
        title_entry = ctk.CTkEntry(popup, width=220)
        title_entry.insert(0, task["title"])
        title_entry.grid(row=0, column=1, padx=10, pady=12)

        ctk.CTkLabel(popup, text="Description:", font=ctk.CTkFont(size=12)
                     ).grid(row=1, column=0, padx=20, pady=12, sticky="w")
        desc_entry = ctk.CTkEntry(popup, width=220)
        desc_entry.insert(0, task["description"])
        desc_entry.grid(row=1, column=1, padx=10, pady=12)

        ctk.CTkLabel(popup, text="Period:", font=ctk.CTkFont(size=12)
                     ).grid(row=2, column=0, padx=20, pady=12, sticky="w")
        period_var = ctk.StringVar(value=task["period"])
        ctk.CTkComboBox(popup, variable=period_var,
                        values=["daily","weekly","monthly","yearly"],
                        state="readonly").grid(row=2, column=1, padx=10, pady=12)

        def save_changes():
            self.db.update_task(task_id, title_entry.get(),
                                desc_entry.get(), period_var.get())
            popup.destroy()
            self.show_tasks(self.current_period)

        ctk.CTkButton(popup, text="Save Changes", height=36,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=save_changes).grid(row=3, column=0, columnspan=2, pady=16)

    def _build_quest_task_picker(self, popup, selected_task_ids=None):
        selected_task_ids = selected_task_ids or []
        all_tasks = self.db.get_all_tasks()

        ctk.CTkLabel(popup, text="Linked Tasks:", font=ctk.CTkFont(size=12)
                     ).grid(row=9, column=0, padx=20, pady=(8,4), sticky="nw")

        picker_frame = ctk.CTkScrollableFrame(popup, width=220, height=160)
        picker_frame.grid(row=9, column=1, padx=10, pady=(8,4), sticky="nsew")

        task_vars = {}
        for task in all_tasks:
            var = tk.IntVar(value=1 if task["id"] in selected_task_ids else 0)
            label = f"{task['title']} [{task['period']}]"
            ctk.CTkCheckBox(picker_frame, text=label, variable=var).pack(anchor="w", pady=2)
            task_vars[task["id"]] = var

        return task_vars

    def _calculate_quest_rewards(self, task_ids, quest_difficulty, progress_mode, target_count):
        total_oxp = 0
        total_gold = 0
        total_sxp = 0
        total_atk = 0

        for task_id in task_ids:
            task = self.db.get_task(task_id)
            if not task:
                continue
            total_oxp += task.get("oxp", 0)
            total_gold += task.get("gold", 0)
            total_atk += self.engine.ATTACK_PER_DIFFICULTY.get(
                task.get("difficulty", "medium").lower(), 10
            )
            for reward in self.db.get_task_rewards(task_id):
                total_sxp += reward.get("sxp", 0)

        linked_count = max(1, len(task_ids))
        difficulty_mult = QUEST_DIFFICULTY_MULTIPLIER.get(quest_difficulty, 0.30)
        mode_mult = 1.0
        if progress_mode == "completion_count":
            mode_mult += min(0.35, max(0, target_count - linked_count) * 0.08)

        quest_oxp = max(10, int(total_oxp * difficulty_mult * mode_mult))
        quest_gold = max(10, int(total_gold * (difficulty_mult * 0.85) * mode_mult))
        quest_atk = max(3, int(total_atk * (difficulty_mult * 0.55) * mode_mult))

        return {
            "oxp_reward": quest_oxp,
            "gold_reward": quest_gold,
            "attack_reward": quest_atk,
            "task_sxp_total": total_sxp,
            "linked_tasks": len(task_ids),
        }

    def open_add_quest_popup(self):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Create Quest")
        popup.geometry("560x700")
        popup.grab_set()
        popup.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(popup, text="Quest Title:", font=ctk.CTkFont(size=12)
                     ).grid(row=0, column=0, padx=20, pady=8, sticky="w")
        title_entry = ctk.CTkEntry(popup, width=260)
        title_entry.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(popup, text="Description:", font=ctk.CTkFont(size=12)
                     ).grid(row=1, column=0, padx=20, pady=8, sticky="w")
        desc_entry = ctk.CTkTextbox(popup, width=260, height=80)
        desc_entry.grid(row=1, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(popup, text="Category:", font=ctk.CTkFont(size=12)
                     ).grid(row=2, column=0, padx=20, pady=8, sticky="w")
        category_var = ctk.StringVar(value="discipline")
        ctk.CTkComboBox(popup, variable=category_var,
                        values=["discipline", "health", "mind", "career", "general"],
                        state="readonly").grid(row=2, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(popup, text="Difficulty:", font=ctk.CTkFont(size=12)
                     ).grid(row=3, column=0, padx=20, pady=8, sticky="w")
        difficulty_var = ctk.StringVar(value="Medium")
        ctk.CTkComboBox(popup, variable=difficulty_var,
                        values=["Easy", "Medium", "Hard"],
                        state="readonly").grid(row=3, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(popup, text="Progress Mode:", font=ctk.CTkFont(size=12)
                     ).grid(row=4, column=0, padx=20, pady=8, sticky="w")
        mode_var = ctk.StringVar(value="Complete linked tasks")
        mode_box = ctk.CTkComboBox(
            popup,
            variable=mode_var,
            values=["Complete linked tasks", "Reach total task completions"],
            state="readonly"
        )
        mode_box.grid(row=4, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(popup, text="Target Count:", font=ctk.CTkFont(size=12)
                     ).grid(row=5, column=0, padx=20, pady=8, sticky="w")
        target_entry = ctk.CTkEntry(popup, width=260)
        target_entry.insert(0, "1")
        target_entry.grid(row=5, column=1, padx=10, pady=8, sticky="ew")
        reward_preview = ctk.CTkLabel(
            popup,
            text="Auto rewards will be based on linked tasks and difficulty.",
            text_color="#aaaaaa",
            justify="left",
            anchor="w",
            wraplength=260,
            font=ctk.CTkFont(size=11)
        )
        reward_preview.grid(row=6, column=0, columnspan=2, padx=20, pady=(8,4), sticky="w")

        task_vars = self._build_quest_task_picker(popup)

        def update_reward_preview(*_args):
            progress_mode = "all_tasks" if mode_var.get() == "Complete linked tasks" else "completion_count"
            try:
                target_count = int(target_entry.get().strip() or "1")
            except ValueError:
                target_count = 1
            selected_tasks = [task_id for task_id, var in task_vars.items() if var.get()]
            rewards = self._calculate_quest_rewards(
                selected_tasks, difficulty_var.get().lower(), progress_mode, target_count
            )
            reward_preview.configure(
                text=(
                    f"Quest bonus: +{rewards['oxp_reward']} OXP, "
                    f"+{rewards['gold_reward']} Gold, +{rewards['attack_reward']} ATK\n"
                    f"Linked task SXP in this path: {rewards['task_sxp_total']}\n"
                    f"Balanced from {rewards['linked_tasks']} linked task(s)."
                )
            )

        for var in task_vars.values():
            var.trace_add("write", update_reward_preview)
        mode_var.trace_add("write", update_reward_preview)
        difficulty_var.trace_add("write", update_reward_preview)
        target_entry.bind("<KeyRelease>", update_reward_preview)
        update_reward_preview()

        def save_quest():
            title = title_entry.get().strip()
            description = desc_entry.get("1.0", "end").strip()
            difficulty = difficulty_var.get().lower()
            progress_mode = "all_tasks" if mode_var.get() == "Complete linked tasks" else "completion_count"
            try:
                target_count = int(target_entry.get().strip() or "1")
            except ValueError:
                messagebox.showerror("Error", "Target count must be a whole number")
                return
            selected_tasks = [task_id for task_id, var in task_vars.items() if var.get()]

            if not title:
                messagebox.showerror("Error", "Quest title is required")
                return
            if not description:
                messagebox.showerror("Error", "Quest description is required")
                return
            if not selected_tasks:
                messagebox.showerror("Error", "Select at least one task for the quest")
                return
            if progress_mode == "completion_count" and target_count < 1:
                messagebox.showerror("Error", "Target count must be at least 1")
                return

            rewards = self._calculate_quest_rewards(
                selected_tasks, difficulty, progress_mode, target_count
            )

            try:
                quest_id = self.db.add_quest(
                    title, description, category_var.get(), difficulty,
                    progress_mode, target_count,
                    rewards["oxp_reward"], rewards["gold_reward"], rewards["attack_reward"]
                )
            except Exception:
                messagebox.showerror("Error", "Quest title must be unique")
                return
            self.db.set_quest_tasks(quest_id, selected_tasks)
            popup.destroy()
            self.show_quests()

        ctk.CTkButton(popup, text="Create Quest", height=36,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=save_quest).grid(row=10, column=0, columnspan=2, pady=18)

    def open_edit_quest_popup(self, quest_id):
        quest = self.db.get_quest(quest_id)
        selected_task_ids = [task["id"] for task in self.db.get_quest_tasks(quest_id)]

        popup = ctk.CTkToplevel(self.root)
        popup.title("Edit Quest")
        popup.geometry("560x700")
        popup.grab_set()
        popup.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(popup, text="Quest Title:", font=ctk.CTkFont(size=12)
                     ).grid(row=0, column=0, padx=20, pady=8, sticky="w")
        title_entry = ctk.CTkEntry(popup, width=260)
        title_entry.insert(0, quest["title"])
        title_entry.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(popup, text="Description:", font=ctk.CTkFont(size=12)
                     ).grid(row=1, column=0, padx=20, pady=8, sticky="w")
        desc_entry = ctk.CTkTextbox(popup, width=260, height=80)
        desc_entry.insert("1.0", quest.get("description", ""))
        desc_entry.grid(row=1, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(popup, text="Category:", font=ctk.CTkFont(size=12)
                     ).grid(row=2, column=0, padx=20, pady=8, sticky="w")
        category_var = ctk.StringVar(value=quest.get("category", "general"))
        ctk.CTkComboBox(popup, variable=category_var,
                        values=["discipline", "health", "mind", "career", "general"],
                        state="readonly").grid(row=2, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(popup, text="Difficulty:", font=ctk.CTkFont(size=12)
                     ).grid(row=3, column=0, padx=20, pady=8, sticky="w")
        difficulty_var = ctk.StringVar(value=quest.get("difficulty", "medium").capitalize())
        ctk.CTkComboBox(popup, variable=difficulty_var,
                        values=["Easy", "Medium", "Hard"],
                        state="readonly").grid(row=3, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(popup, text="Progress Mode:", font=ctk.CTkFont(size=12)
                     ).grid(row=4, column=0, padx=20, pady=8, sticky="w")
        mode_label = "Complete linked tasks" if quest.get("progress_mode") == "all_tasks" else "Reach total task completions"
        mode_var = ctk.StringVar(value=mode_label)
        ctk.CTkComboBox(
            popup,
            variable=mode_var,
            values=["Complete linked tasks", "Reach total task completions"],
            state="readonly"
        ).grid(row=4, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(popup, text="Target Count:", font=ctk.CTkFont(size=12)
                     ).grid(row=5, column=0, padx=20, pady=8, sticky="w")
        target_entry = ctk.CTkEntry(popup, width=260)
        target_entry.insert(0, str(max(1, quest.get("target_count", 1))))
        target_entry.grid(row=5, column=1, padx=10, pady=8, sticky="ew")
        reward_preview = ctk.CTkLabel(
            popup,
            text="Rewards are auto-balanced from linked tasks.",
            text_color="#aaaaaa",
            justify="left",
            anchor="w",
            wraplength=260,
            font=ctk.CTkFont(size=11)
        )
        reward_preview.grid(row=6, column=0, columnspan=2, padx=20, pady=(8,4), sticky="w")

        task_vars = self._build_quest_task_picker(popup, selected_task_ids)

        def update_reward_preview(*_args):
            progress_mode = "all_tasks" if mode_var.get() == "Complete linked tasks" else "completion_count"
            try:
                target_count = int(target_entry.get().strip() or "1")
            except ValueError:
                target_count = 1
            selected_tasks = [task_id for task_id, var in task_vars.items() if var.get()]
            rewards = self._calculate_quest_rewards(
                selected_tasks, difficulty_var.get().lower(), progress_mode, target_count
            )
            reward_preview.configure(
                text=(
                    f"Quest bonus: +{rewards['oxp_reward']} OXP, "
                    f"+{rewards['gold_reward']} Gold, +{rewards['attack_reward']} ATK\n"
                    f"Linked task SXP in this path: {rewards['task_sxp_total']}\n"
                    f"Balanced from {rewards['linked_tasks']} linked task(s)."
                )
            )

        for var in task_vars.values():
            var.trace_add("write", update_reward_preview)
        mode_var.trace_add("write", update_reward_preview)
        difficulty_var.trace_add("write", update_reward_preview)
        target_entry.bind("<KeyRelease>", update_reward_preview)
        update_reward_preview()

        def save_quest():
            title = title_entry.get().strip()
            description = desc_entry.get("1.0", "end").strip()
            difficulty = difficulty_var.get().lower()
            progress_mode = "all_tasks" if mode_var.get() == "Complete linked tasks" else "completion_count"
            try:
                target_count = int(target_entry.get().strip() or "1")
            except ValueError:
                messagebox.showerror("Error", "Target count must be a whole number")
                return
            selected_tasks = [task_id for task_id, var in task_vars.items() if var.get()]

            if not title:
                messagebox.showerror("Error", "Quest title is required")
                return
            if not description:
                messagebox.showerror("Error", "Quest description is required")
                return
            if not selected_tasks:
                messagebox.showerror("Error", "Select at least one task for the quest")
                return

            if progress_mode == "completion_count" and target_count < 1:
                messagebox.showerror("Error", "Target count must be at least 1")
                return

            rewards = self._calculate_quest_rewards(
                selected_tasks, difficulty, progress_mode, target_count
            )

            try:
                self.db.update_quest(
                    quest_id, title, description, category_var.get(), difficulty,
                    progress_mode, target_count,
                    rewards["oxp_reward"], rewards["gold_reward"], rewards["attack_reward"]
                )
            except Exception:
                messagebox.showerror("Error", "Quest title must be unique")
                return
            self.db.set_quest_tasks(quest_id, selected_tasks)
            popup.destroy()
            self.show_quests()

        ctk.CTkButton(popup, text="Save Quest", height=36,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=save_quest).grid(row=10, column=0, columnspan=2, pady=18)

    def delete_quest(self, quest_id):
        if messagebox.askyesno("Delete Quest", "Delete this quest and unlink its tasks?"):
            self.db.delete_quest(quest_id)
            self.show_quests()

    def open_add_skill_popup(self):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Add New Skill")
        popup.geometry("320x160")
        popup.grab_set()

        ctk.CTkLabel(popup, text="Skill Name:", font=ctk.CTkFont(size=12)
                     ).grid(row=0, column=0, padx=20, pady=20, sticky="w")
        name_entry = ctk.CTkEntry(popup, width=160, font=ctk.CTkFont(size=12))
        name_entry.grid(row=0, column=1, padx=10, pady=20)
        name_entry.focus()

        def save_skill():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error","Skill name cannot be empty"); return
            if len(name) > 20:
                messagebox.showerror("Error","Name too long (max 20 chars)"); return
            if not self.db.add_skill(name):
                messagebox.showerror("Error",f"'{name}' already exists"); return
            popup.destroy()
            self.refresh_skill_ui()
            self.engine.check_all_achievements()

        name_entry.bind("<Return>", lambda e: save_skill())
        ctk.CTkButton(popup, text="Add Skill", height=34,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=save_skill).grid(row=1, column=0, columnspan=2, pady=8)

    # -------------------------------------------------------------------------
    # TASK ACTIONS
    # -------------------------------------------------------------------------

    def complete_task(self, task_id):
        """
        Handle task completion — shows separate popups for each event:
        1. Task reward popup (always)
        2. Skill level up popup (for each skill that leveled)
        3. Character level up popup (for each level gained)
        4. Achievement popup (for each achievement unlocked)
        5. Boss spawn alert (if a boss spawned)
        All popups appear in sequence, each must be closed before the next.
        """
        result = self.engine.complete_task(task_id)

        if result is False:
            messagebox.showinfo("Task","Task already completed")
            return

        self.refresh_player_ui()
        self.refresh_skill_ui()
        self._update_boss_ui()
        self.show_tasks(self.current_period)

        # Build popup sequence
        popup_queue = []

        # 1. Task reward popup
        popup_queue.append(lambda r=result: self.show_task_reward_popup(r))

        # 2. Skill level up popups (one per skill that leveled)
        for skill_event in result.get("skill_events", []):
            if skill_event["leveled_up"]:
                popup_queue.append(
                    lambda se=skill_event: self.show_skill_level_up_popup(se)
                )

        # 3. Character level up popups (one per level gained)
        for level_event in result.get("level_events", []):
            popup_queue.append(
                lambda le=level_event: self.show_level_up_popup(le)
            )

        # 4. Achievement popups (one per achievement)
        for title in result.get("newly_unlocked", []):
            popup_queue.append(
                lambda t=title: self.show_achievement_unlock_popup(t)
            )

        # 5. Quest completion popups
        for quest in result.get("quest_events", []):
            popup_queue.append(
                lambda q=quest: self.show_quest_complete_popup(q)
            )

        # 6. Boss spawn alert
        if result.get("boss"):
            popup_queue.append(
                lambda b=result["boss"]: self.show_boss_alert(b)
            )

        # Show all in sequence
        self._show_popups_in_sequence(popup_queue)

    def delete_task(self, task_id):
        if messagebox.askyesno("Confirm Deletion",
                               "This task will be permanently deleted.\n\nContinue?"):
            self.db.delete_task(task_id)
            self.show_tasks(self.current_period)

    def buy_skill(self, skill_name):
        result = self.engine.buy_skill_boost(skill_name)
        if result:
            self.refresh_player_ui()
            self.refresh_skill_ui()
            self.show_shop()
            # Show skill level up popup if it happened
            if result.get("leveled_up"):
                self.root.after(300, lambda: self.show_shop_skill_up_popup(result))
        else:
            messagebox.showerror("Error","Not enough Gold")

    def buy_armor(self, armor_key):
        result = self.engine.buy_armor(armor_key)
        if result.get("success"):
            self.refresh_player_ui()
            self.show_shop()
            messagebox.showinfo(
                "Armor Equipped",
                f"{result['name']} equipped.\n+{result['hp_gain']} max HP"
            )
            return

        if result.get("reason") == "gold":
            messagebox.showerror("Error", "Not enough Gold")
        elif result.get("reason") == "owned":
            messagebox.showinfo("Armor", "That armor is already equipped.")
        elif result.get("reason") == "downgrade":
            messagebox.showinfo("Armor", "You already have better armor equipped.")
        else:
            messagebox.showerror("Error", "Unable to equip armor.")

    def buy_sword(self, sword_key):
        result = self.engine.buy_sword(sword_key)
        if result.get("success"):
            self.refresh_player_ui()
            self.show_shop()
            messagebox.showinfo(
                "Sword Equipped",
                f"{result['name']} equipped.\n+{result['damage_gain']} damage per hit"
            )
            return

        if result.get("reason") == "gold":
            messagebox.showerror("Error", "Not enough Gold")
        elif result.get("reason") == "owned":
            messagebox.showinfo("Sword", "That sword is already equipped.")
        elif result.get("reason") == "downgrade":
            messagebox.showinfo("Sword", "You already have a stronger sword equipped.")
        else:
            messagebox.showerror("Error", "Unable to equip sword.")

    # -------------------------------------------------------------------------
    # NAVIGATION
    # -------------------------------------------------------------------------

    def switch_menu(self, period):
        self.current_period = period
        self.highlight_button(period)
        self.show_tasks(period)

    def highlight_button(self, period):
        for name, btn in self.bottons.items():
            if name == period:
                btn.configure(fg_color=("#1f538d","#1f538d"))
            else:
                btn.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])

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
        self.level_label.configure(text=f"{name}  |  lvl {player['level']}")
        self.xp_label.configure(text=f"{current} / {required} OXP")
        self.xp_bar.set(current / required if required > 0 else 0)

        if player["level"] >= 10:
            self.xp_bar.configure(progress_color="#00ff88")
        elif player["level"] >= 5:
            self.xp_bar.configure(progress_color="#00ccff")
        else:
            self.xp_bar.configure(progress_color="#ffcc00")

        current_hp = player.get("current_hp",100)
        max_hp     = player.get("max_hp",100)
        hp_ratio   = current_hp / max_hp if max_hp > 0 else 1

        self.hp_label.configure(text=f"HP: {current_hp} / {max_hp}")
        self.hp_bar.set(max(0, hp_ratio))

        hp_color = "#ff4444" if hp_ratio > 0.6 else "#ff8800" if hp_ratio > 0.3 else "#ffcc00"
        self.hp_bar.configure(progress_color=hp_color)

        self.attack_label.configure(
            text=f"Attack Pts: {player.get('attack_points', 0)} | Hit: {self.engine.get_attack_damage(player)}"
        )
        self.gold_label.configure(text=f"💰 Gold: {player['gold']}")
        self.gear_label.configure(
            text=f"{player.get('armor_name', 'Cloth Armor')} | {player.get('sword_name', 'Training Sword')}"
        )

    # -------------------------------------------------------------------------
    # GRAPHS
    # -------------------------------------------------------------------------

    def show_heatmap(self):
        show_heatmap(self.db)

    def show_task_graph(self):
        tasks = self.db.get_tasks_by_period(self.current_period)
        difficulty_count = {"Easy":0,"Medium":0,"Hard":0}
        completed_count  = {"Easy":0,"Medium":0,"Hard":0}

        for task in tasks:
            diff = task["difficulty"].capitalize()
            if diff in difficulty_count:
                difficulty_count[diff] += 1
                if task["status"] == "Completed":
                    completed_count[diff] += 1

        labels        = list(difficulty_count.keys())
        totals        = list(difficulty_count.values())
        done          = [completed_count[l] for l in labels]
        pending       = [totals[i]-done[i] for i in range(len(labels))]
        bar_colors    = ["#00cc66","#ffcc00","#ff4444"]
        pending_colors= ["#005522","#665500","#661111"]

        fig, ax = plt.subplots(figsize=(7,4))
        fig.patch.set_facecolor("#1e1e2e")
        ax.set_facecolor("#1e1e2e")

        x = range(len(labels))
        ax.bar(x, done,    color=bar_colors,     label="Completed", width=0.5)
        ax.bar(x, pending, color=pending_colors,  label="Pending",
               width=0.5, bottom=done)

        for i, (d, p) in enumerate(zip(done, pending)):
            if d > 0:
                ax.text(i, d/2, str(d), ha="center", va="center",
                        color="white", fontsize=10, fontweight="bold")
            if p > 0:
                ax.text(i, d+p/2, str(p), ha="center", va="center",
                        color="#aaaaaa", fontsize=10)

        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, color="#E0E0E0", fontsize=12)
        ax.set_ylabel("Tasks", color="#E0E0E0")
        ax.set_title(f"Tasks by Difficulty — {self.current_period.capitalize()}",
                     color="#E0E0E0", fontsize=13, pad=12)
        ax.tick_params(colors="#aaaaaa")
        for spine in ["bottom","left"]:
            ax.spines[spine].set_color("#444444")
        for spine in ["top","right"]:
            ax.spines[spine].set_visible(False)
        ax.legend(facecolor="#2b2b2b", edgecolor="#444444", labelcolor="#E0E0E0")
        plt.tight_layout()
        plt.show()

    # -------------------------------------------------------------------------
    # NOTIFICATIONS
    # -------------------------------------------------------------------------

    def show_login_reward(self, reward, on_close=None):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Daily Reward")
        popup.geometry("340x290")
        popup.grab_set()

        ctk.CTkLabel(popup, text="Daily Login Reward!",
                     text_color="#ffcc00", font=ctk.CTkFont(size=15, weight="bold")
                     ).pack(pady=(22,4))
        ctk.CTkLabel(popup, text=reward["message"], font=ctk.CTkFont(size=11)).pack(pady=4)
        ctk.CTkLabel(popup, text=f"+ {reward['gold']} Gold     + {reward['oxp']} OXP",
                     text_color="#00ccff", font=ctk.CTkFont(size=13, weight="bold")
                     ).pack(pady=4)
        ctk.CTkLabel(popup, text=f"⚔️ + {reward.get('bonus_atk',0)} Attack Points",
                     text_color="#ff9900", font=ctk.CTkFont(size=12)).pack(pady=2)
        if reward.get("hp_restored",0) > 0:
            ctk.CTkLabel(popup, text=f"+ {reward['hp_restored']} HP restored",
                         text_color="#ff6666", font=ctk.CTkFont(size=11)).pack(pady=2)
        ctk.CTkLabel(popup, text=f"Login Streak: {reward['streak']} days 🔥",
                     text_color="#ff9900", font=ctk.CTkFont(size=12)).pack(pady=4)

        def claim():
            popup.destroy()
            self.refresh_player_ui()
            if on_close:
                on_close()

        ctk.CTkButton(popup, text="Claim!", height=36,
                      text_color="#ffcc00", font=ctk.CTkFont(size=13, weight="bold"),
                      command=claim).pack(pady=10)

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def get_required_oxp(self, level):
        return 100 + (level-1) * 50

    def get_required_sxp(self, level):
        return 50 + (level-1) * 25
