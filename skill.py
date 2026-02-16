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
        relief="flat",borderwidth=1,cursor="hand2",font=("Arial", 12, "bold"))
        daily_btn.grid(row=5, column=0,pady=25)
        
        weekly_btn = tk.Button(tasks_frame, text="W", bg="#001833",fg="#E0E0E0",activebackground="#002b5c",activeforeground="white",
        relief="flat",borderwidth=1,cursor="hand2",font=("Arial", 12, "bold"))
        weekly_btn.grid(row=6, column=0,pady=25)
        
        monthly_btn = tk.Button(tasks_frame, text="M", bg="#001833",fg="#E0E0E0",activebackground="#002b5c",activeforeground="white",
        relief="flat",borderwidth=1,cursor="hand2",font=("Arial", 12, "bold"))
        monthly_btn.grid(row=7, column=0,pady=25)
        
        yearly_btn = tk.Button(tasks_frame, text="Y", bg="#001833",fg="#E0E0E0",activebackground="#002b5c",activeforeground="white",
        relief="flat",borderwidth=1,cursor="hand2",font=("Arial", 12, "bold"))
        yearly_btn.grid(row=8, column=0,pady=25)