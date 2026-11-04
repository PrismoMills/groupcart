"""Integration checks in a new disposable MySQL database; never uses the application DB."""
import re
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
import pymysql
import test_fixes

m = test_fixes.app_module
import json
import os
root = Path(__file__).resolve().parents[1]
config = json.loads(Path(os.environ['MYSQL_TEST_ADMIN_CONFIG']).read_text(encoding='utf-8'))
config.update(charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor, connect_timeout=5)

database = 'groupcart_fix_test_' + uuid4().hex
admin = pymysql.connect(**config)
created = False

def check(value, message):
    if not value: raise AssertionError(message)

try:
    with admin.cursor() as cursor:
        cursor.execute('CREATE DATABASE `' + database + '` CHARACTER SET utf8mb4')
    created = True
    connection = pymysql.connect(database=database, **config)
    dump = (root / 'database' / 'seed.sql').read_text(encoding='utf-8-sig')
    with connection.cursor() as cursor:
        for name in ('customer', 'vendor', 'product', 'tag', 'producttag', 'transaction', 'transactionitem'):
            ddl = re.search(r'CREATE TABLE `' + name + r'` \([\s\S]*?\) ENGINE=[^;]+;', dump).group()
            cursor.execute(ddl)
        for match in re.finditer(r'TRIGGER `([^`]+)` (AFTER (?:INSERT|UPDATE|DELETE)) ON `transactionitem` FOR EACH ROW BEGIN([\s\S]*?)END', dump):
            cursor.execute('CREATE TRIGGER `' + match[1] + '` ' + match[2] + ' ON transactionitem FOR EACH ROW BEGIN' + match[3] + 'END')
        cursor.execute("INSERT INTO customer (CustomerID, ContactNumber, ShippingDetails, password) VALUES ('C1', '1', 'Test', 'test')")
        cursor.execute("INSERT INTO vendor (VendorID, BusinessName, CustomerFeedbackScore, GeographicalPresence,password) VALUES ('V1','One',5,'Test','test'), ('V2','Two',5,'Test','test')")
        cursor.execute("INSERT INTO product (ProductID,VendorID,Name,ListedPrice) VALUES ('A','V1','Same',10),('B','V1','Same',20),('C','V2','Other',7)")
        cursor.execute("INSERT INTO tag (TagName) VALUES ('Test')")
    connection.commit()
    m.get_db_connection = lambda: pymysql.connect(database=database, **config)
    client = m.app.test_client()
    def post(path, data): return client.post('/api/' + path, json=data)
    def query(sql, args=()):
        connection.commit()
        with connection.cursor() as cursor:
            cursor.execute(sql, args)
            return cursor.fetchall()
    response = post('cart_confirm_order', dict(customerID='C1',userType='customer',totalAmount=0.01,
        items=[dict(ProductID='A',Quantity=3),dict(ProductID='B',Quantity=1),dict(ProductID='C',Quantity=2)]))
    check(response.status_code == 200, response.json)
    orders = {item['vendorID']:item['transactionID'] for item in response.json['orders']}
    check(len(orders) == 2, 'Cross-vendor order was not split')
    check(sorted(row['TotalAmount'] for row in query('SELECT TotalAmount FROM transaction')) == [Decimal('14'),Decimal('50')], 'Incorrect server prices')
    response = post('remove_items', dict(transactionID=orders['V1'],ProductID='A',userType='customer',customerID='C1'))
    check(response.status_code == 200, response.json)
    check(query('SELECT TotalAmount FROM transaction WHERE TransactionID=%s',(orders['V1'],))[0]['TotalAmount']==20, 'Trigger and application total disagree')
    response = post('update_order_status', dict(transactionID=orders['V1'], userType='vendor', newStatus='SHIPPED'))
    check(response.status_code == 200, response.json)
    check(query('SELECT status FROM transaction WHERE TransactionID=%s',(orders['V2'],))[0]['status']=='PENDING_SHIPMENT', 'Other vendor order changed')
    # Force an item insert error after the order header has been inserted.
    with connection.cursor() as cursor:
        cursor.execute("CREATE TRIGGER fail_item BEFORE INSERT ON transactionitem FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='test failure'")
    baseline = len(query('SELECT TransactionID FROM transaction'))
    response = post('confirm_order', dict(customerID='C1',userType='customer',ProductID='A',Quantity=1))
    check(response.status_code == 500, 'Expected injected item failure')
    check(len(query('SELECT TransactionID FROM transaction'))==baseline, 'Order header survived rollback')
    with connection.cursor() as cursor:
        cursor.execute('DROP TRIGGER fail_item')
        cursor.execute("CREATE TRIGGER fail_tag BEFORE INSERT ON producttag FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='test failure'")
    response = post('insert_product', dict(userType='vendor',VendorID='V1',Name='New',ListedPrice='12.34',tag1='Test'))
    check(response.status_code == 500, 'Expected injected tag failure')
    check(len(query('SELECT ProductID FROM product'))==3, 'Product survived tag rollback')
    with connection.cursor() as cursor: cursor.execute('DROP TRIGGER fail_tag')
    response = post('remove_items', dict(transactionID=orders['V2'],ProductID='C',userType='customer',customerID='C1'))
    check(response.status_code == 200, response.json)
    row = query('SELECT TotalAmount,status FROM transaction WHERE TransactionID=%s',(orders['V2'],))[0]
    check(row['TotalAmount']==0 and row['status']=='CANCELLED','Empty order not normalized')
    connection.close()
    print('PASS: MySQL schema/triggers, vendor isolation, server totals, removal, empty order, and real rollback checks')
finally:
    if created:
        with admin.cursor() as cursor: cursor.execute('DROP DATABASE `' + database + '`')
        print('Disposable test database removed')
    admin.close()
