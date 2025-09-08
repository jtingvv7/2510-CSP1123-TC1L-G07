import os
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, session
import stripe
from dotenv import load_dotenv
from sqlalchemy import func
from models import Transaction, Review
from main import app, db
from models import User, Transaction, Review 
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

#render first page(login)
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        #check database
        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            session["user_id"] = user.id  #save login session
            return  redirect(url_for('profile'))
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
    


@app.route("/profile")
def profile():
    if "user_id" not in session: 
        return redirect(url_for("login"))
    
    user = User.query.get_or_404(session["user_id"])

     # completed sales & purchases
    completed_sales = Transaction.query.filter_by(seller_id=user.id, status="completed").count()
    completed_purchases = Transaction.query.filter_by(buyer_id=user.id, status="completed").count()

    # average rating
    avg_rating = db.session.query(func.avg(Review.rating)).filter(Review.reviewed_id == user.id).scalar()

    return render_template(
        "profile.html",
        user=user,
        completed_sales=completed_sales,
        completed_purchases=completed_purchases,
        avg_rating=avg_rating
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


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/cancel")
def cancel():
    return render_template("cancel.html")

if __name__ == "__main__":
    app.run(debug=True)