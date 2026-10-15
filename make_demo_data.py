"""Демо-замена архива Прил_2: 5 Excel-таблиц и картинки в папке Прил_2/.

На экзамене этот скрипт не нужен — там Прил_2 дают готовым. Данные выдуманы,
имена файлов и колонок — как ждёт db.py.
"""
import os

import pandas as pd
from PIL import Image, ImageDraw

OUT = "Прил_2"

products = pd.DataFrame([
    # Артикул, Наименование, Категория, Подкатегория, Производство, Цена, Фото
    ("A112T4", "Ботинки", "Женская обувь", "Ботинки", "Kari", 4990, "1.jpg"),
    ("F635R4", "Ботинки", "Женская обувь", "Ботинки", "Marco Tozzi", 3244, "2.jpg"),
    ("H782T5", "Туфли", "Мужская обувь", "Туфли", "Kari", 4499, "3.jpg"),
    ("G783F5", "Ботинки", "Мужская обувь", "Ботинки", "Рос", 5900, "4.jpg"),
    ("J384T6", "Ботинки", "Мужская обувь", "Ботинки", "Rieker", 3800, "5.jpg"),
    ("D572U8", "Кроссовки", "Мужская обувь", "Кроссовки", "Рос", 4100, ""),
    ("F572H7", "Туфли", "Женская обувь", "Туфли", "Marco Tozzi", 2700, "7.jpg"),
], columns=["Артикул", "Наименование", "Категория", "Подкатегория",
            "Производство", "Цена", "Фото"])
products["Описание"] = "Демо-описание товара " + products["Артикул"]
products["Состав"] = ["Натуральная кожа", "Искусственная кожа", "Замша",
                      "Натуральная кожа", "Нубук", "Текстиль", "Лак"]

sizes = pd.DataFrame({"Размер": list(range(36, 46))})

users = pd.DataFrame([
    ("Никифорова Весения Николаевна", "admin1", "Администратор"),
    ("Сазонов Руслан Германович", "manager1", "Менеджер"),
    ("Одинцов Серафим Артёмович", "client1", "Авторизированный клиент"),
    ("Степанов Михаил", "client2", "Авторизированный клиент"),  # без отчества
], columns=["ФИО", "Логин", "Роль"])

stock = pd.DataFrame([
    (a, s, q) for i, a in enumerate(products["Артикул"])
    for s, q in [(38, i + 1), (40, 2 * i), (42, 3)]
], columns=["Артикул", "Размер", "Количество"])

orders = pd.DataFrame([
    (1, pd.Timestamp("2026-02-27"), "client1", "A112T4", 38, 2, 4990),
    (1, pd.Timestamp("2026-02-27"), "client1", "F635R4", 40, 1, 3244),
    (2, pd.Timestamp("2026-03-05"), "client2", "H782T5", 42, 1, 4499),
], columns=["Номер заказа", "Дата заказа", "Логин", "Артикул", "Размер",
            "Количество", "Цена"])


def image(name, text, color, size=(300, 300)):
    img = Image.new("RGB", size, color)
    ImageDraw.Draw(img).text((20, size[1] // 2), text, fill="black")
    img.save(os.path.join(OUT, "images", name))


os.makedirs(os.path.join(OUT, "images"), exist_ok=True)
for name, df in [("Products", products), ("Sizes", sizes), ("Users", users),
                 ("Stock_Items", stock), ("Orders", orders)]:
    df.to_excel(os.path.join(OUT, f"{name}_import.xlsx"), index=False)

palette = ["#E8C39E", "#B5D99C", "#9CC3E4", "#E4A1A1", "#D6B4E8", "#F2E394"]
for i, (photo, article) in enumerate(zip(products["Фото"], products["Артикул"])):
    if photo:
        image(photo, article, palette[i % len(palette)])
image("picture.png", "no photo", "#DDDDDD")
image("logo.png", "CHUDO OBUV", "#7FFF00", (200, 80))
print("Демо Прил_2 готов:", os.path.abspath(OUT))
