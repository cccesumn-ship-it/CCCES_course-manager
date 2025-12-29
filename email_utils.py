{\rtf1\ansi\ansicpg1252\cocoartf2821
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fnil\fcharset0 .AppleSystemUIFontMonospaced-Regular;}
{\colortbl;\red255\green255\blue255;\red255\green255\blue255;\red25\green27\blue29;}
{\*\expandedcolortbl;;\cssrgb\c100000\c100000\c100000;\cssrgb\c12941\c14118\c15294;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\deftab720
\pard\pardeftab720\partightenfactor0

\f0\fs32 \cf2 \cb3 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 import os\
from sendgrid import SendGridAPIClient\
from sendgrid.helpers.mail import Mail\
from itsdangerous import URLSafeTimedSerializer\
from datetime import datetime, timedelta\
from models import db, Participant, ReminderTracking\
\
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")\
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")\
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")\
\
serializer = URLSafeTimedSerializer(SECRET_KEY)\
\
\
def send_email(to_email, subject, html_content):\
    # If no API key present, just log to console\
    if not SENDGRID_API_KEY:\
        print(f"[DEV] Would send email to \{to_email\}: \{subject\}")\
        print(html_content)\
        return\
\
    message = Mail(\
        from_email="no-reply@example.com",  # change if you wish\
        to_emails=to_email,\
        subject=subject,\
        html_content=html_content,\
    )\
    try:\
        sg = SendGridAPIClient(SENDGRID_API_KEY)\
        sg.send(message)\
    except Exception as e:\
        print("Error sending email:", e)\
\
\
def make_token(participant_id):\
    return serializer.dumps(\{"pid": participant_id\})\
\
\
def decode_token(token, max_age_days=60):\
    data = serializer.loads(token, max_age=60 * 60 * 24 * max_age_days)\
    return data["pid"]\
\
\
def get_or_create_reminder(participant_id, rtype, max_allowed=4):\
    r = ReminderTracking.query.filter_by(participant_id=participant_id, type=rtype).first()\
    if not r:\
        r = ReminderTracking(\
            participant_id=participant_id,\
            type=rtype,\
            count_sent=0,\
            max_allowed=max_allowed,\
        )\
        db.session.add(r)\
        db.session.commit()\
    return r\
\
\
def can_send_reminder(reminder, min_days_between=7):\
    if reminder.count_sent >= reminder.max_allowed:\
        return False\
    if reminder.last_sent_at is None:\
        return True\
    return datetime.utcnow() - reminder.last_sent_at >= timedelta(days=min_days_between)\
\
\
# ---- Specific emails ----\
\
def send_initial_rsvp_email(participant):\
    token = make_token(participant.id)\
    yes_url = f"\{BASE_URL\}/rsvp/\{token\}?answer=yes"\
    no_url = f"\{BASE_URL\}/rsvp/\{token\}?answer=no"\
    html = f"""\
    <p>Dear \{participant.first_name or ''\} \{participant.last_name or ''\},</p>\
    <p>You are invited to the course <b>\{participant.course.name\}</b>.</p>\
    <p>Please confirm if you will attend:</p>\
    <p>\
      <a href="\{yes_url\}">Yes, I will attend</a><br>\
      <a href="\{no_url\}">No, I cannot attend</a>\
    </p>\
    """\
    send_email(participant.email, "Course attendance confirmation", html)\
\
\
def send_rsvp_reminder(participant):\
    r = get_or_create_reminder(participant.id, "RSVP", max_allowed=4)\
    if not can_send_reminder(r):\
        return\
    send_initial_rsvp_email(participant)\
    r.count_sent += 1\
    r.last_sent_at = datetime.utcnow()\
    db.session.commit()\
\
\
def send_info_form_email(participant):\
    token = make_token(participant.id)\
    url = f"\{BASE_URL\}/info-form/\{token\}"\
    html = f"""\
    <p>Dear \{participant.first_name or ''\} \{participant.last_name or ''\},</p>\
    <p>Thank you for confirming your attendance for <b>\{participant.course.name\}</b>.</p>\
    <p>Please complete your information here:</p>\
    <p><a href="\{url\}">Fill in your details</a></p>\
    """\
    send_email(participant.email, "Course information form", html)\
\
\
def send_info_reminder(participant):\
    r = get_or_create_reminder(participant.id, "INFO", max_allowed=4)\
    if not can_send_reminder(r):\
        return\
    send_info_form_email(participant)\
    r.count_sent += 1\
    r.last_sent_at = datetime.utcnow()\
    db.session.commit()\
\
\
def send_hotel_form_email(participant):\
    token = make_token(participant.id)\
    url = f"\{BASE_URL\}/info-form/\{token\}#hotel"\
    html = f"""\
    <p>Dear \{participant.first_name or ''\} \{participant.last_name or ''\},</p>\
    <p>Please let us know if you need a hotel room for the course <b>\{participant.course.name\}</b>.</p>\
    <p><a href="\{url\}">Fill in your hotel details</a></p>\
    """\
    send_email(participant.email, "Hotel booking information", html)\
\
\
def send_hotel_reminder(participant):\
    r = get_or_create_reminder(participant.id, "HOTEL", max_allowed=4)\
    if not can_send_reminder(r):\
        return\
    send_hotel_form_email(participant)\
    r.count_sent += 1\
    r.last_sent_at = datetime.utcnow()\
    db.session.commit()\
\
\
def send_hotel_final_email(participant):\
    r = get_or_create_reminder(participant.id, "HOTEL_FINAL", max_allowed=1)\
    if not can_send_reminder(r, min_days_between=0):\
        return\
    html = f"""\
    <p>Dear \{participant.first_name or ''\} \{participant.last_name or ''\},</p>\
    <p>We did not receive your hotel room request in time, so we will not be able to book a hotel room for you.</p>\
    """\
    send_email(participant.email, "Hotel booking closed", html)\
    r.count_sent += 1\
    r.last_sent_at = datetime.utcnow()\
    db.session.commit()}