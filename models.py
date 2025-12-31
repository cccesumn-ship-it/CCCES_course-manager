from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import secrets

db = SQLAlchemy()


class Course(db.Model):
    """Main course entity"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # Hotel nights (3 configurable dates)
    hotel_night1 = db.Column(db.Date)
    hotel_night1_label = db.Column(db.String(100), default='Night 1')
    hotel_night2 = db.Column(db.Date)
    hotel_night2_label = db.Column(db.String(100), default='Night 2')
    hotel_night3 = db.Column(db.Date)
    hotel_night3_label = db.Column(db.String(100), default='Night 3')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    persons = db.relationship('Person', backref='course', lazy=True, cascade='all, delete-orphan')
    questions = db.relationship('CustomQuestion', backref='course', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Course {self.name}>'


class Person(db.Model):
    """Participants and Faculty"""
    __tablename__ = 'persons'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Basic info
    email = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    
    # Role: PARTICIPANT or FACULTY
    role = db.Column(db.String(20), nullable=False, default='PARTICIPANT')
    
    # RSVP status
    status = db.Column(db.String(20), default='INVITED')  # INVITED, ATTENDING, NOT_ATTENDING
    attending_responded = db.Column(db.Boolean, default=False)
    rsvp_responded_at = db.Column(db.DateTime)
    
    # Unique token for personalized links
    token = db.Column(db.String(100), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    
    # Info form completion
    info_completed = db.Column(db.Boolean, default=False)
    info_completed_at = db.Column(db.DateTime)
    
    # Info reminder tracking
    info_reminder_count = db.Column(db.Integer, default=0)
    info_last_reminder_sent = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    answers = db.relationship('Answer', backref='person', lazy=True, cascade='all, delete-orphan')
    hotel_request = db.relationship('HotelRequest', backref='person', uselist=False, cascade='all, delete-orphan')
    files = db.relationship('UploadedFile', backref='person', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Person {self.email} ({self.role})>'


class CustomQuestion(db.Model):
    """Editable questions for info form"""
    __tablename__ = 'custom_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    label = db.Column(db.String(200), nullable=False)
    field_type = db.Column(db.String(50), default='text')  # text, textarea, email, date, select, number
    required = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    answers = db.relationship('Answer', backref='question', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Question {self.label}>'


class Answer(db.Model):
    """Participant answers to custom questions"""
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('custom_questions.id'), nullable=False)
    
    answer_text = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Answer {self.id}>'


class HotelRequest(db.Model):
    """Hotel room requests for 3 nights"""
    __tablename__ = 'hotel_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False, unique=True)
    
    need_hotel = db.Column(db.Boolean, default=False)
    night1 = db.Column(db.Boolean, default=False)
    night2 = db.Column(db.Boolean, default=False)
    night3 = db.Column(db.Boolean, default=False)
    
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    
    # Hotel reminder tracking
    reminder_count = db.Column(db.Integer, default=0)
    last_reminder_sent = db.Column(db.DateTime)
    final_notice_sent = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<HotelRequest {self.person_id}>'


class UploadedFile(db.Model):
    """Track uploaded files from participants/faculty"""
    __tablename__ = 'uploaded_files'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False)
    
    filename = db.Column(db.String(255), nullable=False)  # Stored filename
    original_filename = db.Column(db.String(255), nullable=False)  # Original filename
    file_size = db.Column(db.Integer)
    
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UploadedFile {self.original_filename}>'

class EmailTemplate(db.Model):
    """Editable email templates"""
    __tablename__ = 'email_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Template identifier
    template_name = db.Column(db.String(100), unique=True, nullable=False)
    # e.g., 'rsvp_invitation', 'info_form_request', 'info_reminder', 
    #       'hotel_request', 'hotel_reminder', 'hotel_final_notice'
    
    display_name = db.Column(db.String(200), nullable=False)  # User-friendly name
    subject = db.Column(db.String(300), nullable=False)
    html_body = db.Column(db.Text, nullable=False)
    
    # Available variables for this template (stored as JSON string)
    available_variables = db.Column(db.Text)
    # e.g., "{{first_name}}, {{last_name}}, {{course_name}}, {{yes_link}}, {{no_link}}"
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailTemplate {self.template_name}>'