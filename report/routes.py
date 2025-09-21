import logging
import time
import os
from flask import Blueprint, render_template, redirect, url_for , flash, abort, request
from functools import wraps
from flask_login import  login_required , current_user, login_user, logout_user
from datetime import datetime, timezone
from models import db
from models import User, Product, Transaction, Messages, Wallet, Report
from sqlalchemy.exc import SQLAlchemyError 
from werkzeug.utils import secure_filename

report_bp = Blueprint("report", __name__, template_folder="templates", static_folder="static")

UPLOAD_FOLDER = os.path.join("static","uploads","reports")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# render report center
@report_bp.route("/report", methods=["GET"])
@login_required
def report_center():
    return render_template("report_center.html")

# report form (submit)
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
            filename = f"{current_user.id}{int(time.time())}{secure_filename(file.filename)}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        new_report = Report(
            reporter_id=current_user.id,
            reported_type=report_type,
            reason=reason,
            evidence_file=filename,
            status="pending"
        )
        
        db.session.add(new_report)
        db.session.commit()
        flash("Your report has been submitted. Admin will review it soon.", "success")
        return redirect(url_for("report.report_center"))

    return render_template("report_form.html")

