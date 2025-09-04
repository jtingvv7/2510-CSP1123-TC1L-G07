import logging
from flask import Flask, render_template
from extensions import db  


def create_app():
    app = Flask(__name__)    
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///secondloop.db"  #connect database
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    logging.basicConfig(level = logging.INFO, filename = "app.log") #for creators can see errors

    db.init_app(app)

    from transaction.routes import transaction_bp
    # register blueprint
    app.register_blueprint(transaction_bp, url_prefix="/transaction")
    
    @app.route("/")
    def index():
        return render_template ("home_index.html")
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

