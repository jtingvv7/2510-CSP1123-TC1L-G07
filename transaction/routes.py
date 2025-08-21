from flask import Blueprint, render_template

transaction_bp = Blueprint('transaction', __name__, template_folder='templates', static_folder='static')

@transaction_bp.route("/")
def index():
    return render_template("transaction/transaction.html")