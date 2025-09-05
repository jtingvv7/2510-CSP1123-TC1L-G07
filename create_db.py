import os
from main import app
from models import db, User, Product, Transaction, Messages, Review, SafeLocation, Order

with app.app_context():
    # Create Database
    db.create_all()
    print("Database tables created")