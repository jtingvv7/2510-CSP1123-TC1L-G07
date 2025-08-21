from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from transaction.routes import transaction_bp


app = Flask(__name__)

# register blueprint
app.register_blueprint(transaction_bp, url_prefix="/transaction")


if __name__ == "_main_":
    app.run(debug=True)