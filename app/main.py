import json
import os
import re
from pathlib import Path
from decimal import Decimal, InvalidOperation
from uuid import uuid4

import flask
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pymysql
from datetime import datetime
app = Flask(__name__)
CORS(app)

# Already change to English version
# database configuration and connect to database
def get_db_connection():
    config_path = Path(__file__).with_name('db_config.json')
    if not config_path.exists():
        raise RuntimeError('Copy app/db_config.example.json to app/db_config.json and configure your MySQL connection. See README.md.')
    config = json.loads(config_path.read_text(encoding='utf-8'))
    return pymysql.connect(**config, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)

#
def get_product_price(product_id):
    # setup database connection
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(("SELECT ListedPrice FROM product WHERE ProductID = %s"),(product_id,))
            price=cursor.fetchall()
            if price:
                # return products price
                return price[0]['ListedPrice']
            else:
                # if productID cannot be found
                return None
    finally:
        # close database connection
            conn.close()


#json格式要改

class InputError(ValueError):
    pass

def positive_money(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount <= 0 or amount > Decimal('99999999.99'):
            raise InputError('Price must be positive and within the supported range')
        if amount != amount.quantize(Decimal('0.01')):
            raise InputError('Price must have at most two decimal places')
        return amount
    except (InvalidOperation, TypeError, ValueError):
        raise InputError('Invalid price')

def positive_quantity(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 2147483647:
        raise InputError('Quantity must be a positive integer')
    return value

def json_object():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise InputError('A JSON object is required')
    return data

def create_orders(data, items):
    conn = None
    try:
        if data.get('userType') != 'customer' or not data.get('customerID'):
            raise InputError('Only customers can place orders')
        if not isinstance(items, list) or not items:
            raise InputError('At least one item is required')
        quantities = {}
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get('ProductID'), str) or not item['ProductID']:
                raise InputError('Invalid product')
            product_id = item['ProductID']
            quantities[product_id] = positive_quantity(quantities.get(product_id, 0) + positive_quantity(item.get('Quantity')))
        conn = get_db_connection()
        conn.begin()
        cursor = conn.cursor()
        cursor.execute('SELECT CustomerID FROM customer WHERE CustomerID = %s', (data['customerID'],))
        if not cursor.fetchone():
            raise InputError('Customer not found')
        groups = {}
        for product_id, quantity in sorted(quantities.items()):
            cursor.execute('SELECT ProductID, VendorID, ListedPrice FROM product WHERE ProductID = %s FOR UPDATE', (product_id,))
            product = cursor.fetchone()
            if not product:
                raise InputError('Product not found: ' + product_id)
            price = positive_money(product['ListedPrice'])
            groups.setdefault(product['VendorID'], []).append((product_id, quantity, price))
        orders = []
        checkout_date = datetime.now()
        checkout_id = 'T' + checkout_date.strftime('%Y%m%d%H%M%S%f') + '-' + uuid4().hex[:8]
        for vendor_index, (vendor_id, products) in enumerate(groups.items(), 1):
            total = sum((quantity * price for _, quantity, price in products), Decimal('0'))
            if total > Decimal('99999999.99'):
                raise InputError('Order total exceeds the supported range')
            transaction_id = checkout_id + '-' + str(vendor_index).zfill(2)
            cursor.execute("INSERT INTO transaction (TransactionID, CustomerID, TransactionDate, TotalAmount, status) VALUES (%s, %s, %s, %s, 'PENDING_SHIPMENT')", (transaction_id, data['customerID'], checkout_date, total))
            for product_id, quantity, price in products:
                cursor.execute('INSERT INTO transactionitem (TransactionID, ProductID, Quantity, PriceAtPurchase) VALUES (%s, %s, %s, %s)', (transaction_id, product_id, quantity, price))
            orders.append({'transactionID': transaction_id, 'vendorID': vendor_id, 'checkoutID': checkout_id})
        conn.commit()
        return jsonify(success=True, message='Order(s) created successfully', orders=orders,
                       transactionID=orders[0]['transactionID'], vendorID=orders[0]['vendorID'], checkoutID=checkout_id), 200
    except InputError as exc:
        if conn: conn.rollback()
        return jsonify(success=False, message=str(exc)), 400
    except Exception:
        if conn: conn.rollback()
        app.logger.exception('Order creation failed')
        return jsonify(success=False, message='Internal server error'), 500
    finally:
        if conn: conn.close()

@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT VendorID, BusinessName, CustomerFeedbackScore, GeographicalPresence FROM vendor")
            vendors = cursor.fetchall()
            print(vendors)
            # calls json.dumps to customize serialization
            json_response = json.dumps(vendors, default=str)
            response = flask.make_response(json_response, 200)
            response.content_type = 'application/json'  # set rightful JSON format for Content-Type
            response.success = True
            return response
            # return jsonify(vendors)
    finally:
        conn.close()
@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT BusinessName as name  FROM vendor")
            categories = cursor.fetchall()
            return jsonify(categories)
    finally:
        conn.close()

#this api is focusing on finding out what products does the specific/specified/particular vendor publish
@app.route('/api/vendor_products', methods=['GET'])
def get_vendor_products():
    vendor_id = request.args.get('vendorID')
    if not vendor_id:
        return jsonify({'success': False, 'message': 'Missing vendorID parameter'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Search for all products uploaded by the merchant=what products do those venders have
            cursor.execute("SELECT ProductID, Name, ListedPrice, VendorID FROM product WHERE VendorID = %s", (vendor_id,))
            products = cursor.fetchall()
            # create a json obj
            data = {
                'success': True,
                'products': products
            }
            # calls json.dumps to customize serialization
            json_response = json.dumps(data, default=str)
            response = flask.make_response(json_response, 200)
            response.content_type = 'application/json'  # set rightful JSON format for Content-Type
            response.success = True
            return response
            # return jsonify({'success': True, 'products': products}), 200
    except Exception as e:
        print("Error fetching vendor products:", e)
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
    finally:
        conn.close()

@app.route('/api/customer_info', methods=['GET'])
def get_customer_info():
    customer_id = request.args.get('CustomerID')
    if not customer_id:
        return jsonify({'success': False, 'message': 'Missing CustomerID parameter'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT CustomerID, ContactNumber, ShippingDetails FROM customer WHERE CustomerID = %s", (customer_id,))
            customer = cursor.fetchone()
            if customer:
                return jsonify({'success': True, 'customer': customer}), 200
            else:
                return jsonify({'success': False, 'message': 'Customer not found'}), 404
    except Exception as e:
        print("Error fetching customer info:", e)
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
    finally:
        conn.close()

@app.route('/api/vendor_info', methods=['GET'])
def get_vendor_info():
    vendor_id = request.args.get('vendorID')
    if not vendor_id:
        return jsonify({'success': False, 'message': 'Missing vendorID parameter'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT VendorID, BusinessName, CustomerFeedbackScore, GeographicalPresence FROM vendor WHERE VendorID = %s", (vendor_id,))
            vendor = cursor.fetchone()
            if vendor:
                # return jsonify({'success': True, 'vendor': vendor}), 200 # Decimal Error, cannot be identified
                # create a json obj
                data = {
                    'success': True,
                    'vendor': vendor
                }
                # calls json.dumps to customize serialization
                json_response = json.dumps(data, default=str)
                response = flask.make_response(json_response, 200)
                response.content_type = 'application/json'  # set rightful JSON format for Content-Type
                response.success = True
                return response
            else:
                return jsonify({'success': False, 'message': 'Vendor not found'}), 404
    except Exception as e:
        print("Error fetching vendor info:", e)
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
    finally:
        conn.close()

@app.route('/api/products', methods=['GET'])
def get_products():
    category_name = request.args.get('category_name', default='all')

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if category_name == 'all':
                cursor.execute("SELECT ProductID,Name,ListedPrice,p.VendorID,BusinessName as VendorName FROM product p inner join vendor v on p.VendorID = v.VendorID")
            else:
                cursor.execute(
                    "SELECT ProductID,Name,ListedPrice,p.VendorID,BusinessName as VendorName FROM product p inner join vendor v on p.VendorID = v.VendorID HAVING BusinessName = %s",
                    (category_name,)
                )
            products = cursor.fetchall()
            print(products)

            # Use json.dumps to customize serialization
            json_response = json.dumps(products, default=str)
            response = flask.make_response(json_response, 200)
            response.content_type = 'application/json' # set correct ContentType for json data
            return response
    finally:
        conn.close()
@app.route('/api/add_vendor', methods=['POST'])
def add_vendor():
    data = request.json  # get JSON data from request
    vendor_id = data.get('VendorID')  # get VendorID

    # Check if there is already an identical VendorID in the database
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM vendor WHERE VendorID = %s", (vendor_id,))
            existing_vendor = cursor.fetchone()
            if existing_vendor:
                return jsonify({'success': False, 'message': 'Vendor ID already exists.'}), 400

            # Insert new record of VENDOR
            cursor.execute(
                "INSERT INTO vendor (VendorID, BusinessName, CustomerFeedbackScore, GeographicalPresence,password) VALUES (%s, %s, %s, %s, %s)",
                (data.get('VendorID'), data.get('BusinessName'), data.get('CustomerFeedbackScore'), data.get('GeographicalPresence'),data.get('password'))
            )
            conn.commit()
            return jsonify({'success': True, 'message': 'Vendor added successfully.'})

    finally:
        conn.close()
@app.route('/api/add_tag', methods=['POST'])
def add_tag():
    try:
        data = request.get_json()
        tag_name = data.get('TagName')
        if not tag_name:
            return jsonify({'success': False, 'message': 'TagName is required'}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        # Check whether the Tag exist
        cursor.execute("SELECT * FROM tag WHERE TagName = %s", (tag_name,))
        existing_tag = cursor.fetchone()
        if existing_tag:
            return jsonify({'success': False, 'message': 'Tag already exists'}), 400
        cursor.execute("INSERT INTO tag (TagName) VALUES (%s)", (tag_name,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Tag added successfully'}), 200
    except Exception as e:
        print("Error adding tag:", e)
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/api/insert_product', methods=['POST'])
def insert_product():
    conn = None
    try:
        data = json_object()
        if data.get('userType') != 'vendor':
            raise InputError('Only vendors can publish products')
        name = data.get('Name')
        vendor_id = data.get('VendorID')
        if not isinstance(name, str) or not name.strip() or len(name) > 100 or not vendor_id:
            raise InputError('Valid name and vendor are required')
        price = positive_money(data.get('ListedPrice'))
        tags = []
        for key in ('tag1', 'tag2', 'tag3'):
            tag = data.get(key) or ''
            if not isinstance(tag, str):
                raise InputError('Invalid tag')
            if tag.strip() and tag.strip() not in tags:
                tags.append(tag.strip())
        conn = get_db_connection()
        conn.begin()
        cursor = conn.cursor()
        cursor.execute('SELECT VendorID FROM vendor WHERE VendorID = %s', (vendor_id,))
        if not cursor.fetchone():
            raise InputError('Vendor not found')
        tag_ids = []
        for tag in tags:
            cursor.execute('SELECT TagID FROM tag WHERE TagName = %s', (tag,))
            row = cursor.fetchone()
            if not row: raise InputError('Tag not found: ' + tag)
            tag_ids.append(row['TagID'])
        product_id = 'P' + uuid4().hex
        cursor.execute('INSERT INTO product (ProductID, VendorID, Name, ListedPrice) VALUES (%s, %s, %s, %s)', (product_id, vendor_id, name.strip(), price))
        for tag_id in tag_ids:
            cursor.execute('INSERT INTO producttag (ProductID, TagID) VALUES (%s, %s)', (product_id, tag_id))
        conn.commit()
        return jsonify(success=True, message='Product inserted successfully'), 200
    except InputError as exc:
        if conn: conn.rollback()
        return jsonify(success=False, message=str(exc)), 400
    except Exception:
        if conn: conn.rollback()
        app.logger.exception('Product insertion failed')
        return jsonify(success=False, message='Internal server error'), 500
    finally:
        if conn: conn.close()

@app.route('/api/product_tags', methods=['GET'])
def get_product_tags():
    product_id = request.args.get('ProductID')
    if not product_id:
        return jsonify({'success': False, 'message': 'Missing ProductID parameter'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Query all tags associated with this product
            cursor.execute("""
                SELECT t.TagName 
                FROM producttag pt 
                INNER JOIN tag t ON pt.TagID = t.TagID 
                WHERE pt.ProductID = %s
            """, (product_id,))
            tags = cursor.fetchall()
            return jsonify({'success': True, 'tags': tags}), 200
    except Exception as e:
        print("Error fetching product tags:", e)
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
    finally:
        conn.close()
@app.route('/api/search_by_tag', methods=['GET'])
def search_by_tag():
    tag = request.args.get('tag', '').strip()
    role = request.args.get('userType', 'customer')
    vendor_id = request.args.get('vendorID')
    if not tag or role not in ('customer', 'vendor') or (role == 'vendor' and not vendor_id):
        return jsonify(success=False, message='A tag and valid account context are required'), 400
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT p.ProductID, p.Name, p.ListedPrice, p.VendorID,
                            v.BusinessName AS VendorName
            FROM product p
            JOIN producttag pt ON pt.ProductID = p.ProductID
            JOIN tag t ON t.TagID = pt.TagID
            JOIN vendor v ON v.VendorID = p.VendorID
            WHERE t.TagName LIKE %s
        """
        args = ['%' + tag + '%']
        if role == 'vendor':
            query += ' AND p.VendorID = %s'
            args.append(vendor_id)
        query += ' ORDER BY p.ListedPrice, p.ProductID'
        cursor.execute(query, tuple(args))
        products = cursor.fetchall()
        return app.response_class(json.dumps({'success': True, 'products': products}, default=str), mimetype='application/json')
    except Exception:
        app.logger.exception('Tag search failed')
        return jsonify(success=False, message='Unable to search products'), 500
    finally:
        if conn: conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        user_id = data.get('customerID')
        password = data.get('password')

        if not user_id or not password:
            print("Missing customerID or password")
            return jsonify({'message': 'Missing customerID or password'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Attempt to log in as customer
        cursor.execute("SELECT * FROM customer WHERE CustomerID = %s", (user_id,))
        customer = cursor.fetchone()
        if customer:
            stored_password = customer['password']
            if verify_password(stored_password, password):
                print("Customer login success")
                conn.close()
                return jsonify({
                    'message': 'Login successful',
                    'userType': 'customer',
                    'customerID': customer['CustomerID'],
                    'vendorID': None
                }), 200

        # Attempt to log in as vendor
        cursor.execute("SELECT * FROM vendor WHERE VendorID = %s", (user_id,))
        vendor = cursor.fetchone()
        if vendor:
            stored_password = vendor['password']
            if verify_password(stored_password, password):
                print("Vendor login success")
                conn.close()
                return jsonify({
                    'message': 'Login successful',
                    'userType': 'vendor',
                    'vendorID': vendor['VendorID'],
                    'customerID': None
                }), 200

        print("Invalid credentials")
        conn.close()
        return jsonify({'message': 'Invalid credentials'}), 401

    except Exception as e:
        print("Exception occurred:", str(e))
        return jsonify({'message': 'Internal server error'}), 500
def verify_password(stored_password, provided_password):
    return stored_password == provided_password  # 暂时改成明文比对

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        customer_id = data.get('CustomerID')
        contact_number = data.get('ContactNumber')
        shipping_details = data.get('ShippingDetails')
        password = data.get('Password')

        # Check if the input is complete
        if not customer_id or not contact_number or not shipping_details or not password:
            return jsonify({'success': False, 'message': 'All fields are required!'}), 400

        # Check if the CustomerID already exists
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM customer WHERE CustomerID = %s", (customer_id,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({'success': False, 'message': 'CustomerID already exists!'}), 400

        # Insert new user into database
        cursor.execute("INSERT INTO customer (CustomerID, ContactNumber, ShippingDetails, password)VALUES (%s, %s, %s, %s)", (customer_id, contact_number, shipping_details, password))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Registration successful!'}), 200

    except Exception as e:
        print("Error during registration:", e)
        return jsonify({'success': False, 'message': 'Internal server error'}), 500


def checkout_id_from_transaction(transaction_id):
    match = re.fullmatch(r'(T\d{20}-[0-9a-f]{8})-\d{2,}', transaction_id)
    return match.group(1) if match else transaction_id

@app.route('/api/orders', methods=['GET'])
def get_orders():
    role = request.args.get('userType')
    identity = request.args.get('customerID' if role == 'customer' else 'vendorID')
    if role not in ('customer', 'vendor') or not identity:
        return jsonify(success=False, message='Valid user type and account ID are required'), 400
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT t.TransactionID, t.TransactionDate, t.CustomerID,
                   t.TotalAmount, t.status AS Status, ti.TransactionItemID,
                   ti.ProductID, ti.Quantity, ti.PriceAtPurchase,
                   p.Name AS Item, p.VendorID, v.BusinessName AS VendorName
            FROM transaction t
            LEFT JOIN transactionitem ti ON ti.TransactionID = t.TransactionID
            LEFT JOIN product p ON p.ProductID = ti.ProductID
            LEFT JOIN vendor v ON v.VendorID = p.VendorID
            WHERE """ + ('t.CustomerID = %s' if role == 'customer' else 'p.VendorID = %s') + " ORDER BY t.TransactionDate DESC, t.TransactionID, ti.TransactionItemID"
        cursor.execute(query, (identity,))
        orders = []
        for row in cursor.fetchall():
            date = row['TransactionDate']
            row['TransactionDate'] = date.strftime('%Y-%m-%d %H:%M:%S') if hasattr(date, 'strftime') else str(date)
            row['CheckoutID'] = checkout_id_from_transaction(row['TransactionID'])
            row['TotalAmount'] = float(row['TotalAmount'] or 0)
            row['Quantity'] = row['Quantity'] or 0
            row['PriceAtPurchase'] = float(row['PriceAtPurchase'] or 0)
            row['Subtotal'] = float(Decimal(str(row['PriceAtPurchase'])) * row['Quantity'])
            orders.append(row)
        return jsonify(success=True, orders=orders), 200
    except Exception:
        app.logger.exception('Order query failed')
        return jsonify(success=False, message='Unable to load orders'), 500
    finally:
        if conn: conn.close()

@app.route('/api/cancel_order', methods=['POST'])
def cancel_order():
    try:
        data = request.get_json()  # Get the JSON data of the request
        transaction_id = data.get('transactionID')
        user_type = data.get('userType')

        if not transaction_id or user_type not in ('customer', 'vendor'):
            return jsonify({'success': False, 'message': 'Missing transactionID or userType'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the order exists
        cursor.execute("SELECT * FROM transaction WHERE TransactionID = %s", (transaction_id,))
        transaction = cursor.fetchone()
        if not transaction:
            return jsonify({'success': False, 'message': 'Order not found'}), 404

        current_status = transaction['status']

        # Determine whether the order can be cancelled based on the user type
        if user_type == 'customer' and current_status != 'PENDING_SHIPMENT':
            return jsonify({'success': False, 'message': 'You can only cancel orders in PENDING_SHIPMENT status.'}), 400
        if user_type == 'vendor' and current_status not in ['PENDING_SHIPMENT', 'SHIPPED']:
            return jsonify({'success': False, 'message': 'You can only cancel orders in PENDING_SHIPMENT or SHIPPED status.'}), 400

        # Update order status to 'cancelled'
        cursor.execute("UPDATE transaction SET status = 'CANCELLED' WHERE TransactionID = %s", (transaction_id,))
        conn.commit()

        conn.close()
        return jsonify({'success': True, 'message': 'Order canceled successfully.'}), 200

    except Exception as e:
        print("Error during canceling order:", e)
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
@app.route('/api/update_order_status', methods=['POST'])
def update_order_status():
    try:
        # Get request data
        data = request.get_json()
        transaction_id = data.get('transactionID')
        new_status = data.get('newStatus')
        user_type = data.get('userType')

        # Check if the required parameters are present
        if not transaction_id or not new_status or not user_type:
            return jsonify({'success': False, 'message': 'Missing required parameters'}), 400

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the order exists
        cursor.execute("SELECT * FROM transaction WHERE TransactionID = %s", (transaction_id,))
        transaction = cursor.fetchone()
        if not transaction:
            return jsonify({'success': False, 'message': 'Order not found'}), 404

        # Check the current status of the order
        current_status = transaction['status']

        # Handle the status update based on user type
        if user_type == 'vendor':
            if current_status == 'PENDING_SHIPMENT' and new_status == 'SHIPPED':
                # Vendor can change 'PENDING_SHIPMENT' to 'SHIPPED'
                cursor.execute("UPDATE transaction SET status = %s WHERE TransactionID = %s", (new_status, transaction_id))
                conn.commit()
                conn.close()
                return jsonify({'success': True, 'message': 'Order status updated to SHIPPED.'}), 200
            else:
                return jsonify({'success': False, 'message': 'Invalid status change for vendor.'}), 400
        elif user_type == 'customer':
            if current_status == 'SHIPPED' and new_status == 'COMPLETED':
                # Customer can change 'SHIPPED' to 'COMPLETED'
                cursor.execute("UPDATE transaction SET status = %s WHERE TransactionID = %s", (new_status, transaction_id))
                conn.commit()
                conn.close()
                return jsonify({'success': True, 'message': 'Order status updated to COMPLETED.'}), 200
            else:
                return jsonify({'success': False, 'message': 'Invalid status change for customer.'}), 400
        else:
            return jsonify({'success': False, 'message': 'Invalid user type'}), 400

    except Exception as e:
        print("Error during status update:", e)
        return jsonify({'success': False, 'message': 'Internal server error'}), 500


@app.route('/api/confirm_order', methods=['POST'])
def confirm_order():
    try:
        data = json_object()
    except InputError as exc:
        return jsonify(success=False, message=str(exc)), 400
    return create_orders(data, [{'ProductID': data.get('ProductID'), 'Quantity': data.get('Quantity')}])

@app.route('/api/buy_product/<string:product_id>', methods=['GET'])
def buy_product(product_id):
    try:
        # Connect to DB
        conn = get_db_connection()
        # print(("chenggonglianjie"))
        cursor = conn.cursor()

        # Query the specified product information
        cursor.execute("SELECT ProductID, Name, ListedPrice, VendorID FROM product WHERE ProductID = %s", (product_id,))
        product = cursor.fetchone()
        # print(product)
        if not product:
            return jsonify({'error': 'Product not found!'}), 404

        # Return the product information found
        return jsonify({
            'ProductID': product['ProductID'],
            'Name': product['Name'],
            'ListedPrice': float(product['ListedPrice']),
            'VendorID': product['VendorID']
        })

    except Exception as e:
        print("Error appeared while obtaining product information:", e)
        return jsonify({'error': 'Internal server error'}), 500

    finally:
        conn.close()


@app.route('/api/cart_confirm_order', methods=['POST'])
def cart_confirm_order():
    try:
        data = json_object()
    except InputError as exc:
        return jsonify(success=False, message=str(exc)), 400
    return create_orders(data, data.get('items'))

@app.route('/api/get_tags', methods=['GET'])
def get_tags():
    role = request.args.get('userType', 'customer')
    vendor_id = request.args.get('vendorID')
    if role not in ('customer', 'vendor') or (role == 'vendor' and not vendor_id):
        return jsonify(success=False, message='Valid account context is required'), 400
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if role == 'vendor':
            cursor.execute('SELECT DISTINCT t.TagName FROM tag t JOIN producttag pt ON pt.TagID=t.TagID JOIN product p ON p.ProductID=pt.ProductID WHERE p.VendorID=%s ORDER BY t.TagName', (vendor_id,))
        else:
            cursor.execute('SELECT TagName FROM tag ORDER BY TagName')
        return jsonify(success=True, tags=[row['TagName'] for row in cursor.fetchall()]), 200
    except Exception:
        app.logger.exception('Tag list failed')
        return jsonify(success=False, message='Unable to load tags'), 500
    finally:
        if conn: conn.close()

@app.route('/api/remove_items', methods=['POST'])
def remove_items():
    conn = None
    try:
        data = json_object()
        role = data.get('userType')
        if role not in ('customer', 'vendor'):
            raise InputError('Invalid user type')
        if role != 'customer':
            return jsonify(success=False, message='Only customers can remove items from their orders'), 403
        transaction_id = data.get('transactionID')
        product_id = data.get('ProductID')
        if not transaction_id or not product_id:
            raise InputError('Transaction ID and product ID are required')
        conn = get_db_connection()
        conn.begin()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM transaction WHERE TransactionID = %s FOR UPDATE', (transaction_id,))
        order = cursor.fetchone()
        if not order: raise InputError('Order not found')
        allowed = ('PENDING_SHIPMENT',)
        if order['status'] not in allowed:
            raise InputError('Items cannot be removed in this order status')
        if order['CustomerID'] != data.get('customerID'):
            raise InputError('Customer does not own this order')
        cursor.execute('SELECT VendorID FROM product WHERE ProductID = %s', (product_id,))
        product = cursor.fetchone()
        if not product: raise InputError('Product not found')
        cursor.execute('DELETE FROM transactionitem WHERE TransactionID = %s AND ProductID = %s', (transaction_id, product_id))
        if not cursor.rowcount: raise InputError('Item not found in order')
        cursor.execute('SELECT COALESCE(SUM(Quantity * PriceAtPurchase), 0) AS total, COUNT(*) AS remaining FROM transactionitem WHERE TransactionID = %s', (transaction_id,))
        remaining = cursor.fetchone()
        cursor.execute('UPDATE transaction SET TotalAmount = %s, status = %s WHERE TransactionID = %s', (remaining['total'], order['status'] if remaining['remaining'] else 'CANCELLED', transaction_id))
        conn.commit()
        return jsonify(success=True, message='Item removed successfully'), 200
    except InputError as exc:
        if conn: conn.rollback()
        return jsonify(success=False, message=str(exc)), 400
    except Exception:
        if conn: conn.rollback()
        app.logger.exception('Item removal failed')
        return jsonify(success=False, message='Internal server error'), 500
    finally:
        if conn: conn.close()

@app.route('/')
def home_page():
    return send_from_directory(Path(__file__).parent / 'webpage', 'home.html')

@app.route('/<path:filename>')
def frontend_file(filename):
    mimetype = 'application/javascript' if filename.endswith('.js') else None
    return send_from_directory(Path(__file__).parent / 'webpage', filename, mimetype=mimetype)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
