from extensions import db
from datetime import datetime, timezone
from flask_login import UserMixin
from datetime import datetime, timezone

#user db
class User(db.Model,UserMixin):
    __tablename__ = 'user'
    id = db.Column (db.Integer, primary_key = True) #primary key
    name = db.Column (db.String(30), nullable = False, unique = True) #nullable = cannot be empty, unique = cannot same with others
    email = db.Column (db.String(150), nullable = False, unique = True)
    password = db.Column (db.String(80), nullable = False)
    profile_pic = db.Column(db.String(200), default="profile.jpg")
    join_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default="user")
    
#relationship of user
    #backref = can find user through transactions , lazy = lazy loading
    products = db.relationship("Product", back_populates="seller", lazy=True)
    wallet = db.relationship("Wallet", backref="wallet_owner", uselist=False, lazy=True)
    payment = db.relationship("Payment", backref="payment_user", lazy=True)


    def __repr__(self): #automatically called when you print an object or view it in the python console so more readable
        return f"<User {self.id} name: {self.name}>" #insert id and name and return a string


#product db
class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column (db.Integer, primary_key = True) 
    seller_id = db.Column (db.Integer, db.ForeignKey('user.id'), nullable = False)
    name = db.Column(db.String(30), nullable = False, unique = True) #product name
    price = db.Column(db.Float, nullable = False)
    description = db.Column(db.Text, nullable = True) #can be empty
    is_sold = db.Column(db.Boolean, default = True)
    date_posted = db.Column(db.DateTime, default = lambda : datetime.now(timezone.utc))
    image = db.Column(db.String(200), default="default_product.jpg") 
    pickup_location_id = db.Column(db.Integer, db.ForeignKey('safelocation.id'), nullable=True)

#relationship
    transactions = db.relationship('Transaction', backref = 'product',lazy = True)
    pickup_location = db.relationship("SafeLocation", backref="products")
    seller = db.relationship("User", back_populates="products")

    def __repr__(self):
        return f"<Product {self.id}  {self.name}>"

#transaction db
class Transaction(db.Model):
    id = db.Column (db.Integer, primary_key = True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'),nullable = False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable = False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    status = db.Column(db.String(50), default = "pending") #pending/ accepted/ rejected/ completed
    created_at = db.Column(db.DateTime, default = lambda : datetime.now(timezone.utc))
    safe_location_id = db.Column(db.Integer, db.ForeignKey('safelocation.id'))
    
#relationship
    messages = db.relationship('Messages', backref = 'chating',lazy = True)
    buyer = db.relationship('User', foreign_keys=[buyer_id], backref='purchases',lazy = True)
    seller = db.relationship('User', foreign_keys=[seller_id], backref='sales', lazy= True)
    safe_location = db.relationship('SafeLocation', backref = 'location', lazy = True)

    def __repr__(self):
        return f"<Transaction {self.id}  {self.status}>"

#messaging db
class Messages(db.Model):
    id = db.Column (db.Integer, primary_key = True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable = True)
    content = db.Column(db.Text, nullable = False)
    timestamp = db.Column(db.DateTime, default = lambda : datetime.now(timezone.utc))

#relationship
    sender = db.relationship('User', foreign_keys=[sender_id], backref='messages_sent', lazy = True)
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='messages_received', lazy = True)
    
    def __repr__(self):
        return f"<Messages {self.id} from {self.sender_id} to {self.receiver_id}>"
    
#review & rating db
class Review(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable = False)
    rating= db.Column(db.Integer, nullable = False)
    comment = db.Column(db.Text, nullable = True)
    date_review = db.Column(db.DateTime, default = lambda : datetime.now(timezone.utc))

#relationship
    sender = db.relationship('User', foreign_keys=[buyer_id], backref='sender', lazy = True)
    receiver = db.relationship('User', foreign_keys=[seller_id], backref='reveiver', lazy = True)

    def __repr__(self):
        return f"<Review {self.id} :buyer rate {self.rating}>"
    
#location db
class SafeLocation(db.Model):
    __tablename__ = 'safelocation'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    name = db.Column(db.String(100), nullable = False)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable = True)
    longitude = db.Column(db.Float, nullable = True)
    description = db.Column(db.Text, nullable = True)

    def __repr__(self):
        return f"<Safe Location: {self.name} ({self.latitude}, {self.longitude})>"


class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    balance = db.Column(db.Float, default = 0.0)

    def __repr__(self):
        return f"<Wallet {self.user_id} balance {self.balance}>"
    
class Payment(db.Model):
    id =db.Column(db.Integer, primary_key = True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable = False)
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    amount = db.Column(db.Float, nullable = False)
    method =db.Column(db.String(20), nullable= False) #wallet / online / offline
    status = db.Column(db.String(20), default = 'pending') #pending / success / fail
    date_created = db.Column(db.DateTime, default = lambda : datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<Payment {self.id} amount: {self.amount}>"


class Order(db.Model):
    id =db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(20), default="MYR")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    def __repr__(self):
        return f"<Order {self.id} order_id: {self.order_id}>"
