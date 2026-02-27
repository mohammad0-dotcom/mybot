from flask import Flask, render_template, jsonify, request
import psutil
import time
import os
from bot.config import WEB_SECRET_TOKEN

app = Flask(__name__)

bot_stats = {
    'start_time': time.time(),
    'users': 0,
    'groups': 0,
    'games': 0
}

@app.route('/')
def home():
    token = request.args.get('token')
    if token != WEB_SECRET_TOKEN:
        return "🔒 دسترسی غیرمجاز!", 403
    
    uptime = time.time() - bot_stats['start_time']
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    
    return render_template('index.html',
        uptime=f"{hours}h {minutes}m",
        users=bot_stats['users'],
        groups=bot_stats['groups'],
        games=bot_stats['games'],
        cpu=psutil.cpu_percent(),
        memory=psutil.virtual_memory().percent
    )

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'time': time.time()})

@app.route('/stats')
def stats():
    token = request.args.get('token')
    if token != WEB_SECRET_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify(bot_stats)

def start_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
