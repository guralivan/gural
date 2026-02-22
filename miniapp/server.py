# -*- coding: utf-8 -*-
import base64
import json
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, Response
from markupsafe import escape
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"
ORDERS_FILE = DATA_DIR / "orders.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
CUSTOMERS_FILE = DATA_DIR / "customers.json"
ASSETS_DIR = BASE_DIR / "assets"

LOCK = threading.Lock()

PROMO_RULES = {
    "FLOWER10": {"type": "percent", "value": 10},
    "MOSCOW500": {"type": "fixed", "value": 500},
}

SERVICE_FEE_RATE = 0.1
BONUS_VALUE = 300

app = Flask(__name__)
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


def _check_basic_auth():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(auth.split(" ", 1)[1]).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return False
    user, _, password = decoded.partition(":")
    return user == ADMIN_USER and password == ADMIN_PASSWORD


def _require_admin():
    if _check_basic_auth():
        return None
    return Response(
        "Unauthorized",
        401,
        {"WWW-Authenticate": 'Basic realm="Admin"'},
    )


def _load_products():
    if not PRODUCTS_FILE.exists():
        return []
    with PRODUCTS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)

def _save_products(products):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with PRODUCTS_FILE.open("w", encoding="utf-8") as file:
        json.dump(products, file, ensure_ascii=False, indent=2)

def _allowed_image(filename):
    ext = Path(filename).suffix.lower()
    return ext in {".jpg", ".jpeg", ".png", ".webp"}

def _default_settings():
    return {
        "service_fee_rate": 0.1,
        "bonus_value": 300,
        "bonus_balance": 500,
        "bonus_earn_rate": 0.01,
        "theme_color": "#94a36a",
        "hero_title": "Цветы по себестоимости",
        "hero_subtitle": "Доставка по Москве",
        "offer_enabled": True,
        "offer_link_title": (
            "Я принимаю условия Публичной оферты, "
            "а также даю согласие на обработку персональных данных."
        ),
        "offer_page_text": "Публичная оферта",
        "offer_link": "/offer.html",
        "filters": {
            "categories": ["Кустовые розы", "Розы", "Хризантемы", "Зелень", "Хвоя"],
            "colors": ["Красные", "Розовые", "Белые", "Зеленые"],
            "features": ["Сеты", "Высокие", "Ароматные", "Стойкие", "Пионовидные"],
        },
        "promo_codes": [
            {"code": "FLOWER10", "type": "percent", "value": 10},
            {"code": "MOSCOW500", "type": "fixed", "value": 500},
        ],
    }

def _load_settings():
    if not SETTINGS_FILE.exists():
        return _default_settings()
    with SETTINGS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    merged = _default_settings()
    merged.update({k: data.get(k) for k in merged.keys() if k in data})
    return merged

def _save_settings(settings):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with SETTINGS_FILE.open("w", encoding="utf-8") as file:
        json.dump(settings, file, ensure_ascii=False, indent=2)

def _load_customers():
    if not CUSTOMERS_FILE.exists():
        return {}
    with CUSTOMERS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)

def _save_customers(customers):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CUSTOMERS_FILE.open("w", encoding="utf-8") as file:
        json.dump(customers, file, ensure_ascii=False, indent=2)


def _load_orders():
    if not ORDERS_FILE.exists():
        return []
    with ORDERS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def _save_orders(orders):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with ORDERS_FILE.open("w", encoding="utf-8") as file:
        json.dump(orders, file, ensure_ascii=False, indent=2)


def _promo_rules_from_settings(settings):
    rules = {}
    for item in settings.get("promo_codes", []) or []:
        code = (item.get("code") or "").strip().upper()
        if not code:
            continue
        rule_type = item.get("type") if item.get("type") in {"percent", "fixed"} else "fixed"
        try:
            value = float(item.get("value") or 0)
        except (TypeError, ValueError):
            value = 0
        if value <= 0:
            continue
        rules[code] = {"type": rule_type, "value": value}
    return rules or PROMO_RULES


