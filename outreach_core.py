import os
import re
import time
from datetime import datetime

import pandas as pd

from generate_email import generate_email
from send_email import send_email


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PERSONAL_DOMAINS = {
    "gmail",
    "yahoo",
    "outlook",
    "hotmail",
    "live",
    "icloud",
    "protonmail",
}

COLUMN_SYNONYMS = {
    "email": ["email", "email address", "mail", "mail id", "e-mail"],
    "hr_name": ["hr name", "name", "recruiter", "recruiter name", "contact"],
    "company_name": ["company", "company name", "organization", "org", "employer"],
    "role": ["role", "position", "job role", "title", "designation"],
}


def _normalize_label(value):
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def auto_detect_columns(columns):
    normalized = {_normalize_label(col): col for col in columns}
    result = {"email": None, "hr_name": None, "company_name": None, "role": None}

    for target, aliases in COLUMN_SYNONYMS.items():
        for alias in aliases:
            match = normalized.get(alias)
            if match:
                result[target] = match
                break
    return result


def read_contacts_file(input_path, sheet_name=None):
    ext = os.path.splitext(input_path)[1].lower()
    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(input_path, sheet_name=sheet_name or 0)
    return pd.read_csv(input_path)


def infer_name_company_from_email(email):
    local_part, domain_part = email.split("@", 1)
    domain_root = domain_part.split(".", 1)[0]

    guessed_name = re.sub(r"[._\-+]+", " ", local_part)
    guessed_name = re.sub(r"\d+", " ", guessed_name)
    guessed_name = re.sub(r"\s+", " ", guessed_name).strip().title()

    guessed_company = re.sub(r"[-_]+", " ", domain_root)
    guessed_company = re.sub(r"\s+", " ", guessed_company).strip().title()

    if not guessed_name:
        guessed_name = "Hiring Team"

    if not guessed_company or domain_root.lower() in PERSONAL_DOMAINS:
        guessed_company = "Your Organization"

    return guessed_name, guessed_company


def _read_value(row, col_name):
    if not col_name or col_name not in row.index:
        return ""
    value = row.get(col_name, "")
    if pd.isna(value):
        return ""
    return str(value).strip()


def prepare_contacts(df, column_map, default_role):
    results = []
    skipped = []

    email_col = column_map.get("email")
    if not email_col:
        raise ValueError("Email column mapping is required.")

    for idx, row in df.iterrows():
        email = _read_value(row, email_col).lower()
        if not EMAIL_RE.match(email):
            skipped.append(
                {
                    "row_number": idx + 2,
                    "reason": "Invalid or missing email",
                    "email": email,
                }
            )
            continue

        hr_name = _read_value(row, column_map.get("hr_name"))
        company_name = _read_value(row, column_map.get("company_name"))
        role = _read_value(row, column_map.get("role")) or default_role

        guessed_hr_name = False
        guessed_company = False
        if not hr_name or not company_name:
            inferred_name, inferred_company = infer_name_company_from_email(email)
            if not hr_name:
                hr_name = inferred_name
                guessed_hr_name = True
            if not company_name:
                company_name = inferred_company
                guessed_company = True

        results.append(
            {
                "email": email,
                "hr_name": hr_name or "Hiring Team",
                "company_name": company_name or "Your Organization",
                "role": role or default_role,
                "guessed_hr_name": guessed_hr_name,
                "guessed_company_name": guessed_company,
            }
        )

    return pd.DataFrame(results), skipped


def build_validation_summary(df, column_map, default_role):
    contacts_df, skipped_rows = prepare_contacts(df, column_map, default_role)
    total_rows = len(df)
    valid_rows = len(contacts_df)

    guessed_name_count = 0
    guessed_company_count = 0
    missing_role_count = 0
    if valid_rows:
        guessed_name_count = int(contacts_df["guessed_hr_name"].sum())
        guessed_company_count = int(contacts_df["guessed_company_name"].sum())
        missing_role_count = int((contacts_df["role"].astype(str).str.strip() == default_role).sum())

    return {
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "invalid_rows": len(skipped_rows),
        "guessed_name_count": guessed_name_count,
        "guessed_company_count": guessed_company_count,
        "default_role_applied_count": missing_role_count,
        "invalid_samples": skipped_rows[:20],
    }


