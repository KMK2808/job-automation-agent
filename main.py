import argparse
import os

from outreach_core import auto_detect_columns, read_contacts_file, run_campaign


def parse_args():
    parser = argparse.ArgumentParser(description="Job Automation Agent (CLI)")
    parser.add_argument("--input", default="recruiters.csv", help="Path to CSV/XLSX recruiter file")
    parser.add_argument("--sheet", default=None, help="Sheet name for Excel input")
    parser.add_argument("--email-col", default=None, help="Column name for email")
    parser.add_argument("--hr-col", default=None, help="Column name for recruiter/HR name")
    parser.add_argument("--company-col", default=None, help="Column name for company name")
    parser.add_argument("--role-col", default=None, help="Column name for role")
    parser.add_argument("--default-role", default="Data Analyst", help="Fallback role if missing in row")
    parser.add_argument("--daily-limit", type=int, default=30, help="Maximum emails per run")
    parser.add_argument("--delay-seconds", type=int, default=10, help="Delay between emails")
    parser.add_argument("--log-path", default="sent_log.csv", help="Path to sent log CSV")
    parser.add_argument(
        "--status-path",
        default="contact_status.csv",
        help="Path to contact status workflow CSV",
    )
    parser.add_argument(
        "--template-path",
        default=os.getenv("EMAIL_TEMPLATE_PATH", "auto"),
        help="Template path or 'auto' for role template library",
    )
    parser.add_argument(
        "--resume-path",
        default=os.getenv("RESUME_PATH", "resume.pdf"),
        help="Resume PDF path",
    )
    parser.add_argument("--preview-limit", type=int, default=10, help="Preview rows to print")
    parser.add_argument(
        "--allow-resend",
        action="store_true",
        help="Allow sending even if email is already marked SENT in sent_log.csv",
    )
    parser.add_argument(
        "--preview-only",
        action="store_true",
        help="Only generate preview and do not write/send",
    )

    send_group = parser.add_mutually_exclusive_group()
    send_group.add_argument(
        "--send",
        action="store_true",
        help="Actually send emails (default is dry-run).",
    )
    send_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate sending only (default behavior).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    is_dry_run = not args.send

    df = read_contacts_file(args.input, sheet_name=args.sheet)
    detected = auto_detect_columns(df.columns)
    print("Detected columns:", detected)

    column_map = {
        "email": args.email_col,
        "hr_name": args.hr_col,
        "company_name": args.company_col,
        "role": args.role_col,
    }

    result = run_campaign(
        input_path=args.input,
        column_map=column_map,
        default_role=args.default_role,
        dry_run=is_dry_run,
        daily_limit=args.daily_limit,
        delay_seconds=args.delay_seconds,
        log_path=args.log_path,
        template_path=args.template_path,
        resume_path=args.resume_path,
        sheet_name=args.sheet,
        preview_only=args.preview_only,
        preview_limit=args.preview_limit,
        allow_resend=args.allow_resend,
        status_path=args.status_path,
    )

    print("Dry run:", result["dry_run"])
    print("Preview only:", result["preview_only"])
    print("Processed contacts:", result["processed_contacts"])
    print("Sent/Dry-run rows:", result["sent_or_dryrun_count"])
    print("Skipped invalid input rows:", len(result["skipped_input_rows"]))
    print("Skipped existing contacts:", len(result["skipped_existing"]))
    print("Failed rows:", len(result["failed_rows"]))
    print("Log path:", result["log_path"])
    if result.get("status_tracker_path"):
        print("Status tracker path:", result["status_tracker_path"])

    if result["preview_rows"]:
        print("\nPreview:")
        for row in result["preview_rows"][: args.preview_limit]:
            print(
                f"- {row['email']} | {row['role']} | {row['subject']}"
                + (f" | {row['notes']}" if row["notes"] else "")
            )

    if result["failed_rows"]:
        print("\nFailures:")
        for row in result["failed_rows"]:
            print(f"- {row['email']}: {row['reason']}")


if __name__ == "__main__":
    main()
