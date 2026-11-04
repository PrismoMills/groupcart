import importlib.util
import sqlite3
import unittest
from decimal import Decimal
from pathlib import Path

spec = importlib.util.spec_from_file_location('reviewed_app', Path(__file__).resolve().parents[1] / 'app' / 'main.py')
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)


class Cursor:
    def __init__(self, db):
        self.db = db
        self.cursor = db.raw.cursor()

    def execute(self, sql, args=()):
        if self.db.fail_on and self.db.fail_on in sql:
            raise RuntimeError('Injected database failure')
        if getattr(self.db, 'fail_product', None) and 'INSERT INTO transactionitem' in sql and args[1] == self.db.fail_product:
            raise RuntimeError('Injected second-vendor failure')
        sql = sql.replace('%s', '?').replace(' FOR UPDATE', '')
        self.cursor.execute(sql, tuple(str(v) if isinstance(v, Decimal) else v for v in args))
        return self.cursor.rowcount

    def fetchone(self):
        row = self.cursor.fetchone()
        return dict(row) if row else None

    @property
    def rowcount(self):
        return self.cursor.rowcount


class Database:
    def __init__(self):
        self.raw = sqlite3.connect(':memory:')
        self.raw.row_factory = sqlite3.Row
        self.fail_on = None
        self.commits = 0
        self.rollbacks = 0
        self.raw.executescript('''
            CREATE TABLE customer (CustomerID TEXT PRIMARY KEY);
            CREATE TABLE vendor (VendorID TEXT PRIMARY KEY);
            CREATE TABLE product (ProductID TEXT PRIMARY KEY, VendorID TEXT, Name TEXT, ListedPrice NUMERIC);
            CREATE TABLE tag (TagID INTEGER PRIMARY KEY, TagName TEXT);
            CREATE TABLE producttag (ProductID TEXT, TagID INTEGER);
            CREATE TABLE "transaction" (TransactionID TEXT PRIMARY KEY, CustomerID TEXT, TransactionDate TEXT, TotalAmount NUMERIC, status TEXT);
            CREATE TABLE transactionitem (TransactionID TEXT, ProductID TEXT, Quantity INTEGER, PriceAtPurchase NUMERIC);
            INSERT INTO customer VALUES ('C1');
            INSERT INTO vendor VALUES ('V1'), ('V2');
            INSERT INTO product VALUES ('A', 'V1', 'Same name', 10), ('B', 'V1', 'Same name', 20), ('C', 'V2', 'Other', 7);
            INSERT INTO tag VALUES (1, 'Test');
        ''')

    def begin(self): self.raw.execute('BEGIN')
    def cursor(self): return Cursor(self)
    def commit(self):
        self.commits += 1
        self.raw.commit()
    def rollback(self):
        self.rollbacks += 1
        self.raw.rollback()
    def close(self): pass


# SQLite reserves TRANSACTION; adapt just that table name in this test double.
original_execute = Cursor.execute
def execute(self, sql, args=()):
    import re
    sql = re.sub(r'\b(FROM|INTO|UPDATE) transaction\b', r'\1 "transaction"', sql)
    return original_execute(self, sql, args)
Cursor.execute = execute


