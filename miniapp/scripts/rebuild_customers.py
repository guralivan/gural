#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
ORDERS_FILE = DATA_DIR / "orders.json"
CUSTOMERS_FILE = DATA_DIR / "customers.json"


def _load_json(path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _normalize_user_id(order):
    username = (order.get("username") or "").strip()
    if username:
        return f"@{username}"
    uid = order.get("user_id")
    if uid is None:
        return None
    uid_str = str(uid).strip()
    if not uid_str or uid_str.lower() == "guest":
        return None
    return uid_str


def main():
    orders = _load_json(ORDERS_FILE, [])
    existing_customers = _load_json(CUSTOMERS_FILE, {})
    rebuilt = {}

    for order in orders:
        user_id = _normalize_user_id(order)
        if not user_id:
            continue
        order["user_id"] = user_id
        customer = rebuilt.get(user_id) or existing_customers.get(user_id) or {
            "addresses": [],
            "orders": [],
            "bonus_balance": 0,
            "welcome_bonus_awarded": False,
        }
        if order.get("address"):
            if order["address"] not in customer.get("addresses", []):
                customer.setdefault("addresses", []).append(order["address"])
        if order.get("id") and order["id"] not in customer.get("orders", []):
            customer.setdefault("orders", []).append(order["id"])
        if order.get("name"):
            customer["name"] = order["name"]
        if order.get("username"):
            customer["username"] = order["username"]
        if order.get("phone"):
            customer["phone"] = order["phone"]
        if order.get("email"):
            customer["email"] = order["email"]
        rebuilt[user_id] = customer

    _save_json(ORDERS_FILE, orders)
    _save_json(CUSTOMERS_FILE, rebuilt)
    print(f"Customers rebuilt: {len(rebuilt)}")


if __name__ == "__main__":
    main()
