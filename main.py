import glob
import os
import sqlite3
import tkinter as tk

from PIL import Image, ImageTk

FONT = ("Times New Roman", 12)
BIG_FONT = ("Times New Roman", 16)
BG = "#FFFFFF"  # цвета и шрифт — из руководства по стилю (Прил_3)

# Все файлы проекта по имени: так не важно, в какой подпапке картинка
files = {}
for path in glob.glob("**/*", recursive=True):
    files[os.path.basename(path)] = path


def picture(name, size):
    # Нет фото -> заглушка picture.png; нет и её -> серый квадрат
    path = files.get(name) or files.get("picture.png")
    if path:
        image = Image.open(path)
    else:
        image = Image.new("RGB", (size, size), "#CCCCCC")
    image.thumbnail((size, size))
    photo = ImageTk.PhotoImage(image)
    images.append(photo)  # без ссылки tkinter удалит картинку
    return photo


root = tk.Tk()
root.title("Чудо Обувь — Каталог товаров")
root.geometry("1000x700")
root.configure(bg=BG)
images = []

# Иконка окна: файл .ico или со словом «icon»/«иконка» в имени
icon = [n for n in files if n.lower().endswith(".ico")
        or "icon" in n.lower() or "иконк" in n.lower()]
if icon:
    root.iconphoto(True, picture(icon[0], 64))

# Логотип: любой файл, в имени которого есть «logo» или «лого»
logo = [n for n in files
        if "logo" in n.lower() or "лого" in n.lower()]
if logo:
    tk.Label(root, image=picture(logo[0], 60), bg=BG).pack(
        anchor="w", padx=10, pady=5)

conn = sqlite3.connect("chudo.db")
products = conn.execute("""
    SELECT p.manufacturer, p.product_name, p.category, p.composition,
           p.price, p.image_path, IFNULL(SUM(s.quantity_available), 0)
    FROM products p
    LEFT JOIN stock_items s ON s.product_id = p.product_id
    GROUP BY p.product_id""").fetchall()
conn.close()

# Прокрутка: Canvas + Scrollbar, карточки лежат во Frame на Canvas
canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
scrollbar = tk.Scrollbar(root, command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)
cards = tk.Frame(canvas, bg=BG)
canvas.create_window((0, 0), window=cards, anchor="nw")
cards.bind("<Configure>", lambda e: canvas.configure(
    scrollregion=canvas.bbox("all")))

for factory, name, category, sostav, price, photo, amount in products:
    card = tk.Frame(cards, bg=BG, bd=1, relief="solid")
    card.pack(fill="x", padx=10, pady=5)
    card.columnconfigure(1, minsize=600)
    tk.Label(card, image=picture(photo, 120), bg=BG).grid(
        row=0, column=0, rowspan=4, padx=10, pady=5)
    tk.Label(card, text=f"{factory} | {name}", font=FONT, bg=BG).grid(
        row=0, column=1, sticky="w")
    tk.Label(card, text=f"Категория: {category}", font=FONT,
             bg=BG).grid(row=1, column=1, sticky="w")
    tk.Label(card, text=f"Количество: {amount}", font=FONT,
             bg=BG).grid(row=2, column=1, sticky="w")
    tk.Label(card, text=f"Состав: {sostav}", font=FONT, bg=BG).grid(
        row=3, column=1, sticky="w")
    tk.Label(card, text=f"{price:.2f} ₽", font=BIG_FONT,
             bg=BG).grid(row=0, column=2, rowspan=4, padx=20)

root.mainloop()
