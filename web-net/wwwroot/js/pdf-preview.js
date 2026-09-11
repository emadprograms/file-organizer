// ── PDF Live Peek & macOS-Style Document Inspector Component ──────────────────
(function() {
    let peekTimer = null;
    let currentHoverDoc = null;
    let selectedDoc = null;

    // Inspector Modal elements
    let quickLookModal = null;
    let quickLookTitle = null;
    let quickLookSubtitle = null;
    let quickLookBadge = null;
    let quickLookClose = null;
    let quickLookOpenFull = null;
    let quickLookCurrentDoc = null;

    // Inspector Badges & Fields
    let tenantVal = null;
    let categoryVal = null;
    let dateVal = null;
    let pagesVal = null;
    let manualBadge = null;
    let vaultIdEl = null;
    let batchEl = null;
    let catTextEl = null;
    let tenantTextEl = null;
    let pagesSection = null;
    let pagesList = null;

    // Notes elements
    let notesInput = null;
    let notesStatus = null;
    let notesAutosaveTimer = null;

    const PEEK_DELAY_MS = 250;

    function initPdfPreview() {
        quickLookModal = document.getElementById('quick-look-modal');
        quickLookTitle = document.getElementById('quick-look-title');
        quickLookSubtitle = document.getElementById('doc-inspector-subtitle');
        quickLookBadge = document.getElementById('quick-look-badge');
        quickLookClose = document.getElementById('quick-look-close');
        quickLookOpenFull = document.getElementById('quick-look-open-full');

        tenantVal = document.getElementById('doc-inspector-tenant-val');
        categoryVal = document.getElementById('doc-inspector-category-val');
        dateVal = document.getElementById('doc-inspector-date-val');
        pagesVal = document.getElementById('doc-inspector-pages-val');
        manualBadge = document.getElementById('doc-inspector-manual-badge');

        vaultIdEl = document.getElementById('doc-inspector-vault-id');
        batchEl = document.getElementById('doc-inspector-batch');
        catTextEl = document.getElementById('doc-inspector-cat-text');
        tenantTextEl = document.getElementById('doc-inspector-tenant-text');
        pagesSection = document.getElementById('doc-inspector-pages-section');
        pagesList = document.getElementById('doc-inspector-pages-list');

        notesInput = document.getElementById('doc-inspector-notes-input');
        notesStatus = document.getElementById('doc-inspector-notes-status');

        if (quickLookClose) {
            quickLookClose.onclick = () => closeQuickLook();
        }
        if (quickLookModal) {
            quickLookModal.onclick = (e) => {
                if (e.target === quickLookModal) {
                    closeQuickLook();
                }
            };
        }
        if (quickLookOpenFull) {
            quickLookOpenFull.onclick = () => {
                if (quickLookCurrentDoc) {
                    const { vaultId, title, doc } = quickLookCurrentDoc;
                    const docCategory = doc ? (doc.category || doc.folder || doc.subfolder) : null;
                    closeQuickLook();
                    if (typeof window.openDocument === 'function') {
                        window.openDocument(vaultId, title, docCategory);
                    }
                }
            };
        }

        if (notesInput) {
            notesInput.oninput = () => {
                clearTimeout(notesAutosaveTimer);
                if (notesStatus) {
                    notesStatus.textContent = 'Unsaved changes...';
                    notesStatus.className = 'text-[11px] text-amber-700 font-medium transition-opacity opacity-100';
                }
                notesAutosaveTimer = setTimeout(() => {
                    saveCurrentNotes(true);
                }, 1000);
            };
            notesInput.onblur = () => {
                if (notesAutosaveTimer) {
                    clearTimeout(notesAutosaveTimer);
                    notesAutosaveTimer = null;
                    saveCurrentNotes(true);
                }
            };
        }

        // Global dismiss / cancel listeners for live peek
        window.addEventListener('scroll', () => cancelPeek(), { passive: true, capture: true });
        document.addEventListener('mousedown', (e) => {
            if (e.target && e.target.closest && (e.target.closest('.doc-menu-btn') || e.target.closest('.doc-info-btn'))) {
                cancelPeek();
            }
        });

        // Global keyboard shortcut: Space for Inspector, Esc for dismiss
        document.addEventListener('keydown', (e) => {
            const target = document.activeElement;
            const tag = target ? target.tagName.toLowerCase() : '';
            const isEditing = tag === 'input' || tag === 'textarea' || tag === 'select' || (target && target.isContentEditable);

            if (e.key === 'Escape') {
                if (isQuickLookOpen()) {
                    e.preventDefault();
                    closeQuickLook();
                }
                cancelPeek();
                return;
            }

            if (e.key === ' ' || e.code === 'Space') {
                if (isEditing) return; // Allow normal typing in text fields / notes input
                
                // Do not intercept if a modal other than inspector is actively open
                const tenantModal = document.getElementById('tenant-modal');
                const docModal = document.getElementById('doc-modal');
                if ((tenantModal && !tenantModal.classList.contains('hidden')) ||
                    (docModal && !docModal.classList.contains('hidden'))) {
                    return;
                }

                if (isQuickLookOpen()) {
                    e.preventDefault();
                    closeQuickLook();
                } else {
                    const targetDoc = currentHoverDoc || selectedDoc;
                    if (targetDoc) {
                        e.preventDefault();
                        cancelPeek();
                        openQuickLook(targetDoc.vaultId, targetDoc.title, targetDoc.doc);
                    }
                }
            }
        });
    }

    function cancelPeek() {
        clearTimeout(peekTimer);
        peekTimer = null;
    }

    function attachPreview(el, vaultId, title, doc = null) {
        if (!el) return;
        const displayTitle = title || (doc && (doc.brief_arabic_title || doc.filename)) || 'Document';

        el.addEventListener('mouseenter', () => {
            currentHoverDoc = { vaultId, title: displayTitle, doc, el };
            clearTimeout(peekTimer);
            peekTimer = setTimeout(() => {
                if (typeof window.peekDocument === 'function') {
                    const docCategory = doc ? (doc.category || doc.folder || doc.subfolder) : null;
                    window.peekDocument(vaultId, displayTitle, docCategory);
                }
            }, PEEK_DELAY_MS);
        });

        el.addEventListener('mouseleave', () => {
            clearTimeout(peekTimer);
            if (currentHoverDoc && currentHoverDoc.vaultId === vaultId) {
                currentHoverDoc = null;
            }
        });
    }

    // ── Document Selection ───────────────────────────────────────────────────

    function setSelectedDoc(doc, title, el) {
        document.querySelectorAll('.doc-row-selected').forEach(elem => {
            elem.classList.remove('doc-row-selected');
        });

        if (el) {
            el.classList.add('doc-row-selected');
        }

        const vaultId = (doc && (doc.vault_id || doc.id)) || doc;
        const displayTitle = title || (doc && (doc.brief_arabic_title || doc.filename)) || 'Document';
        selectedDoc = { doc, vaultId, title: displayTitle, el };
        return selectedDoc;
    }

    function getSelectedDoc() {
        return selectedDoc;
    }

    // ── Document Inspector & Notes ───────────────────────────────────────────

    async function openQuickLook(vaultId, title, doc = null) {
        cancelPeek();
        if (!quickLookModal) return;

        const effectiveTitle = title || (doc && (doc.brief_arabic_title || doc.filename)) || 'Document Inspector';
        if (quickLookTitle) quickLookTitle.textContent = effectiveTitle;
        if (quickLookSubtitle) quickLookSubtitle.textContent = `ID: ${vaultId}`;

        const tenantName = (doc && (doc.tenant || doc.primary_tenant)) || 'No Tenant';
        const categoryName = (doc && doc.category) || 'General';
        const docDate = (doc && (doc.date || (doc.dates && doc.dates[0]))) || 'Unknown Date';
        const pageCount = (doc && (doc.end_page || doc.page_count)) || 1;
        const isManual = Boolean(doc && doc.is_manual);

        if (tenantVal) tenantVal.textContent = tenantName;
        if (categoryVal) categoryVal.textContent = categoryName;
        if (dateVal) dateVal.textContent = docDate;
        if (pagesVal) pagesVal.textContent = `${pageCount} page${pageCount > 1 ? 's' : ''}`;
        
        if (manualBadge) {
            if (isManual) {
                manualBadge.classList.remove('hidden');
            } else {
                manualBadge.classList.add('hidden');
            }
        }

        if (vaultIdEl) vaultIdEl.textContent = vaultId;
        if (catTextEl) catTextEl.textContent = categoryName;
        if (tenantTextEl) tenantTextEl.textContent = tenantName;
        if (batchEl) batchEl.textContent = (doc && doc.filename) || `doc_${vaultId}.pdf`;

        // Notes field initialization
        if (notesInput) {
            notesInput.value = (doc && doc.notes) ? doc.notes : '';
        }
        if (notesStatus) {
            notesStatus.textContent = '';
            notesStatus.classList.add('opacity-0');
        }

        // Reset pages section
        if (pagesSection) pagesSection.classList.add('hidden');
        if (pagesList) pagesList.innerHTML = '';

        quickLookCurrentDoc = { vaultId, title: effectiveTitle, doc };
        quickLookModal.classList.remove('hidden');
        quickLookModal.focus();

        // Fetch detailed database metadata and OCR page intel
        if (typeof isStaticMode === 'undefined' || !isStaticMode) {
            const area = (typeof currentArea !== 'undefined') ? currentArea : 'default';
            const house = (typeof currentHouse !== 'undefined') ? currentHouse : 'default';
            try {
                const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(vaultId)}/metadata`);
                if (res.ok) {
                    const meta = await res.json();
                    if (quickLookCurrentDoc && quickLookCurrentDoc.vaultId === vaultId) {
                        if (meta.arabic_title && quickLookTitle) quickLookTitle.textContent = meta.arabic_title;
                        if (meta.tenant_name && tenantVal) tenantVal.textContent = meta.tenant_name;
                        if (meta.tenant_name && tenantTextEl) tenantTextEl.textContent = meta.tenant_name;
                        if (meta.category && categoryVal) categoryVal.textContent = meta.category;
                        if (meta.category && catTextEl) catTextEl.textContent = meta.category;
                        if (meta.primary_date && dateVal) dateVal.textContent = meta.primary_date;
                        if (meta.page_count && pagesVal) pagesVal.textContent = `${meta.page_count} page${meta.page_count > 1 ? 's' : ''}`;
                        if (meta.batch_filename && batchEl) batchEl.textContent = meta.batch_filename;
                        if (meta.notes !== undefined && notesInput && document.activeElement !== notesInput) {
                            notesInput.value = meta.notes || '';
                        }
                        if (meta.is_manual && manualBadge) {
                            manualBadge.classList.remove('hidden');
                        }

                        if (meta.pages && meta.pages.length > 0 && pagesSection && pagesList) {
                            const validPages = meta.pages.filter(p => p.subject || p.sender || p.receiver || p.content_explanation);
                            if (validPages.length > 0) {
                                pagesList.innerHTML = validPages.map(p => `
                                    <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
                                        <div class="flex items-center justify-between text-[11px] font-semibold text-slate-700">
                                            <span>Page ${p.page_number}</span>
                                            <span class="text-[10px] text-slate-400">${p.raw_date || ''}</span>
                                        </div>
                                        ${p.subject ? `<div class="text-slate-800 font-medium">${p.subject}</div>` : ''}
                                        <div class="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-600">
                                            ${p.sender ? `<span><strong class="text-slate-400">From:</strong> ${p.sender}</span>` : ''}
                                            ${p.receiver ? `<span><strong class="text-slate-400">To:</strong> ${p.receiver}</span>` : ''}
                                        </div>
                                        ${p.content_explanation ? `<p class="text-[11px] text-slate-500 italic mt-1">${p.content_explanation}</p>` : ''}
                                    </div>
                                `).join('');
                                pagesSection.classList.remove('hidden');
                            }
                        }
                    }
                }
            } catch (err) {
                // Ignore metadata fetch error, basic doc info is already displayed
            }
        }
    }

    async function saveCurrentNotes(isAutosave = false) {
        if (!quickLookCurrentDoc) return;
        const { vaultId, doc } = quickLookCurrentDoc;
        const newNotes = notesInput ? notesInput.value.trim() : '';

        if (notesStatus) {
            notesStatus.textContent = isAutosave ? 'Autosaving...' : 'Saving...';
            notesStatus.className = 'text-[11px] text-amber-600 font-medium transition-opacity opacity-100';
        }

        try {
            if (typeof isStaticMode !== 'undefined' && isStaticMode) {
                if (doc) doc.notes = newNotes;
            } else {
                const area = (typeof currentArea !== 'undefined') ? currentArea : 'default';
                const house = (typeof currentHouse !== 'undefined') ? currentHouse : 'default';
                const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(vaultId)}/notes`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ notes: newNotes })
                });
                if (!res.ok) throw new Error('Failed to save notes');
                const data = await res.json();
                if (doc) doc.notes = data.notes;
            }

            if (doc) doc.notes = newNotes;
            updateCachesDocNotes(vaultId, newNotes);
            updateDocRowInDOM(vaultId, newNotes);

            if (notesStatus) {
                notesStatus.textContent = '✓ Saved';
                notesStatus.className = 'text-[11px] text-emerald-600 font-medium transition-opacity opacity-100';
                setTimeout(() => {
                    if (notesStatus && notesStatus.textContent === '✓ Saved') {
                        notesStatus.classList.add('opacity-0');
                    }
                }, 2500);
            }
        } catch (err) {
            console.error('Error saving notes:', err);
            if (notesStatus) {
                notesStatus.textContent = 'Error saving';
                notesStatus.className = 'text-[11px] text-rose-600 font-medium transition-opacity opacity-100';
            }
        }
    }

    function updateDocRowInDOM(vaultId, notes) {
        const hasNotes = Boolean(notes && notes.trim());
        const trimmedNotes = notes ? notes.trim() : '';
        const snippet = hasNotes ? (typeof window.getNoteSnippet === 'function' ? window.getNoteSnippet(trimmedNotes) : trimmedNotes.slice(0, 14)) : '';
        const docEls = document.querySelectorAll(`[data-vault-id="${vaultId}"]`);
        docEls.forEach(docEl => {
            // Category doc row
            if (docEl.classList.contains('group/doc')) {
                let noteBadge = docEl.querySelector('.doc-note-badge');
                if (hasNotes) {
                    docEl.classList.add('bg-amber-50/80', 'border-l-4', 'border-l-amber-400', 'border', 'border-amber-200/80', 'text-amber-900', 'shadow-2xs');
                    docEl.classList.remove('text-blue-600', 'hover:bg-blue-50');
                    if (noteBadge) {
                        noteBadge.textContent = `📝 ${snippet}`;
                        noteBadge.title = trimmedNotes;
                    } else {
                        noteBadge = document.createElement('span');
                        noteBadge.className = 'doc-note-badge inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded font-medium bg-amber-100 text-amber-800 border border-amber-300/60 flex-shrink-0';
                        noteBadge.title = trimmedNotes;
                        noteBadge.textContent = `📝 ${snippet}`;
                        const titleContainer = docEl.querySelector('.flex.items-center.gap-2.min-w-0');
                        if (titleContainer) {
                            titleContainer.appendChild(noteBadge);
                        }
                    }
                } else {
                    docEl.classList.remove('bg-amber-50/80', 'border-l-4', 'border-l-amber-400', 'border', 'border-amber-200/80', 'text-amber-900', 'shadow-2xs');
                    docEl.classList.add('text-blue-600', 'hover:bg-blue-50');
                    if (noteBadge) noteBadge.remove();
                }
            }
            // Timeline card
            if (docEl.classList.contains('group') && !docEl.classList.contains('group/doc')) {
                let noteBadge = docEl.querySelector('.doc-note-badge');
                if (hasNotes) {
                    docEl.classList.add('border-l-4', 'border-l-amber-400', 'bg-amber-50/80');
                    if (noteBadge) {
                        noteBadge.textContent = `📝 ${snippet}`;
                        noteBadge.title = trimmedNotes;
                    } else {
                        noteBadge = document.createElement('span');
                        noteBadge.className = 'doc-note-badge text-[10px] bg-amber-100 text-amber-800 border border-amber-300/70 px-1.5 py-0.5 rounded flex items-center gap-1 font-semibold flex-shrink-0';
                        noteBadge.title = trimmedNotes;
                        noteBadge.textContent = `📝 ${snippet}`;
                        const headerRight = docEl.querySelector('.flex.items-center.gap-1.flex-shrink-0');
                        if (headerRight) {
                            headerRight.insertBefore(noteBadge, headerRight.firstChild);
                        }
                    }
                } else {
                    docEl.classList.remove('border-l-4', 'border-l-amber-400', 'bg-amber-50/80');
                    if (noteBadge) noteBadge.remove();
                }
            }
        });
    }

    function updateCachesDocNotes(vaultId, notes) {
        if (typeof currentCategories !== 'undefined' && Array.isArray(currentCategories)) {
            currentCategories.forEach(cat => {
                if (cat.documents) {
                    cat.documents.forEach(d => {
                        if (d.vault_id === vaultId) d.notes = notes;
                    });
                }
            });
        }
        if (typeof currentTimeline !== 'undefined' && Array.isArray(currentTimeline)) {
            currentTimeline.forEach(d => {
                if (d.vault_id === vaultId) d.notes = notes;
            });
        }
    }

    function closeQuickLook() {
        if (!quickLookModal) return;
        if (notesAutosaveTimer) {
            clearTimeout(notesAutosaveTimer);
            notesAutosaveTimer = null;
            saveCurrentNotes(true);
        }
        quickLookModal.classList.add('hidden');
        quickLookCurrentDoc = null;
    }

    function isQuickLookOpen() {
        return quickLookModal && !quickLookModal.classList.contains('hidden');
    }

    function toggleQuickLook() {
        if (isQuickLookOpen()) {
            closeQuickLook();
        } else {
            const targetDoc = currentHoverDoc || selectedDoc;
            if (targetDoc) {
                openQuickLook(targetDoc.vaultId, targetDoc.title, targetDoc.doc);
            }
        }
    }

    // Compatibility stubs
    function positionTooltip() { return { left: 0, top: 0 }; }
    function showPreview(vaultId, title, category = null) {
        if (typeof window.peekDocument === 'function') {
            window.peekDocument(vaultId, title, category);
        }
    }
    function hidePreview() { cancelPeek(); }

    // Expose on window
    window.initPdfPreview = initPdfPreview;
    window.positionTooltip = positionTooltip;
    window.showPreview = showPreview;
    window.hidePreview = hidePreview;
    window.cancelPeek = cancelPeek;
    window.attachPreview = attachPreview;
    window.setSelectedDoc = setSelectedDoc;
    window.getSelectedDoc = getSelectedDoc;
    window.openQuickLook = openQuickLook;
    window.openDocInspector = openQuickLook;
    window.closeQuickLook = closeQuickLook;
    window.toggleQuickLook = toggleQuickLook;
    window.isQuickLookOpen = isQuickLookOpen;
    window.saveCurrentNotes = saveCurrentNotes;
    window.updateDocRowInDOM = updateDocRowInDOM;
    window.PEEK_DELAY_MS = PEEK_DELAY_MS;
    window.PREVIEW_DELAY_MS = PEEK_DELAY_MS;
})();

