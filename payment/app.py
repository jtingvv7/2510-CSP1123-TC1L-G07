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
    
    # Calculate total price
    total_price = 0
    for pid, qty in cart.items():
        product = Product.query.get(int(pid))
        if product:
            total_price += product.price * qty
    
    grand_total = total_price
    
    # Create or get Transaction
    transaction = Transaction.query.first()
    if not transaction:
       # Use first product_id id there is cart items
        if cart:
            first_product_id = int(list(cart.keys())[0]) # Might be change it!!!
            transaction = Transaction(
                product_id=first_product_id,
                buyer_id=1,  # Assume current user id  is 1
                seller_id=1,  # Assume seller user id  is 1
                status="pending"
            )
            db.session.add(transaction)
            db.session.commit()
    
    return render_template("index.html", 
                         transaction=transaction, 
                         grand_total=grand_total)


@payment_bp.route("/card", methods=['GET', 'POST'])
def card():
    cart = session.get("cart", {})

    total_price = 0
    for pid, qty in cart.items():
        product = Product.query.get(int(pid))
        if product:
            total_price += product.price * qty
    
    grand_total = total_price

    transaction = Transaction.query.first()
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
    cart = session.get("cart", {})

    total_price = 0
    for pid, qty in cart.items():
        product = Product.query.get(int(pid))
        if product:
            total_price += product.price * qty
    
    grand_total = total_price

    transaction = Transaction.query.first()
    if request.method == 'POST':
        email = request.form.get('email')
        
        db.session.commit()

        # Clear shopping cart
        session['cart'] = {}

        return redirect(url_for('payment.success'))
    return render_template("grabpay.html", transaction=transaction, grand_total=grand_total)


@payment_bp.route("/fpx", methods=['GET', 'POST'])
def fpx():
    cart = session.get("cart", {})

    total_price = 0
    for pid, qty in cart.items():
        product = Product.query.get(int(pid))
        if product:
            total_price += product.price * qty
    
    grand_total = total_price

    transaction = Transaction.query.first()
    if request.method == 'POST':
        bank = request.form.get('bank')
        
        db.session.commit()

        # Clear shopping cart
        session['cart'] = {}

        return redirect(url_for('payment.success'))
    return render_template("fpx.html", transaction=transaction, grand_total=grand_total)
    

@payment_bp.route("/secondlooppay", methods=['GET', 'POST'])
def secondlooppay():
    cart = session.get("cart", {})

    total_price = 0
    for pid, qty in cart.items():
        product = Product.query.get(int(pid))
        if product:
            total_price += product.price * qty
    
    grand_total = total_price

    # Get current user wallet
    current_user_id = session.get('user_id', 1) # Assume current user ID
    wallet = Wallet.query.filter_by(user_id=current_user_id).first()

    if not wallet: # might be change it!!!
        wallet = Wallet(user_id=current_user_id, balance=100.0) # Give initial balance
        db.session.add(wallet)
        db.session.commit()

    transaction = Transaction.query.first()
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
    transaction = Transaction.query.first()
    db.session.commit()
    return render_template("success.html")


@payment_bp.route("/cancel")
def cancel():
    return render_template("cancel.html")
