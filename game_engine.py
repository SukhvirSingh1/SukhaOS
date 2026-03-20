"""
game_engine.py
==============
Core game logic for SukhaOS.
Handles task completion, XP/leveling, HP system,
attack points currency, login rewards, and shop.
"""

from datetime import date, datetime


class GameEngine:
    """Manages all game mechanics for SukhaOS."""

    # HP constants
    HP_PER_LEVEL        = 10   # max HP gained per character level up
    HP_PER_HEALTH_LEVEL = 15   # max HP gained per Health skill level up

    # Attack points awarded per task difficulty
    ATTACK_PER_DIFFICULTY = {
        "easy":   5,
        "medium": 10,
        "hard":   15
    }

    # Attack points bonus on character level up
    ATTACK_PER_LEVEL_UP = 20

    def __init__(self, database):
        """
        Args:
            database: Instance of the Database class.
        """
        self.db = database

    # -------------------------------------------------------------------------
    # ATTACK DAMAGE CALCULATION
    # -------------------------------------------------------------------------

    def get_attack_damage(self):
        """
        Calculate the player's current attack damage per hit.
        Base damage is 10. Each level of Strength skill adds +2.

        Returns:
            int: Total attack damage per hit.
        """
        base_damage = 10
        strength_skill = self.db.get_skill("Strength")
        # Each Strength level beyond 1 adds +2 damage
        bonus = (strength_skill["level"] - 1) * 2
        return base_damage + bonus

    # -------------------------------------------------------------------------
    # TASK COMPLETION
    # -------------------------------------------------------------------------

    def complete_task(self, task_id):
        """
        Process a task completion.
        Awards gold, OXP, skill XP, attack points.
        Updates streaks, logs to history, checks level ups.

        Args:
            task_id (int): ID of the task being completed.

        Returns:
            True if completed, False if already completed.
        """
        task   = self.db.get_task(task_id)
        player = self.db.get_player()

        if task["status"] == "Completed":
            return False

        # --- Base rewards ---
        player["gold"] += task["gold"]
        player["oxp"]  += task["oxp"]

        # --- Attack points based on difficulty ---
        difficulty = task.get("difficulty", "Medium").lower()
        atk_reward = self.ATTACK_PER_DIFFICULTY.get(difficulty, 10)
        player["attack_points"] += atk_reward
        print(f"Task completed! +{atk_reward} attack points (difficulty: {difficulty})")

        # --- Skill XP ---
        rewards = self.db.get_task_rewards(task_id)
        for reward in rewards:
            skill     = self.db.get_skill(reward["skill_name"])
            skill["xp"] += reward["sxp"]

            old_level = skill["level"]
            self.check_skill_level_up(skill)

            # Health skill level up → increase max HP
            if skill["name"] == "Health" and skill["level"] > old_level:
                levels_gained        = skill["level"] - old_level
                player["max_hp"]    += self.HP_PER_HEALTH_LEVEL * levels_gained
                player["current_hp"] = min(
                    player["current_hp"] + self.HP_PER_HEALTH_LEVEL * levels_gained,
                    player["max_hp"]
                )

            self.db.update_skill(skill)

            if skill["name"] == "Mind" and skill["level"] >= 5:
                self.db.unlock_achievement("Mind Level 5")

        # --- Streak logic ---
        today          = date.today()
        last_completed = task.get("last_completed")
        new_streak     = 1

        if last_completed:
            last_date = datetime.strptime(last_completed, "%Y-%m-%d").date()

            if task["period"] == "daily":
                new_streak = task["streak"] + 1 if (today - last_date).days == 1 else 1

            elif task["period"] == "weekly":
                this_week = today.isocalendar()[1]
                last_week = last_date.isocalendar()[1]
                new_streak = task["streak"] + 1 if this_week - last_week == 1 else task["streak"]

            else:
                new_streak = task["streak"]

        # --- Streak milestones ---
        if new_streak >= 7:
            self.db.unlock_achievement("7 Day Discipline")
        if new_streak % 7 == 0:
            player["oxp"] += 50
            print(f"Streak bonus! +50 OXP for {new_streak}-day streak.")

        # --- Level up ---
        self.check_player_level_up(player)

        # --- Achievements ---
        self.db.unlock_achievement("First Task")
        if player["gold"] >= 500:
            self.db.unlock_achievement("Gold Collector")

        # --- Save ---
        self.db.mark_task_completed(task_id)
        self.db.update_task_streak(task_id, new_streak)
        self.db.update_player(player)

        # --- Log to history ---
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO task_history(task_id, title, difficulty, date_completed)
            VALUES (?, ?, ?, ?)
        """, (task["id"], task["title"], task.get("difficulty", "Medium"),
              date.today().isoformat()))
        self.db.conn.commit()

        return True

    # -------------------------------------------------------------------------
    # LOGIN REWARD
    # -------------------------------------------------------------------------

    def check_login_reward(self):
        """
        Check if a daily login reward is due.
        Awards gold, OXP, restores 5 HP, and gives bonus attack points on streaks.

        Returns:
            dict with reward info, or None if already claimed today.
        """
        player     = self.db.get_player()
        today      = date.today()
        today_str  = today.isoformat()
        last_login = player.get("last_login")
        login_streak = player.get("login_streak", 0)

        if last_login == today_str:
            return None

        # Calculate streak
        if last_login:
            last_date    = datetime.strptime(last_login, "%Y-%m-%d").date()
            diff         = (today - last_date).days
            login_streak = login_streak + 1 if diff == 1 else 1
        else:
            login_streak = 1

        # Rewards based on streak
        gold, oxp = 10, 10
        bonus_atk = 5   # small attack bonus every login

        if login_streak >= 7:
            gold, oxp = 50, 50
            bonus_atk = 20
            bonus_msg = "7 Day Login Streak! MEGA reward!"
        elif login_streak >= 3:
            gold, oxp = 25, 25
            bonus_atk = 10
            bonus_msg = f"{login_streak} Day Streak! Bonus reward!"
        else:
            bonus_msg = f"Day {login_streak} streak. Keep it up!"

        # Small HP regen on login
        hp_restored          = min(5, player["max_hp"] - player["current_hp"])
        player["current_hp"] += hp_restored

        # Apply rewards
        player["gold"]          += gold
        player["oxp"]           += oxp
        player["attack_points"] += bonus_atk

        self.check_player_level_up(player)
        self.db.update_player(player)
        self.db.update_login(today_str, login_streak)

        return {
            "gold":        gold,
            "oxp":         oxp,
            "streak":      login_streak,
            "message":     bonus_msg,
            "hp_restored": hp_restored,
            "bonus_atk":   bonus_atk
        }

    # -------------------------------------------------------------------------
    # SHOP
    # -------------------------------------------------------------------------

    def buy_skill_boost(self, skill_name):
        """
        Purchase a +20 XP skill boost for 100 gold.

        Returns:
            True if purchased, False if not enough gold.
        """
        player = self.db.get_player()
        skill  = self.db.get_skill(skill_name)

        if player["gold"] < 100:
            return False

        player["gold"] -= 100
        skill["xp"]    += 20

        old_level = skill["level"]
        self.check_skill_level_up(skill)

        # Health skill level up via shop — increase HP
        if skill["name"] == "Health" and skill["level"] > old_level:
            levels_gained        = skill["level"] - old_level
            player["max_hp"]    += self.HP_PER_HEALTH_LEVEL * levels_gained
            player["current_hp"] = min(
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
        Level up the player if they have enough OXP.
        Each level up:
          - increases max HP by HP_PER_LEVEL
          - fully restores HP
          - awards ATTACK_PER_LEVEL_UP attack points

        Formula: required OXP = 100 + (level - 1) * 50
        Modifies player dict in place.
        """
        while True:
            required = 100 + (player["level"] - 1) * 50
            if player["oxp"] >= required:
                player["oxp"]   -= required
                player["level"] += 1

                # HP bonus on level up
                player["max_hp"]     += self.HP_PER_LEVEL
                player["current_hp"]  = player["max_hp"]   # full heal on level up

                # Attack points bonus on level up
                player["attack_points"] += self.ATTACK_PER_LEVEL_UP

                print(f"Level up! Level: {player['level']}, "
                      f"Max HP: {player['max_hp']}, "
                      f"ATK: {player['attack_points']}")
            else:
                break

    def check_skill_level_up(self, skill):
        """
        Level up a skill if it has enough XP.
        Formula: required SXP = 50 + (level - 1) * 25
        Modifies skill dict in place.
        """
        while True:
            required = 50 + (skill["level"] - 1) * 25
            if skill["xp"] >= required:
                skill["xp"]    -= required
                skill["level"] += 1
                print(f"Skill '{skill['name']}' leveled up! Level: {skill['level']}")
            else:
                break