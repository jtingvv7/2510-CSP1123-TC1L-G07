from main import db
from datetime import datetime, timezone

#user db
class User(db.Model):
    id = db.Column (db.Integer, primary_key = True) #primary key
    username = db.Column (db.String(30), nullable = False, unique = True) #nullable = cannot be empty, unique = cannot same with others
    email = db.Column (db.String(150), nullable = False, unique = True)
    password = db.Column (db.String(80), nullable = False)
#relationship of user
    transactions = db.relationship('Transaction', backref = 'buyer',lazy = True) #backref = can find user through transactions , lazy = lazy loading


#product db
class Product(db.Model):
    id = db.Column (db.Integer, primary_key = True) 
    name = db.Column(db.String(30), nullable = False, unique = True) #product name
    price = db.Column(db.Float, nullable = False)
    description = db.Column(db.Text, nullable = True) #can be empty
    date_posted = db.Column(db.datetime, default = lambda : datetime.now(timezone.utc))

#transaction db
class Transaction(db.Model):
    id = db.Column (db.Integer, primary_key = True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'),nullable = False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable = False)
    status = db.Column(db.String(50), default = "pending")
    created_at = db.Column(db.datetime, default = lambda : datetime.now(timezone.utc))

#messaging db
class Messages(db.Model):
    id = db.Column (db.Integer, primary_key = True)
