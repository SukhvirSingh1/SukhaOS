# layout.py - Defines the SkillUI class for SukhaOS application, responsible for building the user interface and handling task display and interactions.
import tkinter as tk
from tkinter import ttk

class SkillUI:
    def __init__(self,root,db,engine):
        self.root = root
        self.db = db
        self.engine = engine
        self.current_period = "daily"
        self.build_ui()
        
    def build_ui(self):
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=0)
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=7)
        
        # --- 1. Top Left Frame (30%) ---
        chrctr_frame = tk.Frame(self.root, bg="#00254d", bd=2, relief="ridge")
        chrctr_frame.grid(row=0, column=0, sticky="nsew")
        
        self.skill_title = tk.Label(
            chrctr_frame,
            text="Skills",
            bg="#00254d",
            fg="#E0E0E0",
            font=("Arial", 14, "bold")
        )
        self.skill_title.grid(row=0, column=0, pady=(20,10))
        
        self.skills_container = tk.Frame(chrctr_frame, bg="#00254d")
        self.skills_container.grid(row=1, column=0, sticky="nsew", padx=10)
        
        chrctr_frame.rowconfigure(1, weight=1)
        chrctr_frame.columnconfigure(0, weight=1)
        

        # --- 2. Top Right Frame (70%) ---
        info_frame = tk.Frame(self.root, bg="#00254d", bd=2, relief="ridge")
        info_frame.grid(row=0, column=1, sticky="nsew")
        
        self.level_label = tk.Label(info_frame, 
                                    text="Character lvl 1",
                                    bg="#00254d",
                                    fg="#E0E0E0",
                                    font=("Arial", 16, "bold"))
        self.level_label.grid(row=0, column=0, pady=20)
        info_frame.rowconfigure(0, weight=0)
        info_frame.rowconfigure(1, weight=0)
        info_frame.rowconfigure(2, weight=0)
        info_frame.rowconfigure(3, weight=0)
        info_frame.columnconfigure(0, weight=1)

        
        self.gold_label = tk.Label(info_frame,
                                    text="Gold: 0",
                                    bg="#00254d",
                                    fg="gold",
                                    font=("Arial", 12))
        self.gold_label.grid(row=1, column=0, pady=(0, 15))
        

        # --- 3. Bottom Frame (Whole Bottom) ---
        tasks_frame = tk.Frame(self.root, bg="#001833", bd=2, relief="ridge")
        tasks_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        tasks_frame.rowconfigure(0, weight=1)
        tasks_frame.columnconfigure(0, weight=0)
        tasks_frame.columnconfigure(1, weight=1)
        
        side_bar = tk.Frame(tasks_frame, bg="#003366")
        side_bar.grid(row=0, column=0, sticky="ns",padx=15)
        


        
       
        
      
        
    # Buttons to switch between task periods
        # Button frame
       
        

        self.bottons = {}
        btn_names = ["daily", "weekly", "monthly", "yearly"]
        btn_labels = ["D", "W", "M", "Y"]

        for i, (name, label) in enumerate(zip(btn_names, btn_labels)):
            btn = tk.Button(side_bar,
                    text=label,
                    bg="#003366",
                    fg="#E0E0E0",
                    font=("Arial", 10, "bold"),
                    command=lambda n=name: self.switch_menu(n))

            btn.grid(row=i,column=0,pady=10)
            self.bottons[name] = btn
        
        self.task_container = tk.Frame(tasks_frame, bg="#001833")
        self.task_container.grid(row=0, column=1, sticky="nsew", padx=20)
            
        for i in range(2):
            self.task_container.grid_rowconfigure(i, weight=1)
            self.task_container.grid_columnconfigure(i, weight=1)
            
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar",
                        troughcolor="#001833",
                        background="#00ccff",
                        thickness=18,
                        bordercolor="#001833",
                        lightcolor="#00ccff",
                        darkcolor="#00ccff")
            
        self.xp_label = tk.Label(tasks_frame,
                                 text="0 / 100 OXP",
                                 bg="#001833",
                                 font=("Arial", 9,"bold"),
                                 fg="#aaaaaa")
        self.xp_label.grid(row=3, column=0,)
        
        self.xp_bar = ttk.Progressbar(info_frame,
                                            orient="horizontal",
                                            mode="determinate",
                                            style="XP.Horizontal.TProgressbar")
        self.xp_bar.grid(row=3, column=0, padx=40, sticky="ew",pady=(10,2))
        
        self.switch_menu("daily")
        self.refresh_player_ui()
        self.refresh_skill_ui()
        
    # skill layout
    
    def refresh_skill_ui(self):
        
        for widget in self.skills_container.winfo_children():
            widget.destroy()
            
        skills = self.db.get_all_skills()
        
        if not skills:
            tk.Label(
                self.skills_container,
                text="No skills yet",
                bg="#00254d",
                fg="#E0E0E0",
                font=("Arial", 10)
            ).grid(row=0, column=0)
            return
        
        for index, skill in enumerate(skills):
            required = self.get_required_sxp(skill["level"])
            
            skill_text =(
                f"{skill['name']} | Lv {skill['level']} "
                f"{skill['xp']} / {required}"
            )
            
            tk.Label(
                self.skills_container,
                text=skill_text,
                bg="#00254d",
                fg="#E0E0E0",
                anchor="w",
                font=("Arial", 10)
            ).grid(row=index, column=0, sticky="ew",pady=3)
    



        
        
    def create_task_card(self, row, col, task_id, title, description, status):
        
        card = tk.Frame(self.task_container, bg="#003366", bd=0)
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
       
        
        # title
        tk.Label(card,
                 text=title,
                 bg="#003366",
                 fg="#E0E0E0",
                 font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="w", padx=10, pady=(10, 0))
        
        # description
        tk.Label(card,
                 text=description,
                 bg="#003366",
                 fg="#E0E0E0",
                 font=("Arial", 10)).grid(row=1, column=1, sticky="w", padx=10)
        
        # status
        status_color = "green" if status == "Completed" else "orange"

        status_label = tk.Label(card,
                        text=status,
                        bg="#003366",
                        fg=status_color,
                        font=("Arial", 9, "italic"),
                        cursor="hand2")

        status_label.grid(row=2, column=1, sticky="e", padx=10, pady=(5, 10))

