import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import formataddr
from email import encoders
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SENDER_NAME = os.getenv("SENDER_NAME", "Job Automation Agent")

DEFAULT_RESUME_PATH = os.getenv(
    "RESUME_PATH", "Kollu_Manoj_Kumar_Data_engineering_PowerBI_2026.pdf"
)


def send_email(to_email, subject, body_html, resume_path=None):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD must be set in .env")

    selected_resume_path = resume_path or DEFAULT_RESUME_PATH
    if not os.path.exists(selected_resume_path):
        raise FileNotFoundError(f"Resume file not found: {selected_resume_path}")

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = formataddr((SENDER_NAME, EMAIL_ADDRESS))
    msg["To"] = to_email

    # HTML body
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    # Attach resume
    with open(selected_resume_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="{os.path.basename(selected_resume_path)}"',
    )
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
