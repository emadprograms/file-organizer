// ── Categories / Folder Hierarchy Component ──────────────────────────────
(function() {
    const FOLDER_PREFIXES = {
        "بيانات شخصية": "01",
        "عقد الإيجار": "02",
        "سند أمر": "03",
        "إشعار": "04",
        "مخالصة": "05",
        "سند قبض": "06",
        "استقطاع": "07",
        "إلغاء استقطاع": "08",
        "حكم قضائي": "09",
        "طلب إخلاء": "10",
        "مستندات أخرى": "99"
    };

    async function loadCategories(areaId, houseId) {
        const docListEl = document.getElementById('document-list');
        const statsBadge = document.getElementById('stats-badge');
        if (!docListEl) return;
        docListEl.innerHTML = '<p class="text-xs text-slate-500 p-3">Loading categories...</p>';
        try {
            if (isStaticMode) {
                const stateData = await fetchHouseState(areaId, houseId);
                const groups = getDocumentGroups(stateData);
                const catMap = {};
                
                groups.forEach(g => {
                    const tenant = g.primary_tenant;
                    const catRaw = g.folder_path || g.category;
                    if (tenant && catRaw) {
                        const prefix = FOLDER_PREFIXES[catRaw] || '';
                        const catNumbered = prefix ? `${prefix} - ${catRaw}` : catRaw;
                        const key = `${tenant}:::${catNumbered}`;
                        if (!catMap[key]) {
                            catMap[key] = {
                                tenant: tenant,
                                name: catNumbered,
                                documents: []
                            };
                        }
                        catMap[key].documents.push({
                            vault_id: g.vault_id || '',
                            filename: g.filename || '',
                            start_page: g.start_page || 1,
                            end_page: g.end_page || 1,
                            date: (g.dates && g.dates[0]) ? g.dates[0] : '',
                            tenant: tenant,
                            brief_arabic_title: g.brief_arabic_title || '',
                            is_manual: g.is_manual || 0,
                            category: catNumbered
                        });
                    }
                });
                
                currentCategories = Object.values(catMap).map(c => ({
                    tenant: c.tenant,
                    name: c.name,
                    document_count: c.documents.length,
                    documents: c.documents
                }));
            } else {
                const res = await fetch(`/api/areas/${encodeURIComponent(areaId)}/houses/${encodeURIComponent(houseId)}/categories`);
                if (!res.ok) throw new Error('Failed to load categories');
                currentCategories = await res.json();
            }
            
            const totalDocs = currentCategories.reduce((sum, cat) => sum + cat.document_count, 0);
            if (statsBadge) {
                statsBadge.textContent = `${currentCategories.length} Categories (${totalDocs} Docs)`;
                statsBadge.classList.remove('hidden');
            }
            
            renderCategories();
        } catch (err) {
            console.error(err);
            docListEl.innerHTML = '<p class="text-xs text-rose-500 p-3">Error loading categories.</p>';
        }
    }

    function renderCategories() {
        const docListEl = document.getElementById('document-list');
        if (!docListEl) return;
        docListEl.innerHTML = '';

        if (currentTenant) {
            const banner = document.createElement('div');
            banner.className = 'tenant-breadcrumb-banner bg-blue-50/60 border border-blue-200/80 rounded-xl p-2.5 mb-3 flex items-center justify-between gap-2 shadow-2xs';
            banner.innerHTML = `
                <div class="flex items-center gap-2 min-w-0">
                    <div class="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs flex-shrink-0">
                        👤
                    </div>
                    <div class="min-w-0">
                        <h3 class="text-xs font-bold text-slate-900 truncate">${currentTenant}</h3>
                        <p class="text-[10px] text-blue-600 font-medium truncate">سجل مستندات المستأجر</p>
                    </div>
                </div>
                <button id="btn-back-to-tenants-list" type="button" class="flex-shrink-0 text-xs font-semibold text-blue-700 hover:text-blue-900 bg-white hover:bg-blue-50 border border-blue-200 px-2.5 py-1 rounded-lg transition-all shadow-2xs flex items-center gap-1 cursor-pointer" title="العودة لسجل المستأجرين">
                    <svg class="w-3.5 h-3.5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
                    <span>← Back to Tenants</span>
                </button>
            `;
            const bannerBackBtn = banner.querySelector('#btn-back-to-tenants-list');
            if (bannerBackBtn) {
                bannerBackBtn.onclick = (e) => {
                    e.preventDefault();
                    if (currentArea && currentHouse) {
                        window.location.hash = `#/area/${encodeURIComponent(currentArea)}/house/${encodeURIComponent(currentHouse)}`;
                    }
                };
            }
            docListEl.appendChild(banner);
        }
        
        let displayCategories = [];
        
        if (currentTenant) {
            displayCategories = currentCategories.filter(cat => cat.tenant === currentTenant);
        } else {
            const agg = {};
            currentCategories.forEach(cat => {
                if (!agg[cat.name]) {
                    agg[cat.name] = { count: 0, documents: [] };
                }
                agg[cat.name].count += cat.document_count;
                if (cat.documents) {
                    agg[cat.name].documents = agg[cat.name].documents.concat(cat.documents);
                }
            });
            for (const [name, data] of Object.entries(agg)) {
                displayCategories.push({ name: name, document_count: data.count, documents: data.documents });
            }
        }
        
        displayCategories.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
        
        if (displayCategories.length === 0) {
            const emptyP = document.createElement('p');
            emptyP.className = 'text-xs text-slate-400 p-4 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200';
            emptyP.textContent = 'No folders found for this selection.';
            docListEl.appendChild(emptyP);
            return;
        }
        
        displayCategories.forEach(cat => {
            const card = document.createElement('div');
            card.className = 'p-3 bg-white rounded-xl border border-slate-200 shadow-2xs hover:border-slate-300 transition-all mb-2 cursor-pointer category-folder-card';
            card.setAttribute('data-category-name', cat.name);
            
            if (typeof window.handleCategoryDragOver === 'function') {
                card.ondragover = (e) => window.handleCategoryDragOver(e, card);
                card.ondragleave = (e) => window.handleCategoryDragLeave(e, card);
                card.ondrop = (e) => window.handleCategoryDrop(e, cat.name, card);
            }

            card.innerHTML = `
                <div class="flex justify-between items-center">
                    <div class="flex items-center gap-2 min-w-0">
                        <div class="w-6 h-6 rounded-lg bg-blue-50 text-blue-600 border border-blue-100 flex items-center justify-center flex-shrink-0">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                        </div>
                        <h4 class="text-xs font-semibold text-slate-800 truncate">${cat.name}</h4>
                    </div>
                    <span class="bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full text-[10px] font-bold border border-slate-200 flex-shrink-0">${cat.document_count} Documents</span>
                </div>
                <div class="category-docs hidden mt-2.5 pt-2.5 border-t border-slate-100 space-y-1">
                </div>
            `;
            
            if (cat.documents && cat.documents.length > 0) {
                const docsContainer = card.querySelector('.category-docs');
                cat.documents.forEach(doc => {
                    const docEl = document.createElement('div');
                    docEl.className = 'text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-2.5 py-1.5 rounded-lg cursor-pointer transition-colors flex items-center justify-between gap-2 font-medium group/doc';
                    docEl.draggable = true;
                    docEl.setAttribute('data-vault-id', doc.vault_id);
                    if (typeof window.handleDocDragStart === 'function') {
                        docEl.ondragstart = (e) => window.handleDocDragStart(e, doc, cat.name);
                        docEl.ondragend = (e) => window.handleDocDragEnd(e);
                    }

                    const title = doc.brief_arabic_title || doc.filename || 'Document';
                    const isManual = Boolean(doc.is_manual);
                    const lockIcon = isManual ? '<span title="Manually assigned - protected from auto-reallocation" class="text-[10px] text-amber-600 flex-shrink-0">🔒</span>' : '';

                    docEl.innerHTML = `
                        <div class="flex items-center gap-2 min-w-0 flex-1">
                            <svg class="w-3.5 h-3.5 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                            <span class="truncate">${title}</span>
                            ${lockIcon}
                        </div>
                        <button class="doc-menu-btn opacity-0 group-hover/doc:opacity-100 p-1 hover:bg-blue-100 rounded text-slate-400 hover:text-slate-700 transition-opacity flex-shrink-0" data-vault-id="${doc.vault_id}" title="Manage Document (Rename, Move, Copy)">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"/></svg>
                        </button>
                    `;

                    const menuBtn = docEl.querySelector('.doc-menu-btn');
                    if (menuBtn) {
                        menuBtn.onclick = (e) => {
                            e.stopPropagation();
                            if (typeof window.openDocModal === 'function') {
                                window.openDocModal(doc, cat.name);
                            }
                        };
                    }

                    docEl.onclick = (e) => {
                        e.stopPropagation();
                        openDocument(doc.vault_id, title);
                    };
                    attachPreview(docEl, doc.vault_id, title);
                    docsContainer.appendChild(docEl);
                });
            }
            
            card.onclick = () => {
                const docsContainer = card.querySelector('.category-docs');
                if (docsContainer) {
                    docsContainer.classList.toggle('hidden');
                }
            };
            docListEl.appendChild(card);
        });
    }

    window.loadCategories = loadCategories;
    window.renderCategories = renderCategories;
    window.FOLDER_PREFIXES = FOLDER_PREFIXES;
})();
