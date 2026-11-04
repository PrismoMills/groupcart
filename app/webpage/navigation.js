(function (root) {
    'use strict';
    function account(storage) {
        return storage.getItem('isRegistered') === 'true' ? storage.getItem('userType') : null;
    }
    function apiUrl(path, parameters = {}, storage = root.localStorage) {
        const url = new URL(path, 'http://localhost:5000');
        Object.entries(parameters).forEach(([key, value]) => url.searchParams.set(key, value));
        if (account(storage) === 'vendor') {
            url.searchParams.set('userType', 'vendor');
            url.searchParams.set('vendorID', storage.getItem('VendorID') || '');
        }
        return url.toString();
    }
    root.shopApi = apiUrl;
    function alignNavigation() {
        const image = root.document.querySelector('header .header-container img');
        const menu = root.document.querySelector('header .nav-center');
        if (!image || !menu) return;
        menu.style.setProperty('--navigation-shift', '0px');
        if (root.innerWidth < 900 || !image.naturalWidth || !image.naturalHeight) return;
        const links = Array.from(menu.querySelectorAll('a')).filter(link => link.getClientRects().length && !link.closest('li').hidden);
        if (!links.length) return;
        const rectangles = links.map(link => link.getBoundingClientRect());
        if (rectangles.some(rect => Math.abs(rect.top - rectangles[0].top) > 2)) return;
        const order = menu.querySelector('a[href="order.html"]');
        const cart = menu.querySelector('a[href="cart.html"]');
        if (!order || !cart) return;
        const vendor = account(root.localStorage) === 'vendor';
        const orderBox = order.getBoundingClientRect();
        const cartBox = cart.getBoundingClientRect();
        const imageBox = image.getBoundingClientRect();
        const scale = Math.min(imageBox.width/image.naturalWidth, imageBox.height/image.naturalHeight);
        const artworkLeft = imageBox.left + (imageBox.width-image.naturalWidth*scale)/2;
        // Points in the existing logo artwork: center of G / center of GROUP.
        const target = artworkLeft + image.naturalWidth * scale * (vendor ? 562/911 : 360/911);
        const anchor = vendor ? (orderBox.left+orderBox.right)/2 : (cartBox.right+orderBox.left)/2;
        const nav = menu.closest('nav');
        const navBox = nav.getBoundingClientRect();
        const leftControl = nav.querySelector('.nav-left');
        const minX = leftControl ? leftControl.getBoundingClientRect().right+12 : navBox.left+16;
        const centerY = (orderBox.top+orderBox.bottom)/2;
        let maxX = navBox.right-16;
        nav.querySelectorAll('.search-bar, .login-links, .nav-right').forEach(control => {
            const box = control.getBoundingClientRect();
            if (box.width && box.top <= centerY && box.bottom >= centerY) maxX = Math.min(maxX,box.left-14);
        });
        const lower = minX-rectangles[0].left;
        const upper = maxX-rectangles[rectangles.length-1].right;
        if (lower > upper) return;
        const shift = Math.max(lower,Math.min(upper,target-anchor));
        menu.style.setProperty('--navigation-shift',shift+'px');
    }
    if (typeof module !== 'undefined') module.exports = {apiUrl, account};
    if (!root.document) return;
    root.document.addEventListener('DOMContentLoaded', function () {
        const vendor = account(root.localStorage) === 'vendor';
        root.document.querySelectorAll('[data-cart-nav]').forEach(item => { item.hidden = vendor; });
        root.document.querySelectorAll('[data-order-nav]').forEach(item => { item.hidden = false; });
        if (vendor && /(?:^|\/)cart\.html$/.test(root.location.pathname)) {
            root.location.replace('order.html');
            return;
        }
        if (account(root.localStorage)) {
            const links = root.document.getElementById('loginLinks');
            if (links) {
                const logout = root.document.createElement('a');
                logout.href = '#';
                logout.textContent = 'Log Out';
                logout.addEventListener('click', event => {
                    event.preventDefault();
                    ['isRegistered', 'userType', 'CustomerID', 'VendorID', 'orders'].forEach(key => root.localStorage.removeItem(key));
                    root.location.href = 'home.html';
                });
                links.replaceChildren(logout);
            }
        }
        let queued = false;
        const scheduleAlignment = () => {
            if (queued) return;
            queued = true;
            root.requestAnimationFrame(() => { queued = false; alignNavigation(); });
        };
        const logo = root.document.querySelector('header .header-container img');
        if (logo) logo.addEventListener('load',scheduleAlignment);
        root.addEventListener('resize',scheduleAlignment);
        if (root.ResizeObserver) {
            const observer = new root.ResizeObserver(scheduleAlignment);
            root.document.querySelectorAll('header nav, header .login-links, header .nav-right').forEach(element => observer.observe(element));
        }
        scheduleAlignment();
    });
})(typeof window !== 'undefined' ? window : globalThis);
