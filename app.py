import os
from datetime import datetime, date
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    make_response,
)
from werkzeug.utils import secure_filename
from io import BytesIO
import pandas as pd
import sys  # <--- add this

print("PYTHON VERSION AT RUNTIME:", sys.version)  # <--- add this

from models import (
    db,
    Course,
    Participant,
    CustomQuestion,
    ParticipantAnswer,
    HotelRequest,
)
from email_utils import (
    decode_token,
    send_initial_rsvp_email,
    send_info_form_email,
    send_hotel_form_email,
    make_token,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key")
db_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")

# Normalize old postgres:// to postgresql://
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# If using PostgreSQL, force psycopg v3 driver
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


def admin_logged_in():
    return request.cookies.get("admin_pass") == ADMIN_PASSWORD


def admin_required(view):
    def wrapper(*args, **kwargs):
        if not admin_logged_in():
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    wrapper.__name__ = view.__name__
    return wrapper


@app.before_first_request
def create_tables():
    db.create_all()


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            resp = make_response(redirect(url_for("admin")))
            resp.set_cookie("admin_pass", ADMIN_PASSWORD, httponly=True)
            return resp
        flash("Wrong password", "error")
    return render_template(
        "message.html",
        title="Admin Login",
        body="""
    <form method="post">
      <label>Password: <input type="password" name="password"></label>
      <button type="submit">Login</button>
    </form>
    """,
    )


@app.route("/")
def index():
    return redirect(url_for("admin"))


@app.route("/admin", methods=["GET"])
@admin_required
def admin():
    courses = Course.query.order_by(Course.created_at.desc()).all()
    return render_template("admin.html", courses=courses)


@app.route("/admin/create-course", methods=["POST"])
@admin_required
def create_course():
    name = request.form.get("name")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    hotel_night1 = request.form.get("hotel_night1") or None
    hotel_night2 = request.form.get("hotel_night2") or None
    hotel_night3 = request.form.get("hotel_night3") or None

    c = Course(
        name=name,
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date),
        hotel_night1=date.fromisoformat(hotel_night1) if hotel_night1 else None,
        hotel_night2=date.fromisoformat(hotel_night2) if hotel_night2 else None,
        hotel_night3=date.fromisoformat(hotel_night3) if hotel_night3 else None,
    )
    db.session.add(c)
    db.session.commit()
    flash("Course created", "success")
    return redirect(url_for("admin"))


@app.route("/admin/course/<int:course_id>", methods=["GET"])
@admin_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    participants = Participant.query.filter_by(course_id=course.id).all()
    questions = CustomQuestion.query.filter_by(course_id=course.id).order_by(
        CustomQuestion.order_index
    )
    return render_template(
        "admin.html",
        courses=[course],
        course=course,
        participants=participants,
        questions=questions,
    )


@app.route("/admin/course/<int:course_id>/upload", methods=["POST"])
@admin_required
def upload_participants(course_id):
    course = Course.query.get_or_404(course_id)
    file = request.files.get("file")
    if not file:
        flash("No file uploaded", "error")
        return redirect(url_for("course_detail", course_id=course.id))

    filename = secure_filename(file.filename)
    if not filename.lower().endswith((".csv", ".xlsx", ".xls")):
        flash("Please upload a CSV or Excel file", "error")
        return redirect(url_for("course_detail", course_id=course.id))

    if filename.lower().endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    required_cols = {"email"}
    if not required_cols.issubset(set(df.columns.str.lower())):
        flash("File must contain at least an 'email' column", "error")
        return redirect(url_for("course_detail", course_id=course.id))

    # Normalize column names
    df.columns = [c.lower().strip() for c in df.columns]

    created = 0
    for _, row in df.iterrows():
        email = str(row.get("email", "")).strip()
        if not email:
            continue
        if Participant.query.filter_by(course_id=course.id, email=email).first():
            continue
        p = Participant(
            course_id=course.id,
            email=email,
            first_name=str(row.get("first_name", "")).strip() or None,
            last_name=str(row.get("last_name", "")).strip() or None,
        )
        db.session.add(p)
        created += 1

    db.session.commit()
    flash(f"Imported {created} participants.", "success")
    return redirect(url_for("course_detail", course_id=course.id))


@app.route("/admin/course/<int:course_id>/send-initial", methods=["POST"])
@admin_required
def send_initial(course_id):
    course = Course.query.get_or_404(course_id)
    participants = Participant.query.filter_by(course_id=course.id).all()
    sent = 0
    for p in participants:
        if p.status == "INVITED" and not p.attending_responded:
            send_initial_rsvp_email(p)
            sent += 1
    flash(f"Sent initial RSVP emails to {sent} participants.", "success")
    return redirect(url_for("course_detail", course_id=course.id))


