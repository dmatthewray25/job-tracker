import os
import json
import smtplib
import urllib.parse
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText

# ==================== SETTINGS ====================
SENDER_EMAIL = "dmatthewray@gmail.com"
RECEIVER_EMAIL = "dmatthewray@gmail.com"
EMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD") 
# ==================================================

SEEN_JOBS_FILE = "seen_jobs_final.json"

def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, "r") as f:
            try: return set(json.load(f))
            except json.JSONDecodeError: return set()
    return set()

def save_seen_jobs(seen_jobs):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen_jobs), f)

def send_email(job_title, job_url):
    subject = f"🚨 New ATS Job Match: {job_title}"
    body = f"A matching open role was found!\n\nRole: {job_title}\n\nView Post: {job_url}"
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP_SSL("://gmail.com", 465) as server:
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print(f"📧 Email sent for: {job_title}")
    except Exception as e:
        print(f"❌ Email failed: {e}")

def main():
    print("🔄 Starting bulletproof live feed job scan...")
    seen_jobs = load_seen_jobs()
    
    # Clean target terms 
    keywords = ["sales operations", "incentive compensation", "sales compensation", "commission", "revenue operations", "commercial operations"]
    local_cities = ["overland park", "olathe", "lenexa", "leawood", "kansas city", "66221"]
    
    # Uses a clean, open RSS job database aggregator query string
    search_query = "Sales Operations Manager Analyst"
    encoded_query = urllib.parse.quote_plus(search_query)
    url = f"https://upwork.com{encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"⚠️ Feed access paused by server code: {response.status_code}")
            return
            
        soup = BeautifulSoup(response.text, "xml")
        items = soup.find_all("item")
        print(f"🔍 Reading active live data index stream... Processing {len(items)} listings.")
        
        for item in items:
            title = item.find("title").text if item.find("title") else "Open Position"
            link = item.find("link").text if item.find("link") else ""
            description = item.find("description").text if item.find("description") else ""
            
            full_text_lower = f"{title} {description}".lower()
            
            # --- CRITERIA MATCHING PIPELINE ---
            # 1. Title Term Verification
            if not any(k in full_text_lower for k in keywords):
                continue
                
            # 2. Level Verification
            if not any(level in full_text_lower for level in ["manager", "analyst"]):
                continue
                
            # 3. Location and Hybrid Rules Check
            is_local = any(city in full_text_lower for city in local_cities)
            is_remote = "remote" in full_text_lower
            is_hybrid = "hybrid" in full_text_lower
            
            # YOUR EXACT RULE: Hybrid is totally fine if local, but strictly banned if it's outside your area!
            if is_hybrid and not is_local:
                continue
                
            if not (is_local or is_remote):
                continue
                
            if link and link not in seen_jobs:
                print(f"✨ Match verified on feed: {title}")
                send_email(title, link)
                seen_jobs.add(link)
                
    except Exception as e:
        print(f"❌ System error during live feed parse: {e}")
        
    save_seen_jobs(seen_jobs)
    print("🏁 Tracking run complete.")

if __name__ == "__main__":
    main()
