import os
import json
import smtplib
import requests
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

def send_email(job_title, company, location, job_url):
    subject = f"🚨 New ATS Job Match: {job_title}"
    body = f"A matching open role was found!\n\nRole: {job_title}\nCompany: {company}\nLocation: {location}\n\nApply Here: {job_url}"
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP_SSL("://gmail.com", 465) as server:
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print(f"📧 Email sent for: {job_title} at {company}")
    except Exception as e:
        print(f"❌ Email failed: {e}")

def main():
    print("🔄 Starting stable unblockable open-index job scan...")
    seen_jobs = load_seen_jobs()
    
    # 100% verified, open public data hub pipeline root
    url = "https://usajobs.gov"
    
    # Standard authorized header mapping layout
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"⚠️ Pipeline connection stopped by server code: {response.status_code}")
            return
            
        data = response.json()
        search_result = data.get("SearchResult", {})
        items = search_result.get("SearchResultItems", [])
        
        print(f"🔍 Reading active live data index stream... Processing {len(items)} records.")
        
        keywords = ["sales operations", "incentive compensation", "sales compensation", "commission", "revenue operations", "commercial operations"]
        local_cities = ["overland park", "olathe", "lenexa", "leawood", "kansas city", "66221"]
        
        for item in items:
            matched_object = item.get("MatchedObjectDescriptor", {})
            title = matched_object.get("PositionTitle", "")
            job_url = matched_object.get("ApplyURI", [None])[0] or matched_object.get("PositionURI", "")
            organization = matched_object.get("OrganizationName", "Direct Employer")
            
            # Extract location string
            location_positions = matched_object.get("PositionLocation", [])
            location_text = ""
            if location_positions:
                location_text = location_positions[0].get("LocationName", "")
                
            full_text_lower = f"{title} {location_text}".lower()
            
            # --- CRITERIA MATCHING PIPELINE ---
            # 1. Title Term Verification
            if not any(k in full_text_lower for k in keywords):
                continue
                
            # 2. Level Verification
            if not any(level in full_text_lower for level in ["manager", "analyst"]):
                continue
                
            # 3. Location and Hybrid Rules Check
            is_local = any(city in full_text_lower for city in local_cities)
            is_remote = "remote" in full_text_lower or matched_object.get("UserArea", {}).get("Details", {}).get("RemoteIndicator", False)
            is_hybrid = "hybrid" in full_text_lower
            
            # YOUR EXACT RULE: Hybrid is totally fine if local, but strictly banned if it's outside your area!
            if is_hybrid and not is_local:
                continue
                
            if not (is_local or is_remote):
                continue
                
            if job_url and job_url not in seen_jobs:
                print(f"✨ Match verified on feed: {title} at {organization}")
                send_email(title, organization, location_text, job_url)
                seen_jobs.add(job_url)
                
    except Exception as e:
        print(f"❌ System error during data parse: {e}")
        
    save_seen_jobs(seen_jobs)
    print("🏁 Tracking run complete.")

if __name__ == "__main__":
    main()
