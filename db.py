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
  article VARCHAR(50), category VARCHAR(100) NOT NULL,
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

# Товар в других файлах ищем по артикулу или по наименованию
PRODUCT = "(article = ? OR product_name = ?)"
# Клиента в заказах ищем по логину или по ФИО
USER = ("(login = ? OR TRIM(last_name || ' ' || first_name || ' '"
        " || IFNULL(middle_name, '')) = ?)")


def excel(name):
    # Ищем файл во всех подпапках: не важно, как распакован архив
    found = glob.glob(f"**/{name}_import.xlsx", recursive=True)
    if not found:
        raise SystemExit(f"Нет {name}_import.xlsx: распакуй Прил_2")
    return pd.read_excel(found[0]).fillna("").to_dict("records")


def get(row, *words, default=KeyError):
    # Колонку ищем по названию без учёта регистра: сначала точное
    # совпадение, потом часть слова («Цена, руб.» найдётся по «цена»)
    columns = {str(c).strip().lower(): c for c in row}
    for word in words:
        if word in columns:
            return row[columns[word]]
    for word in words:
        for name, column in columns.items():
            if word in name:
                return row[column]
    if default is KeyError:
        raise SystemExit(f"Нет колонки {words}. Есть: {list(row)}")
    return default


if os.path.exists("chudo.db"):
    os.remove("chudo.db")  # каждый запуск создаёт базу заново
db = sqlite3.connect("chudo.db")
db.executescript(TABLES)

for r in excel("Products"):
    db.execute("INSERT INTO products (article, category, subcategory,"
               " product_name, manufacturer, description,"
               " composition, price, image_path)"
               " VALUES (?,?,?,?,?,?,?,?,?)",
               (get(r, "артикул", default=""), get(r, "категория"),
                get(r, "подкатегория", default=""),
                get(r, "наименование", "название"),
                get(r, "производство", "производитель"),
                get(r, "описание", default=""), get(r, "состав"),
                get(r, "цена", "стоимость"),
                get(r, "фото", "изображение", default="")))

for r in excel("Sizes"):
    db.execute("INSERT OR IGNORE INTO sizes (size_value) VALUES (?)",
               (get(r, "размер"),))

for r in excel("Users"):
    role = get(r, "роль")
    db.execute("INSERT OR IGNORE INTO roles (role_name) VALUES (?)",
               (role,))
    fio = get(r, "фио", default="")
    if fio:
        parts = fio.split() + [None]
    else:
        parts = [get(r, "фамилия"), get(r, "имя"),
                 get(r, "отчество", default=None)]
    db.execute("INSERT INTO users (last_name, first_name,"
               " middle_name, login, role_id)"
               " SELECT ?, ?, ?, ?, role_id FROM roles"
               " WHERE role_name = ?",
               (parts[0], parts[1], parts[2], get(r, "логин"), role))

for r in excel("Stock_Items"):
    model = get(r, "артикул", "наименование", "модель", "товар")
    db.execute("INSERT INTO stock_items (product_id, size_id,"
               " quantity_available) SELECT product_id, size_id, ?"
               " FROM products, sizes WHERE " + PRODUCT +
               " AND size_value = ?",
               (get(r, "количество"), model, model, get(r, "размер")))

for r in excel("Orders"):
    number = get(r, "номер")
    client = get(r, "логин", "клиент", "фио")
    db.execute("INSERT OR IGNORE INTO orders (order_id, order_date,"
               " user_id) SELECT ?, ?, user_id FROM users"
               " WHERE " + USER,
               (number, str(get(r, "дата"))[:10], client, client))
    model = get(r, "артикул", "наименование", "модель", "товар")
    # Нет цены в заказе -> берём цену товара из каталога
    db.execute("INSERT INTO order_items (order_id, product_id,"
               " size_id, quantity, price)"
               " SELECT ?, product_id, size_id, ?, COALESCE(?, price)"
               " FROM products, sizes WHERE " + PRODUCT +
               " AND size_value = ?",
               (number, get(r, "количество"),
                get(r, "цена", default=None), model, model,
                get(r, "размер")))

db.commit()
for table in ("products", "sizes", "stock_items", "users", "orders",
              "order_items"):
    count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count} строк")
print("База готова")
