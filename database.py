"""
database.py
===========
Handles all SQLite database operations for SukhaOS.
"""

import sqlite3


class Database:
    def __init__(self, db_name="sukhaos.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    # -------------------------------------------------------------------------
    # TABLE CREATION & SEEDING
    # -------------------------------------------------------------------------

    def create_tables(self):
        """Create all tables and seed defaults on first run."""
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
                difficulty TEXT DEFAULT "medium",
                oxp INTEGER DEFAULT 0,
                gold INTEGER DEFAULT 0,
                status TEXT DEFAULT "Pending",
                last_completed TEXT,
                Streak INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_reward (
                task_id INTEGER,
                skill_name TEXT,
                sxp INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                unlocked INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                title TEXT,
                difficulty TEXT,
                date_completed TEXT
            )
        ''')

        # --- Safely add new columns to existing databases ---
        new_columns = [
            "ALTER TABLE player ADD COLUMN last_login TEXT",
            "ALTER TABLE player ADD COLUMN login_streak INTEGER DEFAULT 0",
            "ALTER TABLE player ADD COLUMN name TEXT DEFAULT 'Hero'",
            "ALTER TABLE player ADD COLUMN current_hp INTEGER DEFAULT 100",
            "ALTER TABLE player ADD COLUMN max_hp INTEGER DEFAULT 100",
            "ALTER TABLE player ADD COLUMN attack_points INTEGER DEFAULT 0",
            # is_core: 1 = core skill (locked, cannot be deleted), 0 = custom skill
            "ALTER TABLE skill ADD COLUMN is_core INTEGER DEFAULT 0",
        ]
        for sql in new_columns:
            try:
                cursor.execute(sql)
            except:
                pass  # column already exists — skip

        # --- Seed default player ---
        cursor.execute("SELECT COUNT(*) FROM player")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO player (id, oxp, level, gold, current_hp, max_hp, attack_points)
                VALUES (1, 0, 1, 0, 100, 100, 0)
            """)

        # --- Seed default skills ---
        # Core skills are locked — they power game mechanics and cannot be deleted
        # Health → max HP, Strength → attack damage, Mind → Mind Level 5 achievement
        CORE_SKILLS   = {"Mind", "Health", "Strength"}
        default_skills = ["Mind", "Health", "Strength", "IQ", "Programming", "Editing"]

        for skill in default_skills:
            is_core = 1 if skill in CORE_SKILLS else 0
            cursor.execute(
                "INSERT OR IGNORE INTO skill (name, xp, level, is_core) VALUES (?, 0, 1, ?)",
                (skill, is_core)
            )

        # --- Mark existing core skills as core in case they were seeded before is_core existed ---
        for skill in CORE_SKILLS:
            cursor.execute(
                "UPDATE skill SET is_core=1 WHERE name=?", (skill,)
            )

        # --- Seed default achievements ---
        cursor.execute("SELECT COUNT(*) FROM achievement")
        if cursor.fetchone()[0] == 0:
            for title, desc in [
                ("First Task",       "Complete your first task"),
                ("7 Day Discipline", "Reach a 7-day streak on a daily task"),
                ("Gold Collector",   "Earn 500 total gold"),
                ("Mind Level 5",     "Reach Mind skill level 5"),
            ]:
                cursor.execute(
                    "INSERT INTO achievement(title, description) VALUES (?, ?)", (title, desc)
                )

        self.conn.commit()

    # -------------------------------------------------------------------------
    # PLAYER
    # -------------------------------------------------------------------------

    def get_player(self):
        """Fetch the player record. Returns dict with all fields."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM player LIMIT 1")
        row = cursor.fetchone()

        if row is None:
            cursor.execute("""
                INSERT INTO player (id, oxp, level, gold, current_hp, max_hp, attack_points)
                VALUES (1, 0, 1, 0, 100, 100, 0)
            """)
            self.conn.commit()
            cursor.execute("SELECT * FROM player LIMIT 1")
            row = cursor.fetchone()

        return {
            "id":             row[0],
            "oxp":            row[1],
            "level":          row[2],
            "gold":           row[3],
            "last_login":     row[4] if len(row) > 4 else None,
            "login_streak":   row[5] if len(row) > 5 else 0,
            "name":           row[6] if len(row) > 6 else "Hero",
            "current_hp":     row[7] if len(row) > 7 else 100,
            "max_hp":         row[8] if len(row) > 8 else 100,
            "attack_points":  row[9] if len(row) > 9 else 0,
        }

    def update_player(self, player):
        """Save all player fields back to the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE player
            SET oxp=?, level=?, gold=?, current_hp=?, max_hp=?, attack_points=?
            WHERE id=?
        """, (
            player["oxp"],
            player["level"],
            player["gold"],
            player["current_hp"],
            player["max_hp"],
            player["attack_points"],
            player["id"]
        ))
        self.conn.commit()

    def set_player_name(self, name):
        """Set the player's character name (called once on first launch)."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE player SET name=? WHERE id=1", (name,))
        self.conn.commit()

    def update_hp(self, current_hp, max_hp):
        """Directly update HP values."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE player SET current_hp=?, max_hp=? WHERE id=1",
            (current_hp, max_hp)
        )
        self.conn.commit()

    def update_login(self, last_login, login_streak):
        """Update last login date and streak."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE player SET last_login=?, login_streak=? WHERE id=1",
            (last_login, login_streak)
        )
        self.conn.commit()

    # -------------------------------------------------------------------------
    # TASKS
    # -------------------------------------------------------------------------

    def get_task(self, task_id):
        """Fetch a single task by ID. Returns dict or None."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, description, period, oxp, gold,
                   status, last_completed, streak, difficulty
            FROM task WHERE id=?
        """, (task_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row[0], "title": row[1], "description": row[2],
            "period": row[3], "oxp": row[4], "gold": row[5],
            "status": row[6], "last_completed": row[7],
            "streak": row[8], "difficulty": row[9]
        }

    def get_tasks_by_period(self, period):
        """Fetch all tasks for a given period."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, description, status, streak, difficulty
            FROM task WHERE period=?
        """, (period,))
        return [{
            "id": r[0], "title": r[1], "description": r[2],
            "period": period, "status": r[3], "streak": r[4], "difficulty": r[5]
        } for r in cursor.fetchall()]

    def add_task(self, title, description, period, difficulty, oxp, gold):
        """Insert a new task. Returns new task ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO task(title, description, period, difficulty, oxp, gold, status)
            VALUES(?, ?, ?, ?, ?, ?, 'Pending')
        """, (title, description, period, difficulty, oxp, gold))
        self.conn.commit()
        return cursor.lastrowid

    def update_task(self, task_id, title, description, period):
        """Update task title, description, period."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE task SET title=?, description=?, period=? WHERE id=?
        """, (title, description, period, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        """Delete a task and its rewards."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM task_reward WHERE task_id=?", (task_id,))
        cursor.execute("DELETE FROM task WHERE id=?", (task_id,))
        self.conn.commit()

    def mark_task_completed(self, task_id):
        """Mark task as completed with today's date."""
        from datetime import date
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE task SET status='Completed', last_completed=? WHERE id=?",
            (date.today().isoformat(), task_id)
        )
        self.conn.commit()

    def update_task_streak(self, task_id, streak):
        """Update task streak count."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE task SET streak=? WHERE id=?", (streak, task_id))
        self.conn.commit()

    def reset_tasks(self):
        """Reset expired tasks to Pending on app startup."""
        from datetime import date, datetime
        today = date.today()
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, period, last_completed FROM task")

        for task_id, period, last_completed in cursor.fetchall():
            if not last_completed:
                continue
            last_date = datetime.strptime(last_completed, "%Y-%m-%d").date()
            reset = False
            if period == "daily":
                reset = last_date != today
            elif period == "weekly":
                reset = (last_date.isocalendar()[1] != today.isocalendar()[1]
                         or last_date.year != today.year)
            elif period == "monthly":
                reset = last_date.month != today.month or last_date.year != today.year
            elif period == "yearly":
                reset = last_date.year != today.year
            if reset:
                cursor.execute("UPDATE task SET status='Pending' WHERE id=?", (task_id,))

        self.conn.commit()

    # -------------------------------------------------------------------------
    # TASK REWARDS
    # -------------------------------------------------------------------------

    def get_task_rewards(self, task_id):
        """Fetch all skill rewards linked to a task."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT skill_name, sxp FROM task_reward WHERE task_id=?", (task_id,)
        )
        return [{"skill_name": r[0], "sxp": r[1]} for r in cursor.fetchall()]

    def add_task_reward(self, task_id, skill_name, sxp):
        """Link a skill reward to a task."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO task_reward(task_id, skill_name, sxp) VALUES(?, ?, ?)",
            (task_id, skill_name, sxp)
        )
        self.conn.commit()

    # -------------------------------------------------------------------------
    # SKILLS
    # -------------------------------------------------------------------------

    def get_all_skills(self):
        """
        Fetch all skills including is_core flag.

        Returns:
            list of dicts with keys: name, xp, level, is_core.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, xp, level, is_core FROM skill")
        return [{
            "name":    r[0],
            "xp":      r[1],
            "level":   r[2],
            "is_core": r[3]
        } for r in cursor.fetchall()]

    def get_skill(self, skill_name):
        """Fetch a skill by name. Creates it if not found."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM skill WHERE name=?", (skill_name,))
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                "INSERT INTO skill (name, xp, level, is_core) VALUES (?, 0, 1, 0)",
                (skill_name,)
            )
            self.conn.commit()
            return {"name": skill_name, "xp": 0, "level": 1, "is_core": 0}
        return {
            "id": row[0], "name": row[1], "xp": row[2],
            "level": row[3], "is_core": row[4] if len(row) > 4 else 0
        }

    def update_skill(self, skill):
        """Save updated skill XP and level."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE skill SET xp=?, level=? WHERE name=?",
            (skill["xp"], skill["level"], skill["name"])
        )
        self.conn.commit()

    def add_skill(self, skill_name):
        """
        Add a new custom skill. Returns False if duplicate.
        Custom skills always have is_core=0 so they can be deleted.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM skill WHERE name=?", (skill_name,))
        if cursor.fetchone():
            return False
        cursor.execute(
            "INSERT INTO skill(name, xp, level, is_core) VALUES (?, 0, 1, 0)",
            (skill_name,)
        )
        self.conn.commit()
        return True

    def delete_skill(self, skill_name):
        """
        Delete a non-core skill.
        Core skills (is_core=1) are protected and cannot be deleted.

        Returns:
            True if deleted, False if skill is core-protected.
        """
        cursor = self.conn.cursor()
        # Double-check in database — never delete a core skill
        cursor.execute("SELECT is_core FROM skill WHERE name=?", (skill_name,))
        row = cursor.fetchone()
        if row and row[0] == 1:
            return False  # protected — should never reach here via UI
        cursor.execute("DELETE FROM skill WHERE name=?", (skill_name,))
        self.conn.commit()
        return True

    # -------------------------------------------------------------------------
    # ACHIEVEMENTS
    # -------------------------------------------------------------------------

    def unlock_achievement(self, title):
        """Mark an achievement as unlocked."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE achievement SET unlocked=1 WHERE title=?", (title,))
        self.conn.commit()

    def get_achievement(self):
        """Fetch all achievements."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT title, description, unlocked FROM achievement")
        return [{"title": r[0], "description": r[1], "unlocked": r[2]}
                for r in cursor.fetchall()]

    # -------------------------------------------------------------------------
    # TASK HISTORY
    # -------------------------------------------------------------------------

    def get_task_history(self):
        """Fetch all task history entries, newest first."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT title, difficulty, date_completed
            FROM task_history ORDER BY date_completed DESC
        """)
        return cursor.fetchall()

    # -------------------------------------------------------------------------
    # UTILITY
    # -------------------------------------------------------------------------

    def commit(self):
        """Manually commit pending transactions."""
        self.conn.commit()