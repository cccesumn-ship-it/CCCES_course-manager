import os
from werkzeug.utils import secure_filename
from config import Config
from datetime import datetime

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def generate_hotel_summary(course):
    """Generate hotel room summary for all 3 nights and sequences"""
    from models import Person, HotelRequest
    
    # Get all attending persons
    persons = Person.query.filter_by(
        course_id=course.id,
        status='ATTENDING'
    ).all()
    
    summary = {
        'night1': 0,
        'night2': 0,
        'night3': 0,
        'sequences': {
            'all_three': 0,           # Night 1, 2, 3
            'night1_2': 0,            # Night 1, 2
            'night2_3': 0,            # Night 2, 3
            'night1_3': 0,            # Night 1, 3
            'night1_only': 0,
            'night2_only': 0,
            'night3_only': 0,
            'no_hotel': 0
        },
        'by_role': {
            'PARTICIPANT': {
                'night1': 0,
                'night2': 0,
                'night3': 0
            },
            'FACULTY': {
                'night1': 0,
                'night2': 0,
                'night3': 0
            }
        }
    }
    
    for person in persons:
        hotel = person.hotel_request
        if hotel and hotel.need_hotel:
            # Count individual nights
            if hotel.night1:
                summary['night1'] += 1
                summary['by_role'][person.role]['night1'] += 1
            if hotel.night2:
                summary['night2'] += 1
                summary['by_role'][person.role]['night2'] += 1
            if hotel.night3:
                summary['night3'] += 1
                summary['by_role'][person.role]['night3'] += 1
            
            # Calculate sequences
            nights = (hotel.night1, hotel.night2, hotel.night3)
            if nights == (True, True, True):
                summary['sequences']['all_three'] += 1
            elif nights == (True, True, False):
                summary['sequences']['night1_2'] += 1
            elif nights == (False, True, True):
                summary['sequences']['night2_3'] += 1
            elif nights == (True, False, True):
                summary['sequences']['night1_3'] += 1
            elif nights == (True, False, False):
                summary['sequences']['night1_only'] += 1
            elif nights == (False, True, False):
                summary['sequences']['night2_only'] += 1
            elif nights == (False, False, True):
                summary['sequences']['night3_only'] += 1
        else:
            summary['sequences']['no_hotel'] += 1
    
    return summary


