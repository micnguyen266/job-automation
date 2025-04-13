import os
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Load environment variables ---
load_dotenv()
USERNAME = os.getenv("LINKEDIN_USERNAME")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# --- Google Sheets Logging ---
def log_job_to_sheet(company, title, location, url, status="Applied"):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Job Tracker").sheet1
    sheet.append_row([datetime.today().strftime('%Y-%m-%d'), company, title, location, url, status])

# --- Job Application Logic ---
def apply_to_jobs(max_apps=5):
    driver = webdriver.Chrome()
    driver.get("https://www.linkedin.com/login")

    # Log in
    driver.find_element(By.ID, 'username').send_keys(USERNAME)
    driver.find_element(By.ID, 'password').send_keys(PASSWORD)
    driver.find_element(By.ID, 'password').send_keys(Keys.RETURN)
    time.sleep(5)

    # Job search URL for SRE + Easy Apply
    search_url = "https://www.linkedin.com/jobs/search/?keywords=site%20reliability%20engineer&f_AL=true"
    driver.get(search_url)
    time.sleep(5)

    jobs = driver.find_elements(By.CLASS_NAME, "job-card-container--clickable")
    applications_sent = 0

    for job in jobs:
        if applications_sent >= max_apps:
            print("Reached application limit.")
            break

        try:
            job.click()
            time.sleep(2)

            title = driver.find_element(By.CLASS_NAME, "topcard__title").text
            if "site reliability" in title.lower() or "sre" in title.lower():
                print(f"Found SRE job: {title}")

                apply_btn = driver.find_element(By.CLASS_NAME, "jobs-apply-button")
                apply_btn.click()
                time.sleep(2)

                submit_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']")
                submit_btn.click()
                time.sleep(2)

                log_job_to_sheet(
                    company=driver.find_element(By.CLASS_NAME, "topcard__flavor").text,
                    title=title,
                    location=driver.find_element(By.CLASS_NAME, "topcard__flavor--bullet").text,
                    url=driver.current_url,
                    status="Applied"
                )

                applications_sent += 1
                print(f"Applied and logged ({applications_sent}/{max_apps})")

        except Exception as e:
            print(f"Skipped a job due to error: {e}")
            continue

    driver.quit()
    print("Done!")

# --- Entry Point ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LinkedIn Job Applier Script")
    parser.add_argument("--apply", type=int, default=5, help="Number of jobs to apply to")
    args = parser.parse_args()

    apply_to_jobs(max_apps=args.apply)