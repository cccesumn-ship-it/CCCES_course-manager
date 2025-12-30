import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import url_for

# ============================================
# EMAIL CONFIGURATION
# ============================================

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = 'your-email@gmail.com'  # Change this
SENDER_PASSWORD = 'your-app-password'  # Change this (use App Password for Gmail)
SENDER_NAME = 'Course Manager'

# ============================================
# HELPER FUNCTION TO SEND EMAIL
# ============================================

def send_email(to_email, subject, html_content):
    """
    Generic function to send HTML emails
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'{SENDER_NAME} <{SENDER_EMAIL}>'
        msg['To'] = to_email
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent to {to_email}")
        return True
    
    except Exception as e:
        print(f"❌ Error sending email to {to_email}: {str(e)}")
        return False


# ============================================
# RSVP EMAIL
# ============================================

def send_rsvp_email(participant, course):
    """
    Send initial RSVP email to participant
    """
    yes_link = url_for('rsvp', token=participant.token, attending='yes', _external=True)
    no_link = url_for('rsvp', token=participant.token, attending='no', _external=True)
    
    subject = f"RSVP: {course.name}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; padding: 15px 30px; margin: 10px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; }}
            .btn-yes {{ background: #28a745; color: white; }}
            .btn-no {{ background: #dc3545; color: white; }}
            .info-box {{ background: white; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📅 Course Invitation</h1>
            </div>
            <div class="content">
                <h2>You're Invited to {course.name}</h2>
                
                <div class="info-box">
                    <p><strong>📅 Start Date:</strong> {course.start_date}</p>
                    <p><strong>📅 End Date:</strong> {course.end_date}</p>
                </div>
                
                <p>Please confirm your attendance by clicking one of the buttons below:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{yes_link}" class="button btn-yes">✅ Yes, I'll Attend</a>
                    <a href="{no_link}" class="button btn-no">❌ Can't Attend</a>
                </div>
                
                <p style="color: #666; font-size: 14px;">If you have any questions, please contact the course administrator.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(participant.email, subject, html_content)


# ============================================
# INFO FORM EMAIL
# ============================================

def send_info_form_email(participant, course):
    """
    Send email with link to complete information form
    """
    form_link = url_for('info_form', token=participant.token, _external=True)
    
    subject = f"Complete Your Information - {course.name}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; padding: 15px 30px; margin: 20px 0; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; background: #667eea; color: white; }}
            .info-box {{ background: white; padding: 20px; border-left: 4px solid #28a745; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ RSVP Confirmed!</h1>
            </div>
            <div class="content">
                <h2>Thank You for Confirming</h2>
                
                <div class="info-box">
                    <p><strong>Course:</strong> {course.name}</p>
                    <p><strong>📅 Dates:</strong> {course.start_date} to {course.end_date}</p>
                </div>
                
                <p>Please complete your registration by providing additional information:</p>
                
                <div style="text-align: center;">
                    <a href="{form_link}" class="button">📝 Complete Information Form</a>
                </div>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    <strong>Important:</strong> Please complete this form as soon as possible to finalize your registration.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(participant.email, subject, html_content)

# ============================================
# HOTEL FINALIZATION EMAIL
# ============================================

def send_hotel_finalization_email(participant, course):
    """
    Send email confirming hotel booking details
    """
    subject = f"Hotel Accommodation Confirmed - {course.name}"
    
    nights_list = []
    if participant.hotel_request:
        if participant.hotel_request.night1 and course.hotel_night1:
            nights_list
def send_hotel_finalization_email(participant, course):
    """
    Send email confirming hotel booking details
    """
    subject = f"Hotel Accommodation Confirmed - {course.name}"
    
    nights_list = []
    if participant.hotel_request:
        if participant.hotel_request.night1 and course.hotel_night1:
            nights_list.append(f"<li>{course.hotel_night1}</li>")
        if participant.hotel_request.night2 and course.hotel_night2:
            nights_list.append(f"<li>{course.hotel_night2}</li>")
        if participant.hotel_request.night3 and course.hotel_night3:
            nights_list.append(f"<li>{course.hotel_night3}</li>")
    
    nights_html = "<ul>" + "".join(nights_list) + "</ul>" if nights_list else "<p>No nights selected</p>"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .info-box {{ background: white; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0; }}
            ul {{ margin: 10px 0; padding-left: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏨 Hotel Accommodation Confirmed</h1>
            </div>
            <div class="content">
                <h2>Your Hotel Request Has Been Finalized</h2>
                
                <div class="info-box">
                    <p><strong>Course:</strong> {course.name}</p>
                    <p><strong>Participant:</strong> {participant.first_name} {participant.last_name}</p>
                </div>
                
                <h3>Requested Nights:</h3>
                {nights_html}
                
                <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <p style="margin: 0;"><strong>⚠️ Important:</strong> Your hotel preferences have been finalized and cannot be changed. If you need to make changes, please contact the course administrator immediately.</p>
                </div>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    You will receive further details about your hotel accommodation closer to the course date.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(participant.email, subject, html_content)


# ============================================
# FILE UPLOAD CONFIRMATION EMAIL (OPTIONAL)
# ============================================

def send_file_upload_email(participant, course, filename):
    """
    Send email confirming file upload
    """
    subject = f"File Uploaded Successfully - {course.name}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin
def send_file_upload_email(participant, course, filename):
    """
    Send email confirming file upload
    """
    subject = f"File Uploaded Successfully - {course.name}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .info-box {{ background: white; padding: 20px; border-left: 4px solid #28a745; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📎 File Upload Confirmed</h1>
            </div>
            <div class="content">
                <h2>Your File Has Been Uploaded Successfully</h2>
                
                <div class="info-box">
                    <p><strong>Course:</strong> {course.name}</p>
                    <p><strong>File:</strong> {filename}</p>
                    <p><strong>Uploaded by:</strong> {participant.first_name} {participant.last_name}</p>
                </div>
                
                <p>Your file has been received and stored securely. The course administrator will review it shortly.</p>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    If you need to upload additional files or have any questions, please contact the course administrator.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(participant.email, subject, html_content)