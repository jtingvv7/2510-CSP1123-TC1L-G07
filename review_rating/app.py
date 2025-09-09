from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db
from models import Review

review_bp = Blueprint('review', __name__, template_folder='templates')



# Main Page: Display all Review
@review_bp.route("/")
def index():
    reviews = Review.query.all()
    return render_template("review_index.html", reviews=reviews)


# Add Review
@review_bp.route("/add", methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        username = request.form.get('username')
        rating = int(request.form.get('rating'))
        comment = request.form.get('comment')

        if not username or not comment:
            return "Username and Comment cannot be empty!", 400

        new_review = Review(username=username, rating=rating, comment=comment)
        db.session.add(new_review)
        db.session.commit()

        return redirect(url_for('review.success'))
    return render_template("add.html")


@review_bp.route("/success")
def success():
    return render_template("success.html")