def _load_sent_log(log_path):
    if not os.path.exists(log_path):
        empty = pd.DataFrame(
            columns=[
                "Date",
                "Email",
                "Company Name",
                "Role",
                "Subject",
                "Status",
                "Notes",
            ]
        )
        return empty, set()

    log_df = pd.read_csv(log_path)
    emails = set()
    if "Email" in log_df.columns:
        if "Status" in log_df.columns:
            sent_only = log_df[log_df["Status"].astype(str).str.upper() == "SENT"]
            emails = set(sent_only["Email"].astype(str).str.lower())
        else:
            emails = set(log_df["Email"].astype(str).str.lower())
    return log_df, emails


def _append_rows(log_df, rows):
    if not rows:
        return log_df
    return pd.concat([log_df, pd.DataFrame(rows)], ignore_index=True)


def _update_contact_status(run_rows, status_path):
    if not run_rows:
        return status_path

    if os.path.exists(status_path):
        status_df = pd.read_csv(status_path)
    else:
        status_df = pd.DataFrame(
            columns=[
                "Email",
                "HR Name",
                "Company Name",
                "Role",
                "Outreach Status",
                "Last Outreach Date",
                "Last Subject",
                "Notes",
            ]
        )

    for row in run_rows:
        email = str(row.get("Email", "")).strip().lower()
        if not email:
            continue

        if str(row.get("Status", "")).upper() == "SENT":
            outreach_status = "Sent"
        elif str(row.get("Status", "")).upper() == "FAILED":
            outreach_status = "Send Failed"
        else:
            outreach_status = "Dry Run"

        existing_idx = status_df.index[status_df["Email"].astype(str).str.lower() == email]
        update_values = {
            "Email": email,
            "HR Name": row.get("HR Name", ""),
            "Company Name": row.get("Company Name", ""),
            "Role": row.get("Role", ""),
            "Outreach Status": outreach_status,
            "Last Outreach Date": row.get("Date", ""),
            "Last Subject": row.get("Subject", ""),
            "Notes": row.get("Notes", ""),
        }
        if len(existing_idx) > 0:
            for key, value in update_values.items():
                status_df.loc[existing_idx[0], key] = value
        else:
            status_df = pd.concat([status_df, pd.DataFrame([update_values])], ignore_index=True)

    status_df.to_csv(status_path, index=False)
    return status_path


def _write_run_history(run_rows, base_log_path):
    if not run_rows:
        return None

    history_dir = os.path.join(os.path.dirname(base_log_path) or ".", "logs")
    os.makedirs(history_dir, exist_ok=True)
    history_path = os.path.join(history_dir, "run_history.csv")

    history_rows = []
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    for row in run_rows:
        new_row = dict(row)
        new_row["RunId"] = run_id
        history_rows.append(new_row)

    if os.path.exists(history_path):
        history_df = pd.read_csv(history_path)
    else:
        history_df = pd.DataFrame(columns=list(history_rows[0].keys()))

    history_df = pd.concat([history_df, pd.DataFrame(history_rows)], ignore_index=True)
    history_df.to_csv(history_path, index=False)
    return history_path


