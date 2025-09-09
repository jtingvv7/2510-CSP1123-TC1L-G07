from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db
from models import Order

payment_bp = Blueprint('payment', __name__, template_folder='templates')



# Main Page: Display Order ID and Payment Methods
@payment_bp.route("/")
def index():
    order = Order.query.first()
    if not order:
        #Create a sample order if none exists
        order = Order(order_id="SECONDLOOP1234", amount=99.90, currency="MYR")
        db.session.add(order)
        db.session.commit()
    return render_template("index.html", order=order)


@payment_bp.route("/card", methods=['GET', 'POST'])
def card():
    order = Order.query.first()
    if request.method == 'POST':
        email = request.form.get('email')
        card_number = request.form.get('card_number')
        expiry = request.form.get('expiry')
        cvv = request.form.get('cvv')

        db.session.commit()
        return redirect(url_for('payment.success'))
    return render_template("card.html", order=order)


@payment_bp.route("/grabpay", methods=['GET', 'POST'])
def grabpay():
    order = Order.query.first()
    if request.method == 'POST':
        email = request.form.get('email')
        
        db.session.commit()
        return redirect(url_for('payment.success'))
    return render_template("grabpay.html", order=order)


@payment_bp.route("/fpx", methods=['GET', 'POST'])
def fpx():
    order = Order.query.first()
    if request.method == 'POST':
        bank = request.form.get('bank')
        
        db.session.commit()
        return redirect(url_for('payment.success'))
    return render_template("fpx.html", order=order)


@payment_bp.route("/success")
def success():
    order = Order.query.first()
    db.session.commit()
    return render_template("success.html")


@payment_bp.route("/cancel")
def cancel():
    return render_template("cancel.html")
