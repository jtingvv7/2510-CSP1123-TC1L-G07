import logging
from flask import Blueprint, render_template, redirect, url_for , flash, abort
from functools import wraps
from flask_login import  login_required , current_user, login_user, logout_user
from datetime import datetime, timezone
from models import db
from models import User, Product, Transaction, Messages
from sqlalchemy.exc import SQLAlchemyError

admin_bp = Blueprint("admin", __name__, template_folder="templates", static_folder="static")

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
    return render_template("dashboard.html")

#check all users
@admin_bp.route("/users")
@login_required
@admin_required
def users():
    all_users = User.query.all()
    return render_template("users.html", users=all_users)

#make other user become admin
@admin_bp.route("/make_admin/<int:user_id>")
@login_required
@admin_required
def make_admin(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("User not found","danger")
        return redirect(url_for("admin.users"))
    user.role = "admin"
    db.session.commit()
    flash(f"{user.name} is now an admin", "success")
    return redirect(url_for("admin.users"))

#delete user
@admin_bp.route("/delete_user/<int:user_id>")
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("User not found","danger")
        return redirect(url_for("admin.users"))
    #prevent admin delete own acc
    if user.id == current_user.id:
        flash("You cannot delete your own account!","warning")
        return redirect(url_for("admin.users"))
    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.name} has been deleted!","success")
    return redirect(url_for("admin.users"))