from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///secondloop.db"  #connect database
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)  

import models  # import models AFTER db is created

with app.app_context():
    db.create_all()  # make sure tables are created

from transaction.routes import transaction_bp
# register blueprint
app.register_blueprint(transaction_bp, url_prefix="/transaction")


if __name__ == "_main_":
    app.run(debug=True) 