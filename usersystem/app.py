import os
import time
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify, Flask
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from main import db
from datetime import datetime, timezone
from collections import defaultdict
from models import User, Transaction, Review, SafeLocation, Product, Wallet, Announcement
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


# ----------------- product manage-----------------

@usersystem_bp.route("/product_manage", methods=["GET", "POST"])
def product_manage():
    product_id = request.args.get("product_id")
    product = Product.query.get(product_id) if product_id else None

    if request.method == "POST":
        # Handle delete
        if "delete" in request.form:
            if product.transactions:  # has transactions
                product.is_active = False  # soft-delete
                db.session.commit()
                flash("Product cannot be deleted because it has transactions. It is now deactivated.", "warning")
            else:
                if product and product.image:
                    image_path = os.path.join(current_app.root_path, "static", "uploads", product.image)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                db.session.delete(product)
                db.session.commit()
            return redirect(url_for("usersystem.profile"))

        # Handle create/update
        name = request.form.get("name")
        description = request.form.get("description")
        price = float(request.form.get("price", 0))
        quantity = int(request.form.get("quantity", 1))
        pickup_location_id = request.form.get("pickup_location_id")

        # Handle file upload
        file = request.files.get("image")
        filename = None
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"product_{current_user.id}_{int(time.time())}.{ext}"
            upload_path = os.path.join(current_app.root_path, "static", "uploads", "products")
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))

        if product:  # Update existing
            product.name = name
            product.description = description
            product.price = price
            product.quantity = quantity
            product.pickup_location_id = pickup_location_id
            if filename:  # only update image if new one uploaded
                product.image = filename
            db.session.commit()
            flash("Product updated successfully!", "success")
        else:  # Create new
            new_product = Product(
                name=name,
                description=description,
                price=price,
                quantity=quantity,
                pickup_location_id=pickup_location_id,
                seller_id=current_user.id,
                image=filename,
                is_sold=False,
                is_active=True
            )
            db.session.add(new_product)
            db.session.commit()
            flash("Product added successfully!", "success")

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

            now = datetime.now(timezone.utc)
            latest_announcement = Announcement.query.filter(
                ((Announcement.user_id == None) | (Announcement.user_id == user.id)) &
                ((Announcement.expires_at == None) | (Announcement.expires_at > now))
                ).order_by(Announcement.id.desc()).first()

            if latest_announcement and (user.last_seen_announcement_id is None or latest_announcement.id > user.last_seen_announcement_id):
                flash(f"{latest_announcement.title}: {latest_announcement.content}", "info")
                user.last_seen_announcement_id = latest_announcement.id
                db.session.commit()

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
        #Each new user can get one wallet 
        new_wallet = Wallet(user_id=user.id, balance=0.0)
        db.session.add(new_wallet)
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
    history = session.get("history", [])

    user_id = session.get("user_id")
    if not user_id:
        flash("Please login first!", "danger")
        return redirect(url_for("usersystem.login"))

    user = User.query.get(user_id)
    if not user:
        flash("User not found. Please login again.", "danger")
        session.clear()
        return redirect(url_for("usersystem.login"))

    #  Handle pickup point actions (for products, not profile address)
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
                flash("You don't have permission to delete this location.", "danger")

        return redirect(url_for("usersystem.profile"))

    #  Fetch related user data
    products = Product.query.filter_by(seller_id=user.id).all()
    completed_sales = Transaction.query.filter_by(seller_id=user_id, status="completed").all()
    completed_purchases = Transaction.query.filter_by(buyer_id=user_id, status="completed").all()
    avg_rating = db.session.query(db.func.avg(Review.rating)).filter_by(seller_id=user_id).scalar()
    wallet = user.wallet.balance if user.wallet else 0.0

 # Extract product IDs safely (works with dicts and ints)
    history_ids = []
    for item in history:
        if isinstance(item, dict):  # new format with {"id":..., "date":...}
            history_ids.append(int(item["id"]))
        elif isinstance(item, (int, str)):  # fallback old format
            history_ids.append(int(item))

    # Query products (only if we have IDs)
    history_products = []
    if history_ids:
        history_products = Product.query.filter(Product.id.in_(history_ids)).all()

    return render_template(
        "profile.html",
        user=user,
        products=products,
        completed_sales=len(completed_sales),
        completed_purchases=len(completed_purchases),
        avg_rating=avg_rating,
        wallet=wallet,
        history_products=history_products 
    )

# ----------------- ADD TO HISTORY  -----------------

@usersystem_bp.route("/add_to_history/<int:product_id>", methods=["POST"])
def add_to_history(product_id):
    history = session.get("history", [])
    if product_id not in history:
        history.append(product_id)
        session["history"] = history
        session.modified = True   #  force save
    return jsonify({"status": "success", "history": session.get("history")})

# -----------------product detail -----------------

@usersystem_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)

    # history is always separate from Flask-Login's session["user_id"]
    history = session.get("history", [])

    if not isinstance(history, list):
        history = []

    # remove old record if product already exists
    history = [h for h in history if isinstance(h, dict) and h.get("id") != product_id]

    # add new record
    history.append({
        "id": product_id,
        "date": datetime.today().strftime("%Y-%m-%d")
    })

    session["history"] = history
    session.modified = True

    return render_template("product_detail.html", product=product)

# ----------------- ADD TO cart  -----------------

