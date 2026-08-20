import os
import json
import smtplib
from googlesearch import search
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
    print("🔄 Starting universal unblockable search engine scan...")
    seen_jobs = load_seen_jobs()
    
    # Your core titles and location queries
    query = '("Sales Operations" OR "Incentive Compensation" OR "Sales Compensation" OR "Revenue Operations" OR "Commercial Operations") ("Manager" OR "Analyst") (Overland Park OR Olathe OR Lenexa OR Leawood OR Kansas City OR Remote)'
    
    local_cities = ["overland park", "olathe", "lenexa", "leawood", "kansas city"]
    
    print(f"🔍 Searching for matching active job links across the web...")
    
    try:
        # Bypasses the blocks by using the native search framework to pull 100 links
        for url in search(query, num_results=100):
            url_lower = url.lower()
            
            # Skips pages that aren't real job descriptions
            if not any(x in url_lower for x in ["job", "post", "career", "board", "detail"]):
                continue
                
            is_local = any(city in url_lower for city in local_cities)
            is_hybrid = "hybrid" in url_lower
            
            # YOUR EXACT RULE: If it's hybrid but NOT in your local cities, skip it completely!
            if is_hybrid and not is_local:
                continue
                
            if url not in seen_jobs:
                # Creates a clean title from the website address snippet
                clean_title = url.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
                if not clean_title or len(clean_title) < 5:
                    clean_title = "Active Ops Position Match"
                    
                print(f"✨ Match found: {clean_title}")
                send_email(clean_title, url)
                seen_jobs.add(url)
    except Exception as e:
        print(f"❌ Search tool failed: {e}")
        
    save_seen_jobs(seen_jobs)
    print("🏁 Tracking run complete.")

if __name__ == "__main__":
    main()
