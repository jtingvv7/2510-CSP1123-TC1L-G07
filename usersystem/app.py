import os
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
import stripe
from dotenv import load_dotenv

from main import app, db
from models import User

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


order_data = {
    "order_id": "SECONDLOOP_123456",
    "amount": 99.90,
    "currency": "myr"
}

#render first page(login)
@app.route("/")
def login():
    return render_template("login.html", order=order_data)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # handle form submission
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        # save user into db 
        from main import db
        from models import User
        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash("🎉 Registration successful! Welcome, " + name, "success")
        return redirect(url_for("profile"))  # go to profile after register

    # if GET, just show the form
    return render_template("register.html")


@app.route("/profile")
def profile():
    return render_template("profile.html", order=order_data)

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