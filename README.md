# GroupCart

**A multi-vendor shopping platform built with Flask, MySQL and JavaScript.**

GroupCart brings product discovery, shopping carts and order tracking into one place. Customers can browse products by seller or tag, purchase from several sellers in one checkout, and track each seller’s fulfillment separately. Sellers manage their own catalog and incoming orders.

## What you can do

- Browse a product catalog, filter by seller, or select a tag to search immediately.
- Add products to a cart and check out across multiple sellers.
- View one checkout as a group, with separate seller orders and fulfillment statuses.
- Cancel eligible orders, remove eligible items before shipment, and confirm receipt.
- Sign in as a seller to publish products, view seller-specific search results and manage fulfillment.
- Register customer accounts and manage the seller directory.

## How checkout works

The backend validates quantities and prices, retrieves current product prices from MySQL and splits cart items by seller. All resulting orders are written in one database transaction: a failure rolls back the entire checkout. A shared checkout identifier keeps the seller orders together in the customer view. Removing an item recalculates the order total from its remaining line items.

The interface also groups older orders from the same customer created in the same second. These older records have no explicit checkout identifier, so this display rule may combine separate historical purchases made within one second.

## Run locally

Requirements: Python 3.10+, MySQL 8.0, and a web browser. Node.js is optional and only needed for frontend tests.

1. Create a virtual environment and install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. Import `database/seed.sql` using MySQL Workbench: open the script and execute it with an account allowed to create databases, tables and triggers. It creates **ecommerceplatform** and loads sample customers, sellers, products, tags and orders. On a fresh MySQL installation, this database does not need to exist first.

   **Import once into a fresh instance.** The original script includes `CREATE DATABASE`, `DROP TABLE` and sample records. Do not rerun it against a database containing data you need to keep. See [database setup](docs/DATABASE.md).

3. Copy the connection template and edit it with your own MySQL credentials:

   ```powershell
   Copy-Item app/db_config.example.json app/db_config.json
   ```

   Use host `127.0.0.1`, your MySQL port (normally `3306`), database `ecommerceplatform`, and a database user/password you created. The example username is a placeholder; importing the SQL does not create it. Do not commit `app/db_config.json`.

4. Start the platform:

   ```powershell
   .\.venv\Scripts\python.exe app/main.py
   ```

5. Open **http://localhost:5000**. Use this hostname consistently because the frontend calls `localhost:5000` and stores cart/account state in browser local storage. Product images are served by the same Flask process. No separate frontend server is required.

On macOS/Linux, use `.venv/bin/python` instead of `.\.venv\Scripts\python.exe` and `cp` instead of `Copy-Item`.

### Sample accounts

| Role | Account ID | Password |
| --- | --- | --- |
| Customer | C001 | C001 |
| Customer | C002 | C002 |
| Seller | V001 | V001 |
| Seller | V002 | V002 |

IDs are case-sensitive in the interface. These are website accounts from the sample data, not MySQL connection credentials.

## Project layout

```text
app/main.py                 Flask API and frontend serving
app/webpage/                HTML, shared JavaScript and styles
app/static/images/          Product and interface images
app/db_config.example.json  Portable connection template
database/seed.sql           Original MySQL schema and sample data
tests/                      Backend and frontend regression checks
docs/                       Database setup and implementation notes
```

## Validation

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_fixes.py
node tests/test_cart.cjs
node tests/test_order_groups.cjs
node tests/test_tag_search.cjs
node tests/test_catalog.cjs
```

The backend unit tests use an in-memory SQLite adapter for transaction-failure scenarios. Additional MySQL integration checks cover actual triggers and multi-seller checkout; see [testing](docs/TESTING.md).

## Current scope

This version supports local evaluation of the shopping and seller workflows. Payments, stock reservation, shipping integrations and refunds are not implemented. Account passwords in the sample application are stored in plaintext, and API identity currently relies on client-supplied account IDs rather than authenticated server sessions. Seller-directory creation is exposed without an administrator role. These are explicit areas for further development before deployment with real users or money.

GroupCart started as a course project and has continued to evolve through functionality and interface improvements. See [project background and assets](docs/CREDITS.md) for context and notes on demonstration images.
