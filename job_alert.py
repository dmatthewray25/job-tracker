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

def scan_ats_platform(platform_domain, seen_jobs):
    search_query = f"site:{platform_domain} (Sales Operations OR Incentive Compensation OR Revenue Operations OR Commercial Operations) (Manager OR Analyst) (Overland Park OR Olathe OR Lenexa OR Leawood OR Kansas City OR Remote)"
    encoded_query = urllib.parse.quote_plus(search_query)
    url = f"https://duckduckgo.com{encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200: 
            return
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.find_all('a', class_='result__url')
        
        for r in results:
            raw_link = r.get('href', '')
            
            parsed_url = urllib.parse.urlparse(raw_link)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            if 'uddg' in query_params:
                link = query_params['uddg']
            else:
                link = raw_link
                
            title_box = r.find_parent('div', class_='result__body')
            if not title_box:
                title_box = r.find_parent('div', class_='links_main')
                
            title_text = "Open ATS Position"
            snippet_text = ""
            if title_box:
                title_elem = title_box.find('a', class_='result__title')
                if title_elem:
                    title_text = title_elem.text.strip()
                snippet_elem = title_box.find('a', class_='result__snippet')
                if snippet_elem:
                    snippet_text = snippet_elem.text.strip()
            
            # Combine all texts to search for locations and terms
            full_text_lower = (title_text + " " + snippet_text + " " + str(link)).lower()
            
            local_cities = ["overland park", "olathe", "lenexa", "leawood", "kansas city"]
            is_local_role = any(city in full_text_lower for city in local_cities)
            has_hybrid_word = "hybrid" in full_text_lower
            
            # FIXED LOGIC: If it's a hybrid role but NOT in your local cities, skip it!
            if has_hybrid_word and not is_local_role:
                continue
            
            if link and link.startswith('http') and link not in seen_jobs:
                print(f"✨ Match found on {platform_domain}: {title_text}")
                send_email(title_text, link)
                seen_jobs.add(link)
    except Exception as e:
        print(f"Error checking platform {platform_domain}: {e}")

def main():
    print("🔄 Starting universal non-hybrid ATS scan...")
    seen_jobs = load_seen_jobs()
    
    ats_platforms = [
        "boards.greenhouse.io", "jobs.lever.co", "://smartrecruiters.com", 
        "ashbyhq.com", "myworkdayjobs.com", "icims.com", "://workable.com",
        "://bamboohr.com", "breezy.hr", "recruitee.com", "teamtailor.com", 
        "jazzhr.com", "jobvite.com", "://rippling.com", "paylocity.com", 
        "oraclecloud.com", "://jobadder.com", "manatal.com", "jobdiva.com"
    ]
    
    for platform in ats_platforms:
        scan_ats_platform(platform, seen_jobs)
        
    save_seen_jobs(seen_jobs)
    print("🏁 Complete tracking run achieved.")

if __name__ == "__main__":
    main()
