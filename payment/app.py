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
            wallet.escrow_balance += grand_total

            # Create payment record
            payment = Payment(
                transaction_id=transaction.id,
                payer_id=current_user_id, 
                amount=grand_total,
                method="wallet",
                status="held",
                escrow_status="held"
            )
            db.session.add(payment)

            transaction.status = "pending"
            db.session.commit()

            # Clear shopping cart
            session['cart'] = {}
            
            return redirect(url_for('payment.success'))
        else:
            flash('Balance is not enough!', 'error')

    return render_template("secondlooppay.html", transaction=transaction, grand_total=grand_total, wallet_balance=wallet.balance)

@payment_bp.route("/cod", methods=['GET', 'POST'])
def cod():
    current_user_id = session.get('user_id', 1)
    transaction = Transaction.query.filter_by(buyer_id=current_user_id, status="payment_pending").first()
    grand_total = transaction.price if transaction else 0
    
    if request.method == 'POST':
        if not transaction:
            flash("No pending transaction found!", "error")
            return redirect(url_for('payment.index'))
            
        # Create COD payment record
        payment = Payment(
            transaction_id=transaction.id,
            payer_id=current_user_id,
            amount=grand_total,
            method="cod",
            status="pending",
            escrow_status="none"
        )
        db.session.add(payment)
        
        # Update transaction status
        transaction.status = "pending"
        db.session.commit()

        session['cart'] = {}
        
        flash('Order placed successfully! You will pay when you receive the item.', 'success')
        return redirect(url_for('transaction.my_transactions'))
    
    return render_template("cod.html", transaction=transaction, grand_total=grand_total)


@payment_bp.route("/success")
def success():
    transaction = Transaction.query.filter_by(buyer_id=session.get('user_id', 1), status="payment_pending").first()

    if transaction:
        # Change transaction status to completed
        transaction.status = "pending"
        db.session.commit()

    return render_template("success.html")


@payment_bp.route("/cancel")
def cancel():
    transactions = Transaction.query.filter_by(
        buyer_id=session.get('user_id', 1), 
        status="payment_pending"
    ).all()

    if transactions:
        for transaction in transactions:
            product = Product.query.get(transaction.product_id)
            if product:
                # 使用transaction.quantity恢复库存
                product.quantity += transaction.quantity
                product.is_sold = False
            
            db.session.delete(transaction)
        
        db.session.commit()
        session['cart'] = {}
        flash("Payment cancelled. All products are back on the market.", "info")

    return render_template("cancel.html")