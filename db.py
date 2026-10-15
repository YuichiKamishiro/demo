import glob
import os
import sqlite3

import pandas as pd

# Таблицы базы (модуль 1): каждая сущность отдельно, связи через id
TABLES = """
CREATE TABLE roles (role_id INTEGER PRIMARY KEY,
  role_name VARCHAR(50) NOT NULL UNIQUE);
CREATE TABLE users (user_id INTEGER PRIMARY KEY,
  last_name VARCHAR(100) NOT NULL, first_name VARCHAR(100) NOT NULL,
  middle_name VARCHAR(100), login VARCHAR(100) NOT NULL UNIQUE,
  role_id INTEGER NOT NULL REFERENCES roles(role_id));
CREATE TABLE products (product_id INTEGER PRIMARY KEY,
  article VARCHAR(50) UNIQUE, category VARCHAR(100) NOT NULL,
  subcategory VARCHAR(100), product_name VARCHAR(200) NOT NULL,
  manufacturer VARCHAR(100), description VARCHAR(1000),
  composition VARCHAR(200), price NUMERIC(10,2) NOT NULL,
  image_path VARCHAR(255));
CREATE TABLE sizes (size_id INTEGER PRIMARY KEY,
  size_value NUMERIC(4,1) NOT NULL UNIQUE);
CREATE TABLE stock_items (stock_item_id INTEGER PRIMARY KEY,
  product_id INTEGER NOT NULL REFERENCES products(product_id),
  size_id INTEGER NOT NULL REFERENCES sizes(size_id),
  quantity_available INTEGER NOT NULL);
CREATE TABLE orders (order_id INTEGER PRIMARY KEY,
  order_date DATE NOT NULL,
  user_id INTEGER NOT NULL REFERENCES users(user_id));
CREATE TABLE order_items (order_item_id INTEGER PRIMARY KEY,
  order_id INTEGER NOT NULL REFERENCES orders(order_id),
  product_id INTEGER NOT NULL REFERENCES products(product_id),
  size_id INTEGER NOT NULL REFERENCES sizes(size_id),
  quantity INTEGER NOT NULL, price NUMERIC(10,2) NOT NULL);
"""


def excel(name):
    # Ищем файл во всех подпапках: не важно, как распакован архив
    found = glob.glob(f"**/{name}_import.xlsx", recursive=True)
    if not found:
        raise SystemExit(f"Нет {name}_import.xlsx: распакуй Прил_2")
    return pd.read_excel(found[0]).fillna("").to_dict("records")


if os.path.exists("chudo.db"):
    os.remove("chudo.db")  # каждый запуск создаёт базу заново
db = sqlite3.connect("chudo.db")
db.executescript(TABLES)

for r in excel("Products"):
    db.execute("INSERT INTO products (article, category, subcategory,"
               " product_name, manufacturer, description,"
               " composition, price, image_path)"
               " VALUES (?,?,?,?,?,?,?,?,?)",
               (r["Артикул"], r["Категория"], r["Подкатегория"],
                r["Наименование"], r["Производство"], r["Описание"],
                r["Состав"], r["Цена"], r["Фото"]))

for r in excel("Sizes"):
    db.execute("INSERT INTO sizes (size_value) VALUES (?)",
               (r["Размер"],))

for r in excel("Users"):
    db.execute("INSERT OR IGNORE INTO roles (role_name) VALUES (?)",
               (r["Роль"],))
    fio = r["ФИО"].split() + [None]
    db.execute("INSERT INTO users (last_name, first_name,"
               " middle_name, login, role_id)"
               " SELECT ?, ?, ?, ?, role_id FROM roles"
               " WHERE role_name = ?",
               (fio[0], fio[1], fio[2], r["Логин"], r["Роль"]))

for r in excel("Stock_Items"):
    db.execute("INSERT INTO stock_items (product_id, size_id,"
               " quantity_available) SELECT product_id, size_id, ?"
               " FROM products, sizes"
               " WHERE article = ? AND size_value = ?",
               (r["Количество"], r["Артикул"], r["Размер"]))

for r in excel("Orders"):
    db.execute("INSERT OR IGNORE INTO orders (order_id, order_date,"
               " user_id) SELECT ?, ?, user_id FROM users"
               " WHERE login = ?",
               (r["Номер заказа"], str(r["Дата заказа"])[:10],
                r["Логин"]))
    db.execute("INSERT INTO order_items (order_id, product_id,"
               " size_id, quantity, price)"
               " SELECT ?, product_id, size_id, ?, ?"
               " FROM products, sizes"
               " WHERE article = ? AND size_value = ?",
               (r["Номер заказа"], r["Количество"], r["Цена"],
                r["Артикул"], r["Размер"]))

db.commit()
count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
print("База готова, товаров:", count)
