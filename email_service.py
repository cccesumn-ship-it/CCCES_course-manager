from flask import url_for
from flask_mail import Mail, Message
from datetime import datetime
from utils import render_email_template

mail = Mail()


def send_email(recipient, subject, html_body):
    """Send email via Gmail"""
    try:
        msg = Message(
            subject=subject,
            recipients=[recipient],
            html=html_body
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email to {recipient}: {e}")
        return False


def send_rsvp_email(person, course):
    """Send initial RSVP email"""
    yes_link = url_for('rsvp_response', token=person.token, response='yes', _external=True)
    no_link = url_for('rsvp_response', token=person.token, response='no', _external=True)
    
    variables = {
        'first_name': person.first_name or 'there',
        'last_name': person.last_name or '',
        'course_name': course.name,
        'start_date': course.start_date.strftime('%B %d, %Y'),
        'end_date': course.end_date.strftime('%B %d, %Y'),
        'yes_link': yes_link,
        'no_link': no_link
    }
    
    subject, html_body = render_email_template('rsvp_invitation', variables)
    return send_email(person.email, subject, html_body)


def send_info_form_email(person, course):
    """Send link to info form"""
    form_link = url_for('info_form', token=person.token, _external=True)
    
    variables = {
        'first_name': person.first_name or 'there',
        'last_name': person.last_name or '',
        'course_name': course.name,
        'form_link': form_link
    }
    
    subject, html_body = render_email_template('info_form_request', variables)
    return send_email(person.email, subject, html_body)


def send_info_reminder_email(person, course, reminder_number):
    """Send reminder to complete info form"""
    form_link = url_for('info_form', token=person.token, _external=True)
    
    variables = {
        'first_name': person.first_name or 'there',
        'last_name': person.last_name or '',
        'course_name': course.name,
        'form_link': form_link,
        'reminder_number': reminder_number
    }
    
    subject, html_body = render_email_template('info_reminder', variables)
    return send_email(person.email, subject, html_body)


def send_hotel_request_email(person, course):
    """Send hotel request form link"""
    hotel_link = url_for('hotel_form', token=person.token, _external=True)
    
    variables = {
        'first_name': person.first_name or 'there',
        'last_name': person.last_name or '',
        'course_name': course.name,
        'hotel_link': hotel_link,
        'night1_date': course.hotel_night1.strftime('%B %d, %Y') if course.hotel_night1 else 'TBD',
        'night2_date': course.hotel_night2.strftime('%B %d, %Y') if course.hotel_night2 else 'TBD',
        'night3_date': course.hotel_night3.strftime('%B %d, %Y') if course.hotel_night3 else 'TBD'
    }
    
    subject, html_body = render_email_template('hotel_request', variables)
    return send_email(person.email, subject, html_body)


def send_hotel_reminder_email(person, course, reminder_number):
    """Send reminder for hotel request"""
    hotel_link = url_for('hotel_form', token=person.token, _external=True)
    
    variables = {
        'first_name': person.first_name or 'there',
        'last_name': person.last_name or '',
        'course_name': course.name,
        'hotel_link': hotel_link,
        'reminder_number': reminder_number
    }
    
    subject, html_body = render_email_template('hotel_reminder', variables)
    return send_email(person.email, subject, html_body)


def send_hotel_final_notice_email(person, course):
    """Send final notice - no hotel will be booked"""
    variables = {
        'first_name': person.first_name or 'there',
        'last_name': person.last_name or '',
        'course_name': course.name
    }
    
    subject, html_body = render_email_template('hotel_final_notice', variables)
    return send_email(person.email, subject, html_body)


def send_file_upload_notification(person, files, admin_email):
    """Send uploaded files notification to admin email"""
    subject = f"{person.last_name}, {person.first_name} - Files"
    
    file_list_html = '<ul>' + ''.join([f"<li>{f.original_filename} ({f.file_size / 1024:.1f} KB)</li>" for f in files]) + '</ul>'
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #6c757d; color: white; padding: 20px; text-align: center; }}
            .content {{ background: #f9f9f9; padding: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📎 Files Uploaded</h1>
            </div>
            <div class="content">
                <h2>{person.last_name}, {person.first_name}</h2>
                <p><strong>Email:</strong> {person.email}</p>
                <p><strong>Role:</strong> {person.role}</p>
                <p><strong>Course:</strong> {person.course.name}</p>
                
                <p><strong>Files uploaded:</strong></p>
                {file_list_html}
                
                <p style="color: #666; font-size: 14px;">
                    Files are stored in the uploads folder and can be accessed from the admin panel.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(admin_email, subject, html_body)


def send_bulk_rsvp_emails(persons, course):
    """Send RSVP emails to multiple persons"""
    results = {'success': 0, 'failed': 0, 'errors': []}
    
    for person in persons:
        try:
            if send_rsvp_email(person, course):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f"{person.email}: Email send failed")
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"{person.email}: {str(e)}")
    
    return results


def send_bulk_info_form_emails(persons, course):
    """Send info form emails to multiple persons"""
    results = {'success': 0, 'failed': 0, 'errors': []}
    
    for person in persons:
        try:
            if send_info_form_email(person, course):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f"{person.email}: Email send failed")
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"{person.email}: {str(e)}")
    
    return results


