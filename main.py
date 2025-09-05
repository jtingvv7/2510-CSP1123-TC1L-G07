import logging
from flask import Flask, render_template, redirect, url_for
from models import db

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///secondloop.db"  #connect database
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

logging.basicConfig(level = logging.INFO, filename = "app.log") #for creators can see errors

db.init_app(app)


from payment.payment import payment_bp
from review_rating.review import review_bp

# register blueprint

app.register_blueprint(payment_bp, url_prefix="/payment")
app.register_blueprint(review_bp, url_prefix="/review")
    

@app.route("/")
def home():
    return render_template ("home_index.html")


if __name__ == "__main__":
    app.run(debug=True)

