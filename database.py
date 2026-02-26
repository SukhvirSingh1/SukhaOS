# database.py - Handles database operations for SukhaOS application
import sqlite3

class Database:
    def __init__(self, db_name="sukhaos.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player (
                id INTEGER PRIMARY KEY,
                oxp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                gold INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skill (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task (
                id INTEGER PRIMARY KEY,
                title TEXT,
                description TEXT,
                period TEXT,
                oxp INTEGER DEFAULT 0,
                gold INTEGER DEFAULT 0,
                status TEXT DEFAULT "Pending",
                last_completed TEXT            )
        ''')
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_reward (
                    task_id INTEGER,
                    skill_name TEXT,
                    sxp INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute("SELECT COUNT(*) FROM player")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("INSERT INTO player (id, oxp, level, gold) VALUES (1, 0, 1, 0)")
        
        default_skills = ["Mind","Health","Strength","IQ","Programming",
                          "Editing"]
        for skill in default_skills:
            cursor.execute("INSERT OR IGNORE INTO skill (name, xp, level) VALUES (?, 0, 1)", (skill,))
        self.conn.commit()
        
    def get_player(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM player LIMIT 1")
        row = cursor.fetchone()
        if row is None:
            cursor.execute("INSERT INTO player (id, oxp, level, gold) VALUES (1, 0, 1, 0)")
            self.conn.commit()
            cursor.execute("SELECT * FROM player LIMIT 1")
            row = cursor.fetchone()
        return {"id": row[0], "oxp": row[1], "level": row[2], "gold": row[3]}
    
    def get_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, description, period, oxp, gold, status FROM task WHERE id=?", (task_id,))
        row = cursor.fetchone()
        if row is None:
            raise None
        return {"id": row[0], "title": row[1], "description": row[2], "period": row[3], "oxp": row[4], "gold": row[5], "status": row[6]}
    
    def get_task_rewards(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT skill_name, sxp FROM task_reward WHERE task_id=?", (task_id,))
        return [{"skill_name": r[0], "sxp": r[1]} for r in cursor.fetchall()]
    
    def get_skill(self, skill_name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM skill WHERE name=?", (skill_name,))
        row = cursor.fetchone()
        if row is None:
            cursor.execute("INSERT INTO skill (name, xp, level) VALUES (?, 0, 1)", (skill_name,))
            self.conn.commit()
            return { "name": skill_name, "xp": 0, "level": 1}
        return {"id": row[0], "name": row[1], "xp": row[2], "level": row[3]}
    
    def update_skill(self, skill):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE skill SET xp=?, level=? WHERE name=?", 
                       (skill["xp"], skill["level"], skill["name"]))
        self.conn.commit()
        
    def update_player(self, player):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE player SET oxp=?, level=?, gold=? WHERE id=?", 
                       (player["oxp"], player["level"], player["gold"], player["id"]))
        self.conn.commit()
        
    def commit(self):
        self.conn.commit()
        
    def get_tasks_by_period(self, period):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, description, status FROM task WHERE period=?", (period,))
        
        rows = cursor.fetchall()
        
        
        return [{"id": row[0], "title": row[1], "description": row[2], "period": period, "status": row[3]} for row in rows]
    
    def mark_task_completed(self, task_id):
        from datetime import date
        today = date.today().isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute("UPDATE task SET status='Completed', last_completed=? WHERE id=?", (today, task_id))
        self.conn.commit()
        
    def reset_tasks(self):
        from datetime import date,datetime
        today = date.today()
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT id, period, last_completed FROM task")
        tasks = cursor.fetchall()
        
        for task_id, period, last_completed in tasks:
            
            if last_completed is None:
                continue
            
            last_date = datetime.strptime(last_completed, "%Y-%m-%d").date()
            
            reset = False
            if period == "daily":
               reset = last_date != today
               
            elif period == "weekly":
                reset = last_date.isocalendar()[1] != today.isocalendar()[1]\
                    or last_date.year != today.year
                    
            elif period == "monthly":
                reset = last_date.month != today.month \
                    or last_date.year != today.year
            
            elif period == "yearly":
                reset = last_date.year != today.year
                
            if reset:
                cursor.execute("UPDATE task SET status='Pending' WHERE id=?", (task_id,))
        self.conn.commit()
        
    def get_all_skills(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, xp, level FROM skill")
        rows = cursor.fetchall()     
        
        return[
            {"name":r[0],"xp":r[1],"level":r[2]}
            for r in rows
        ]
        
    def add_task(self, title, description, period, oxp, gold):
        cursor = self.conn.cursor()
        cursor.execute("""
                       INSERT INTO task(title, description, period, oxp, gold, status)
                       VALUES(?, ?, ?, ? ,?, 'Pending')
        """,(title, description, period, oxp, gold))
        self.conn.commit()
        return cursor.lastrowid
    
    def add_task_reward(self, task_id, skill_name, sxp):
        cursor = self.conn.cursor()
        cursor.execute("""
                    INSERT INTO task_reward(task_id, skill_name, sxp)
                    VALUES(?, ?, ?)
                    """,(task_id, skill_name, sxp))
        self.conn.commit()


       