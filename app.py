import os
from flask import Flask, request, send_file, redirect
import requests
from datetime import datetime
import io
import json
import socket

app = Flask(__name__)

# --- CONFIGURATION (Sirf Discord aur AbuseIPDB) ---
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
ABUSEIPDB_KEY = os.environ.get('ABUSEIPDB_KEY')

# 1x1 pixel ki transparent GIF image
PIXEL_BYTES = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'

# --- Main Logging Route ---
@app.route('/assets/tracker.gif')
def track():
    # --- Desktop Redirect Hata Diya Gaya Hai ---
    
    # Step 1: Data Capture (Optimized)
    raw_ip_list = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip_address = raw_ip_list.split(',')[0].strip()
    
    username = request.args.get('username', 'Guest')
    avatar_url = request.args.get('avatar', '')
    user_message = request.args.get('message', 'N/A')
    visitor_type = "Returning ♻️" if request.args.get('isNew') == 'false' else "New ✨"
    
    screen_res, os_type, browser, is_touch, timezone, languages, ad_blocker, canvas_hash, referrer = [request.args.get(k, 'N/A') for k in ['screen', 'os', 'browser', 'touch', 'timezone', 'langs', 'adBlock', 'canvas']] + [request.headers.get('Referer', 'Direct Visit')]
    is_touch = 'Yes' if is_touch == 'true' else 'No'
    ad_blocker_status = 'Detected 🛡️' if ad_blocker == 'true' else 'Not Detected 🟢'
    
    # Step 2: Deep IP Intelligence
    geo_info, asn_info, hostname, threat_level, risk_color, abuse_score = "N/A", "N/A", "N/A", "Low ✅", 3066993, 0
    try:
        response_geo = requests.get(f"http://ip-api.com/json/{ip_address}?fields=status,message,country,countryCode,city,isp,as,query", timeout=5)
        if response_geo.status_code == 200 and response_geo.json().get('status') == 'success':
            data = response_geo.json()
            city, country_code, isp, asn_str = data.get('city', 'N/A'), data.get('countryCode', 'N/A'), data.get('isp', 'N/A'), data.get('as', 'N/A')
            flag_emoji = "".join(chr(ord(c.upper()) + 127397) for c in country_code) if country_code and country_code != 'N/A' else ""
            geo_info = f"{flag_emoji} {city}, {country_code}"
            asn_info = f"{isp}\n({asn_str.split(' ')[0]})"
            if any(word in asn_info.lower() for word in ['vpn', 'proxy', 'hosting', 'datacenter']):
                threat_level, risk_color = "Medium 🟨 (VPN/Proxy Host)", 15844367
    except Exception as e: print(f"ERROR ip-api: {e}")
    try: hostname = socket.gethostbyaddr(ip_address)[0]
    except Exception: hostname = "Not Found"
    if ABUSEIPDB_KEY:
        try:
            response_abuse = requests.get(f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip_address}", headers={'Key': ABUSEIPDB_KEY, 'Accept': 'application/json'}, timeout=5)
            if response_abuse.status_code == 200:
                data = response_abuse.json()['data']
                abuse_score = data.get('abuseConfidenceScore', 0)
                if data.get('isTor'): threat_level, risk_color = "Critical 🚨 (Tor Exit Node)", 15158332
                elif abuse_score > 75: threat_level, risk_color = f"High 🟥 ({abuse_score}% Abuse Score)", 15158332
                elif abuse_score > 25 and risk_color != 15158332: threat_level, risk_color = f"Medium 🟨 ({abuse_score}% Abuse Score)", 15844367
        except Exception as e: print(f"ERROR AbuseIPDB: {e}")
    else: abuse_score = "API Key Missing"

    # Step 3: Prepare Discord Embed
    discord_embed = {
        "author": { "name": f"Holland Intel Report: {visitor_type} Visitor", "icon_url": "https://i.imgur.com/M6yB8oA.png" },
        "description": f"**Subject:** `{username}`\n**IP Address:** `{ip_address}`\n**Threat Assessment:** **{threat_level}**",
        "color": risk_color, "thumbnail": { "url": avatar_url },
        "fields": [
            { "name": "📍 Location", "value": f"`{geo_info}`", "inline": True },
            { "name": "🏢 Network Operator", "value": f"`{asn_info}`", "inline": True },
            { "name": "🛡️ Abuse Score", "value": f"`{abuse_score}%`", "inline": True },
            { "name": "💻 Client Profile", "value": f"**OS:** `{os_type}`\n**Browser:** `{browser}`\n**Screen:** `{screen_res}`", "inline": True },
            { "name": "🕵️‍♂️ Fingerprint", "value": f"**Languages:** `{languages}`\n**Timezone:** `{timezone}`\n**Touch:** `{is_touch}`", "inline": True },
            { "name": "💬 User Message", "value": f"> {user_message}" if user_message != 'N/A' else "> No message left.", "inline": False },
        ],
        "footer": { "text": f"Canvas: {canvas_hash} | AdBlocker: {ad_blocker_status}" }
    }

    # Step 4: Send Notification
    if DISCORD_WEBHOOK_URL:
        try:
            requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [discord_embed]}, timeout=10)
        except Exception as e:
            print(f"ERROR (Discord): {e}")

    return send_file(io.BytesIO(PIXEL_BYTES), mimetype='image/gif')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)