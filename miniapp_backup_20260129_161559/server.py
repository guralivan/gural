# -*- coding: utf-8 -*-
import json
import threading
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, Response
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
        "filters": {
            "categories": ["Кустовые розы", "Розы", "Хризантемы", "Зелень", "Хвоя"],
            "colors": ["Красные", "Розовые", "Белые", "Зеленые"],
            "features": ["Сеты", "Высокие", "Ароматные", "Стойкие", "Пионовидные"],
        },
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


def _apply_promo(subtotal, promo_code):
    if not promo_code:
        return 0
    rule = PROMO_RULES.get(promo_code)
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
    return send_from_directory(BASE_DIR, "admin.html")


@app.get("/<path:filename>")
def static_files(filename):
    return send_from_directory(BASE_DIR, filename)


@app.get("/api/orders")
def get_orders():
    with LOCK:
        orders = _load_orders()
        user_id = request.args.get("user_id")
        if user_id:
            orders = [o for o in orders if str(o.get("user_id")) == str(user_id)]
        return jsonify(orders)

@app.get("/api/customers/<user_id>")
def get_customer(user_id):
    with LOCK:
        customers = _load_customers()
        return jsonify(customers.get(str(user_id), {"addresses": [], "orders": []}))

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
    payload = request.get_json(force=True, silent=True) or {}
    status = (payload.get("status") or "").strip()
    if status not in {"не обработан", "собран", "отправлен"}:
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
    with LOCK:
        orders = _load_orders()
        new_orders = [o for o in orders if int(o.get("id", 0)) != order_id]
        if len(new_orders) == len(orders):
            return jsonify({"message": "Заказ не найден"}), 404
        _save_orders(new_orders)
    return jsonify({"ok": True})

@app.patch("/api/orders/<int:order_id>")
def update_order(order_id):
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

@app.post("/api/products/<product_id>/image")
def upload_product_image(product_id):
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

@app.post("/api/products/import")
def import_products():
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
    phone = (payload.get("phone") or "").strip()
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
    bonus_requested = int(payload.get("bonus") or 0) > 0
    user_id = payload.get("user_id")
    username = (payload.get("username") or "").strip()

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
    service_fee = round(subtotal * float(settings.get("service_fee_rate", SERVICE_FEE_RATE)))
    discount = _apply_promo(subtotal, promo_code)
    total = subtotal + service_fee + delivery_fee - discount
    bonus_value = int(settings.get("bonus_value", BONUS_VALUE))
    bonus = bonus_value if bonus_requested else 0
    if bonus > total:
        bonus = total
    total = total - bonus

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

        if user_id:
            customers = _load_customers()
            customer = customers.get(str(user_id), {"addresses": [], "orders": []})
            if address and address not in customer.get("addresses", []):
                customer.setdefault("addresses", []).append(address)
            customer.setdefault("orders", []).append(next_id)
            if name:
                customer["name"] = name
            if username:
                customer["username"] = username
            customers[str(user_id)] = customer
            _save_customers(customers)

    return jsonify({"order_id": next_id, "total": total})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
