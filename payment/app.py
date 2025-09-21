from flask import Blueprint, flash, render_template, request, redirect, url_for, session
from flask_login import current_user
from extensions import db
from models import Payment, Product, Transaction, Wallet
from transaction.routes import transaction_bp

payment_bp = Blueprint('payment', __name__, template_folder='templates')



# Main Page: Display Order ID and Payment Methods
@payment_bp.route("/")
def index():
    # Get cart data
    cart = session.get("cart", {})
    
    # Get current user's pending transaction
    current_user_id = session.get('user_id', 1)
    transaction = Transaction.query.filter_by(buyer_id=current_user_id, status="payment_pending").first()
    
    # Use transaction price for grand_total
    grand_total = transaction.price if transaction else 0
    
    return render_template("index.html", 
                         transaction=transaction, 
                         grand_total=grand_total)


@payment_bp.route("/card", methods=['GET', 'POST'])
def card():
    # Get current user's pending transaction
    current_user_id = session.get('user_id', 1)
    transaction = Transaction.query.filter_by(buyer_id=current_user_id, status="payment_pending").first()
    
    # Use transaction price for grand_total
    grand_total = transaction.price if transaction else 0
    if request.method == 'POST':
        email = request.form.get('email')
        card_number = request.form.get('card_number')
        expiry = request.form.get('expiry')
        cvv = request.form.get('cvv')

        db.session.commit()

        # Clear shopping cart
        session['cart'] = {}

        return redirect(url_for('payment.success'))
    return render_template("card.html", transaction=transaction, grand_total=grand_total)


@payment_bp.route("/grabpay", methods=['GET', 'POST'])
def grabpay():
    # Get current user's pending transaction
    current_user_id = session.get('user_id', 1)
    transaction = Transaction.query.filter_by(buyer_id=current_user_id, status="payment_pending").first()
    
    # Use transaction price for grand_total
    grand_total = transaction.price if transaction else 0
    if request.method == 'POST':
        email = request.form.get('email')
        
        db.session.commit()

        # Clear shopping cart
        session['cart'] = {}

        return redirect(url_for('payment.success'))
    return render_template("grabpay.html", transaction=transaction, grand_total=grand_total)


@payment_bp.route("/fpx", methods=['GET', 'POST'])
def fpx():
    # Get current user's pending transaction
    current_user_id = session.get('user_id', 1)
    transaction = Transaction.query.filter_by(buyer_id=current_user_id, status="payment_pending").first()
    
    # Use transaction price for grand_total
    grand_total = transaction.price if transaction else 0
    if request.method == 'POST':
        bank = request.form.get('bank')
        
        db.session.commit()

        # Clear shopping cart
        session['cart'] = {}

        return redirect(url_for('payment.success'))
    return render_template("fpx.html", transaction=transaction, grand_total=grand_total)
    

@payment_bp.route("/secondlooppay", methods=['GET', 'POST'])
def secondlooppay():
    # Get current user's pending transaction
    current_user_id = session.get('user_id', 1)
    transaction = Transaction.query.filter_by(buyer_id=current_user_id, status="payment_pending").first()
    
    # Use transaction price for grand_total
    grand_total = transaction.price if transaction else 0

    # Get current user wallet
    current_user_id = session.get('user_id', 1) # Assume current user ID
    wallet = Wallet.query.filter_by(user_id=current_user_id).first()

    if not wallet: # might be change it!!!
        wallet = Wallet(user_id=current_user_id, balance=100.0) # Give initial balance
        db.session.add(wallet)
        db.session.commit()

    transaction = Transaction.query.filter_by(buyer_id=session.get('user_id', 1), status="payment_pending").first()
    if request.method == 'POST':
        # Check if wallet has enough balance
        if wallet.balance >= grand_total:
            # Minus balance from wallet
            wallet.balance -= grand_total
            db.session.commit()

            # Create payment record
            payment = Payment(
                transaction_id=transaction.id,
                payer_id=current_user_id, 
                amount=grand_total,
                method="wallet",
                status="success"
            )
            db.session.add(payment)
            db.session.commit()

            # Clear shopping cart
            session['cart'] = {}
            
            return redirect(url_for('payment.success'))
        else:
            flash('Balance is not enough!', 'error')

    return render_template("secondlooppay.html", transaction=transaction, grand_total=grand_total, wallet_balance=wallet.balance)


@payment_bp.route("/success")
def success():
    transaction = Transaction.query.filter_by(buyer_id=session.get('user_id', 1), status="payment_pending").first()

    if transaction:
        # Change transaction status to completed
        transaction.status = "completed"
        db.session.commit()

    return render_template("success.html")


@payment_bp.route("/cancel")
def cancel():
    transaction = Transaction.query.filter_by(buyer_id=session.get('user_id', 1), status="payment_pending").first()

    if transaction:
        # Change transaction status to shipped
        transaction.status = "shipped"
        db.session.commit()

    return render_template("cancel.html")
