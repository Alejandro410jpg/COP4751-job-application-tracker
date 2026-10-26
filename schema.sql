-- Job Application Tracker - database creation script
-- Run with: mysql -u root -p < schema.sql

DROP DATABASE IF EXISTS job_tracker;
CREATE DATABASE job_tracker;
USE job_tracker;

-- 1. companies
CREATE TABLE companies (
    company_id   INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    industry     VARCHAR(50),
    website      VARCHAR(200),
    city         VARCHAR(50),
    state        VARCHAR(50),
    notes        TEXT
);

-- 2. jobs (each job belongs to one company)
CREATE TABLE jobs (
    job_id       INT PRIMARY KEY AUTO_INCREMENT,
    company_id   INT NOT NULL,
    job_title    VARCHAR(100) NOT NULL,
    job_type     ENUM('Full-time','Part-time','Contract','Internship') DEFAULT 'Full-time',
    salary_min   INT,
    salary_max   INT,
    job_url      VARCHAR(300),
    date_posted  DATE,
    requirements JSON,  -- example: ["Python", "SQL", "Flask"]
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON DELETE CASCADE
);

-- 3. applications (each application is for one job)
CREATE TABLE applications (
    application_id    INT PRIMARY KEY AUTO_INCREMENT,
    job_id            INT NOT NULL,
    application_date  DATE NOT NULL,
    status            ENUM('Applied','Screening','Interview','Offer','Rejected','Withdrawn') DEFAULT 'Applied',
    resume_version    VARCHAR(50),
    cover_letter_sent BOOLEAN DEFAULT FALSE,
    interview_data    JSON,  -- example: {"date": "2026-11-05", "type": "Phone", "notes": "..."}
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        ON DELETE CASCADE
);

-- 4. contacts (each contact works at one company)
CREATE TABLE contacts (
    contact_id   INT PRIMARY KEY AUTO_INCREMENT,
    company_id   INT NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    title        VARCHAR(100),
    email        VARCHAR(100),
    phone        VARCHAR(20),
    linkedin_url VARCHAR(200),
    notes        TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON DELETE CASCADE
);

-- ---------- Sample data ----------

INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES
('TechCorp',  'Software',   'https://www.techcorp.example',  'Miami',   'Florida', 'Great remote policy.'),
('DataCo',    'Analytics',  'https://www.dataco.example',    'Orlando', 'Florida', 'Met recruiter at career fair.'),
('CloudNine', 'Cloud',      'https://www.cloudnine.example', 'Tampa',   'Florida', NULL);

INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1, 'Software Developer', 'Full-time', 70000, 95000, 'https://www.techcorp.example/jobs/1', '2026-10-01', JSON_ARRAY('Python','SQL','Flask')),
(2, 'Data Analyst',       'Full-time', 60000, 80000, 'https://www.dataco.example/jobs/7',    '2026-10-05', JSON_ARRAY('Python','SQL','Tableau')),
(3, 'Cloud Intern',       'Internship', 20000, 30000, 'https://www.cloudnine.example/jobs/3', '2026-10-10', JSON_ARRAY('Linux','AWS','Python'));

INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1, '2026-10-12', 'Interview', 'v2-software', TRUE,  JSON_OBJECT('date','2026-11-05','type','Phone','notes','Prepare Flask questions')),
(2, '2026-10-15', 'Applied',   'v1-data',     FALSE, NULL),
(3, '2026-10-18', 'Screening', 'v2-software', TRUE,  NULL);

INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(1, 'Maria Lopez', 'Tech Recruiter',   'maria@techcorp.example', '305-555-0101', 'https://linkedin.com/in/marialopez-example', 'Sent follow-up email.'),
(2, 'James Carter', 'Hiring Manager',  'james@dataco.example',   '407-555-0102', NULL, NULL);
