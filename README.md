<div align="center">

# GroupCart

### One cart. Multiple sellers. A checkout that keeps everything together.

A local shopping demo where customers shop across stores<br>and each seller stays in control of their own orders.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web%20app-000000?logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8-4479A1?logo=mysql&logoColor=white)

[Explore the experience](#a-shopping-trip-with-groupcart) · [Run locally](#try-it-locally) · [Project notes](#under-the-hood) · [简体中文](README.zh-CN.md)

</div>

---

## A shopping trip with GroupCart

Find something you like, add it to your cart, and keep browsing another seller. When you check out, GroupCart turns that cart into a shared purchase with separate seller orders—so one store can ship while another is still preparing.

| For shoppers | For sellers |
| :--- | :--- |
| Browse products by seller or tag, with immediate search | Publish products and search your own catalog |
| Buy from several stores in one checkout | See and fulfill your own orders |
| Track seller orders together under one purchase | Update fulfillment without changing another seller's orders |
| Cancel eligible orders, remove items before shipment, and confirm receipt | Keep your storefront and order work in one place |

The app also includes customer registration and a seller directory with management tools.

### One purchase, separate deliveries

```text
Your cart
├── Store A · two products ──→ Seller order A · Preparing
└── Store B · one product  ──→ Seller order B · Shipped
                              └── Same checkout group
```

Checkout reads current prices from MySQL, validates quantities, and creates every seller order in a single transaction. If one part fails, the whole checkout rolls back. Removing an eligible item also recalculates its order total.

## Try it locally

You'll need **Python 3.10+**, **MySQL 8**, and a browser. Node.js is optional for JavaScript checks.

### 1. Install the Python dependencies

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Import the demo database

Open `database/seed.sql` in MySQL Workbench and run it against a fresh local instance. It creates the `ecommerceplatform` database and fills it with sample products, customers, sellers, tags, and orders.

> The seed script drops and recreates tables. Use it for a fresh demo database; rerunning it will replace existing data. See [database setup](docs/DATABASE.md).

### 3. Connect the app to MySQL

```powershell
Copy-Item app/db_config.example.json app/db_config.json
```

Edit `app/db_config.json` with your own MySQL username and password. Keep `database` set to `ecommerceplatform`. The example username is a placeholder; the seed script does not create a MySQL account. Your local configuration is ignored by Git.

### 4. Start shopping

```powershell
.\.venv\Scripts\python.exe app/main.py
```

Open **[http://localhost:5000](http://localhost:5000)**. Use the same hostname throughout; the frontend uses `localhost` and browser-local state. Flask serves the interface and images together.

On macOS/Linux, use `.venv/bin/python` and `cp` instead of their Windows equivalents.

| Demo role | Account | Password |
| :--- | :--- | :--- |
| Customer | `C001` or `C002` | Same as the account |
| Seller | `V001` or `V002` | Same as the account |

Account IDs are case-sensitive. These are website demo accounts, separate from your MySQL credentials.

## Under the hood

<details>
<summary><strong>Repository map</strong></summary>

```text
app/
├── main.py                 Flask routes and checkout logic
├── webpage/                HTML, CSS, and JavaScript
├── static/images/          Demo product images
└── db_config.example.json  Local database configuration template
database/seed.sql           Demo schema and data
tests/                      Backend and frontend checks
docs/                       Database, testing, and project notes
```

</details>

<details>
<summary><strong>Run the checks</strong></summary>

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_fixes.py
node tests/test_cart.cjs
node tests/test_order_groups.cjs
node tests/test_tag_search.cjs
node tests/test_catalog.cjs
```

Backend regression tests use an in-memory SQLite adapter, including failure scenarios. See [testing notes](docs/TESTING.md) for checks against a real MySQL instance.

</details>

<details>
<summary><strong>How older orders are grouped</strong></summary>

New purchases use an explicit checkout ID. Historical orders without one are grouped by customer and timestamp to the second. Two separate historical purchases made in the same second can therefore appear in one group.

</details>

## Before using real accounts

GroupCart is a local evaluation project. Payments, stock reservation, shipping integrations, and refunds are not implemented. Demo passwords are stored as plaintext, API identity comes from client-supplied account IDs rather than authenticated server sessions, and seller-directory creation has no administrator role. Authentication and authorization need further work before this app handles real users or money.

Originally built as a course project and refined with transactional checkout, grouped orders, and interface improvements. See [project background and asset notes](docs/CREDITS.md).
