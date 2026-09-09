// ── PDF Preview & macOS-Style Quick Look Component ──────────────────────────
(function() {
    let previewTooltip = null;
    let previewIframe = null;
    let previewTitleEl = null;
    let previewShowTimer = null;
    let previewHideTimer = null;
    let previewCurrentUrl = null;

    // Quick Look Modal elements
    let quickLookModal = null;
    let quickLookIframe = null;
    let quickLookTitle = null;
    let quickLookBadge = null;
    let quickLookClose = null;
    let quickLookOpenFull = null;
    let quickLookCurrentDoc = null;

    // Currently selected / focused document
    let selectedDoc = null;

    const PREVIEW_GAP = 12;
    const PREVIEW_DELAY_MS = 450;

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
        previewTooltip = document.getElementById('pdf-preview-tooltip');
        previewIframe = document.getElementById('pdf-preview-iframe');
        previewTitleEl = document.getElementById('pdf-preview-title');

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

        // Global dismiss listeners for hover preview
        window.addEventListener('scroll', () => hidePreview(true), { passive: true, capture: true });
        document.addEventListener('mousedown', (e) => {
            if (e.target && e.target.closest && e.target.closest('.doc-menu-btn')) {
                hidePreview(true);
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
                hidePreview(true);
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
                } else if (selectedDoc) {
                    e.preventDefault();
                    hidePreview(true);
                    openQuickLook(selectedDoc.vaultId, selectedDoc.title, selectedDoc.doc);
                }
            }
        });
    }

    function positionTooltip(mouseX, mouseY, anchorEl) {
        if (!previewTooltip) return;
        const tw = previewTooltip.offsetWidth || 380;
        const th = previewTooltip.offsetHeight || 520;
        const vw = window.innerWidth;
        const vh = window.innerHeight;

        let left, top;

        if (anchorEl && typeof anchorEl.getBoundingClientRect === 'function') {
            const rect = anchorEl.getBoundingClientRect();
            left = rect.right + PREVIEW_GAP;
            top = rect.top - 20;

            // Flip left if overflowing viewport
            if (left + tw > vw - 12) {
                left = rect.left - tw - PREVIEW_GAP;
            }
            // Clamp horizontal
            if (left < 12) left = 12;
            if (left + tw > vw - 12) left = vw - tw - 12;

            // Clamp vertical
            if (top + th > vh - 12) top = vh - th - 12;
            if (top < 12) top = 12;
        } else {
            left = mouseX + PREVIEW_GAP;
            top = mouseY - 60;

            if (left + tw > vw - 8) left = mouseX - tw - PREVIEW_GAP;
            if (top + th > vh - 8) top = vh - th - 8;
            if (top < 8) top = 8;
        }

        previewTooltip.style.left = `${left}px`;
        previewTooltip.style.top = `${top}px`;
        return { left, top };
    }

    function showPreview(vaultId, title, mouseX, mouseY, anchorEl) {
        if (!previewTooltip || !previewIframe) return;
        const pdfUrl = resolvePdfUrl(vaultId, false);

        clearTimeout(previewHideTimer);
        clearTimeout(previewShowTimer);

        previewShowTimer = setTimeout(() => {
            if (previewCurrentUrl !== pdfUrl) {
                previewCurrentUrl = pdfUrl;
                previewIframe.src = pdfUrl;
                if (previewTitleEl) previewTitleEl.textContent = title;
            }
            positionTooltip(mouseX, mouseY, anchorEl);
            previewTooltip.classList.add('visible');
        }, PREVIEW_DELAY_MS);
        return previewShowTimer;
    }

    function hidePreview(immediate = false) {
        clearTimeout(previewShowTimer);
        if (immediate) {
            clearTimeout(previewHideTimer);
            if (previewTooltip) previewTooltip.classList.remove('visible');
            return null;
        }
        previewHideTimer = setTimeout(() => {
            if (previewTooltip) previewTooltip.classList.remove('visible');
        }, 100);
        return previewHideTimer;
    }

    function attachPreview(el, vaultId, title) {
        if (!el) return;
        el.addEventListener('mouseenter', (e) => showPreview(vaultId, title, e.clientX, e.clientY, el));
        el.addEventListener('mouseleave', () => hidePreview(false));
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
        hidePreview(true);
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
        } else if (selectedDoc) {
            openQuickLook(selectedDoc.vaultId, selectedDoc.title, selectedDoc.doc);
        }
    }

    // Expose on window
    window.initPdfPreview = initPdfPreview;
    window.positionTooltip = positionTooltip;
    window.showPreview = showPreview;
    window.hidePreview = hidePreview;
    window.attachPreview = attachPreview;
    window.setSelectedDoc = setSelectedDoc;
    window.getSelectedDoc = getSelectedDoc;
    window.openQuickLook = openQuickLook;
    window.closeQuickLook = closeQuickLook;
    window.toggleQuickLook = toggleQuickLook;
    window.isQuickLookOpen = isQuickLookOpen;
    window.PREVIEW_DELAY_MS = PREVIEW_DELAY_MS;
})();
