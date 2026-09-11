// ── Document Viewer Component ─────────────────────────────────────────────
(function() {
    let currentPinnedDoc = null;

    function resolvePdfUrl(vaultId) {
        if (typeof getPdfUrl === 'function' && typeof currentArea !== 'undefined' && typeof currentHouse !== 'undefined') {
            return getPdfUrl(currentArea, currentHouse, vaultId);
        }
        return `/api/areas/default/houses/default/pdf/${encodeURIComponent(vaultId)}`;
    }

    function updateViewerCategory(vaultId, explicitCategory) {
        const catBadge = document.getElementById('viewer-category-badge');
        const catVal = document.getElementById('viewer-category-val');
        if (!catBadge || !catVal) return;

        let foundCategory = explicitCategory || null;

        // If doc object was passed as category
        if (foundCategory && typeof foundCategory === 'object') {
            foundCategory = foundCategory.category || foundCategory.folder || foundCategory.subfolder || null;
        }

        // 1. Try finding in currentTimeline
        if (!foundCategory && typeof currentTimeline !== 'undefined' && Array.isArray(currentTimeline)) {
            const item = currentTimeline.find(d => d && (d.vault_id === vaultId || d.id === vaultId));
            if (item && item.category) {
                foundCategory = item.category;
            }
        }

        // 2. Try finding in window.getSelectedDoc()
        if (!foundCategory && typeof window.getSelectedDoc === 'function') {
            const sel = window.getSelectedDoc();
            if (sel && (sel.vaultId === vaultId || sel.doc?.vault_id === vaultId) && sel.doc?.category) {
                foundCategory = sel.doc.category;
            }
        }

        // 3. Try finding in globalTreeData
        if (!foundCategory) {
            const tree = (typeof globalTreeData !== 'undefined' ? globalTreeData : window.globalTreeData) || [];
            const area = (typeof currentArea !== 'undefined' ? currentArea : window.currentArea);
            const house = (typeof currentHouse !== 'undefined' ? currentHouse : window.currentHouse);
            if (tree && area && house) {
                const areaNode = tree.find(a => a.name === area);
                const houseNode = areaNode?.houses?.find(h => String(h.house_number || h.name) === String(house));
                if (houseNode && houseNode.categories) {
                    for (const cat of houseNode.categories) {
                        if (cat.documents && cat.documents.some(d => (d.vault_id === vaultId || d.id === vaultId))) {
                            foundCategory = cat.name;
                            break;
                        }
                    }
                }
            }
        }

        if (foundCategory) {
            catVal.textContent = foundCategory;
            catBadge.classList.remove('hidden');
            catBadge.classList.add('flex');
        } else {
            catVal.textContent = '';
            catBadge.classList.add('hidden');
            catBadge.classList.remove('flex');

            // Asynchronous fetch from metadata API if not static mode
            if (typeof isStaticMode === 'undefined' || !isStaticMode) {
                const area = (typeof currentArea !== 'undefined' ? currentArea : window.currentArea) || 'default';
                const house = (typeof currentHouse !== 'undefined' ? currentHouse : window.currentHouse) || 'default';
                fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(vaultId)}/metadata`)
                    .then(res => res.ok ? res.json() : null)
                    .then(meta => {
                        if (meta && meta.category && catBadge && catVal && (!currentPinnedDoc || currentPinnedDoc.vaultId === vaultId)) {
                            catVal.textContent = meta.category;
                            catBadge.classList.remove('hidden');
                            catBadge.classList.add('flex');
                        }
                    })
                    .catch(() => {});
            }
        }
    }

    function openDocument(vaultId, title, category = null) {
        const docViewerPanel = document.getElementById('document-viewer-panel');
        const welcomePanel = document.getElementById('welcome-panel');
        const resizer2 = document.getElementById('resizer-2');
        const viewerTitle = document.getElementById('viewer-title');
        const viewerPeekBadge = document.getElementById('viewer-peek-badge');
        const pdfFrame = document.getElementById('pdf-frame');
        const viewerDownload = document.getElementById('viewer-download');

        if (!docViewerPanel) return;
        if (welcomePanel) welcomePanel.classList.add('hidden');
        if (resizer2) resizer2.classList.remove('hidden');

        docViewerPanel.classList.remove('hidden');
        docViewerPanel.classList.add('flex');
        
        if (viewerTitle) viewerTitle.textContent = title;
        if (viewerPeekBadge) viewerPeekBadge.classList.add('hidden');

        currentPinnedDoc = { vaultId, title, category };

        const pdfUrl = resolvePdfUrl(vaultId);
        const targetSrc = pdfUrl + '#view=FitH';
        if (pdfFrame && pdfFrame.src !== targetSrc) {
            pdfFrame.src = targetSrc;
        }
        if (viewerDownload) viewerDownload.href = pdfUrl;

        updateViewerCategory(vaultId, category);
    }

    function peekDocument(vaultId, title, category = null) {
        const docViewerPanel = document.getElementById('document-viewer-panel');
        const welcomePanel = document.getElementById('welcome-panel');
        const resizer2 = document.getElementById('resizer-2');
        const viewerTitle = document.getElementById('viewer-title');
        const viewerPeekBadge = document.getElementById('viewer-peek-badge');
        const pdfFrame = document.getElementById('pdf-frame');
        const viewerDownload = document.getElementById('viewer-download');

        if (!docViewerPanel) return;
        if (welcomePanel) welcomePanel.classList.add('hidden');
        if (resizer2) resizer2.classList.remove('hidden');

        docViewerPanel.classList.remove('hidden');
        docViewerPanel.classList.add('flex');

        if (viewerTitle) viewerTitle.textContent = title;
        if (viewerPeekBadge) viewerPeekBadge.classList.remove('hidden');

        const pdfUrl = resolvePdfUrl(vaultId);
        const targetSrc = pdfUrl + '#view=FitH';
        if (pdfFrame && pdfFrame.src !== targetSrc) {
            pdfFrame.src = targetSrc;
        }
        if (viewerDownload) viewerDownload.href = pdfUrl;

        updateViewerCategory(vaultId, category);
    }

    function closeDocument() {
        const docViewerPanel = document.getElementById('document-viewer-panel');
        const welcomePanel = document.getElementById('welcome-panel');
        const pdfFrame = document.getElementById('pdf-frame');
        const catBadge = document.getElementById('viewer-category-badge');
        const catVal = document.getElementById('viewer-category-val');

        if (!docViewerPanel) return;
        docViewerPanel.classList.add('hidden');
        docViewerPanel.classList.remove('flex');
        if (welcomePanel) welcomePanel.classList.remove('hidden');
        if (pdfFrame) pdfFrame.src = 'about:blank';
        if (catBadge) {
            catBadge.classList.add('hidden');
            catBadge.classList.remove('flex');
        }
        if (catVal) catVal.textContent = '';
        currentPinnedDoc = null;
    }

    window.openDocument = openDocument;
    window.peekDocument = peekDocument;
    window.closeDocument = closeDocument;
    window.getPinnedDoc = () => currentPinnedDoc;
    window.updateViewerCategory = updateViewerCategory;
})();
