import os
import uuid

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from outreach_core import auto_detect_columns, build_validation_summary, read_contacts_file, run_campaign


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-me")
app.config["UPLOAD_DIR"] = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)

UPLOAD_CACHE = {}


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _base_context():
    return {
        "columns": [],
        "detected": {"email": None, "hr_name": None, "company_name": None, "role": None},
        "token": "",
        "default_role": "Data Analyst",
        "daily_limit": "30",
        "delay_seconds": "10",
        "log_path": "sent_log.csv",
        "template_path": "auto",
        "resume_path": "Kollu_Manoj_Kumar_Data_engineering_PowerBI_2026.pdf",
        "sheet_name": "",
        "allow_resend": False,
        "status_path": "contact_status.csv",
        "validation": None,
        "result": None,
        "error": None,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    context = _base_context()

    if request.method == "GET":
        return render_template("index.html", **context)

    action = request.form.get("action", "prepare")
    context.update(
        {
            "token": request.form.get("token", ""),
            "default_role": request.form.get("default_role", "Data Analyst"),
            "daily_limit": request.form.get("daily_limit", "30"),
            "delay_seconds": request.form.get("delay_seconds", "10"),
            "log_path": request.form.get("log_path", "sent_log.csv"),
            "template_path": request.form.get("template_path", "auto"),
            "resume_path": request.form.get(
                "resume_path", "Kollu_Manoj_Kumar_Data_engineering_PowerBI_2026.pdf"
            ),
            "status_path": request.form.get("status_path", "contact_status.csv"),
            "sheet_name": request.form.get("sheet_name", ""),
            "allow_resend": request.form.get("allow_resend") == "yes",
        }
    )

    if action == "prepare":
        uploaded = request.files.get("contacts_file")
        if not uploaded or not uploaded.filename:
            context["error"] = "Please upload a CSV/XLSX file."
            return render_template("index.html", **context)

        safe_name = secure_filename(uploaded.filename)
        token = str(uuid.uuid4())
        stored_path = os.path.join(app.config["UPLOAD_DIR"], f"{token}_{safe_name}")
        uploaded.save(stored_path)
        UPLOAD_CACHE[token] = stored_path
        context["token"] = token

        try:
            df = read_contacts_file(stored_path, sheet_name=context["sheet_name"] or None)
        except Exception as exc:
            context["error"] = f"Unable to read file: {exc}"
            return render_template("index.html", **context)

        context["columns"] = list(df.columns)
        context["detected"] = auto_detect_columns(context["columns"])
        context["validation"] = build_validation_summary(
            df,
            context["detected"],
            context["default_role"],
        )
        return render_template("index.html", **context)

    input_path = UPLOAD_CACHE.get(context["token"])
    if not input_path or not os.path.exists(input_path):
        context["error"] = "Session expired. Upload file again."
        return render_template("index.html", **context)

    df = read_contacts_file(input_path, sheet_name=context["sheet_name"] or None)
    context["columns"] = list(df.columns)
    context["detected"] = auto_detect_columns(context["columns"])

    should_send = action == "send"
    if should_send and request.form.get("confirm_send") != "yes":
        context["error"] = "Enable confirmation before sending."
        return render_template("index.html", **context)

    column_map = {
        "email": request.form.get("email_col") or None,
        "hr_name": request.form.get("hr_col") or None,
        "company_name": request.form.get("company_col") or None,
        "role": request.form.get("role_col") or None,
    }
    context["validation"] = build_validation_summary(
        df,
        {
            "email": column_map.get("email") or context["detected"].get("email"),
            "hr_name": column_map.get("hr_name") or context["detected"].get("hr_name"),
            "company_name": column_map.get("company_name") or context["detected"].get("company_name"),
            "role": column_map.get("role") or context["detected"].get("role"),
        },
        context["default_role"],
    )

    result = run_campaign(
        input_path=input_path,
        column_map=column_map,
        default_role=context["default_role"],
        dry_run=not should_send,
        daily_limit=_to_int(context["daily_limit"], 30),
        delay_seconds=_to_int(context["delay_seconds"], 10),
        log_path=context["log_path"],
        template_path=context["template_path"],
        resume_path=context["resume_path"],
        sheet_name=context["sheet_name"] or None,
        preview_only=action == "preview",
        preview_limit=20,
        allow_resend=context["allow_resend"],
        status_path=context["status_path"],
    )
    context["result"] = result
    return render_template("index.html", **context)


if __name__ == "__main__":
    app.run(debug=True)
