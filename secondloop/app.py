import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

order_data = {
    "order_id": "SECONDLOOP_123456",
    "amount": 99.90,
    "currency": "myr"
}


@app.route("/")
def index():
    return render_template("index.html", order=order_data)


@app.route("/card", methods=['GET', 'POST'])
def card():
    if request.method == 'POST':
        return redirect(url_for('success'))
    return render_template("card.html")


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/cancel")
def cancel():
    return render_template("cancel.html")


if __name__ == "__main__":
    app.run(debug=True)