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
        
        
        # Buutons for Daily,weekly,monthly,yearly tasks
        daily_btn = tk.Button(tasks_frame, text="D", bg="#001833",fg="#E0E0E0",activebackground="#002b5c",activeforeground="white",
        relief="flat",borderwidth=1,cursor="hand2",font=("Arial", 12, "bold"),
        command=lambda: self.show_tasks("daily"))
        daily_btn.grid(row=5, column=0,pady=25)
        
        weekly_btn = tk.Button(tasks_frame, text="W", bg="#001833",fg="#E0E0E0",activebackground="#002b5c",activeforeground="white",
        relief="flat",borderwidth=1,cursor="hand2",font=("Arial", 12, "bold"),
        command=lambda: self.show_tasks("weekly"))
        weekly_btn.grid(row=6, column=0,pady=25)
        
        monthly_btn = tk.Button(tasks_frame, text="M", bg="#001833",fg="#E0E0E0",activebackground="#002b5c",activeforeground="white",
        relief="flat",borderwidth=1,cursor="hand2",font=("Arial", 12, "bold"),
        command=lambda: self.show_tasks("monthly"))
        monthly_btn.grid(row=7, column=0,pady=25)
        
        yearly_btn = tk.Button(tasks_frame, text="Y", bg="#001833",fg="#E0E0E0",activebackground="#002b5c",activeforeground="white",
        relief="flat",borderwidth=1,cursor="hand2",font=("Arial", 12, "bold"),
        command=lambda: self.show_tasks("yearly"))
        yearly_btn.grid(row=8, column=0,pady=25)
        
        self.task_container = tk.Frame(tasks_frame, bg="#001833")
        self.task_container.grid(row=1, column=0, columnspan=4, sticky="nsew")
        
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
                 text="title",
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
        tk.Label(card_frame,
                 text=status,
                 bg="#003366",
                 fg=status_color,
                 font=("Arial", 9,"italic")).grid(row=2, column=1, sticky="e", padx=10, pady=(5, 10))
        
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
            
            
        
        
      