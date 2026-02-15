class Skill:
    def __init__(self, name, hour=0, streak=0, level=1,xp=0):
        self.name = name
        self.hour = hour
        self.streak = streak
        self.level = level
        self.xp = xp
        
    def add_hours(self, hours):
        self.hour += hours
        self.xp = hours*10
        self.check_level_up()
        
    def check_level(self):
        xp_needed = self.level * 100
        while self.xp >= xp_needed:
            self.xp -= xp_needed
            self.level += 1
            xp_needed = self.level * 100
        
    