"""
app.py - Flask application for the Job Application Tracker.
"""
import re
from datetime import date, datetime

import mysql.connector
from flask import Flask, abort, flash, redirect, render_template, request, url_for

import database as db

app = Flask(__name__)
app.secret_key = "change-this-secret-key"  # needed for flash messages


# ------------------------------------------------------------ error handling

@app.errorhandler(mysql.connector.Error)
def database_error(error):
    """Show a friendly message if MySQL is down or the login is wrong."""
    return render_template("error.html", message=str(error)), 500


# ---------------------------------------------------------------- dashboard

@app.route("/")
def dashboard():
    stats = db.get_stats()

    # Interviews that are still coming up (today or later), soonest first.
    today = date.today().isoformat()
    upcoming = []
    for a in db.get_applications():
        info = a["interview_data"] or {}
        when = info.get("date")
        if when and when >= today and a["status"] not in ("Rejected", "Withdrawn"):
            upcoming.append({"application": a, "date": when, "type": info.get("type")})
    upcoming.sort(key=lambda u: u["date"])

    return render_template("dashboard.html", stats=stats, total=stats["applications"],
                           upcoming=upcoming[:5])


# ---------------------------------------------------------------- companies

def validate_company(form):
    """Return an error message, or None if the form is OK."""
    name = form.get("company_name", "").strip()
    if not name:
        return "Company name is required."
    limits = {"company_name": 100, "industry": 50, "website": 200, "city": 50, "state": 50}
    for field, limit in limits.items():
        if len(form.get(field, "").strip()) > limit:
            return f"{field.replace('_', ' ').capitalize()} must be {limit} characters or less."
    website = form.get("website", "").strip()
    if website and not website.lower().startswith(("http://", "https://")):
        return "Website must start with http:// or https://"
    return None


@app.route("/companies")
def companies():
    return render_template("companies.html", companies=db.get_companies())


@app.route("/companies/<int:company_id>")
def company_detail(company_id):
    company = db.get_company(company_id)
    if company is None:
        abort(404)
    jobs = [j for j in db.get_jobs() if j["company_id"] == company_id]
    contacts = [c for c in db.get_contacts() if c["company_id"] == company_id]
    return render_template("company_detail.html", company=company, jobs=jobs, contacts=contacts)


@app.route("/companies/add", methods=["GET", "POST"])
def add_company():
    if request.method == "POST":
        error = validate_company(request.form)
        if error:
            flash(error, "error")
            return render_template("company_form.html", company=request.form, mode="add")
        db.add_company(request.form)
        flash("Company added.", "success")
        return redirect(url_for("companies"))
    return render_template("company_form.html", company={}, mode="add")


@app.route("/companies/<int:company_id>/edit", methods=["GET", "POST"])
def edit_company(company_id):
    company = db.get_company(company_id)
    if company is None:
        abort(404)
    if request.method == "POST":
        error = validate_company(request.form)
        if error:
            flash(error, "error")
            return render_template("company_form.html", company=request.form,
                                   mode="edit", company_id=company_id)
        db.update_company(company_id, request.form)
        flash("Company updated.", "success")
        return redirect(url_for("companies"))
    return render_template("company_form.html", company=company, mode="edit",
                           company_id=company_id)


@app.route("/companies/<int:company_id>/delete", methods=["POST"])
def delete_company(company_id):
    if db.get_company(company_id) is None:
        abort(404)
    db.delete_company(company_id)
    flash("Company deleted.", "success")
    return redirect(url_for("companies"))


# --------------------------------------------------------------------- jobs

JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship"]


@app.template_filter("money")
def money(value):
    """12345 -> $12,345"""
    return f"${value:,}"


def valid_date(text):
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_job(form):
    """Return an error message, or None if the form is OK."""
    title = form.get("job_title", "").strip()
    if not title:
        return "Job title is required."
    if len(title) > 100:
        return "Job title must be 100 characters or less."

    company_id = form.get("company_id", "")
    if not company_id.isdigit() or db.get_company(int(company_id)) is None:
        return "Please choose a company."

    if form.get("job_type") not in JOB_TYPES:
        return "Please choose a job type."

    salaries = {}
    for field, label in (("salary_min", "Minimum salary"), ("salary_max", "Maximum salary")):
        text = form.get(field, "").strip()
        if text:
            if not text.isdigit():
                return f"{label} must be a whole number."
            salaries[field] = int(text)
    if len(salaries) == 2 and salaries["salary_min"] > salaries["salary_max"]:
        return "Minimum salary cannot be more than maximum salary."

    url = form.get("job_url", "").strip()
    if len(url) > 300:
        return "Job URL must be 300 characters or less."
    if url and not url.lower().startswith(("http://", "https://")):
        return "Job URL must start with http:// or https://"

    posted = form.get("date_posted", "").strip()
    if posted and not valid_date(posted):
        return "Date posted must be a valid date."
    return None


@app.route("/jobs")
def jobs():
    return render_template("jobs.html", jobs=db.get_jobs())


