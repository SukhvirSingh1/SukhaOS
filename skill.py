from logging import root
import tkinter as tk

class SkillUI:
    def __init__(self,root,db):
        self.root = root
        self.db = db
        self.build_ui()
        
    def build_ui(self):
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=0)
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=7)
        
        # --- 1. Top Left Frame (30%) ---
        chrctr_frame = tk.Frame(self.root, bg="#00254d", bd=2, relief="ridge")
        chrctr_frame.grid(row=0, column=0, sticky="nsew")
        

        # --- 2. Top Right Frame (70%) ---
        info_frame = tk.Frame(self.root, bg="#00254d", bd=2, relief="ridge")
        info_frame.grid(row=0, column=1, sticky="nsew")
        

        # --- 3. Bottom Frame (Whole Bottom) ---
        tasks_frame = tk.Frame(self.root, bg="#001833", bd=2, relief="ridge")
        tasks_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        


        
       
        
      
        
    # Buttons to switch between task periods
        # Button frame
        button_frame = tk.Frame(tasks_frame, bg="#001833")
        button_frame.grid(row=0, column=0, columnspan=4, sticky="ew")

        for i in range(4):
            button_frame.grid_columnconfigure(i, weight=1)

        self.bottons = {}
        btn_names = ["daily", "weekly", "monthly", "yearly"]
        btn_labels = ["D", "W", "M", "Y"]

        for i, (name, label) in enumerate(zip(btn_names, btn_labels)):
            btn = tk.Button(button_frame,
                    text=label,
                    bg="#003366",
                    fg="#E0E0E0",
                    font=("Arial", 10, "bold"),
                    command=lambda n=name.lower(): self.switch_menu(n))

            btn.grid(row=0, column=i, sticky="ew", padx=5, pady=5)
            self.bottons[name] = btn
        
            self.task_container = tk.Frame(tasks_frame, bg="#001833")
            self.task_container.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)
        
            close_btn = tk.Button(button_frame,
                      text="X",
                      bg="#660000",
                      fg="white",
                      font=("Arial", 10, "bold"),
                      command=self.close_tasks)

            close_btn.grid(row=0, column=4, padx=5)
            button_frame.grid_columnconfigure(4, weight=0)
            
    def show_main_screen(self):
        for widget in self.task_container.winfo_children():
            widget.destroy()

        tk.Label(self.task_container,
             text="Welcome to SukhaOS",
             bg="#001833",
             fg="white",
             font=("Arial", 16, "bold")
             ).pack(pady=40)

        tk.Label(self.task_container,
             text="Select D / W / M / Y to view tasks",
             bg="#001833",
             fg="#cccccc",
             font=("Arial", 11)
             ).pack()

        
    def close_tasks(self):
        self.show_main_screen()

    # Reset button colors
        for btn in self.bottons.values():
            btn.config(bg="#003366")



        
        
    def create_task_card(self, row, title, description, status):
        card_frame = tk.Frame(self.task_container, bg="#003366", height=90, relief="solid")
        card_frame.grid(row=row, column=0, pady=8, padx=15, sticky="ew")
        
        card_frame.propagate(False)  # Fix height
        self.task_container.grid_columnconfigure(0, weight=1)  # Make card expand horizontally
        
        logo = tk.Frame(card_frame, bg="#E0E0E0", width=60,)
        logo.grid(row=0, column=0, rowspan=2, sticky="ns")
        
        tk.Label(logo,text="T",bg="#E0E0E0",fg="#003366").pack(expand=True)
        
        # title
        tk.Label(card_frame,
                 text=title,
                 bg="#003366",
                 fg="#E0E0E0",
                 font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="w", padx=10, pady=(10, 0))
        
        # description
        tk.Label(card_frame,
                 text=description,
                 bg="#003366",
                 fg="#E0E0E0",
                 font=("Arial", 10)).grid(row=1, column=1, sticky="w", padx=10)
        
        # status
        status_color = "green" if status == "Completed" else "orange"

        status_label = tk.Label(card_frame,
                        text=status,
                        bg="#003366",
                        fg=status_color,
                        font=("Arial", 9, "italic"),
                        cursor="hand2")

        status_label.grid(row=2, column=1, sticky="e", padx=10, pady=(5, 10))

# Bind click event
        status_label.bind("<Button-1>", lambda e: self.toggle_status(status_label))

        
    def show_tasks(self, period):
        # Clear existing tasks
        for widget in self.task_container.winfo_children():
            widget.destroy()
        
        data = {
        "daily": [
            ("Workout", "Push workout session", "Pending"),
            ("Code", "Practice Python 1 hr", "Completed"),
            ("Study", "Revise Pol Sci", "Pending"),
            ("Content", "Post 1 reel", "Pending")
        ],
        "weekly": [
            ("Finance", "Track expenses", "Pending"),
            ("Review", "Weekly self-review", "Pending"),
            ("Skill", "Learn new concept", "Completed"),
            ("Family", "Call relatives", "Pending")
        ],
        "monthly": [
            ("Goal Check", "Review big goals", "Pending"),
            ("Upgrade", "Improve SukhaOS", "Pending"),
            ("Savings", "Invest money", "Pending"),
            ("Health", "Body check progress", "Completed")
        ],
        "yearly": [
            ("Vision", "Year reflection", "Pending"),
            ("Income", "Increase revenue", "Pending"),
            ("Skill Mastery", "Deep specialization", "Pending"),
            ("Network", "Build connections", "Completed")
        ]
       }
        
        tasks = data.get(period, [])
        for index, task in enumerate(tasks):
            self.create_task_card(index, task[0], task[1], task[2])
            
    def toggle_status(self, label):
        current = label.cget("text")

        if current == "Pending":
            label.config(text="Completed", fg="green")
        else:
            label.config(text="Pending", fg="orange")

    def switch_menu(self, period):
        self.highlight_button(period)
        self.animate_switch(period)
        
    def highlight_button(self, period):
        for name, btn in self.bottons.items():
            if name.lower() == period:
                btn.config(bg="#0059b3")
            else:
                btn.config(bg="#003366")
                
    def animate_switch(self, period):
        for widget in self.task_container.winfo_children():
            widget.destroy()
            
        self.root.after(120, lambda: self.show_tasks(period))
        
            
            
        
        
      