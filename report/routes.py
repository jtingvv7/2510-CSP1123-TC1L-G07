import logging
import time
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timezone
from models import db, Report, User, Product, Transaction, Messages
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

report_bp = Blueprint("report", __name__, template_folder="templates", static_folder="static")

UPLOAD_FOLDER = os.path.join("static", "uploads", "reports")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

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
        reported_id = request.form.get("reported_id")
        reason = request.form.get("reason")
        file = request.files.get("evidence")

        filename = None
        if file and allowed_file(file.filename):
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            filename = f"{current_user.id}_{int(time.time())}_{secure_filename(file.filename)}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        new_report = Report(
            reporter_id=current_user.id,
            reported_type=report_type,
            reported_id=reported_id,
            reason=reason,
            evidence_file=filename,
            status="pending",
            date_report=datetime.now(timezone.utc)
        )

        try:
            db.session.add(new_report)
            db.session.commit()
            flash("Your report has been submitted. Admin will review it soon.", "success")
        except SQLAlchemyError:
            db.session.rollback()
            flash("Error submitting report. Please try again.", "danger")

        return redirect(url_for("report.report_center"))
    pre_type = request.args.get("type")
    pre_id = request.args.get("pre_id")

    return render_template("report_form.html", pre_id = pre_id, pre_type = pre_type)

# My report
@report_bp.route("/report/my_reports", methods=["GET"])
@login_required
def my_reports():
    reports = Report.query.filter_by(reporter_id=current_user.id).all()
    return render_template("my_reports.html", reports=reports)

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