from main import db
from datetime import datetime, timezone

# User model
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    profile_pic = db.Column(db.String(200), default="profile.jpg")
    join_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    phone = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<User {self.id} name: {self.name}>"

# Product model
class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(30), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_posted = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    image = db.Column(db.String(200), default="default_product.jpg")  # image filename
    pickup_location_id = db.Column(db.Integer, db.ForeignKey('safelocation.id'), nullable=True)  # optional location

    # Relationships
    pickup_location = db.relationship("SafeLocation", backref="products")
    seller = db.relationship("User", backref="products")

    def __repr__(self):
        return f"<Product {self.id} {self.name}>"
    
class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)

    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # who wrote the review
    reviewed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # who is being reviewed

    rating = db.Column(db.Integer, nullable=False)  # e.g., 1–5 stars
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())   

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
      
class SafeLocation(db.Model):
    __tablename__ = 'safelocation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # link to user
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Safe Location: {self.name} ({self.latitude}, {self.longitude})>"