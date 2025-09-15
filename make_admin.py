from models import db, User
from main import create_app   


app = create_app()
with app.app_context():
    name = "Joan"

    user = User.query.filter_by(name=name).first()
    if user:
        user.role = "admin"
        db.session.commit()
        print(f"✅ {user.name} has been set to admin")
    else:
        print("Can't find this user")