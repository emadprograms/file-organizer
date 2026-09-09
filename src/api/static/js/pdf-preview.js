// ── PDF Hover Preview Component ──────────────────────────────────────────
(function() {
    let previewTooltip = null;
    let previewIframe = null;
    let previewTitleEl = null;
    let previewShowTimer = null;
    let previewHideTimer = null;
    let previewCurrentUrl = null;
    const PREVIEW_GAP = 12;
    const PREVIEW_DELAY_MS = 350;

    function initPdfPreview() {
        previewTooltip = document.getElementById('pdf-preview-tooltip');
        previewIframe = document.getElementById('pdf-preview-iframe');
        previewTitleEl = document.getElementById('pdf-preview-title');

        if (previewTooltip) {
            previewTooltip.addEventListener('mouseenter', () => clearTimeout(previewHideTimer));
            previewTooltip.addEventListener('mouseleave', hidePreview);
        }
    }

    function positionTooltip(mouseX, mouseY) {
        if (!previewTooltip) return;
        const tw = previewTooltip.offsetWidth;
        const th = previewTooltip.offsetHeight;
        const vw = window.innerWidth;
        const vh = window.innerHeight;

        let left = mouseX + PREVIEW_GAP;
        let top = mouseY - 60;

        if (left + tw > vw - 8) left = mouseX - tw - PREVIEW_GAP;
        if (top + th > vh - 8) top = vh - th - 8;
        if (top < 8) top = 8;

        previewTooltip.style.left = `${left}px`;
        previewTooltip.style.top = `${top}px`;
        return { left, top };
    }

    function showPreview(vaultId, title, mouseX, mouseY) {
        if (!previewTooltip || !previewIframe) return;
        const pdfUrl = getPdfUrl(currentArea, currentHouse, vaultId) + '#toolbar=0&view=FitH';

        clearTimeout(previewHideTimer);
        clearTimeout(previewShowTimer);

        previewShowTimer = setTimeout(() => {
            if (previewCurrentUrl !== pdfUrl) {
                previewCurrentUrl = pdfUrl;
                previewIframe.src = pdfUrl;
                if (previewTitleEl) previewTitleEl.textContent = title;
            }
            positionTooltip(mouseX, mouseY);
            previewTooltip.classList.add('visible');
        }, PREVIEW_DELAY_MS);
        return previewShowTimer;
    }

    function hidePreview() {
        clearTimeout(previewShowTimer);
        previewHideTimer = setTimeout(() => {
            if (previewTooltip) previewTooltip.classList.remove('visible');
        }, 100);
        return previewHideTimer;
    }

    function attachPreview(el, vaultId, title) {
        if (!el) return;
        el.addEventListener('mouseenter', (e) => showPreview(vaultId, title, e.clientX, e.clientY));
        el.addEventListener('mousemove', (e) => {
            if (previewTooltip && previewTooltip.classList.contains('visible')) {
                positionTooltip(e.clientX, e.clientY);
            }
        });
        el.addEventListener('mouseleave', hidePreview);
    }

    // Expose on window
    window.initPdfPreview = initPdfPreview;
    window.positionTooltip = positionTooltip;
    window.showPreview = showPreview;
    window.hidePreview = hidePreview;
    window.attachPreview = attachPreview;
})();
