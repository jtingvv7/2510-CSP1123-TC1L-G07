from extensions import db
from datetime import datetime, timezone
from flask_login import UserMixin
from datetime import datetime, timezone

# User model
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    profile_pic = db.Column(db.String(200), nullable=True)
    join_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default="user") #admin
    profile_address = db.Column(db.String(250))
    is_active = db.Column(db.Boolean, default=True)
    last_seen_announcement_id = db.Column(db.Integer, default=0) #for announcement flash

    @property
    def is_sold(self):
        return self.quantity <= 0 or not self.is_active
    
    # relationship of user
    wallet = db.relationship("Wallet", backref="wallet_owner", uselist=False, lazy=True)
    payment = db.relationship("Payment", backref="payment_user", lazy=True)
    
    def __repr__(self):
        return f"<User {self.id} name: {self.name}>"

# Product model
class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # FK to User
    name = db.Column(db.String(30), nullable=False, unique=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_sold = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True) 
    date_posted = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    image = db.Column(db.String(200), default="default_product.jpg")
    pickup_location_id = db.Column(db.Integer, db.ForeignKey('safelocation.id'), nullable=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    # relationships
    transactions = db.relationship('Transaction', backref='product', lazy=True)
    pickup_location = db.relationship("SafeLocation", backref="products")
    seller = db.relationship(
    "User",
    backref=db.backref("products_selling", lazy=True),  # Use a unique backref name
    foreign_keys=[seller_id])

    def __repr__(self):
        return f"<Product {self.id}  {self.name}>"
    
    @property
    def sold_out(self):
        """Automatically returns True if quantity is 0 or product is marked sold"""
        return self.is_sold or self.quantity <= 0

#transaction db
class Transaction(db.Model):
    id = db.Column (db.Integer, primary_key = True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'),nullable = False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable = False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    status = db.Column(db.String(50), default = "pending") #pending/ accepted/ rejected/ shipped/ completed
    created_at = db.Column(db.DateTime, default = lambda : datetime.now(timezone.utc))
    safe_location_id = db.Column(db.Integer, db.ForeignKey('safelocation.id'))
    price = db.Column(db.Float, nullable=False)
    
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
    content = db.Column(db.Text, nullable = True)
    timestamp = db.Column(db.DateTime, default = lambda : datetime.now(timezone.utc))
    is_read = db.Column(db.Text, default = True)
    message_type = db.Column(db.String(20), default = "text") #text/image/transaction

#relationship
    sender = db.relationship('User', foreign_keys=[sender_id], backref='messages_sent', lazy = True)
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='messages_received', lazy = True)
    
    def __repr__(self):
        return f"<Messages {self.id} from {self.sender_id} to {self.receiver_id}>"
    
#review & rating db
class Review(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), nullable = False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable = False)
    rating= db.Column(db.Integer, nullable = False)
    comment = db.Column(db.Text, nullable = True)
    image_path = db.Column(db.String(225), nullable=True)
    date_review = db.Column(db.DateTime, default = lambda : datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Review {self.id} by {self.id} rating {self.rating}>"
    

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

#wallet db
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
    
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reported_type = db.Column(db.String(50), nullable=False)   # user / product / transaction / message
    reported_id = db.Column(db.Integer, nullable=True)        
    reason = db.Column(db.Text, nullable=False)
    evidence_file = db.Column(db.String(255), nullable=True)   # save filename (JPG/PNG/PDF)
    status = db.Column(db.String(20), default="pending")       # pending / resolved
    date_report = db.Column(db.DateTime, default = lambda : datetime.now(timezone.utc))
    #admin feedback
    admin_comment = db.Column(db.Text, nullable = True)
    #appeal part
    appeal_text = db.Column(db.Text, nullable=True)
    appeal_file = db.Column(db.String(200), nullable=True)
    appeal_status = db.Column(db.String(20), default="none")   # none / submitted / reviewed
    appeal_deadline = db.Column(db.DateTime, nullable=True)

    # relationship
    reporter = db.relationship("User", backref="reports", lazy=True)

    def _repr_(self):
        return f"<Report {self.id} status={self.status}>"
    
class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True) #None = to everyone
    reporter_id = db.Column(db.Integer, db.ForeignKey("report.id"), nullable=True) #if about report
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default = lambda : datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # which admin

    # relationship
    author = db.relationship("User", backref="author", lazy=True)
    report = db.relationship("Report", backref="announcements", lazy=True)