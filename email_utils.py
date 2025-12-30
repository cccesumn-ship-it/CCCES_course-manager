import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta
from models import db, Participant, ReminderTracking

BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
FILES_EMAIL_ADDRESS = os.environ.get("FILES_EMAIL_ADDRESS", GMAIL_ADDRESS)

serializer = URLSafeTimedSerializer(SECRET_KEY)


def make_token(participant_id):
    """Generate secure token for participant"""
    return serializer.dumps(participant_id, salt="participant")


def decode_token(token, max_age=7776000):
    """Decode token (90 days expiry)"""
    return serializer.loads(token, salt="participant", max_age=max_age)


def send_email(to_email, subject, html_content, attachments=None):
    """Send email via Gmail SMTP"""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print(f"[NO EMAIL CONFIG] Would send to {to_email}: {subject}")
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))
        
        if attachments:
            for filename, file_data in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file_data)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={filename}')
                msg.attach(part)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"✓ Sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"✗ Failed to {to_email}: {e}")
        return False


def send_initial_rsvp_email(participant):
    """Send initial RSVP invitation"""
    token = make_token(participant.id)
    yes_link = f"{BASE_URL}/rsvp/{token}?answer=yes"
    no_link = f"{BASE_URL}/rsvp/{token}?answer=no"
    subject = f"RSVP: {participant.course.name}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #0066cc;">Course Invitation</h2>
        <p>Dear {participant.first_name or 'Participant'},</p>
        <p>You are invited to attend <strong>{participant.course.name}</strong>.</p>
        <p><strong>Dates:</strong> {