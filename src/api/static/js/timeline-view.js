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
                    brief_arabic_title: g.brief_arabic_title || ''
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

    function renderTimeline() {
        const docListEl = document.getElementById('document-list');
        if (!docListEl) return;
        docListEl.innerHTML = '';
        
        let displayTimeline = currentTimeline;
        if (currentTenant) {
            displayTimeline = currentTimeline.filter(doc => doc.primary_tenant === currentTenant);
        }
        
        if (displayTimeline.length === 0) {
            docListEl.innerHTML = '<p class="text-xs text-slate-400 p-3 text-center">No documents found for this selection.</p>';
            return;
        }
        
        displayTimeline.forEach(doc => {
            const card = document.createElement('div');
            card.className = 'p-3 bg-white rounded-xl rounded-md border border-slate-200 shadow-2xs hover:shadow-sm hover:border-blue-400 cursor-pointer transition-all flex flex-col gap-2 group relative';
            card.draggable = true;
            card.setAttribute('data-vault-id', doc.vault_id);
            if (typeof window.handleDocDragStart === 'function') {
                card.ondragstart = (e) => window.handleDocDragStart(e, doc, doc.category);
                card.ondragend = (e) => window.handleDocDragEnd(e);
            }
            
            const title = doc.brief_arabic_title || 'Untitled Document';
            const date = (doc.dates && doc.dates.length > 0) ? doc.dates[0] : 'Unknown Date';
            const isManual = Boolean(doc.is_manual);
            const lockBadgeHtml = isManual 
                ? `<span title="Manually assigned - protected from auto-reallocation" class="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded flex items-center gap-1 font-semibold flex-shrink-0">🔒 Pinned</span>`
                : '';
            
            card.innerHTML = `
                <div class="flex justify-between items-start gap-2">
                    <div class="flex items-start gap-1.5 min-w-0 flex-1">
                        <span class="doc-icon-preview p-0.5 rounded text-blue-500 hover:text-blue-700 hover:bg-blue-100 cursor-pointer flex-shrink-0 mt-0.5 transition-colors" title="Quick Preview (or press Space)">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                        </span>
                        <h4 class="text-xs font-semibold text-slate-800 group-hover:text-blue-600 transition-colors line-clamp-2 leading-snug">${title}</h4>
                    </div>
                    <div class="flex items-center gap-1 flex-shrink-0">
                        ${lockBadgeHtml}
                        <button type="button" class="doc-quick-look-btn opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-blue-600 transition-opacity" title="Quick Look (Spacebar)">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                        </button>
                        <button type="button" class="doc-menu-btn opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-700 transition-opacity" data-vault-id="${doc.vault_id}" title="Manage Document (Rename, Move, Copy)">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"/></svg>
                        </button>
                    </div>
                </div>
                <div class="flex items-center justify-between text-[11px] text-slate-500 pt-1.5 border-t border-slate-100">
                    <span class="flex items-center gap-1 font-mono text-[10px] text-slate-400">
                        <svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
                        <span>${date}</span>
                    </span>
                    <span class="bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md font-medium text-[10px] border border-slate-200 truncate max-w-[140px]">${doc.primary_tenant || 'No Tenant'}</span>
                </div>
            `;
            
            const previewIcon = card.querySelector('.doc-icon-preview');
            const quickLookBtn = card.querySelector('.doc-quick-look-btn');
            const menuBtn = card.querySelector('.doc-menu-btn');

            // Zero-click Live Peek in the right panel on hover (250ms debounce)
            if (typeof window.attachPreview === 'function') {
                window.attachPreview(card, doc.vault_id, title, doc);
            }

            if (previewIcon) {
                previewIcon.onclick = (e) => {
                    e.stopPropagation();
                    if (typeof window.setSelectedDoc === 'function') {
                        window.setSelectedDoc(doc, title, card);
                    }
                    if (typeof window.openQuickLook === 'function') {
                        window.openQuickLook(doc.vault_id, title, doc);
                    }
                };
            }

            // Eye button: opens the centered macOS-style Quick Look modal
            if (quickLookBtn) {
                quickLookBtn.onclick = (e) => {
                    e.stopPropagation();
                    if (typeof window.setSelectedDoc === 'function') {
                        window.setSelectedDoc(doc, title, card);
                    }
                    if (typeof window.openQuickLook === 'function') {
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
                        window.openDocModal(doc, doc.category);
                    }
                };
            }

            card.onclick = () => {
                if (typeof window.setSelectedDoc === 'function') {
                    window.setSelectedDoc(doc, title, card);
                }
                openDocument(doc.vault_id, title);
            };
            docListEl.appendChild(card);
        });
    }

    window.loadTimeline = loadTimeline;
    window.renderTimeline = renderTimeline;
})();
