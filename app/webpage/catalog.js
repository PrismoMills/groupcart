(function (root) {
    'use strict';
    function vendorsForView(products, vendors, role, ownVendor, tagged) {
        if (role === 'vendor') return ownVendor ? [ownVendor] : [];
        if (!tagged) return vendors;
        const involved = new Set(products.map(product => product.VendorID));
        return vendors.filter(vendor => involved.has(vendor.VendorID));
    }
    function productsForVendor(products, id) {
        return id === 'all' ? products : products.filter(product => product.VendorID === id);
    }
    if (typeof module !== 'undefined') module.exports = {vendorsForView, productsForVendor};
    if (!root.document) return;
    const document = root.document;
    const role = root.localStorage.getItem('isRegistered') === 'true' ? root.localStorage.getItem('userType') : null;
    const vendorID = root.localStorage.getItem('VendorID');
    const tag = /(?:^|\/)search_tag\.html$/.test(root.location.pathname) ? new URLSearchParams(root.location.search).get('tag') : null;
    const size = 18;
    let products = [], vendors = [], selected = 'all', page = 1;
    function node(tagName, text) {
        const result = document.createElement(tagName);
        if (text !== undefined) result.textContent = text;
        return result;
    }
    async function json(url) {
        const response = await root.fetch(url);
        const data = await response.json();
        if (!response.ok || data.success === false) throw new Error(data.message || 'Unable to load products');
        return data;
    }
    function renderVendors() {
        const menu = document.getElementById('categoryMenu');
        menu.replaceChildren();
        const choices = role === 'vendor' ? vendors : [{VendorID:'all', BusinessName:'All'}, ...vendors];
        choices.forEach(vendor => {
            const li = node('li');
            if (role === 'vendor') {
                const label = node('span', vendor.BusinessName);
                label.className = 'vendor-label';
                li.append(label); menu.append(li);
                return;
            }
            const link = node('a', vendor.BusinessName);
            link.href = '#';
            link.dataset.vendorId = vendor.VendorID;
            if (vendor.VendorID === selected) link.setAttribute('aria-current', 'true');
            link.addEventListener('click', event => {
                event.preventDefault(); selected = vendor.VendorID; page = 1;
                renderVendors(); renderProducts();
            });
            li.append(link); menu.append(li);
        });
    }
    function renderProducts() {
        const container = document.getElementById('productContainer');
        const pagination = document.getElementById('pagination');
        container.replaceChildren(); pagination.replaceChildren();
        const filtered = productsForVendor(products, selected);
        if (!filtered.length) {
            const message = node('p', tag ? 'No products match this tag.' : 'No products to display.');
            message.className = 'catalog-message'; container.append(message); return;
        }
        filtered.slice((page-1)*size, page*size).forEach(product => {
            const card = node('div'); card.className = 'product'; card.tabIndex = 0;
            card.setAttribute('role','link'); card.setAttribute('aria-label',product.Name);
            const image = node('img');
            image.src = 'http://127.0.0.1:5000/static/images/' + encodeURIComponent(product.Name.replace(/\s+/g,'')) + '.png';
            image.alt = product.Name;
            const open = () => {
                const params = new URLSearchParams({ProductID:product.ProductID,Name:product.Name,ListedPrice:product.ListedPrice,image:image.src});
                root.location.href = 'product_detail.html?' + params;
            };
            card.addEventListener('click',open);
            card.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();open();}});
            card.append(image,node('h3',product.Name),node('p','$'+Number(product.ListedPrice).toFixed(2)));
            container.append(card);
        });
        const pages = Math.ceil(filtered.length/size);
        if (pages <= 1) return;
        function button(label, destination) {
            const control = node('button',label); control.type='button';
            control.disabled = destination < 1 || destination > pages;
            if (destination === page && Number.isInteger(label)) control.style.backgroundColor='#d17abf';
            control.addEventListener('click',()=>{page=destination;renderProducts();});
            pagination.append(control);
        }
        button('Previous',page-1);
        for(let i=1;i<=pages;i++) button(i,i);
        button('Next',page+1);
    }
    async function load() {
        const container = document.getElementById('productContainer');
        document.getElementById('catalogTitle').textContent = tag ? 'Products tagged #' + tag : 'Products for Sale';
        try {
            if (role === 'vendor') {
                if (!vendorID) throw new Error('Please log in again.');
                const [info, result] = await Promise.all([
                    json(root.shopApi('/api/vendor_info',{vendorID})),
                    json(tag ? root.shopApi('/api/search_by_tag',{tag}) : root.shopApi('/api/vendor_products',{vendorID}))
                ]);
                products = result.products;
                vendors = vendorsForView(products, [], role, info.vendor, Boolean(tag));
                selected = vendorID;
                const add = document.getElementById('addProductBtn');
                add.style.display='block'; add.addEventListener('click',()=>{root.location.href='product_detail.html';});
            } else {
                const [allVendors, result] = await Promise.all([
                    json(root.shopApi('/api/vendors')),
                    json(tag ? root.shopApi('/api/search_by_tag',{tag}) : root.shopApi('/api/products',{category_name:'all'}))
                ]);
                products = Array.isArray(result) ? result : result.products;
                vendors = vendorsForView(products, allVendors, role, null, Boolean(tag));
            }
            if (!Array.isArray(products)) throw new Error('Invalid product data');
            renderVendors(); renderProducts();
        } catch (error) {
            container.replaceChildren(node('p',error.message));
        }
    }
    document.addEventListener('DOMContentLoaded',load);
})(typeof window !== 'undefined' ? window : globalThis);
