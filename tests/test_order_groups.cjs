const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const path = require('path');
const {groupOrders, actions} = require('../app/webpage/orders.js');
const {apiUrl} = require('../app/webpage/navigation.js');
const row = (checkout, tx, vendor, amount, subtotal, product = 'P1') => ({CheckoutID:checkout, TransactionID:tx,
  VendorID:vendor, VendorName:vendor, TotalAmount:amount, Subtotal:subtotal, ProductID:product,
  TransactionDate:'2026-11-05 10:00:00', Status:'PENDING_SHIPMENT', Quantity:1, PriceAtPurchase:subtotal});
const data = [row('checkout1','t1','v1',30,10), row('checkout1','t1','v1',30,20,'P2'),
  row('checkout1','t2','v2',7,7), row('checkout2','t3','v1',5,5)];
const grouped = groupOrders(data,'customer');
assert.equal(grouped.length,2);
assert.equal(grouped[0].vendors.length,2);
assert.equal(grouped[0].vendors[0].items.length,2);
assert.equal(grouped[0].total,37);
assert.equal(grouped[0].vendors[0].total,30);
const legacy = [row('old','old','v1',40,10), row('old','old','v2',40,30)];
assert.equal(groupOrders(legacy,'customer')[0].total,40);
assert.equal(groupOrders([legacy[0]],'vendor')[0].total,10);
const old1 = {...row('uuid1','uuid1','v1',10,10), CustomerID:'C1'};
const old2 = {...row('uuid2','uuid2','v2',30,30), CustomerID:'C1'};
assert.equal(groupOrders([old1,old2],'customer').length,1);
assert.equal(groupOrders([old1,old2],'customer')[0].vendors.length,2);
assert.equal(groupOrders([old1,old2],'customer')[0].total,40);
assert.equal(groupOrders([old1,{...old2,CustomerID:'C2'}],'customer').length,2);
assert.equal(groupOrders([old1,{...old2,TransactionDate:'2026-11-05 10:00:01'}],'customer').length,2);
assert.equal(groupOrders([old1,old2],'vendor').length,2);
// Explicit checkout IDs must stay separate even if they share a timestamp.
assert.equal(groupOrders([{...old1,CheckoutID:'batch1'},{...old2,CheckoutID:'batch2'}],'customer').length,2);
assert.equal(groupOrders([old1,{...old1,ProductID:'P2',Subtotal:0}],'customer')[0].total,10);
const empty = groupOrders([row('empty','empty',null,0,0,null)],'customer')[0];
assert.equal(empty.total,0); assert.equal(empty.vendors[0].items.length,0);
assert.equal(actions('customer','PENDING_SHIPMENT').cancel,true);
assert.equal(actions('customer','SHIPPED').remove,false);
assert.equal(actions('vendor','PENDING_SHIPMENT').ship,true);
assert.equal(actions('vendor','PENDING_SHIPMENT').remove,false);
assert.equal(actions('vendor','SHIPPED').remove,false);
assert.equal(actions('customer','PENDING_SHIPMENT').remove,true);
assert.equal(actions('vendor','COMPLETED').cancel,false);
const vendorStorage = {getItem:key=>({isRegistered:'true',userType:'vendor',VendorID:'V001'})[key]};
const customerStorage = {getItem:key=>({isRegistered:'true',userType:'customer',CustomerID:'C001'})[key]};
const url = new URL(apiUrl('/api/search_by_tag',{tag:'A & B'},vendorStorage));
assert.equal(url.searchParams.get('vendorID'),'V001');
assert.equal(url.searchParams.get('userType'),'vendor');
assert.equal(url.searchParams.get('tag'),'A & B');
assert.equal(new URL(apiUrl('/api/search_by_tag',{tag:'x'},customerStorage)).searchParams.has('vendorID'),false);
const folder = path.resolve(__dirname,'../app/webpage');
for(const file of fs.readdirSync(folder).filter(name=>name.endsWith('.html'))) {
  const html = fs.readFileSync(path.join(folder,file),'utf8');
  assert(html.includes('<script src="navigation.js'),file);
  assert(html.indexOf('data-order-nav') > html.indexOf('data-cart-nav'),file);
  for(const match of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)) new vm.Script(match[1],{filename:file});
}
assert(!fs.readFileSync(path.join(folder,'home.html'),'utf8').match(/<div id="leftSidebar"[\s\S]*?href="order.html"[\s\S]*?<\/div>/));
for(const name of fs.readdirSync(folder).filter(name=>name.endsWith('.html'))) {
  assert(fs.readFileSync(path.join(folder,name),'utf8').includes('site-header.css?v='),name);
}
console.log('PASS: checkout/vendor grouping, totals, legacy orders, action states, vendor search scope and page navigation');
