import json
import os
from pathlib import Path
import re
from uuid import uuid4
import pymysql
import test_fixes

m = test_fixes.app_module
config_path = Path(os.environ.get('MYSQL_TEST_ADMIN_CONFIG', Path(__file__).resolve().parents[1] / 'mysql-test' / 'admin.json'))
config = json.loads(config_path.read_text(encoding='utf-8'))
config.update(cursorclass=pymysql.cursors.DictCursor, charset='utf8mb4')
database = 'groupcart_api_test_' + uuid4().hex
admin = pymysql.connect(**config)
created = False

try:
    with admin.cursor() as cursor:
        cursor.execute('CREATE DATABASE `' + database + '`')
    created = True
    conn = pymysql.connect(database=database, **config)
    dump = (Path(__file__).resolve().parents[1] / 'database' / 'seed.sql').read_text(encoding='utf-8-sig')
    with conn.cursor() as cursor:
        for name in ('customer','vendor','product','tag','producttag','transaction','transactionitem'):
            cursor.execute(re.search(r'CREATE TABLE `' + name + r'` \([\s\S]*?\) ENGINE=[^;]+;',dump).group())
        cursor.execute("INSERT INTO customer VALUES ('C1','1','Test','test'),('C2','2','Test','test')")
        cursor.execute("INSERT INTO vendor VALUES ('V1','Shop One',5,'Test','test'),('V2','Shop Two',5,'Test','test')")
        cursor.execute("INSERT INTO product VALUES ('A','V1','Item A',10),('B','V1','Item B',20),('C','V2','Item C',7)")
        cursor.execute("INSERT INTO tag (TagID,TagName) VALUES (1,'Shared'),(2,'Only Shop Two')")
        cursor.execute("INSERT INTO producttag VALUES ('A',1),('B',1),('C',1),('C',2)")
    conn.commit()
    m.get_db_connection = lambda: pymysql.connect(database=database,**config)
    client = m.app.test_client()
    response = client.post('/api/cart_confirm_order',json=dict(userType='customer',customerID='C1',items=[dict(ProductID='A',Quantity=2),dict(ProductID='B',Quantity=1),dict(ProductID='C',Quantity=3)]))
    assert response.status_code==200,response.json
    checkout = response.json['checkoutID']
    assert re.fullmatch(r'T\d{20}-[0-9a-f]{8}',checkout)
    assert len(response.json['orders'])==2
    assert all(item['transactionID'].startswith(checkout+'-') for item in response.json['orders'])
    rows = client.get('/api/orders?userType=customer&customerID=C1').json['orders']
    assert len(rows)==3 and all(row['CheckoutID']==checkout for row in rows)
    assert sum(row['Subtotal'] for row in rows)==61
    assert all('Quantity' in row and 'PriceAtPurchase' in row and 'VendorName' in row for row in rows)
    own_order = next(item for item in response.json['orders'] if item['vendorID']=='V1')
    denied = client.post('/api/remove_items',json=dict(transactionID=own_order['transactionID'], ProductID='A', userType='vendor', vendorID='V1'))
    assert denied.status_code==403,denied.json
    unchanged = client.get('/api/orders?userType=customer&customerID=C1').json['orders']
    assert next(row for row in unchanged if row['ProductID']=='A')['Quantity']==2
    vendor_rows = client.get('/api/orders?userType=vendor&vendorID=V1').json['orders']
    assert len(vendor_rows)==2 and all(row['VendorID']=='V1' and row['CustomerID']=='C1' for row in vendor_rows)
    assert not client.get('/api/orders?userType=customer&customerID=C2').json['orders']
    assert len(client.get('/api/search_by_tag?tag=Shared').json['products'])==3
    results = client.get('/api/search_by_tag?tag=Shared&userType=vendor&vendorID=V1').json['products']
    assert len(results)==2 and all(row['VendorID']=='V1' for row in results)
    assert not client.get('/api/search_by_tag?tag=Only&userType=vendor&vendorID=V1').json['products']
    assert client.get('/api/get_tags?userType=vendor&vendorID=V1').json['tags']==['Shared']
    assert len(client.get('/api/get_tags').json['tags'])==2
    assert client.get('/api/search_by_tag?tag=Shared&userType=vendor').status_code==400
    assert client.get('/api/orders?userType=admin&customerID=C1').status_code==400
    legacy = 'T202310161234'
    assert m.checkout_id_from_transaction(legacy)==legacy
    assert m.checkout_id_from_transaction('T'+'a'*32)=='T'+'a'*32
    # Removing the only product keeps a visible zero-value cancelled customer order.
    order = next(item for item in response.json['orders'] if item['vendorID']=='V2')
    result = client.post('/api/remove_items',json=dict(transactionID=order['transactionID'],ProductID='C',userType='customer',customerID='C1'))
    assert result.status_code==200,result.json
    empty = next(row for row in client.get('/api/orders?userType=customer&customerID=C1').json['orders'] if row['TransactionID']==order['transactionID'])
    assert empty['Status']=='CANCELLED' and empty['TotalAmount']==0 and empty['ProductID'] is None
    conn.close()
    print('PASS: real MySQL checkout grouping, dated IDs, product details, customer/vendor filtering, tag scope and empty cancelled orders')
finally:
    if created:
        with admin.cursor() as cursor: cursor.execute('DROP DATABASE `' + database + '`')
    admin.close()