def run_campaign(
    input_path,
    column_map=None,
    default_role="Data Analyst",
    dry_run=True,
    daily_limit=30,
    delay_seconds=10,
    log_path="sent_log.csv",
    template_path="templates/email_template.html",
    resume_path=None,
    sheet_name=None,
    preview_only=False,
    preview_limit=10,
    allow_resend=False,
    status_path="contact_status.csv",
):
    df = read_contacts_file(input_path, sheet_name=sheet_name)
    detected = auto_detect_columns(df.columns)
    mapping = dict(detected)
    if column_map:
        mapping.update({k: v for k, v in column_map.items() if v})

    contacts_df, skipped_input_rows = prepare_contacts(df, mapping, default_role)
    log_df, sent_emails = _load_sent_log(log_path)

    run_rows = []
    preview_rows = []
    failed_rows = []
    skipped_existing = []
    sent_count = 0

    for _, contact in contacts_df.iterrows():
        email = str(contact["email"]).strip().lower()
        if (not allow_resend) and email in sent_emails:
            skipped_existing.append({"email": email, "reason": "Already in sent_log.csv"})
            continue

        if sent_count >= daily_limit:
            break

        subject, body_html = generate_email(
            company=contact["company_name"],
            hr_name=contact["hr_name"],
            role=contact["role"],
            template_path=template_path,
        )

        row_note_parts = []
        if contact.get("guessed_hr_name"):
            row_note_parts.append("HR name guessed from email")
        if contact.get("guessed_company_name"):
            row_note_parts.append("Company guessed from email")
        row_notes = "; ".join(row_note_parts)

        preview_rows.append(
            {
                "email": email,
                "company_name": contact["company_name"],
                "hr_name": contact["hr_name"],
                "role": contact["role"],
                "subject": subject,
                "notes": row_notes,
                "body_preview": body_html[:220] + ("..." if len(body_html) > 220 else ""),
            }
        )

        if preview_only and len(preview_rows) >= preview_limit:
            break
        if preview_only:
            continue

        timestamp = datetime.now().isoformat(timespec="seconds")
        if dry_run:
            run_rows.append(
                {
                    "Date": timestamp,
                    "Email": email,
                    "HR Name": contact["hr_name"],
                    "Company Name": contact["company_name"],
                    "Role": contact["role"],
                    "Subject": subject,
                    "Status": "DRY_RUN",
                    "Notes": row_notes,
                }
            )
            sent_count += 1
            continue

        try:
            send_email(email, subject, body_html, resume_path=resume_path)
            run_rows.append(
                {
                    "Date": timestamp,
                    "Email": email,
                    "HR Name": contact["hr_name"],
                    "Company Name": contact["company_name"],
                    "Role": contact["role"],
                    "Subject": subject,
                    "Status": "SENT",
                    "Notes": row_notes,
                }
            )
            sent_emails.add(email)
            sent_count += 1
        except Exception as exc:
            failed_rows.append({"email": email, "reason": str(exc)})
            run_rows.append(
                {
                    "Date": timestamp,
                    "Email": email,
                    "HR Name": contact["hr_name"],
                    "Company Name": contact["company_name"],
                    "Role": contact["role"],
                    "Subject": subject,
                    "Status": "FAILED",
                    "Notes": str(exc),
                }
            )

        if delay_seconds > 0:
            time.sleep(delay_seconds)

    if not preview_only:
        updated_log = _append_rows(log_df, run_rows)
        updated_log.to_csv(log_path, index=False)
        history_path = _write_run_history(run_rows, log_path)
        status_tracker_path = _update_contact_status(run_rows, status_path)
    else:
        history_path = None
        status_tracker_path = None

    return {
        "input_path": input_path,
        "detected_columns": detected,
        "column_map_used": mapping,
        "processed_contacts": len(contacts_df),
        "sent_or_dryrun_count": sent_count,
        "run_rows": run_rows,
        "preview_rows": preview_rows[:preview_limit],
        "failed_rows": failed_rows,
        "skipped_input_rows": skipped_input_rows,
        "skipped_existing": skipped_existing,
        "dry_run": dry_run,
        "preview_only": preview_only,
        "log_path": log_path,
        "history_log_path": history_path,
        "allow_resend": allow_resend,
        "status_tracker_path": status_tracker_path,
    }
