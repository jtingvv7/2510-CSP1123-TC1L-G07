import os
import time
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from main import db
from models import User, Transaction, Review, SafeLocation, Product
from flask_login import login_user, logout_user, current_user

usersystem_bp = Blueprint(
    "usersystem",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/usersystem/static"
)


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ----------------- peoduct manage-----------------

@usersystem_bp.route("/product_manage", methods=["GET", "POST"])
def product_manage():
    product_id = request.args.get("product_id")
    product = Product.query.get(product_id) if product_id else None

    if request.method == "POST":
        # Handle delete
        if "delete" in request.form:
            db.session.delete(product)
            db.session.commit()
            flash("Product deleted successfully.", "success")
            return redirect(url_for("usersystem.profile"))

        # Handle create or update
        name = request.form.get("name")
        description = request.form.get("description")
        price = request.form.get("price")
        pickup_location_id = request.form.get("pickup_location_id")

        # update existing
        if product:
            product.name = name
            product.description = description
            product.price = price
            product.pickup_location_id = pickup_location_id
        else:
            # create new
            new_product = Product(
                name=name,
                description=description,
                price=price,
                pickup_location_id=pickup_location_id,
                seller_id=current_user.id
            )
            db.session.add(new_product)

        db.session.commit()
        flash("Product saved successfully.", "success")

        # ✅ Redirect to profile instead of staying
        return redirect(url_for("usersystem.profile"))

    pickup_points = SafeLocation.query.filter_by(user_id=current_user.id).all()
    return render_template("product_manage.html", user=current_user, product=product, pickup_points=pickup_points)


# ----------------- LOGIN -----------------
@usersystem_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password_input = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Email not registered.", "error")
            return redirect(url_for('usersystem.register'))
        
        if check_password_hash(user.password, password_input):
            # Successful login
            login_user(user) #let flask-login remember user

            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_profile_pic"] = user.profile_pic
            return redirect(url_for("index"))
        else:
            flash("Invalid password.", "error")
            return redirect(url_for('usersystem.login'))

    return render_template('login.html')

# ----------------- REGISTER -----------------
@usersystem_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        # Validate email domain
        if not email.endswith("@student.mmu.edu.my"):
            flash("Only @student.mmu.edu.my emails are allowed to register!", "danger")
            return redirect(url_for("usersystem.register"))

        # Check if email or username already exists
        if User.query.filter_by(email=email).first() or User.query.filter_by(name=name).first():
            flash("Email or username already exists!", "danger")
            return redirect(url_for("usersystem.login"))
        
        # Hash password before storing
        hashed_password = generate_password_hash(password)

        # Create new user
        user = User(name=name, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("usersystem.login"))

    return render_template("register.html")

# ----------------- FORGOT / RESET PASSWORD -----------------
@usersystem_bp.route('/forgot_reset_password', methods=['GET', 'POST'])
def forgot_reset_password():
    email_verified = False  # to show/hide password fields

    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Email not registered. Please register first.", "error")
            return render_template('forgot_reset_password.html', email_verified=False)

        # Email exists → show password fields
        email_verified = True
        flash("Email verified! You can now reset your password.", "success")

        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Only update password if both password fields are filled
        if password and confirm_password:
            if password != confirm_password:
                flash("Passwords do not match.", "error")
            else:
                user.password = generate_password_hash(password)
                db.session.commit()
                flash("Password successfully reset!", "success")
                return redirect(url_for('usersystem.login'))

    return render_template('forgot_reset_password.html', email_verified=email_verified)
# ----------------- PROFILE -----------------
@usersystem_bp.route("/profile", methods=["GET", "POST"])
def profile():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first!", "danger")
        return redirect(url_for("usersystem.login"))

    user = User.query.get(user_id)
    if not user:
        flash("User not found. Please login again.", "danger")
        session.clear()
        return redirect(url_for("usersystem.login"))

    # ✅ Handle pickup point actions (for products, not profile address)
    if request.method == "POST":
        action = request.form.get("action")

        if action == "add_location":
            name = request.form.get("location_name")
            address = request.form.get("location_address")
            if not name or not address:
                flash("Both name and address are required.", "danger")
            else:
                new_location = SafeLocation(user_id=user_id, name=name, address=address)
                db.session.add(new_location)
                db.session.commit()
                flash("Pickup location added!", "success")

        elif action == "delete_location":
            location_id = request.form.get("location_id")
            location = SafeLocation.query.get(location_id)
            if location and location.user_id == user_id:
                db.session.delete(location)
                db.session.commit()
                flash("Pickup location deleted!", "success")
            else:
                flash("You don’t have permission to delete this location.", "danger")

        return redirect(url_for("usersystem.profile"))

    # ✅ Fetch related user data
    products = Product.query.filter_by(seller_id=user.id).all()
    completed_sales = Transaction.query.filter_by(seller_id=user_id, status="completed").all()
    completed_purchases = Transaction.query.filter_by(buyer_id=user_id, status="completed").all()
    avg_rating = db.session.query(db.func.avg(Review.rating)).filter_by(seller_id=user_id).scalar()

    # ✅ Profile will now display user.profile_address (from edit_address_profile.html)
    return render_template(
        "profile.html",
        user=user,
        products=products,
        completed_sales=len(completed_sales),
        completed_purchases=len(completed_purchases),
        avg_rating=avg_rating
    )


