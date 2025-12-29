# Course Participant Manager\
\
A small Flask app to manage course participants, RSVP, information forms,\
hotel needs, reminders, and Excel exports.\
\
## Features\
\
- Upload participants (CSV/Excel)\
- Send Yes/No RSVP email (with up to 4 reminders)\
- Collect extra information via configurable questions\
- Ask about hotel room and nights; send reminders\
- Final "no hotel room will be booked" email after 4 missed reminders\
- Hotel summary by night and by night sequence pattern\
- Excel export of all participants and answers\
\
## Quick Run Locally\
\
```bash\
python -m venv venv\
source venv/bin/activate  # on Windows: venv\\Scripts\\activate\
pip install -r requirements.txt\
export SECRET_KEY="dev-key"\
export DATABASE_URL="sqlite:///local.db"\
export BASE_URL="http://localhost:5000"\
export ADMIN_PASSWORD="admin123"\
flask --app app run}