from flask import Blueprint, flash, render_template, request, redirect, url_for, session
from flask_login import current_user
from extensions import db
from models import Payment, Product, Transaction, Wallet
from transaction.routes import transaction_bp

payment_bp = Blueprint('payment', __name__, template_folder='templates')



# Main Page: Display Order ID and Payment Methods
@payment_bp.route("/")
def index():
    
    # Get current user's pending transactions
    current_user_id = session.get('user_id', 1)
    transactions = Transaction.query.filter_by(buyer_id=current_user_id, status="payment_pending").all()
    
    # Calculate total price from all pending transactions
    grand_total = sum(transaction.price for transaction in transactions) if transactions else 0
    
    return render_template("index.html", 
                         transactions=transactions, 
                         grand_total=grand_total)


    

@payment_bp.route("/secondlooppay", methods=['GET', 'POST'])
def secondlooppay():
    # Get current user's pending transactions
    current_user_id = session.get('user_id', 1)
    transactions = Transaction.query.filter_by(buyer_id=current_user_id, status="payment_pending").all()
    
    # Calculate total price from all pending transactions
    grand_total = sum(transaction.price for transaction in transactions) if transactions else 0

    # Get current user wallet
    wallet = Wallet.query.filter_by(user_id=current_user_id).first()

    if request.method == 'POST':
        # Check if wallet has enough balance
        if wallet.balance >= grand_total:
            # Minus balance from wallet
            wallet.balance -= grand_total
            wallet.escrow_balance += grand_total

            # Create payment record for each transaction
            for transaction in transactions:
                payment = Payment(
                    transaction_id=transaction.id,
                    payer_id=current_user_id, 
                    amount=transaction.price,
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

    return render_template("secondlooppay.html", transactions=transactions, grand_total=grand_total, wallet_balance=wallet.balance)

@payment_bp.route("/cod", methods=['GET', 'POST'])
def cod():
    current_user_id = session.get('user_id', 1)
    transactions = Transaction.query.filter_by(buyer_id=current_user_id, status="payment_pending").all()
    grand_total = sum(transaction.price for transaction in transactions) if transactions else 0
    
    if request.method == 'POST':
        if not transactions:
            flash("No pending transactions found!", "error")
            return redirect(url_for('payment.index'))
            
        # Create COD payment record for each transaction
        for transaction in transactions:
            payment = Payment(
                transaction_id=transaction.id,
                payer_id=current_user_id,
                amount=transaction.price,
                method="cod",
                status="pending",
                escrow_status="none"
            )
            db.session.add(payment)
            transaction.status = "pending"
        
        db.session.commit()

        session['cart'] = {}
        
        flash('Order placed successfully! You will pay when you receive the item.', 'success')
        return redirect(url_for('transaction.my_transaction'))
    
    return render_template("cod.html", transactions=transactions, grand_total=grand_total)


@payment_bp.route("/success")
def success():
    transactions = Transaction.query.filter_by(buyer_id=session.get('user_id', 1), status="payment_pending").all()

    if transactions:
        # Change transaction status to completed
        for transaction in transactions:
            transaction.status = "payment_pending"
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
                # Restore stock
                product.is_sold = False
                db.session.flush()
            
            db.session.delete(transaction)
        
        db.session.commit()
        session['cart'] = {}
        flash("Payment cancelled. All products are back on the market.", "info")

    return render_template("cancel.html")