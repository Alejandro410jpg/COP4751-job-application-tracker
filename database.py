"""
database.py - database connection and all queries for the Job Application Tracker.
"""
import json
import os

import mysql.connector

# Change these if your MySQL login is different.
# You can also set them as environment variables.
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "tracker"),
    "password": os.environ.get("DB_PASSWORD", "tracker123"),
    "database": os.environ.get("DB_NAME", "job_tracker"),
}


def get_db():
    """Open a new database connection."""
    return mysql.connector.connect(**DB_CONFIG)


def run_query(sql, params=(), fetch=None):
    """
    Run one SQL statement.
    fetch="all"  -> return a list of rows (dicts)
    fetch="one"  -> return one row (dict) or None
    fetch=None   -> save the change and return the new row id
    """
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        if fetch == "all":
            return cursor.fetchall()
        if fetch == "one":
            return cursor.fetchone()
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def _blank_to_none(value):
    """Empty form fields become NULL in the database."""
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None


def parse_json(value):
    """JSON columns may come back as text. Turn them into Python objects."""
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return None


def skills_to_json(skills_text):
    """'Python, SQL, Flask' -> '["Python", "SQL", "Flask"]'"""
    skills = [s.strip() for s in (skills_text or "").split(",") if s.strip()]
    return json.dumps(skills)


# ---------------------------------------------------------------- companies

def get_companies():
    return run_query("SELECT * FROM companies ORDER BY company_name", fetch="all")


def get_company(company_id):
    return run_query("SELECT * FROM companies WHERE company_id = %s",
                     (company_id,), fetch="one")


def add_company(data):
    return run_query(
        """INSERT INTO companies (company_name, industry, website, city, state, notes)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (data["company_name"].strip(), _blank_to_none(data.get("industry")),
         _blank_to_none(data.get("website")), _blank_to_none(data.get("city")),
         _blank_to_none(data.get("state")), _blank_to_none(data.get("notes"))))


def update_company(company_id, data):
    run_query(
        """UPDATE companies SET company_name=%s, industry=%s, website=%s,
           city=%s, state=%s, notes=%s WHERE company_id=%s""",
        (data["company_name"].strip(), _blank_to_none(data.get("industry")),
         _blank_to_none(data.get("website")), _blank_to_none(data.get("city")),
         _blank_to_none(data.get("state")), _blank_to_none(data.get("notes")),
         company_id))


def delete_company(company_id):
    run_query("DELETE FROM companies WHERE company_id = %s", (company_id,))


# --------------------------------------------------------------------- jobs

JOB_SELECT = """
    SELECT j.*, c.company_name
    FROM jobs j JOIN companies c ON j.company_id = c.company_id
"""


def _fix_job(job):
    if job:
        job["requirements"] = parse_json(job["requirements"]) or []
    return job


def get_jobs():
    rows = run_query(JOB_SELECT + " ORDER BY j.date_posted DESC, j.job_id DESC",
                     fetch="all")
    return [_fix_job(r) for r in rows]


def get_job(job_id):
    return _fix_job(run_query(JOB_SELECT + " WHERE j.job_id = %s",
                              (job_id,), fetch="one"))


def _int_or_none(value):
    value = _blank_to_none(value)
    return int(value) if value is not None else None


def add_job(data):
    return run_query(
        """INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max,
                             job_url, date_posted, requirements)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (int(data["company_id"]), data["job_title"].strip(), data.get("job_type"),
         _int_or_none(data.get("salary_min")), _int_or_none(data.get("salary_max")),
         _blank_to_none(data.get("job_url")), _blank_to_none(data.get("date_posted")),
         skills_to_json(data.get("requirements"))))


def update_job(job_id, data):
    run_query(
        """UPDATE jobs SET company_id=%s, job_title=%s, job_type=%s, salary_min=%s,
           salary_max=%s, job_url=%s, date_posted=%s, requirements=%s
           WHERE job_id=%s""",
        (int(data["company_id"]), data["job_title"].strip(), data.get("job_type"),
         _int_or_none(data.get("salary_min")), _int_or_none(data.get("salary_max")),
         _blank_to_none(data.get("job_url")), _blank_to_none(data.get("date_posted")),
         skills_to_json(data.get("requirements")), job_id))


def delete_job(job_id):
    run_query("DELETE FROM jobs WHERE job_id = %s", (job_id,))


# ------------------------------------------------------------ applications

