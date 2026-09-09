// ── PDF Live Peek & macOS-Style Quick Look Component ──────────────────────────
(function() {
    let peekTimer = null;
    let currentHoverDoc = null;
    let selectedDoc = null;

    // Quick Look Modal elements
    let quickLookModal = null;
    let quickLookIframe = null;
    let quickLookTitle = null;
    let quickLookBadge = null;
    let quickLookClose = null;
    let quickLookOpenFull = null;
    let quickLookCurrentDoc = null;

    const PEEK_DELAY_MS = 250;

    function resolvePdfUrl(vaultId, forQuickLook = false) {
        let baseUrl = '';
        if (typeof getPdfUrl === 'function' && typeof currentArea !== 'undefined' && typeof currentHouse !== 'undefined') {
            baseUrl = getPdfUrl(currentArea, currentHouse, vaultId);
        } else {
            baseUrl = `/api/areas/default/houses/default/pdf/${encodeURIComponent(vaultId)}`;
        }
        return forQuickLook ? `${baseUrl}#view=FitH` : `${baseUrl}#toolbar=0&view=FitH`;
    }

    function initPdfPreview() {
        quickLookModal = document.getElementById('quick-look-modal');
        quickLookIframe = document.getElementById('quick-look-iframe');
        quickLookTitle = document.getElementById('quick-look-title');
        quickLookBadge = document.getElementById('quick-look-badge');
        quickLookClose = document.getElementById('quick-look-close');
        quickLookOpenFull = document.getElementById('quick-look-open-full');

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
                    const { vaultId, title } = quickLookCurrentDoc;
                    closeQuickLook();
                    if (typeof window.openDocument === 'function') {
                        window.openDocument(vaultId, title);
                    }
                }
            };
        }

        // Global dismiss / cancel listeners for live peek
        window.addEventListener('scroll', () => cancelPeek(), { passive: true, capture: true });
        document.addEventListener('mousedown', (e) => {
            if (e.target && e.target.closest && e.target.closest('.doc-menu-btn')) {
                cancelPeek();
            }
        });

        // Global keyboard shortcut: Space for Quick Look, Esc for dismiss
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
                if (isEditing) return; // Allow normal typing in text fields
                
                // Do not intercept if a modal other than quick-look is actively open
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
                    window.peekDocument(vaultId, displayTitle);
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

    // ── Quick Look & Selection ───────────────────────────────────────────────

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

    function openQuickLook(vaultId, title, doc = null) {
        cancelPeek();
        if (!quickLookModal || !quickLookIframe) return;

        const effectiveTitle = title || (doc && (doc.brief_arabic_title || doc.filename)) || 'Document Preview';
        if (quickLookTitle) quickLookTitle.textContent = effectiveTitle;

        if (quickLookBadge) {
            const metaInfo = (doc && (doc.category || doc.primary_tenant)) || '';
            if (metaInfo) {
                quickLookBadge.textContent = metaInfo;
                quickLookBadge.classList.remove('hidden');
            } else {
                quickLookBadge.classList.add('hidden');
            }
        }

        const pdfUrl = resolvePdfUrl(vaultId, true);
        quickLookIframe.src = pdfUrl;
        quickLookCurrentDoc = { vaultId, title: effectiveTitle, doc };

        quickLookModal.classList.remove('hidden');
        quickLookModal.focus();
    }

    function closeQuickLook() {
        if (!quickLookModal) return;
        quickLookModal.classList.add('hidden');
        if (quickLookIframe) {
            quickLookIframe.src = 'about:blank';
        }
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
    function showPreview(vaultId, title) {
        if (typeof window.peekDocument === 'function') {
            window.peekDocument(vaultId, title);
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
    window.closeQuickLook = closeQuickLook;
    window.toggleQuickLook = toggleQuickLook;
    window.isQuickLookOpen = isQuickLookOpen;
    window.PEEK_DELAY_MS = PEEK_DELAY_MS;
    window.PREVIEW_DELAY_MS = PEEK_DELAY_MS;
})();
