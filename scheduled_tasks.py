{\rtf1\ansi\ansicpg1252\cocoartf2821
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fnil\fcharset0 .AppleSystemUIFontMonospaced-Regular;}
{\colortbl;\red255\green255\blue255;\red255\green255\blue255;\red25\green27\blue29;}
{\*\expandedcolortbl;;\cssrgb\c100000\c100000\c100000;\cssrgb\c12941\c14118\c15294;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\deftab720
\pard\pardeftab720\partightenfactor0

\f0\fs32 \cf2 \cb3 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 import os\
from datetime import datetime\
from flask import Flask\
from models import (\
    db,\
    Course,\
    Participant,\
    CustomQuestion,\
    ParticipantAnswer,\
    HotelRequest,\
    ReminderTracking,\
)\
from email_utils import (\
    send_rsvp_reminder,\
    send_info_reminder,\
    send_hotel_reminder,\
    send_hotel_final_email,\
)\
\
app = Flask(__name__)\
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key")\
db_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")\
if db_url.startswith("postgres://"):\
    db_url = db_url.replace("postgres://", "postgresql://", 1)\
app.config["SQLALCHEMY_DATABASE_URI"] = db_url\
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False\
db.init_app(app)\
\
\
def missing_required_info(participant):\
    questions = CustomQuestion.query.filter_by(\
        course_id=participant.course_id, required=True\
    )\
    answers = \{\
        a.question_id: a.answer_text\
        for a in ParticipantAnswer.query.filter_by(participant_id=participant.id).all()\
    \}\
    for q in questions:\
        if not answers.get(q.id, "").strip():\
            return True\
    return False\
\
\
def hotel_missing(participant):\
    hr = participant.hotel_request\
    if not hr or hr.need_hotel is None:\
        return True\
    return False\
\
\
with app.app_context():\
    print("Running scheduled tasks at", datetime.utcnow())\
\
    # 1. RSVP reminders (up to 4)\
    invited = Participant.query.filter_by(\
        status="INVITED", attending_responded=False\
    ).all()\
    for p in invited:\
        send_rsvp_reminder(p)\
\
    # 2. Info form reminders (up to 4)\
    confirmed = Participant.query.filter_by(status="CONFIRMED").all()\
    for p in confirmed:\
        if missing_required_info(p):\
            send_info_reminder(p)\
\
    # 3. Hotel reminders (up to 4 + final)\
    for p in confirmed:\
        hr = p.hotel_request\
        if hotel_missing(p):\
            send_hotel_reminder(p)\
\
    # Final hotel email for those who hit 4 hotel reminders and still no need_hotel\
    for p in confirmed:\
        hr = p.hotel_request\
        r = ReminderTracking.query.filter_by(participant_id=p.id, type="HOTEL").first()\
        if r and r.count_sent >= 4 and (not hr or hr.need_hotel is None):\
            send_hotel_final_email(p)\
            if hr:\
                hr.finalized = True\
                db.session.commit()}