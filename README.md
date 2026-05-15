# Institutional AI Trading Bot

1. Install Python 3.10+ & MT5.
2. pip install -r requirements.txt
3. Edit config/config.yaml with your MT5 credentials.
4. Create .env file (optional) for sensitive data.
5. Run `python init_db.py` once.
6. Start bot: `python main.py`
7. (Optional) Dashboard: `python dashboard/app.py`

The bot will learn from its trades and improve over time. Check logs/bot.log.