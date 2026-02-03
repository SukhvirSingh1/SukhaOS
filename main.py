import tkinter as tk
from tkinter import ttk

class SukhaOS:
    def __init__(self, root):
        self.root = root
        self.root.title("Sukha OS - Level Up")
        self.root.geometry("800x500")

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
        # This function clears the content area and shows the new page
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
        
        

    def load_expense_ui(self):
        # You can move your previous expense GUI code here!
        tk.Label(self.content_area, text="Total Spent: ₹0", bg="#ecf0f1").pack()
        tk.Button(self.content_area, text="Add Expense").pack(pady=10)
        
    def Skill_functions_ui(self):
        # ... (Clear widgets code) ...

        # 1. Create a transparent "Button Bar"
        # This acts as a container for our two buttons
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
        exit
    def side_skill_ui(self):
        exit
# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = SukhaOS(root)
    root.mainloop()