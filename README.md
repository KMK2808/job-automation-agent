# AI Job Outreach Agent
AI‑powered outreach tool that helps data / BI professionals send personalized, HTML emails with attached resumes to recruiters and HR contacts at scale. 
It supports CSV‑based contact lists, OpenAI‑powered tailoring, logging to avoid duplicates, and can be extended with a web UI (Flask/Streamlit).
This project is aimed at Power BI / Data Engineering roles but is easy to adapt to other domains.[1]

***

## Features

- **CSV‑driven outreach**  
  - Upload or maintain recruiter lists in CSV format with columns such as `Company Name`, `HR Name`, `Email`, and `Role`.[1]

- **Role‑aware email generation**  
  - Uses fixed, professional templates plus optional OpenAI tweaks to adapt one paragraph and subject line for each role (e.g., Power BI Developer vs Data Engineer).   
  - HTML emails with bold highlights for key skills (Power BI, SQL, Azure, etc.) and an attached resume PDF.

- **Bulk sending with safety controls**  
  - Delay between emails (e.g., 10–20 seconds) to avoid spammy bursts.  
  - Daily send limit to control volume.  
  - Error handling so one failed send does not stop the whole run.

- **Logging and de‑duplication**  
  - All successful sends are logged to `sent_log.csv` with `Date`, `Email`, `Company Name`, `Role`, and `Subject`.   
  - Before sending, the agent checks this log and skips addresses that were already contacted.

- **LLM‑assisted personalization (optional)**  
  - Integrates with OpenAI’s Chat Completions API to:  
    - Slightly refine the subject line per role.  
    - Rewrite a middle paragraph to emphasize skills most relevant to that role, without inventing facts.   

- **Extensible architecture**  
  - Clear separation of concerns:  
    - `generate_email.py` – content generation.  
    - `send_email.py` – transport and attachment.  
    - `main.py` – orchestration, logging, de‑duplication, and safety controls.   
  - Can be wrapped by a Flask/Streamlit front‑end without changing the core logic.

***

## Project structure

```text
.
├── generate_email.py      # Builds HTML email content, role-aware + optional OpenAI tweaks
├── send_email.py          # Sends emails via Gmail SMTP with resume attachment
├── main.py                # CLI orchestrator: reads CSV, loops over contacts, logs sends
├── recruiters.csv         # Sample recruiter/contact list (not committed in real repo)
├── sent_log.csv           # Generated log of sent emails (git-ignored in real use)
├── .env                   # Environment variables (never commit)
└── README.md
```

Optional (if you add a web UI):

```text
├── app.py                 # Flask or Streamlit app (web front-end)
└── templates/             # HTML templates for Flask
```

***

## Prerequisites

- Python 3.10+  
- A Gmail account with **App Password** enabled for SMTP sending.   
- An OpenAI API key (optional but recommended for LLM features). 

Python packages:

```bash
pip install pandas python-dotenv requests
# plus, if you use Flask or Streamlit:
pip install flask         # or: pip install streamlit
```

***

## Environment configuration

Create a `.env` file in the project root (do not commit this file):

```env
EMAIL_ADDRESS=yourgmail@gmail.com
EMAIL_PASSWORD=your_app_password   # 16-char Gmail App Password without spaces
LLM_API_KEY=your_openai_api_key    # used by generate_email.py
```

- Generate a Gmail App Password in your Google Account under **Security → App passwords**, then paste it into `EMAIL_PASSWORD` with no spaces.   
- `LLM_API_KEY` is optional; if missing, the agent falls back to fixed templates.

***

## Input data format

The outreach agent expects a CSV file called `recruiters.csv` in the project root with at least these columns:

- `Company Name` – e.g., `LTI Mindtree`, `Virtusa`.   
- `HR Name` – recruiter or HR name (can be blank).[1]
- `Email` – contact email address.   
- `Role` – target role title, e.g., `Power BI Developer`, `Senior Data Engineer`, `Data Analyst`.[1]

Example:

```csv
Company Name,HR Name,Email,Role
LTI Mindtree,Gayatri Gupta,Gayatri.gupta2@ltimindtree.com,Power BI Developer
Virtusa,Mary Sherin,marysherin@virtusa.com,Data Analyst
GoKwik,Chetna Gogia,example@gokwik.co,Senior Data Engineer
```

You can build this file manually, export from existing Excel sheets, or generate it from other sources, as long as the headers match.
***
## How it works
### 1. Email generation (`generate_email.py`)

