import logging
from flask import Blueprint, render_template, redirect, url_for , flash, request
from flask_login import  login_required , current_user, login_user
from datetime import datetime, timezone
from models import db
from models import User, Product, Transaction, Messages
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level = logging.INFO, filename = "app.log")
messages_bp = Blueprint('messages', __name__, template_folder='templates', static_folder='static')

#view conversation
@messages_bp.route("/chat/<int:user_id>",methods=["POST"])
@login_required
def chat(user_id):
    conversation = Messages.query.filter(
        ((Message.sender_id == current_user.id)  )
    ).order_by(Message.timestamp).all()





#send messages
@messages_bp.route("/send/<int:user_id>",methods=["POST"])
@login_required
def send_messages(user_id):
    content = request.form.get("content") #use for get content from front end
    if content:
        new_msg = Messages(sender_id=current_user.id, receiver_id= user_id, content=content)
        db.session.commit(new_msg)
        db.session.commit()
    return redirect(url_for("messages.chat",user_id=user_id))

