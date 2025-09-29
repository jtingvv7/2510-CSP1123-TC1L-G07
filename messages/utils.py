from models import db, User, Product, Transaction, Messages

def create_message(sender_id=1, receiver_id=None, content=None, transaction_id=None, message_type="system"):
    if sender_id is None:
        sender_id = 1  # System user ID
    if receiver_id is None or content is None:
        raise ValueError("receiver_id and content are required")

    msg = Messages(
        sender_id=int(sender_id),   # force integer
        receiver_id=int(receiver_id),
        transaction_id=transaction_id,
        content=content,
        message_type=message_type,
        is_read=True
    )
    db.session.add(msg)
    db.session.commit()
    return msg