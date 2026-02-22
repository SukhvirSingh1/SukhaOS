# xp, levels, rewards logic for SukhaOS application

class GameEngine:
    def __init__(self, database):
        self.db = database
    def complete_task(self, task_id):   
        task = self.db.get_task(task_id)
        player = self.db.get_player()
        
        if task["status"] == "Completed":
            return  # Task already completed
    
        
        player["gold"] += task["gold"]
        player["oxp"] += task["oxp"]
        
        rewards = self.db.get_task_rewards(task_id) 
        for reward in rewards:
            skill = self.db.get_skill(reward["skill_name"])
            skill["xp"] += reward["sxp"]
            self.check_skill_level_up(skill)
            
            
        self.check_player_level_up(player)
        self.db.mark_task_completed(task_id)
        self.db.update_player(player)
        self.db.commit()
        
    def check_player_level_up(self, player):
        while True:
            required = 100 + (player["level"] - 1) * 50
            if player["oxp"] >= required:
                player["oxp"] -= required
                player["level"] += 1
            else:
                break
            print(f"Player leveled up! New level: {player['level']}, OXP: {player['oxp']}")
    
    def check_skill_level_up(self, skill):
        while True:
            required = 50 + (skill["level"] - 1) * 25
            
            if skill["xp"] >= required:
                skill["xp"] -= required
                skill["level"] += 1
            else:
                break
            print(f"Skill {skill['name']} leveled up! New level: {skill['level']}, XP: {skill['xp']}")