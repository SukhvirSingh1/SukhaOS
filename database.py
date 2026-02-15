import _sqlite3

class Database:
    def __init__(self):
        self.conn = _sqlite3.connect("SukhaOS.db")
        self.cursor = self.conn.cursor()
        self.create_table()
        
    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                hours REAL,
                streak INTEGER,
                last_day TEXT,
                level INTEGER DEFAULT 1,
                xp REAL DEFAULT 0,
                type TEXT NOT NULL
            )
        ''')
        self.conn.commit()
    def add_skill(self, name, hours, streak, last_day, skill_type):
        self.cursor.execute('''
            INSERT INTO skills (name, hours, streak, last_day, type)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, hours, streak, last_day, skill_type))
        self.conn.commit()
        
    def get_skills(self, skill_type):
        self.cursor.execute('SELECT * FROM skills WHERE type = ?', (skill_type,))
        return self.cursor.fetchall()
    
    def update_skill(self, name, hours, streak, last_day, level, xp, skill_type):
        self.cursor.execute('''
            UPDATE skills
            SET hours = ?, streak = ?, last_day = ?, level = ?, xp = ?, skill_type = ?
            WHERE name = ? AND type = ?
        ''', (hours, streak, last_day, level, xp, skill_type, name, skill_type))
        self.conn.commit()
        
        