@app.route("/jobs/<int:job_id>")
def job_detail(job_id):
    job = db.get_job(job_id)
    if job is None:
        abort(404)
    applications = [a for a in db.get_applications() if a["job_id"] == job_id]
    return render_template("job_detail.html", job=job, applications=applications)


@app.route("/jobs/add", methods=["GET", "POST"])
def add_job():
    companies = db.get_companies()
    if request.method == "POST":
        error = validate_job(request.form)
        if error:
            flash(error, "error")
            return render_template("job_form.html", job=request.form, mode="add",
                                   companies=companies, job_types=JOB_TYPES)
        db.add_job(request.form)
        flash("Job added.", "success")
        return redirect(url_for("jobs"))
    return render_template("job_form.html", job={"job_type": "Full-time"}, mode="add",
                           companies=companies, job_types=JOB_TYPES)


@app.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
def edit_job(job_id):
    job = db.get_job(job_id)
    if job is None:
        abort(404)
    companies = db.get_companies()
    if request.method == "POST":
        error = validate_job(request.form)
        if error:
            flash(error, "error")
            return render_template("job_form.html", job=request.form, mode="edit",
                                   job_id=job_id, companies=companies, job_types=JOB_TYPES)
        db.update_job(job_id, request.form)
        flash("Job updated.", "success")
        return redirect(url_for("jobs"))
    return render_template("job_form.html", job=job, mode="edit", job_id=job_id,
                           companies=companies, job_types=JOB_TYPES)


@app.route("/jobs/<int:job_id>/delete", methods=["POST"])
def delete_job(job_id):
    if db.get_job(job_id) is None:
        abort(404)
    db.delete_job(job_id)
    flash("Job deleted.", "success")
    return redirect(url_for("jobs"))


# ------------------------------------------------------------ applications

APP_STATUSES = ["Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn"]
INTERVIEW_TYPES = ["Phone", "Video", "On-site", "Other"]


def application_form_data():
    """Dropdown choices needed by the application form."""
    return {"jobs": db.get_jobs(), "statuses": APP_STATUSES, "interview_types": INTERVIEW_TYPES}


def flatten_application(a):
    """Copy the interview JSON into plain form fields so the edit form can fill them."""
    info = a.get("interview_data") or {}
    flat = dict(a)
    flat["interview_date"] = info.get("date") or ""
    flat["interview_type"] = info.get("type") or ""
    flat["interview_notes"] = info.get("notes") or ""
    return flat


def validate_application(form):
    """Return an error message, or None if the form is OK."""
    job_id = form.get("job_id", "")
    if not job_id.isdigit() or db.get_job(int(job_id)) is None:
        return "Please choose a job."

    applied = form.get("application_date", "").strip()
    if not applied:
        return "Application date is required."
    if not valid_date(applied):
        return "Application date must be a valid date."

    if form.get("status") not in APP_STATUSES:
        return "Please choose a status."
    if len(form.get("resume_version", "").strip()) > 50:
        return "Resume version must be 50 characters or less."

    interview_date = form.get("interview_date", "").strip()
    if interview_date and not valid_date(interview_date):
        return "Interview date must be a valid date."
    interview_type = form.get("interview_type", "").strip()
    if interview_type and interview_type not in INTERVIEW_TYPES:
        return "Please choose a valid interview type."
    if len(form.get("interview_notes", "").strip()) > 1000:
        return "Interview notes must be 1000 characters or less."
    return None


@app.route("/applications")
def applications():
    selected = request.args.get("status", "")
    rows = db.get_applications()
    if selected in APP_STATUSES:
        rows = [a for a in rows if a["status"] == selected]
    else:
        selected = ""
    return render_template("applications.html", applications=rows,
                           statuses=APP_STATUSES, selected=selected)


@app.route("/applications/<int:application_id>")
def application_detail(application_id):
    application = db.get_application(application_id)
    if application is None:
        abort(404)
    return render_template("application_detail.html", application=application,
                           interview=application["interview_data"] or {})


@app.route("/applications/add", methods=["GET", "POST"])
def add_application():
    if request.method == "POST":
        error = validate_application(request.form)
        if error:
            flash(error, "error")
            return render_template("application_form.html", application=request.form,
                                   mode="add", **application_form_data())
        db.add_application(request.form)
        flash("Application added.", "success")
        return redirect(url_for("applications"))
    defaults = {"status": "Applied", "application_date": date.today().isoformat()}
    return render_template("application_form.html", application=defaults,
                           mode="add", **application_form_data())


@app.route("/applications/<int:application_id>/edit", methods=["GET", "POST"])
def edit_application(application_id):
    application = db.get_application(application_id)
    if application is None:
        abort(404)
    if request.method == "POST":
        error = validate_application(request.form)
        if error:
            flash(error, "error")
            return render_template("application_form.html", application=request.form,
                                   mode="edit", application_id=application_id,
                                   **application_form_data())
        db.update_application(application_id, request.form)
        flash("Application updated.", "success")
        return redirect(url_for("applications"))
    return render_template("application_form.html", application=flatten_application(application),
                           mode="edit", application_id=application_id, **application_form_data())


@app.route("/applications/<int:application_id>/delete", methods=["POST"])
def delete_application(application_id):
    if db.get_application(application_id) is None:
        abort(404)
    db.delete_application(application_id)
    flash("Application deleted.", "success")
    return redirect(url_for("applications"))


