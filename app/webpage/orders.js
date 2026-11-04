(function (root) {
    'use strict';
    function groupOrders(rows, role) {
        const checkouts = new Map();
        rows.forEach(row => {
            const match = /^(T\d{20}-[0-9a-f]{8})-\d{2,}$/.exec(row.TransactionID || '');
            const batch = row.CheckoutID && row.CheckoutID !== row.TransactionID ? row.CheckoutID : match && match[1];
            const byTime = !batch && role === 'customer' && row.CustomerID && row.TransactionDate;
            const id = batch || (byTime ? 'time:' + row.CustomerID + ':' + row.TransactionDate : row.TransactionID);
            if (!checkouts.has(id)) checkouts.set(id, {id, byTime: Boolean(byTime), date: row.TransactionDate, vendors: new Map(), totals: new Map()});
            const checkout = checkouts.get(id);
            const key = row.TransactionID + '|' + (row.VendorID || 'empty');
            if (!checkout.vendors.has(key)) checkout.vendors.set(key, {
                transactionID: row.TransactionID, vendorID: row.VendorID,
                name: row.VendorName || 'No remaining items', customerID: row.CustomerID,
                status: row.Status, items: [], total: 0
            });
            const vendor = checkout.vendors.get(key);
            if (row.ProductID) {
                vendor.items.push(row);
                vendor.total += Number(row.Subtotal);
            }
            // A legacy order can have multiple vendors. Count its header total
            // once, rather than once per product or once per vendor.
            checkout.totals.set(row.TransactionID, Number(row.TotalAmount));
        });
        return Array.from(checkouts.values()).map(checkout => {
            const vendors = Array.from(checkout.vendors.values());
            return {...checkout, vendors, total: role === 'vendor'
                ? vendors.reduce((sum, vendor) => sum + vendor.total, 0)
                : Array.from(checkout.totals.values()).reduce((sum, amount) => sum + amount, 0)};
        });
    }
    function actions(role, status) {
        return {
            ship: role === 'vendor' && status === 'PENDING_SHIPMENT',
            receive: role === 'customer' && status === 'SHIPPED',
            cancel: (role === 'customer' && status === 'PENDING_SHIPMENT') ||
                (role === 'vendor' && ['PENDING_SHIPMENT', 'SHIPPED'].includes(status)),
            remove: role === 'customer' && status === 'PENDING_SHIPMENT'
        };
    }
    if (typeof module !== 'undefined') module.exports = {groupOrders, actions};
    if (!root.document) return;
    const document = root.document;
    const money = amount => '$' + Number(amount).toFixed(2);
    const statusNames = {PENDING_SHIPMENT: 'Awaiting shipment', SHIPPED: 'Shipped', COMPLETED: 'Completed', CANCELLED: 'Cancelled'};
    function element(tag, text, className) {
        const node = document.createElement(tag);
        if (text !== undefined) node.textContent = text;
        if (className) node.className = className;
        return node;
    }
    let pending = false;
    async function changeOrder(path, vendor, button, extra = {}) {
        if (pending) return;
        if (!root.confirm(button.textContent + '?')) return;
        pending = true;
        button.disabled = true;
        try {
            const response = await root.fetch('http://localhost:5000/api/' + path, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({transactionID: vendor.transactionID,
                    userType: root.localStorage.getItem('userType'),
                    customerID: root.localStorage.getItem('CustomerID'),
                    vendorID: root.localStorage.getItem('VendorID'), ...extra})
            });
            const result = await response.json();
            if (!response.ok || !result.success) throw new Error(result.message || 'Unable to update order');
            await loadOrders();
        } catch (error) {
            document.getElementById('orderMessage').textContent = error.message;
        } finally {
            pending = false;
            button.disabled = false;
        }
    }
    function actionButton(text, path, vendor, extra) {
        const button = element('button', text, 'action-btn');
        button.type = 'button';
        button.addEventListener('click', () => changeOrder(path, vendor, button, extra));
        return button;
    }
    function renderOrders(rows, role) {
        const container = document.getElementById('orderGroups');
        container.replaceChildren();
        groupOrders(rows, role).forEach(checkout => {
            const card = element('section', undefined, 'checkout-card');
            const heading = element('div', undefined, 'checkout-heading');
            const title = element('div');
            title.append(element('h2', role === 'vendor' ? 'Customer order' : 'Checkout'));
            title.append(element('p', checkout.date, 'order-date'));
            if (!checkout.byTime) title.append(element('p', checkout.id, 'order-code'));
            const summary = element('div', undefined, 'checkout-summary');
            summary.append(element('strong', money(checkout.total)));
            summary.append(element('p', checkout.vendors.length + (checkout.vendors.length === 1 ? ' vendor order' : ' vendor orders')));
            heading.append(title, summary);
            card.append(heading);
            checkout.vendors.forEach(vendor => {
                const section = element('section', undefined, 'vendor-order');
                const header = element('div', undefined, 'vendor-heading');
                const info = element('div');
                info.append(element('h3', vendor.name));
                info.append(element('p', 'Order: ' + vendor.transactionID, 'order-code'));
                if (role === 'vendor') info.append(element('p', 'Customer: ' + vendor.customerID, 'order-date'));
                header.append(info, element('span', statusNames[vendor.status] || vendor.status, 'order-status status-' + vendor.status));
                section.append(header);
                const scroll = element('div', undefined, 'order-table-scroll');
                const table = element('table');
                const thead = element('thead');
                const headings = element('tr');
                ['Product', 'Quantity', 'Unit price', 'Subtotal', ''].forEach(text => headings.append(element('th', text)));
                thead.append(headings);
                const tbody = element('tbody');
                const allowed = actions(role, vendor.status);
                vendor.items.forEach(item => {
                    const tr = element('tr');
                    [item.Item, item.Quantity, money(item.PriceAtPurchase), money(item.Subtotal)].forEach(text => tr.append(element('td', text)));
                    const controls = element('td');
                    if (allowed.remove) controls.append(actionButton('Remove item', 'remove_items', vendor, {ProductID: item.ProductID}));
                    tr.append(controls);
                    tbody.append(tr);
                });
                if (!vendor.items.length) {
                    const tr = element('tr');
                    const td = element('td', 'All items have been removed.');
                    td.colSpan = 5;
                    tr.append(td); tbody.append(tr);
                }
                table.append(thead, tbody); scroll.append(table); section.append(scroll);
                const footer = element('div', undefined, 'vendor-footer');
                footer.append(element('strong', 'Vendor subtotal: ' + money(vendor.total)));
                const controls = element('div', undefined, 'order-actions');
                if (allowed.ship) controls.append(actionButton('Mark as shipped', 'update_order_status', vendor, {newStatus: 'SHIPPED'}));
                if (allowed.receive) controls.append(actionButton('Confirm receipt', 'update_order_status', vendor, {newStatus: 'COMPLETED'}));
                if (allowed.cancel) controls.append(actionButton('Cancel order', 'cancel_order', vendor));
                footer.append(controls); section.append(footer); card.append(section);
            });
            container.append(card);
        });
    }
    async function loadOrders() {
        const role = root.localStorage.getItem('userType');
        const identity = root.localStorage.getItem(role === 'customer' ? 'CustomerID' : 'VendorID');
        if (root.localStorage.getItem('isRegistered') !== 'true' || !['customer', 'vendor'].includes(role) || !identity) {
            root.location.href = 'login.html';
            return;
        }
        const message = document.getElementById('orderMessage');
        const parameters = new URLSearchParams({userType: role});
        parameters.set(role === 'customer' ? 'customerID' : 'vendorID', identity);
        try {
            const response = await root.fetch('http://localhost:5000/api/orders?' + parameters);
            const data = await response.json();
            if (!response.ok || !data.success || !Array.isArray(data.orders)) throw new Error(data.message || 'Unable to load orders');
            renderOrders(data.orders, role);
            document.querySelector('.container h1').textContent = role === 'vendor' ? 'Your Customer Orders' : 'Your Orders';
            message.textContent = data.orders.length ? '' : 'You have no orders yet.';
        } catch (error) {
            message.textContent = error.message + '. Please try again.';
        }
    }
    document.addEventListener('DOMContentLoaded', loadOrders);
})(typeof window !== 'undefined' ? window : globalThis);
