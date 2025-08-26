from flask import Blueprint, render_template, redirect, url_for , flash
from flask_login import  login_required , current_user
from datetime import datetime, timezone
from models import db, Product, Transaction
from sqlalchemy.exc import SQLAlchemyError


transaction_bp = Blueprint('transaction', __name__, template_folder='templates', static_folder='static')

#buyer action

#buyer click product, initiate purchase request
@transaction_bp.route("/buy/<int:product_id>", methods = ["POST"])
@login_required
def buy_product(product_id):
    product = Product.query.get_or_404(product_id)

    #check if product is available
    if not product.is_active or product.is_sold:
        flash("Product is not available for purchase.","warning")
        return redirect (url_for("transaction.home"))
    
    #prevent duplicate purchase requests
    existing = Transaction.query.filter_by( buyer_id = current_user.id,
                                           product_id = product_id,
                                           status = "pending").first() 
    if existing:
        flash("You have already requested to purchase this product","info")
        return redirect(url_for("transaction.home"))

    try:
        new_transaction = Transaction (buyer_id = current_user.id,
                                   product_id = product_id,
                                   status = Transaction.status_pending)  #use a constant 
        db.session.add(new_transaction)
        db.session.commit()
        flash("Purchase request send! Waiting for seller confirmation","success")
    except SQLAlchemyError: 
        db.session.rollback()
        flash("An error occurred while processing your request.","danger")


        return redirect(url_for("transaction.index"))

#check transaction record & check request     
@transaction_bp.route("/my_transactions") 
@login_required
def my_transaction():
    transactions = Transaction.query.filter_by(buyer_id = current_user.id).all  #check all owner by current user transaction record
    return render_template("transaction/my_transactions.html", transactions = transactions )

#buyer want to cancel transaction when pending state
@transaction_bp.route("cancel/ <int: trancaction_id >",methods = ["POST"])
@login_required
def cancel_transaction(transaction_id): #user cannot delete transaction for others
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.buyer_id != current_user.id :
        flash("You cannot cancel this transaction.","warning")
        return redirect(url_for("transaction.my_transactions"))
    
    if transaction.status != "pending": #only transaction in pending state can be cancelled
        flash("Only pending requests can be cancelled,","warning")
        return redirect(url_for("transaction.my_transactions"))
    
    try:
        transaction.status = "cancelled"
        db.session.commit()
        flash("Transaction cancelled successsfully.","success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Error cancelling transaction.","danger")

    return redirect(url_for("transaction.my_transactions"))




#transaction front page
@transaction_bp.route("/")
def index():
    return render_template("transaction/transaction.html")

