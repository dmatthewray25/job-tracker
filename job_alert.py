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

def scan_ats_platform(platform_domain, titles_query, locations_query, seen_jobs):
    search_query = f"site:{platform_domain} {titles_query} {locations_query}"
    encoded_query = urllib.parse.quote_plus(search_query)
    url = f"https://duckduckgo.com{encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200: 
            print(f"⚠️ Limit hit for: {platform_domain}")
            return
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.find_all('a', class_='result__url')
        print(f"🔍 Checking {platform_domain}... Parsing {len(results)} layout elements.")
        
        for r in results:
            link = r.get('href', '')
            if 'uddg=' in link:
                # FIXED: Rewrote path extraction loop to prevent hidden code crashes
                parts = link.split('uddg=')
                if len(parts) > 1:
                    real_url = parts[1].split('&')[0]
                    link = urllib.parse.unquote(real_url)
                
            title_box = r.find_parent('div', class_='result__body')
            if not title_box:
                title_box = r.find_parent('div', class_='links_main')
                
            title = "Open ATS Position"
            if title_box:
                title_elem = title_box.find('a', class_='result__title')
                if title_elem:
                    title = title_elem.text.strip()
            
            if link and link.startswith('http') and link not in seen_jobs:
                print(f"✨ Match found on {platform_domain}: {title}")
                send_email(title, link)
                seen_jobs.add(link)
    except Exception as e:
        print(f"Error checking platform {platform_domain}: {e}")

def main():
    print("🔄 Starting universal web-wide unblockable scan...")
    seen_jobs = load_seen_jobs()
    
    titles = '("Sales Operations" OR "Incentive Compensation" OR "Sales Compensation" OR "Revenue Operations" OR "Commercial Operations" OR "Commission" OR "Sales Incentive" OR "SIP") ("Manager" OR "Analyst")'
    locations = '("66221" OR "Overland Park" OR "Olathe" OR "Leawood" OR "Lenexa" OR "Kansas City" OR "remote")'
    
    ats_platforms = [
        "boards.greenhouse.io", "jobs.lever.co", "://smartrecruiters.com", 
        "ashbyhq.com", "myworkdayjobs.com", "icims.com", "://workable.com", 
        "://bamboohr.com", "breezy.hr", "recruitee.com", "teamtailor.com", 
        "jazzhr.com", "jobvite.com", "://rippling.com", "paylocity.com", 
        "oraclecloud.com", "://jobadder.com", "manatal.com", "jobdiva.com"
    ]
    
    for platform in ats_platforms:
        scan_ats_platform(platform, titles, locations, seen_jobs)
        
    save_seen_jobs(seen_jobs)
    print("🏁 Complete tracking run achieved.")

if __name__ == "__main__":
    main()
