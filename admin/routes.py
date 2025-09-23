import logging
import time
import os
from flask import Blueprint, render_template, redirect, url_for , flash, abort, request, current_app
from functools import wraps
from flask_login import  login_required , current_user, login_user, logout_user
from datetime import datetime, timezone
from models import db
from werkzeug.utils import secure_filename
from models import User, Product, Transaction, Messages, Wallet, Report
from sqlalchemy.exc import SQLAlchemyError 

admin_bp = Blueprint("admin", __name__, template_folder="templates", static_folder="static")

UPLOAD_FOLDER = os.path.join("static", "uploads", "products")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

#ensure only admin can enter
def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = User.query.get(current_user.id)
        print("DEBUG: admin_required called,user=",current_user)
        if not user or user.role != "admin":
            abort(403)
        print("DEBUG: user is admin,continue")
        return func(*args, **kwargs)
    return wrapper

#dashboard html 
@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    user_count = User.query.count()
    product_count = Product.query.count()
    transaction_count = Transaction.query.count()
    return render_template("dashboard.html",
                           user_count = user_count,
                           product_count = product_count,
                           transaction_count = transaction_count)

#check all users
@admin_bp.route("/manage_users")
@login_required
@admin_required
def manage_users():
    all_users = User.query.all()
    return render_template("manage_users.html", users=all_users)

#check all products
@admin_bp.route("/manage_products")
@login_required
@admin_required
def manage_products():
    all_products = Product.query.all()
    return render_template("manage_products.html", products = all_products)

#check all transactions
@admin_bp.route("/manage_transactions")
@login_required
@admin_required
def manage_transactions():
    all_transactions = Transaction.query.all()
    return render_template("manage_transactions.html", transactions = all_transactions)

#check all wallets
@admin_bp.route("/manage_wallets")
@login_required
@admin_required
def manage_wallets():
    all_wallets = Wallet.query.all()
    return render_template("manage_wallets.html", wallets = all_wallets)

#check all messages
@admin_bp.route("/manage_messages")
@login_required
@admin_required
def manage_messages():
    all_messages = Messages.query.all()
    return render_template("manage_messages.html", messages = all_messages)

#check all reports
@admin_bp.route("/manage_reports")
@login_required
@admin_required
def manage_reports():
    reports = Report.query.order_by(Report.date_report.desc()).all()
    return render_template("manage_reports.html", reports=reports)

################## user management #####################

#make other user become admin
@admin_bp.route("/make_admin/<int:user_id>")
@login_required
@admin_required
def make_admin(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("User not found","danger")
        return redirect(url_for("manage_users"))
    user.role = "admin"
    db.session.commit()
    flash(f"{user.name} is now an admin", "success")
    return redirect(url_for("manage_users"))

#delete user
@admin_bp.route("/delete_user/<int:user_id>")
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("User not found","danger")
        return redirect(url_for("manage_users"))
    #prevent admin delete own acc
    if user.id == current_user.id:
        flash("You cannot delete your own account!","warning")
        return redirect(url_for("manage_users"))
    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.name} has been deleted!","success")
    return redirect(url_for("manage_users"))

################## product management #####################

# add product
@admin_bp.route("/products/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_product():
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        description = request.form.get("description")
        file = request.files.get("image")

        if file and file.filename != "" and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"product_{int(time.time())}.{ext}"
            upload_path = os.path.join(current_app.root_path, "static", "uploads", "products")
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename.split("/")[-1]))

            db_filename = f"products/{filename}"

        else:
            db_filename = "products/default_product.jpg"

        new_product = Product(
            name=name,
            price=price,
            description=description,
            is_sold=False,
            seller_id = current_user.id,
            image = db_filename,
            is_active = True)
        db.session.add(new_product)
        db.session.commit()

        flash("Product added successfully!", "success")
        return redirect(url_for("admin.manage_products"))

    return render_template("add_product.html")
    

# edit product
@admin_bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        product.name = request.form.get("name")
        product.price = request.form.get("price")
        product.description = request.form.get("description")

        file = request.files.get("image")
        if file and file.filename:
            filename = f"{product.id}{int(time.time())}{secure_filename(file.filename)}"
            upload_path = os.path.join("static", "uploads", "products", filename)
            file.save(upload_path)
            product.image = filename  

        db.session.commit()
        flash("Product updated successfully!", "success")
        return redirect(url_for("admin.manage_products"))

    return render_template("edit_product.html", product=product)


# delete product
@admin_bp.route("/products/delete/<int:product_id>", methods=["POST"])
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()

    flash("Product deleted successfully!", "success")
    return redirect(url_for("admin.manage_products"))

################## transactions management #####################

#delete transaction
@admin_bp.route("/delete_transactions/<int:transaction_id>", methods=["POST"])
@login_required
@admin_required
def delete_transaction(transaction_id):
    tx = Transaction.query.get_or_404(transaction_id)
    db.session.delete(tx)
    db.session.commit()
    flash("Transaction deleted successfully","success")
    return redirect(url_for("admin.manage_transactions"))


#update transacton status(when error)
@admin_bp.route("/update_transaction/<int:transaction_id>", methods=["POST"])
@login_required
@admin_required
def update_transaction(transaction_id):
    tx = Transaction.query.get_or_404(transaction_id)
    new_status = request.form.get("new_status")
    if new_status:
        tx.status = new_status
        db.session.commit()
        flash(f"Transaction status updated to {new_status}","success")
    else:
        flash("Invalid status", "danger")
    return redirect(url_for("admin.manage_transactions"))

################## wallet management #####################

#simulated recharge
@admin_bp.route("/recharge_wallet/<int:user_id>", methods=["POST"])
@login_required
def recharge_wallet(user_id):
    amount = float(request.form.get("amount", 0))
    wallet = Wallet.query.filter_by(user_id=user_id).first()

    if wallet:
        wallet.balance += amount   
    else:
        wallet = Wallet(user_id=user_id, balance=amount)
        db.session.add(wallet)

    db.session.commit()
    flash(f"Added RM{amount:.2f} to User {user_id}'s wallet", "success")
    return redirect(url_for("admin.manage_wallets"))

################## messages management #####################

#delete messages
@admin_bp.route("/delete_message/<int:message_id>")
@login_required
@admin_required
def delete_message(message_id):
    msg = Messages.query.get_or_404(message_id)
    db.session.delete(msg)
    db.session.commit()
    flash("Message deleted", "success")
    return redirect(url_for("admin.manage_messages"))

################## report management #####################

#resolve report
@admin_bp.route("/resolve_report/<int:report_id>")
@login_required
@admin_required
def resolve_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.status = "resolved"
    db.session.commit()
    flash("Report resolved!", "success")
    return redirect(url_for("admin.manage_reports"))

#delete report
@admin_bp.route("/delete_report/<int:report_id>")
@login_required
@admin_required
def delete_report(report_id):
    report = Report.query.get_or_404(report_id)
    db.session.delete(report)
    db.session.commit()
    flash("Report deleted!", "danger")
    return redirect(url_for("admin.manage_reports"))

#update report
@admin_bp.route("/update_report/<int:report_id>", methods=["POST"])
@login_required
@admin_required
def update_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.admin_comment = request.form.get("admin_comment")
    db.session.commit()
    flash("Admin comment updated.", "success")
    return redirect(url_for("admin.manage_reports"))