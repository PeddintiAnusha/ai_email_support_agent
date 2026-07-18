# AI Email Support Agent

An AI-powered customer support tool that reads incoming customer emails, detects
sentiment/priority/category/spam, and generates professional reply drafts that a
support agent can review, edit, and send.

## Features
- Register / Login / Logout (secure password hashing, sessions via Flask-Login)
- Inbox with search, filters (status, category, priority), and pagination
- Compose & send emails, delete emails, mark important
- "Simulate Inbound Email" page — paste a sample customer email to see the AI
  pipeline run automatically (sentiment, category, spam, priority, summary)
- AI Reply page: generate a draft reply, edit it, then send
- Dashboard with inbox/sent/pending/urgent counts
- Works **out of the box with no API key** (rule-based fallback AI). Add an
  OpenAI key to switch to real LLM-generated replies.

## 1. Requirements
- Python 3.10+
- pip

## 2. Setup

```bash
# 1. Go into the project folder
cd AI_Email_Support_Agent

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## 3. Configuration (optional)

Create a `.env` file in the project root if you want to use a real LLM instead
of the built-in rule-based fallback:

```
SECRET_KEY=some-random-secret-string
OPENAI_API_KEY=sk-...........................
OPENAI_MODEL=gpt-4o-mini
```

If you skip this step, the app still runs fully — `services/ai_service.py`
automatically detects the missing key and uses a keyword/rule-based engine
for replies, summaries, sentiment, spam detection, classification, and
priority, so you can demo the whole workflow with zero cost/setup.

## 4. Run the app

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

The first time it runs, `app.py` automatically calls `db.create_all()`, which
creates any missing tables in `database/database.db`. A ready-made empty
database (with the schema already applied) is already included in this
project, so you can also just register a user and start immediately.

## 5. Where is the database?

`database/database.db` — a single-file **SQLite** database (chosen so the
project runs with zero external setup; the project also lists MySQL in the
original design and you can swap it in later, see below).

It contains 4 tables:

| Table         | Purpose                                        |
|---------------|-------------------------------------------------|
| `users`       | registered agents/admins (name, email, password hash) |
| `emails`      | inbound + outbound emails, with AI-assigned category/priority/sentiment/spam flag |
| `ai_replies`  | AI-generated draft replies + agent-edited version, per email |
| `feedback`    | optional agent rating/comments on AI reply quality |

You can inspect it any time with:

```bash
python -c "import sqlite3; c=sqlite3.connect('database/database.db'); print(c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall())"
```

or open it with a GUI tool like **DB Browser for SQLite**.

### Switching to MySQL later (as in the original tech stack)
1. `pip install pymysql`
2. In `.env` set:
   `DATABASE_URL=mysql+pymysql://user:password@localhost/ai_email_agent`
3. Restart the app — SQLAlchemy will create the tables in MySQL instead.

## 6. Typical demo flow
1. Register a new account → Login
2. Go to **Simulate Inbound Email** → paste a sample angry/refund/complaint
   email → AI tags it with category/priority/sentiment automatically
3. Open the email → click **Generate AI Reply** → edit if needed → **Send Reply**
4. Check **Dashboard** for updated counts, and **History** for sent replies

## 7. Project structure
```
AI_Email_Support_Agent/
├── app.py                 # Flask app factory, blueprint registration
├── config.py              # Config (DB URI, secret key, AI settings)
├── requirements.txt
├── database/database.db   # SQLite database file
├── models/                # SQLAlchemy models (User, Email, AIReply, Feedback)
├── routes/                # Blueprints: auth.py, email.py, ai.py
├── services/              # Business logic: email_service.py, ai_service.py
├── utils/helpers.py       # Validation + small helpers
├── static/                # css/js/images
├── templates/             # Jinja2 + Bootstrap 5 templates
├── uploads/                # Reserved for future attachment support
└── tests/                 # Unit tests
```

## 8. Deployment
The app is ready for Render/Railway/PythonAnywhere:
- Start command: `gunicorn app:app`
- Set `SECRET_KEY`, `OPENAI_API_KEY` (optional), and `DATABASE_URL` as
  environment variables.
