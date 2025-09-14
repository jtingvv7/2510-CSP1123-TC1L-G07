import os
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, session
import stripe
from dotenv import load_dotenv
from sqlalchemy import func
from models import Transaction, Review
from main import app, db
from models import User, Transaction, Review, SafeLocation, Product
import re #phonenum


load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

#upload photo
order_data = {
    "order_id": "SECONDLOOP_123456",
    "amount": 99.90,
    "currency": "myr"
}

@app.route("/")
def home():
    # Show latest 6 products for homepage
    latest_products = Product.query.order_by(Product.date_posted.desc()).limit(6).all()
    return render_template("home.html", products=latest_products)

#render first page(login)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        #check database
        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            session["user_id"] = user.id  #save login session
            session["user_name"] = user.name
            session["user_profile_pic"] = user.profile_pic
            return  redirect(url_for('home'))
        else:
            flash("Invalid email or password, please try again!", "invalid")
            return redirect(url_for('login'))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # handle form submission
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        from main import db
        from models import User

        #limit for student
        if not email.endswith("@student.mmu.edu.my"):
            flash("Please register with your student email", "invalid")
            return redirect(url_for('register'))
        
        # --- Check if user already exists ---
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Account already exists. Please log in instead.", "invalid")
            return redirect(url_for("login"))
        
        # save user into db 
        from main import db
        from models import User
        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash(" Registration successful! Welcome, " + name, "success")
        return redirect(url_for("login"))  # redirect to login

    # if GET, just show the form
    return render_template("register.html")
    


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session: 
        return redirect(url_for("login"))
    
    user = User.query.get_or_404(session["user_id"])

    if request.method == "POST":
        if "profile_pic" in request.files:
            file = request.files["profile_pic"]
            if file and file.filename != "":
                filename = f"user_{user.id}.jpg"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                user.profile_pic = filename
                session["user_profile_pic"] = filename
                db.session.commit()
                flash("Profile picture updated!", "success")
        return redirect(url_for("profile"))

    # completed sales & purchases
    completed_sales = Transaction.query.filter_by(seller_id=user.id, status="completed").count()
    completed_purchases = Transaction.query.filter_by(buyer_id=user.id, status="completed").count()

    # average rating
    avg_rating = db.session.query(func.avg(Review.rating)).filter(Review.reviewed_id == user.id).scalar()

    # ✅ Only get the first pickup point (or None if not set)
    pickup_point = SafeLocation.query.filter_by(user_id=user.id).first()

    return render_template(
        "profile.html",
        user=user,
        completed_sales=completed_sales,
        completed_purchases=completed_purchases,
        avg_rating=avg_rating,
        pickup_point=pickup_point  
    )



@app.route("/editprofile", methods=["GET", "POST"])
def editprofile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get_or_404(session["user_id"])

    if request.method == "POST":
        # Update name
        name = request.form.get("name")
        if name:
            user.name = name

        # Update phone
        phone = request.form.get("phone")
        if phone:  # only digits from input
            full_phone = "+60" + phone.strip()  # build full phone number
            if re.fullmatch(r"\+60\d{9}", full_phone):
                user.phone = full_phone
            else:
                flash("Phone number must start with +60 and have exactly 9 digits.", "danger")
                return redirect(url_for("editprofile"))

        # Update profile photo
        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename != "":
                filename = f"user_{user.id}.jpg"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                user.profile_pic = filename

                # ⚡ Update session so it reflects immediately
                session["user_profile_pic"] = filename

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("editprofile.html", user=user)



@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    payment_method = request.json.get("payment_method", "card")
    
    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=[payment_method],
        line_items=[{
            "price_data": {
                "currency": "myr",
                "product_data": {"name": "Test Order"},
                "unit_amount": 5000, #50.00 
            },
            "quantity": 1,
        }],
        success_url=os.getenv("BASE_URL") + "/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=os.getenv("BASE_URL") + "/cancel",
        metadata={"order_id": "SECONDLOOP_123456"}
    )
    return jsonify({"id": session.id, "url": session.url})

@app.route("/map", methods=["GET", "POST"])
def map():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        address = request.form["address"]

        # ✅ check if user already has one pickup point
        pickup_point = SafeLocation.query.filter_by(user_id=session["user_id"]).first()

        if pickup_point:
            # update existing
            pickup_point.name = name
            pickup_point.address = address
        else:
            # create new
            new_point = SafeLocation(user_id=session["user_id"], name=name, address=address)
            db.session.add(new_point)

        db.session.commit()
        flash("Pickup point updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("map.html")

@app.route("/product")
def product():
    """
    Show all products to users.
    """
    all_products = Product.query.all()  # Fetch all products
    return render_template("product.html", products=all_products)


# Add or edit a product
@app.route("/product/manage", methods=["GET", "POST"])
@app.route("/product/manage/<int:product_id>", methods=["GET", "POST"])
def product_manage(product_id=None):
    """
    Add a new product or edit an existing product.
    - If product_id is provided, edit the product.
    - Otherwise, create a new product.
    """
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    locations = SafeLocation.query.filter_by(user_id=user.id).all()  # Pickup locations for dropdown
    product_item = Product.query.get(product_id) if product_id else None

    if request.method == "POST":
        # --- Form Input ---
        name = request.form.get("name")
        price_str = request.form.get("price")
        description = request.form.get("description")
        pickup_location_id = request.form.get("pickup_location")
        image_file = request.files.get("image")

        # --- Validation ---
        if not name or not price_str:
            flash("Product name and price are required!", "danger")
            return redirect(request.url)

        try:
            price = float(price_str)
        except ValueError:
            flash("Invalid price format!", "danger")
            return redirect(request.url)

        # Check duplicate name
        existing_product = Product.query.filter_by(name=name).first()
        if existing_product and (not product_item or existing_product.id != product_item.id):
            flash("Product name already exists!", "danger")
            return redirect(request.url)

        # Handle image upload
        filename = "default_product.jpg"
        if image_file and image_file.filename != "":
            filename = f"product_{user.id}_{image_file.filename}"
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        if product_item:
            # Edit existing product
            product_item.name = name
            product_item.price = price
            product_item.description = description
            product_item.pickup_location_id = int(pickup_location_id) if pickup_location_id else None
            product_item.image = filename
            flash("Product updated successfully!", "success")
        else:
            # Add new product
            new_product = Product(
                seller_id=user.id,
                name=name,
                price=price,
                description=description,
                pickup_location_id=int(pickup_location_id) if pickup_location_id else None,
                image=filename
            )
            db.session.add(new_product)
            flash("Product added successfully!", "success")

        db.session.commit()

        # ✅ Redirect to product listing after submission
        return redirect(url_for("product"))

    # GET request → show form
    return render_template("product_manage.html", product=product_item, locations=locations)

@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/cancel")
def cancel():
    return render_template("cancel.html")

if __name__ == "__main__":
    app.run(debug=True)