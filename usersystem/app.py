import os
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from main import db
from models import User, Transaction, Review, SafeLocation, Product

usersystem_bp = Blueprint(
    "usersystem",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/usersystem/static"
)


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ----------------- HOME -----------------
@usersystem_bp.route("/")
def home():
    return render_template("home_index.html")


# ----------------- LOGIN -----------------
@usersystem_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_profile_pic"] = user.profile_pic
            return redirect(url_for("usersystem.home"))
        else:
            flash("Invalid email or password, please try again!", "danger")
            return redirect(url_for("usersystem.login"))

    return render_template("login.html")


# ----------------- REGISTER -----------------
@usersystem_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        # 1️⃣ Validate email domain
        if not email.endswith("@student.mmu.edu.my"):
            flash("Only @student.mmu.edu.my emails are allowed to register!", "danger")
            return redirect(url_for("usersystem.register"))

        # 2️⃣ Check if email or username already exists
        if User.query.filter_by(email=email).first() or User.query.filter_by(name=name).first():
            flash("Email or username already exists!", "danger")
            return redirect(url_for("usersystem.register"))

        # 3️⃣ Create new user
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("usersystem.login"))

    return render_template("register.html")

# ----------------- FORGOT / RESET PASSWORD -----------------
@usersystem_bp.route("/forgot_reset_password", methods=["GET", "POST"])
def forgot_reset_password():
    step = request.args.get("step", "email")  # "email" or "reset"

    if request.method == "POST":
        if step == "email":
            # Step 1: Submit email
            email = request.form.get("email")
            user = User.query.filter_by(email=email).first()
            if not user:
                flash("Email not found. Please try again.", "danger")
                return redirect(url_for("usersystem.forgot_reset_password"))
            
            session["reset_user_id"] = user.id
            flash("Email verified. Please reset your password.", "info")
            return redirect(url_for("usersystem.forgot_reset_password", step="reset"))

        elif step == "reset":
            # Step 2: Reset password
            if "reset_user_id" not in session:
                flash("Unauthorized access.", "danger")
                return redirect(url_for("usersystem.login"))

            user = User.query.get(session["reset_user_id"])
            new_password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

            if new_password != confirm_password:
                flash("Passwords do not match.", "danger")
                return redirect(url_for("usersystem.forgot_reset_password", step="reset"))

            user.password = new_password
            db.session.commit()
            session.pop("reset_user_id", None)
            flash("Password reset successfully! Please login.", "success")
            return redirect(url_for("usersystem.login"))

    return render_template("forgot_reset_password.html", step=step)

# ----------------- PROFILE -----------------
@usersystem_bp.route("/profile", methods=["GET"])
def profile():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first!", "danger")
        return redirect(url_for("usersystem.login"))

    user = User.query.get(session.get("user_id"))
    if not user:   # <-- NEW: user not found in DB
        flash("User not found. Please login again.", "danger")
        session.clear()
        return redirect(url_for("usersystem.login"))

    completed_sales = Transaction.query.filter_by(seller_id=user_id, status="completed").all()
    completed_purchases = Transaction.query.filter_by(buyer_id=user_id, status="completed").all()
    avg_rating = db.session.query(db.func.avg(Review.rating)).filter_by(seller_id=user_id).scalar()
    pickup_points = SafeLocation.query.filter_by(user_id=user_id).all()

    return render_template(
        "profile.html",
        user=user,
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
        # ✅ Name
        name = request.form.get("name")
        user.name = name

        # ✅ Phone
        phone = request.form.get("phone")
        if phone and not re.match(r"^\d{9}$", phone):  
            flash("Phone number must be 9 digits!", "danger")
            return redirect(url_for("usersystem.editprofile"))
        user.phone = f"+60{phone}" if phone else None

        # ✅ Profile Picture
        file = request.files.get("file")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.root_path, "static", "uploads")
            os.makedirs(upload_path, exist_ok=True)
            filepath = os.path.join(upload_path, filename)
            file.save(filepath)
            user.profile_pic = filename
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
        flash("Pickup point saved successfully!", "success")
        return redirect(url_for("usersystem.profile"))

    return render_template("map.html")


# ----------------- PRODUCT LIST -----------------
@usersystem_bp.route("/product")
def product():
    products = Product.query.all()
    return render_template("product.html", products=products)


# ----------------- PRODUCT MANAGE -----------------
@usersystem_bp.route("/product/manage", methods=["GET", "POST"])
@usersystem_bp.route("/product/manage/<int:product_id>", methods=["GET", "POST"])
def product_manage(product_id=None):
    if "user_id" not in session:
        return redirect(url_for("usersystem.login"))

    product = Product.query.get(product_id) if product_id else None
    locations = SafeLocation.query.filter_by(user_id=session["user_id"]).all()

    if request.method == "POST":
        # handle delete
        if "delete" in request.form:
            if product and product.seller_id == session["user_id"]:
                db.session.delete(product)
                db.session.commit()
                flash("Product deleted successfully!", "success")
            return redirect(url_for("usersystem.product"))

        name = request.form.get("name")
        price = float(request.form.get("price"))
        description = request.form.get("description")
        pickup_location_id = request.form.get("pickup_location") or None

        if product_id:
            product.name = name
            product.price = price
            product.description = description
            product.pickup_location_id = pickup_location_id
        else:
            product = Product(
                name=name,
                price=price,
                description=description,
                seller_id=session["user_id"],
                pickup_location_id=pickup_location_id
            )
            db.session.add(product)

        db.session.commit()
        flash("Product saved successfully!", "success")
        return redirect(url_for("usersystem.product"))

    return render_template("product_manage.html", product=product, locations=locations)


# ----------------- SUCCESS -----------------
@usersystem_bp.route("/success")
def success():
    return render_template("success.html")