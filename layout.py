# layout.py - Defines the SkillUI class for SukhaOS application, responsible for building the user interface and handling task display and interactions.
import tkinter as tk
from tkinter import ttk

PERIOD_REWARDS = {
            "daily": {"gold": 20, "oxp": 20, "sxp": 10},
            "weekly": {"gold": 50, "oxp": 60, "sxp": 25},
            "monthly": {"gold": 120, "oxp": 150, "sxp": 60},
            "yearly": {"gold": 500, "oxp": 500, "sxp": 200}
            }  

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
        
        self.add_task_button = tk.Button(info_frame,
                                          text="Add Task",
                                          bg="#003366",
                                          fg="#E0E0E0",
                                          font=("Arial", 12, "bold"),
                                          command=self.open_add_task_popup)
        self.add_task_button.grid(row=2, column=0, pady=(0, 15))
        
        self.stats_btn = tk.Button(info_frame,
                                   text="Stats",
                                   bg="#003366",
                                   fg="white",
                                   font=("Arial", 11, "bold"),
                                   command=self.show_stats)
        self.stats_btn.grid(row=4, column=0, pady=15)
        
        
       

        # --- 3. Bottom Frame (Whole Bottom) ---
        tasks_frame = tk.Frame(self.root, bg="#001833", bd=2, relief="ridge")
        tasks_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        tasks_frame.rowconfigure(0, weight=1)
        tasks_frame.columnconfigure(0, weight=0)
        tasks_frame.columnconfigure(1, weight=1)
        
        side_bar = tk.Frame(tasks_frame, bg="#003366")
        side_bar.grid(row=0, column=0, sticky="ns",padx=15)
        
        shop_btn = tk.Button(side_bar,
                             text="shop",
                             bg="#003366",
                             fg="white",
                             command=self.show_shop
        )
        shop_btn.grid(row=5, column=0, pady=15)


        
        
        
      
        
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
    def clear_content(self):
        for widget in self.task_container.winfo_children():
            widget.destroy()
    
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
            



        
        
    def create_task_card(self, row, col, task_id, title, description, status, streak):
        
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
        
        # streak
        
        tk.Label(card,
                 text=f"Streak:{streak}",
                 bg="#003366",
                 fg ="orange",
                font=("Arial", 9, "italic")
                ).grid(row=0, column=2, padx=10)

