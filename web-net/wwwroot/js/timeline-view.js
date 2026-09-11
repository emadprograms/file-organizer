// ── Timeline View Component ──────────────────────────────────────────────
(function() {
    async function loadTimeline(areaId, houseId) {
        const docListEl = document.getElementById('document-list');
        const statsBadge = document.getElementById('stats-badge');
        if (!docListEl) return;
        docListEl.innerHTML = '<p class="text-xs text-slate-500 p-3">Loading documents...</p>';
        try {
            if (isStaticMode) {
                const stateData = await fetchHouseState(areaId, houseId);
                const groups = getDocumentGroups(stateData);
                currentTimeline = groups.map(g => ({
                    vault_id: g.vault_id || '',
                    primary_tenant: g.primary_tenant || '',
                    dates: g.dates || [],
                    brief_arabic_title: g.brief_arabic_title || '',
                    category: g.folder_path || g.category || '',
                    is_manual: g.is_manual || 0,
                    notes: g.notes || ''
                }));
                currentTimeline.sort((a, b) => {
                    const dateA = (a.dates && a.dates[0] && a.dates[0] !== 'NONE') ? a.dates[0] : '0000-00-00';
                    const dateB = (b.dates && b.dates[0] && b.dates[0] !== 'NONE') ? b.dates[0] : '0000-00-00';
                    return dateB.localeCompare(dateA);
                });
            } else {
                const res = await fetch(`/api/areas/${encodeURIComponent(areaId)}/houses/${encodeURIComponent(houseId)}/timeline`);
                if (!res.ok) throw new Error('Failed to load timeline');
                currentTimeline = await res.json();
            }
            
            const displayTimeline = currentTenant 
                ? currentTimeline.filter(doc => doc.primary_tenant === currentTenant)
                : currentTimeline;

            if (statsBadge) {
                statsBadge.textContent = `${displayTimeline.length} Documents`;
                statsBadge.classList.remove('hidden');
            }
            
            renderTimeline();
        } catch (err) {
            console.error(err);
            docListEl.innerHTML = '<p class="text-xs text-rose-500 p-3">Error loading timeline.</p>';
        }
    }

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

    function handleInlineRename(e, doc, titleEl, currentArea, currentHouse) {
        if (e) {
            if (typeof e.stopPropagation === 'function') e.stopPropagation();
            if (typeof e.preventDefault === 'function') e.preventDefault();
        }

        if (!titleEl || titleEl.querySelector('.inline-rename-input')) {
            return;
        }

        const originalTitle = doc.brief_arabic_title || doc.filename || titleEl.textContent.trim() || 'Untitled Document';
        titleEl.classList.remove('line-clamp-2');
        titleEl.innerHTML = `<input type="text" class="inline-rename-input px-2 py-0.5 text-xs font-normal border border-slate-300 rounded-md bg-white text-slate-800 focus:outline-hidden focus:border-blue-400 focus:ring-1 focus:ring-blue-400/30 w-full min-w-0" value="${escapeHtml(originalTitle)}" />`;

        const input = titleEl.querySelector('.inline-rename-input');
        if (!input) return;

        input.onclick = (ev) => {
            if (ev && typeof ev.stopPropagation === 'function') ev.stopPropagation();
        };
        input.ondblclick = (ev) => {
            if (ev && typeof ev.stopPropagation === 'function') ev.stopPropagation();
        };
        input.onmousedown = (ev) => {
            if (ev && typeof ev.stopPropagation === 'function') ev.stopPropagation();
        };
        input.ondragstart = (ev) => {
            if (ev) {
                if (typeof ev.stopPropagation === 'function') ev.stopPropagation();
                if (typeof ev.preventDefault === 'function') ev.preventDefault();
            }
        };

        input.focus();
        input.select();

        let committed = false;

        const restoreOriginal = () => {
            titleEl.classList.add('line-clamp-2');
            titleEl.textContent = originalTitle;
            titleEl.title = 'Double-click to rename';
        };

        const commitRename = async () => {
            if (committed) return;
            committed = true;

            const newTitle = input.value.trim();
            if (!newTitle || newTitle === originalTitle) {
                restoreOriginal();
                return;
            }

            const area = (doc && doc.area_id)
                || (typeof currentArea !== 'undefined' && currentArea)
                || (typeof window !== 'undefined' && window.currentArea)
                || (typeof window !== 'undefined' && typeof window.getResolvedArea === 'function' ? window.getResolvedArea(doc) : '')
                || (typeof window !== 'undefined' && window.location && window.location.hash ? (window.location.hash.match(/#\/area\/([^/]+)/) ? decodeURIComponent(window.location.hash.match(/#\/area\/([^/]+)/)[1]).replace(/^area_/, '') : '') : '');

            const house = (doc && doc.house_id)
                || (typeof currentHouse !== 'undefined' && currentHouse)
                || (typeof window !== 'undefined' && window.currentHouse)
                || (typeof window !== 'undefined' && typeof window.getResolvedHouse === 'function' ? window.getResolvedHouse(doc) : '')
                || (typeof window !== 'undefined' && window.location && window.location.hash ? (window.location.hash.match(/house\/([^/]+)/) ? decodeURIComponent(window.location.hash.match(/house\/([^/]+)/)[1]) : '') : '');

            try {
                const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(doc.vault_id)}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ arabic_title: newTitle })
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Failed to rename document');
                }

                doc.brief_arabic_title = newTitle;
                doc.filename = newTitle;
                titleEl.classList.add('line-clamp-2');
                titleEl.textContent = newTitle;
                titleEl.title = 'Double-click to rename';

                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' && window.showToast ? window.showToast : null);
                if (toast) toast('Document renamed successfully.');
            } catch (err) {
                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' && window.showToast ? window.showToast : null);
                if (toast) toast('Failed to rename document: ' + err.message, 'error');
                restoreOriginal();
            }
        };

        input.onkeydown = (ev) => {
            if (ev && typeof ev.stopPropagation === 'function') ev.stopPropagation();
            if (ev.key === 'Enter') {
                if (typeof ev.preventDefault === 'function') ev.preventDefault();
                commitRename();
            } else if (ev.key === 'Escape') {
                if (typeof ev.preventDefault === 'function') ev.preventDefault();
                committed = true;
                restoreOriginal();
            }
        };

        input.onblur = () => {
            commitRename();
        };
    }

    function renderTimeline(data) {
        const docListEl = document.getElementById('document-list');
        if (!docListEl) return;
        docListEl.innerHTML = '';

        if (data && typeof currentTimeline !== 'undefined') {
            currentTimeline = data;
        }
        let displayTimeline = data || (typeof currentTimeline !== 'undefined' ? currentTimeline : (typeof window !== 'undefined' ? window.currentTimeline : [])) || [];
        if (typeof currentTenant !== 'undefined' && currentTenant) {
            displayTimeline = displayTimeline.filter(doc => doc.primary_tenant === currentTenant);
        }

        if (displayTimeline.length === 0) {
            const emptyP = document.createElement('p');
            emptyP.className = 'text-xs text-slate-400 p-4 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200';
            emptyP.textContent = 'No documents found for this selection.';
            docListEl.appendChild(emptyP);
            return;
        }

        displayTimeline.forEach(doc => {
            const card = document.createElement('div');
            const hasNotes = Boolean(doc.notes && doc.notes.trim());
            const snippet = hasNotes ? getNoteSnippet(doc.notes) : '';
            const highlightClasses = hasNotes
                ? 'bg-amber-50/80 border-l-4 border-l-amber-400 border border-amber-200/80 hover:border-amber-300 shadow-2xs'
                : 'bg-white border border-slate-200 hover:border-slate-300 shadow-2xs';

            card.className = `p-3 rounded-xl transition-all mb-2 cursor-pointer group ${highlightClasses}`;
            card.draggable = true;
            card.setAttribute('data-vault-id', doc.vault_id);
            if (typeof window.handleDocDragStart === 'function') {
                card.ondragstart = (e) => window.handleDocDragStart(e, doc, doc.category);
                card.ondragend = (e) => window.handleDocDragEnd(e);
            }
            const title = doc.brief_arabic_title || doc.filename || 'Untitled Document';
            const date = (doc.dates && doc.dates[0] && doc.dates[0] !== 'NONE') ? doc.dates[0] : 'No Date';

            const isManual = Boolean(doc.is_manual);
            const lockBadgeHtml = isManual 
                ? `<span title="Manually assigned - protected from auto-reallocation" class="doc-pinned-badge text-[8.5px] bg-amber-50 text-amber-700 border border-amber-200/80 px-1.5 py-0.5 rounded flex items-center gap-0.5 font-medium flex-shrink-0 select-none"><span class="text-[8px] leading-none inline-block">🔒</span><span class="leading-none">Pinned</span></span>`
                : '';
            const noteBadgeHtml = hasNotes 
                ? `<span class="doc-note-badge text-[10px] bg-amber-100 text-amber-800 border border-amber-300/70 px-1.5 py-0.5 rounded flex items-center gap-1 font-semibold flex-shrink-0" title="${escapeHtml(doc.notes)}">📝 ${escapeHtml(snippet)}</span>` 
                : '';
            
            card.innerHTML = `
                <div class="flex justify-between items-start gap-2">
                    <div class="flex items-start gap-1.5 min-w-0 flex-1">
                        <span class="doc-icon-preview p-0.5 rounded text-blue-500 hover:text-blue-700 hover:bg-blue-100 cursor-pointer flex-shrink-0 mt-0.5 transition-colors" title="Document Details & Notes (Spacebar)">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        </span>
                        <h4 class="text-xs font-semibold flex-1 min-w-0 ${hasNotes ? 'text-amber-950' : 'text-slate-800'} group-hover:text-blue-600 transition-colors line-clamp-2 leading-snug doc-title-text cursor-text" title="Double-click to rename">${escapeHtml(title)}</h4>
                    </div>
                    <div class="flex items-center gap-1 flex-shrink-0">
                        ${noteBadgeHtml}
                        ${lockBadgeHtml}
                        <button type="button" class="doc-menu-btn opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-700 transition-opacity" data-vault-id="${escapeHtml(doc.vault_id)}" title="Manage Document (Rename, Move, Copy)">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"/></svg>
                        </button>
                    </div>
                </div>
                <div class="flex items-center justify-between text-[11px] text-slate-500 pt-1.5 border-t border-slate-100">
                    <span class="flex items-center gap-1 font-mono text-[10px] text-slate-400">
                        <svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
                        <span>${escapeHtml(date)}</span>
                    </span>
                    <span class="bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md font-medium text-[10px] border border-slate-200 truncate max-w-[140px]">${escapeHtml(doc.primary_tenant || 'No Tenant')}</span>
                </div>
            `;
            
            const previewIcon = card.querySelector('.doc-icon-preview');
            const menuBtn = card.querySelector('.doc-menu-btn');
            const titleH4 = card.querySelector('.doc-title-text');

            if (titleH4) {
                titleH4.ondblclick = (e) => {
                    handleInlineRename(e, doc, titleH4, (typeof currentArea !== 'undefined' ? currentArea : (typeof window !== 'undefined' ? window.currentArea : '')), (typeof currentHouse !== 'undefined' ? currentHouse : (typeof window !== 'undefined' ? window.currentHouse : '')));
                };
            }

            // Zero-click Live Peek in the right panel on hover (250ms debounce)
            if (typeof window.attachPreview === 'function') {
                window.attachPreview(card, doc.vault_id, title, doc);
            }

            // Info icon on left before name: opens Document Inspector & Notes modal
            if (previewIcon) {
                previewIcon.onclick = (e) => {
                    e.stopPropagation();
                    if (typeof window.setSelectedDoc === 'function') {
                        window.setSelectedDoc(doc, title, card);
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
                    if (typeof window.openDocDropdownMenu === 'function') {
                        window.openDocDropdownMenu(e, doc, doc.category, menuBtn);
                    } else if (typeof window.openDocModal === 'function') {
                        window.openDocModal(doc, doc.category);
                    }
                };
            }

            card.onclick = () => {
                const currentDocTitle = doc.brief_arabic_title || doc.filename || title;
                if (typeof window !== 'undefined' && typeof window.setSelectedDoc === 'function') {
                    window.setSelectedDoc(doc, currentDocTitle, card);
                } else if (typeof setSelectedDoc === 'function') {
                    setSelectedDoc(doc, currentDocTitle, card);
                }
                if (typeof openDocument === 'function') {
                    openDocument(doc.vault_id, currentDocTitle);
                } else if (typeof window !== 'undefined' && typeof window.openDocument === 'function') {
                    window.openDocument(doc.vault_id, currentDocTitle);
                }
            };
            docListEl.appendChild(card);
        });
    }

    if (typeof window !== 'undefined') {
        window.loadTimeline = loadTimeline;
        window.renderTimeline = renderTimeline;
        window.handleInlineRenameTimeline = handleInlineRename;
    }

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            loadTimeline,
            renderTimeline,
            handleInlineRename,
        };
    }
})();