def _apply_promo(subtotal, promo_code, rules):
    if not promo_code:
        return 0
    rule = rules.get(promo_code)
    if not rule:
        return 0
    if rule["type"] == "percent":
        return min(subtotal, subtotal * rule["value"] / 100)
    return min(subtotal, rule["value"])


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/admin")
def admin():
    auth = _require_admin()
    if auth:
        return auth
    return send_from_directory(BASE_DIR, "admin.html")


@app.get("/offer.html")
def offer_page():
    settings = _load_settings()
    title = "Jamsu — Публичная оферта"
    offer_page_text = (
        settings.get("offer_page_text")
        or settings.get("offer_text")
        or "Публичная оферта"
    )
    normalized_text = re.sub(r"<br\s*/?>", "\n", offer_page_text, flags=re.IGNORECASE)
    safe_text = escape(normalized_text)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", safe_text) if p.strip()]
    offer_html = "".join(f"<p>{p.replace(chr(10), '<br />')}</p>" for p in paragraphs)
    html = f"""<!doctype html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <link rel="stylesheet" href="styles.css?v=20260130" />
  </head>
  <body>
    <div class="app">
      <section class="hero">
        <div class="hero-title">Публичная оферта</div>
        <div class="hero-subtitle">Jamsu</div>
      </section>
      <section class="about">
        <div class="offer-content">{offer_html}</div>
      </section>
    </div>
  </body>
</html>"""
    return Response(html, mimetype="text/html")


@app.get("/<path:filename>")
def static_files(filename):
    return send_from_directory(BASE_DIR, filename)


@app.get("/api/orders")
def get_orders():
    with LOCK:
        orders = _load_orders()
        user_id = request.args.get("user_id")
        if not user_id:
            auth = _require_admin()
            if auth:
                return auth
        if user_id:
            orders = [o for o in orders if str(o.get("user_id")) == str(user_id)]
        return jsonify(orders)

@app.get("/api/customers/<user_id>")
def get_customer(user_id):
    with LOCK:
        customers = _load_customers()
        if str(user_id) == "guest":
            return jsonify({"addresses": [], "orders": [], "bonus_balance": 0})
        customer = customers.get(str(user_id))
        if not customer:
            settings = _load_settings()
            customer = {
                "addresses": [],
                "orders": [],
                "bonus_balance": int(settings.get("bonus_balance", 0)),
                "welcome_bonus_awarded": True,
            }
            customers[str(user_id)] = customer
            _save_customers(customers)
        if "bonus_balance" not in customer:
            settings = _load_settings()
            customer["bonus_balance"] = int(settings.get("bonus_balance", 0))
            customers[str(user_id)] = customer
            _save_customers(customers)
        if "welcome_bonus_awarded" not in customer:
            customer["welcome_bonus_awarded"] = True
            customers[str(user_id)] = customer
            _save_customers(customers)
        return jsonify(customer)


@app.delete("/api/customers/<user_id>")
def delete_customer(user_id):
    auth = _require_admin()
    if auth:
        return auth
    with LOCK:
        customers = _load_customers()
        if str(user_id) not in customers:
            return jsonify({"message": "Покупатель не найден"}), 404
        customers.pop(str(user_id), None)
        _save_customers(customers)
    return jsonify({"ok": True})


