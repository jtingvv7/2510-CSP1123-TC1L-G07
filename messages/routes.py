import logging
import os
from flask import Blueprint, render_template, redirect, url_for , flash, request, jsonify
from flask_login import  login_required , current_user, login_user, current_app
from datetime import timedelta
from models import db
from models import User, Product, Transaction, Messages
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

logging.basicConfig(level = logging.INFO, filename = "app.log")
messages_bp = Blueprint('messages', __name__, template_folder='templates', static_folder='static')

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


''' for test
#fake inbox
@messages_bp.route("/test_inbox")
@login_required
def test_inbox():
    user1 = User.query.get(1)
    user2 = User.query.get(2)
    if not user1 or not user2 :
        return"create at least 2 user in database",400
    
    #insert test message
    test_msg = Messages(sender_id=user1.id, receiver_id=user2.id, content="hello from user1")
    db.session.add(test_msg)
    db.session.commit()
    
    return"already insert test message"

#fake messages
@messages_bp.route("/fake_messages")
@login_required
def fake_messages():
    # confirm user1 and user2 is exist
    user1 = User.query.filter_by(email="test1@gmail.com").first()
    user2 = User.query.filter_by(email="test2@gmail.com").first()

    if not user1 or not user2:
        return "Please run /transaction/fake_login first", 400

    # insert fake messages
    msg1 = Messages(sender_id=user1.id, receiver_id=user2.id, content="Hello from test1")
    msg2 = Messages(sender_id=user2.id, receiver_id=user1.id, content="Hi, this is test2")
    db.session.add_all([msg1, msg2])
    db.session.commit()

    return "Fake messages inserted. Now go check /messages/inbox"
'''

#view conversation
@messages_bp.route("/chat/<int:user_id>/json", methods=["GET"])
@login_required
def chat_json(user_id):
    conversation = Messages.query.filter(
        ((Messages.sender_id == current_user.id) & (Messages.receiver_id == user_id)) |
        ((Messages.sender_id == user_id) & (Messages.receiver_id == current_user.id))
    ).order_by(Messages.timestamp).all()

    return jsonify([
        {
            "sender_id": msg.sender_id,
            "sender_name": msg.sender.name,
            "sender_avatar": (
                url_for('static', filename=f'uploads/profiles/{msg.sender.profile_pic}')
                if msg.sender.profile_pic else f"https://i.pravatar.cc/40?u={msg.sender.id}"
            ),
            "content": msg.content,
            "time": (msg.timestamp + timedelta(hours=8)).strftime("%H:%M:%S")  # convert to MYT
        }
        for msg in conversation 
        ])

#send messages
@messages_bp.route("/send/<int:user_id>",methods=["POST"])
@login_required
def send_messages(user_id):
    content = request.form.get("content") #use for get content from front end
    if content:
        new_msg = Messages(sender_id=current_user.id, receiver_id= user_id, content=content, is_read = False)
        db.session.add(new_msg)
        db.session.commit()
        return jsonify({"status": "ok", "message": content})
    return jsonify({"status": "error", "message": "empty content"})

#send image
@messages_bp.route("/send_image/<int:user_id>", methods=["POST"])
@login_required
def send_image(user_id):
    if "image" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"})

    file = request.files["image"]
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], "messages", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)

        new_msg = Messages(
            sender_id=current_user.id,
            receiver_id=user_id,
            content=f"uploads/messages/{filename}",
            message_type="image"
        )
        db.session.add(new_msg)
        db.session.commit()
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "Invalid file"})


#send transaction


#chat page
@messages_bp.route("/chat/<int:user_id>")
@login_required
def chat(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("chat.html", user=user, user_id=user_id)

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