from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Order
import random
import string

payment_bp = Blueprint('payment', __name__)

# Create Order Data
def get_mock_order():
    return{
        'order_id': 'SECONDLOOP_' + ''.join(random.choices(string.digits, k=6)),
        'amount': 99.90,
        'currency': 'MYR'
    }




# Main Page: Display Order ID and Payment Methods
@payment_bp.route("/payment")
def payment():
    order = get_mock_order()
    return render_template("index.html", order=order)


@payment_bp.route("/card", methods=['GET', 'POST'])
def card():
    order = get_mock_order()
    if request.method == 'POST':
        email = request.form.get('email')
        card_number = request.form.get('card_number')
        expiry = request.form.get('expiry')
        cvv = request.form.get('cvv')

        # Simulate Payment
        flash('Credit Card Payment Successful!', 'success')
        return redirect(url_for('payment.success'))
    return render_template("card.html", order=order)


@payment_bp.route("/grabpay", methods=['GET', 'POST'])
def grabpay():
    order = get_mock_order()
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Simulate Payment
        flash('GrabPay Payment Successful!', 'success')
        return redirect(url_for('payment.success'))
    return render_template("grabpay.html", order=order)


@payment_bp.route("/fpx", methods=['GET', 'POST'])
def fpx():
    order = get_mock_order()
    if request.method == 'POST':
        bank = request.form.get('bank')
        
        # Simulate Payment
        flash('FPX Payment Successful!', 'success')
        return redirect(url_for('payment.success'))
    return render_template("fpx.html", order=order)


@payment_bp.route("/success")
def success():
    order = get_mock_order()
    db.session.commit()
    return render_template("success.html", order=order)


@payment_bp.route("/cancel")
def cancel():
    flash('Payment Cancelled', 'info')
    return render_template("cancel.html")


if __name__ == "__main__":
    payment_bp.run(debug=True)