"""
game_engine.py
==============
Core game logic for SukhaOS.
Handles task completion rewards, XP/level progression,
skill leveling, login streaks, shop purchases, and HP system.
"""

from datetime import date, datetime


class GameEngine:
    """
    Manages all game mechanics for SukhaOS.
    Acts as the bridge between the UI (layout.py) and the database (database.py).
    """

    # HP gained per character level up
    HP_PER_LEVEL = 10

    # Extra max HP gained when Health skill levels up
    HP_PER_HEALTH_LEVEL = 15

    def __init__(self, database):
        """
        Initialise the game engine with a database connection.

        Args:
            database: An instance of the Database class from database.py
        """
        self.db = database

    # -------------------------------------------------------------------------
    # TASK COMPLETION
    # -------------------------------------------------------------------------

    def complete_task(self, task_id):
        """
        Process a task completion — award gold, OXP, skill XP, update streaks,
        log to task history, and check for level ups and achievements.

        Args:
            task_id (int): The ID of the task being completed.

        Returns:
            True if successfully completed, False if already completed.
        """
        task = self.db.get_task(task_id)
        player = self.db.get_player()

        if task["status"] == "Completed":
            return False

        # --- Award base rewards ---
        player["gold"] += task["gold"]
        player["oxp"] += task["oxp"]

        # --- Award skill XP ---
        rewards = self.db.get_task_rewards(task_id)
        for reward in rewards:
            skill = self.db.get_skill(reward["skill_name"])
            skill["xp"] += reward["sxp"]

            # Check if Health skill leveled up — increase max HP
            old_level = skill["level"]
            self.check_skill_level_up(skill)

            if skill["name"] == "Health" and skill["level"] > old_level:
                # Each Health level gained adds HP_PER_HEALTH_LEVEL to max HP
                levels_gained = skill["level"] - old_level
                player["max_hp"] += self.HP_PER_HEALTH_LEVEL * levels_gained
                # Also heal the player by same amount — leveling Health feels rewarding
                player["current_hp"] = min(
                    player["current_hp"] + self.HP_PER_HEALTH_LEVEL * levels_gained,
                    player["max_hp"]
                )

            self.db.update_skill(skill)

            if skill["name"] == "Mind" and skill["level"] >= 5:
                self.db.unlock_achievement("Mind Level 5")

        # --- Streak logic ---
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
                new_streak = task["streak"]

        # --- Streak milestone rewards ---
        if new_streak >= 7:
            self.db.unlock_achievement("7 Day Discipline")

        if new_streak % 7 == 0:
            player["oxp"] += 50
            print(f"Streak bonus! +50 OXP for {new_streak}-day streak.")

        # --- Check for character level up ---
        self.check_player_level_up(player)

        # --- Unlock standard achievements ---
        self.db.unlock_achievement("First Task")
        if player["gold"] >= 500:
            self.db.unlock_achievement("Gold Collector")

        # --- Persist all changes ---
        self.db.mark_task_completed(task_id)
        self.db.update_task_streak(task_id, new_streak)
        self.db.update_player(player)

        # --- Log to task history ---
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO task_history(task_id, title, difficulty, date_completed)
            VALUES (?, ?, ?, ?)
        """, (
            task["id"],
            task["title"],
            task.get("difficulty", "Medium"),
            date.today().isoformat()
        ))
        self.db.conn.commit()

        return True

    # -------------------------------------------------------------------------
    # LOGIN REWARD
    # -------------------------------------------------------------------------

    def check_login_reward(self):
        """
        Check if the player is eligible for a daily login reward.
        Also restores a small amount of HP on login — waking up heals you.

        Returns:
            dict with reward info, or None if already claimed today.
        """
        player = self.db.get_player()
        today = date.today()
        today_str = today.isoformat()

        last_login = player.get("last_login")
        login_streak = player.get("login_streak", 0)

        if last_login == today_str:
            return None

        # --- Calculate login streak ---
        if last_login:
            last_date = datetime.strptime(last_login, "%Y-%m-%d").date()
            diff = (today - last_date).days
            login_streak = login_streak + 1 if diff == 1 else 1
        else:
            login_streak = 1

        # --- Determine reward ---
        gold, oxp = 10, 10

        if login_streak >= 7:
            gold, oxp = 50, 50
            bonus_msg = "7 Day Login Streak! MEGA reward!"
        elif login_streak >= 3:
            gold, oxp = 25, 25
            bonus_msg = f"{login_streak} Day Streak! Bonus reward!"
        else:
            bonus_msg = f"Day {login_streak} streak. Keep it up!"

        # --- Small HP regen on login (5 HP, capped at max) ---
        hp_restored = min(5, player["max_hp"] - player["current_hp"])
        player["current_hp"] += hp_restored

        # --- Apply rewards ---
        player["gold"] += gold
        player["oxp"] += oxp
        self.check_player_level_up(player)
        self.db.update_player(player)
        self.db.update_login(today_str, login_streak)

        return {
            "gold":         gold,
            "oxp":          oxp,
            "streak":       login_streak,
            "message":      bonus_msg,
            "hp_restored":  hp_restored
        }

    # -------------------------------------------------------------------------
    # SHOP
    # -------------------------------------------------------------------------

    def buy_skill_boost(self, skill_name):
        """
        Purchase a skill XP boost from the shop.

        Args:
            skill_name (str): The name of the skill to boost.

        Returns:
            True if successful, False if not enough gold.
        """
        player = self.db.get_player()
        skill  = self.db.get_skill(skill_name)

        COST         = 100
        BOOST_AMOUNT = 20

        if player["gold"] < COST:
            return False

        player["gold"] -= COST
        skill["xp"]    += BOOST_AMOUNT

        old_level = skill["level"]
        self.check_skill_level_up(skill)

        # If Health skill leveled up via shop boost, increase max HP too
        if skill["name"] == "Health" and skill["level"] > old_level:
            levels_gained = skill["level"] - old_level
            player["max_hp"]     += self.HP_PER_HEALTH_LEVEL * levels_gained
            player["current_hp"]  = min(
                player["current_hp"] + self.HP_PER_HEALTH_LEVEL * levels_gained,
                player["max_hp"]
            )

        self.db.update_skill(skill)
        self.db.update_player(player)
        self.db.commit()
        return True

    # -------------------------------------------------------------------------
    # LEVEL UP LOGIC
    # -------------------------------------------------------------------------

    def check_player_level_up(self, player):
        """
        Check if the player has enough OXP to level up.
        Each level up also increases max HP by HP_PER_LEVEL
        and fully restores HP as a reward.

        Formula: required OXP = 100 + (level - 1) * 50

        Args:
            player (dict): Player data dict. Modified in place.
        """
        while True:
            required = 100 + (player["level"] - 1) * 50
            if player["oxp"] >= required:
                player["oxp"]    -= required
                player["level"]  += 1

                # Increase max HP on level up
                player["max_hp"]     += self.HP_PER_LEVEL
                # Fully restore HP on level up — feels like a proper RPG reward
                player["current_hp"]  = player["max_hp"]

                print(f"Level up! Level: {player['level']}, Max HP: {player['max_hp']}")
            else:
                break

    def check_skill_level_up(self, skill):
        """
        Check if a skill has enough XP to level up.
        Modifies the skill dict in place.

        Formula: required SXP = 50 + (level - 1) * 25

        Args:
            skill (dict): Skill data dict. Modified in place.
        """
        while True:
            required = 50 + (skill["level"] - 1) * 25
            if skill["xp"] >= required:
                skill["xp"]    -= required
                skill["level"] += 1
                print(f"Skill '{skill['name']}' leveled up! Level: {skill['level']}")
            else:
                break