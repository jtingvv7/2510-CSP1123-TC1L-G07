import os
from flask import Blueprint, render_template, request, redirect, url_for
from models import db, Review

review_bp = Blueprint('review_rating', __name__, template_folder='templates')



# Main Page: Display all Review
@review_bp.route("/")
def index():
    reviews = Review.query.all()
    return render_template("index.html", reviews=reviews)


# Add Review
@review_bp.route("/add", methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        username = request.form.get('username')
        rating = int(request.form.get('rating'))
        comment = request.form.get('comment')

        if not username or not comment:
            return "Username and Comment cannot be emty!", 400

        new_review = Review(username=username, rating=rating, comment=comment)
        db.session.add(new_review)
        db.session.commit()

        return redirect(url_for('success'))
    return render_template("add.html")


@review_bp.route("/success")
def success():
    return render_template("success.html")


if __name__ == "__main__":
    review_bp.run(debug=True)