@app.get("/api/customers")
def list_customers():
    auth = _require_admin()
    if auth:
        return auth
    include_orders = request.args.get("include") == "orders"
    with LOCK:
        customers = _load_customers()
        orders = _load_orders() if include_orders else []
        orders_map = {}
        orders_by_user = {}
        orders_by_username = {}
        if include_orders:
            for order in orders:
                oid = int(order.get("id", 0))
                if oid:
                    orders_map[oid] = order
                uid = str(order.get("user_id"))
                if not uid:
                    continue
                orders_by_user.setdefault(uid, []).append(order)
                username = (order.get("username") or "").strip()
                if username:
                    orders_by_username.setdefault(f"@{username}", []).append(order)
        result = []
        for uid, customer in customers.items():
            entry = {"user_id": uid}
            if isinstance(customer, dict):
                entry.update(customer)
            if include_orders:
                order_ids = [
                    int(order_id)
                    for order_id in (customer.get("orders") or [])
                    if str(order_id).isdigit()
                ]
                order_details = [orders_map.get(oid) for oid in order_ids]
                order_details = [o for o in order_details if o]
                if not order_details:
                    order_details = orders_by_user.get(str(uid), [])
                if not order_details:
                    order_details = orders_by_username.get(str(uid), [])
                entry["order_details"] = order_details
                if order_details:
                    last_order = order_details[-1]
                    entry.setdefault("phone", last_order.get("phone"))
                    entry.setdefault("email", last_order.get("email"))
                    entry.setdefault("name", last_order.get("name"))
                    entry.setdefault("address", last_order.get("address"))
            result.append(entry)
        return jsonify(result)

@app.patch("/api/customers/<user_id>")
def update_customer(user_id):
    payload = request.get_json(force=True, silent=True) or {}
    with LOCK:
        customers = _load_customers()
        customer = customers.get(str(user_id), {"addresses": [], "orders": []})
        if "addresses" in payload and isinstance(payload.get("addresses"), list):
            customer["addresses"] = payload.get("addresses")
        if "name" in payload:
            customer["name"] = payload.get("name")
        if "username" in payload:
            customer["username"] = payload.get("username")
        customers[str(user_id)] = customer
        _save_customers(customers)
    return jsonify({"ok": True})

@app.patch("/api/orders/<int:order_id>/status")
def update_order_status(order_id):
    auth = _require_admin()
    if auth:
        return auth
    payload = request.get_json(force=True, silent=True) or {}
    status = (payload.get("status") or "").strip()
    if status not in {"не обработан", "собран", "отправлен", "оплачен", "выполнен", "отменен"}:
        return jsonify({"message": "Некорректный статус"}), 400
    with LOCK:
        orders = _load_orders()
        updated = False
        for order in orders:
            if int(order.get("id", 0)) == order_id:
                order["status"] = status
                updated = True
                break
        if not updated:
            return jsonify({"message": "Заказ не найден"}), 404
        _save_orders(orders)
    return jsonify({"ok": True})

@app.delete("/api/orders/<int:order_id>")
def delete_order(order_id):
    auth = _require_admin()
    if auth:
        return auth
    with LOCK:
        orders = _load_orders()
        new_orders = [o for o in orders if int(o.get("id", 0)) != order_id]
        if len(new_orders) == len(orders):
            return jsonify({"message": "Заказ не найден"}), 404
        _save_orders(new_orders)
    return jsonify({"ok": True})

@app.patch("/api/orders/<int:order_id>")
def update_order(order_id):
    auth = _require_admin()
    if auth:
        return auth
    payload = request.get_json(force=True, silent=True) or {}
    allowed_fields = {
        "phone",
        "name",
        "email",
        "address",
        "delivery_time",
        "recipient_name",
        "recipient_phone",
        "delivery_id",
        "delivery_fee",
        "promo_code",
        "status",
    }
    with LOCK:
        orders = _load_orders()
        updated = False
        for order in orders:
            if int(order.get("id", 0)) == order_id:
                for key, value in payload.items():
                    if key in allowed_fields:
                        order[key] = value
                updated = True
                break
        if not updated:
            return jsonify({"message": "Заказ не найден"}), 404
        _save_orders(orders)
    return jsonify({"ok": True})
@app.get("/api/settings")
def get_settings():
    with LOCK:
        return jsonify(_load_settings())

@app.patch("/api/settings")
def update_settings():
    auth = _require_admin()
    if auth:
        return auth
    payload = request.get_json(force=True, silent=True) or {}
    with LOCK:
        settings = _load_settings()
        for key in settings.keys():
            if key in payload:
                settings[key] = payload[key]
        if "filters" in payload and isinstance(payload.get("filters"), dict):
            settings["filters"] = payload["filters"]
        _save_settings(settings)
    return jsonify({"ok": True})

