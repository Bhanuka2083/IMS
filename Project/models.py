from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(150), unique = True)
    username = db.Column(db.String(150), unique = True)
    password = db.Column(db.String(150))
    date_created = db.Column(db.DateTime(timezone = True), default = func.now())
    product = db.relationship('Product', backref='user', passive_deletes = True)
    category = db.relationship('Category', backref='user', passive_deletes = True)
    stock = db.relationship('Stock', backref='user', passive_deletes = True)
    location = db.relationship('Location', backref='user', passive_deletes = True)
    Sale_detail = db.relationship('SaleDetail', backref='user', passive_deletes = True)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(80), unique=True, nullable=False)
    date_created = db.Column(db.DateTime(timezone = True), default = func.now())
    products = db.relationship('Product', backref='category', passive_deletes = True) # Define the relationship to Product (backref helps access products from a category)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Foreign Key: Links Category to User

class Location(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    location_name = db.Column(db.String(150), unique = True)
    date_created = db.Column(db.DateTime(timezone = True), default = func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Foreign Key: Links Stock to User M : 1
    stock_id = db.relationship('Stock', backref='location', passive_deletes = True) # Define the relationship to Stock (backref helps access stocks from a location)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    item_name = db.Column(db.String(150), unique = True)
    date_created = db.Column(db.DateTime(timezone = True), default = func.now())
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False) # Foreign Key: Links Product to Category
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Foreign Key: Links Product to User
    stocks = db.relationship('Stock', backref='product', passive_deletes = True) # Define the relationship to Stock (backref helps access products from a category)



class Stock(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    stock_name = db.Column(db.String(150), unique = True)
    unit_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    saled_quantity = db.Column(db.Integer)
    stock_description = db.Column(db.String(1500))
    date_created = db.Column(db.DateTime(timezone = True), default = func.now())
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False) # Foreign Key: Links Stock to Product 1: 1
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False) # Foreign Key: Links Stock to Category M : 1
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Foreign Key: Links Stock to User M : 1
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False) # Foreign Key: Links Stock to Location M : 1
    selles_dtails_id = db.relationship('SaleDetail', backref='stock', passive_deletes = True) # Define the relationship to Saledetails (backref helps access stocks from a location)
    




class Sale(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    sale_name = db.Column(db.String(150), unique = True)
    buyer_name = db.Column(db.String(150))
    total_amount = db.Column(db.Float, nullable=False)
    date_created = db.Column(db.DateTime(timezone = True), default = func.now())
    selles_dtails_id = db.relationship('SaleDetail', backref='sale', passive_deletes = True) # Define the relationship to Saledetails (backref helps access stocks from a location)
    



class SaleDetail(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    quantity_sold = db.Column(db.Integer, nullable=False)
    date_created = db.Column(db.DateTime(timezone = True), default = func.now())
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False) # Foreign Key: Links Sale to Sale_Details M : 1
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False) # Foreign Key: Links Stock to Sale_Details M : 1
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Foreign Key: Links Stock to User M : 1


class LogMesssage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(50)) # e.g., 'error', 'success', 'info'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Optional: Who saw/triggered the message
    date_created = db.Column(db.DateTime(timezone = True), default = func.now())


class UserLoginLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(250))
    status = db.Column(db.String(20), default='Success')
    login_time = db.Column(db.DateTime(timezone=True), default=func.now())
    user = db.relationship('User')


