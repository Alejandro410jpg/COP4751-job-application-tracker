"""
app.py - Flask application for the Job Application Tracker.
"""
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
    # The real dashboard comes in a later step.
    return redirect(url_for("companies"))


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


# ------------------------------------------------------------------ 404 page

@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", message="Page not found."), 404


if __name__ == "__main__":
    app.run(debug=True)
