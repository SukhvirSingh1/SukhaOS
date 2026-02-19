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
                gold INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_reward (
                    task_id INTEGER,
                    skill_name TEXT,
                    sxp INTEGER DEFAULT 0
            )
        ''')

        self.conn.commit()
        
    def get_player(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM player LIMIT 1")
        row = cursor.fetchone()
        if row is None:
            cursor.execute("INSERT INTO player (oxp, level, gold) VALUES (1, 0, 1, 0)")
        return {"id": row[0], "oxp": row[1], "level": row[2], "gold": row[3]}
    
    def get_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM task WHERE id=?", (task_id,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"Task with ID {task_id} not found")
        return {"id": row[0], "title": row[1], "description": row[2], "period": row[3], "oxp": row[4], "gold": row[5]}
    
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