import logging
from flask import Blueprint, render_template, redirect, url_for , flash, abort, request
from functools import wraps
from flask_login import  login_required , current_user, login_user, logout_user
from datetime import datetime, timezone
from models import db
from models import User, Product, Transaction, Messages
from sqlalchemy.exc import SQLAlchemyError 

admin_bp = Blueprint("admin", __name__, template_folder="templates", static_folder="static")

#ensure only admin can enter
def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = User.query.get(current_user.id)
        print("DEBUG: admin_required called,user=",current_user)
        if not user or user.role != "admin":
            abort(403)
        print("DEBUG: user is admin,continue")
        return func(*args, **kwargs)
    return wrapper

#dashboard html 
@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    user_count = User.query.count()
    product_count = Product.query.count()
    transaction_count = Transaction.query.count()
    return render_template("dashboard.html",
                           user_count = user_count,
                           product_count = product_count,
                           transaction_count = transaction_count)

#check all users
@admin_bp.route("/manage_users")
@login_required
@admin_required
def manage_users():
    all_users = User.query.all()
    return render_template("manage_users.html", users=all_users)

#check all products
@admin_bp.route("/manage_products")
@login_required
@admin_required
def manage_products():
    all_products = Product.query.all()
    return render_template("manage_products.html", products = all_products)

#check all transactions
@admin_bp.route("/manage_transactions")
@login_required
@admin_required
def manage_transactions():
    all_transactions = Transaction.query.all()
    return render_template("manage_transactions.html", transactions = all_transactions)


################## user management #####################

#make other user become admin
@admin_bp.route("/make_admin/<int:user_id>")
@login_required
@admin_required
def make_admin(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("User not found","danger")
        return redirect(url_for("manage_users"))
    user.role = "admin"
    db.session.commit()
    flash(f"{user.name} is now an admin", "success")
    return redirect(url_for("manage_users"))

#delete user
@admin_bp.route("/delete_user/<int:user_id>")
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("User not found","danger")
        return redirect(url_for("manage_users"))
    #prevent admin delete own acc
    if user.id == current_user.id:
        flash("You cannot delete your own account!","warning")
        return redirect(url_for("manage_users"))
    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.name} has been deleted!","success")
    return redirect(url_for("manage_users"))

################## product management #####################

#add product
@admin_bp.route("/product/add", methods=["GET","POST"])
@login_required
@admin_required
def add_product():
    '''
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        description = request.form["description"]

        new_product = Product(name=name, price=price, description=description)
        db.session.add(new_product)
        db.session.commit()

        flash("Product added successfully!","success")
        '''
    return redirect(url_for("usersystem.product_manage"))
    #return render_template("manage_products")

#edit product
@admin_bp.route("/products/edit/<int:product_id>", methods=["GET","POST"])
@login_required
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method =="POST":
        product.name = request.form["name"]
        product.price = request.form["price"]
        product.description = request.form["description"]
        db.session.commit()
        flash("Product update successfully!","success")
        return redirect(url_for("admin.manage_products",))
    return render_template("edit_product.html",product = product)

#delete product
@admin_bp.route("/products/delete/<int:product_id>", methods=["GET","POST"])
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted successfully!","success")
    return redirect(url_for("usersystem.manage_products"))

################## transactions management #####################

#delete transaction
@admin_bp.route("/delete_transactions/<int:transaction_id>", methods=["POST"])
@login_required
@admin_required
def delete_transaction(transaction_id):
    tx = Transaction.query.get_or_404(transaction_id)
    db.session.delete(tx)
    db.session.commit()
    flash("Transaction deleted successfully","success")
    return redirect(url_for("manage_trasactions"))


#update transacton status(when error)
@admin_bp.route("/update_transaction/<int:transaction_id>", methods=["POST"])
@login_required
@admin_required
def update_transaction(transaction_id):
    tx = Transaction.query.get_or_404(transaction_id)
    new_status = request.form.get("new_status")
    if new_status:
        tx.status = new_status
        db.session.commit()
        flash(f"Transaction status updated to {new_status}","success")
    else:
        flash("Invalid status", "danger")
    return redirect(url_for("manage_trasactions"))