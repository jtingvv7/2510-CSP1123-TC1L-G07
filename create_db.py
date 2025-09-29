from main import create_app
from extensions import db
from models import User, Product, Transaction

app = create_app()

with app.app_context():
    db.create_all()
    print("Database tables created")