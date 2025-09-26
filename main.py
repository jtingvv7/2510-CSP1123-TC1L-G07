import os
import logging
from flask import Flask, render_template, session, url_for
from flask_login import current_user
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Extensions & Models
from extensions import db, login_manager
from models import User, Product, SafeLocation, Messages

# --- Logging Setup ---
if not os.path.exists("logs"):
    os.mkdir("logs")

logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
)
logging.info("Starting application...")

# --- Flask App Factory ---
def create_app():
    app = Flask(__name__, template_folder="templates")

    # Config
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///secondloop.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")

    # Error handling
    @app.errorhandler(Exception)
    def handle_exception(e):
        logging.error("Unhandled Exception", exc_info=True)
        return "Internal Server Error", 500

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # --- Blueprint Registration ---
    from transaction.routes import transaction_bp
    from payment.app import payment_bp
    from review_rating.app import review_bp
    from messages.routes import messages_bp
    from usersystem.app import usersystem_bp
    from admin.routes import admin_bp
    from ranking.app import ranking_bp
    from report.routes import report_bp

    app.register_blueprint(transaction_bp, url_prefix="/transaction")
    app.register_blueprint(messages_bp, url_prefix="/messages")
    app.register_blueprint(payment_bp, url_prefix="/payment")
    app.register_blueprint(review_bp, url_prefix="/review")
    app.register_blueprint(usersystem_bp, url_prefix="/usersystem")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(ranking_bp, url_prefix="/ranking")
    app.register_blueprint(report_bp, url_prefix="/report")

    # --- Context Processors & Filters ---
    @app.context_processor
    def utility_processor():
        def get_image_url(image_filename):
            if not image_filename:
                return url_for('static', filename='uploads/products/default_product.jpg')
            if image_filename.startswith("products/"):
                return url_for('static', filename='uploads/' + image_filename)
            return url_for('static', filename='uploads/products/' + image_filename)
        return dict(get_image_url=get_image_url)

    def format_history_date(value):
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

    @app.context_processor
    def inject_unread_count():
        if current_user.is_authenticated:
            unread_count = Messages.query.filter_by(
                receiver_id=current_user.id, is_read=False
            ).count()
            return dict(unread_count=unread_count)
        return dict(unread_count=0)

    # --- Routes ---
    @app.route("/")
    def index():
        try:
            products = (
                Product.query.options(joinedload(Product.seller))
                .filter_by(is_sold=False, is_active=True)
                .all()
            )
            user_id = session.get("user_id")
            locations = SafeLocation.query.filter_by(user_id=user_id).all() if user_id else []
            return render_template("home_index.html", products=products, locations=locations)
        except Exception as e:
            logging.error("Error in index route", exc_info=True)
            return "Internal Server Error", 500

    return app

# --- User Loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Auto Confirm Task ---
def auto_confirm_transactions(app):
    from models import Transaction, Messages
    from datetime import datetime, timedelta

    with app.app_context():
        try:
            deadline = datetime.now() - timedelta(days=5)
            expired_tx = Transaction.query.filter(
                Transaction.status == "shipped",
                Transaction.shipped_at <= deadline
            ).all()

            for tx in expired_tx:
                tx.status = "completed"
                msg = Messages(
                    sender_id=tx.seller_id,
                    receiver_id=tx.buyer_id,
                    transaction_id=tx.id,
                    message_type="system",
                    content="[System] Transaction auto-confirmed after 5 days."
                )
                db.session.add(msg)

            if expired_tx:
                db.session.commit()
                logging.info(f"[AutoConfirm] {len(expired_tx)} transactions updated.")
        except Exception as e:
            logging.error("Error in auto_confirm_transactions", exc_info=e)

# --- App Instance ---
app = create_app()

# --- APScheduler Setup ---
scheduler = BackgroundScheduler()
scheduler.add_job(func=lambda: auto_confirm_transactions(app), trigger="interval", hours=24)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())
logging.info("APScheduler started.")

# --- Run App ---
if __name__ == "__main__":
    logging.info("Running Flask app...")
    app.run(debug=True)
