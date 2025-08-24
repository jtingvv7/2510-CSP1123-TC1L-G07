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

