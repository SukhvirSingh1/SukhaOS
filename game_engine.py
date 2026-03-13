# game_engine.py
# xp, levels, rewards logic for SukhaOS application

from datetime import date, datetime

class GameEngine:
    def __init__(self, database):
        self.db = database

    def complete_task(self, task_id):
        task = self.db.get_task(task_id)
        player = self.db.get_player()

        if task["status"] == "Completed":
            return False  # Task already completed

        # --- Rewards ---
        player["gold"] += task["gold"]
        player["oxp"] += task["oxp"]

        # --- Skill XP (only once) ---
        rewards = self.db.get_task_rewards(task_id)
        for reward in rewards:
            skill = self.db.get_skill(reward["skill_name"])
            skill["xp"] += reward["sxp"]
            self.check_skill_level_up(skill)
            self.db.update_skill(skill)

            if skill["name"] == "Mind" and skill["level"] >= 5:
                self.db.unlock_achievement("Mind Level 5")

        # --- Streak Logic ---
        today = date.today()
        last_completed = task.get("last_completed")
        new_streak = 1

        if last_completed:
            last_date = datetime.strptime(last_completed, "%Y-%m-%d").date()

            if task["period"] == "daily":
                if (today - last_date).days == 1:
                    new_streak = task["streak"] + 1
                else:
                    new_streak = 1

            elif task["period"] == "weekly":
                this_week = today.isocalendar()[1]
                last_week = last_date.isocalendar()[1]
                if this_week - last_week == 1:
                    new_streak = task["streak"] + 1
                else:
                    new_streak = task["streak"]

            else:
                # monthly/yearly — just preserve streak
                new_streak = task["streak"]

        # --- Streak Bonus ---
        if new_streak >= 7:
            self.db.unlock_achievement("7 Day Discipline")

        if new_streak % 7 == 0:
            player["oxp"] += 50
            print(f"Streak bonus! Player earned 50 OXP for a {new_streak}-day streak.")

        # --- Level Up ---
        self.check_player_level_up(player)

        # --- Achievements ---
        self.db.unlock_achievement("First Task")
        if player["gold"] >= 500:
            self.db.unlock_achievement("Gold Collector")

        # --- Save everything ---
        self.db.mark_task_completed(task_id)
        self.db.update_task_streak(task_id, new_streak)
        self.db.update_player(player)

        # --- Task History ---
        today_str = date.today().isoformat()
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO task_history(task_id, title, difficulty, date_completed)
            VALUES (?, ?, ?, ?)
        """, (
            task["id"],
            task["title"],
            task.get("difficulty", "Medium"),
            today_str
        ))
        self.db.conn.commit()

        return True

    def buy_skill_boost(self, skill_name):
        player = self.db.get_player()
        skill = self.db.get_skill(skill_name)

        COST = 100
        BOOST_AMOUNT = 20

        if player["gold"] < COST:
            return False  # not enough gold

        player["gold"] -= COST
        skill["xp"] += BOOST_AMOUNT

        self.check_skill_level_up(skill)

        self.db.update_skill(skill)
        self.db.update_player(player)
        self.db.commit()
        return True

    def check_player_level_up(self, player):
        while True:
            required = 100 + (player["level"] - 1) * 50
            if player["oxp"] >= required:
                player["oxp"] -= required
                player["level"] += 1
                print(f"Player leveled up! New level: {player['level']}, OXP: {player['oxp']}")
            else:
                break

    def check_skill_level_up(self, skill):
        while True:
            required = 50 + (skill["level"] - 1) * 25
            if skill["xp"] >= required:
                skill["xp"] -= required
                skill["level"] += 1
                print(f"Skill {skill['name']} leveled up! New level: {skill['level']}, XP: {skill['xp']}")
            else:
                break