from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from models import db, Course, Participant, CustomQuestion, ParticipantAnswer, HotelRequest, ReminderTracking, ParticipantFile
from email_utils import send_email, send_rsvp_email, send_info_form_email, send_hotel_finalization_email, send_file_upload_email
from datetime import datetime, timedelta
import pandas as pd
import secrets
import os
from io import BytesIO
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///courses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

# Admin credentials (change these!)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

with app.app_context():
    db.create_all()


# Helper function to check if user is logged in
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# LOGIN AND ADMIN ROUTES
# ============================================

@app.route('/')
def index():
    return redirect(url_for('admin_login'))


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))


@app.route('/admin')
@login_required
def admin():
    courses = Course.query.all()
    message = request.args.get('message')
    return render_template('admin.html', courses=courses, message=message)


@app.route('/create-course', methods=['POST'])
@login_required
def create_course():
    name = request.form.get('name')
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
    
    hotel_night1 = request.form.get('hotel_night1')
    hotel_night2 = request.form.get('hotel_night2')
    hotel_night3 = request.form.get('hotel_night3')
    
    course = Course(
        name=name,
        start_date=start_date,
        end_date=end_date,
        hotel_night1=datetime.strptime(hotel_night1, '%Y-%m-%d').date() if hotel_night1 else None,
        hotel_night2=datetime.strptime(hotel_night2, '%Y-%m-%d').date() if hotel_night2 else None,
        hotel_night3=datetime.strptime(hotel_night3, '%Y-%m-%d').date() if hotel_night3 else None
    )
    
    db.session.add(course)
    db.session.commit()
    
    return redirect(url_for('admin', message='Course created successfully'))


@app.route('/delete-course/<int:course_id>')
@login_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    return redirect(url_for('admin', message='Course deleted successfully'))

# ============================================
# COURSE DETAIL AND PARTICIPANT MANAGEMENT
# ============================================

@app.route('/course/<int:course_id>')
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    participants = Participant.query.filter_by(course_id=course_id, role='PARTICIPANT').all()
    faculty = Participant.query.filter_by(course_id=course_id, role='FACULTY').all()
    message = request.args.get('message')
    return render_template('course_detail.html', 
                         course=course, 
                         participants=participants,
                         faculty=faculty,
                         message=message)


@app.route('/upload-participants/<int:course_id>', methods=['POST'])
@login_required
def upload_participants(course_id):
    course = Course.query.get_or_404(course_id)
    file = request.files.get('file')
    role = request.form.get('role', 'PARTICIPANT')
    
    if not file:
        return redirect(url_for('course_detail', course_id=course_id, message='No file uploaded'))
    
    try:
        df = pd.read_excel(file)
        
        if 'email' not in df.columns:
            return redirect(url_for('course_detail', course_id=course_id, message='Excel file must have an "email" column'))
        
        count = 0
        for _, row in df.iterrows():
            email = row['email']
            if pd.notna(email) and email.strip():
                existing = Participant.query.filter_by(course_id=course_id, email=email.strip()).first()
                if not existing:
                    participant = Participant(
                        course_id=course_id,
                        email=email.strip(),
                        role=role,
                        status='INVITED'
                    )
                    db.session.add(participant)
                    count += 1
        
        db.session.commit()
        role_name = "faculty" if role == "FACULTY" else "participants"
        return redirect(url_for('course_detail', course_id=course_id, message=f'{count} {role_name} added successfully'))
    
    except Exception as e:
        return redirect(url_for('course_detail', course_id=course_id, message=f'Error: {str(e)}'))


@app.route('/delete-participant/<int:participant_id>')
@login_required
def delete_participant(participant_id):
    participant = Participant.query.get_or_404(participant_id)
    course_id = participant.course_id
    db.session.delete(participant)
    db.session.commit()
    return redirect(url_for('course_detail', course_id=course_id, message='Participant deleted successfully'))


@app.route('/add-question/<int:course_id>', methods=['POST'])
@login_required
def add_question(course_id):
    course = Course.query.get_or_404(course_id)
    
    label = request.form.get('label')
    field_type = request.form.get('field_type', 'text')
    required = 'required' in request.form
    
    question = CustomQuestion(
        course_id=course_id,
        label=label,
        field_type=field_type,
        required=required,
        order_index=len(course.questions)
    )
    
    db.session.add(question)
    db.session.commit()
    
    return redirect(url_for('course_detail', course_id=course_id, message='Question added successfully'))

# ============================================
# DELETE QUESTION, PREVIEW, AND EXPORT
# ============================================

