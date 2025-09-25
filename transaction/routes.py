import logging
import time
import os
from flask import Blueprint, render_template, redirect, url_for , flash, request, current_app
from flask_login import  login_required , current_user, login_user
from datetime import datetime, timezone, timedelta
from models import db
from models import User, Product, Transaction, Messages, Review, Payment, Wallet
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

logging.basicConfig(level = logging.INFO, filename = "app.log")
transaction_bp = Blueprint('transaction', __name__, template_folder='templates', static_folder='static')

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


''' for test
#clear fake transaction
@transaction_bp.route("/clear_fake")
def clear_fake():
    Transaction.query.delete()
    User.query.delete()
    db.session.commit()
    return " All transactions cleared ! "

#use for test user login in transaction system !!!!!!!
@transaction_bp.route("/fake_login")
def fake_login():
    user1 = User.query.filter_by(email="test1@gmail.com").first()
    if not user1:
        user1 = User(name="test1",password="123",email="test1@gmail.com")
        db.session.add(user1)

    user2 = User.query.filter_by(email="test2@gmail.com").first()
    if not user2:
        user2 = User(name="test2",password="123",email="test2@gmail.com")
        db.session.add(user2)
    
    db.session.commit()
    login_user(user1)
    return f" Fake users created. You are now logged in as {user1.name} "

#use for test transaction history
@transaction_bp.route("/fake_transactions")
def fake_transaction():
    buyer_id = current_user.id
    seller_id = current_user.id
    fake_data = [
        Transaction(product_id="0619",buyer_id=buyer_id,seller_id=seller_id,status="pending", quantity=1),
        Transaction(product_id="201",buyer_id=buyer_id,seller_id=seller_id,status="completed", quantity=1),
        Transaction(product_id="333",buyer_id=buyer_id,seller_id=seller_id,status="cancelled", quantity=1),
    ]
    db.session.add_all(fake_data)
    db.session.commit()
    return "Fake transactions inserted"

#use for test view requests
@transaction_bp.route("/fake_purchase")
def fake_purchase():
    buyer_id = 999
    seller_id = current_user.id
    fake_requests = [
        Transaction(product_id="111",buyer_id=buyer_id,seller_id=seller_id,status="pending", quantity=1),
        Transaction(product_id="222",buyer_id=buyer_id,seller_id=seller_id,status="pending", quantity=1),
        Transaction(product_id="1018",buyer_id=buyer_id,seller_id=seller_id,status="pending", quantity=1),
    ]
    db.session.add_all(fake_requests)
    db.session.commit()
    return "Fake purchase requests inserted"

'''

#auto confirm transactions
from datetime import datetime, timedelta
from models import db, Transaction, Messages

def auto_confirm_transactions():
    now = datetime.now()
    deadline = now - timedelta(days=5)

    expired_tx = Transaction.query.filter(
        Transaction.status == "shipped",
        Transaction.shipped_at <= deadline
    ).all()

    for tx in expired_tx:
        tx.status = "completed"

        msg = Messages(
            sender_id=tx.seller_id,
            receiver_id=tx.buyer_id,
            transaction_id=tx.id,
            message_type="system",
            content="[System] Transaction auto-confirmed after 5 days."
        )
        db.session.add(msg)

    if expired_tx:
        db.session.commit()
        print(f"[AutoConfirm] {len(expired_tx)} transactions confirmed.")


#buyer action

#buyer click product, initiate purchase request   all return to transaction home
@transaction_bp.route("/buy/<int:product_id>", methods = ["POST"])
@login_required
def buy_product(product_id):
    product = Product.query.get_or_404(product_id)

    #check if product is available
    if product.is_sold == True:
        flash("Product is not available for purchase.","warning")
        return redirect (url_for("index"))
    
    #prevent duplicate purchase requests
    existing = Transaction.query.filter_by( buyer_id = current_user.id,
                                           product_id = product_id,
                                           status = "pending").first() 
    if existing:
        flash("You have already requested to purchase this product.","info")
        return redirect(url_for("index"))

    #prevent seller buy own product
    if product.seller_id == current_user.id:
        flash("You cannot buy your own product.","warning")
        return redirect(url_for("index"))

    #save in database
    try:
        product = Product.query.get(product_id)
        product.is_sold = True
        new_transaction = Transaction (buyer_id = current_user.id,
                                   product_id = product_id,
                                   seller_id =product.seller_id,
                                   status = "pending",
                                   price = product.price)
        db.session.add(new_transaction)
        db.session.add(product)
        db.session.commit()
        flash("Purchase request send! Waiting for seller confirmation","success")
        return redirect(url_for("index"))
    
    except SQLAlchemyError as e: #e will save the wrong object
        db.session.rollback()
        logging.error( f"Transaction creation failed: buyer_id ={current_user.id},product_id = {product_id}. Error:{e}",
                      exc_info = True ) #save in app log thn we can know 
        flash("An error occurred while processing your request.","danger")


        return redirect(url_for("index"))


