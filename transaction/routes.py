from flask import Blueprint, render_template, redirect, url_for , flash
from flask_login import  login_required , current_user
from datetime import datetime, timezone
from models import db, Product, Transaction


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
    existing = Transaction.query.filter_by( buyer_id = current_user,
                                           product_id = product_id,
                                           status = "pending").first()
    if existing:
        flash("You have already requested to purchase this product","info")
        return redirect(url_for("transaction.home"))

    new_transaction = Transaction (buyer_id = current_user.id,
                                   product_id = product_id,
                                   status = "pending")
    db.session.add(new_transaction)
    db.session.commit()

    flash("Purchase request send! Waiting for seller confirmation","success")
    return redirect(url_for("transaction.index"))

#transaction front page
@transaction_bp.route("/")
def index():
    return render_template("transaction/transaction.html")

