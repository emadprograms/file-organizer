// ── Document Viewer Component ─────────────────────────────────────────────
(function() {
    function openDocument(vaultId, title) {
        const docViewerPanel = document.getElementById('document-viewer-panel');
        const viewerTitle = document.getElementById('viewer-title');
        const pdfFrame = document.getElementById('pdf-frame');
        const viewerDownload = document.getElementById('viewer-download');

        if (!docViewerPanel) return;
        docViewerPanel.classList.remove('hidden');
        docViewerPanel.classList.add('flex');
        
        if (viewerTitle) viewerTitle.textContent = title;
        const pdfUrl = getPdfUrl(currentArea, currentHouse, vaultId);
        if (pdfFrame) pdfFrame.src = pdfUrl + '#view=FitH';
        if (viewerDownload) viewerDownload.href = pdfUrl;
        if (typeof window.updateViewerTenantSelect === 'function') {
            window.updateViewerTenantSelect(vaultId);
        }
    }

    function closeDocument() {
        const docViewerPanel = document.getElementById('document-viewer-panel');
        const pdfFrame = document.getElementById('pdf-frame');

        if (!docViewerPanel) return;
        docViewerPanel.classList.add('hidden');
        docViewerPanel.classList.remove('flex');
        if (pdfFrame) pdfFrame.src = 'about:blank';
    }

    window.openDocument = openDocument;
    window.closeDocument = closeDocument;
})();