#complete transaction
@transaction_bp.route("/confirm/<int:transaction_id>", methods=["POST"])
@login_required
def confirm_receipt(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Check permission
    if transaction.buyer_id != current_user.id:
        flash("You are not authorized to confirm this transaction.", "danger")
        return redirect(url_for("transaction.my_transaction"))
    
    # Only confirm after the product is shipped
    if transaction.status != "shipped":
        flash("You can only confirm after the product is shipped.", "warning")
        return redirect(url_for("transaction.my_transaction"))
    
    try:
        # Find related payment record
        payment = Payment.query.filter_by(transaction_id=transaction_id).first()
        
        if payment and payment.escrow_status == "held":
            buyer_wallet = Wallet.query.filter_by(user_id=current_user.id).first()
            if not buyer_wallet:
                buyer_wallet = Wallet(user_id=current_user.id, balance=0.0, escrow_balance=0.0)
                db.session.add(buyer_wallet)
            
            seller_wallet = Wallet.query.filter_by(user_id=transaction.seller_id).first()
            if not seller_wallet:
                seller_wallet = Wallet(user_id=transaction.seller_id, balance=0.0, escrow_balance=0.0)
                db.session.add(seller_wallet)

            # Release funds from buyer
            buyer_wallet.escrow_balance -= payment.amount
            buyer_wallet.total_escrow_released += payment.amount
            
            # Release funds to seller
            seller_wallet.balance += payment.amount
            seller_wallet.total_escrow_received += payment.amount
            
            # Update payment status
            payment.escrow_status = "released"
            payment.date_released = datetime.now(timezone.utc)
            
            # Update transaction status
            transaction.status = "completed"
            transaction.created_at = datetime.now(timezone.utc)
        
        elif payment and payment.escrow_status == "released":
            # Funds already released, just complete the transaction
            transaction.status = "completed"
            transaction.created_at = datetime.now(timezone.utc)

        elif payment and payment.method == "cod":
            # COD no need to release fund, just complete
            transaction.status = "completed"
            transaction.created_at = datetime.now(timezone.utc)
            
        else:
            flash("No valid payment found for this transaction.", "error")
            return redirect(url_for("transaction.my_transaction"))
        
        # Send system message
        msg = Messages(
            sender_id=current_user.id,
            receiver_id=transaction.seller_id,
            transaction_id=transaction.id,
            message_type="system",
            content="[System] Buyer has confirmed receipt and payment has been released."
        )
        db.session.add(msg)
        db.session.commit()
        
        flash("Transaction completed successfully! Payment has been released to seller.", "success")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        flash("Error confirming transaction.", "danger")
        print(f"Error: {e}")
    
    return redirect(url_for("transaction.my_transaction"))
    

#buyer want to cancel transaction when pending state
@transaction_bp.route("/cancel/<int:transaction_id>",methods = ["POST"])
@login_required
def cancel_transaction(transaction_id): #user cannot delete transaction for others
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.buyer_id != current_user.id :
        flash("You cannot cancel this transaction.","warning")
        return redirect(url_for("transaction.my_transaction"))
    
    if transaction.status != "payment_pending": #only transaction in pending state can be cancelled
        flash("Only pending requests can be cancelled.","warning")
        return redirect(url_for("transaction.my_transaction"))
    
    try:
        transaction.status = "cancelled"
        db.session.commit()

        #send message to seller (auto)
        msg = Messages(
            sender_id=current_user.id,
            receiver_id=transaction.seller_id,
            transaction_id=transaction.id,
            message_type="system",
            content="[System] Buyer has cancel request."
            )
        db.session.add(msg)
        db.session.commit()
        

        flash("Transaction cancelled successsfully.","success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Error cancelling transaction.","danger")

    return redirect(url_for("transaction.my_transaction"))


#seller action

#check request
@transaction_bp.route("/view_requests")
@login_required
def view_requests():
    requests = Transaction.query.filter(
        Transaction.seller_id == current_user.id,
        Transaction.status == "pending"   ).all()
    return render_template("transaction/view_requests.html", requests = requests)


#seller accept order
@transaction_bp.route("/accept/<int:transaction_id>",methods = ["POST"])
@login_required
def accept_transaction(transaction_id):
    tx = Transaction.query.get_or_404(transaction_id)
    #product = Product.query.get_or_404(tx.product_id)

    #if product.seller_id != current_user.id:
        #flash("You do not have permission to perform this request.","danger")
        #return redirect(url_for("transaction.view_requests"))
    
    try:
        print(f"Before: {tx.status}")
        tx.status = "accepted"
        db.session.commit()
        print(f"After: {tx.status}")

        # send to buyer (auto)
        msg = Messages(
            sender_id=current_user.id,
            receiver_id=tx.buyer_id,
            transaction_id=tx.id,
            message_type="system",
            content="[System] Seller has accept your request."
        )
        db.session.add(msg)
        db.session.commit()
        flash("You have accepted the purchase request.","success")
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error( f"Transaction accept failed, tx_id{tx.id},buyer_id ={current_user.id}. Error:{e}",
                      exc_info = True )
        flash("Error accept the purchase request.","danger")

    return redirect(url_for("transaction.view_requests"))


#reject order
@transaction_bp.route("/reject/<int:transaction_id>",methods = ["POST"])
@login_required
def reject_request(transaction_id):
    tx = Transaction.query.get_or_404(transaction_id)
    #product = Product.query.get_or_404(tx.product_id)

    #if product.seller_id != current_user.id:
        #flash("You do not have permission to perform this request.","danger")
        #return redirect(url_for("transaction.view_requests"))
    
    try:
        tx.status = "rejected"
        tx.product.is_sold = False
        db.session.commit()
        
        db.session.commit()

        # send to buyer (auto)
        msg = Messages(
            sender_id=current_user.id,
            receiver_id=tx.buyer_id,
            transaction_id=tx.id,
            message_type="system",
            content="[System] Seller has rejected your request."
        )
        db.session.add(msg)
        db.session.commit()

        flash("You have rejected the purchase request.","success")
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error( f"Transaction reject failed, tx_id={tx.id}, buyer_id ={current_user.id}. Error:{e}",
                      exc_info = True )
        flash("Error reject the purchase request.","danger")

    return redirect(url_for("transaction.view_requests"))


# marks transaction as shipped (with proof)
@transaction_bp.route("/ship/<int:transaction_id>", methods=["POST"])
@login_required
def ship_transaction(transaction_id):
    tx = Transaction.query.get_or_404(transaction_id)

    # only seller can ship
    if tx.seller_id != current_user.id:
        flash("You do not have permission to ship this order.", "danger")
        return redirect(url_for("transaction.my_transaction"))

    if tx.status != "accepted":
        flash("Only accepted orders can be shipped.", "warning")
        return redirect(url_for("transaction.my_transaction"))

    # check file upload
    if "proof" not in request.files:
        flash("Please upload shipping proof.", "danger")
        return redirect(url_for("transaction.my_transaction"))

    file = request.files["proof"]
    if not (file and allowed_file(file.filename)):
        flash("Invalid file type. Please upload an image or PDF.", "danger")
        return redirect(url_for("transaction.my_transaction"))

    try:
        folder = os.path.join(current_app.static_folder, "uploads", "proofs")
        os.makedirs(folder, exist_ok=True)

        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"tx{tx.id}_{int(time.time())}.{ext}"

        filepath = os.path.join(folder, filename)
        file.save(filepath)

        tx.proof = f"uploads/proofs/{filename}"
        tx.status = "shipped"
        tx.shipped_at = datetime.now()
        db.session.commit()

        msg = Messages(
            sender_id=current_user.id,
            receiver_id=tx.buyer_id,
            transaction_id=tx.id,
            message_type="system",
            content="[System] Seller has marked the transaction as shipped with proof."
        )
        
        msg2 = Messages(
        sender_id=tx.buyer_id,
        receiver_id=tx.seller_id,
        transaction_id=tx.id,
        message_type="system",
        content="[System] Transaction was auto-confirmed after 5 days."
        )
    
        db.session.add(msg)
        db.session.add(msg2)
        db.session.commit()

        flash("Order marked as shipped with proof uploaded.", "success")

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Transaction ship failed, tx_id={tx.id}, error={e}", exc_info=True)
        flash("Error marking as shipped.", "danger")

    return redirect(url_for("transaction.my_transaction"))


#check transaction records  (buyer/seller) 
@transaction_bp.route("/my_transaction") 
@login_required
def my_transaction():#check all owner by current user transaction record
    bought_transactions = Transaction.query.filter_by(buyer_id = current_user.id).all()  

    sold_transactions = Transaction.query.filter_by(seller_id = current_user.id).all()

    user_reviews = Review.query.filter_by(username=current_user.name).all()

    return render_template("transaction/my_transactions.html", 
                           bought_transactions = bought_transactions,
                            sold_transactions = sold_transactions,
                            reviews = user_reviews )

#view transaction (in chat)
@transaction_bp.route("/view/<int:transaction_id>")
@login_required
def view_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)

    if transaction.buyer_id != current_user.id and transaction.seller_id != current_user.id:
        flash("You are not authorized to view this transaction.", "danger")
        return redirect(url_for("transaction.my_transaction"))

    return render_template("transaction/view_transaction.html", transaction=transaction, product=transaction.product)
