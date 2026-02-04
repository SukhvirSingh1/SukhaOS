import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import date

db = "SukhaOS.db"
class SukhaOS:
    def __init__(self, root):
        self.root = root
        self.root.title("Sukha OS - Level Up")
        self.root.geometry("800x500")
        self.init_database()
        
    def init_database(self):
        self.conn =sqlite3.connect(db)
        self.cur = self.conn.cursor()
        
        self.cur.execute('''CREATE TABLE IF NOT EXISTS main_skill
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, hour REAL, streak TEXT,last_day TEXT)''')
        
        self.conn.commit()     

        # 1. SIDEBAR
        self.sidebar = tk.Frame(self.root, width=200, bg="#2c3e50")
        self.sidebar.pack(side="left", fill="y")

        # 2. MAIN CONTENT AREA
        self.content_area = tk.Frame(self.root, bg="#ecf0f1")
        self.content_area.pack(side="right", expand=True, fill="both")

        self.create_sidebar()

    def create_sidebar(self):
        tk.Label(self.sidebar, text="SUKHA OS", font=("Arial", 14, "bold"), 
                 bg="#2c3e50", fg="white", pady=20).pack()

    
        sections = ["Skill", "Health", "Mind", "Occupation", "Expense", "Habits", "Work", "Thoughts"]
        
        for name in sections:
            btn = tk.Button(self.sidebar, text=name, width=20, bg="#34495e", fg="white",
                            relief="flat", pady=10, cursor="hand2",
                            command=lambda n=name: self.switch_page(n))
            btn.pack(fill="x", padx=10, pady=5)

    def switch_page(self, page_name):
    
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        # Heading for the page
        tk.Label(self.content_area, text=f"{page_name} Section", 
                 font=("Arial", 20), bg="#ecf0f1").pack(pady=20)
        
        # Logic to call your features
        if page_name == "Skill":
            self.Skill_functions_ui()
        elif page_name == "Mind":
            tk.Label(self.content_area, text="Mind Functions Coming Soon!", bg= "#ecf0f1").pack()
        elif page_name == "Occupation":
            tk.Label(self.content_area, text="Occupation Functions Coming Soon!", bg= "#ecf0f1").pack()
        elif page_name == "Habits":
            tk.Label(self.content_area, text="Habits Functions Coming Soon!", bg= "#ecf0f1").pack()
        elif page_name == "Work":
            tk.Label(self.content_area, text="Work Functions Coming Soon!", bg= "#ecf0f1").pack()
        elif page_name == "Thoughts":
            tk.Label(self.content_area, text="Thoughts Functions Coming Soon!", bg= "#ecf0f1").pack()
        elif page_name == "Expense":
            self.load_expense_ui()
        elif page_name == "Health":
            tk.Label(self.content_area, text="Workout Tracker Coming Soon!", bg="#ecf0f1").pack()
        
        #  for clearing page
    def clear_content(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()

    def load_expense_ui(self):
        
        tk.Label(self.content_area, text="Total Spent: ₹0", bg="#ecf0f1").pack()
        tk.Button(self.content_area, text="Add Expense").pack(pady=10)
        
    def Skill_functions_ui(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
            
        tk.Label(self.content_area,text="SKILL MENU",font=("Arial",18,"bold")).pack(pady=20)
            
        button_bar = tk.Frame(self.content_area, bg="#ecf0f1")
        button_bar.pack(fill="x", pady=(100, 20)) 

        
        btn_main = tk.Button(button_bar, text="Main Skill", font=("Roboto", 12, "bold"),
                           bg="#007ACC", fg="white", activebackground="#005A99",
                           padx=20, pady=10, borderwidth=0, cursor="hand2",
                           command=self.main_skill_ui)
        btn_main.pack(side="left", padx=100) 

        
        btn_side = tk.Button(button_bar, text="Side Skill", font=("Roboto", 12, "bold"),
                           bg="#007ACC", fg="white", activebackground="#005A99",
                           padx=20, pady=10, borderwidth=0, cursor="hand2",
                           command=self.side_skill_ui)
        btn_side.pack(side="right", padx=100) 
        
        
    def main_skill_ui(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
            
        tk.Label(self.content_area,text="SKILL DASHBOARD",font=("Roboto",20,"bold"),
                 bg="#ecf0f1", fg="#2c3e50").pack(pady=30)
        
        
        option_frame  = tk.Frame(self.content_area, bg="#ecf0f1")
        option_frame.pack(pady=10)
        
        btn_add = tk.Button(option_frame,text="➕ ADD SKILL",font=("Arial",12,"bold"),
                            bg="#27ae60",fg="white",width=25,pady=10,borderwidth=0,cursor="hand2",
                            command=self.add_skill_ui).pack(pady=10)
        
        btn_view = tk.Button(option_frame,text="📊 VIEW SKILL",font=("Arial",12,"bold"),
                             bg="#2980b9",fg="white",width=25,pady=10,borderwidth=0,cursor="hand2",
                             command=self.view_skill_ui).pack(pady=10)
        
        btn_update = tk.Button(option_frame,text="🔄 UPDATE SKILL",font=("Roboto", 12, "bold"),
                  bg="#f39c12", fg="white", width=25, pady=10, borderwidth=0, 
                  activebackground="#e67e22", cursor="hand2", 
                  command=self.update_skill_ui).pack(pady=10)
        
        btn_dlt = tk.Button(option_frame,text="🗑️DELETE SKILL",font=("Roboto",12,"bold"),
                            bg="#e74c3c",fg="white",width=25,activebackground="#c0392b",pady=10
                            ,cursor="hand2",borderwidth=0,
                            command=self.dlt_skill_ui).pack(pady=10)
        
        btn_back = tk.Button(self.content_area,text="← Back to main menu",font=("Arial",10),
                             bg="#95a5a6", fg="white",borderwidth=0, cursor="hand2",
                             command=self.Skill_functions_ui).pack(side="bottom",pady=20)
        
        
        
    def side_skill_ui(self):
        exit
        
    def add_skill_ui(self):
       
        self.clear_content()
        
        tk.Label(self.content_area, text="Add New Pursuit", 
                 font=("Helvetica", 22, "bold"), bg="#ecf0f1", fg="#2c3e50").pack(pady=(30, 10))
        
        tk.Label(self.content_area, text="Every brick builds the house.", 
                 font=("Helvetica", 10, "italic"), bg="#ecf0f1", fg="#7f8c8d").pack(pady=(0, 20))

        form_frame = tk.Frame(self.content_area, bg="white", padx=30, pady=30, 
                              highlightbackground="#bdc3c7", highlightthickness=1)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="SKILL NAME", font=("Arial", 9, "bold"), 
                 bg="white", fg="#34495e").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.name_entry = tk.Entry(form_frame, font=("Arial", 12), width=25, relief="flat", bg="#f8f9fa")
        self.name_entry.grid(row=1, column=0, pady=(0, 15))
        self.name_entry.insert(0, "")

        tk.Label(form_frame, text="INITIAL HOURS", font=("Arial", 9, "bold"), 
                 bg="white", fg="#34495e").grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.hour_entry = tk.Entry(form_frame, font=("Arial", 12), width=25, relief="flat", bg="#f8f9fa")
        self.hour_entry.grid(row=3, column=0, pady=(0, 15))
        self.hour_entry.insert(0, "0")

        btn_save = tk.Button(self.content_area, text="CONFIRM & REGISTER", 
                             font=("Roboto", 11, "bold"), bg="#27ae60", fg="white", 
                             padx=40, pady=12, borderwidth=0, cursor="hand2",
                             activebackground="#2ecc71", command=self.save_skill_ui)
        btn_save.pack(pady=25)

        tk.Button(self.content_area, text="Go Back", font=("Arial", 10, "underline"),
                  bg="#ecf0f1", fg="#7f8c8d", borderwidth=0, cursor="hand2",
                  command=self.main_skill_ui).pack(side="bottom", pady=20)
        
    def save_skill_ui(self):
            skill_name = self.name_entry.get()
            skill_hour = self.hour_entry.get()
            today = date.today().strftime("%Y-%m-%d") # Use lowercase %d for day
            default_streak = 0
        
            if skill_name and skill_hour.isdigit():
                try:
                # FIX: Removed '9=' and fixed the placeholders
                    self.cur.execute('''INSERT INTO main_skill(name, hour, streak, last_day) 
                                   VALUES (?, ?, ?, ?)''',
                                (skill_name, float(skill_hour), default_streak, today))
                    self.conn.commit()
                
                    print(f"SUCCESS: {skill_name} saved to SukhaOS on {today}")
                    self.main_skill_ui() # Go back to dashboard
                except Exception as e:
                    print(f"Database Error: {e}")
            else:
                print("Error! Enter valid name and numeric hours")
        
        
        
        
        
    def view_skill_ui(self):
        print("comming soon!!")
        exit
    def update_skill_ui(self):
        print("comming soon!!")
    def dlt_skill_ui(self):
        print("comming soon!!")
# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = SukhaOS(root)
    root.mainloop()