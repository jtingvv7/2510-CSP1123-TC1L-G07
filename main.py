import logging
import os
from flask import Flask, render_template, session
from extensions import db, login_manager
from models import User, Product, SafeLocation


def create_app():
    app = Flask(__name__, template_folder="templates")    

    # Database + Config
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///secondloop.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = "supersecretkey"  # session key

    # Logging setup
    logging.basicConfig(level=logging.INFO, filename="app.log")

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "transaction.fake_login"  # (joan test) where login_manager redirects

    # Import & register blueprints (AFTER app is created ✅)
    from transaction.routes import transaction_bp
    from payment.app import payment_bp
    from review_rating.app import review_bp
    from messages.routes import messages_bp
    from usersystem.app import usersystem_bp
    from admin.routes import admin_bp

    #register blueprint
    app.register_blueprint(transaction_bp, url_prefix="/transaction")
    app.register_blueprint(messages_bp, url_prefix="/messages")
    app.register_blueprint(payment_bp, url_prefix="/payment")
    app.register_blueprint(review_bp, url_prefix="/review")
    app.register_blueprint(usersystem_bp, url_prefix="/usersystem")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Home route
    @app.route("/")
    def index():
        # Fetch all products from DB
        products = Product.query.order_by(Product.id.desc()).all()  # latest first

        # Optional: fetch user locations if user logged in
        user_id = session.get("user_id")
        locations = SafeLocation.query.filter_by(user_id=user_id).all() if user_id else []

        return render_template("home_index.html", products=products, locations=locations)

    return app


# Flask-Login: user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)