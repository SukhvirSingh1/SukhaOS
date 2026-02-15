import tkinter as tk

class SkillUI:
    def __init__(self,root,db):
        self.root = root
        self.db = db
        self.build_ui()
        
    def build_ui(self):
        tk.Label(self.root , text="Skill Manager").pack()
        
        tk.Button(self.root, text="Add skill", font=("Roboto",12,"bold"),command=self.add_skill).pack()
        tk.Button(self.root,text="View Skill",font=("roboto",12,"bold"),command=self.view_skills).pack()
        
    def add_skill(self):
        self.db.add_skill("Reading",1)
        
    def view_skills(self):
        skills = self.db.get_skills()
        print(skills)