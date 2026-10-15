# Чудо Обувь — демо (ДЭ 09.02.07)

База (SQLite) и каталог товаров (tkinter) по шпаргалке ДЭ.

- `db.py` — модуль 1: читает `*_import.xlsx` из Прил_2 и создаёт `chudo.db`.
- `main.py` — модуль 2: окно с карточками товаров из `chudo.db`.
- `make_demo_data.py` — выдуманная замена архива Прил_2 (Excel + картинки),
  чтобы запустить без экзаменационных файлов.

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python make_demo_data.py   # или распакуй настоящий Прил_2 сюда
.venv/bin/python db.py               # База готова, товаров: 7
.venv/bin/python main.py
```