@app.route("/rsvp/<token>")
def rsvp(token):
    try:
        pid = decode_token(token)
    except Exception:
        return render_template("message.html", title="Error", body="Invalid or expired link.")

    participant = Participant.query.get_or_404(pid)
    answer = request.args.get("answer")
    if answer == "yes":
        participant.status = "CONFIRMED"
        participant.attending_responded = True
        db.session.commit()
        # Send info and hotel email link
        send_info_form_email(participant)
        send_hotel_form_email(participant)
        return render_template(
            "message.html",
            title="Thank you",
            body="Thank you for confirming your attendance. Please check your email for the information form link.",
        )
    elif answer == "no":
        participant.status = "DECLINED"
        participant.attending_responded = True
        db.session.commit()
        return render_template(
            "message.html",
            title="Response recorded",
            body="Thank you. Your response has been recorded as not attending.",
        )
    else:
        return render_template("rsvp.html", participant=participant, token=token)


@app.route("/info-form/<token>", methods=["GET", "POST"])
def info_form(token):
    try:
        pid = decode_token(token)
    except Exception:
        return render_template("message.html", title="Error", body="Invalid or expired link.")

    participant = Participant.query.get_or_404(pid)
    if participant.status != "CONFIRMED":
        return render_template(
            "message.html",
            title="Not attending",
            body="You are not marked as attending this course.",
        )

    course = participant.course
    questions = CustomQuestion.query.filter_by(course_id=course.id).order_by(
        CustomQuestion.order_index
    )

    if request.method == "POST":
        # Save answers
        for q in questions:
            field_name = f"q_{q.id}"
            val = request.form.get(field_name, "").strip()
            ans = ParticipantAnswer.query.filter_by(
                participant_id=participant.id, question_id=q.id
            ).first()
            if not ans:
                ans = ParticipantAnswer(
                    participant_id=participant.id,
                    question_id=q.id,
                    answer_text=val,
                )
                db.session.add(ans)
            else:
                ans.answer_text = val

        # Hotel part
        need_hotel = request.form.get("need_hotel")
        hr = participant.hotel_request
        if not hr:
            hr = HotelRequest(participant_id=participant.id)
            db.session.add(hr)

        if need_hotel == "yes":
            hr.need_hotel = True
            hr.night1 = bool(request.form.get("night1"))
            hr.night2 = bool(request.form.get("night2"))
            hr.night3 = bool(request.form.get("night3"))
        elif need_hotel == "no":
            hr.need_hotel = False
            hr.night1 = hr.night2 = hr.night3 = False

        db.session.commit()

        flash("Information saved. Thank you!", "success")
        return redirect(url_for("info_form", token=token))

    # GET: prefill
    answers_map = {
        a.question_id: a.answer_text
        for a in ParticipantAnswer.query.filter_by(participant_id=participant.id).all()
    }
    hotel = participant.hotel_request
    return render_template(
        "info_form.html",
        participant=participant,
        course=course,
        questions=questions,
        answers_map=answers_map,
        hotel=hotel,
    )


@app.route("/admin/course/<int:course_id>/add-question", methods=["POST"])
@admin_required
def add_question(course_id):
    course = Course.query.get_or_404(course_id)
    label = request.form.get("label")
    required = bool(request.form.get("required"))
    order_index = int(request.form.get("order_index") or 0)
    q = CustomQuestion(
        course_id=course.id,
        label=label,
        required=required,
        order_index=order_index,
    )
    db.session.add(q)
    db.session.commit()
    flash("Question added", "success")
    return redirect(url_for("course_detail", course_id=course.id))


@app.route("/admin/course/<int:course_id>/hotel-summary")
@admin_required
def hotel_summary(course_id):
    course = Course.query.get_or_404(course_id)
    prs = Participant.query.filter_by(course_id=course.id, status="CONFIRMED").all()
    night1 = night2 = night3 = 0
    seq_counts = {}
    for p in prs:
        hr = p.hotel_request
        if not hr or not hr.need_hotel:
            continue
        if hr.night1:
            night1 += 1
        if hr.night2:
            night2 += 1
        if hr.night3:
            night3 += 1
        seq = (
            ("1" if hr.night1 else "-")
            + ("2" if hr.night2 else "-")
            + ("3" if hr.night3 else "-")
        )
        seq_counts[seq] = seq_counts.get(seq, 0) + 1

    return render_template(
        "hotel_summary.html",
        course=course,
        night1=night1,
        night2=night2,
        night3=night3,
        seq_counts=seq_counts,
    )


@app.route("/admin/course/<int:course_id>/export")
@admin_required
def export_excel(course_id):
    course = Course.query.get_or_404(course_id)
    participants = Participant.query.filter_by(course_id=course.id).all()
    questions = CustomQuestion.query.filter_by(course_id=course.id).order_by(
        CustomQuestion.order_index
    )

    rows = []
    for p in participants:
        row = {
            "First Name": p.first_name,
            "Last Name": p.last_name,
            "Email": p.email,
            "Status": p.status,
        }
        answers = {
            a.question_id: a.answer_text
            for a in ParticipantAnswer.query.filter_by(participant_id=p.id).all()
        }
        for q in questions:
            row[q.label] = answers.get(q.id, "")
        hr = p.hotel_request
        row["Need Hotel"] = hr.need_hotel if hr else None
        row["Night1"] = hr.night1 if hr else False
        row["Night2"] = hr.night2 if hr else False
        row["Night3"] = hr.night3 if hr else False
        rows.append(row)

    df = pd.DataFrame(rows)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Participants")
    output.seek(0)

    filename = f"course_{course.id}_export.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    app.run(debug=True)