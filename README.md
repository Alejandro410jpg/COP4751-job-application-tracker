# Job Application Tracker

A web app for keeping track of a job search. Built for COP4751.

- **Database:** MySQL
- **Backend:** Python and Flask
- **Frontend:** HTML and CSS (Jinja templates)

## Features

- **Dashboard:** totals for each table, applications by status, upcoming interviews, recent applications.
- **Companies, Jobs, Applications, Contacts:** each one has add, view, edit, and delete. Delete always asks for confirmation.
- **Job Match:** type your skills and see every job ranked by match percentage, with the skills you have and the skills you are missing.
- **Validation:** forms check required fields, lengths, dates, numbers, emails, and links before saving.

## What you need first

1. **Python 3.9 or newer** (https://www.python.org/downloads/). On Windows, check "Add python.exe to PATH" when installing.
2. **MySQL 8 or newer** (tested with MySQL Workbench). The server must be running.

## Setup

### 1. Get the code

```
git clone https://github.com/Alejandro410jpg/COP4751-job-application-tracker.git
cd COP4751-job-application-tracker
```

### 2. Create the database

This creates the `job_tracker` database, the 4 tables, and sample data.

> **Warning:** `schema.sql` deletes any existing database named `job_tracker` and creates it again.

**Option A: command line**
```
mysql -u root -p < schema.sql
```

**Option B: MySQL Workbench**
Open `schema.sql` with **File > Open SQL Script**, then click the lightning bolt.

### 3. Give the app a MySQL login

The app logs in as user `tracker` with password `tracker123`. Create that user once. Run this in MySQL Workbench or the `mysql` command line:

```sql
CREATE USER 'tracker'@'localhost' IDENTIFIED BY 'tracker123';
GRANT ALL PRIVILEGES ON job_tracker.* TO 'tracker'@'localhost';
FLUSH PRIVILEGES;
```

**Prefer to use your own login (for example root)?** Skip the step above and set these before running the app instead.

Windows (Command Prompt):
```
set DB_USER=root
set DB_PASSWORD=your_password
```

Windows (PowerShell):
```
$env:DB_USER="root"
$env:DB_PASSWORD="your_password"
```

Mac or Linux:
```
export DB_USER=root
export DB_PASSWORD=your_password
```

Optional settings: `DB_HOST` (default `localhost`) and `DB_NAME` (default `job_tracker`).

### 4. Install the Python packages

```
pip install -r requirements.txt
```
If `pip` is not found on Windows, use `py -m pip install -r requirements.txt`.

### 5. Run the app

```
python app.py
```
If `python` is not found on Windows, use `py app.py`.

Open **http://127.0.0.1:5000** in your browser. To stop the app, press `Ctrl+C` in the terminal.

## Project files

| File or folder | What it is |
|---|---|
| `app.py` | Flask app: all routes, form validation, and Job Match logic |
| `database.py` | MySQL connection and all database functions |
| `schema.sql` | Creates the database, tables, and sample data |
| `templates/` | HTML pages (Jinja) |
| `static/style.css` | Styles |
| `requirements.txt` | Python packages |
| `AI_USAGE.md` | How AI tools were used on this project |

## Database

| Table | Main columns | Links to |
|---|---|---|
| `companies` | name, industry, website, city, state, notes | |
| `jobs` | title, type, salary range, URL, date posted, `requirements` (JSON list of skills) | `companies` |
| `applications` | date, status, resume version, cover letter sent, `interview_data` (JSON) | `jobs` |
| `contacts` | name, title, email, phone, LinkedIn, notes | `companies` |

Foreign keys use `ON DELETE CASCADE`. Deleting a company also deletes its jobs, contacts, and the applications for those jobs. Deleting a job deletes its applications.

## How Job Match works

1. You type skills separated by commas, for example `Python, SQL`.
2. Skills are compared ignoring upper and lower case and extra spaces.
3. For each job: **match % = skills you have / skills the job requires x 100**.
4. Jobs are shown from best match to worst. Each job lists the skills you have and the skills you are missing.
5. A job with no required skills shows 0% and is listed last.

## Troubleshooting

- **"Access denied for user" error page:** the MySQL login is wrong. Do step 3 again.
- **"Unknown database 'job_tracker'":** run `schema.sql` (step 2).
- **"Can't connect to MySQL server":** the MySQL server is not running. Start it, then refresh the page.
- **Page does not open:** make sure the terminal running `python app.py` is still open and has no error.
