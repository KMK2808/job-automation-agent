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

# Ensure this file exists in the same folder
RESUME_PATH = "Kollu_Manoj_Kumar_Data_engineering_PowerBI_2025.pdf"


def send_email(to_email, subject, body_html):
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = formataddr(("Kollu Manoj Kumar", EMAIL_ADDRESS))
    msg["To"] = to_email

    # HTML body
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    # Attach resume
    with open(RESUME_PATH, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="{os.path.basename(RESUME_PATH)}"',
    )
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
