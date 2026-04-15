"""
game_engine.py
==============
Core game logic for SukhaOS.
Now tracks all events (level ups, skill ups, achievements)
so the UI can show proper reward popups for each one.
"""

from datetime import date, datetime
import random


class GameEngine:
    HP_PER_LEVEL          = 10
    HP_PER_HEALTH_LEVEL   = 15
    ATTACK_PER_DIFFICULTY = {"easy": 3, "medium": 6, "hard": 9}
    ATTACK_PER_LEVEL_UP   = 8
    ARMOR_SHOP = [
        {"key": "leather", "name": "Leather Armor", "cost": 140, "hp_bonus": 20},
        {"key": "iron", "name": "Iron Armor", "cost": 300, "hp_bonus": 52},
        {"key": "dragon", "name": "Dragon Armor", "cost": 560, "hp_bonus": 100},
    ]
    SWORD_SHOP = [
        {"key": "iron", "name": "Iron Sword", "cost": 125, "damage_bonus": 3},
        {"key": "steel", "name": "Steel Sword", "cost": 280, "damage_bonus": 7},
        {"key": "legend", "name": "Legend Sword", "cost": 520, "damage_bonus": 12},
    ]

    BOSS_ROSTER = {
        "easy": [
            ("The Slacker",     80,  5,  "You haven't worked in days... I'm barely trying."),
            ("Brain Fog",       90,  5,  "Can't think clearly? Neither can you."),
            ("The Distraction", 100, 5,  "Look at this shiny thing instead of your tasks!"),
        ],
        "medium": [
            ("The Procrastinator", 200, 15, "You'll defeat me tomorrow, right? Maybe next week."),
            ("Doubt",              220, 15, "Are you sure you're good enough for this?"),
            ("Entropy",            250, 15, "Everything falls apart eventually. Including you."),
        ],
        "hard": [
            ("Lord Chaos",      500, 30, "Your discipline means nothing. I am inevitable."),
            ("The Void",        600, 30, "You cannot defeat what you cannot see."),
            ("The Final Exam",  700, 30, "Let's see what you're really made of."),
        ]
    }

    BOSS_REWARDS = {
        "easy":   {"gold": 70, "oxp": 60,  "attack": 12},
        "medium": {"gold": 170, "oxp": 150, "attack": 28},
        "hard":   {"gold": 420, "oxp": 360, "attack": 65},
    }

    def __init__(self, database):
        self.db = database

    # -------------------------------------------------------------------------
    # ACHIEVEMENT CHECKING
    # -------------------------------------------------------------------------

    def check_all_achievements(self, player=None, new_streak=None, task_difficulty=None):
        """
        Check all achievement conditions and unlock any newly met ones.
        Returns list of newly unlocked achievement titles.
        """
        if player is None:
            player = self.db.get_player()

        newly_unlocked = []

        def check(title, condition):
            if condition:
                cursor = self.db.conn.cursor()
                cursor.execute(
                    "SELECT unlocked FROM achievement WHERE title=?", (title,)
                )
                row = cursor.fetchone()
                if row and row[0] == 0:
                    self.db.unlock_achievement(title)
                    newly_unlocked.append(title)

        total_completed = self.db.get_total_tasks_completed()
        check("First Task",      total_completed >= 1)
        check("Getting Started", total_completed >= 10)
        check("Halfway There",   total_completed >= 50)
        check("Century",         total_completed >= 100)
        check("Hard Worker",     task_difficulty and task_difficulty.lower() == "hard")
        check("Triple Threat",   self.db.get_tasks_completed_today() >= 3)

        login_streak    = player.get("login_streak", 0)
        max_task_streak = self.db.get_max_task_streak()
        check("Consistent",       login_streak >= 3)
        check("Dedicated",        login_streak >= 30)
        check("7 Day Discipline", new_streak is not None and new_streak >= 7)
        check("Two Weeks Strong", max_task_streak >= 14)

        check("Rising",   player["level"] >= 5)
        check("Veteran",  player["level"] >= 10)
        check("Elite",    player["level"] >= 25)

        check("Gold Collector", player.get("total_gold_earned", 0) >= 500)
        check("Rich",           player.get("total_gold_earned", 0) >= 1000)
        check("Big Spender",    player.get("gold_spent", 0) >= 500)

        check("Mind Level 5",  self.db.get_skill("Mind")["level"] >= 5)
        check("Master",        self.db.get_max_skill_level() >= 10)
        check("Well Rounded",  self.db.get_skills_above_level(5) >= 3)
        check("Creator",       self.db.get_custom_skill_count() >= 1)

        bosses_defeated = self.db.get_bosses_defeated_count()
        check("Boss Slayer",  bosses_defeated >= 1)
        check("Boss Hunter",  bosses_defeated >= 3)

        return newly_unlocked

    # -------------------------------------------------------------------------
    # ATTACK DAMAGE
    # -------------------------------------------------------------------------

    def get_attack_damage(self, player=None):
        if player is None:
            player = self.db.get_player()
        strength = self.db.get_skill("Strength")
        return 8 + (strength["level"] - 1) * 2 + player.get("sword_bonus_damage", 0)

    def _apply_level_ups(self, player):
        level_events = []
        while True:
            required = 120 + (player["level"] - 1) * 65
            if player["oxp"] >= required:
                player["oxp"] -= required
                player["level"] += 1
                player["max_hp"] += self.HP_PER_LEVEL
                player["current_hp"] = player["max_hp"]
                player["attack_points"] += self.ATTACK_PER_LEVEL_UP
                level_events.append({
                    "new_level": player["level"],
                    "hp_gained": self.HP_PER_LEVEL,
                    "atk_gained": self.ATTACK_PER_LEVEL_UP,
                    "max_hp": player["max_hp"],
                })
            else:
                break
        return level_events

    def _process_quest_completion(self, task_id, player):
        quest_events = []
        level_events = []

        for quest in self.db.get_task_quests(task_id):
            if quest.get("status") != "Active":
                continue

            progress = self.db.get_quest_progress(quest["id"])
            if not progress or not progress["is_complete"]:
                continue

            self.db.complete_quest(quest["id"])

            player["gold"] += quest.get("gold_reward", 0)
            player["oxp"] += quest.get("oxp_reward", 0)
            player["attack_points"] += quest.get("attack_reward", 0)
            player["total_gold_earned"] = (
                player.get("total_gold_earned", 0) + quest.get("gold_reward", 0)
            )

            level_events.extend(self._apply_level_ups(player))
            quest["status"] = "Completed"
            quest["progress"] = progress
            quest_events.append(quest)

        return quest_events, level_events

    # -------------------------------------------------------------------------
    # BOSS SYSTEM
    # -------------------------------------------------------------------------

    def check_boss_spawn(self, player_level):
        if self.db.get_active_boss():
            return None
        if self.db.boss_already_spawned_for_level(player_level):
            return None

        tier = None
        if player_level % 50 == 0:
            tier = "hard"
        elif player_level % 25 == 0:
            tier = "medium"
        elif player_level % 10 == 0:
            tier = "easy"

        if tier is None:
            return None

        name, hp, atk_damage, taunt = random.choice(self.BOSS_ROSTER[tier])
        self.db.spawn_boss(name, tier, hp, atk_damage, player_level, taunt)
        return self.db.get_active_boss()

    def apply_passive_boss_damage(self):
        boss = self.db.get_active_boss()
        if not boss or not boss["date_spawned"]:
            return None

        today        = date.today()
        spawned_date = datetime.strptime(boss["date_spawned"], "%Y-%m-%d").date()
        days_ignored = (today - spawned_date).days

        if days_ignored < 1:
            return None

        player = self.db.get_player()
        damage = boss["attack_damage"] * days_ignored
        new_hp = max(1, player["current_hp"] - damage)
        player["current_hp"] = new_hp
        self.db.update_player(player)

        return {
            "boss_name":    boss["name"],
            "damage":       damage,
            "days":         days_ignored,
            "remaining_hp": new_hp
        }

    def attack_boss(self, boss_id):
        """
        One round of combat.
        Returns full result dict including any achievements unlocked on victory.
        """
        boss   = self.db.get_active_boss()
        player = self.db.get_player()

        if not boss or boss["id"] != boss_id:
            return None
        if player["attack_points"] <= 0:
            return None

        player["attack_points"] -= 1

        player_damage = self.get_attack_damage(player)
        new_boss_hp   = max(0, boss["hp"] - player_damage)
        self.db.update_boss_hp(boss_id, new_boss_hp)

        boss_damage   = boss["attack_damage"]
        new_player_hp = player["current_hp"] - boss_damage

        near_death          = False
        rewards             = None
        newly_unlocked      = []
        gold_penalty        = 0
        atk_penalty         = 0

        if new_player_hp <= 0:
            new_player_hp           = 1
            near_death              = True
            gold_penalty            = min(player["gold"], 50)
            atk_penalty             = min(player["attack_points"], 20)
            player["gold"]          = max(0, player["gold"] - gold_penalty)
            player["attack_points"] = max(0, player["attack_points"] - atk_penalty)
            self.db.unlock_achievement("Near Death")
            newly_unlocked.append("Near Death")

        player["current_hp"] = new_player_hp

        boss_defeated = new_boss_hp <= 0
        if boss_defeated:
            self.db.defeat_boss(boss_id)
            player["bosses_defeated"] = player.get("bosses_defeated", 0) + 1

            if boss["tier"] == "hard":
                self.db.unlock_achievement("Giant Killer")
                newly_unlocked.append("Giant Killer")

            tier_rewards                = self.BOSS_REWARDS[boss["tier"]]
            player["gold"]             += tier_rewards["gold"]
            player["oxp"]              += tier_rewards["oxp"]
            player["attack_points"]    += tier_rewards["attack"]
            player["total_gold_earned"] = player.get("total_gold_earned", 0) + tier_rewards["gold"]

            self.check_player_level_up(player)
            self.db.update_player(player)

            extra = self.check_all_achievements(player=self.db.get_player())
            newly_unlocked.extend(extra)
            rewards = tier_rewards
        else:
            self.db.update_player(player)

        return {
            "player_damage":     player_damage,
            "boss_damage":       boss_damage,
            "boss_hp":           new_boss_hp,
            "player_hp":         new_player_hp,
            "boss_defeated":     boss_defeated,
            "player_near_death": near_death,
            "gold_penalty":      gold_penalty,
            "atk_penalty":       atk_penalty,
            "rewards":           rewards,
            "attack_points":     player["attack_points"],
            "newly_unlocked":    newly_unlocked,
            "boss":              boss,
        }

    # -------------------------------------------------------------------------
    # TASK COMPLETION
    # -------------------------------------------------------------------------

    def complete_task(self, task_id):
        """
        Process task completion.

        Returns a rich dict containing every event that happened:
            - base rewards (oxp, gold, attack points)
            - skill_events: list of {name, old_level, new_level, xp_gained}
            - level_events: list of {old_level, new_level, hp_gained, atk_gained}
            - newly_unlocked: list of achievement titles
            - boss: boss dict if one spawned
            - streak: new streak value
            - task: task info for display
        """
        task   = self.db.get_task(task_id)
        player = self.db.get_player()

        if task["status"] == "Completed":
            return False

        # --- Base rewards ---
        gold_earned                 = task["gold"]
        oxp_earned                  = task["oxp"]
        player["gold"]             += gold_earned
        player["oxp"]              += oxp_earned
        player["total_gold_earned"] = player.get("total_gold_earned", 0) + gold_earned

        difficulty = task.get("difficulty", "Medium").lower()
        atk_earned = self.ATTACK_PER_DIFFICULTY.get(difficulty, 10)
        player["attack_points"] += atk_earned

        # --- Skill XP + track level ups ---
        skill_events = []
        rewards      = self.db.get_task_rewards(task_id)

        for reward in rewards:
            skill      = self.db.get_skill(reward["skill_name"])
            old_level  = skill["level"]
            skill["xp"] += reward["sxp"]
            self.check_skill_level_up(skill)
            new_level  = skill["level"]

            skill_events.append({
                "name":      skill["name"],
                "old_level": old_level,
                "new_level": new_level,
                "xp_gained": reward["sxp"],
                "leveled_up": new_level > old_level,
            })

            if skill["name"] == "Health" and new_level > old_level:
                levels_gained        = new_level - old_level
                player["max_hp"]    += self.HP_PER_HEALTH_LEVEL * levels_gained
                player["current_hp"] = min(
                    player["current_hp"] + self.HP_PER_HEALTH_LEVEL * levels_gained,
                    player["max_hp"]
                )

            self.db.update_skill(skill)

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

        if new_streak % 7 == 0:
            player["oxp"] += 50

        # --- Character level up + track events ---
        old_level    = player["level"]
        level_events = self._apply_level_ups(player)

        new_level = player["level"]

        # --- Save ---
        self.db.mark_task_completed(task_id)
        self.db.update_task_streak(task_id, new_streak)
        self.db.update_player(player)

        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO task_history(task_id, title, difficulty, date_completed)
            VALUES (?, ?, ?, ?)
        """, (task["id"], task["title"],
              task.get("difficulty", "Medium"), date.today().isoformat()))
        self.db.conn.commit()

        quest_events, quest_level_events = self._process_quest_completion(task_id, player)
        if quest_level_events:
            level_events.extend(quest_level_events)
        self.db.update_player(player)
        new_level = player["level"]

        # --- Achievements ---
        newly_unlocked = self.check_all_achievements(
            player=self.db.get_player(),
            new_streak=new_streak,
            task_difficulty=task.get("difficulty")
        )

        # --- Boss spawn ---
        spawned_boss = None
        if new_level > old_level:
            for lvl in range(old_level + 1, new_level + 1):
                spawned_boss = self.check_boss_spawn(lvl)
                if spawned_boss:
                    break

        return {
            # What was earned
            "oxp_earned":      oxp_earned,
            "gold_earned":     gold_earned,
            "atk_earned":      atk_earned,
            "streak":          new_streak,
            # Events
            "skill_events":    skill_events,
            "level_events":    level_events,
            "quest_events":    quest_events,
            "newly_unlocked":  newly_unlocked,
            "boss":            spawned_boss,
            # Task info for display
            "task_title":      task["title"],
            "task_difficulty": task.get("difficulty", "Medium"),
            "task_period":     task.get("period", "daily"),
        }

    # -------------------------------------------------------------------------
    # LOGIN REWARD
    # -------------------------------------------------------------------------

    def check_login_reward(self):
        player       = self.db.get_player()
        today        = date.today()
        today_str    = today.isoformat()
        last_login   = player.get("last_login")
        login_streak = player.get("login_streak", 0)

        if last_login == today_str:
            return None

        if last_login:
            last_date    = datetime.strptime(last_login, "%Y-%m-%d").date()
            diff         = (today - last_date).days
            login_streak = login_streak + 1 if diff == 1 else 1
        else:
            login_streak = 1

        gold, oxp = 8, 8
        bonus_atk = 3

        if login_streak >= 7:
            gold, oxp = 30, 35
            bonus_atk = 10
            bonus_msg = "7 Day Login Streak! MEGA reward!"
        elif login_streak >= 3:
            gold, oxp = 18, 20
            bonus_atk = 6
            bonus_msg = f"{login_streak} Day Streak! Bonus reward!"
        else:
            bonus_msg = f"Day {login_streak} streak. Keep it up!"

        hp_restored             = min(5, player["max_hp"] - player["current_hp"])
        player["current_hp"]   += hp_restored
        player["gold"]         += gold
        player["oxp"]          += oxp
        player["attack_points"] += bonus_atk
        player["total_gold_earned"] = player.get("total_gold_earned", 0) + gold

        self.check_player_level_up(player)
        self.db.update_player(player)
        self.db.update_login(today_str, login_streak)
        self.check_all_achievements(player=self.db.get_player())

        return {
            "gold": gold, "oxp": oxp, "streak": login_streak,
            "message": bonus_msg, "hp_restored": hp_restored, "bonus_atk": bonus_atk
        }

    # -------------------------------------------------------------------------
    # SHOP
    # -------------------------------------------------------------------------

    def buy_skill_boost(self, skill_name):
        player = self.db.get_player()
        skill  = self.db.get_skill(skill_name)

        if player["gold"] < 120:
            return False

        player["gold"]       -= 120
        player["gold_spent"]  = player.get("gold_spent", 0) + 120
        skill["xp"]          += 16

        old_level = skill["level"]
        self.check_skill_level_up(skill)

        skill_leveled_up = skill["level"] > old_level

        if skill["name"] == "Health" and skill_leveled_up:
            levels_gained        = skill["level"] - old_level
            player["max_hp"]    += self.HP_PER_HEALTH_LEVEL * levels_gained
            player["current_hp"] = min(
                player["current_hp"] + self.HP_PER_HEALTH_LEVEL * levels_gained,
                player["max_hp"]
            )

        self.db.update_skill(skill)
        self.db.update_player(player)
        self.db.commit()
        self.check_all_achievements(player=self.db.get_player())

        return {
            "success":       True,
            "skill_name":    skill["name"],
            "old_level":     old_level,
            "new_level":     skill["level"],
            "leveled_up":    skill_leveled_up,
        }

    def buy_armor(self, armor_key):
        player = self.db.get_player()
        armor = next((item for item in self.ARMOR_SHOP if item["key"] == armor_key), None)

        if armor is None:
            return {"success": False, "reason": "missing"}
        if player.get("armor_name") == armor["name"]:
            return {"success": False, "reason": "owned"}
        if armor["hp_bonus"] <= player.get("armor_bonus_hp", 0):
            return {"success": False, "reason": "downgrade"}
        if player["gold"] < armor["cost"]:
            return {"success": False, "reason": "gold"}

        hp_gain = armor["hp_bonus"] - player.get("armor_bonus_hp", 0)
        player["gold"] -= armor["cost"]
        player["gold_spent"] = player.get("gold_spent", 0) + armor["cost"]
        player["armor_name"] = armor["name"]
        player["armor_bonus_hp"] = armor["hp_bonus"]
        player["max_hp"] += hp_gain
        player["current_hp"] = min(player["current_hp"] + hp_gain, player["max_hp"])

        self.db.update_player(player)
        self.db.commit()
        self.check_all_achievements(player=self.db.get_player())

        return {
            "success": True,
            "item_type": "armor",
            "name": armor["name"],
            "cost": armor["cost"],
            "hp_gain": hp_gain,
            "max_hp": player["max_hp"],
        }

    def buy_sword(self, sword_key):
        player = self.db.get_player()
        sword = next((item for item in self.SWORD_SHOP if item["key"] == sword_key), None)

        if sword is None:
            return {"success": False, "reason": "missing"}
        if player.get("sword_name") == sword["name"]:
            return {"success": False, "reason": "owned"}
        if sword["damage_bonus"] <= player.get("sword_bonus_damage", 0):
            return {"success": False, "reason": "downgrade"}
        if player["gold"] < sword["cost"]:
            return {"success": False, "reason": "gold"}

        damage_gain = sword["damage_bonus"] - player.get("sword_bonus_damage", 0)
        player["gold"] -= sword["cost"]
        player["gold_spent"] = player.get("gold_spent", 0) + sword["cost"]
        player["sword_name"] = sword["name"]
        player["sword_bonus_damage"] = sword["damage_bonus"]

        self.db.update_player(player)
        self.db.commit()
        self.check_all_achievements(player=self.db.get_player())

        return {
            "success": True,
            "item_type": "sword",
            "name": sword["name"],
            "cost": sword["cost"],
            "damage_gain": damage_gain,
            "damage_per_hit": self.get_attack_damage(player),
        }

    # -------------------------------------------------------------------------
    # LEVEL UP
    # -------------------------------------------------------------------------

    def check_player_level_up(self, player):
        while True:
            required = 120 + (player["level"] - 1) * 65
            if player["oxp"] >= required:
                player["oxp"]           -= required
                player["level"]         += 1
                player["max_hp"]        += self.HP_PER_LEVEL
                player["current_hp"]     = player["max_hp"]
                player["attack_points"] += self.ATTACK_PER_LEVEL_UP
            else:
                break

    def check_skill_level_up(self, skill):
        while True:
            required = 50 + (skill["level"] - 1) * 25
            if skill["xp"] >= required:
                skill["xp"]    -= required
                skill["level"] += 1
            else:
                break
