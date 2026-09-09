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

    function renderTimeline() {
        const docListEl = document.getElementById('document-list');
        if (!docListEl) return;
        docListEl.innerHTML = '';

        let displayTimeline = currentTimeline || [];
        if (currentTenant) {
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
            const title = doc.brief_arabic_title || 'Untitled Document';
            const date = (doc.dates && doc.dates[0] && doc.dates[0] !== 'NONE') ? doc.dates[0] : 'No Date';

            const isManual = Boolean(doc.is_manual);
            const lockBadgeHtml = isManual 
                ? `<span title="Manually assigned - protected from auto-reallocation" class="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded flex items-center gap-1 font-semibold flex-shrink-0">🔒 Pinned</span>`
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
                        <h4 class="text-xs font-semibold ${hasNotes ? 'text-amber-950' : 'text-slate-800'} group-hover:text-blue-600 transition-colors line-clamp-2 leading-snug">${title}</h4>
                    </div>
                    <div class="flex items-center gap-1 flex-shrink-0">
                        ${noteBadgeHtml}
                        ${lockBadgeHtml}
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
            const menuBtn = card.querySelector('.doc-menu-btn');

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