@usersystem_bp.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    cart = session.get("cart", {})
    product = Product.query.get_or_404(product_id)

    if product.is_sold:
        flash("This product is sold out!", "danger")
        return redirect(url_for("usersystem.cart"))

    if str(product.id) in cart:
        if cart[str(product.id)] < product.quantity:
            cart[str(product.id)] += 1
            flash("Increased quantity in cart.", "success")
        else:
            flash("No more stock available.", "warning")
    else:
        cart[str(product.id)] = 1
        flash("Product added to cart!", "success")

    session["cart"] = cart
    return redirect(url_for("usersystem.cart"))


# -----------------view HISTORY  -----------------

@usersystem_bp.route("/history")
def history():
    history = session.get("history", [])
    grouped = defaultdict(list)

    for h in history:
        if isinstance(h, dict):
            product = Product.query.get(h["id"])
            if product:
                grouped[h["date"]].append(product)

    return render_template("history.html", grouped=grouped)

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


 # ----------------- cart -----------------
@usersystem_bp.route("/cart", methods=["GET", "POST"])
def cart():
    # ----------------- LOAD CART -----------------
    cart = session.get("cart", {})
    # normalize keys to int for internal use
    cart = {int(pid): qty for pid, qty in cart.items()}

    if request.method == "POST":
        action = request.form.get("action")
        product_id = request.form.get("product_id")

        # ----------------- CHECKOUT -----------------
        if action == "checkout":
            if not cart:
                flash("Your cart is empty.", "warning")
                return redirect(url_for("usersystem.cart"))

            try:
                for pid, qty in cart.items():
                    product = Product.query.get(int(pid))
                    if not product or product.is_sold:
                        continue

                    # prevent over-checkout
                    if qty > product.quantity:
                        flash(f"Not enough stock for {product.name}.", "danger")
                        return redirect(url_for("usersystem.cart"))

                    new_transaction = Transaction(
                        product_id=product.id,
                        buyer_id=current_user.id,
                        seller_id=product.seller_id,
                        status="pending",
                        price=product.price * qty,
                    )
                    db.session.add(new_transaction)

                    # reduce stock
                    product.quantity -= qty
                    if product.quantity <= 0:
                        product.is_sold = True

                db.session.commit()
                session["cart"] = {}

                flash("Checkout successful!Your orders are now pending seller confirmation.", "success")
                return redirect(url_for("transaction.my_transaction"))

            except Exception as e:
                db.session.rollback()
                flash("Checkout failed.", "danger")
                print("Checkout error:", e)
                return redirect(url_for("usersystem.cart"))

        # ----------------- ADD -----------------
        if action == "add":
            if not product_id:
                flash("Invalid product.", "danger")
                return redirect(url_for("usersystem.cart"))

            product = Product.query.get(int(product_id))
            if not product:
                flash("Product not found.", "danger")
            elif product.is_sold:
                flash("This product is already sold.", "danger")
            elif str(product.id) in cart:
                flash("This product is already in your cart.", "warning")
            else:
                cart[str(product.id)] = 1   

        elif action == "increase":
            if product_id:
                pid = int(product_id)
                if pid in cart:
                    product = Product.query.get(pid)
                    if product and not product.is_sold and cart[pid] < product.quantity:
                        cart[pid] += 1
                    else:
                        flash("No more stock available.", "warning")

        elif action == "decrease":
            if product_id:
                pid = int(product_id)
                if pid in cart and cart[pid] > 1:
                    cart[pid] -= 1

        # ----------------- REMOVE -----------------
        elif action == "remove":
            if product_id and int(product_id) in cart:
                del cart[int(product_id)]

        # ----------------- CLEAR -----------------
        elif action == "clear":
            cart.clear()

        # ✅ Save back with string keys (JSON-safe)
        session["cart"] = {str(pid): qty for pid, qty in cart.items()}
        session.modified = True
        return redirect(url_for("usersystem.cart"))

    # ----------------- GET CART -----------------
    cart_items = []
    total_price = 0

    for pid, qty in cart.items():
        product = Product.query.get(int(pid))
        if product:
            cart_items.append({
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "qty": qty,
                "image": product.image,
                "is_sold": product.is_sold or product.quantity <= 0
            })
            if not (product.is_sold or product.quantity <= 0):
                total_price += product.price * qty

    return render_template(
        "cart.html",
        cart_items=cart_items,
        grand_total=total_price,
    )


# ----------------- search engine -----------------

@usersystem_bp.route("/search")
def search():
    query = request.args.get("q", "").strip()
    
    products = []
    if query:
        products = (
            Product.query
            .filter(
                Product.name.ilike(f"%{query}%"),
                Product.is_sold == False,    # Exclude sold
                Product.is_active == True    # Exclude inactive
            )
            .all()
        )

    return render_template("search.html", query=query, products=products)

# ----------------- view seller profile -----------------
@usersystem_bp.route("/profile/<int:user_id>")
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    return_product = request.args.get("return_product")  # NEW

    # Fetch products
    products = Product.query.filter_by(seller_id=user.id).all()
    completed_sales = Transaction.query.filter_by(seller_id=user.id, status="completed").all()
    avg_rating = db.session.query(db.func.avg(Review.rating)).filter_by(seller_id=user.id).scalar()
    wallet = user.wallet.balance if user.wallet else 0.0

    return render_template(
        "view_seller_profile.html",
        user=user,
        products=products,
        completed_sales=len(completed_sales),
        avg_rating=avg_rating,
        wallet=wallet,
        editable=False,
        return_product=return_product  # pass to template
    )


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