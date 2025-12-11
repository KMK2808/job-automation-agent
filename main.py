import os
import time
from datetime import datetime

import pandas as pd

from generate_email import generate_email
from send_email import send_email

# --------- settings ---------

DRY_RUN = False          # set to False to actually send emails
DAILY_LIMIT = 10000        # max emails to send in one run
LOG_PATH = "sent_log.csv"


def main():
    # Load recruiters list [file:33]
    df = pd.read_csv("recruiters1.csv")

    # Basic cleaning
    df = df.dropna(subset=["Email"])
    df = df[df["Email"].str.contains("@")]

    # Optional: filter by role keywords
    df = df[df["Role"].str.contains("Power BI|Data|Analyst|Engineer",
                                    case=False, na=False)]

    # Load existing log if present
    sent_emails = set()
    if os.path.exists(LOG_PATH):
        log_df = pd.read_csv(LOG_PATH)
        if "Email" in log_df.columns:
            sent_emails = set(log_df["Email"].astype(str).str.lower())
    else:
        log_df = pd.DataFrame(
            columns=["Date", "Email", "Company Name", "Role", "Subject"]
        )

    sent_count = 0

    for _, row in df.iterrows():
        company = str(row.get("Company Name", "")).strip()
        hr_name = str(row.get("HR Name", "")).strip()
        email = str(row.get("Email", "")).strip()
        role = str(row.get("Role", "Power BI Developer")).strip() or "Power BI Developer"

        if not email or "@" not in email:
            continue

        email_lower = email.lower()
        if email_lower in sent_emails:
            print("Already contacted, skipping:", email)
            continue

        if sent_count >= DAILY_LIMIT:
            print(f"Reached DAILY_LIMIT of {DAILY_LIMIT}, stopping.")
            break

        subject, body = generate_email(company, hr_name, role)

        if DRY_RUN:
            print("[DRY RUN] Would send to:", email, "| Subject:", subject)
        else:
            print("Sending to:", email, "| Subject:", subject)
            try:
                send_email(email, subject, body)
                sent_count += 1
                print(f"Sent to {email}. Total sent this run: {sent_count}")
            except Exception as e:
                print(f"Error sending to {email}: {e}")
                # do not log as sent if it failed
                continue

        # Log (even in dry-run if you prefer, but usually only real sends)
        if not DRY_RUN:
            now = datetime.now().isoformat(timespec="seconds")
            new_row = {
                "Date": now,
                "Email": email,
                "Company Name": company,
                "Role": role,
                "Subject": subject,
            }
            log_df = pd.concat(
                [log_df, pd.DataFrame([new_row])],
                ignore_index=True,
            )
            sent_emails.add(email_lower)

        time.sleep(10)  # avoid spammy burst sending [web:13]

    if not DRY_RUN:
        log_df.to_csv(LOG_PATH, index=False)
        print("Log updated at", LOG_PATH)

    print("Run complete. Emails processed in this run:", sent_count)


if __name__ == "__main__":
    main()
