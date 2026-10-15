import os

import pandas as pd
from PIL import Image

# Тестовые данные, если своих нет: те же файлы и колонки, что в Прил_2
os.makedirs("demo/images", exist_ok=True)
products = [
    ["A1", "Женская обувь", "Туфли", "Туфли лодочки", "Россия",
     "Классика", "Кожа", 4990, "1.jpg"],
    ["A2", "Мужская обувь", "Ботинки", "Ботинки зимние", "Италия",
     "Тёплые", "Нубук", 8990, "2.jpg"],
    ["A3", "Женская обувь", "Кроссовки", "Кроссовки беговые", "Китай",
     "Лёгкие", "Текстиль", 3500, ""],
]
pd.DataFrame(products, columns=[
    "Артикул", "Категория", "Подкатегория", "Наименование",
    "Производство", "Описание", "Состав", "Цена", "Фото",
]).to_excel("demo/Products_import.xlsx", index=False)
pd.DataFrame({"Размер": [36, 38, 42]}).to_excel(
    "demo/Sizes_import.xlsx", index=False)
pd.DataFrame({"Артикул": ["A1", "A2", "A3"], "Размер": [36, 42, 38],
              "Количество": [2, 10, 5]}).to_excel(
    "demo/Stock_Items_import.xlsx", index=False)
pd.DataFrame({"Логин": ["admin"], "ФИО": ["Иванов Иван Иванович"],
              "Роль": ["Администратор"]}).to_excel(
    "demo/Users_import.xlsx", index=False)
pd.DataFrame({"Номер заказа": [1], "Дата заказа": ["2026-10-01"],
              "Логин": ["admin"], "Артикул": ["A1"], "Размер": [36],
              "Количество": [1], "Цена": [4990]}).to_excel(
    "demo/Orders_import.xlsx", index=False)
# Цветные квадраты вместо фото; у третьего товара фото нет -> заглушка
Image.new("RGB", (300, 300), "#E8A0A0").save("demo/images/1.jpg")
Image.new("RGB", (300, 300), "#A0C8E8").save("demo/images/2.jpg")
Image.new("RGB", (300, 300), "#CCCCCC").save("demo/picture.png")
print("Тестовые данные созданы в папке demo")
