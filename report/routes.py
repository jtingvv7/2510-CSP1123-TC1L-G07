import logging
from flask import Blueprint, render_template, redirect, url_for , flash, abort, request
from functools import wraps
from flask_login import  login_required , current_user, login_user, logout_user
from datetime import datetime, timezone
from models import db
from models import User, Product, Transaction, Messages, Wallet
from sqlalchemy.exc import SQLAlchemyError 

report_bp = Blueprint("admin", __name__, template_folder="templates", static_folder="static")


#render report center
@report_bp.route("/report", methods=["GET"])
@login_required
def report_center():
    return render_template("report_center.html")