# ----------------- EDIT PROFILE -----------------
@usersystem_bp.route("/editprofile", methods=["GET", "POST"])
def editprofile():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first!", "danger")
        return redirect(url_for("usersystem.login"))

    user = User.query.get(user_id)
    if not user:
        flash("User not found. Please login again.", "danger")
        session.clear()
        return redirect(url_for("usersystem.login"))

    if request.method == "POST":
        # Update name
        name = request.form.get("name")
        user.name = name

        # Update phone
        phone = request.form.get("phone")
        if phone and not re.match(r"^\d{9}$", phone):
            flash("Phone number must be 9 digits!", "danger")
            return redirect(url_for("usersystem.editprofile"))
        user.phone = f"+60{phone}" if phone else None

        # Update profile picture
        file = request.files.get("file")
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit(".",1)[-1]  #extension name
            filename = f"user{current_user.id}_{int(time.time())}.{ext}" #profile_time.png
            upload_path = os.path.join(current_app.root_path, "static", "uploads","profiles")
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))
            current_user.profile_pic = filename
            session["user_profile_pic"] = filename
            

        db.session.commit()
        return redirect(url_for("usersystem.profile"))

    return render_template("editprofile.html", user=user)


# ----------------- edit profile address -----------------

@usersystem_bp.route("/profile/edit_address", methods=["GET", "POST"])
def profile_address():
    user = current_user

    if request.method == "POST":
        profile_address = request.form.get("profile_address")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        if profile_address:
            user.profile_address = profile_address
            user.profile_latitude = float(latitude) if latitude else None
            user.profile_longitude = float(longitude) if longitude else None
            db.session.commit()
            return redirect(url_for("usersystem.profile"))

    return render_template("edit_address_profile.html", user=user)

# ----------------- edit pickup point -----------------

@usersystem_bp.route("/product_manage/add_pickup", methods=["GET", "POST"])
def pickup_point():
    user_id = current_user.id

    if request.method == "POST":
        name = request.form.get("name")
        address = request.form.get("address")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        description = request.form.get("description")

        if not all([name, address, latitude, longitude]):
            flash("Please fill all required fields!", "danger")
            return redirect(url_for("usersystem.pickup_point"))

        new_location = SafeLocation(
            user_id=user_id,
            name=name,
            address=address,
            latitude=float(latitude),
            longitude=float(longitude),
            description=description
        )
        db.session.add(new_location)
        db.session.commit()
        return redirect(url_for("usersystem.product_manage"))

    #  Pass current_user into template
    return render_template("map_pickup_point.html", user=current_user)


# ----------------- CART -----------------
@usersystem_bp.route("/cart", methods=["GET", "POST"])
def cart():
    cart = session.get("cart", {})

    if request.method == "POST":
        action = request.form.get("action")
        product_id = request.form.get("product_id")

        if not product_id:
            flash("Invalid product.", "danger")
            return redirect(url_for("usersystem.cart"))

        # ✅ Make sure product_id is int
        try:
            product_id = int(product_id)
        except ValueError:
            flash("Invalid product ID.", "danger")
            return redirect(url_for("usersystem.cart"))

        # ----------------- ADD / INCREASE -----------------
        if action in ["add", "increase"]:
            product = Product.query.get(product_id)
            if not product:
                flash("Product not found.", "danger")
            else:
                if hasattr(product, "quantity") and product.quantity is not None:
                    if product.quantity <= 0 or product.is_sold:
                        flash("Product is sold out.", "danger")
                    else:
                        qty_in_cart = cart.get(product_id, 0)
                        if qty_in_cart >= product.quantity:
                            flash("Cannot add more than available stock.", "warning")
                        else:
                            cart[product_id] = qty_in_cart + 1
                else:
                    # fallback: always allow adding
                    cart[product_id] = cart.get(product_id, 0) + 1

        # ----------------- DECREASE -----------------
        elif action == "decrease":
            if product_id in cart:
                if cart[product_id] > 1:
                    cart[product_id] -= 1
                else:
                    del cart[product_id]

        # ----------------- REMOVE -----------------
        elif action == "remove":
            if product_id in cart:
                del cart[product_id]

        # ----------------- CLEAR -----------------
        elif action == "clear":
            cart.clear()

        session["cart"] = cart
        return redirect(url_for("usersystem.cart"))

    # ----------------- GET CART -----------------
    cart_items = []
    total_price = 0
    for pid, qty in cart.items():
        product = Product.query.get(pid)
        if product:
            subtotal = product.price * qty
            cart_items.append({
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "quantity": qty,
                "subtotal": subtotal,
                "image": product.image
            })
            total_price += subtotal

    return render_template("cart.html", cart_items=cart_items, total_price=total_price)




# ----------------- SUCCESS -----------------
@usersystem_bp.route("/success")
def success():
    return render_template("success.html")

# ----------------- LOGOUT -----------------
@usersystem_bp.route("/logout")
def logout():
    logout_user() #clear current_user
    session.clear() 
    return redirect(url_for("index"))