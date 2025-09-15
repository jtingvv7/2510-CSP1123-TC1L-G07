from main import create_app
from models import db, User

app = create_app()
with app.app_context():
    users = User.query.all()
    for u in users:
        print(u.id, u.name, u.role)