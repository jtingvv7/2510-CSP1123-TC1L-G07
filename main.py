import logging
from flask import Flask, render_template
from extensions import db, login_manager
from models import User
import os


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app():
    app = Flask(__name__, template_folder="templates")    
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///secondloop.db"  #connect database
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = "supersecretkey" #need sessin manage

    logging.basicConfig(level = logging.INFO, filename = "app.log") #for creators can see errors

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "transaction.fake_login" #(joan test) tell flasklogin login page

    from transaction.routes import transaction_bp
    from messages.routes import messages_bp
    # register blueprint
    app.register_blueprint(transaction_bp, url_prefix="/transaction")
    app.register_blueprint(messages_bp, url_prefix="/messaging")
    
    @app.route("/")
    def index():
        return render_template ("home_index.html")
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

