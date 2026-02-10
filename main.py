import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import date
import os


db = "SukhaOS.db"
print("DB PATH:", os.path.abspath(db))
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
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, hour REAL, streak TEXT,last_day TEXT, level INTEGER DEFAULT 1, xp REAL DEFAULT 0)''')
        
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
            today = date.today().strftime("%Y-%m-%d")
            default_streak = 0
        
            if skill_name and skill_hour.isdigit():
                try:
                
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
        self.clear_content()
        
        tk.Label(self.content_area,text="YOUR SKILLS",
                  font=("Helvetica", 22, "bold"), bg="#ecf0f1", fg="#2c3e50").pack(pady=(30, 10))      
        
        search_frame = tk.Frame(self.content_area,bg="#ecf0f1")
        search_frame.pack(pady=10)
        
        self.cur.execute("SELECT name FROM main_skill")
        skill_list =[rows[0] for rows in self.cur.fetchall()]
        
        if not skill_list:
            tk.Label(search_frame,text="No skill found,Add one first",
                     bg="#ecf0f1",fg="#e74c3c",font=("Arial",12)).pack(pady=20)
            
        selection_frame = tk.Frame(self.content_area,bg="#ecf0f1")
        selection_frame.pack(pady=20)
        
        tk.Label(selection_frame,text="SELECT YOUR SKILL:",font=("Arial",11),bg="#ecf0f1").pack(pady=5)
        
        self.dropdown_box = ttk.Combobox(selection_frame,values=skill_list,font=("Arial",11),state="readonly")
        self.dropdown_box.pack(pady=10)
        self.dropdown_box.set("Choose a skill...")
        
        btn_inspect = tk.Button(self.content_area,text="VIEW DATA",font=("Roboto",10,"bold")
                                ,bg="#2980b9",fg="white",borderwidth=0,padx=40,pady=10,cursor="hand2",
                                command=self.specific_skill_ui).pack(pady=10)
        tk.Button(self.content_area,text="←Back",command=self.main_skill_ui,borderwidth=0).pack(side="bottom",pady=20)
        
    def specific_skill_ui(self):
        target_name = self.dropdown_box.get()
        
        if target_name == "Choose a skill...":
            return
        
        
        
        self.clear_content()
        
        try:
            self.cur.execute("SELECT name, hour, streak, last_day, level, xp FROM main_skill where name = ?",(target_name,))
            data = self.cur.fetchone()
            
            if data:
                lvl = data[4]
                xp = data[5]
                xp_needed = lvl * 100
                card = tk.Frame(self.content_area,bg="white",highlightthickness=1,padx=40,pady=40,highlightbackground="#bdc3c7")
                card.pack(padx=30)
                
                tk.Label(card,text=data[0].upper(),font=("Helvetica",12,"bold"),bg="white",fg="#007ACC").pack(pady=(0,20))
                
                stats = tk.Frame(card,bg="white")
                stats.pack()
                
                tk.Label(stats, text="Total Hours Practiced:", bg="white", font=("Arial", 12)).grid(row=0, column=0, sticky="e", pady=5)
                tk.Label(stats, text=f"{data[1]} hrs", bg="white", font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="w", padx=10)

                tk.Label(stats, text="Current Day Streak:", bg="white", font=("Arial", 12)).grid(row=1, column=0, sticky="e", pady=5)
                tk.Label(stats, text=f"🔥 {data[2]} Days", bg="white", font=("Arial", 12, "bold"), fg="#e67e22").grid(row=1, column=1, sticky="w", padx=10)

                tk.Label(stats, text="Last Logged On:", bg="white", font=("Arial", 12)).grid(row=2, column=0, sticky="e", pady=5)
                tk.Label(stats, text=data[3], bg="white", font=("Arial", 12, "italic")).grid(row=2, column=1, sticky="w", padx=10)
                
                tk.Label(card, text=f"LEVEL {lvl}", font=("Helvetica", 14, "bold"), 
                 bg="#f1c40f", fg="#2c3e50", padx=10).pack(pady=5)
                
                progress_frame = tk.Frame(card, bg="white")
                progress_frame.pack(pady=10)
        
                tk.Label(progress_frame, text=f"XP: {int(xp)} / {xp_needed}", bg="white", font=("Arial", 10)).pack()
        
                style = ttk.Style()
                style.theme_use('default')
                style.configure("green.Horizontal.TProgressbar", background='#2ecc71', thickness=20)
        
                pb = ttk.Progressbar(progress_frame, length=200, style="green.Horizontal.TProgressbar", 
                             mode='determinate')
                pb.pack()
                pb['value'] = (xp / xp_needed) * 100
            else:
                tk.Label(self.content_area, text="No data found for this skill.", fg="red").pack(pady=20)
                
        except Exception as e:
            print(f"Error:{e}")
            
        tk.Button(self.content_area, text="← New Search", command=self.view_skill_ui, borderwidth=0).pack(pady=20)
        
        
        
    def update_skill_ui(self):
        self.clear_content()
        
        
        # GUI for updating skill
        
        tk.Label(self.content_area,text="UPDATE YOUR SKILL",font=("Helvetica",22,"bold"),
                  bg="#ecf0f1", fg="#2c3e50").pack(pady=20)
        
        self.cur.execute("SELECT name FROM main_skill")
        skill_list = [row[0] for row in self.cur.fetchall()]
        
        if not skill_list:
            tk.Label(self.content_area,text="NO skill YEt!! ADD ONE FISRT",fg="red").pack
            return
        
        selection_frame = tk.Frame(self.content_area,bg="#ecf0f1")
        selection_frame.pack(pady=10)
        
        self.update_dropdown = ttk.Combobox(selection_frame,values=skill_list,state="readonly",font=("Arial",12))
        self.update_dropdown.pack(pady=10)
        self.update_dropdown.set("Choose a skill...")
        
        action_frame = tk.Frame(self.content_area,bg="white",padx=30,pady=30
                                ,highlightthickness=1,highlightbackground="#bdc3c7")
        action_frame.pack(pady=20)

        tk.Button(action_frame,text="🕒 ADD +1 HOUR",font=("Roboto",12,"bold"),
                                                          bg="#27ae60",fg="white",width=20,borderwidth=0,pady=10,cursor="hand2",
                                                          command=lambda: self.process_update(1.0)).pack(pady=10)
        
        tk.Label(action_frame, text="OR add custom hours:", font=("Arial",10),bg="white").pack()
        self.custom_hour = tk.Entry(action_frame, font=("Arial", 12), width=10, justify="center")
        self.custom_hour.pack(pady=5)
        self.custom_hour.insert(0, "0")
        
        tk.Button(action_frame,text="✅ UPDATE CUSTOM",font=("Roboto",10),
                  bg="#2980b9",fg="white",width=15,
                  command=lambda: self.process_update(float(self.custom_hour.get()))).pack(pady=5)
        
        tk.Button(self.content_area, text="← Back", command=self.main_skill_ui, borderwidth=0).pack(side="bottom", pady=20)
        
        
        
        
        
        
    def process_update(self,added_hours):
        target_name = self.update_dropdown.get()
        if target_name == "Choose a skill...":
            return
        
        today = date.today().strftime("%Y-%m-%d")
        
        try:
            self.cur.execute("SELECT hour, streak, last_day, level, xp FROM main_skill WHERE name=?",(target_name,)) 
            h, s, ld, lvl, xp = self.cur.fetchone()
        
            new_hour = h + added_hours
            new_xp = xp + (added_hours * 10)    
            new_streak = s + 1 if ld != today else s
            
            xp_needed = lvl * 100
            levelup = False
            
            while new_xp >= xp_needed:
                new_xp -= xp_needed
                lvl += 1
                xp_needed = lvl * 100
                levelup = True
                
            self.cur.execute("UPDATE main_skill SET hour=?, streak=?, last_day=?, level=?, xp=?  WHERE name=?",
                             (new_hour, new_streak, today, lvl, new_xp, target_name))
            self.conn.commit()
            
            if levelup:
                print(f"CONGRATS! {target_name} is now Level {lvl}")
                
            self.main_skill_ui()
        except Exception as e:
            print(f"Error Updating: {e}")
            
            
    def dlt_skill_ui(self):
        self.clear_content()
        
        tk.Label(self.content_area, text="DELETE SKILL",font=("Helvetica",22,"bold"),
                 pady=10,bg="#ecf0f1",fg="#2c3e50").pack(pady=20)
        
        delete_frame = tk.Frame(self.content_area,bg="#ecf0f1")
        delete_frame.pack()
        
        self.cur.execute("SELECT name FROM main_skill")
        delete_name =[rows[0] for rows in self.cur.fetchall()]
        
        self.delete_dropdown = ttk.Combobox(delete_frame,values=delete_name,state="readonly",font=("Arial",12))
        self.delete_dropdown.pack(pady=20)
        self.delete_dropdown.set("Choose a skill...")
        
        tk.Button(delete_frame,text="DELETE SKILL",font=("Roboto",12,"bold"),
                  bg="red",fg="white",width=25,activebackground="#8B0000",cursor="hand2",
                  command=self.delete_skill_ui).pack(pady=10)
        
        tk.Button(delete_frame,text="RESET STREAK",font=("Roboto",12,"bold"),
                  bg="yellow",fg="white",width=25,activebackground="#BA8E23",cursor="hand2",
                  command=self.reset_streak_ui).pack(pady=10)
        
        tk.Button(delete_frame,text="RESET HOUR",font=("Roboto",12,"bold"),
                  bg="orange",fg="white",width=25,activebackground="#BA8E23",cursor="hand2",
                  command=self.reset_hour_ui).pack(pady=10)
        
        tk.Button(delete_frame,text="<--back",command=self.main_skill_ui).pack(side="bottom",pady=10)
        
        
    def delete_skill_ui(self):
        target_name = self.delete_dropdown.get()
        if not target_name:
            return
        
        popup = tk.Toplevel(self.content_area)
        popup.title("Confirmation")
        popup.geometry("300x150")
        popup.grab_set()
        tk.Label(popup, text="ARE YOU SURE",font=("Arial",12)).pack(pady=20)
        tk.Button(popup,text="YES",command=self.final_delete ,bg="green",font=("Arial")).pack(side="left",padx=30,pady=30)
        tk.Button(popup,text="NO",command=lambda: popup.destroy(),bg="red",font=("Arial")).pack(side="right",padx=30,pady=30)
    def final_delete(self):
        target_name = self.delete_dropdown.get()
        self.cur.execute("DELETE FROM main_skill WHERE name=?",(target_name,))
        self.conn.commit()
        
        self.main_skill_ui()
            
            
    def reset_streak_ui(self):
        target_name = self.delete_dropdown.get()
        if not target_name:
            return
        
        try:
            popup = tk.Toplevel(self.content_area)
            popup.title("Confirmation")
            popup.geometry("350x150")
            
            tk.Label(popup,text="ARE YOU SURE",font=("Arial",12)).pack(pady=20)
            
            tk.Button(popup,text=("YES"),font=("Arial"),bg="green",command=self.final_reset).pack(side="left",padx=30,pady=30)
            tk.Button(popup,text=("NO"),font=("Arial"),bg="red",command=lambda: popup.destroy()).pack(side="right",padx=30,pady=30)
            
        except Exception as e:
            print(f"Error! {e}")
    def final_reset(self):
        target_name = self.delete_dropdown.get()
        self.cur.execute("UPDATE main_skill SET streak=? WHERE name=?",(0,target_name))
        self.conn.commit()
        
        self.main_skill_ui()
        
    def reset_hour_ui(self):
        target_name = self.delete_dropdown.get()
        if not target_name:
            return
        
        try:
            popup = tk.Toplevel(self.content_area)
            popup.title("Confirmation")
            popup.geometry("350x150")
            
            tk.Label(popup,text="ARE YOU SURE",font=("Arial",12)).pack(pady=20)
            
            tk.Button(popup,text=("YES"),font=("Arial"),bg="green",command=self.hour_reset).pack(side="left",padx=30,pady=30)
            tk.Button(popup,text=("NO"),font=("Arial"),bg="red",command=lambda: popup.destroy()).pack(side="right",padx=30,pady=30)
            
        except Exception as e:
            print(f"Error! {e}")
    def hour_reset(self):
        target_name = self.delete_dropdown.get()
        self.cur.execute("UPDATE main_skill SET hour=? WHERE name=?",(0,target_name))
        self.conn.commit()
        
        self.main_skill_ui()

    def side_skill():
        pass
    
    def add_skill():
        pass
    
    def view_skill():
        pass
    
    def update_skill():
        pass
        
    def delete_skill():
        pass
        
class health_ui():
    

    
    # functions in healh menu
    def workout(self):
        pass
    def health_status(self):
        pass
    def steps_tracker(self):
        pass
    
    # GUI of health menu
    
health = health_ui()
    
# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = SukhaOS(root)
    root.mainloop()