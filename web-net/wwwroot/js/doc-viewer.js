// ── Document Viewer Component ─────────────────────────────────────────────
(function() {
    let currentPinnedDoc = null;

    function resolvePdfUrl(vaultId) {
        if (typeof getPdfUrl === 'function' && typeof currentArea !== 'undefined' && typeof currentHouse !== 'undefined') {
            return getPdfUrl(currentArea, currentHouse, vaultId);
        }
        return `/api/areas/default/houses/default/pdf/${encodeURIComponent(vaultId)}`;
    }

    function openDocument(vaultId, title) {
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

        currentPinnedDoc = { vaultId, title };

        const pdfUrl = resolvePdfUrl(vaultId);
        const targetSrc = pdfUrl + '#view=FitH';
        if (pdfFrame && pdfFrame.src !== targetSrc) {
            pdfFrame.src = targetSrc;
        }
        if (viewerDownload) viewerDownload.href = pdfUrl;
        if (typeof window.updateViewerTenantSelect === 'function') {
            window.updateViewerTenantSelect(vaultId);
        }
    }

    function peekDocument(vaultId, title) {
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
    }

    function closeDocument() {
        const docViewerPanel = document.getElementById('document-viewer-panel');
        const welcomePanel = document.getElementById('welcome-panel');
        const pdfFrame = document.getElementById('pdf-frame');

        if (!docViewerPanel) return;
        docViewerPanel.classList.add('hidden');
        docViewerPanel.classList.remove('flex');
        if (welcomePanel) welcomePanel.classList.remove('hidden');
        if (pdfFrame) pdfFrame.src = 'about:blank';
        currentPinnedDoc = null;
    }

    window.openDocument = openDocument;
    window.peekDocument = peekDocument;
    window.closeDocument = closeDocument;
    window.getPinnedDoc = () => currentPinnedDoc;
})();
