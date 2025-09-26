from main import create_app
from extensions import db
from models import User

app = create_app()  # create the Flask app

with app.app_context():  #  application context
    system_user = User.query.filter_by(email="system@system.com").first()
    if not system_user:
        system_user = User(
            name="System",
            email="system@system.com",
            password="!",  # dummy password
            role="system",
            is_active=False
        )
        db.session.add(system_user)
        db.session.commit()
        print("System user created.")
    else:
        print("System user already exists.")
