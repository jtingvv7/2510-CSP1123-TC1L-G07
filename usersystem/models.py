from main import db
from datetime import datetime, timezone

# User model
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    profile_pic = db.Column(db.String(200), default="profile.jpg")

    def __repr__(self):
        return f"<User {self.id} name: {self.name}>"

# Product model
class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(30), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_posted = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Product {self.id} {self.name}>"
      
class SafeLocation(db.Model):
    __tablename__ = 'safelocation'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Safe Location: {self.name}>"