// ── Categories / Folder Hierarchy Component ──────────────────────────────
(function() {
    const FOLDER_PREFIXES = {
        "بيانات أساسية": "01",
        "بيانات شخصية": "02",
        "أمر تخصيص": "03",
        "محضر تسليم مفتاح": "04",
        "عقود": "05",
        "كهرباء وماء": "06",
        "استقطاع إيجار": "07",
        "وقف استقطاع بدل": "08",
        "إشعارات": "09",
        "صيانة": "10",
        "صور ومعاينات": "11",
        "تعديلات": "12",
        "رسائل متنوعة": "13"
    };

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function getNoteSnippet(notes, maxLen = 14) {
        if (typeof window.getNoteSnippet === 'function') return window.getNoteSnippet(notes, maxLen);
        if (!notes || typeof notes !== 'string') return '';
        const clean = notes.trim().replace(/\s+/g, ' ');
        if (!clean) return '';
        if (clean.length <= maxLen) return clean;
        return clean.substring(0, maxLen).trim() + '…';
    }

    function isStandardCategoryName(name) {
        if (!name) return false;
        const clean = name.trim();
        if (FOLDER_PREFIXES[clean]) return true;
        for (const [folderName, prefix] of Object.entries(FOLDER_PREFIXES)) {
            if (clean === `${prefix} - ${folderName}` || clean.endsWith(folderName)) return true;
        }
        return false;
    }

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
                            notes: g.notes || '',
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
            // Tenant name is now shown in the header breadcrumb; back nav is in the tab bar
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
            card.className = 'p-3 bg-white rounded-xl border border-slate-200 shadow-2xs hover:border-slate-300 transition-all mb-2 cursor-pointer category-folder-card group/card';
            card.setAttribute('data-category-name', cat.name);
            
            if (typeof window.handleCategoryDragOver === 'function') {
                card.ondragover = (e) => window.handleCategoryDragOver(e, card);
                card.ondragleave = (e) => window.handleCategoryDragLeave(e, card);
                card.ondrop = (e) => window.handleCategoryDrop(e, cat.name, card);
            }

            const isCustomFolder = !isStandardCategoryName(cat.name);
            const deleteFolderBtn = isCustomFolder
                ? `<button type="button" class="btn-delete-folder opacity-0 group-hover/card:opacity-100 p-1 hover:bg-rose-50 rounded text-slate-400 hover:text-rose-600 transition-all text-xs flex-shrink-0" title="Delete Custom Folder" data-category-name="${escapeHtml(cat.name)}">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>`
                : '';

            const hasNotedDoc = Boolean(cat.documents && cat.documents.some(d => d.notes && d.notes.trim()));
            const noteFolderBadge = hasNotedDoc 
                ? '<span class="bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full text-[10px] font-bold border border-amber-300/80 flex-shrink-0" title="Contains documents with notes">📝 Notes</span>'
                : '';
            const docsContainerClasses = hasNotedDoc 
                ? 'category-docs mt-2.5 pt-2.5 border-t border-slate-100 space-y-1'
                : 'category-docs hidden mt-2.5 pt-2.5 border-t border-slate-100 space-y-1';

            card.innerHTML = `
                <div class="flex justify-between items-center">
                    <div class="flex items-center gap-2 min-w-0">
                        <div class="w-6 h-6 rounded-lg bg-blue-50 text-blue-600 border border-blue-100 flex items-center justify-center flex-shrink-0">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                        </div>
                        <h4 class="text-xs font-semibold text-slate-800 truncate">${escapeHtml(cat.name)}</h4>
                    </div>
                    <div class="flex items-center gap-1.5 flex-shrink-0">
                        ${noteFolderBadge}
                        <span class="bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full text-[10px] font-bold border border-slate-200 flex-shrink-0">${cat.document_count} Documents</span>
                        ${deleteFolderBtn}
                    </div>
                </div>
                <div class="${docsContainerClasses}">
                </div>
            `;
            
            if (cat.documents && cat.documents.length > 0) {
                const docsContainer = card.querySelector('.category-docs');
                cat.documents.forEach(doc => {
                    const docEl = document.createElement('div');
                    const hasNotes = Boolean(doc.notes && doc.notes.trim());
                    const snippet = hasNotes ? getNoteSnippet(doc.notes) : '';
                    const noteBadge = hasNotes 
                        ? `<span class="doc-note-badge inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded font-medium bg-amber-100 text-amber-800 border border-amber-300/60 flex-shrink-0" title="${escapeHtml(doc.notes)}">📝 ${escapeHtml(snippet)}</span>` 
                        : '';

                    const highlightClasses = hasNotes
                        ? 'bg-amber-50/80 border-l-4 border-l-amber-400 border border-amber-200/80 text-amber-900 hover:bg-amber-100/70 hover:border-amber-300 shadow-2xs'
                        : 'text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50';

                    docEl.className = `${highlightClasses} px-2.5 py-1.5 rounded-lg cursor-pointer transition-all flex items-center justify-between gap-2 font-medium group/doc`;
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
                            <span class="doc-icon-preview p-0.5 rounded text-blue-500 hover:text-blue-700 hover:bg-blue-100 cursor-pointer flex-shrink-0 transition-colors" title="Document Details & Notes (Spacebar)">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                            </span>
                            <span class="truncate ${hasNotes ? 'text-amber-950 font-semibold' : 'text-slate-800'}">${title}</span>
                            ${lockIcon}
                            ${noteBadge}
                        </div>
                        <div class="flex items-center gap-1 flex-shrink-0">
                            <button type="button" class="doc-menu-btn opacity-0 group-hover/doc:opacity-100 p-1 hover:bg-blue-100 rounded text-slate-400 hover:text-slate-700 transition-opacity" data-vault-id="${doc.vault_id}" title="Manage Document (Rename, Move, Copy)">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"/></svg>
                            </button>
                        </div>
                    `;

                    const previewIcon = docEl.querySelector('.doc-icon-preview');
                    const menuBtn = docEl.querySelector('.doc-menu-btn');

                    // Zero-click Live Peek in the right panel on hover (250ms debounce)
                    if (typeof window.attachPreview === 'function') {
                        window.attachPreview(docEl, doc.vault_id, title, doc);
                    }

                    // Info icon on left before name: opens Document Inspector & Notes modal
                    if (previewIcon) {
                        previewIcon.onclick = (e) => {
                            e.stopPropagation();
                            if (typeof window.setSelectedDoc === 'function') {
                                window.setSelectedDoc(doc, title, docEl);
                            }
                            if (typeof window.openDocInspector === 'function') {
                                window.openDocInspector(doc.vault_id, title, doc);
                            } else if (typeof window.openQuickLook === 'function') {
                                window.openQuickLook(doc.vault_id, title, doc);
                            }
                        };
                    }

                    // 3-dot Menu: hover immediately cancels any pending peek so action menu is 100% free
                    if (menuBtn) {
                        menuBtn.onmouseenter = () => {
                            if (typeof window.cancelPeek === 'function') {
                                window.cancelPeek();
                            }
                        };
                        menuBtn.onclick = (e) => {
                            e.stopPropagation();
                            if (typeof window.cancelPeek === 'function') {
                                window.cancelPeek();
                            }
                            if (typeof window.openDocModal === 'function') {
                                window.openDocModal(doc, cat.name);
                            }
                        };
                    }

                    docEl.onclick = (e) => {
                        e.stopPropagation();
                        if (typeof window.setSelectedDoc === 'function') {
                            window.setSelectedDoc(doc, title, docEl);
                        }
                        openDocument(doc.vault_id, title);
                    };
                    docsContainer.appendChild(docEl);
                });
            }
            
            const deleteBtn = card.querySelector('.btn-delete-folder');
            if (deleteBtn) {
                deleteBtn.onclick = async (e) => {
                    e.stopPropagation();
                    const catName = cat.name;
                    if (!window.confirm(`Are you sure you want to delete custom folder "${catName}"?\nAny documents in it will be moved to "13 - رسائل متنوعة".`)) {
                        return;
                    }
                    try {
                        const res = await fetch(`/api/areas/${encodeURIComponent(currentArea)}/houses/${encodeURIComponent(currentHouse)}/categories/${encodeURIComponent(catName)}`, {
                            method: 'DELETE'
                        });
                        if (!res.ok) {
                            const err = await res.json().catch(() => ({}));
                            throw new Error(err.detail || 'Failed to delete folder');
                        }
                        showToast(`Folder "${catName}" deleted successfully.`);
                        if (typeof window.refreshCurrentTab === 'function') {
                            await window.refreshCurrentTab(currentArea, currentHouse);
                        }
                    } catch (err) {
                        showToast(err.message, 'error');
                    }
                };
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
