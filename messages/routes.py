import logging
import os
from flask import Blueprint, render_template, redirect, url_for , flash, request, jsonify, current_app
from flask_login import  login_required , current_user, login_user
from .utils import create_message
from datetime import timedelta
from models import db
from models import User, Product, Transaction, Messages
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename
from extensions import db


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

@messages_bp.route("/send_system_message")
def send_system_message():
    create_message(sender_id=1, receiver_id=2, content=" System message")
    return "System message sent!"

#chat json
@messages_bp.route("/chat/<int:user_id>/json", methods=["GET"])
@login_required
def chat_json(user_id):
    conversation = Messages.query.filter(
        ((Messages.sender_id == current_user.id) & (Messages.receiver_id == user_id)) |
        ((Messages.sender_id == user_id) & (Messages.receiver_id == current_user.id))
    ).order_by(Messages.timestamp).all()

    result = []
    for msg in conversation:
        msg_type = getattr(msg, "message_type", "text")  # default as text

        data = {
            "sender_id": msg.sender_id,
            "sender_name": msg.sender.name if msg_type != "system" else "System",
            "sender_avatar": (
                url_for('static', filename=f'uploads/profiles/{msg.sender.profile_pic}')
                if msg.sender.profile_pic else f"https://i.pravatar.cc/100?u={msg.sender.id}"
            ) if msg_type != "system" else None,  # system messages
            "content": msg.content,
            "message_type": msg_type,
            "time": (msg.timestamp + timedelta(hours=8)).strftime("%H:%M:%S")
        }

        # if msg type = transaction insert details
        if msg_type == "transaction" and getattr(msg, "transaction_id", None):
            tx = Transaction.query.get(msg.transaction_id)
            if tx:
                data["transaction"] = {
                    "id": tx.id,
                    "product": tx.product.name if tx.product else "Unknown",
                    "price": tx.product.price if tx.product else 0,
                    "status": tx.status
                }

        result.append(data)

        for msg in conversation:
            if msg.receiver_id == current_user.id and not msg.is_read:
                msg.is_read = True
        db.session.commit()

    return jsonify(result)

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
@messages_bp.route("/send_transaction/<int:user_id>/<int:transaction_id>", methods=["POST"])
@login_required
def send_transaction(user_id, transaction_id):
    new_msg = Messages(
        sender_id=current_user.id,
        receiver_id=user_id,
        transaction_id=transaction_id,
        message_type="transaction"
    )
    db.session.add(new_msg)
    db.session.commit()
    return jsonify({"status": "ok"})

#chat page
@messages_bp.route("/chat/<int:user_id>")
@login_required
def chat(user_id):
    user = User.query.get_or_404(user_id)

    Messages.query.filter_by(sender_id=user_id, receiver_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()

    transactions = Transaction.query.filter(
        ((Transaction.buyer_id == current_user.id) & (Transaction.seller_id == user_id)) |
        ((Transaction.seller_id == current_user.id) & (Transaction.buyer_id == user_id))
    )

    return render_template("chat.html", user=user, user_id=user_id, transactions=transactions)

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


# helper function, not a route
SYSTEM_USER_ID = 1

def issue_warning(user_id):
    user = User.query.get(user_id)
    if not user:
        return {"message": "User not found"}, 404

    # Increment warnings
    user.warnings += 1

    # Get system user
    system_user = User.query.filter_by(email="system@system.com").first()
    if not system_user:
        raise Exception("System user not found")

    if user.warnings >= 3:
        user.is_banned = True
        db.session.commit()

        warning_msg = Messages(
            sender_id=system_user.id,
            receiver_id=user.id,
            content="⚠️ Your account has been banned due to 3 warnings.",
            message_type="system"
        )
        db.session.add(warning_msg)
        db.session.commit()

        return {"message": "User banned due to 3 warnings."}

    db.session.commit()

    warning_msg = Messages(
        sender_id=system_user.id,
        receiver_id=user.id,
        content=f"⚠️ Warning issued. Current warnings: {user.warnings}. 3 warnings = ban.",
        message_type="system"
    )
    db.session.add(warning_msg)
    db.session.commit()

    return {"message": f"Warning issued. Current warnings: {user.warnings}"}