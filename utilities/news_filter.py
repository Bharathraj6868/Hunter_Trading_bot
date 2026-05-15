from datetime import datetime, timedelta

class NewsFilter:
    def __init__(self, config):
        self.enabled = config['news']['enabled']
        self.before = config['news']['avoid_minutes_before']
        self.after = config['news']['avoid_minutes_after']
        self.calendar = []  # Implement your own API fetch

    def update(self):
        pass  # Fetch economic calendar

    def is_news_nearby(self, dt):
        if not self.enabled:
            return False
        # Compare with calendar
        return False