class FixTests(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        app_module.get_db_connection = lambda: self.db
        app_module.app.config['TESTING'] = True
        self.client = app_module.app.test_client()

    def post(self, path, data):
        return self.client.post('/api/' + path, json=data)

    def checkout(self, items, **changes):
        data = dict(customerID='C1', userType='customer', items=items, totalAmount=0.01)
        data.update(changes)
        return self.post('cart_confirm_order', data)

    def count(self, table):
        return self.db.raw.execute('SELECT COUNT(*) FROM "' + table + '"').fetchone()[0]

    def test_split_vendors_and_database_prices(self):
        result = self.checkout([dict(ProductID='A', Quantity=3), dict(ProductID='C', Quantity=2)])
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.json['orders']), 2)
        totals = sorted(row[0] for row in self.db.raw.execute('SELECT TotalAmount FROM "transaction"'))
        self.assertEqual(totals, [14, 30])
        self.assertEqual(self.db.commits, 1)
        orders = result.json['orders']
        self.post('cancel_order', dict(transactionID=orders[0]['transactionID'], userType='vendor'))
        states = dict(self.db.raw.execute('SELECT TransactionID, status FROM "transaction"'))
        self.assertEqual(states[orders[0]['transactionID']], 'CANCELLED')
        self.assertEqual(states[orders[1]['transactionID']], 'PENDING_SHIPMENT')

    def test_order_failure_rolls_back_all_vendor_orders(self):
        self.db.fail_product = 'C'
        result = self.checkout([dict(ProductID='A', Quantity=1), dict(ProductID='C', Quantity=1)])
        self.assertEqual(result.status_code, 500)
        self.assertEqual(self.count('transaction'), 0)
        self.assertEqual(self.count('transactionitem'), 0)
        self.assertEqual(self.db.rollbacks, 1)

    def test_bad_product_leaves_no_orders(self):
        self.assertEqual(self.checkout([dict(ProductID='missing', Quantity=1)]).status_code, 400)
        self.assertEqual(self.count('transaction'), 0)

    def test_quantities(self):
        for quantity in (0, -1, True, 1.5, '2', None, 2147483648):
            with self.subTest(quantity=quantity):
                self.assertEqual(self.checkout([dict(ProductID='A', Quantity=quantity)]).status_code, 400)

    def test_roles_and_malformed_json(self):
        for role in ('vendor', 'admin', None):
            self.assertEqual(self.checkout([dict(ProductID='A', Quantity=1)], userType=role).status_code, 400)
        for path in ('cart_confirm_order', 'confirm_order', 'insert_product', 'remove_items'):
            self.assertEqual(self.client.post('/api/' + path, json=[]).status_code, 400)
        self.assertEqual(self.post('cancel_order', dict(transactionID='x', userType='admin')).status_code, 400)

    def test_single_order_ignores_client_total(self):
        result = self.post('confirm_order', dict(customerID='C1', userType='customer', ProductID='A', Quantity=2, TotalAmount=-99))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.db.raw.execute('SELECT TotalAmount FROM "transaction"').fetchone()[0], 20)

    def test_duplicate_products_merge(self):
        self.assertEqual(self.checkout([dict(ProductID='A', Quantity=1), dict(ProductID='A', Quantity=2)]).status_code, 200)
        self.assertEqual(self.count('transactionitem'), 1)
        self.assertEqual(self.db.raw.execute('SELECT Quantity FROM transactionitem').fetchone()[0], 3)

    def test_total_overflow_rolls_back(self):
        self.assertEqual(self.checkout([dict(ProductID='A', Quantity=10000000)]).status_code, 400)
        self.assertEqual(self.count('transaction'), 0)

    def publish(self, **changes):
        data = dict(userType='vendor', VendorID='V1', Name='New', ListedPrice='12.34', tag1='Test')
        data.update(changes)
        return self.post('insert_product', data)

    def test_product_and_tags_atomic(self):
        self.db.fail_on = 'INSERT INTO producttag'
        self.assertEqual(self.publish().status_code, 500)
        self.assertEqual(self.count('product'), 3)
        self.assertEqual(self.count('producttag'), 0)

    def test_publish_success_and_validation(self):
        self.assertEqual(self.publish(tag2='Test').status_code, 200)
        self.assertEqual(self.count('producttag'), 1)
        for price in ('0', '-1', 'NaN', 'Infinity', '1.001', '100000000', None, True):
            with self.subTest(price=price):
                self.assertEqual(self.publish(ListedPrice=price).status_code, 400)
        self.assertEqual(self.publish(userType='customer').status_code, 400)
        self.assertEqual(self.publish(VendorID='missing').status_code, 400)
        self.assertEqual(self.publish(tag1='missing').status_code, 400)

    def test_remove_uses_purchase_prices_and_quantities(self):
        result = self.checkout([dict(ProductID='A', Quantity=3), dict(ProductID='B', Quantity=1)])
        transaction_id = result.json['transactionID']
        self.db.raw.execute("UPDATE product SET ListedPrice=999 WHERE ProductID='A'")
        self.db.raw.commit()
        response = self.post('remove_items', dict(transactionID=transaction_id, ProductID='A', userType='customer', customerID='C1'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.db.raw.execute('SELECT TotalAmount FROM "transaction"').fetchone()[0], 20)
        self.assertEqual(self.count('transactionitem'), 1)
        response = self.post('remove_items', dict(transactionID=transaction_id, ProductID='B', userType='customer', customerID='C1'))
        self.assertEqual(response.status_code, 200)
        row = self.db.raw.execute('SELECT TotalAmount, status FROM "transaction"').fetchone()
        self.assertEqual(tuple(row), (0, 'CANCELLED'))

    def test_removal_rejects_status_role_and_owner(self):
        transaction_id = self.checkout([dict(ProductID='A', Quantity=1)]).json['transactionID']
        base = dict(transactionID=transaction_id, ProductID='A', userType='customer', customerID='C1')
        self.assertEqual(self.post('remove_items', {**base, 'customerID': 'other'}).status_code, 400)
        self.assertEqual(self.post('remove_items', {**base, 'userType': 'vendor', 'vendorID': 'V2'}).status_code, 403)
        self.db.raw.execute('UPDATE "transaction" SET status="COMPLETED"')
        self.db.raw.commit()
        self.assertEqual(self.post('remove_items', base).status_code, 400)
        self.assertEqual(self.count('transactionitem'), 1)

    def test_removal_failure_rolls_back(self):
        transaction_id = self.checkout([dict(ProductID='A', Quantity=2)]).json['transactionID']
        self.db.fail_on = 'UPDATE "transaction" SET TotalAmount'
        response = self.post('remove_items', dict(transactionID=transaction_id, ProductID='A', userType='customer', customerID='C1'))
        self.assertEqual(response.status_code, 500)
        self.assertEqual(self.count('transactionitem'), 1)


if __name__ == '__main__':
    unittest.main()