@app.get("/api/products")
def get_products():
    with LOCK:
        return jsonify(_load_products())

@app.patch("/api/products/<product_id>")
def update_product(product_id):
    auth = _require_admin()
    if auth:
        return auth
    payload = request.get_json(force=True, silent=True) or {}
    with LOCK:
        products = _load_products()
        updated = False
        for product in products:
            if str(product.get("id")) == str(product_id):
                if "image" in payload:
                    image = (payload.get("image") or "").strip()
                    product["image"] = image or None
                if "name" in payload:
                    product["name"] = (payload.get("name") or "").strip()
                if "description" in payload:
                    product["description"] = (payload.get("description") or "").strip()
                if "price" in payload:
                    product["price"] = int(payload.get("price") or 0)
                if "min_qty" in payload:
                    product["min_qty"] = max(1, int(payload.get("min_qty") or 1))
                if "tags" in payload and isinstance(payload.get("tags"), list):
                    product["tags"] = payload.get("tags")
                if "delivery_label" in payload:
                    product["delivery_label"] = (payload.get("delivery_label") or "").strip() or None
                updated = True
                break
        if not updated:
            return jsonify({"message": "Товар не найден"}), 404
        _save_products(products)
    return jsonify({"ok": True})


@app.delete("/api/products/<product_id>")
def delete_product(product_id):
    auth = _require_admin()
    if auth:
        return auth
    with LOCK:
        products = _load_products()
        new_products = [p for p in products if str(p.get("id")) != str(product_id)]
        if len(new_products) == len(products):
            return jsonify({"message": "Товар не найден"}), 404
        _save_products(new_products)
    return jsonify({"ok": True})

@app.post("/api/products/<product_id>/image")
def upload_product_image(product_id):
    auth = _require_admin()
    if auth:
        return auth
    if "image" not in request.files:
        return jsonify({"message": "Файл не найден"}), 400
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"message": "Файл не выбран"}), 400
    if not _allowed_image(file.filename):
        return jsonify({"message": "Неподдерживаемый формат"}), 400
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix.lower()
    safe_id = secure_filename(str(product_id))
    filename = f"{safe_id}-{int(time.time())}{ext}"
    save_path = ASSETS_DIR / filename
    file.save(save_path)
    with LOCK:
        products = _load_products()
        updated = False
        for product in products:
            if str(product.get("id")) == str(product_id):
                product["image"] = f"/assets/{filename}"
                updated = True
                break
        if not updated:
            return jsonify({"message": "Товар не найден"}), 404
        _save_products(products)
    return jsonify({"ok": True, "path": f"/assets/{filename}"})


@app.post("/api/products")
def create_product():
    auth = _require_admin()
    if auth:
        return auth
    payload = request.get_json(force=True, silent=True) or {}
    with LOCK:
        products = _load_products()
        existing_ids = {str(p.get("id")) for p in products}
        requested_id = str(payload.get("id") or "").strip()
        if requested_id and requested_id in existing_ids:
            return jsonify({"message": "ID уже используется"}), 400
        if requested_id:
            product_id = requested_id
        else:
            base_id = f"p{int(time.time())}"
            product_id = base_id
            counter = 1
            while product_id in existing_ids:
                counter += 1
                product_id = f"{base_id}_{counter}"
        tags = payload.get("tags")
        if not isinstance(tags, list):
            tags = []
        product = {
            "id": product_id,
            "name": (payload.get("name") or "Новый товар").strip(),
            "price": int(payload.get("price") or 0),
            "category": (payload.get("category") or "").strip(),
            "tags": tags,
            "description": (payload.get("description") or "").strip(),
            "min_qty": max(1, int(payload.get("min_qty") or 1)),
            "delivery_label": (payload.get("delivery_label") or "").strip(),
            "image": (payload.get("image") or "").strip(),
        }
        products.append(product)
        _save_products(products)
    return jsonify(product), 201

