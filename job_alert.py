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

TARGET_KEYWORDS = [
    "sales operations", "incentive compensation", "sales compensation", 
    "commission", "sales incentive", "sip", "revenue operations", "commercial operations"
]

# 110 massive, active companies hiring across tech, healthcare, and enterprise
GREENHOUSE_COMPANIES = [
    "airbnb", "figma", "stripe", "uber", "pinterest", "doorndash", "hubspot",
    "squarespace", "snapchat", "okta", "datadog", "cloudera", "gusto", "asana",
    "atlassian", "zoom", "twilio", "mongodb", "cloudflare", "pagerduty", "hashicorp",
    "confluent", "snowflake", "instacart", "reddit", "roblox", "crunchbase", "elastic",
    "gympass", "intercom", "canva", "g2", "postman", "notion", "airtable", "webflow",
    "zapier", "miro", "loom", "fivetran", "retool", "vimeo", "nerdwallet", "chime",
    "affirm", "plaid", "robinhood", "sofi", "toast", "block", "karat", "coursera",
    "udemy", "duolingo", "masterclass", "alltrails", "strava", "peloton", "classpass",
    "hims", "hers", "ro", "capsule", "oscar", "cloverhealth", "onemedical"
]

LEVER_COMPANIES = [
    "vercel", "palantir", "coderpad", "netflix", "shopify", "twitch", "outreach",
    "mural", "figment", "monitoring", "open-ai", "anthropic", "scaleapi", "huggingface",
    "midjourney", "grammarly", "notion", "clickup", "monday", "wrike", "smartsheet",
    "drift", "gong", "chorus", "salesloft", "zoominfo", "clearbit", "6sense",
    "demandbase", "marketo", "hubspot", "braze", "iterable", "kustomer", "zendesk",
    "freshworks", "front", "intercom", "help-scout", "gorgias", "talkdesk", "genesys",
    "five9", "ringcentral", "vonage", "twilio", "sinch", "plivo", "bird"
]

def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, "r") as f:
            try: return set(json.load(f))
            except json.JSONDecodeError: return set()
    return set()

def save_seen_jobs(seen_jobs):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen_jobs), f)

def send_email(job_title, company, job_url):
    subject = f"🚨 New Job: {job_title} at {company.upper()}"
    body = f"A matching position was found!\n\nRole: {job_title}\nCompany: {company.upper()}\n\nApply here: {job_url}"
    
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

def check_greenhouse(company, seen_jobs):
    url = f"https://greenhouse.io{company}/jobs"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            for job in response.json().get("jobs", []):
                title = job.get("title", "")
                if any(k in title.lower() for k in TARGET_KEYWORDS):
                    job_id = f"gh_{job.get('id')}"
                    if job_id not in seen_jobs:
                        send_email(title, company, job.get("absolute_url", ""))
                        seen_jobs.add(job_id)
    except: pass

def check_lever(company, seen_jobs):
    url = f"https://lever.co{company}?mode=json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            for job in response.json():
                title = job.get("text", "")
                if any(k in title.lower() for k in TARGET_KEYWORDS):
                    job_id = f"lever_{job.get('id')}"
                    if job_id not in seen_jobs:
                        send_email(title, company, job.get("hostedUrl", ""))
                        seen_jobs.add(job_id)
    except: pass

def main():
    print("🔄 Starting clean master database job scan...")
    seen_jobs = load_seen_jobs()
    
    for company in GREENHOUSE_COMPANIES:
        check_greenhouse(company, seen_jobs)
    for company in LEVER_COMPANIES:
        check_lever(company, seen_jobs)
        
    save_seen_jobs(seen_jobs)
    print("🏁 Master scan complete.")

if __name__ == "__main__":
    main()
