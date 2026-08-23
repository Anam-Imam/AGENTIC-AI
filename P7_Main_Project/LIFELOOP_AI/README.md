# LIFELOOP AI — Project 7 Premium

This version keeps the original Prism Desk UI and adds a working long-term deadline reminder system.

## Main features

- Long-term memory in `data/memories.json`
- Local semantic memory in `data/chroma_store/`
- Evidence search and filters
- Risk radar, dependencies, people, timeline and recovery workflows
- Scenarios, decisions, approvals and memory versions
- CSV/JSON export
- Deadline field when adding memory
- Automatic date extraction from text such as `Submit work to Boss at 22 August, 2026`
- One-day-before email reminder
- In-app deadline notification when the Streamlit app is running
- Duplicate email protection in `data/reminder_history.json`
- Optional Windows Task Scheduler worker so email reminders work while Streamlit is closed

## 1. Install

Open a terminal in this folder:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configure email

Copy `.env.example` to `.env` and set:

```env
REMINDER_EMAIL=your_email@gmail.com
REMINDER_PASSWORD=your_google_app_password
REMINDER_TO=your_email@gmail.com
```

For Gmail, use a Google App Password, not your normal Gmail password.

## 3. Start LIFELOOP

```powershell
streamlit run app.py
```

## 4. Add a deadline

Open **Evidence Intelligence → ADD LONG-TERM MEMORY**.

Enter for example:

`I have to submit work to Boss at 22 August, 2026`

You can either:

- check **This memory has a deadline** and choose `22 August 2026`, or
- leave the date field disabled; LIFELOOP will automatically detect the date from the text.

Keep **Email reminder 1 day before** enabled.

## 5. Test email immediately

Go to **Settings → Deadline reminders → Send test email**.

If this fails, the message shown by LIFELOOP tells you what to fix.

## 6. Test the real deadline reminder without waiting

For a safe test, temporarily create a memory whose deadline is tomorrow. The reminder worker checks `today + 1 day`.

You can also run:

```powershell
python reminder_worker.py
```

It will check today's deadlines and report how many emails were sent.

## 7. Run reminders even when Streamlit is closed

Run `setup_reminder_task.bat` once. It creates a Windows Task Scheduler task that runs the reminder worker every day at 09:00.

If Windows blocks task creation, run the `.bat` as Administrator or create a daily Task Scheduler task manually with:

**Program:** your project's `.venv\Scripts\python.exe`

**Argument:** `reminder_worker.py`

**Start in:** your LIFELOOP project folder

## How the reminder works

```text
memory saved
    ↓
deadline stored
    ↓
daily reminder worker
    ↓
Is deadline tomorrow?
    ↓ yes
Is memory completed?
    ↓ no
Was reminder already sent?
    ↓ no
send email
    ↓
save reminder_history.json
```

The Streamlit app also performs the same check when it runs and shows an in-app warning for reminders sent during that run.
