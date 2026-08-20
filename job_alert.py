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

def scan_ats_platform(platform_domain, title, location, seen_jobs):
    """Scans clean, bite-sized queries to prevent parsing crashes."""
    search_query = f"site:{platform_domain} \"{title}\" \"{location}\""
    encoded_query = urllib.parse.quote_plus(search_query)
    
    # Standard clean search directory path structure
    url = f"https://duckduckgo.com{encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code != 200: 
            return
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.find_all('a', class_='result__url')
        
        for r in results:
            link = r.get('href', '')
            if 'uddg=' in link:
                parts = link.split('uddg=')
                if len(parts) > 1:
                    real_url = parts[1].split('&')[0]
                    link = urllib.parse.unquote(real_url)
                
            title_box = r.find_parent('div', class_='result__body')
            if not title_box:
                title_box = r.find_parent('div', class_='links_main')
                
            title_text = "Open ATS Position"
            if title_box:
                title_elem = title_box.find('a', class_='result__title')
                if title_elem:
                    title_text = title_elem.text.strip()
            
            if link and link.startswith('http') and link not in seen_jobs:
                print(f"✨ Match found on {platform_domain}: {title_text}")
                send_email(title_text, link)
                seen_jobs.add(link)
    except:
        pass

def main():
    print("🔄 Starting fresh structured universal ATS scan...")
    seen_jobs = load_seen_jobs()
    
    # Core target title components broken up cleanly
    titles = ["Sales Operations", "Incentive Compensation", "Sales Compensation", "Revenue Operations"]
    locations = ["Overland Park", "Olathe", "Lenexa", "Kansas City", "Remote"]
    
    ats_platforms = [
        "boards.greenhouse.io", "jobs.lever.co", "://smartrecruiters.com", 
        "ashbyhq.com", "myworkdayjobs.com", "icims.com", "://workable.com"
    ]
    
    # Loop combinations to keep queries short and fully unblockable
    for platform in ats_platforms:
        print(f"🔍 Crawling tracking platform: {platform}")
        for title in titles:
            for location in locations:
                scan_ats_platform(platform, title, location, seen_jobs)
        
    save_seen_jobs(seen_jobs)
    print("🏁 Complete tracking run achieved.")

if __name__ == "__main__":
    main()