def export_to_excel(course, role_filter=None):
    """
    Export participant/faculty data to Excel
    role_filter: None (all), 'PARTICIPANT', or 'FACULTY'
    """
    import pandas as pd
    from io import BytesIO
    from models import Person, CustomQuestion, Answer
    
    # Get persons based on filter
    query = Person.query.filter_by(course_id=course.id)
    if role_filter:
        query = query.filter_by(role=role_filter)
    persons = query.all()
    
    # Get all questions
    questions = CustomQuestion.query.filter_by(
        course_id=course.id
    ).order_by(CustomQuestion.order).all()
    
     # Build data structure
    data = []
    for person in persons:
        row = {
            'Email': person.email,
            'First Name': person.first_name,
            'Last Name': person.last_name,
            'Role': person.role,
            'Status': person.status,
            'RSVP Responded': 'Yes' if person.attending_responded else 'No',
            'Info Completed': 'Yes' if person.info_completed else 'No',
            'Info Reminders Sent': person.info_reminder_count,
        }
        
        # Add custom question answers
        for question in questions:
            answer = Answer.query.filter_by(
                person_id=person.id,
                question_id=question.id
            ).first()
            row[question.label] = answer.answer_text if answer else ''
        
        # Add hotel info
        hotel = person.hotel_request
        if hotel:
            row['Needs Hotel'] = 'Yes' if hotel.need_hotel else 'No'
            row['Hotel Night 1'] = 'Yes' if hotel.night1 else 'No'
            row['Hotel Night 2'] = 'Yes' if hotel.night2 else 'No'
            row['Hotel Night 3'] = 'Yes' if hotel.night3 else 'No'
            row['Hotel Completed'] = 'Yes' if hotel.completed else 'No'
            row['Hotel Reminders Sent'] = hotel.reminder_count
            row['Hotel Final Notice'] = 'Yes' if hotel.final_notice_sent else 'No'
        else:
            row['Needs Hotel'] = 'Not Specified'
            row['Hotel Night 1'] = 'No'
            row['Hotel Night 2'] = 'No'
            row['Hotel Night 3'] = 'No'
            row['Hotel Completed'] = 'No'
            row['Hotel Reminders Sent'] = 0
            row['Hotel Final Notice'] = 'No'
        
        # Add file upload count
        row['Files Uploaded'] = len(person.files)
        
        data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Main data sheet
        sheet_name = role_filter if role_filter else 'All Persons'
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Add hotel summary sheet
        hotel_summary = generate_hotel_summary(course)
        summary_data = {
            'Metric': [
                'Total Night 1',
                'Total Night 2',
                'Total Night 3',
                '',
                'Participants Night 1',
                'Participants Night 2',
                'Participants Night 3',
                '',
                'Faculty Night 1',
                'Faculty Night 2',
                'Faculty Night 3',
                '',
                'All Three Nights',
                'Night 1 & 2 Only',
                'Night 2 & 3 Only',
                'Night 1 & 3 Only',
                'Night 1 Only',
                'Night 2 Only',
                'Night 3 Only',
                'No Hotel Needed'
            ],
            'Count': [
                hotel_summary['night1'],
                hotel_summary['night2'],
                hotel_summary['night3'],
                '',
                hotel_summary['by_role']['PARTICIPANT']['night1'],
                hotel_summary['by_role']['PARTICIPANT']['night2'],
                hotel_summary['by_role']['PARTICIPANT']['night3'],
                '',
                hotel_summary['by_role']['FACULTY']['night1'],
                hotel_summary['by_role']['FACULTY']['night2'],
                hotel_summary['by_role']['FACULTY']['night3'],
                '',
		hotel_summary['sequences']['all_three'],
                hotel_summary['sequences']['night1_2'],
                hotel_summary['sequences']['night2_3'],
                hotel_summary['sequences']['night1_3'],
                hotel_summary['sequences']['night1_only'],
                hotel_summary['sequences']['night2_only'],
                hotel_summary['sequences']['night3_only'],
                hotel_summary['sequences']['no_hotel']
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Hotel Summary', index=False)
        
        # Adjust column widths
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return output


def parse_uploaded_csv(file):
    """
    Parse uploaded CSV/Excel file with participants
    Expected columns: email, first_name, last_name, role (optional)
    Returns list of dicts
    """
    import pandas as pd
    
    try:
        # Try reading as Excel
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            # Try CSV
            df = pd.read_csv(file)
        
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Required columns
        required_cols = ['email']
        for col in required_cols:
            if col not in df.columns:
                return None, f"Missing required column: {col}"
        
        persons = []
        for _, row in df.iterrows():
            person = {
                'email': str(row['email']).strip(),
                'first_name': str(row.get('first_name', '')).strip() if pd.notna(row.get('first_name')) else '',
                'last_name': str(row.get('last_name', '')).strip() if pd.notna(row.get('last_name')) else '',
                'role': str(row.get('role', 'PARTICIPANT')).strip().upper() if pd.notna(row.get('role')) else 'PARTICIPANT'
            }
            
            # Validate role
            if person['role'] not in ['PARTICIPANT', 'FACULTY']:
                person['role'] = 'PARTICIPANT'
            
            persons.append(person)
        
        return persons, None
    
    except Exception as e:
        return None, f"Error parsing file: {str(e)}"


def initialize_default_email_templates():
    """Create default email templates if they don't exist"""
    from models import db, EmailTemplate
    
    default_templates = [
        {
            'template_name': 'rsvp_invitation',
            'display_name': 'RSVP Invitation',
            'subject': 'RSVP: {{course_name}}',
            'available_variables': '{{first_name}}, {{last_name}}, {{course_name}}, {{start_date}}, {{end_date}}, {{yes_link}}, {{no_link}}',
            'html_body': '''<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
	.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; padding: 15px 30px; margin: 10px; 
                 text-decoration: none; border-radius: 5px; font-weight: bold; }
        .btn-yes { background: #28a745; color: white; }
        .btn-no { background: #dc3545; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📅 Course Invitation</h1>
        </div>
        <div class="content">
            <h2>Hi {{first_name}},</h2>
            <p>You're invited to <strong>{{course_name}}</strong></p>
            <p><strong>Start:</strong> {{start_date}}<br>
               <strong>End:</strong> {{end_date}}</p>
            
            <p>Please confirm your attendance:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{yes_link}}" class="button btn-yes">✅ Yes, I'll Attend</a>
                <a href="{{no_link}}" class="button btn-no">❌ Can't Attend</a>
            </div>
        </div>
    </div>
</body>
</html>'''
        },
        {
            'template_name': 'info_form_request',
            'display_name': 'Information Form Request',
            'subject': 'Please Complete Your Information - {{course_name}}',
            'available_variables': '{{first_name}}, {{last_name}}, {{course_name}}, {{form_link}}',
            'html_body': '''<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #667eea; color: white; padding: 20px; text-align: center; }
        .content { background: #f9f9f9; padding: 30px; }
        .button { display: inline-block; padding: 15px 30px; background: #28a745; 
                 color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 Information Required</h1>
        </div>
        <div class="content">
            <h2>Hi {{first_name}},</h2>
            <p>Please complete your information for <strong>{{course_name}}</strong>.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{form_link}}" class="button">Complete Information Form</a>
            </div>
            
            <p style="color: #666; font-size: 14px;">This link is unique to you.</p>
        </div>
    </div>
</body>
</html>'''
        },
        {
            'template_name': 'info_reminder',
            'display_name': 'Information Form Reminder',
            'subject': 'Reminder #{{reminder_number}}: Complete Your Information - {{course_name}}',
            'available_variables': '{{first_name}}, {{last_name}}, {{course_name}}, {{form_link}}, {{reminder_number}}',
            'html_body': '''<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #ffc107; color: #333; padding: 20px; text-align: center; }
        .content { background: #f9f9f9; padding: 30px; }
        .button { display: inline-block; padding: 15px 30px; background: #28a745; 
                 color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔔 Reminder: Action Required</h1>
        </div>
        <div class="content">
            <h2>Hi {{first_name}},</h2>
            <p>This is reminder <strong>#{{reminder_number}}</strong> to complete your information for {{course_name}}.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{form_link}}" class="button">Complete Form Now</a>
            </div>
            
            <p style="color: #d9534f;">⚠️ You will receive up to 4 reminders.</p>
        </div>
    </div>
</body>
</html>'''
        },
        {
            'template_name': 'hotel_request',
            'display_name': 'Hotel Request',
            'subject': 'Hotel Accommodation Request - {{course_name}}',
            'available_variables': '{{first_name}}, {{last_name}}, {{course_name}}, {{hotel_link}}, {{night1_date}}, {{night2_date}}, {{night3_date}}',
            'html_body': '''<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #17a2b8; color: white; padding: 20px; text-align: center; }
        .content { background: #f9f9f9; padding: 30px; }
        .button { display: inline-block; padding: 15px 30px; background: #28a745; 
                 color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏨 Hotel Accommodation</h1>
        </div>
        <div class="content">
            <h2>Hi {{first_name}},</h2>
            <p>Please let us know if you need hotel accommodation for {{course_name}}.</p>
            
            <p><strong>Available nights:</strong></p>
            <ul>
                <li>Night 1: {{night1_date}}</li>
                <li>Night 2: {{night2_date}}</li>
                <li>Night 3: {{night3_date}}</li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{hotel_link}}" class="button">Submit Hotel Request</a>
            </div>
        </div>
    </div>
</body>
</html>'''
        },
        {
            'template_name': 'hotel_reminder',
	'display_name': 'Hotel Request Reminder',
            'subject': 'Reminder #{{reminder_number}}: Hotel Request - {{course_name}}',
            'available_variables': '{{first_name}}, {{last_name}}, {{course_name}}, {{hotel_link}}, {{reminder_number}}',
            'html_body': '''<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #ffc107; color: #333; padding: 20px; text-align: center; }
        .content { background: #f9f9f9; padding: 30px; }
        .button { display: inline-block; padding: 15px 30px; background: #17a2b8; 
                 color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔔 Hotel Request Reminder</h1>
        </div>
        <div class="content">
            <h2>Hi {{first_name}},</h2>
            <p>This is reminder <strong>#{{reminder_number}} of 4</strong> to submit your hotel accommodation request.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{hotel_link}}" class="button">Submit Hotel Request</a>
            </div>
            
            <p style="color: #d9534f;">⚠️ After 4 reminders, no hotel room will be booked for you.</p>
        </div>
    </div>
</body>
</html>'''
        },
        {
            'template_name': 'hotel_final_notice',
            'display_name': 'Hotel Final Notice',
            'subject': 'Final Notice: No Hotel Room Will Be Booked - {{course_name}}',
            'available_variables': '{{first_name}}, {{last_name}}, {{course_name}}',
            'html_body': '''<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #dc3545; color: white; padding: 20px; text-align: center; }
        .content { background: #f9f9f9; padding: 30px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>❌ Hotel Booking Closed</h1>
        </div>
        <div class="content">
            <h2>Hi {{first_name}},</h2>
            <p>We have not received your hotel accommodation request for <strong>{{course_name}}</strong>.</p>
            
            <p style="color: #dc3545; font-weight: bold;">
                As a result, no hotel room will be booked for you.
            </p>
            
            <p>If you need accommodation, please make your own arrangements.</p>
            
            <p>If you believe this is an error, please contact the course administrator immediately.</p>
        </div>
    </div>
</body>
</html>'''
        }
    ]
    
    # Create templates if they don't exist
    for template_data in default_templates:
        existing = EmailTemplate.query.filter_by(
            template_name=template_data['template_name']
        ).first()
        
        if not existing:
            template = EmailTemplate(**template_data)
            db.session.add(template)

try:
        db.session.commit()
        print("✅ Default email templates initialized")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error initializing templates: {e}")


def render_email_template(template_name, variables):
    """
    Render an email template with variables
    Returns (subject, html_body) tuple
    """
    from models import EmailTemplate
    from jinja2 import Template
    
    # Get template from database
    template = EmailTemplate.query.filter_by(template_name=template_name).first()
    
    if not template:
        raise ValueError(f"Email template '{template_name}' not found")
    
    # Render subject and body with Jinja2
    subject_template = Template(template.subject)
    body_template = Template(template.html_body)
    
    rendered_subject = subject_template.render(**variables)
    rendered_body = body_template.render(**variables)
    
    return rendered_subject, rendered_body


def get_person_statistics(course_id):
    """Get statistics for a course"""
    from models import Person
    
    stats = {
        'total_invited': 0,
        'total_attending': 0,
        'total_not_attending': 0,
        'total_no_response': 0,
        'info_completed': 0,
        'info_pending': 0,
        'hotel_completed': 0,
        'hotel_pending': 0,
        'participants': {
            'invited': 0,
            'attending': 0,
            'not_attending': 0,
        },
        'faculty': {
            'invited': 0,
            'attending': 0,
            'not_attending': 0,
        }
    }
    
    persons = Person.query.filter_by(course_id=course_id).all()
    
    for person in persons:
        stats['total_invited'] += 1
        
        # Count by status
        if person.status == 'ATTENDING':
            stats['total_attending'] += 1
            stats[person.role.lower()]['attending'] += 1
            
            # Info completion
            if person.info_completed:
                stats['info_completed'] += 1
            else:
                stats['info_pending'] += 1
            
            # Hotel completion
            if person.hotel_request and person.hotel_request.completed:
                stats['hotel_completed'] += 1
            else:
                stats['hotel_pending'] += 1
                
        elif person.status == 'NOT_ATTENDING':
            stats['total_not_attending'] += 1
            stats[person.role.lower()]['not_attending'] += 1
        else:
            stats['total_no_response'] += 1
        
        # Count by role
        stats[person.role.lower()]['invited'] += 1
    
    return stats


def save_uploaded_file(file, person):
    """
    Save uploaded file and return UploadedFile object
    """
    from models import UploadedFile
    import uuid
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Save file
        filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        
        # Get file size
        file_size = os.path.getsize(filepath)
        
        # Create database record
        uploaded_file = UploadedFile(
            person_id=person.id,
            filename=unique_filename,
            original_filename=original_filename,
            file_size=file_size
        )
        
        return uploaded_file
    
    return None