# Bind click event
        status_label.bind("<Button-1>", lambda e, tid=task_id: self.complete_task(tid))

    def show_tasks(self, period):

        # Clear old cards
        for widget in self.task_container.winfo_children():
            widget.destroy()

        # Get tasks from database
        tasks = self.db.get_tasks_by_period(period)

        positions = [(0,0), (0,1), (1,0), (1,1)]

        for task, pos in zip(tasks, positions):
            self.create_task_card(
                pos[0],
                pos[1],
                task["id"],
                task["title"],
                task["description"],
                task["status"]
        )
            
    def get_required_oxp(self, level):
        return 100 + (level - 1) * 50
    
    def get_required_sxp(self, level):
        return 50 + (level - 1) * 25
    
    
    def switch_menu(self, period):
        self.current_period = period
        self.highlight_button(period)
        self.show_tasks(period)
        
    def highlight_button(self, period):
        for name, btn in self.bottons.items():
            if name.lower() == period:
                btn.config(bg="#0059b3")
            else:
                btn.config(bg="#003366")
                
    def refresh_player_ui(self):
        player = self.db.get_player()
        
        required = self.get_required_oxp(player["level"])
        current_xp = player["oxp"]
        
        
        self.level_label.config(
            text=f"Character lvl {player['level']}")
        self.gold_label.config(
            text=f"Gold: {player['gold']}")
        self.xp_label.config(
            text=f"{current_xp} / {required} OXP")
        
        self.xp_bar["maximum"] = required
        self.animate_bar(current_xp)
        
        if player["level"] >= 5:
            color = "#00ccff"
        elif player["level"] >= 10:
            color = "#00ff88"
        else:
            color = "#ffcc00"
        
        style = ttk.Style()
        style.theme_use('clam')    
        style.configure("XP.Horizontal.TProgressbar",
                        background=color,
                        lightcolor=color,
                        darkcolor=color)
        
    def animate_bar(self, target):
        current = self.xp_bar["value"]
        if current < target:
            self.xp_bar["value"] = current + 1
            self.root.after(5, lambda: self.animate_bar(target))
        
        
    def complete_task(self, task_id):
        player = self.engine.complete_task(task_id)
        self.refresh_player_ui()
        self.refresh_skill_ui()
        self.show_tasks(self.current_period)
        
                
 
        
            
            
        
        
      