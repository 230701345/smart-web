from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    uid = db.Column(db.String(64), unique=True, nullable=False)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),)
    user = db.relationship("User")
    product = db.relationship("Product")


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    total_amount = db.Column(db.Integer, nullable=False)
    payment_status = db.Column(db.String(32), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    user = db.relationship("User")


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Integer, nullable=False)
    order = db.relationship("Order")
    product = db.relationship("Product")


def preload_products():
    targets = [
        ("Milk", 50, "66339797"),
        ("Rice", 40, "6F2A9C1F"),
        ("Tomato", 30, "E5340402"),
    ]
    for name, price, uid in targets:
        uid_up = (uid or "").upper()
        existing = Product.query.filter_by(uid=uid_up).first()
        if not existing:
            db.session.add(Product(name=name, price=price, uid=uid_up))
    db.session.commit()
