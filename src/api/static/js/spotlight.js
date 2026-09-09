// ── Spotlight Command Palette Controller ──────────────────────────────────
(function() {
    let spotlightModal = null;
    let spotlightCard = null;
    let searchInput = null;
    let searchResults = null;
    let btnSearchTrigger = null;
    let btnSpotlightClose = null;
    let spotlightResultCount = null;

    let searchDebounceTimer = null;
    let activeResultIndex = -1;
    let currentResultItems = [];

    function initSpotlight() {
        spotlightModal = document.getElementById('spotlight-modal');
        spotlightCard = document.getElementById('spotlight-card');
        searchInput = document.getElementById('search-input');
        searchResults = document.getElementById('search-results');
        btnSearchTrigger = document.getElementById('btn-search-trigger');
        btnSpotlightClose = document.getElementById('btn-spotlight-close');
        spotlightResultCount = document.getElementById('spotlight-result-count');

        if (!spotlightModal || !searchInput) return;

        // Trigger button in top-bar
        if (btnSearchTrigger) {
            btnSearchTrigger.addEventListener('click', (e) => {
                e.preventDefault();
                openSpotlight();
            });
        }

        // Close button inside modal
        if (btnSpotlightClose) {
            btnSpotlightClose.addEventListener('click', (e) => {
                e.preventDefault();
                closeSpotlight();
            });
        }

        // Close on backdrop click (outside card)
        spotlightModal.addEventListener('click', (e) => {
            if (e.target === spotlightModal) {
                closeSpotlight();
            }
        });

        // Search input input event
        searchInput.addEventListener('input', () => {
            clearTimeout(searchDebounceTimer);
            const q = searchInput.value.trim();
            if (!q) {
                renderEmptyState();
                return;
            }
            searchDebounceTimer = setTimeout(() => executeSearch(q), 150);
        });

        // Search input keyboard handling
        searchInput.addEventListener('keydown', handleKeyNavigation);

        // Global Cmd+K / Ctrl+K & Escape shortcuts
        document.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                if (spotlightModal.classList.contains('hidden')) {
                    openSpotlight();
                } else {
                    closeSpotlight();
                }
            } else if (e.key === 'Escape' && !spotlightModal.classList.contains('hidden')) {
                e.preventDefault();
                closeSpotlight();
            }
        });
    }

    function openSpotlight() {
        if (!spotlightModal) return;
        spotlightModal.classList.remove('hidden');
        if (searchResults) searchResults.classList.remove('hidden');
        
        requestAnimationFrame(() => {
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        });

        const q = searchInput ? searchInput.value.trim() : '';
        if (q) {
            executeSearch(q);
        } else {
            renderEmptyState();
        }
    }

    function closeSpotlight() {
        if (!spotlightModal) return;
        spotlightModal.classList.add('hidden');
        if (searchResults) searchResults.classList.add('hidden');
        if (searchInput) searchInput.blur();
        activeResultIndex = -1;
    }

    function renderEmptyState() {
        if (!searchResults) return;
        activeResultIndex = -1;
        currentResultItems = [];
        searchResults.innerHTML = `
            <div class="py-10 text-center text-slate-400">
                <div class="w-10 h-10 mx-auto mb-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-400">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                </div>
                <p class="text-xs font-semibold text-slate-600">Spotlight Search</p>
                <p class="text-[11px] text-slate-400 mt-0.5">Search by house number (e.g. 500), tenant name, or document title.</p>
            </div>
        `;
        if (spotlightResultCount) spotlightResultCount.textContent = '';
    }

    async function executeSearch(q) {
        if (!searchResults) return;
        searchResults.innerHTML = `
            <div class="py-10 text-center text-slate-400">
                <div class="inline-block animate-spin w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full mb-2"></div>
                <p class="text-xs">Searching database...</p>
            </div>
        `;

        try {
            let results = [];
            if (isStaticMode) {
                // Static JSON search fallback
                if (!searchIndexData) {
                    try {
                        const sRes = await fetch('./search_index.json');
                        if (sRes.ok) searchIndexData = await sRes.json();
                    } catch (e) {
                        console.error('Failed to load search_index.json', e);
                    }
                }
                if (searchIndexData) {
                    const qLow = q.toLowerCase();
                    (searchIndexData.houses || []).forEach(h => {
                        if (h.house_dir_name.toLowerCase().includes(qLow)) {
                            results.push({
                                id: h.house_dir_name,
                                type: 'house',
                                title: h.house_dir_name,
                                subtitle: `House in ${h.area_name}`,
                                url: `/#/area/${encodeURIComponent(h.area_name)}/house/${encodeURIComponent(h.house_dir_name)}`
                            });
                        }
                    });
                    (searchIndexData.tenants || []).forEach(t => {
                        if (t.tenant_name.toLowerCase().includes(qLow)) {
                            results.push({
                                id: `${t.house_dir_name}_${t.tenant_name}`,
                                type: 'tenant',
                                title: t.tenant_name,
                                subtitle: `Tenant in ${t.house_dir_name}`,
                                url: `/#/area/${encodeURIComponent(t.area_name)}/house/${encodeURIComponent(t.house_dir_name)}/tenant/${encodeURIComponent(t.house_dir_name + '_' + t.tenant_name)}`
                            });
                        }
                    });
                    (searchIndexData.documents || []).forEach(d => {
                        if ((d.content && d.content.includes(qLow)) || (d.title_field && d.title_field.includes(qLow))) {
                            results.push({
                                id: `${d.house_dir_name}_doc_${d.vault_id}`,
                                type: 'document',
                                title: d.doc_title,
                                subtitle: `Document in ${d.house_dir_name}`,
                                url: `/#/area/${encodeURIComponent(d.area_name)}/house/${encodeURIComponent(d.house_dir_name)}`
                            });
                        }
                    });
                }
            } else {
                const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
                if (!res.ok) throw new Error('Search failed');
                results = await res.json();
            }

            renderGroupedResults(results);
        } catch (err) {
            searchResults.innerHTML = `
                <div class="py-8 text-center text-rose-500 text-xs">
                    <p class="font-semibold">Search failed</p>
                    <p class="text-[11px] text-rose-400 mt-1">${err.message}</p>
                </div>
            `;
            if (spotlightResultCount) spotlightResultCount.textContent = '';
        }
    }

    function renderGroupedResults(results) {
        if (!searchResults) return;
        if (!results || results.length === 0) {
            searchResults.innerHTML = `
                <div class="py-10 text-center text-slate-400">
                    <p class="text-xs font-semibold text-slate-600">No results found</p>
                    <p class="text-[11px] text-slate-400 mt-0.5">Try searching with a different house number, tenant, or keyword.</p>
                </div>
            `;
            if (spotlightResultCount) spotlightResultCount.textContent = '0 results';
            activeResultIndex = -1;
            currentResultItems = [];
            return;
        }

        const houses = results.filter(r => r.type === 'house');
        const tenants = results.filter(r => r.type === 'tenant');
        const documents = results.filter(r => r.type === 'document');

        searchResults.innerHTML = '';
        currentResultItems = [];

        if (spotlightResultCount) {
            spotlightResultCount.textContent = `${results.length} results`;
        }

        // Helper to append a section
        function createSection(title, iconSvg, count, items, renderItemFn) {
            if (items.length === 0) return;

            const sectionEl = document.createElement('div');
            sectionEl.className = 'pt-2 first:pt-0';

            const headerEl = document.createElement('div');
            headerEl.className = 'px-3 py-1.5 flex items-center justify-between text-[11px] font-bold tracking-wider text-slate-400 uppercase';
            headerEl.innerHTML = `
                <div class="flex items-center gap-1.5">
                    ${iconSvg}
                    <span>${title}</span>
                </div>
                <span class="bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded text-[10px] font-medium">${count}</span>
            `;
            sectionEl.appendChild(headerEl);

            const listEl = document.createElement('div');
            listEl.className = 'mt-1 space-y-1';

            items.forEach(item => {
                const itemEl = renderItemFn(item);
                listEl.appendChild(itemEl);
                currentResultItems.push({ element: itemEl, data: item });
            });

            sectionEl.appendChild(listEl);
            searchResults.appendChild(sectionEl);
        }

        // 1. Houses Section
        createSection(
            'Houses',
            `<svg class="w-3.5 h-3.5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>`,
            houses.length,
            houses,
            (h) => {
                const a = document.createElement('a');
                a.href = h.url;
                a.className = 'spotlight-result-item block p-2.5 rounded-xl hover:bg-blue-50/70 border border-transparent hover:border-blue-200 transition-all group cursor-pointer';
                a.innerHTML = `
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2.5 min-w-0">
                            <div class="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-xs flex-shrink-0 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                                🏠
                            </div>
                            <div class="min-w-0">
                                <div class="font-bold text-xs text-slate-800 group-hover:text-blue-600 transition-colors">${h.title}</div>
                                <div class="text-[11px] text-slate-400 truncate mt-0.5">${h.subtitle || ''}</div>
                            </div>
                        </div>
                        ${h.extra_info ? `<span class="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200 flex-shrink-0">${h.extra_info}</span>` : ''}
                    </div>
                `;
                a.onclick = (e) => {
                    closeSpotlight();
                };
                return a;
            }
        );

        // 2. Tenants Section
        createSection(
            'Tenants',
            `<svg class="w-3.5 h-3.5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>`,
            tenants.length,
            tenants,
            (t) => {
                const a = document.createElement('a');
                a.href = t.url;
                a.className = 'spotlight-result-item block p-2.5 rounded-xl hover:bg-emerald-50/70 border border-transparent hover:border-emerald-200 transition-all group cursor-pointer';
                a.innerHTML = `
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2.5 min-w-0">
                            <div class="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold text-xs flex-shrink-0 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
                                👤
                            </div>
                            <div class="min-w-0">
                                <div class="font-bold text-xs text-slate-800 group-hover:text-emerald-700 transition-colors">${t.title}</div>
                                <div class="text-[11px] text-slate-400 truncate mt-0.5">${t.subtitle || ''}</div>
                            </div>
                        </div>
                        ${t.extra_info ? `<span class="text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md flex-shrink-0">${t.extra_info}</span>` : ''}
                    </div>
                `;
                a.onclick = (e) => {
                    closeSpotlight();
                };
                return a;
            }
        );

        // 3. Documents Section (with hierarchical breadcrumbs & direct PDF view)
        createSection(
            'Documents',
            `<svg class="w-3.5 h-3.5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>`,
            documents.length,
            documents,
            (d) => {
                const a = document.createElement('a');
                a.href = d.url;
                a.className = 'spotlight-result-item block p-2.5 rounded-xl hover:bg-indigo-50/70 border border-transparent hover:border-indigo-200 transition-all group cursor-pointer';
                
                const lockBadge = d.is_manual ? `<span title="Manually assigned" class="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.2 rounded font-semibold flex-shrink-0">🔒</span>` : '';
                const dateBadge = d.date ? `<span class="text-[10px] font-mono text-slate-400 bg-slate-50 border border-slate-200 px-1.5 py-0.5 rounded flex-shrink-0">${d.date}</span>` : '';

                a.innerHTML = `
                    <div class="flex items-start justify-between gap-2">
                        <div class="flex items-start gap-2.5 min-w-0 flex-1">
                            <div class="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-xs flex-shrink-0 mt-0.5 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                                📄
                            </div>
                            <div class="min-w-0 flex-1">
                                <div class="font-bold text-xs text-slate-800 group-hover:text-indigo-700 transition-colors leading-snug">${d.title}</div>
                                <div class="flex items-center gap-1.5 text-[11px] text-slate-400 font-medium truncate mt-1">
                                    <span class="truncate text-slate-500 font-semibold">${d.subtitle || ''}</span>
                                </div>
                            </div>
                        </div>
                        <div class="flex items-center gap-1.5 flex-shrink-0">
                            ${lockBadge}
                            ${dateBadge}
                        </div>
                    </div>
                `;

                a.onclick = (e) => {
                    closeSpotlight();
                    if (d.vault_id && typeof window.openDocument === 'function') {
                        // After hash route navigation, trigger document opening
                        setTimeout(() => {
                            window.openDocument(d.vault_id, d.title);
                        }, 120);
                    }
                };
                return a;
            }
        );

        // Auto-select first result
        if (currentResultItems.length > 0) {
            setActiveResultIndex(0);
        }
    }

    function setActiveResultIndex(index) {
        if (currentResultItems.length === 0) {
            activeResultIndex = -1;
            return;
        }

        // Clamp index
        if (index < 0) index = currentResultItems.length - 1;
        if (index >= currentResultItems.length) index = 0;

        activeResultIndex = index;

        currentResultItems.forEach((item, idx) => {
            if (idx === activeResultIndex) {
                item.element.classList.add('bg-blue-50/90', 'border-blue-300', 'ring-1', 'ring-blue-400/30');
                item.element.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            } else {
                item.element.classList.remove('bg-blue-50/90', 'border-blue-300', 'ring-1', 'ring-blue-400/30');
            }
        });
    }

    function handleKeyNavigation(e) {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setActiveResultIndex(activeResultIndex + 1);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setActiveResultIndex(activeResultIndex - 1);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (activeResultIndex >= 0 && activeResultIndex < currentResultItems.length) {
                currentResultItems[activeResultIndex].element.click();
            }
        } else if (e.key === 'Escape') {
            e.preventDefault();
            closeSpotlight();
        }
    }

    // Expose global functions
    window.openSpotlight = openSpotlight;
    window.closeSpotlight = closeSpotlight;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSpotlight);
    } else {
        initSpotlight();
    }
})();
