import sys
import os
import threading
import time
import json
from flask import Flask, render_template, jsonify

# Ensure the parent folder is in sys.path so we can import 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mt5_connector import MT5Connector
import yaml

app = Flask(__name__)

# Load config
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')
with open(config_path) as f:
    config = yaml.safe_load(f)

connector = MT5Connector(
    path=config['mt5'].get('path', ''),
    login=config['mt5']['login'],
    password=config['mt5']['password'],
    server=config['mt5']['server']
)
connector.connect()

# Global dictionary to hold latest data (updated in background thread)
latest_data = {
    'balance': 0,
    'equity': 0,
    'drawdown': 0,
    'positions': []
}

def background_fetcher():
    """Fetch account data every 1 second and update global dict."""
    global latest_data
    while True:
        try:
            acc = connector.get_account_info()
            if acc:
                latest_data['balance'] = acc.balance
                latest_data['equity'] = acc.equity
                latest_data['drawdown'] = (acc.balance - acc.equity) / acc.balance * 100 if acc.balance > 0 else 0
            positions = connector.get_positions()
            if positions:
                latest_data['positions'] = [
                    {
                        'ticket': p.ticket,
                        'symbol': p.symbol,
                        'type': 'BUY' if p.type == 0 else 'SELL',
                        'volume': p.volume,
                        'profit': p.profit
                    }
                    for p in positions if p.magic == 123456
                ]
            else:
                latest_data['positions'] = []
        except Exception as e:
            print(f"Dashboard fetch error: {e}")
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    return jsonify(latest_data)

if __name__ == '__main__':
    # Start background fetcher thread
    t = threading.Thread(target=background_fetcher, daemon=True)
    t.start()

    # Run Flask without eventlet – simple built-in server (OK for local monitoring)
    app.run(host=config['dashboard']['host'], port=config['dashboard']['port'], debug=False, threaded=True)