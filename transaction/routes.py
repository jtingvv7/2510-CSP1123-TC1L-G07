from flask import Blueprint, render_template, redirect, url_for , flash
from flask_login import  login_required , current_user
from datetime import datetime, timezone
from models import db, Product, Transaction
from sqlalchemy.exc import SQLAlchemyError


transaction_bp = Blueprint('transaction', __name__, template_folder='templates', static_folder='static')

#buyer action

#buyer click product, initiate purchase request   all return to transaction home
@transaction_bp.route("/buy/<int:product_id>", methods = ["POST"])
@login_required
def buy_product(product_id):
    product = Product.query.get_or_404(product_id)

    #check if product is available
    if not product.is_sold == False:
        flash("Product is not available for purchase.","warning")
        return redirect (url_for("transaction.home"))
    
    #prevent duplicate purchase requests
    existing = Transaction.query.filter_by( buyer_id = current_user.id,
                                           product_id = product_id,
                                           status = "pending").first() 
    if existing:
        flash("You have already requested to purchase this product.","info")
        return redirect(url_for("transaction.home"))

    #prevent seller buy own product
    if product.seller_id == current_user.id:
        flash("You cannot buy your own product.","warning")
        return redirect(url_for("transaction.home"))

    #save in database
    try:
        new_transaction = Transaction (buyer_id = current_user.id,
                                   product_id = product_id,
                                   status = Transaction.status_pending,
                                   created_at = db.Column(db.DateTime, default = lambda : datetime.now(timezone.utc)))  #use a constant 
        db.session.add(new_transaction)
        db.session.commit()
        flash("Purchase request send! Waiting for seller confirmation","success")
    except SQLAlchemyError: 
        db.session.rollback()
        flash("An error occurred while processing your request.","danger")


        return redirect(url_for("transaction.home"))


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
        return redirect(url_for("transaction/my_transactions"))
    
     #change status
    try:
        transaction.status = "completed"
        transaction.created_at = datetime.mow(timezone.utc)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Error confirming transaction.","danger")
    return redirect(url_for("transaction/my_transactions"))
    

#buyer want to cancel transaction when pending state
@transaction_bp.route("/cancel/<int:transaction_id >",methods = ["POST"])
@login_required
def cancel_transaction(transaction_id): #user cannot delete transaction for others
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.buyer_id != current_user.id :
        flash("You cannot cancel this transaction.","warning")
        return redirect(url_for("transaction/my_transactions"))
    
    if transaction.status != "pending": #only transaction in pending state can be cancelled
        flash("Only pending requests can be cancelled,","warning")
        return redirect(url_for("transaction/my_transactions"))
    
    try:
        transaction.status = "cancelled"
        db.session.commit()
        flash("Transaction cancelled successsfully.","success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Error cancelling transaction.","danger")

    return redirect(url_for("transaction/my_transactions"))


#seller action

#check request
@transaction_bp.route("/view_requests")
@login_required
def view_requests():
    requests = Transaction.query.join(Product).filter(
        Product.seller_id == current_user.id,
            Transaction.status =="pending"   ).all()
    return render_template("transaction/view_requests.html", requests = requests)

#seller accept order
@transaction_bp.route("/accept/<int:transaction_id>",methods = ["POST"])
@login_required
def accept_transaction(transaction_id):
    tx = Transaction.query.get_or_404(transaction_id)
    product = Product.query.get_or_404(tx.product_id)

    if product.seller_id != current_user.id:
        flash("You do not have permission to perform this request.","danger")
        return redirect(url_for("transaction/view_requests"))
    
    try:
        tx.status = "accepted"
        product.is_sold = True
        db.session.commit()
        flash("You have accepted the purchase request.","success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Error accept the purchase request.","danger")

    return redirect(url_for("transaction/view_requests"))


#reject order
@transaction_bp.route("/reject/<int:transaction_id>",methods = ["POST"])
@login_required
def reject_request(transaction_id):
    tx = Transaction.query.get_or_404(transaction_id)
    product = Product.query.get_or_404(tx.product_id)

    if product.seller_id != current_user.id:
        flash("You do not have permission to perform this request.","danger")
        return redirect(url_for("transaction/view_requests"))
    
    try:
        tx.status = "rejected"
        db.session.commit()
        flash("You have rejected the purchase request.","success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Error to reject the purchase request.","danger")

    return redirect(url_for("transaction/view_requests"))


#check transaction records  (buyer/seller) 
@transaction_bp.route("/my_transactions") 
@login_required
def my_transaction():#check all owner by current user transaction record
    bought_transactions = Transaction.query.filter_by(buyer_id = current_user.id).all()  

    sold_transactions = Transaction.query.filter_by(seller_id = current_user.id).all()

    return render_template("transaction/my_transactions.html", 
                           bought_transactions = bought_transactions,
                            sold_transactions = sold_transactions )


#transaction front page
@transaction_bp.route("/")
def home():
    return render_template("transaction_home.html")