@app.route('/delete-question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    question = CustomQuestion.query.get_or_404(question_id)
    course_id = question.course_id
    db.session.delete(question)
    db.session.commit()
    return redirect(url_for('course_detail', course_id=course_id, message='Question deleted successfully'))


@app.route('/preview-form/<int:course_id>')
@login_required
def preview_form(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('preview_form.html', course=course)


@app.route('/export-participants/<int:course_id>')
@login_required
def export_participants(course_id):
    course = Course.query.get_or_404(course_id)
    role_filter = request.args.get('role')
    
    # Build query based on role filter
    if role_filter:
        participants = Participant.query.filter_by(course_id=course_id, role=role_filter).all()
        filename = f"{course.name}_{role_filter.lower()}_export.xlsx"
    else:
        participants = Participant.query.filter_by(course_id=course_id).all()
        filename = f"{course.name}_all_export.xlsx"
    
    # Build data for export
    data = []
    for p in participants:
        row = {
            'Role': p.role,
            'Email': p.email,
            'First Name': p.first_name or '',
            'Last Name': p.last_name or '',
            'Status': p.status,
            'RSVP Responded': 'Yes' if p.attending_responded else 'No'
        }
        
        # Add custom question answers
        for answer in p.answers:
            row[answer.question.label] = answer.answer_text or ''
        
        # Add hotel information
        if p.hotel_request:
            row['Needs Hotel'] = 'Yes' if p.hotel_request.need_hotel else 'No'
            if p.hotel_request.need_hotel:
                nights = []
                if p.hotel_request.night1:
                    nights.append(str(course.hotel_night1))
                if p.hotel_request.night2:
                    nights.append(str(course.hotel_night2))
                if p.hotel_request.night3:
                    nights.append(str(course.hotel_night3))
                row['Hotel Nights'] = ', '.join(nights) if nights else 'None selected'
        else:
            row['Needs Hotel'] = 'Not answered'
            row['Hotel Nights'] = ''
        
        data.append(row)
    
    # Create Excel file
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Participants')
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

# ============================================
# EMAIL SENDING ROUTES
# ============================================

@app.route('/send-initial-rsvp/<int:course_id>', methods=['POST'])
@login_required
def send_initial_rsvp(course_id):
    course = Course.query.get_or_404(course_id)
    participants = Participant.query.filter_by(course_id=course_id).all()
    
    count = 0
    for participant in participants:
        if not participant.attending_responded:
            send_rsvp_email(participant, course)
            count += 1
    
    return redirect(url_for('course_detail', course_id=course_id, message=f'RSVP emails sent to {count} participants'))


@app.route('/send-reminders/<int:course_id>', methods=['POST'])
@login_required
def send_reminders(course_id):
    course = Course.query.get_or_404(course_id)
    participants = Participant.query.filter_by(course_id=course_id, status='INVITED').all()
    
    count = 0
    for participant in participants:
        if not participant.attending_responded:
            send_rsvp_email(participant, course)
            count += 1
    
    return redirect(url_for('course_detail', course_id=course_id, message=f'Reminder emails sent to {count} participants'))


# ============================================
# PARTICIPANT-FACING ROUTES (RSVP)
# ============================================

@app.route('/rsvp/<token>')
def rsvp(token):
    participant = Participant.query.filter_by(token=token).first_or_404()
    course = participant.course
    attending = request.args.get('attending')
    
    if attending == 'yes':
        participant.status = 'ATTENDING'
        participant.attending_responded = True
        db.session.commit()
        
        # Send info form email
        send_info_form_email(participant, course)
        
        return render_template('rsvp_response.html', course=course, attending=True)
    
    elif attending == 'no':
        participant.status = 'NOT_ATTENDING'
        participant.attending_responded = True
        db.session.commit()
        
        return render_template('rsvp_response.html', course=course, attending=False)
    
    return "Invalid RSVP response", 400

# ============================================
# PARTICIPANT INFO FORM AND FILE UPLOAD
# ============================================

@app.route('/info-form/<token>', methods=['GET', 'POST'])
def info_form(token):
    participant = Participant.query.filter_by(token=token).first_or_404()
    course = participant.course
    
    if request.method == 'POST':
        participant.first_name = request.form.get('first_name')
        participant.last_name = request.form.get('last_name')
        
        # Save custom question answers
        for question in course.questions:
            answer_text = request.form.get(f'q_{question.id}')
            existing_answer = ParticipantAnswer.query.filter_by(
                participant_id=participant.id, 
                question_id=question.id
            ).first()
            
            if answer_text:
                if existing_answer:
                    existing_answer.answer_text = answer_text
                else:
                    answer = ParticipantAnswer(
                        participant_id=participant.id,
                        question_id=question.id,
                        answer_text=answer_text
                    )
                    db.session.add(answer)
        
        # Handle hotel request
        need_hotel = request.form.get('need_hotel') == 'yes'
        if need_hotel:
            hotel_request, created = HotelRequest.get_or_create(participant.id)
            hotel_request.need_hotel = True
            hotel_request.night1 = 'night1' in request.form
            hotel_request.night2 = 'night2' in request.form
            hotel_request.night3 = 'night3' in request.form
        else:
            if hasattr(participant, 'hotel_request') and participant.hotel_request:
                db.session.delete(participant.hotel_request)
        
        # Handle file uploads
        files = request.files.getlist('files')
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{participant.id}_{filename}")
                file.save(filepath)

  # Handle file uploads
        files = request.files.getlist('files')
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{participant.id}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                
                # Save file reference to database
                participant_file = ParticipantFile(
                    participant_id=participant.id,
                    filename=filename,
                    filepath=filepath,
                    file_size=os.path.getsize(filepath),
                    mime_type=file.content_type
                )
                db.session.add(participant_file)

db.session.commit()
        
        # Send hotel finalization email if hotel was requested
        if need_hotel:
            send_hotel_finalization_email(participant, course)
            return render_template('hotel_finalized.html', course=course, participant=participant)
        
        # Fixed: Use render_template instead of redirect
        return render_template('rsvp_response.html', course=course, attending=True)
    
    return render_template('info_form.html', course=course, participant=participant)


