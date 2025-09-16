import os
import time
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
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



# ----------------- PRODUCT MANAGEMENT -----------------
@usersystem_bp.route("/product_manage", methods=["GET", "POST"])
@usersystem_bp.route("/product_manage/<int:product_id>", methods=["GET", "POST"])
def product_manage(product_id=None):
    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first!", "danger")
        return redirect(url_for("usersystem.login"))

    product = Product.query.get(product_id) if product_id else None
    locations = SafeLocation.query.filter_by(user_id=user_id).all()

    if request.method == "POST":
        # DELETE product
        if "delete" in request.form and product:
            if product.seller_id == user_id:
                db.session.delete(product)
                db.session.commit()
                flash("Product deleted successfully!", "success")
            else:
                flash("Cannot delete this product.", "danger")
            return redirect(url_for("usersystem.profile"))

        # Collect form data
        name = request.form.get("name")
        description = request.form.get("description")
        price = float(request.form.get("price", 0))
        pickup_location_id = request.form.get("pickup_location") or None

        # Handle image upload
        file = request.files.get("image")
        filename = None
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit(".",1)[-1] #extension name
            filename = f"product_{int(time.time())}.{ext}" #product_time.jpg
            upload_path = os.path.join(current_app.root_path, "static", "uploads","products")
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))

        if product:
            # EDIT existing product
            if product.seller_id != user_id:
                flash("You don’t have permission to edit this product.", "danger")
                return redirect(url_for("usersystem.profile"))

            product.name = name
            product.description = description
            product.price = price
            product.pickup_location_id = pickup_location_id
            if filename:  # only overwrite image if new file uploaded
                product.image = filename
        else:
            # ADD new product
            product = Product(
                name=name,
                description=description,
                price=price,
                seller_id=user_id,
                pickup_location_id=pickup_location_id,
                image=filename if filename else "default_product.jpg"
            )
            db.session.add(product)

        db.session.commit()
        flash("Product saved successfully!", "success")
        return redirect(url_for("usersystem.profile"))

    return render_template("product_manage.html", product=product, locations=locations)
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
        flash("Account created successfully! Please login.", "success")
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
@usersystem_bp.route("/profile", methods=["GET"])
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

    # Get products of this user
    products = Product.query.filter_by(seller_id=user.id).all()

    completed_sales = Transaction.query.filter_by(seller_id=user_id, status="completed").all()
    completed_purchases = Transaction.query.filter_by(buyer_id=user_id, status="completed").all()
    avg_rating = db.session.query(db.func.avg(Review.rating)).filter_by(seller_id=user_id).scalar()
    pickup_points = SafeLocation.query.filter_by(user_id=user_id).all()

    return render_template(
        "profile.html",
        user=user,
        products=products,
        completed_sales=len(completed_sales),
        completed_purchases=len(completed_purchases),
        avg_rating=avg_rating,
        pickup_points=pickup_points
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
        flash("Profile updated successfully!", "success")
        return redirect(url_for("usersystem.profile"))

    return render_template("editprofile.html", user=user)

# ----------------- MAP -----------------
@usersystem_bp.route("/map", methods=["GET", "POST"])
def map():
    if not session.get("user_id"):
        flash("Please login first!", "danger")
        return redirect(url_for("usersystem.login"))

    user_id = session["user_id"]

    if request.method == "POST":
        name = request.form.get("name")
        address = request.form.get("address")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        description = request.form.get("description")

        if not all([name, address, latitude, longitude]):
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("usersystem.map"))

        existing_location = SafeLocation.query.filter_by(user_id=user_id).first()
        if existing_location:
            existing_location.name = name
            existing_location.address = address
            existing_location.latitude = latitude
            existing_location.longitude = longitude
            existing_location.description = description
        else:
            new_location = SafeLocation(
                user_id=user_id,
                name=name,
                address=address,
                latitude=latitude,
                longitude=longitude,
                description=description
            )
            db.session.add(new_location)

        db.session.commit()
        return redirect(url_for("usersystem.profile"))

    return render_template("map.html")



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