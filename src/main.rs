use axum::{
    Json, Router,
    extract::{Path, State},
    http::StatusCode,
    response::Html,
    routing::{get, put},
};
use rusqlite::{Connection, params};
use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};

// Общее состояние: одно соединение с БД под мьютексом
type Db = Arc<Mutex<Connection>>;

#[derive(Serialize)]
struct Product {
    id: i64,
    name: String,
    price: f64,
    stock: i64,
}

#[derive(Deserialize)]
struct NewProduct {
    name: String,
    price: f64,
    stock: i64,
}

#[derive(Deserialize)]
struct NewOrder {
    customer: String,
    items: Vec<OrderItem>,
}

#[derive(Deserialize)]
struct OrderItem {
    product_id: i64,
    qty: i64,
}

#[derive(Serialize)]
struct Order {
    id: i64,
    customer: String,
    total: f64,
    created: String,
}

// ---------- ТОВАРЫ ----------

async fn list_products(State(db): State<Db>) -> Json<Vec<Product>> {
    let conn = db.lock().unwrap();
    let mut stmt = conn
        .prepare("SELECT id, name, price, stock FROM products ORDER BY id")
        .unwrap();
    let rows = stmt
        .query_map([], |r| {
            Ok(Product {
                id: r.get(0)?,
                name: r.get(1)?,
                price: r.get(2)?,
                stock: r.get(3)?,
            })
        })
        .unwrap()
        .filter_map(Result::ok)
        .collect();
    Json(rows)
}

async fn add_product(
    State(db): State<Db>,
    Json(p): Json<NewProduct>,
) -> Result<Json<Product>, (StatusCode, String)> {
    if p.name.trim().is_empty() || p.price < 0.0 || p.stock < 0 {
        return Err((StatusCode::BAD_REQUEST, "Неверные данные".into()));
    }
    let conn = db.lock().unwrap();
    conn.execute(
        "INSERT INTO products (name, price, stock) VALUES (?1, ?2, ?3)",
        params![p.name, p.price, p.stock],
    )
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    Ok(Json(Product {
        id: conn.last_insert_rowid(),
        name: p.name,
        price: p.price,
        stock: p.stock,
    }))
}

async fn update_product(
    State(db): State<Db>,
    Path(id): Path<i64>,
    Json(p): Json<NewProduct>,
) -> Result<Json<Product>, (StatusCode, String)> {
    if p.name.trim().is_empty() || p.price < 0.0 || p.stock < 0 {
        return Err((StatusCode::BAD_REQUEST, "Неверные данные".into()));
    }
    let conn = db.lock().unwrap();
    let n = conn
        .execute(
            "UPDATE products SET name = ?1, price = ?2, stock = ?3 WHERE id = ?4",
            params![p.name, p.price, p.stock, id],
        )
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    if n == 0 {
        return Err((StatusCode::NOT_FOUND, "Товар не найден".into()));
    }
    Ok(Json(Product {
        id,
        name: p.name,
        price: p.price,
        stock: p.stock,
    }))
}

async fn delete_product(State(db): State<Db>, Path(id): Path<i64>) -> StatusCode {
    let conn = db.lock().unwrap();
    match conn.execute("DELETE FROM products WHERE id = ?1", [id]) {
        Ok(0) => StatusCode::NOT_FOUND,
        Ok(_) => StatusCode::NO_CONTENT,
        Err(_) => StatusCode::CONFLICT, // товар есть в заказах (FOREIGN KEY)
    }
}

// ---------- ЗАКАЗЫ ----------

