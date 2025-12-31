from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from flask_mail import Mail
from config import Config
from models import db, Course, Person, CustomQuestion, Answer, HotelRequest, UploadedFile, EmailTemplate
from email_service import mail, send_rsvp_email, send_info_form_email, send_info_reminder_email, \
    send_hotel_request_email, send_hotel_reminder_email, send_hotel_final_notice_email, \
    send_file_upload_notification, send_bulk_rsvp_emails, send_bulk_info_form_emails, \
    send_bulk_hotel_request_emails, process_info_reminders, process_hotel_reminders
from utils import allowed_file, generate_hotel_summary, export_to_excel, parse_uploaded_csv, \
    initialize_default_email_templates, get_person_statistics, save_uploaded_file
from datetime import datetime
from werkzeug.utils import secure_filename
from functools import wraps
import os

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
mail.init_app(app)

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Create database tables and initialize templates
with app.app_context():
    db.create_all()
    initialize_default_email_templates()
    print("✅ Database initialized")
    print("✅ Email templates initialized")


# ============================================
# AUTHENTICATION & DECORATORS
# ============================================

def login_required(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# ADMIN ROUTES - AUTHENTICATION
# ============================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASSWORD']:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))


# ============================================
# ADMIN ROUTES - DASHBOARD & COURSES
# ============================================

@app.route('/admin')
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard - list all courses"""
    courses = Course.query.order_by(Course.start_date.desc()).all()
    
    # Get statistics for each course
    course_stats = {}
    for course in courses:
        course_stats[course.id] = get_person_statistics(course.id)
    
    return render_template('admin/dashboard.html', courses=courses, course_stats=course_stats)


@app.route('/admin/course/create', methods=['GET', 'POST'])
@login_required
def create_course():
    """Create new course"""
    if request.method == 'POST':
        try:
            course = Course(
                name=request.form.get('name'),
                start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
                end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date(),
                hotel_night1=datetime.strptime(request.form.get('hotel_night1'), '%Y-%m-%d').date() if request.form.get('hotel_night1') else None,
                hotel_night1_label=request.form.get('hotel_night1_label', 'Night 1'),
                hotel_night2=datetime.strptime(request.form.get('hotel_night2'), '%Y-%m-%d').date() if request.form.get('hotel_night2') else None,
                hotel_night2_label=request.form.get('hotel_night2_label', 'Night 2'),
                hotel_night3=datetime.strptime(request.form.get('hotel_night3'), '%Y-%m-%d').date() if request.form.get('hotel_night3') else None,
                hotel_night3_label=request.form.get('hotel_night3_label', 'Night 3')
            )
            
            db.session.add(course)
            db.session.commit()
            
            flash(f'Course "{course.name}" created successfully!', 'success')
            return redirect(url_for('course_detail', course_id=course.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating course: {str(e)}', 'danger')
    
    return render_template('admin/create_course.html')


@app.route('/admin/course/<int:course_id>')
@login_required
def course_detail(course_id):
    """Course detail page"""
    course = Course.query.get_or_404(course_id)
    
    # Get participants and faculty separately
    participants = Person.query.filter_by(course_id=course_id, role='PARTICIPANT').all()
    faculty = Person.query.filter_by(course_id=course_id, role='FACULTY').all()
    
    # Get statistics
    stats = get_person_statistics(course_id)
    
    # Get hotel summary
    hotel_summary = generate_hotel_summary(course)
    
    # Get custom questions
    questions = CustomQuestion.query.filter_by(course_id=course_id).order_by(CustomQuestion.order).all()
    
    return render_template('admin/course_detail.html', 
                         course=course, 
                         participants=participants,
                         faculty=faculty,
                         stats=stats,
                         hotel_summary=hotel_summary,
                         questions=questions)


@app.route('/admin/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    """Edit course details"""
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        try:
            course.name = request.form.get('name')
            course.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            course.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            
            if request.form.get('hotel_night1'):
                course.hotel_night1 = datetime.strptime(request.form.get('hotel_night1'), '%Y-%m-%d').date()
            course.hotel_night1_label = request.form.get('hotel_night1_label', 'Night 1')
            
            if request.form.get('hotel_night2'):
                course.hotel_night2 = datetime.strptime(request.form.get('hotel_night2'), '%Y-%m-%d').date()
            course.hotel_night2_label = request.form.get('hotel_night2_label', 'Night 2')
            
            if request.form.get('hotel_night3'):
                course.hotel_night3 = datetime.strptime(request.form.get('hotel_night3'), '%Y-%m-%d').date()
            course.hotel_night3_label = request.form.get('hotel_night3_label', 'Night 3')
            
            course.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash('Course updated successfully!', 'success')
            return redirect(url_for('course_detail', course_id=course.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating course: {str(e)}', 'danger')
    
    return render_template('admin/edit_course.html', course=course)


@app.route('/admin/course/<int:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    """Delete course"""
    course = Course.query.get_or_404(course_id)
    
    try:
        db.session.delete(course)
        db.session.commit()
        flash(f'Course "{course.name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting course: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))


# ============================================
# ADMIN ROUTES - PERSON MANAGEMENT
# ============================================

@app.route('/admin/course/<int:course_id>/upload-persons', methods=['GET', 'POST'])
@login_required
def upload_persons(course_id):
    """Upload CSV/Excel file with persons"""
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded.', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)
        
        if file:
            # Parse file
            persons_data, error = parse_uploaded_csv(file)
            
            if error:
                flash(error, 'danger')
                return redirect(request.url)
            
            # Add persons to database
            added_count = 0
            skipped_count = 0
            
            for person_data in persons_data:
                # Check if person already exists
                existing = Person.query.filter_by(
                    course_id=course_id,
                    email=person_data['email']
                ).first()
                
                if existing:
                    skipped_count += 1
                    continue
                
                person = Person(
                    course_id=course_id,
                    email=person_data['email'],
                    first_name=person_data['first_name'],
                    last_name=person_data['last_name'],
                    role=person_data['role']
                )
                
                db.session.add(person)
                added_count += 1
            
            try:
                db.session.commit()
                flash(f'Successfully added {added_count} persons. Skipped {skipped_count} duplicates.', 'success')
                return redirect(url_for('course_detail', course_id=course_id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error saving persons: {str(e)}', 'danger')
    
    return render_template('admin/upload_persons.html', course=course)


@app.route('/admin/course/<int:course_id>/add-person', methods=['GET', 'POST'])
@login_required
def add_person(course_id):
    """Manually add a single person"""
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Check if person already exists
        existing = Person.query.filter_by(course_id=course_id, email=email).first()
        if existing:
            flash(f'Person with email {email} already exists in this course.', 'warning')
            return redirect(request.url)
        
        try:
            person = Person(
                course_id=course_id,
                email=email,
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                role=request.form.get('role', 'PARTICIPANT')
            )
            
            db.session.add(person)
            db.session.commit()
            
            flash(f'Person {email} added successfully!', 'success')
            return redirect(url_for('course_detail', course_id=course_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding person: {str(e)}', 'danger')
    
    return render_template('admin/add_person.html', course=course)


@app.route('/admin/person/<int:person_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_person(person_id):
    """Edit person details"""
    person = Person.query.get_or_404(person_id)
    
    if request.method == 'POST':
        try:
            person.email = request.form.get('email')
            person.first_name = request.form.get('first_name')
            person.last_name = request.form.get('last_name')
            person.role = request.form.get('role')
            person.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Person updated successfully!', 'success')
            return redirect(url_for('course_detail', course_id=person.course_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating person: {str(e)}', 'danger')
    
    return render_template('admin/edit_person.html', person=person)


@app.route('/admin/person/<int:person_id>/delete', methods=['POST'])
@login_required
def delete_person(person_id):
    """Delete person"""
    person = Person.query.get_or_404(person_id)
    course_id = person.course_id
    
    try:
        db.session.delete(person)
        db.session.commit()
        flash('Person deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting person: {str(e)}', 'danger')
    
    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/admin/person/<int:person_id>/view')
@login_required
def view_person(person_id):
    """View person details with all answers"""
    person = Person.query.get_or_404(person_id)
    
    # Get all answers
    answers = Answer.query.filter_by(person_id=person_id).all()
    
    # Get uploaded files
    files = UploadedFile.query.filter_by(person_id=person_id).all()
    
    return render_template('admin/view_person.html', person=person, answers=answers, files=files)


# ============================================
# ADMIN ROUTES - EMAIL SENDING
# ============================================

@app.route('/admin/course/<int:course_id>/send-rsvp', methods=['POST'])
@login_required
def send_rsvp_emails(course_id):
    """Send RSVP emails to all invited persons"""
    course = Course.query.get_or_404(course_id)
    
    # Get persons who haven't responded yet
    persons = Person.query.filter_by(
        course_id=course_id,
        attending_responded=False
    ).all()
    
    if not persons:
        flash('No persons to send RSVP emails to.', 'warning')
        return redirect(url_for('course_detail', course_id=course_id))
    
    results = send_bulk_rsvp_emails(persons, course)
    
    flash(f'RSVP emails sent: {results["success"]} successful, {results["failed"]} failed.', 
          'success' if results['failed'] == 0 else 'warning')
    
    if results['errors']:
        for error in results['errors'][:5]:  # Show first 5 errors
            flash(error, 'danger')
    
    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/admin/course/<int:course_id>/send-info-forms', methods=['POST'])
@login_required
def send_info_forms(course_id):
    """Send info form emails to attending persons"""
    course = Course.query.get_or_404(course_id)
    
    # Get persons who are attending but haven't completed info
    persons = Person.query.filter_by(
        course_id=course_id,
        status='ATTENDING',
        info_completed=False
    ).all()
    
    if not persons:
        flash('No persons to send info forms to.', 'warning')
        return redirect(url_for('course_detail', course_id=course_id))
    
    results = send_bulk_info_form_emails(persons, course)
    
    flash(f'Info form emails sent: {results["success"]} successful, {results["failed"]} failed.', 
          'success' if results['failed'] == 0 else 'warning')
    
    if results['errors']:
        for error in results['errors'][:5]:
            flash(error, 'danger')
    
    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/admin/course/<int:course_id>/send-hotel-requests', methods=['POST'])
@login_required
def send_hotel_requests(course_id):
    """Send hotel request emails to attending persons"""
    course = Course.query.get_or_404(course_id)
    
    # Get persons who are attending
    persons = Person.query.filter_by(
        course_id=course_id,
        status='ATTENDING'
    ).all()
    
    # Filter those who haven't completed hotel request
    persons_to_email = []
    for person in persons:
        if not person.hotel_request or not person.hotel_request.completed:
            persons_to_email.append(person)
    
    if not persons_to_email:
        flash('No persons to send hotel requests to.', 'warning')
        return redirect(url_for('course_detail', course_id=course_id))
    
    results = send_bulk_hotel_request_emails(persons_to_email, course)
    
    flash(f'Hotel request emails sent: {results["success"]} successful, {results["failed"]} failed.', 
          'success' if results['failed'] == 0 else 'warning')
    
    if results['errors']:
        for error in results['errors'][:5]:
            flash(error, 'danger')
    
    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/admin/course/<int:course_id>/process-info-reminders', methods=['POST'])
@login_required
def run_info_reminders(course_id):
    """Manually trigger info form reminders"""
    course = Course.query.get_or_404(course_id)
    
    results = process_info_reminders(course)
    
    flash(f'Info reminders processed: {results["reminders_sent"]} sent, '
          f'{results["max_reminders_reached"]} reached max reminders.', 'success')
    
    if results['errors']:
        for error in results['errors'][:5]:
            flash(error, 'danger')
    
    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/admin/course/<int:course_id>/process-hotel-reminders', methods=['POST'])
@login_required
def run_hotel_reminders(course_id):
    """Manually trigger hotel reminders"""
    course = Course.query.get_or_404(course_id)
    
    results = process_hotel_reminders(course)
    
    flash(f'Hotel reminders processed: {results["reminders_sent"]} reminders sent, '
          f'{results["final_notices_sent"]} final notices sent.', 'success')
    
    if results['errors']:
        for error in results['errors'][:5]:
            flash(error, 'danger')
    
    return redirect(url_for('course_detail', course_id=course_id))


# ============================================
# ADMIN ROUTES - QUESTIONS MANAGEMENT
# ============================================

@app.route('/admin/course/<int:course_id>/questions', methods=['GET', 'POST'])
@login_required
def manage_questions(course_id):
    """Manage custom questions for info form"""
    course = Course.query.get_or_404(course_id)
    questions = CustomQuestion.query.filter_by(course_id=course_id).order_by(CustomQuestion.order).all()
    
    if request.method == 'POST':
        try:
            # Get the highest order number
            max_order = db.session.query(db.func.max(CustomQuestion.order)).filter_by(course_id=course_id).scalar() or 0
            
            question = CustomQuestion(
                course_id=course_id,
                label=request.form.get('label'),
                field_type=request.form.get('field_type', 'text'),
                required=request.form.get('required') == 'on',
                order=max_order + 1
            )
            
            db.session.add(question)
            db.session.commit()
            
            flash('Question added successfully!', 'success')
            return redirect(url_for('manage_questions', course_id=course_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding question: {str(e)}', 'danger')
    
    return render_template('admin/edit_questions.html', course=course, questions=questions)


@app.route('/admin/question/<int:question_id>/edit', methods=['POST'])
@login_required
def edit_question(question_id):
    """Edit a question"""
    question = CustomQuestion.query.get_or_404(question_id)
    
    try:
        question.label = request.form.get('label')
        question.field_type = request.form.get('field_type')
        question.required = request.form.get('required') == 'on'
        
        db.session.commit()
        flash('Question updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating question: {str(e)}', 'danger')
    
    return redirect(url_for('manage_questions', course_id=question.course_id))


@app.route('/admin/question/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    """Delete a question"""
    question = CustomQuestion.query.get_or_404(question_id)
    course_id = question.course_id
    
    try:
        db.session.delete(question)
        db.session.commit()
        flash('Question deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting question: {str(e)}', 'danger')
    
    return redirect(url_for('manage_questions', course_id=course_id))


@app.route('/admin/question/<int:question_id>/move/<direction>', methods=['POST'])
@login_required
def move_question(question_id, direction):
    """Move question up or down in order"""
    question = CustomQuestion.query.get_or_404(question_id)
    
    try:
        if direction == 'up':
            # Find question with next lower order
            prev_question = CustomQuestion.query.filter_by(course_id=question.course_id)\
                .filter(CustomQuestion.order < question.order)\
                .order_by(CustomQuestion.order.desc()).first()
            
            if prev_question:
                question.order, prev_question.order = prev_question.order, question.order
        
        elif direction == 'down':
            # Find question with next higher order
            next_question = CustomQuestion.query.filter_by(course_id=question.course_id)\
                .filter(CustomQuestion.order > question.order)\
                .order_by(CustomQuestion.order).first()
            
            if next_question:
                question.order, next_question.order = next_question.order, question.order
        
        db.session.commit()
        flash('Question order updated!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error moving question: {str(e)}', 'danger')
    
    return redirect(url_for('manage_questions', course_id=question.course_id))


# ============================================
# ADMIN ROUTES - EXPORT
# ============================================

@app.route('/admin/course/<int:course_id>/export')
@login_required
def export_course_data(course_id):
    """Export course data to Excel"""
    course = Course.query.get_or_404(course_id)
    
    role_filter = request.args.get('role')  # Can be 'PARTICIPANT', 'FACULTY', or None for all
    
    try:
        output = export_to_excel(course, role_filter)
        
        filename = f"{course.name.replace(' ', '_')}"
        if role_filter:
            filename += f"_{role_filter}"
        filename += f"_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error exporting data: {str(e)}', 'danger')
        return redirect(url_for('course_detail', course_id=course_id))


# ============================================
# ADMIN ROUTES - EMAIL TEMPLATES
# ============================================

@app.route('/admin/email-templates')
@login_required
def email_templates():
    """Manage email templates"""
    templates = EmailTemplate.query.all()
    return render_template('admin/email_templates.html', templates=templates)


@app.route('/admin/email-template/<int:template_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_email_template(template_id):
    """Edit email template"""
    template = EmailTemplate.query.get_or_404(template_id)
    
    if request.method == 'POST':
        try:
            template.subject = request.form.get('subject')
            template.html_body = request.form.get('html_body')
            template.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Email template updated successfully!', 'success')
            return redirect(url_for('email_templates'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating template: {str(e)}', 'danger')
    
    return render_template('admin/edit_email_template.html', template=template)


# ============================================
# ADMIN ROUTES - FILE MANAGEMENT
# ============================================

@app.route('/admin/files/<int:file_id>/download')
@login_required
def download_file(file_id):
    """Download uploaded file"""
    file = UploadedFile.query.get_or_404(file_id)
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    
    if not os.path.exists(filepath):
        flash('File not found.', 'danger')
        return redirect(url_for('view_person', person_id=file.person_id))
    
    return send_file(filepath, as_attachment=True, download_name=file.original_filename)


@app.route('/admin/files/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file(file_id):
    """Delete uploaded file"""
    file = UploadedFile.query.get_or_404(file_id)
    person_id = file.person_id
    
    try:
        # Delete physical file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Delete database record
        db.session.delete(file)
        db.session.commit()
        
        flash('File deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting file: {str(e)}', 'danger')
    
    return redirect(url_for('view_person', person_id=person_id))


# ============================================
# PUBLIC ROUTES - RSVP
# ============================================

@app.route('/rsvp/<token>/<response>')
def rsvp_response(token, response):
    """Handle RSVP response (yes/no)"""
    person = Person.query.filter_by(token=token).first_or_404()
    course = person.course
    
    if response == 'yes':
        person.status = 'ATTENDING'
        person.attending_responded = True
        person.rsvp_responded_at = datetime.utcnow()
        
        # Create hotel request record if doesn't exist
        if not person.hotel_request:
            hotel_request = HotelRequest(person_id=person.id)
            db.session.add(hotel_request)
        
        db.session.commit()
        
        return render_template('public/rsvp_yes.html', person=person, course=course)
    
    elif response == 'no':
        person.status = 'NOT_ATTENDING'
        person.attending_responded = True
        person.rsvp_responded_at = datetime.utcnow()
        db.session.commit()
        
        return render_template('public/rsvp_no.html', person=person, course=course)
    
    else:
        return "Invalid response", 400


# ============================================
# PUBLIC ROUTES - INFO FORM
# ============================================

@app.route('/info/<token>', methods=['GET', 'POST'])
def info_form(token):
    """Information form for participants/faculty"""
    person = Person.query.filter_by(token=token).first_or_404()
    course = person.course
    
    # Check if person is attending
    if person.status != 'ATTENDING':
        return render_template('public/not_attending.html', person=person, course=course)
    
    # Get custom questions
    questions = CustomQuestion.query.filter_by(course_id=course.id).order_by(CustomQuestion.order).all()
    
    if request.method == 'POST':
        try:
            # Update basic info
            person.first_name = request.form.get('first_name')
            person.last_name = request.form.get('last_name')
            
            # Save answers to custom questions
            for question in questions:
                answer_text = request.form.get(f'question_{question.id}')
                
                # Check if answer already exists
                existing_answer = Answer.query.filter_by(
                    person_id=person.id,
                    question_id=question.id
                ).first()
                
                if existing_answer:
                    existing_answer.answer_text = answer_text
                    existing_answer.updated_at = datetime.utcnow()
                else:
                    answer = Answer(
                        person_id=person.id,
                        question_id=question.id,
                        answer_text=answer_text
                    )
                    db.session.add(answer)
            
            # Mark info as completed
            person.info_completed = True
            person.info_completed_at = datetime.utcnow()
            person.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return render_template('public/info_success.html', person=person, course=course)
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving information: {str(e)}', 'danger')
    
    # Get existing answers
    existing_answers = {}
    for answer in person.answers:
        existing_answers[answer.question_id] = answer.answer_text
    
    return render_template('public/info_form.html', 
                         person=person, 
                         course=course, 
                         questions=questions,
                         existing_answers=existing_answers)


# ============================================
# PUBLIC ROUTES - HOTEL FORM
# ============================================

@app.route('/hotel/<token>', methods=['GET', 'POST'])
def hotel_form(token):
    """Hotel accommodation request form"""
    person = Person.query.filter_by(token=token).first_or_404()
    course = person.course
    
    # Check if person is attending
    if person.status != 'ATTENDING':
        return render_template('public/not_attending.html', person=person, course=course)
    
    # Get or create hotel request
    hotel = person.hotel_request
    if not hotel:
        hotel = HotelRequest(person_id=person.id)
        db.session.add(hotel)
        db.session.commit()
    
    if request.method == 'POST':
        try:
            need_hotel = request.form.get('need_hotel') == 'yes'
            
            hotel.need_hotel = need_hotel
            
            if need_hotel:
                hotel.night1 = 'night1' in request.form
                hotel.night2 = 'night2' in request.form
                hotel.night3 = 'night3' in request.form
            else:
                hotel.night1 = False
                hotel.night2 = False
                hotel.night3 = False
            
            hotel.completed = True
            hotel.completed_at = datetime.utcnow()
hotel.completed = True
            hotel.completed_at = datetime.utcnow()
            hotel.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return render_template('public/hotel_success.html', person=person, course=course, hotel=hotel)
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving hotel request: {str(e)}', 'danger')
    
    return render_template('public/hotel_form.html', person=person, course=course, hotel=hotel)


# ============================================
# PUBLIC ROUTES - FILE UPLOAD
# ============================================

@app.route('/upload/<token>', methods=['GET', 'POST'])
def file_upload(token):
    """File upload page for participants/faculty"""
    person = Person.query.filter_by(token=token).first_or_404()
    course = person.course
    
    # Check if person is attending
    if person.status != 'ATTENDING':
        return render_template('public/not_attending.html', person=person, course=course)
    
    if request.method == 'POST':
        # Check if files were uploaded
        if 'files' not in request.files:
            flash('No files selected.', 'danger')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        
        if not files or files[0].filename == '':
            flash('No files selected.', 'danger')
            return redirect(request.url)
        
        uploaded_files = []
        errors = []
        
        for file in files:
            if file and allowed_file(file.filename):
                try:
                    uploaded_file = save_uploaded_file(file, person)
                    if uploaded_file:
                        db.session.add(uploaded_file)
                        uploaded_files.append(uploaded_file)
                    else:
                        errors.append(f"Failed to save {file.filename}")
                except Exception as e:
                    errors.append(f"Error uploading {file.filename}: {str(e)}")
            else:
                errors.append(f"Invalid file type: {file.filename}")
        
        try:
            db.session.commit()
            
            # Send notification email to admin
            if uploaded_files and app.config.get('ADMIN_EMAIL'):
                send_file_upload_notification(person, uploaded_files, app.config['ADMIN_EMAIL'])
            
            flash(f'Successfully uploaded {len(uploaded_files)} file(s).', 'success')
            
            if errors:
                for error in errors:
                    flash(error, 'warning')
            
            return render_template('public/upload_success.html', 
                                 person=person, 
                                 course=course, 
                                 uploaded_files=uploaded_files)
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving files: {str(e)}', 'danger')
    
    # Get existing files
    existing_files = UploadedFile.query.filter_by(person_id=person.id).all()
    
    return render_template('public/file_upload.html', 
                         person=person, 
                         course=course, 
                         existing_files=existing_files)


# ============================================
# PUBLIC ROUTES - HOME
# ============================================

@app.route('/')
def index():
    """Home page - redirect to admin login"""
    return redirect(url_for('admin_login'))


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    db.session.rollback()
    return render_template('errors/500.html'), 500

# ============================================
# API ENDPOINTS (for AJAX calls)
# ============================================

@app.route('/api/course/<int:course_id>/stats')
@login_required
def api_course_stats(course_id):
    """Get course statistics as JSON"""
    course = Course.query.get_or_404(course_id)
    stats = get_person_statistics(course_id)
    hotel_summary = generate_hotel_summary(course)
    
    return jsonify({
        'stats': stats,
        'hotel_summary': hotel_summary
    })


@app.route('/api/person/<int:person_id>/resend-rsvp', methods=['POST'])
@login_required
def api_resend_rsvp(person_id):
    """Resend RSVP email to specific person"""
    person = Person.query.get_or_404(person_id)
    course = person.course
    
    try:
        if send_rsvp_email(person, course):
            return jsonify({'success': True, 'message': 'RSVP email sent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send email'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/person/<int:person_id>/resend-info', methods=['POST'])
@login_required
def api_resend_info(person_id):
    """Resend info form email to specific person"""
    person = Person.query.get_or_404(person_id)
    course = person.course
    
    try:
        if send_info_form_email(person, course):
            return jsonify({'success': True, 'message': 'Info form email sent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send email'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/person/<int:person_id>/resend-hotel', methods=['POST'])
@login_required
def api_resend_hotel(person_id):
    """Resend hotel request email to specific person"""
    person = Person.query.get_or_404(person_id)
    course = person.course
    
    try:
        if send_hotel_request_email(person, course):
            return jsonify({'success': True, 'message': 'Hotel request email sent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send email'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/person/<int:person_id>/update-status', methods=['POST'])
@login_required
def api_update_person_status(person_id):
    """Update person's status"""
    person = Person.query.get_or_404(person_id)
    
    try:
        new_status = request.json.get('status')
        if new_status in ['ATTENDING', 'NOT_ATTENDING', 'NO_RESPONSE']:
            person.status = new_status
            person.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Status updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# CONTEXT PROCESSORS
# ============================================

@app.context_processor
def utility_processor():
    """Make utility functions available in templates"""
    return {
        'now': datetime.utcnow(),
        'len': len
    }

# ============================================
# SCHEDULED TASKS (Optional - for automation)
# ============================================

def run_automated_reminders():
    """
    Run automated reminder processing for all active courses
    This can be called by a scheduler (e.g., APScheduler, cron job)
    """
    with app.app_context():
        courses = Course.query.all()
        
        for course in courses:
            # Only process courses that haven't ended yet
            if course.end_date >= datetime.utcnow().date():
                print(f"Processing reminders for course: {course.name}")
                
                # Process info reminders
                info_results = process_info_reminders(course)
                print(f"  Info reminders: {info_results['reminders_sent']} sent")
                
                # Process hotel reminders
                hotel_results = process_hotel_reminders(course)
                print(f"  Hotel reminders: {hotel_results['reminders_sent']} sent, "
                      f"{hotel_results['final_notices_sent']} final notices")


# Optional: Setup APScheduler for automated reminders
# Uncomment if you want automated daily reminders
"""
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=run_automated_reminders,
    trigger="cron",
    hour=9,  # Run at 9 AM daily
    minute=0
)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
"""


# ============================================
# CLI COMMANDS
# ============================================

@app.cli.command('init-db')
def init_db_command():
    """Initialize the database and create default templates"""
    db.create_all()
    initialize_default_email_templates()
    print('✅ Database initialized successfully!')


@app.cli.command('create-admin')
def create_admin_command():
    """Display admin credentials from config"""
    print(f"Admin Username: {app.config['ADMIN_USERNAME']}")
    print(f"Admin Password: {app.config['ADMIN_PASSWORD']}")
    print("You can change these in config.py or .env file")


@app.cli.command('run-reminders')
def run_reminders_command():
    """Manually run reminder processing for all courses"""
    run_automated_reminders()
    print('✅ Reminder processing completed!')


@app.cli.command('test-email')
def test_email_command():
    """Test email configuration"""
    from email_service import send_email
    
    test_recipient = input("Enter test email address: ")
    
    subject = "Test Email from Course Management System"
    html_body = """
    <html>
    <body>
        <h2>Email Test Successful! ✅</h2>
        <p>Your email configuration is working correctly.</p>
    </body>
    </html>
    """
    
    if send_email(test_recipient, subject, html_body):
        print('✅ Test email sent successfully!')
    else:
        print('❌ Failed to send test email. Check your email configuration.')


# ============================================
# RUN APPLICATION
# ============================================

if __name__ == '__main__':
    # Run in debug mode for development
    # For production, use a production WSGI server like Gunicorn
    app.run(debug=True, host='0.0.0.0', port=5000)