def send_bulk_hotel_request_emails(persons, course):
    """Send hotel request emails to multiple persons"""
    results = {'success': 0, 'failed': 0, 'errors': []}
    
    for person in persons:
        try:
            if send_hotel_request_email(person, course):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f"{person.email}: Email send failed")
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"{person.email}: {str(e)}")
    
    return results


def process_info_reminders(course):
    """
    Process and send info form reminders for persons who haven't completed
    Returns dict with reminder statistics
    """
    from models import db, Person
    from datetime import datetime, timedelta
    from config import Config
    
    results = {
        'reminders_sent': 0,
        'max_reminders_reached': 0,
        'errors': []
    }
    
    # Get persons who are attending but haven't completed info
    persons = Person.query.filter_by(
        course_id=course.id,
        status='ATTENDING',
        info_completed=False
    ).all()
    
    now = datetime.utcnow()
    reminder_interval = timedelta(days=Config.REMINDER_INTERVAL_DAYS)
    
    for person in persons:
        # Check if reminder is due
        if person.info_last_reminder_sent:
            time_since_last = now - person.info_last_reminder_sent
            if time_since_last < reminder_interval:
                continue  # Not time yet
        
        # Check if max reminders reached
        if person.info_reminder_count >= Config.MAX_INFO_REMINDERS:
            results['max_reminders_reached'] += 1
            continue
        
        # Send reminder
        try:
            reminder_number = person.info_reminder_count + 1
            if send_info_reminder_email(person, course, reminder_number):
                person.info_reminder_count = reminder_number
                person.info_last_reminder_sent = now
                db.session.commit()
                results['reminders_sent'] += 1
            else:
                results['errors'].append(f"{person.email}: Failed to send")
        except Exception as e:
            results['errors'].append(f"{person.email}: {str(e)}")
    
    return results


def process_hotel_reminders(course):
    """
    Process and send hotel request reminders
    Returns dict with reminder statistics
    """
    from models import db, Person, HotelRequest
    from datetime import datetime, timedelta
    from config import Config
    
    results = {
        'reminders_sent': 0,
        'final_notices_sent': 0,
        'errors': []
    }
    
    # Get persons who are attending but haven't completed hotel request
    persons = Person.query.filter_by(
        course_id=course.id,
        status='ATTENDING'
    ).all()
    
    now = datetime.utcnow()
    reminder_interval = timedelta(days=Config.REMINDER_INTERVAL_DAYS)
    
    for person in persons:
        # Check if hotel request exists and is not completed
        hotel = person.hotel_request
        
        if not hotel or hotel.completed:
            continue
        
        # Check if final notice already sent
        if hotel.final_notice_sent:
            continue
        
        # Check if reminder is due
        if hotel.last_reminder_sent:
            time_since_last = now - hotel.last_reminder_sent
            if time_since_last < reminder_interval:
                continue  # Not time yet
        
        # Check if max reminders reached - send final notice
        if hotel.reminder_count >= Config.MAX_HOTEL_REMINDERS:
            try:
                if send_hotel_final_notice_email(person, course):
                    hotel.final_notice_sent = True
                    db.session.commit()
                    results['final_notices_sent'] += 1
                else:
                    results['errors'].append(f"{person.email}: Failed to send final notice")
            except Exception as e:
                results['errors'].append(f"{person.email}: {str(e)}")
            continue
        
        # Send reminder
        try:
            reminder_number = hotel.reminder_count + 1
            if send_hotel_reminder_email(person, course, reminder_number):
                hotel.reminder_count = reminder_number
                hotel.last_reminder_sent = now
                db.session.commit()
                results['reminders_sent'] += 1
            else:
                results['errors'].append(f"{person.email}: Failed to send reminder")
        except Exception as e:
            results['errors'].append(f"{person.email}: {str(e)}")
    
    return results
