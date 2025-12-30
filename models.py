---

### `models.py`

```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    hotel_night1 = db.Column(db.Date, nullable=True)
    hotel_night2 = db.Column(db.Date, nullable=True)
    hotel_night3 = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    participants = db.relationship("Participant", backref="course", lazy=True)
    questions = db.relationship("CustomQuestion", backref="course", lazy=True)


class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    status = db.Column(
        db.String(50),
        default="INVITED",
    )  # INVITED, CONFIRMED, DECLINED
    attending_responded = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    answers = db.relationship("ParticipantAnswer", backref="participant", lazy=True)
    hotel_request = db.relationship(
        "HotelRequest", backref="participant", lazy=True, uselist=False
    )
    reminders = db.relationship("ReminderTracking", backref="participant", lazy=True)


class CustomQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    label = db.Column(db.String(255), nullable=False)
    field_type = db.Column(
        db.String(50), default="text"
    )  # text, textarea, yesno, select (extend as needed)
    required = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)


class ParticipantAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(
        db.Integer, db.ForeignKey("participant.id"), nullable=False
    )
    question_id = db.Column(
        db.Integer, db.ForeignKey("custom_question.id"), nullable=False
    )
    answer_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    question = db.relationship("CustomQuestion")


class HotelRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(
        db.Integer, db.ForeignKey("participant.id"), nullable=False
    )
    need_hotel = db.Column(db.Boolean, nullable=True)  # None if unanswered
    night1 = db.Column(db.Boolean, default=False)
    night2 = db.Column(db.Boolean, default=False)
    night3 = db.Column(db.Boolean, default=False)
    finalized = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReminderTracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(
        db.Integer, db.ForeignKey("participant.id"), nullable=False
    )
    type = db.Column(
        db.String(50), nullable=False
    )  # RSVP, INFO, HOTEL, HOTEL_FINAL
    count_sent = db.Column(db.Integer, default=0)
    last_sent_at = db.Column(db.DateTime, nullable=True)
    max_allowed = db.Column(db.Integer, default=4)