from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Review
from werkzeug.utils import secure_filename
import uuid
import os

review_bp = Blueprint('review', __name__, template_folder='templates')

# Configuration for file upload
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Main Page: Display all Review
@review_bp.route("/")
def index():
    reviews = Review.query.order_by(Review.date_review.desc()).all()
    return render_template("review_index.html", reviews=reviews)


# Add Review
@review_bp.route("/add", methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        username = request.form.get('username')
        rating = int(request.form.get('rating'))
        comment = request.form.get('comment')

        if not username or not comment:
            flash("Username and Comment cannot be empty!", 400)
            return render_template("add.html")
        
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                # Generate unique filename
                filename = secure_filename(file.filename)
                file_extension = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{file_extension}"

                # Ensure upload directory exists
                upload_path = os.path.join(UPLOAD_FOLDER)
                os.makedirs(upload_path, exist_ok=True)

                # Save file
                file_path = os.path.join(upload_path, unique_filename)
                file.save(file_path)
                image_path = unique_filename

            elif file and file.filename:
                flash('Invalid file type. Please upload JPG, PNG, or Webp image only', 400)
                return render_template('add.html')
        
        new_review = Review(username=username, rating=rating, comment=comment, image_path=image_path)
        db.session.add(new_review)
        db.session.commit()

        flash('Review added successfully!', 'success')
        return redirect(url_for('review.success'))
    
    return render_template("add.html")


@review_bp.route("/success")
def success():
    return render_template("review_success.html")