- Reads environment variables and constants (your name, email, phone).  
- For each contact, it:  
  - Builds a base subject like:  
    - `Application for Power BI Developer or Azure Data engineer Roles | 3 Years Experience`.  
  - Selects a middle paragraph template based on the `Role` (Power BI vs Data Engineer vs generic data).  
  - Optionally calls OpenAI to refine:  
    - The subject line.  
    - The chosen middle paragraph, keeping facts unchanged.   
  - Returns `(subject, body_html)` where `body_html` is a full HTML email with:  
    - Greeting (using HR name if available).  
    - Template describing your experience (Power BI, SQL, Azure, pipelines, etc.).  
    - Bulleted list of key skills and responsibilities.  
    - Closing and contact details. 

### 2. Sending emails (`send_email.py`)

- Connects to Gmail SMTP over SSL (`smtp.gmail.com:465`) using your App Password.   
- Builds a multipart email with:  
  - HTML body (rendering `<b>Power BI</b>` etc. as bold).  
  - A PDF resume attachment (`Manoj_Kollu_Resume.pdf` by default).  
- Sends the message to the target email address.

### 3. Orchestration and logging (`main.py`)

- Loads `recruiters.csv` via `pandas.read_csv`.   
- Cleans and filters data:  
  - Drops rows with missing/invalid emails.  
  - Optionally filters roles to BI / data roles using regex keywords.[1]
- Loads `sent_log.csv` (if present) to build a set of previously contacted emails.   
- Loops over each contact:  
  - Skips if email already exists in `sent_log.csv`.  
  - Respects a configurable `DAILY_LIMIT`.  
  - Calls `generate_email()` and `send_email()` (if not in dry‑run mode).  
  - Waits `time.sleep(delay_seconds)` between sends to avoid burst activity.  
  - On success, appends a new row to `sent_log.csv` with timestamp and metadata.   
  - On error, prints the error and continues.

This design ensures idempotency (no double‑mailing) and gives you a full history of outreach.

***

## Usage (CLI version)

1. Place your resume PDF in the project root, e.g.:

   ```text
   Your_Resume.pdf
   ```

   and ensure `send_email.py` points to this filename.

2. Prepare `recruiters.csv` as described above. 

3. Set dry‑run and limits in `main.py`:

   ```python
   DRY_RUN = True          # True = simulate, False = actually send
   DAILY_LIMIT = 30        # max emails per run
   ```

4. Run:

   ```bash
   python main.py
   ```

5. When comfortable with the previews and logs, switch `DRY_RUN = False` and run again to send real emails.

`sent_log.csv` will be created/updated automatically.

***

## Optional: Web UI (Flask or Streamlit)

Although the core logic is CLI‑based, you can wrap it with a simple front‑end:

- **Streamlit**:  
  - `app.py` with file uploader, “Dry run” checkbox, and basic charts (emails by role/company).[2]
  - Run with `python -m streamlit run app.py`.

- **Flask**:  
  - `app.py` with `/` (upload form) and `/run` (execute outreach and show results table).[3]
  - Run with `python app.py` and open `http://127.0.0.1:5000/`.

Both reuse `generate_email.py`, `send_email.py`, and `sent_log.csv` for the actual logic.

***

## Safety and etiquette

- **Rate limits and spam**  
  - Keep a reasonable delay between emails (10–30 seconds) and a daily cap (e.g., 20–50 emails) to avoid being flagged by email providers.   

- **Honesty and content**  
  - Ensure the templates and any LLM‑generated text accurately reflect your real skills and experience; do not let the model invent projects or years of experience.[4]

- **Data privacy**  
  - Treat the recruiter email lists and logs as sensitive data.  
  - Do not commit `recruiters.csv`, `sent_log.csv`, or `.env` to public repos.

- **Platform policies**  
  - Use this tool to contact people who have explicitly shared email addresses for job applications (e.g., in job posts, referrals, or public HR contact lists).[1]
  - For LinkedIn itself, keep final actions (messages, connection requests) manual to stay within LinkedIn’s automation policy.[5][6]

***

## Possible extensions

- **LinkedIn message generator**:  
  - Use the same recruiter lists (with LinkedIn URLs) to generate short, personalized LinkedIn connection messages that you manually paste into LinkedIn.[1]

- **Response tracking**:  
  - Add a `Status` column to `sent_log.csv` and update it manually with “Responded”, “Interview”, etc., then build simple analytics.

- **More role templates**:  
  - Extend role detection and templates to cover Data Scientist, ML Engineer, or generic Software Engineer roles.

***