async fn create_order(
    State(db): State<Db>,
    Json(o): Json<NewOrder>,
) -> Result<Json<Order>, (StatusCode, String)> {
    if o.customer.trim().is_empty() || o.items.is_empty() {
        return Err((StatusCode::BAD_REQUEST, "Пустой заказ".into()));
    }
    let bad = |e: rusqlite::Error| (StatusCode::BAD_REQUEST, e.to_string());

    let mut conn = db.lock().unwrap();
    let tx = conn.transaction().map_err(bad)?; // всё или ничего
    let mut total = 0.0;

    for it in &o.items {
        let (price, stock): (f64, i64) = tx
            .query_row(
                "SELECT price, stock FROM products WHERE id = ?1",
                [it.product_id],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .map_err(|_| {
                (
                    StatusCode::BAD_REQUEST,
                    format!("Нет товара {}", it.product_id),
                )
            })?;
        if it.qty <= 0 || it.qty > stock {
            return Err((
                StatusCode::BAD_REQUEST,
                format!("Мало на складе: товар {}", it.product_id),
            ));
        }
        tx.execute(
            "UPDATE products SET stock = stock - ?1 WHERE id = ?2",
            params![it.qty, it.product_id],
        )
        .map_err(bad)?;
        total += price * it.qty as f64;
    }

    tx.execute(
        "INSERT INTO orders (customer, total) VALUES (?1, ?2)",
        params![o.customer, total],
    )
    .map_err(bad)?;
    let id = tx.last_insert_rowid();
    for it in &o.items {
        tx.execute(
            "INSERT INTO order_items (order_id, product_id, qty) VALUES (?1, ?2, ?3)",
            params![id, it.product_id, it.qty],
        )
        .map_err(bad)?;
    }
    let created: String = tx
        .query_row("SELECT created FROM orders WHERE id = ?1", [id], |r| {
            r.get(0)
        })
        .map_err(bad)?;
    tx.commit().map_err(bad)?;

    Ok(Json(Order {
        id,
        customer: o.customer,
        total,
        created,
    }))
}

async fn list_orders(State(db): State<Db>) -> Json<Vec<Order>> {
    let conn = db.lock().unwrap();
    let mut stmt = conn
        .prepare("SELECT id, customer, total, created FROM orders ORDER BY id DESC")
        .unwrap();
    let rows = stmt
        .query_map([], |r| {
            Ok(Order {
                id: r.get(0)?,
                customer: r.get(1)?,
                total: r.get(2)?,
                created: r.get(3)?,
            })
        })
        .unwrap()
        .filter_map(Result::ok)
        .collect();
    Json(rows)
}

// ---------- ФРОНТЕНД ----------

async fn index() -> Html<&'static str> {
    Html(include_str!("../static/index.html")) // HTML вшит в бинарник
}

// ---------- БД ----------

fn init_db() -> Connection {
    let conn = Connection::open("shop.db").expect("не открыть shop.db");
    conn.execute_batch(
        "PRAGMA foreign_keys = ON;
         CREATE TABLE IF NOT EXISTS products (
             id    INTEGER PRIMARY KEY AUTOINCREMENT,
             name  TEXT    NOT NULL,
             price REAL    NOT NULL CHECK (price >= 0),
             stock INTEGER NOT NULL CHECK (stock >= 0)
         );
         CREATE TABLE IF NOT EXISTS orders (
             id       INTEGER PRIMARY KEY AUTOINCREMENT,
             customer TEXT NOT NULL,
             total    REAL NOT NULL,
             created  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
         );
         CREATE TABLE IF NOT EXISTS order_items (
             order_id   INTEGER NOT NULL REFERENCES orders(id),
             product_id INTEGER NOT NULL REFERENCES products(id),
             qty        INTEGER NOT NULL
         );",
    )
    .unwrap();

    // Тестовые данные, если таблица пустая
    let n: i64 = conn
        .query_row("SELECT COUNT(*) FROM products", [], |r| r.get(0))
        .unwrap();
    if n == 0 {
        conn.execute_batch(
            "INSERT INTO products (name, price, stock) VALUES
             ('Кроссовки беговые', 4990, 10),
             ('Ботинки зимние',    7490, 5),
             ('Туфли классические',5990, 8),
             ('Сандалии',          1990, 20);",
        )
        .unwrap();
    }
    conn
}

#[tokio::main]
async fn main() {
    let db: Db = Arc::new(Mutex::new(init_db()));

    let app = Router::new()
        .route("/", get(index))
        .route("/api/products", get(list_products).post(add_product))
        .route(
            "/api/products/{id}",
            put(update_product).delete(delete_product),
        )
        .route("/api/orders", get(list_orders).post(create_order))
        .with_state(db);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    println!("Магазин: http://localhost:3000");
    axum::serve(listener, app).await.unwrap();
}
