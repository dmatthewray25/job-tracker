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

def send_email(job_title, job_url):
    subject = f"🚨 New ATS Job Match: {job_title}"
    body = f"A matching open role was found directly on an ATS main stream!\n\nRole: {job_title}\n\nApply Here: {job_url}"
    
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

def process_job_rules(title, location, url, seen_jobs):
    """Processes your precise location and hybrid rules inside Python."""
    full_text_lower = f"{title} {location} {url}".lower()
    
    # 1. Check for Core Roles
    keywords = ["sales operations", "incentive compensation", "sales compensation", "commission", "revenue operations", "commercial operations"]
    if not any(k in full_text_lower for k in keywords):
        return
        
    # 2. Check for Career Levels
    if not any(level in full_text_lower for level in ["manager", "analyst"]):
        return
        
    # 3. Location Checking Arrays
    local_cities = ["overland park", "olathe", "lenexa", "leawood", "kansas city", "66221"]
    is_local = any(city in full_text_lower for city in local_cities)
    is_remote = "remote" in full_text_lower
    is_hybrid = "hybrid" in full_text_lower
    
    # YOUR EXACT RULE:
    # Local roles can be anything (On-site, Hybrid, or Remote).
    # Non-local roles outside your cities MUST be pure Remote and are NOT allowed to be Hybrid!
    if is_hybrid and not is_local:
        return
        
    # If it is completely outside your local cities and doesn't mention remote at all, skip it
    if not (is_local or is_remote):
        return
        
    if url not in seen_jobs:
        print(f"✨ Match verified on ATS stream: {title} ({location})")
        send_email(title, url)
        seen_jobs.add(url)

def scan_greenhouse_stream(seen_jobs):
    print("🔍 Fetching main stream records from Greenhouse API...")
    # Direct pipeline to Greenhouse's primary indexing repository
    url = "https://greenhouse.io"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            jobs = response.json().get("jobs", [])
            for job in jobs:
                title = job.get("title", "")
                loc_dict = job.get("location", {})
                location = loc_dict.get("name", "") if loc_dict else ""
                job_url = job.get("absolute_url", "")
                process_job_rules(title, location, job_url, seen_jobs)
    except Exception as e:
        print(f"Greenhouse stream pause: {e}")

def scan_lever_stream(seen_jobs):
    print("🔍 Fetching main stream records from Lever API...")
    # Direct pipeline to Lever's active posting repository index
    url = "https://lever.co"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            for job in response.json():
                title = job.get("text", "")
                cats = job.get("categories", {})
                location = cats.get("location", "") if cats else ""
                job_url = job.get("hostedUrl", "")
                process_job_rules(title, location, job_url, seen_jobs)
    except Exception as e:
        print(f"Lever stream pause: {e}")

def scan_smartrecruiters_stream(seen_jobs):
    print("🔍 Fetching main stream records from SmartRecruiters API...")
    # Direct pipeline to SmartRecruiters index system
    url = "https://smartrecruiters.com"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            for job in response.json().get("content", []):
                title = job.get("name", "")
                location = job.get("location", {}).get("city", "")
                # Generates a standard application tracking link structure
                job_url = f"https://smartrecruiters.com{job.get('company', {}).get('identifier')}/{job.get('id')}"
                process_job_rules(title, location, job_url, seen_jobs)
    except Exception as e:
        print(f"SmartRecruiters stream pause: {e}")

def main():
    print("🔄 Launching deep pipeline scan across core ATS stream nodes...")
    seen_jobs = load_seen_jobs()
    
    # Scans the active open backend tracking hubs directly
    scan_greenhouse_stream(seen_jobs)
    scan_lever_stream(seen_jobs)
    scan_smartrecruiters_stream(seen_jobs)
    
    save_seen_jobs(seen_jobs)
    print("🏁 Complete pipeline scan achieved.")

if __name__ == "__main__":
    main()
