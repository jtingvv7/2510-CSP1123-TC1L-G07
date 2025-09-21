import logging
import os
from flask import Flask, render_template, session, url_for
from extensions import db, login_manager
from models import User, Product, SafeLocation, Messages
from flask_login import current_user
from datetime import datetime, timedelta


def create_app():
    app = Flask(__name__, template_folder="templates")    

    # Database + Config
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///secondloop.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = "supersecretkey"  # session key

    #set upload folder
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")

    #register helper
    @app.context_processor
    def utility_processor():
        def get_image_url(image_filename):
        # if no image = default
            if not image_filename:
                return url_for('static', filename='uploads/products/default_product.jpg')

        # if have products/
            if image_filename.startswith("products/"):
                return url_for('static', filename='uploads/' + image_filename)

        # if filename only
            return url_for('static', filename='uploads/products/' + image_filename)

        return dict(get_image_url=get_image_url)

    # Logging setup
    logging.basicConfig(level=logging.INFO, filename="app.log")

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    # login_manager.login_view = "transaction.fake_login"  # (joan test) where login_manager redirects

    # Import & register blueprints (AFTER app is created ✅)
    from transaction.routes import transaction_bp
    from payment.app import payment_bp
    from review_rating.app import review_bp
    from messages.routes import messages_bp
    from usersystem.app import usersystem_bp
    from admin.routes import admin_bp
    from ranking.app import ranking_bp
    from report.routes import report_bp

    #register blueprint
    app.register_blueprint(transaction_bp, url_prefix="/transaction")
    app.register_blueprint(messages_bp, url_prefix="/messages")
    app.register_blueprint(payment_bp, url_prefix="/payment")
    app.register_blueprint(review_bp, url_prefix="/review")
    app.register_blueprint(usersystem_bp, url_prefix="/usersystem")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(ranking_bp, url_prefix="/ranking")
    app.register_blueprint(report_bp, url_prefix="/report")

        # --- Register custom filter ---
    def format_history_date(value):
        """Format YYYY-MM-DD into Today / Yesterday / 20 Sep 2025"""
        try:
            date_obj = datetime.strptime(value, "%Y-%m-%d").date()
            today = datetime.today().date()
            if date_obj == today:
                return "Today"
            elif date_obj == today - timedelta(days=1):
                return "Yesterday"
            else:
                return date_obj.strftime("%d %b %Y")
        except Exception:
            return value

    app.jinja_env.filters["history_date"] = format_history_date

    #for unread message
    @app.context_processor
    def inject_unread_count():
        if current_user.is_authenticated:
            unread_count = Messages.query.filter_by(
                        receiver_id = current_user.id,
                        is_read = False
                        ).count()
            return dict(unread_count = unread_count)
        return dict(unread_count = 0)


    # Home route
    @app.route("/")
    def index():
         # Only active and not sold products
        products = Product.query.filter_by(
            is_sold=False, 
            is_active=True
            ).all()
        #  products = [p for p in products if not p.sold_out]

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