import logging
from flask import Blueprint, render_template, redirect, url_for , flash, request, jsonify
from flask_login import  login_required , current_user, login_user
from datetime import datetime, timezone
from models import db
from models import User, Product, Transaction, Messages
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level = logging.INFO, filename = "app.log")
messages_bp = Blueprint('messages', __name__, template_folder='templates', static_folder='static')

#fake inbox


#view conversation
@messages_bp.route("/chat/<int:user_id>/json",methods=["GET"])
@login_required
def chat_json(user_id):
    conversation = Messages.query.filter(
        ((Messages.sender_id == current_user.id) & (Messages.receiver_id == user_id)) |
          ((Messages.sender_id == user_id) & (Messages.receiver_id == current_user.id))
    ).order_by(Messages.timestamp).all()

    #return JSON data to back end
    return jsonify([
        {
        "sender" : "Me" if msg.sender_id == current_user.id else "Them",
        "content" : msg.content,
        "time" : msg.timestamp.strftime("%H:%M:%S")
    }for msg in conversation
    ])   


#send messages
@messages_bp.route("/send/<int:user_id>",methods=["POST"])
@login_required
def send_messages(user_id):
    content = request.form.get("content") #use for get content from front end
    if content:
        new_msg = Messages(sender_id=current_user.id, receiver_id= user_id, content=content)
        db.session.add(new_msg)
        db.session.commit()
        return jsonify({"status": "ok", "message": content})
    return jsonify({"status": "error", "message": "empty content"})

#chat page
@messages_bp.route("/chat/<int:user_id>")
@login_required
def chat(user_id):
    return render_template("chat.html", user_id = user_id)

#inbox
@messages_bp.route("/inbox")
@login_required
def inbox():
    #find all user relationship with current user
    sent = db.session.query(Messages.receiver_id).filter_by(sender_id=current_user.id)
    received = db.session.query(Messages.sender_id).filter_by(receiver_id=current_user.id)
    user_ids = {uid for (uid,) in sent.union(received).all()} #prevent repeat

    users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else[]
    return render_template("inbox.html", users=users)