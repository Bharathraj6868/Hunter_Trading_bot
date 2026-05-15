import requests

class AlertManager:
    def __init__(self, config):
        self.tg_token = config['telegram']['token']
        self.tg_chat = config['telegram']['chat_id']
        self.discord = config['discord']['webhook_url']
        self.tg_enabled = config['telegram']['enabled']
        self.discord_enabled = config['discord']['enabled']

    def send(self, msg):
        if self.tg_enabled:
            url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
            try:
                requests.post(url, data={"chat_id": self.tg_chat, "text": msg})
            except: pass
        if self.discord_enabled and self.discord:
            try:
                requests.post(self.discord, json={"content": msg})
            except: pass