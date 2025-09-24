import logging
import time
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from models import db, Report, User, Product, Transaction, Messages, Announcement
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

report_bp = Blueprint("report", __name__, template_folder="templates", static_folder="static")

UPLOAD_FOLDER = os.path.join("static", "uploads", "reports")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Announcement
@report_bp.route("/announcements")
@login_required
def announcements():
    now = datetime.now(timezone.utc)
    announcements = Announcement.query.filter(
        ((Announcement.user_id == None) | (Announcement.user_id == current_user.id)) &
        ((Announcement.expires_at == None) | (Announcement.expires_at > now))
    ).order_by(Announcement.created_at.desc()).all()

    return render_template("announcement.html", announcements=announcements, now=now, timedelta=timedelta)


# Report Center 
@report_bp.route("/report", methods=["GET"])
@login_required
def report_center():
    my_reports = Report.query.filter_by(reporter_id=current_user.id).all()
    return render_template("report_center.html", reports=my_reports)



# Report Form 
@report_bp.route("/report/submit", methods=["GET", "POST"])
@login_required
def report_submit():
    if request.method == "POST":
        report_type = request.form.get("report_type")
        reported_id = int(request.form.get("reported_id"))   # ensure it is int
        reason = request.form.get("reason")
        file = request.files.get("evidence")

        filename = None
        if file and allowed_file(file.filename):
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            filename = f"{current_user.id}{int(time.time())}{secure_filename(file.filename)}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        appeal_deadline = datetime.now(timezone.utc) + timedelta(days=5)

        # Determine which user should receive the announcement
        target_user_id = None

        if report_type == "user":
            # report directly against a user
            target_user_id = reported_id

        elif report_type == "product":
            # report against a product → send announcement to product owner
            product = Product.query.get(reported_id)
            if product:
                target_user_id = product.seller_id

        elif report_type == "transaction":
            # report against a transaction → notify the other party
            transaction = Transaction.query.get(reported_id)
            if transaction:
                if current_user.id == transaction.buyer_id:
                    target_user_id = transaction.seller_id   # reporter is buyer → notify seller
                elif current_user.id == transaction.seller_id:
                    target_user_id = transaction.buyer_id   # reporter is seller → notify buyer

                #  Create a new Report
        new_report = Report(
            reporter_id=current_user.id,
            reported_type=report_type,
            reported_id=reported_id,         # can be product.id / user.id / transaction.id
            reported_user_id = target_user_id,
            reason=reason,
            evidence_file=filename,
            status="pending",
            date_report=datetime.now(timezone.utc),
            appeal_deadline=appeal_deadline,
        )
        
        try:

            #save report
            db.session.add(new_report)
            db.session.flush()

            #  Create an Announcement
            deadline_str = (appeal_deadline + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")

            new_announcement = Announcement(
                user_id=target_user_id,          # the user who should see this announcement
                report_id=new_report.id,         # link to the report
                author_id=None,       
                title="⚠ You have been reported!",
                content=f"Please submit your appeal before {deadline_str}.",
                expires_at=appeal_deadline
            )

            db.session.add(new_announcement)
            db.session.commit()
            flash("Your report has been submitted. Admin will review it soon.", "success")
        except SQLAlchemyError:
            db.session.rollback()
            flash("Error submitting report. Please try again.", "danger")

        return redirect(url_for("report.report_center"))

    # pre-fill data
    pre_type = request.args.get("type")
    pre_id = request.args.get("pre_id")

    return render_template("report_form.html", pre_id=pre_id, pre_type=pre_type)



# My report
@report_bp.route("/report/my_reports", methods=["GET"])
@login_required
def my_reports():
    reports = Report.query.filter_by(reporter_id=current_user.id).all()
    reports_against_me = Report.query.filter_by(reported_user_id=current_user.id).all()
    return render_template("my_reports.html", reports=reports, reports_against_me=reports_against_me, datetime=datetime,timedelta=timedelta)


# Appeal report
@report_bp.route("/appeal/<int:report_id>", methods=["GET", "POST"])
@login_required
def submit_appeal(report_id):
    report = Report.query.get_or_404(report_id)

    if report.reported_user_id != current_user.id:
        flash("You are not authorized to appeal this report.", "danger")
        return redirect(url_for("index"))
    
    if report.appeal_deadline:
        deadline = report.appeal_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) > deadline:
            flash("The appeal deadline has expired.", "danger")
            return redirect(url_for("index"))

    if request.method == "POST":
        appeal_text = request.form.get("reason")
        appeal_file = request.files.get("evidence")

        if not appeal_text:
            flash("You must provide a reason for your appeal.", "danger")
            return redirect(url_for("report.submit_appeal", report_id=report_id))

        filename = None
        if appeal_file and appeal_file.filename != "":
            filename = f"appeal_{report_id}_{secure_filename(appeal_file.filename)}"
            file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            appeal_file.save(file_path)
            report.appeal_file = filename

        report.appeal_text = appeal_text
        report.appeal_status = "submitted"
        db.session.commit()

        flash("Your appeal has been submitted successfully!", "success")
        return redirect(url_for("report.my_reports"))   

    return render_template(
        "appeal_form.html",
        report=report,
        reason=report.reason,
        evidence_file=report.evidence_file,
        appeal_deadline=report.appeal_deadline,
        datetime=datetime,
        timedelta=timedelta
    )

# ---------------- API endpoints ----------------

# get my products include bought and sell
@report_bp.route("/api/my_products")
@login_required
def my_products():
    selling = Product.query.filter_by(seller_id=current_user.id).all()
    bought_transactions = Transaction.query.filter_by(buyer_id=current_user.id).all()
    bought = [t.product for t in bought_transactions if t.product]
    all_products = {p.id: p for p in (selling + bought)}.values()
    return jsonify([{"id": p.id, "name": p.name} for p in all_products])

# get users I have conversation with
@report_bp.route("/api/my_users")
@login_required
def my_users():
    user_ids = {m.receiver_id for m in Messages.query.filter_by(sender_id=current_user.id)} | \
               {m.sender_id for m in Messages.query.filter_by(receiver_id=current_user.id)}
    users = User.query.filter(User.id.in_(user_ids)).all()
    return jsonify([{"id": u.id, "name": u.name} for u in users])

# get my transactions
@report_bp.route("/api/my_transactions")
@login_required
def my_transactions():
    transactions = Transaction.query.filter(
        (Transaction.buyer_id == current_user.id) | (Transaction.seller_id == current_user.id)
    ).all()
    return jsonify([{"id": t.id, "name": t.product.name if t.product else "Unknown"} for t in transactions])