import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# SQLite
DB_NAME = "app.db"
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Review Model
class Review(db.Model):
    __tablename__ = 'reviews'  # Create table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now()) 

# If database already exist，delete and create new one
if os.path.exists(DB_NAME):
    print("old database deleted，creating new one...")
    os.remove(DB_NAME)

with app.app_context():
    db.create_all()
    sample_review = Review(username="Alice", rating=5, comment="Great product!")
    db.session.add(sample_review)
    db.session.commit()





# Main Page: Display all Review
@app.route("/")
def index():
    reviews = Review.query.all()
    return render_template("index.html", reviews=reviews)


# Add Review
@app.route("/add", methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        username = request.form.get('name')
        rating = int(request.form.get('rating'))
        comment = request.form.get('comment')

        new_review = Review(username=username, rating=rating, comment=comment)
        db.session.add(new_review)
        db.session.commit()

        return redirect(url_for('success'))
    return render_template("add.html")


@app.route("/success")
def success():
    return render_template("success.html")


if __name__ == "__main__":
    app.run(debug=True)