@app.post("/api/products/import")
def import_products():
    auth = _require_admin()
    if auth:
        return auth
    if "file" not in request.files:
        return jsonify({"message": "Файл не найден"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "Файл не выбран"}), 400
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"message": "Нужен CSV файл"}), 400
    content = file.read().decode("utf-8")
    lines = [line for line in content.splitlines() if line.strip()]
    if not lines:
        return jsonify({"message": "Пустой файл"}), 400
    header = [h.strip() for h in lines[0].split(",")]
    rows = lines[1:]
    products = []
    for row in rows:
        cols = [c.strip() for c in row.split(",")]
        data = dict(zip(header, cols))
        tags = [t.strip() for t in data.get("tags", "").split("|") if t.strip()]
        product = {
            "id": data.get("id") or f"p{len(products) + 1}",
            "name": data.get("name", ""),
            "price": int(float(data.get("price", 0) or 0)),
            "category": data.get("category", ""),
            "tags": tags,
            "description": data.get("description", ""),
            "min_qty": int(float(data.get("min_qty", 1) or 1)),
            "delivery_label": data.get("delivery_label", ""),
            "image": data.get("image", ""),
        }
        products.append(product)
    with LOCK:
        _save_products(products)
    return jsonify({"ok": True, "count": len(products)})

@app.patch("/api/products/bulk")
def update_products_bulk():
    auth = _require_admin()
    if auth:
        return auth
    payload = request.get_json(force=True, silent=True) or {}
    items = payload.get("products") or []
    with LOCK:
        products = _load_products()
        products_map = {str(p.get("id")): p for p in products}
        for item in items:
            pid = str(item.get("id"))
            if pid not in products_map:
                continue
            product = products_map[pid]
            if "name" in item:
                product["name"] = str(item.get("name") or "").strip()
            if "description" in item:
                product["description"] = str(item.get("description") or "").strip()
            if "price" in item:
                product["price"] = int(item.get("price") or 0)
            if "min_qty" in item:
                product["min_qty"] = max(1, int(item.get("min_qty") or 1))
            if "tags" in item and isinstance(item.get("tags"), list):
                product["tags"] = item.get("tags")
            if "delivery_label" in item:
                product["delivery_label"] = str(item.get("delivery_label") or "").strip()
            if "image" in item:
                product["image"] = str(item.get("image") or "").strip()
        _save_products(list(products_map.values()))
    return jsonify({"ok": True})

@app.get("/api/products/export")
def export_products():
    auth = _require_admin()
    if auth:
        return auth
    with LOCK:
        products = _load_products()
    header = [
        "id",
        "name",
        "price",
        "category",
        "tags",
        "description",
        "min_qty",
        "delivery_label",
        "image",
    ]
    lines = [",".join(header)]
    for product in products:
        tags = "|".join(product.get("tags", []) or [])
        row = [
            str(product.get("id", "")),
            str(product.get("name", "")).replace(",", " "),
            str(product.get("price", "")),
            str(product.get("category", "")).replace(",", " "),
            tags.replace(",", " "),
            str(product.get("description", "")).replace(",", " "),
            str(product.get("min_qty", "")),
            str(product.get("delivery_label", "")),
            str(product.get("image", "")),
        ]
        lines.append(",".join(row))
    csv_content = "\n".join(lines)
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=products.csv"},
    )