# ------------------------------------------------------------------ contacts

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^[0-9+\-().\s]+$")


def validate_contact(form):
    """Return an error message, or None if the form is OK."""
    name = form.get("contact_name", "").strip()
    if not name:
        return "Contact name is required."
    if len(name) > 100:
        return "Contact name must be 100 characters or less."

    company_id = form.get("company_id", "")
    if not company_id.isdigit() or db.get_company(int(company_id)) is None:
        return "Please choose a company."

    if len(form.get("title", "").strip()) > 100:
        return "Title must be 100 characters or less."

    email = form.get("email", "").strip()
    if email and (len(email) > 100 or not EMAIL_PATTERN.match(email)):
        return "Please enter a valid email address."

    phone = form.get("phone", "").strip()
    if phone and (len(phone) > 20 or not PHONE_PATTERN.match(phone)):
        return "Phone must be 20 characters or less and use only numbers, spaces, + - ( )."

    linkedin = form.get("linkedin_url", "").strip()
    if linkedin and (len(linkedin) > 200 or not linkedin.lower().startswith(("http://", "https://"))):
        return "LinkedIn URL must start with http:// or https:// (200 characters max)."
    return None


@app.route("/contacts")
def contacts():
    return render_template("contacts.html", contacts=db.get_contacts())


@app.route("/contacts/<int:contact_id>")
def contact_detail(contact_id):
    contact = db.get_contact(contact_id)
    if contact is None:
        abort(404)
    return render_template("contact_detail.html", contact=contact)


@app.route("/contacts/add", methods=["GET", "POST"])
def add_contact():
    companies_list = db.get_companies()
    if request.method == "POST":
        error = validate_contact(request.form)
        if error:
            flash(error, "error")
            return render_template("contact_form.html", contact=request.form, mode="add",
                                   companies=companies_list)
        db.add_contact(request.form)
        flash("Contact added.", "success")
        return redirect(url_for("contacts"))
    return render_template("contact_form.html", contact={}, mode="add", companies=companies_list)


@app.route("/contacts/<int:contact_id>/edit", methods=["GET", "POST"])
def edit_contact(contact_id):
    contact = db.get_contact(contact_id)
    if contact is None:
        abort(404)
    companies_list = db.get_companies()
    if request.method == "POST":
        error = validate_contact(request.form)
        if error:
            flash(error, "error")
            return render_template("contact_form.html", contact=request.form, mode="edit",
                                   contact_id=contact_id, companies=companies_list)
        db.update_contact(contact_id, request.form)
        flash("Contact updated.", "success")
        return redirect(url_for("contacts"))
    return render_template("contact_form.html", contact=contact, mode="edit",
                           contact_id=contact_id, companies=companies_list)


@app.route("/contacts/<int:contact_id>/delete", methods=["POST"])
def delete_contact(contact_id):
    if db.get_contact(contact_id) is None:
        abort(404)
    db.delete_contact(contact_id)
    flash("Contact deleted.", "success")
    return redirect(url_for("contacts"))


# ----------------------------------------------------------------- job match

def normalize_skill(text):
    """'  Python ' and 'python' count as the same skill."""
    return " ".join(text.lower().split())


def parse_skills(text):
    """'Python, sql, python' -> {'python': 'Python', 'sql': 'sql'} (no duplicates)."""
    skills = {}
    for part in text.split(","):
        key = normalize_skill(part)
        if key and key not in skills:
            skills[key] = part.strip()
    return skills


def match_jobs(user_skills):
    """
    Compare the user's skills with every job's required skills.
    Returns one result per job, best match first.
    percent = matched skills / required skills * 100
    """
    results = []
    for job in db.get_jobs():
        required = {}
        for skill in job["requirements"]:
            required.setdefault(normalize_skill(skill), skill)

        matched = [name for key, name in required.items() if key in user_skills]
        missing = [name for key, name in required.items() if key not in user_skills]

        if required:
            percent = round(100 * len(matched) / len(required))
            if missing:
                percent = min(percent, 99)   # never show 100% unless nothing is missing
        else:
            percent = 0

        results.append({"job": job, "percent": percent, "matched": matched,
                        "missing": missing, "no_skills": not required})

    results.sort(key=lambda r: (-r["percent"], -len(r["matched"]), r["no_skills"],
                                r["job"]["job_title"].lower()))
    return results


@app.route("/job-match")
def job_match():
    text = request.args.get("skills", "")
    searched = "skills" in request.args
    results = []
    user_skills = {}

    if searched:
        user_skills = parse_skills(text)
        if len(text) > 500:
            flash("Please enter 500 characters or less.", "error")
        elif not user_skills:
            flash("Please enter at least one skill, separated by commas.", "error")
        else:
            results = match_jobs(user_skills)

    return render_template("job_match.html", skills_text=text, searched=searched,
                           user_skills=list(user_skills.values()), results=results)


# ------------------------------------------------------------------ 404 page

@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", message="Page not found."), 404


if __name__ == "__main__":
    app.run(debug=True)
