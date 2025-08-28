import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

logging.basicConfig(level = logging.INFO, filename = "app.log") #for creators can see errors

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///secondloop.db"  #connect database
app.config["SQLALCHEMY_TRACH_MODIFICATIONS"] = False

db = SQLAlchemy(app)  

from transaction.routes import transaction_bp
# register blueprint
app.register_blueprint(transaction_bp, url_prefix="/transaction")


if __name__ == "__main__":
    app.run(debug=True)