APP_SELECT = """
    SELECT a.*, j.job_title, c.company_name
    FROM applications a
    JOIN jobs j ON a.job_id = j.job_id
    JOIN companies c ON j.company_id = c.company_id
"""


def _fix_app(app):
    if app:
        app["interview_data"] = parse_json(app["interview_data"])
    return app


def get_applications():
    rows = run_query(APP_SELECT + " ORDER BY a.application_date DESC, a.application_id DESC",
                     fetch="all")
    return [_fix_app(r) for r in rows]


def get_application(application_id):
    return _fix_app(run_query(APP_SELECT + " WHERE a.application_id = %s",
                              (application_id,), fetch="one"))


def _interview_json(data):
    """Build the interview_data JSON from the three form fields."""
    info = {
        "date": _blank_to_none(data.get("interview_date")),
        "type": _blank_to_none(data.get("interview_type")),
        "notes": _blank_to_none(data.get("interview_notes")),
    }
    info = {k: v for k, v in info.items() if v}
    return json.dumps(info) if info else None


def add_application(data):
    return run_query(
        """INSERT INTO applications (job_id, application_date, status, resume_version,
                                     cover_letter_sent, interview_data)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (int(data["job_id"]), data["application_date"], data.get("status", "Applied"),
         _blank_to_none(data.get("resume_version")),
         1 if data.get("cover_letter_sent") else 0, _interview_json(data)))


def update_application(application_id, data):
    run_query(
        """UPDATE applications SET job_id=%s, application_date=%s, status=%s,
           resume_version=%s, cover_letter_sent=%s, interview_data=%s
           WHERE application_id=%s""",
        (int(data["job_id"]), data["application_date"], data.get("status", "Applied"),
         _blank_to_none(data.get("resume_version")),
         1 if data.get("cover_letter_sent") else 0, _interview_json(data),
         application_id))


def delete_application(application_id):
    run_query("DELETE FROM applications WHERE application_id = %s", (application_id,))


# ----------------------------------------------------------------- contacts

CONTACT_SELECT = """
    SELECT ct.*, c.company_name
    FROM contacts ct JOIN companies c ON ct.company_id = c.company_id
"""


def get_contacts():
    return run_query(CONTACT_SELECT + " ORDER BY ct.contact_name", fetch="all")


def get_contact(contact_id):
    return run_query(CONTACT_SELECT + " WHERE ct.contact_id = %s",
                     (contact_id,), fetch="one")


def add_contact(data):
    return run_query(
        """INSERT INTO contacts (company_id, contact_name, title, email, phone,
                                 linkedin_url, notes)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (int(data["company_id"]), data["contact_name"].strip(),
         _blank_to_none(data.get("title")), _blank_to_none(data.get("email")),
         _blank_to_none(data.get("phone")), _blank_to_none(data.get("linkedin_url")),
         _blank_to_none(data.get("notes"))))


def update_contact(contact_id, data):
    run_query(
        """UPDATE contacts SET company_id=%s, contact_name=%s, title=%s, email=%s,
           phone=%s, linkedin_url=%s, notes=%s WHERE contact_id=%s""",
        (int(data["company_id"]), data["contact_name"].strip(),
         _blank_to_none(data.get("title")), _blank_to_none(data.get("email")),
         _blank_to_none(data.get("phone")), _blank_to_none(data.get("linkedin_url")),
         _blank_to_none(data.get("notes")), contact_id))


def delete_contact(contact_id):
    run_query("DELETE FROM contacts WHERE contact_id = %s", (contact_id,))


# ---------------------------------------------------------------- dashboard

def get_stats():
    """Numbers for the dashboard page."""
    stats = {}
    for name, table in [("companies", "companies"), ("jobs", "jobs"),
                        ("applications", "applications"), ("contacts", "contacts")]:
        row = run_query(f"SELECT COUNT(*) AS n FROM {table}", fetch="one")
        stats[name] = row["n"]

    rows = run_query("SELECT status, COUNT(*) AS n FROM applications GROUP BY status",
                     fetch="all")
    counts = {r["status"]: r["n"] for r in rows}
    statuses = ["Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn"]
    stats["by_status"] = {s: counts.get(s, 0) for s in statuses}

    stats["recent"] = run_query(
        APP_SELECT + " ORDER BY a.application_date DESC, a.application_id DESC LIMIT 5",
        fetch="all")
    return stats
