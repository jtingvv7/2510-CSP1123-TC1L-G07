from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), unique=True, nullable =False)
    amount = db.Column(db.Float, nullable =False)
    currency = db.Column(db.String(10), default= "MYR")


with app.app_context():
    db.create_all()
    if not Order.query.first():
        sample_order = Order(order_id="ORD12345", amount=99.90, currency="MYR")
        db.session.add(sample_order)
        db.session.commit()
    




@app.route("/")
def index():
    order = Order.query.first()
    return render_template("index.html", order=order)


@app.route("/card", methods=['GET', 'POST'])
def card():
    order = Order.query.first()
    if request.method == 'POST':
        email = request.form.get('email')
        card_number = request.form.get('card_number')
        expiry = request.form.get('expiry')
        cvv = request.form.get('cvv')

        db.session.commit()
        return redirect(url_for('success'))
    return render_template("card.html", order=order)


@app.route("/grabpay", methods=['GET', 'POST'])
def grabpay():
    order = Order.query.first()
    if request.method == 'POST':
        email = request.form.get('email')
        
        db.session.commit()
        return redirect(url_for('success'))
    return render_template("grabpay.html", order=order)


@app.route("/fpx", methods=['GET', 'POST'])
def fpx():
    order = Order.query.first()
    if request.method == 'POST':
        bank = request.form.get('bank')
        
        db.session.commit()
        return redirect(url_for('success'))
    return render_template("fpx.html", order=order)


@app.route("/success")
def success():
    order = Order.query.first()
    db.session.commit()
    return render_template("success.html")


@app.route("/cancel")
def cancel():
    return render_template("cancel.html")


if __name__ == "__main__":
    app.run(debug=True)