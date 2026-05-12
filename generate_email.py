import html
import os
import random
from string import Formatter

import requests
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

DEFAULT_TEMPLATE_PATH = os.getenv("EMAIL_TEMPLATE_PATH", "templates/email_template.html")
ROLE_TEMPLATE_DIR = os.getenv("ROLE_TEMPLATE_DIR", "templates/roles")

PROFILE_DEFAULTS = {
    "your_name": os.getenv("CANDIDATE_NAME", "Your Name"),
    "your_email": os.getenv("CANDIDATE_EMAIL", "you@example.com"),
    "your_phone": os.getenv("CANDIDATE_PHONE", "+91-0000000000"),
    "years_experience": os.getenv("YEARS_EXPERIENCE", "3"),
}


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


def middle_para_data_analyst_variant1():
    return (
        "I work closely with business and product teams to convert raw data into useful insights "
        "through exploratory analysis, KPI tracking, and clear dashboard storytelling."
    )


def middle_para_data_analyst_variant2():
    return (
        "My recent work includes building reporting layers, defining data quality checks, and "
        "analyzing trends to support operational and strategic decisions."
    )


def middle_para_data_analyst_variant3():
    return (
        "I focus on making analytics practical for stakeholders by combining SQL-based analysis, "
        "dashboard design, and communication of actionable findings."
    )


def call_llm_for_tweaks(role, base_subject, middle_para_text):
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

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.5,
    }

    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        json=data,
        headers=headers,
        timeout=25,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]

    new_subject = base_subject
    new_paragraph = middle_para_text

    for line in content.splitlines():
        lowered = line.lower()
        if lowered.startswith("subject:"):
            new_subject = line.split(":", 1)[1].strip() or base_subject
        elif lowered.startswith("paragraph:"):
            new_paragraph = line.split(":", 1)[1].strip() or middle_para_text

    return new_subject, new_paragraph


def pick_middle_paragraph(role):
    role_lower = (role or "").lower()
    if "power bi" in role_lower or "bi developer" in role_lower:
        options = [
            middle_para_power_bi_variant1(),
            middle_para_power_bi_variant2(),
            middle_para_power_bi_variant3(),
        ]
    elif "analyst" in role_lower:
        options = [
            middle_para_data_analyst_variant1(),
            middle_para_data_analyst_variant2(),
            middle_para_data_analyst_variant3(),
        ]
    else:
        options = [
            middle_para_data_engineer_variant1(),
            middle_para_data_engineer_variant2(),
            middle_para_data_engineer_variant3(),
        ]
    return random.choice(options)


def resolve_template_path(role, template_path=None):
    if template_path and str(template_path).strip().lower() not in {"auto", "role-auto"}:
        return template_path

    role_lower = (role or "").lower()
    if "power bi" in role_lower or "bi developer" in role_lower:
        candidate = os.path.join(ROLE_TEMPLATE_DIR, "power_bi.html")
    elif "azure" in role_lower or "data engineer" in role_lower or "etl" in role_lower:
        candidate = os.path.join(ROLE_TEMPLATE_DIR, "azure_data_engineer.html")
    elif "analyst" in role_lower:
        candidate = os.path.join(ROLE_TEMPLATE_DIR, "data_analyst.html")
    else:
        candidate = DEFAULT_TEMPLATE_PATH

    if os.path.exists(candidate):
        return candidate
    return DEFAULT_TEMPLATE_PATH


def _render_external_template(template_path, context):
    with open(template_path, "r", encoding="utf-8") as f:
        template_text = f.read()

    formatter = Formatter()
    used_fields = {
        field_name
        for _, field_name, _, _ in formatter.parse(template_text)
        if field_name
    }
    safe_context = dict(context)
    for key in used_fields:
        safe_context.setdefault(key, "")

    return template_text.format_map(safe_context)


def generate_email(company, hr_name, role, template_path=None, profile=None):
    role = (role or "Data Analyst").strip()
    company = (company or "").strip()
    hr_name = (hr_name or "").strip()

    if hr_name:
        greeting_line = f"Dear {hr_name},"
    else:
        greeting_line = "Dear Hiring Team,"

    subject = f"Application for {role} Position | {PROFILE_DEFAULTS['years_experience']} Years of Relevant Experience"
    middle_para_text = pick_middle_paragraph(role)

    try:
        subject, middle_para_text = call_llm_for_tweaks(role, subject, middle_para_text)
    except Exception as exc:
        print("LLM tweak failed, using base template:", exc)

    merged_profile = dict(PROFILE_DEFAULTS)
    if profile:
        merged_profile.update({k: v for k, v in profile.items() if v})

    render_context = {
        "greeting_line": html.escape(greeting_line),
        "role": html.escape(role),
        "intro_role": html.escape(role),
        "company_name": html.escape(company or "your organization"),
        "middle_paragraph": html.escape(middle_para_text),
        "your_name": html.escape(str(merged_profile.get("your_name", ""))),
        "your_email": html.escape(str(merged_profile.get("your_email", ""))),
        "your_phone": html.escape(str(merged_profile.get("your_phone", ""))),
        "years_experience": html.escape(str(merged_profile.get("years_experience", ""))),
    }

    chosen_template_path = resolve_template_path(role, template_path=template_path)
    body_html = _render_external_template(chosen_template_path, render_context)
    return subject, body_html
