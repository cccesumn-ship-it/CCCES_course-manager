from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import secrets

db = SQLAlchemy()


class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    hotel_night1 = db.Column(db.Date, nullable=True)
    hotel_night2 = db.Column(db.Date, nullable=True)
    hotel_night3 = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    participants = db.relationship('Participant', back_populates='course', cascade='all, delete-orphan')
    questions = db.relationship('CustomQuestion', back_populates='course', cascade='all, delete-orphan', order_by='CustomQuestion.order_index')
    
    def __repr__(self):
        return f'<Course {self.name}>'


class Participant(db.Model):
    __tablename__ = 'participants'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(20), default='PARTICIPANT')  # 'PARTICIPANT' or 'FACULTY'
    status = db.Column(db.String(20), default='INVITED')  # 'INVITED', 'ATTENDING', 'NOT_ATTENDING'
    attending_responded = db.Column(db.Boolean, default=False)
    token = db.Column(db.String(100), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', back_populates='participants')
    answers = db.relationship('ParticipantAnswer', back_populates='participant', cascade='all, delete-orphan')
    hotel_request = db.relationship('HotelRequest', back_populates='participant', uselist=False, cascade='all, delete-orphan')
    files = db.relationship('ParticipantFile', back_populates='participant', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Participant {self.email}>'


class CustomQuestion(db.Model):
    __tablename__ = 'custom_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    label = db.Column(db.String(500), nullable=False)
    field_type = db.Column(db.String(50), default='text')  # 'text', 'textarea', 'email', 'date'
    required = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', back_populates='questions')
    answers = db.relationship('ParticipantAnswer', back_populates='question', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CustomQuestion {self.label}>'


class ParticipantAnswer(db.Model):
    __tablename__ = 'participant_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('custom_questions.id'), nullable=False)
    answer_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    participant = db.relationship('Participant', back_populates='answers')
    question = db.relationship('CustomQuestion', back_populates='answers')
    
    def __repr__(self):
        return f'<ParticipantAnswer {self.id}>'


class HotelRequest(db.Model):
    __tablename__ = 'hotel_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'), nullable=False, unique=True)
    need_hotel = db.Column(db.Boolean, default=False)
    night1 = db.Column(db.Boolean, default=False)
    night2 = db.Column(db.Boolean, default=False)
    night3 = db.Column(db.Boolean, default=False)
    finalized = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    participant = db.relationship('Participant', back_populates='hotel_request')
    
    @staticmethod
    def get_or_create(participant_id):
        """Get existing hotel request or create new one"""
        hotel_request = HotelRequest.query.filter_by(participant_id=participant_id).first()
        if hotel_request:
            return hotel_request, False
        else:
            hotel_request = HotelRequest(participant_id=participant_id)
            db.session.add(hotel_request)
            return hotel_request, True
    
    def __repr__(self):
        return f'<HotelRequest Participant:{self.participant_id}>'


class ParticipantFile(db.Model):
    __tablename__ = 'participant_files'
    
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    mime_type = db.Column(db.String(100), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    participant = db.relationship('Participant', back_populates='files')
    
    def __repr__(self):
        return f'<ParticipantFile {self.filename}>'


class ReminderTracking(db.Model):
    __tablename__ = 'reminder_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'), nullable=False)
    reminder_type = db.Column(db.String(50), nullable=False)  # 'RSVP', 'INFO_FORM', 'HOTEL'