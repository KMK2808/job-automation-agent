import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("LLM_API_KEY")

YOUR_NAME = "Your name"
YOUR_EMAIL = "Your Email"
YOUR_PHONE = "Your NUmber"


# ----- Template variants for middle paragraph -----

def middle_para_power_bi_variant1():
    return (
        "In my current role, I focus on building interactive Power BI dashboards and "
        "data models, working closely with stakeholders to turn raw data into clear, "
        "actionable insights."
    )

def middle_para_power_bi_variant2():
    return (
        "Recently, most of my work has been around optimizing existing Power BI reports, "
        "improving DAX calculations, and ensuring data models are efficient and easy to maintain."
    )

def middle_para_power_bi_variant3():
    return (
        "I enjoy end-to-end ownership of BI solutions, from preparing data with SQL and Azure "
        "services to publishing and maintaining Power BI reports for business teams."
    )

def middle_para_data_engineer_variant1():
    return (
        "In my current role, I work on building and maintaining scalable data pipelines, "
        "using SQL, Spark, and Azure services to support analytics and reporting use cases."
    )

def middle_para_data_engineer_variant2():
    return (
        "My day-to-day responsibilities include designing ETL workflows, ensuring data quality, "
        "and collaborating with analysts to make sure data is ready for BI and advanced analytics."
    )

def middle_para_data_engineer_variant3():
    return (
        "I have experience working with large datasets, optimizing queries, and tuning pipelines so "
        "that downstream dashboards and reports are reliable and performant."
    )


# ----- OpenAI helper -----

def call_llm_for_tweaks(role, base_subject, middle_para_text):
    """
    Uses OpenAI to slightly improve the subject and middle paragraph
    based on the role. If anything fails, caller should use base versions.
    """
    if not OPENAI_API_KEY:
        return base_subject, middle_para_text

    system_msg = (
        "You improve job-application emails without changing facts. "
        "Keep length similar and keep the tone professional."
    )

    user_msg = f"""
User's target role: {role}

Base subject:
{base_subject}

Base middle paragraph (plain text, no HTML tags):
{middle_para_text}

Tasks:
1) Rewrite the subject to better match the role, but keep the same general idea and similar length.
2) Rewrite the paragraph to emphasize skills relevant to this role. Do not invent new skills or experience.

Respond ONLY in this format:
Subject: <new subject line>
Paragraph: <new paragraph text>
"""

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gpt-4o-mini",  # choose any chat-capable model you have access to [web:13]
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.5,
    }

    resp = requests.post(url, json=data, headers=headers)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]

    new_subject = base_subject
    new_paragraph = middle_para_text

    for line in content.splitlines():
        if line.lower().startswith("subject:"):
            new_subject = line.split(":", 1)[1].strip()
        elif line.lower().startswith("paragraph:"):
            new_paragraph = line.split(":", 1)[1].strip()

    return new_subject, new_paragraph


# ----- Main generator -----

def generate_email(company, hr_name, role):
    role = role or "Power BI Developer"
    base_subject = f"Application for {role} Roles | 3 Years Experience"

    if hr_name and hr_name.strip():
        greeting_line = f"Dear {hr_name.strip()},"
    else:
        greeting_line = "Dear Hiring Team,"

    role_lower = role.lower()

    # pick base middle paragraph variants based on role + random choice
    if "power bi" in role_lower or "bi developer" in role_lower:
        middle_options = [
            middle_para_power_bi_variant1(),
            middle_para_power_bi_variant2(),
            middle_para_power_bi_variant3(),
        ]
    else:  # treat as data engineer / generic data role
        middle_options = [
            middle_para_data_engineer_variant1(),
            middle_para_data_engineer_variant2(),
            middle_para_data_engineer_variant3(),
        ]

    middle_para_text = random.choice(middle_options)

    # Try OpenAI tweaks; fall back to base versions on any error
    try:
        base_subject, middle_para_text = call_llm_for_tweaks(
            role, base_subject, middle_para_text
        )
    except Exception as e:
        print("LLM tweak failed, using base template:", e)

    body_html = f"""\
<p>{greeting_line}</p>

<p>I hope you are doing well.</p>

<p>
My name is {YOUR_NAME}, and I am reaching out to express my interest in
<b>Power BI Developer</b> opportunities. I have around <b>3 years</b> of experience in
Data Engineering and Business Intelligence, working extensively with
<b>Power BI</b>, <b>SQL</b>, and <b>Azure</b>-based data platforms.
</p>

<p>
{middle_para_text}
 I have hands-on experience in:
</p>

<ul>
  <li>Designing interactive dashboards and data models in Power BI (DAX, measures, visuals)</li>
  <li>Writing complex SQL queries for reporting and analytics</li>
  <li>Working with large datasets and preparing data for BI use cases</li>
  <li>Collaborating with cross-functional teams to deliver actionable insights</li>
</ul>

<p>
I am looking for opportunities that allow me to grow further in <b>Power BI</b>, <b>DAX</b>,
and overall <b>BI &amp; Analytics</b>. I would be grateful if you could review my profile
and consider me for any suitable openings within your organization.
</p>

<p>I have attached my resume for your reference.</p>

<p>Thank you for your time.</p>

<p>
Best regards,<br>
{YOUR_NAME}<br>
Email: {YOUR_EMAIL}<br>
Phone: {YOUR_PHONE}
</p>
"""

    return base_subject, body_html
