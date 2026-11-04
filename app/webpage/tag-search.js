(function (root) {
    'use strict';
    function resultUrl(tag) {
        return 'search_tag.html?tag=' + encodeURIComponent(tag);
    }
    function matchingTags(tags, query) {
        const value = query.trim().toLocaleLowerCase();
        return tags.filter(tag => tag.toLocaleLowerCase().includes(value));
    }
    function initTagSearch() {
        root.document.querySelectorAll('[data-tag-search]').forEach(container => {
            if (container.dataset.tagReady) return;
            container.dataset.tagReady = 'true';
            const input = container.querySelector('[data-tag-input]');
            const panel = container.querySelector('[data-tag-options]');
            let tags = [], loading = true, failed = false;
            const close = () => { panel.hidden = true; input.setAttribute('aria-expanded', 'false'); };
            const select = tag => {
                input.value = tag;
                close();
                root.location.href = resultUrl(tag);
            };
            function render() {
                panel.replaceChildren();
                const matches = matchingTags(tags, input.value);
                if (loading || failed || !matches.length) {
                    const status = root.document.createElement('p');
                    status.className = 'tag-search-status';
                    status.textContent = loading ? 'Loading tags...' : failed ? 'Unable to load tags. Refresh to retry.' : 'No matching tags.';
                    panel.append(status);
                    return;
                }
                matches.forEach(tag => {
                    const option = root.document.createElement('button');
                    option.type = 'button';
                    option.className = 'tag-option';
                    option.textContent = tag;
                    option.addEventListener('click', () => select(tag));
                    option.addEventListener('keydown', event => {
                        if (event.key === 'Escape') { close(); input.focus(); close(); }
                    });
                    panel.append(option);
                });
            }
            const open = () => {
                render(); panel.hidden = false; input.setAttribute('aria-expanded', 'true');
            };
            input.addEventListener('focus', open);
            input.addEventListener('input', open);
            input.addEventListener('keydown', event => {
                if (event.key === 'Escape') close();
                if (event.key === 'ArrowDown') {
                    event.preventDefault(); open();
                    const first = panel.querySelector('button');
                    if (first) first.focus();
                }
                if (event.key === 'Enter') {
                    event.preventDefault();
                    const exact = tags.find(tag => tag.toLocaleLowerCase() === input.value.trim().toLocaleLowerCase());
                    if (exact) select(exact); else open();
                }
            });
            container.addEventListener('focusout', event => {
                if (!container.contains(event.relatedTarget)) close();
            });
            root.document.addEventListener('click', event => {
                if (!container.contains(event.target)) close();
            });
            root.fetch(root.shopApi('/api/get_tags'))
                .then(response => {
                    if (!response.ok) throw new Error('Unable to load tags');
                    return response.json();
                })
                .then(data => {
                    if (!data.success || !Array.isArray(data.tags)) throw new Error('Invalid tags');
                    tags = data.tags.filter(tag => typeof tag === 'string');
                })
                .catch(() => { failed = true; })
                .finally(() => { loading = false; if (!panel.hidden) render(); });
        });
    }
    root.initTagSearch = initTagSearch;
    if (typeof module !== 'undefined') module.exports = {resultUrl, matchingTags, initTagSearch};
    if (root.document) root.document.addEventListener('DOMContentLoaded', initTagSearch);
})(typeof window !== 'undefined' ? window : globalThis);