@app.post("/api/orders")
def create_order():
    payload = request.get_json(force=True, silent=True) or {}
    phone_raw = (payload.get("phone") or "").strip()
    phone_digits = "".join(ch for ch in phone_raw if ch.isdigit())
    if len(phone_digits) == 11 and phone_digits.startswith("8"):
        phone = f"+7{phone_digits[1:]}"
    elif len(phone_digits) == 11 and phone_digits.startswith("7"):
        phone = f"+7{phone_digits[1:]}"
    elif len(phone_digits) == 10:
        phone = f"+7{phone_digits}"
    else:
        phone = phone_raw
    items = payload.get("items") or []
    promo_code = (payload.get("promo_code") or "").strip().upper()
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    address = (payload.get("address") or "").strip()
    delivery_time = (payload.get("delivery_time") or "").strip()
    recipient_name = (payload.get("recipient_name") or "").strip()
    recipient_phone = (payload.get("recipient_phone") or "").strip()
    delivery_id = (payload.get("delivery_id") or "").strip()
    delivery_fee = int(payload.get("delivery_fee") or 0)
    bonus_requested = int(payload.get("bonus") or 0)
    user_id = payload.get("user_id")
    username = (payload.get("username") or "").strip()
    if username:
        user_id = f"@{username}"
    elif isinstance(user_id, str) and user_id.startswith("@"):
        username = user_id.lstrip("@")

    if not phone or len(items) == 0:
        return jsonify({"message": "Телефон и товары обязательны"}), 400
    if not phone.startswith("+7") or len(phone) != 12 or not phone[1:].isdigit():
        return jsonify({"message": "Телефон должен быть в формате +7XXXXXXXXXX"}), 400

    products = {p["id"]: p for p in _load_products()}
    order_items = []
    subtotal = 0
    for item in items:
        product_id = item.get("id")
        qty = int(item.get("qty") or 0)
        product = products.get(product_id)
        if not product or qty <= 0:
            continue
        line_total = product["price"] * qty
        subtotal += line_total
        order_items.append(
            {
                "id": product_id,
                "name": product["name"],
                "price": product["price"],
                "qty": qty,
            }
        )

    if not order_items:
        return jsonify({"message": "Некорректные товары"}), 400

    settings = _load_settings()
    promo_rules = _promo_rules_from_settings(settings)
    service_fee = round(subtotal * float(settings.get("service_fee_rate", SERVICE_FEE_RATE)))
    discount = _apply_promo(subtotal, promo_code, promo_rules)
    total_before_bonus = subtotal + service_fee + delivery_fee - discount
    available_bonus = int(settings.get("bonus_balance", 0))
    if user_id and str(user_id) != "guest":
        customers = _load_customers()
        customer = customers.get(str(user_id), {})
        available_bonus = int(customer.get("bonus_balance", available_bonus))
    bonus = max(0, min(int(bonus_requested or 0), available_bonus, total_before_bonus))
    total = total_before_bonus - bonus
    bonus_earned = round(subtotal * float(settings.get("bonus_earn_rate", 0)))
    if bonus > 0:
        bonus_earned = 0

    with LOCK:
        orders = _load_orders()
        next_id = (orders[-1]["id"] + 1) if orders else 1
        order = {
            "id": next_id,
            "user_id": user_id,
            "username": username,
            "phone": phone,
            "name": name,
            "email": email,
            "address": address,
            "delivery_time": delivery_time,
            "recipient_name": recipient_name,
            "recipient_phone": recipient_phone,
            "delivery_id": delivery_id,
            "items": order_items,
            "promo_code": promo_code or None,
            "subtotal": subtotal,
            "service_fee": service_fee,
            "delivery_fee": delivery_fee,
            "discount": discount,
            "bonus": bonus,
            "total": total,
            "status": "не обработан",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        orders.append(order)
        _save_orders(orders)

        if user_id and str(user_id) != "guest":
            customers = _load_customers()
            customer = customers.get(
                str(user_id),
                {
                    "addresses": [],
                    "orders": [],
                    "bonus_balance": available_bonus,
                    "welcome_bonus_awarded": True,
                },
            )
            if address and address not in customer.get("addresses", []):
                customer.setdefault("addresses", []).append(address)
            customer.setdefault("orders", []).append(next_id)
            if name:
                customer["name"] = name
            if username:
                customer["username"] = username
            customer["phone"] = phone
            if email:
                customer["email"] = email
            current_bonus = int(customer.get("bonus_balance", available_bonus))
            customer["bonus_balance"] = max(0, current_bonus - int(bonus)) + int(bonus_earned)
            customers[str(user_id)] = customer
            _save_customers(customers)

    return jsonify({"order_id": next_id, "total": total})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
