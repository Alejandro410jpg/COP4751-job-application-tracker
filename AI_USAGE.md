# AI Usage

## Tools used

| Tool | What I used it for |
| :---- | :---- |
| **Claude (Anthropic)** | Main AI tool. It wrote the code, the SQL, the HTML/CSS, the README, and tested the code. |
| **MySQL Workbench** | I ran `schema.sql` and created the app's database user myself. |
| **VS Code** | I ran the app and viewed the code. |
| **GitHub (website)** | I uploaded the files and made the commits myself. |

## How I worked

I gave Claude the two project documents (the specification and the guidelines) and asked it to build the project step by step. Each step it gave me files, I saved them in my project folder, ran them, and uploaded them to GitHub with a small commit.

The steps were:

1. `schema.sql` (4 tables and sample data)  
2. `database.py` (connection and all queries)  
3. `app.py` with the page layout and Companies  
4. Jobs  
5. Applications, Contacts, Dashboard, and Job Match, all at once (I asked for this to save time)  
6. README, requirements, and this file

## Main prompts

These are summaries of what I asked. They are not word for word.

1. "Read the 2 documents in this project and give me a simple 5 sentence summary of what we have to do and say the deliverables."  
2. "I want you to build the project step by step. What's the first thing you are going to build?"  
3. "Can you test this code to make sure it works." (after [`database.py`](http://database.py))  
4. Then I continued askinfg it to build the next step and test it  
5. Asked different short questions about setup: how to open the terminal, how to structure file, what does this part of the code mean, how to fix errors.

## What worked well

- **Step by step.** Small steps meant I could see each part work before moving on, and it gave me many small commits.  
- **Claude tested the code against a real database.** Before giving me files, Claude ran automated checks (about 170 in total) against a real MariaDB database, which is very close to MySQL. The checks covered add, view, edit, delete, validation, cascading deletes, the dashboard numbers, and the Job Match percentages.  
- **Screenshots.** Claude looked at screenshots of the pages and found visual problems I would have missed.  
- **Plain explanations.** When I got an error (for example, `mysql` or `pip` not recognized), Claude gave short fixes I could follow.

## Problems found and fixed

| Problem | How it was found | Fix |
| :---- | :---- | :---- |
| Delete confirmation popup would break for names with an apostrophe, like `O'Brien` | Claude's own test, which first checked too little | Claude changed the templates to build the popup text safely with Jinja's `tojson` |
| On Job Match, matched skills were not green and missing skills were not red | A screenshot showed all tags were blue | Claude fixed the CSS order (more specific selectors) |
| "You have:" label wrapped onto two lines | The same screenshot | Wider label with no wrapping |
| One test passed even when the company dropdown might not pre-select the right company | Claude noticed the test was too loose | Claude wrote an exact check |
| I forgot my MySQL root password | Running the schema from the command line failed | I ran the schema in Workbench instead, and created a separate `tracker` user for the app |
| `pip` and `mysql` were not found on my Windows computer | Errors in my terminal | I used `py -m pip` and the full path to `mysql.exe` |
| The app showed "Failed to load page" | My terminal had gone back to the prompt, so Flask had stopped | I ran `py app.py` again and left that terminal alone |

## What I decided myself

- Use **many small commits**, not one big one (Claude warned that the rubric gives points for good commits).  
- Keep the `CREATE USER` step **out of `schema.sql`** and put it in the README, so the script is safe to run on other computers.  
- Build the remaining features **all at once** to save time.

## What I changed or checked

- I ran the app on my own computer and clicked through the pages.  
- I uploaded each file to GitHub myself.  
- I created the MySQL user and ran the schema on my own MySQL 9.6.

## Lessons learned

- AI can write a lot of code quickly, but it must be **run and tested**. Claude could not run it on my computer, so setup problems (Python path, MySQL login) only showed up when I ran it.  
- **AI tests can be weak.** One of Claude's own tests was too loose, and a screenshot caught a visual bug that tests did not. Checking both the code and the page matters.  
- **Small steps make problems easy to find.** When something broke, I knew which step caused it.  
- **Keep secrets out of the code when possible.** The database login can be changed with environment variables, so it is not locked into the code.  
- I should understand the code I submit. Reading `database.py` and `app.py` helped me explain how the pages talk to the database.