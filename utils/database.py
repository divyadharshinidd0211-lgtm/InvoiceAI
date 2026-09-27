import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "invoices.db"


def get_connection():
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            customer TEXT NOT NULL,
            email TEXT,
            subtotal REAL NOT NULL,
            gst_rate REAL NOT NULL,
            gst_amount REAL NOT NULL,
            total REAL NOT NULL,
            notes TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            service TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            price_found INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (invoice_id)
                REFERENCES invoices(id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()


def get_next_invoice_number():
    connection = get_connection()

    row = connection.execute(
        "SELECT COALESCE(MAX(id), 0) + 1 AS next_number FROM invoices"
    ).fetchone()

    connection.close()

    return f"INV-{row['next_number']:04d}"


def save_invoice(
    invoice_number,
    customer,
    email,
    invoice_items,
    subtotal,
    gst_rate,
    gst_amount,
    total,
    notes,
    status="Approved"
):
    connection = get_connection()

    try:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor = connection.execute(
            """
            INSERT INTO invoices (
                invoice_number,
                customer,
                email,
                subtotal,
                gst_rate,
                gst_amount,
                total,
                notes,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invoice_number,
                customer,
                email,
                subtotal,
                gst_rate,
                gst_amount,
                total,
                notes,
                status,
                created_at
            )
        )

        invoice_id = cursor.lastrowid

        for item in invoice_items:
            connection.execute(
                """
                INSERT INTO invoice_items (
                    invoice_id,
                    service,
                    quantity,
                    unit_price,
                    price_found
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    invoice_id,
                    item["service"],
                    int(item["quantity"]),
                    float(item["unit_price"]),
                    1 if item.get("price_found", True) else 0
                )
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_all_invoices():
    connection = get_connection()

    invoice_rows = connection.execute(
        """
        SELECT *
        FROM invoices
        ORDER BY id ASC
        """
    ).fetchall()

    invoices = []

    for invoice in invoice_rows:
        item_rows = connection.execute(
            """
            SELECT service, quantity, unit_price, price_found
            FROM invoice_items
            WHERE invoice_id = ?
            ORDER BY id ASC
            """,
            (invoice["id"],)
        ).fetchall()

        items = []

        for item in item_rows:
            items.append({
                "service": item["service"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "price_found": bool(item["price_found"])
            })

        invoices.append({
            "invoice_number": invoice["invoice_number"],
            "customer": invoice["customer"],
            "email": invoice["email"] or "",
            "items": items,
            "subtotal": invoice["subtotal"],
            "gst_rate": invoice["gst_rate"],
            "gst_amount": invoice["gst_amount"],
            "total": invoice["total"],
            "notes": invoice["notes"] or "",
            "status": invoice["status"],
            "created_at": invoice["created_at"]
        })

    connection.close()

    return invoices
