# Job Automation Agent

Job Automation Agent is a Python-based email outreach tool for job applications.
It supports CSV/Excel contact lists, dynamic column mapping, optional LLM-assisted personalization, and a single-page Flask UI for preview-first sending.

## What Is New

- Single-page Flask workflow:
  - Upload file
  - Configure defaults
  - Map columns
  - Preview
  - Send
- Dynamic mapping:
  - You are not locked to fixed column names.
  - Only email is mandatory.
- Fallback inference from email:
  - Missing recruiter name and company can be inferred from `local@domain.com`.
- Dynamic role fallback:
  - Uses row role if available, otherwise default role from UI/CLI.
- External editable email template:
  - Update HTML in `templates/email_template.html` without changing Python code.
- Safer operations:
  - Preview-first flow
  - Dry-run behavior and explicit confirmation in UI before live send
  - Delay and daily limit controls
- Better logging:
  - `sent_log.csv` as master log
  - `logs/run_history.csv` as append-only run history
  - De-dup checks only rows with `Status=SENT`
- UI themes:
  - Forest, Sunset, Ocean, Midnight, Graphite

## Project Structure

```text
.
|-- app.py
|-- main.py
|-- outreach_core.py
|-- generate_email.py
|-- send_email.py
|-- requirements.txt
|-- templates/
|   |-- index.html
|   `-- email_template.html
|-- logs/
|   `-- run_history.csv
|-- sent_log.csv
`-- .env
```

## Requirements

- Python 3.10+
- Gmail account with App Password
- OpenAI API key (optional)

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create `.env` in project root:

```env
EMAIL_ADDRESS=yourgmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
LLM_API_KEY=your_openai_key
SENDER_NAME=Your Name
CANDIDATE_NAME=Your Name
CANDIDATE_EMAIL=yourgmail@gmail.com
CANDIDATE_PHONE=your_phone
YEARS_EXPERIENCE=3.5
RESUME_PATH=resume.pdf
EMAIL_TEMPLATE_PATH=templates/email_template.html
LLM_MODEL=gpt-4o-mini
```

Minimum required:

- `EMAIL_ADDRESS`
- `EMAIL_PASSWORD`
- `RESUME_PATH`

## Input File Support

Supported input formats:

- `.csv`
- `.xlsx`
- `.xls`

Expected fields (flexible names, mapped in UI):

- Email (required)
- HR/Recruiter Name (optional)
- Company Name (optional)
- Role (optional)

If HR name or company is missing, the app infers values from email.

## Run (Flask UI)

```bash
python app.py
```

Open:

`http://127.0.0.1:5000`

Workflow:

1. Upload recruiter file
2. Set defaults (role, limits, paths)
3. Load columns
4. Map columns
5. Preview
6. Confirm and send

## Run (CLI)

Preview only:

```bash
python main.py --input recruiters.csv --preview-only
```

Actual send:

```bash
python main.py --input recruiters.csv --send --daily-limit 30 --delay-seconds 10
```

## Logging Behavior

- `sent_log.csv`:
  - Contains `SENT`, `FAILED`, and `DRY_RUN` rows.
  - De-dup logic only treats `SENT` emails as already contacted.
- `logs/run_history.csv`:
  - Append-only run-level history with `RunId`.
  - Useful for audits, analytics, and tracking retries.

You do not need to delete logs between runs.

## Notes

- `LLM_API_KEY` is optional. If unavailable, template generation still works.
- Keep `.env`, contact lists, and logs private.
- Send responsibly and follow platform policies and anti-spam best practices.
