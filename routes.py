import os
import json
import bcrypt
from flask import Blueprint, request, redirect, url_for, render_template, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from models import db, User, Product, CartItem, Order, OrderItem, preload_products

web_bp = Blueprint("web", __name__)
api_bp = Blueprint("api", __name__)

ACTIVE_USER_ID = None


@web_bp.before_app_request
def load_initial():
    preload_products()
    # Ensure a default demo user exists for ESP32 posts
    demo = User.query.filter_by(username="demo").first()
    if not demo:
        pw = bcrypt.hashpw("SmartCart!123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        demo = User(username="demo", password_hash=pw)
        db.session.add(demo)
        db.session.commit()
    global ACTIVE_USER_ID
    ACTIVE_USER_ID = demo.id


@web_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("web.dashboard"))
    return redirect(url_for("web.login"))


@web_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method != "POST":
        return render_template("register.html")
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"status": "error"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"status": "error"}), 400
    pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(username=username, password_hash=pw)
    db.session.add(user)
    db.session.commit()
    return jsonify({"status": "success"})


@web_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method != "POST":
        return render_template("login.html")
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"status": "error"}), 401
    ok = bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8"))
    if not ok:
        return jsonify({"status": "error"}), 401
    login_user(user)
    global ACTIVE_USER_ID
    ACTIVE_USER_ID = user.id
    return jsonify({"status": "success"})


@web_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("web.login"))


@web_bp.route("/dashboard")
@login_required
def dashboard():
    products = Product.query.all()
    total_qty = db.session.query(db.func.coalesce(db.func.sum(CartItem.quantity), 0)).filter(CartItem.user_id == current_user.id).scalar()
    total_amount = db.session.query(db.func.coalesce(db.func.sum(CartItem.quantity * Product.price), 0)).join(Product, Product.id == CartItem.product_id).filter(CartItem.user_id == current_user.id).scalar()
    return render_template("dashboard.html", products=products, total_qty=total_qty, total_amount=total_amount)


@web_bp.route("/cart")
@login_required
def cart_page():
    items = db.session.query(CartItem, Product).join(Product, Product.id == CartItem.product_id).filter(CartItem.user_id == current_user.id).all()
    total_amount = sum(ci.quantity * p.price for ci, p in items)
    return render_template("cart.html", items=items, total_amount=total_amount)


@web_bp.route("/payment")
@login_required
def payment_page():
    return render_template("payment.html")


@web_bp.route("/success")
@login_required
def success_page():
    return render_template("success.html")


@web_bp.route("/history")
@login_required
def history_page():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    items_map = {}
    for o in orders:
        items = OrderItem.query.filter_by(order_id=o.id).all()
        items_map[o.id] = items
    return render_template("history.html", orders=orders, items_map=items_map)


@api_bp.route("/scan", methods=["POST"])
def scan():
    data = request.get_json() or {}
    uid = (data.get("uid") or "").strip().upper()
    if not uid:
        return jsonify({"status": "error"}), 400
    product = Product.query.filter_by(uid=uid).first()
    if not product:
        return jsonify({"status": "error"}), 404
    uid_for_user = current_user.id if current_user.is_authenticated else ACTIVE_USER_ID
    if not uid_for_user:
        return jsonify({"status": "error"}), 401
    ci = CartItem.query.filter_by(user_id=uid_for_user, product_id=product.id).first()
    if ci:
        ci.quantity += 1
    else:
        ci = CartItem(user_id=uid_for_user, product_id=product.id, quantity=1)
        db.session.add(ci)
    db.session.commit()
    total_amount = db.session.query(db.func.coalesce(db.func.sum(CartItem.quantity * Product.price), 0)).join(Product, Product.id == CartItem.product_id).filter(CartItem.user_id == uid_for_user).scalar()
    return jsonify({"status": "success", "product": product.name, "price": product.price, "cart_total": int(total_amount)})


@api_bp.route("/cart", methods=["GET"])
def cart_get():
    uid_for_user = current_user.id if current_user.is_authenticated else ACTIVE_USER_ID
    if not uid_for_user:
        return jsonify({"status": "error"}), 401
    items = db.session.query(CartItem, Product).join(Product, Product.id == CartItem.product_id).filter(CartItem.user_id == uid_for_user).all()
    out = []
    for ci, p in items:
        out.append({"id": p.id, "name": p.name, "price": int(p.price), "qty": int(ci.quantity)})
    total_amount = sum(i["price"] * i["qty"] for i in out)
    total_qty = sum(i["qty"] for i in out)
    return jsonify({"items": out, "total_items": int(total_qty), "total_price": int(total_amount)})


@api_bp.route("/checkout", methods=["POST"])
def checkout():
    uid_for_user = current_user.id if current_user.is_authenticated else ACTIVE_USER_ID
    if not uid_for_user:
        return jsonify({"status": "error"}), 401
    items = db.session.query(CartItem, Product).join(Product, Product.id == CartItem.product_id).filter(CartItem.user_id == uid_for_user).all()
    if not items:
        return jsonify({"status": "error"}), 400
    total_amount = sum(ci.quantity * p.price for ci, p in items)
    order = Order(user_id=uid_for_user, total_amount=int(total_amount), payment_status="SUCCESS")
    db.session.add(order)
    db.session.commit()
    for ci, p in items:
        db.session.add(OrderItem(order_id=order.id, product_id=p.id, quantity=int(ci.quantity), price_at_purchase=int(p.price)))
    db.session.commit()
    CartItem.query.filter_by(user_id=uid_for_user).delete()
    db.session.commit()
    return jsonify({"status": "success"})


@api_bp.route("/history", methods=["GET"])
def history():
    uid_for_user = current_user.id if current_user.is_authenticated else ACTIVE_USER_ID
    if not uid_for_user:
        return jsonify({"status": "error"}), 401
    orders = Order.query.filter_by(user_id=uid_for_user).order_by(Order.created_at.desc()).all()
    out = []
    for o in orders:
        its = OrderItem.query.filter_by(order_id=o.id).all()
        out.append({"id": o.id, "total_amount": int(o.total_amount), "payment_status": o.payment_status, "created_at": o.created_at.isoformat(), "items": [{"product_id": it.product_id, "quantity": int(it.quantity), "price_at_purchase": int(it.price_at_purchase)} for it in its]})
    return jsonify({"orders": out})