# Bind click event
        status_label.bind("<Button-1>", lambda e, tid=task_id: self.complete_task(tid))
        
    def show_stats(self):
        self.clear_content()
        
        for i in range(10):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i , weight=0)
            
        self.task_container.grid_rowconfigure(0, weight=1)
        self.task_container.grid_rowconfigure(1, weight=1)
        self.task_container.grid_columnconfigure(0, weight=1)
        self.task_container.grid_columnconfigure(1, weight=1)
        
        back_btn =tk.Button(
            self.task_container,
            text="<-Back",
            bg="#003366",
            fg="white",
            command=lambda: self.switch_menu(self.current_period)
        )
        back_btn.grid(row=0, column=0, sticky="w", pady=5)
            
            
        player = self.db.get_player()
        required_oxp = 100 + (player["level"] - 1) * 50
        
        
        
        tk.Label(self.task_container,
                 text="Character Stats",
                 bg="#001833",
                 fg="white",
                 font=("Arial",16,"bold")
                 ).grid(row=0,column=0,columnspan=2,pady=10)
        
        tk.Label(self.task_container,
                 text=f"Level: {player['level']}",
                 bg="#001833",
                 fg="white",).grid(row=1,column=0,sticky="w", padx=20)
        
        tk.Label(self.task_container,
                 text=f"OXP: {player['oxp']}",
                 bg="#001833",
                 fg="white",).grid(row=2,column=0,sticky="w", padx=20)
        tk.Label(self.task_container,
                 text=f"Gold: {player['gold']}",
                 bg="#001833",
                 fg="white",).grid(row=3,column=0,sticky="w", padx=20)
        self.show_skill_stats()
        
        
    def show_skill_stats(self):
        skills = self.db.get_all_skills()
        
        start_row = 5
        
        for index, skill in enumerate(skills):
            required = 50 + (skill["level"] - 1) * 25
            
            tk.Label(self.task_container,
                     text=f"{skill['name']} - Lv {skill['level']}",
                     bg="#001833",
                     fg="white",
                     font=("Arial", 11,"bold")).grid(row=start_row+index*2, column=0, sticky="w", padx=20)
            
            progress = ttk.Progressbar(self.task_container,
                                       length=250,
                                       maximum=required,
                                       value=skill["xp"],
                                       style="TProgressbar")
            progress.grid(row=start_row+index*2+1, column=0, sticky="w", padx=20, pady=5)
        

    def show_tasks(self, period):

        # Clear old cards
        for widget in self.task_container.winfo_children():
            widget.destroy()
            
        for i in range(10):
            self.task_container.grid_rowconfigure(i, weight=0)
            self.task_container.grid_columnconfigure(i , weight=0)
            
        self.task_container.grid_rowconfigure(0, weight=1)
        self.task_container.grid_rowconfigure(1, weight=1)
        self.task_container.grid_columnconfigure(0, weight=1)
        self.task_container.grid_columnconfigure(1, weight=1)

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
                task["status"],
                task["streak"]
        )
            
    def get_required_oxp(self, level):
        return 100 + (level - 1) * 50
    
    def get_required_sxp(self, level):
        return 50 + (level - 1) * 25
    
    def show_shop(self):
        self.clear_content()
        
        tk.Label(self.task_container,
                 text="Skill boost shop",
                 bg="#001833",
                 fg="white",
                 font=("Arial",16,"bold")
                 ).grid(row=0, column=0, pady=10)
        
        skills = self.db.get_all_skills()
        
        row = 1
        for skill in skills:
            skill_text = f"{skill['name']} (Lvl {skill['level']})"
            
            tk.Label(self.task_container,
                     text=skill_text,
                     bg="#001833",
                     ).grid(row=row, column=0, sticky="w")
            
            buy_btn = tk.Button(self.task_container,
                                text="Buy +20 XP (100 GOLD)",
                                command=lambda  s=skill["name"]: self.buy_skill(s))
            buy_btn.grid(row=row, column=1, padx=10)
            row += 1
            
        tk.Button(self.task_container,
                    text="<-Back",
                  command=lambda: self.switch_menu(self.current_period)
                  ).grid(row=row+1, column=0, pady=20)
            
    def buy_skill(self, skill_name):
        success = self.engine.buy_skill_boost(skill_name)
        if success:
            self.refresh_player_ui()
            self.show_shop()
            
        else:
            print("Not enough Gold")
    
    
    
    
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
        period_menu = ttk.Combobox(popup,
                                   textvariable=period_var,
                                   values=["daily", "weekly", "monthly", "yearly"], state="readonly")
        period_menu.grid(row=2, column=1)
        
        tk.Label(popup, text="Skill 1",bg = "#00254d", fg="#E0E0E0").grid(row=3, column=0)
        skills = [skill["name"] for skill in self.db.get_all_skills()]
        skill1_var = tk.StringVar()      
        skill1_entry = ttk.Combobox(popup, values=skills, textvariable=skill1_var, state="readonly")
        skill1_entry.grid(row=3, column=1)
        
        
        
        tk.Label(popup, text="Skill 2 (OPTIONAL)",bg = "#00254d", fg="#E0E0E0").grid(row=4, column=0)
        skill2_var = tk.StringVar()
        skill2_entry = ttk.Combobox(popup, values=skills, textvariable=skill2_var, state="readonly")
        skill2_entry.grid(row=4, column=1)
        
        def save_task():
            title = title_entry.get()
            description = desc_entry.get()
            period = period_var.get()
            
            rewards = PERIOD_REWARDS.get(period)
    
           
               
            
            task_id = self.db.add_task(title, description, period, rewards["oxp"], rewards["gold"])
            self.db.add_task_reward(task_id, skill1_entry.get(), rewards["sxp"])
            if skill2_entry.get():
                self.db.add_task_reward(task_id, skill2_entry.get(), rewards["sxp"])
            popup.destroy()
            self.show_tasks(self.current_period)
            
        tk.Button(popup, text="Save Task", command=save_task).grid(row=5, column=0, columnspan=2, pady=20)
        
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
        
        
                
 
        
            
            
        
        
      