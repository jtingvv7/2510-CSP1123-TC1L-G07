import os
from create_db import db, create_app
#cuz new to use database to test

DB_PATH = os.path.join("instance", "secondloop.db")

if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
        print(f"done for delete current database: {DB_PATH}")
    except Exception as e:
        print(f"failed for delete database: {e}")
else:
    print("not found current database")

# create new database
app = create_app()
with app.app_context():
    db.create_all()
    print("new database")