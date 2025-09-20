import logging
from flask import Blueprint, render_template, redirect, url_for , flash
from flask_login import  login_required , current_user, login_user
from datetime import datetime, timezone
from models import db
from models import User, Product, Transaction, Messages
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level = logging.INFO, filename = "app.log")
transaction_bp = Blueprint('transaction', __name__, template_folder='templates', static_folder='static')


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
        Transaction(product_id="0619",buyer_id=buyer_id,seller_id=seller_id,status="pending"),
        Transaction(product_id="201",buyer_id=buyer_id,seller_id=seller_id,status="completed"),
        Transaction(product_id="333",buyer_id=buyer_id,seller_id=seller_id,status="cancelled"),
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
        Transaction(product_id="111",buyer_id=buyer_id,seller_id=seller_id,status="pending"),
        Transaction(product_id="222",buyer_id=buyer_id,seller_id=seller_id,status="pending"),
        Transaction(product_id="1018",buyer_id=buyer_id,seller_id=seller_id,status="pending"),
    ]
    db.session.add_all(fake_requests)
    db.session.commit()
    return "Fake purchase requests inserted"

'''

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
@transaction_bp.route("/confirm/<int:transaction_id>",methods = ["POST"])
@login_required
def confirm_receipt(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    #only buyer can complete transaction
    if transaction.buyer_id != current_user.id:
        flash("You are not authorized to confirm this transaction.","danger")
        return redirect(url_for("transaction.my_transactions"))
    
    #only can complete when shipped 
    if transaction.status != "shipped":
        flash ("You can only confirm after the product is shipped.","warning")
        return redirect(url_for("transaction.my_transactions"))
    
     #change status
    try:
        transaction.status = "completed"
        transaction.created_at = datetime.now(timezone.utc)
        db.session.commit()

        #send message to seller (auto)
        msg = Messages(
            sender_id=current_user.id,
            receiver_id=transaction.seller_id,
            transaction_id=transaction.id,
            message_type="system",
            content="[System] Buyer has confirmed receipt."
        )
        db.session.add(msg)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        flash("Error confirming transaction.","danger")
    return redirect(url_for("payment.index"))
    

#buyer want to cancel transaction when pending state
@transaction_bp.route("/cancel/<int:transaction_id>",methods = ["POST"])
@login_required
def cancel_transaction(transaction_id): #user cannot delete transaction for others
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.buyer_id != current_user.id :
        flash("You cannot cancel this transaction.","warning")
        return redirect(url_for("transaction.my_transaction"))
    
    if transaction.status != "pending": #only transaction in pending state can be cancelled
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


#marks transaction as shipped
@transaction_bp.route("/ship/<int:transaction_id>",methods = ["POST"])
@login_required
def ship_transaction(transaction_id):
    tx = Transaction.query.get_or_404(transaction_id)
    #only seller can ship
    if tx.seller_id != current_user.id:
        flash("You do not have permission to ship this order.","danger")
        return redirect(url_for("transaction.my_transaction"))
    
    if tx.status !="accepted":
        flash("Only accepted orders can be shipped.","warning")
        return redirect(url_for("transaction.my_transaction"))
    
    try:
        tx.status = "shipped"
        db.session.commit()

        # send message to buyer (auto)
        msg = Messages(
            sender_id=current_user.id,
            receiver_id=tx.buyer_id,
            transaction_id=tx.id,
            message_type="system",
            content="[System] Seller has marked the transaction as shipped."
        )
        db.session.add(msg)
        db.session.commit()
        flash("Order marked as shipped.","success")
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error( f"Transaction ship failed, tx_id={tx.id}, error={e}", exc_info = True )
        flash("Error marking as shipped.","danger")
    
    return redirect(url_for("transaction.my_transaction"))


#check transaction records  (buyer/seller) 
@transaction_bp.route("/my_transactions") 
@login_required
def my_transaction():#check all owner by current user transaction record
    bought_transactions = Transaction.query.filter_by(buyer_id = current_user.id).all()  

    sold_transactions = Transaction.query.filter_by(seller_id = current_user.id).all()

    return render_template("transaction/my_transactions.html", 
                           bought_transactions = bought_transactions,
                            sold_transactions = sold_transactions )

#view transaction (in chat)
@transaction_bp.route("/view/<int:transaction_id>")
@login_required
def view_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)

    if transaction.buyer_id != current_user.id and transaction.seller_id != current_user.id:
        flash("You are not authorized to view this transaction.", "danger")
        return redirect(url_for("transaction.my_transactions"))

    return render_template("transaction/view_transaction.html", transaction=transaction, product=transaction.product)
