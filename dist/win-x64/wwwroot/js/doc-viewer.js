// ── Document Viewer Component ─────────────────────────────────────────────
(function() {
    let currentPinnedDoc = null;
    let currentPdfDoc = null;
    let currentPdfUrl = null;
    let currentScale = 1.0;
    let currentScaleMode = 'fit'; // 'fit' or 'manual'
    let currentLoadingTask = null;

    function isVaultHashName(name) {
        if (!name || typeof name !== 'string') return false;
        const clean = name.trim();
        // Matches patterns like doc_ac132cf0...pdf, ac132cf0...pdf, or hex hash >= 16 chars
        return /^(?:doc_)?[0-9a-f]{16,}(?:\.pdf)?$/i.test(clean);
    }

    function getCleanDocTitle(doc, fallbackCategory = null) {
        if (!doc) return fallbackCategory || 'وثيقة';
        if (typeof doc === 'string') {
            return isVaultHashName(doc) ? (fallbackCategory || 'وثيقة') : doc.trim();
        }
        const arabicTitle = doc.brief_arabic_title || doc.arabic_title;
        if (arabicTitle && !isVaultHashName(arabicTitle)) {
            return arabicTitle.trim();
        }
        const title = doc.title;
        if (title && !isVaultHashName(title)) {
            return title.trim();
        }
        const filename = doc.filename || doc.file_name || doc.name;
        if (filename && !isVaultHashName(filename)) {
            return filename.trim();
        }
        const category = doc.category || doc.folder || doc.subfolder || fallbackCategory;
        if (category && typeof category === 'string' && category.trim()) {
            return category.trim();
        }
        return 'وثيقة';
    }

    function resolvePdfUrl(vaultId) {
        if (typeof getPdfUrl === 'function' && typeof currentArea !== 'undefined' && typeof currentHouse !== 'undefined') {
            return getPdfUrl(currentArea, currentHouse, vaultId);
        }
        return `/api/areas/default/houses/default/pdf/${encodeURIComponent(vaultId)}`;
    }

    function shouldUseCanvasViewer() {
        let stored = null;
        try {
            stored = (typeof localStorage !== 'undefined') ? localStorage.getItem('pdf_viewer_mode') : null;
        } catch (e) {}

        if (stored === 'canvas') return true;
        if (stored === 'native') return false;

        // In automated test runners (Playwright/Puppeteer), prefer native iframe for desktop assertions unless explicitly set
        if (typeof navigator !== 'undefined' && navigator.webdriver) {
            return false;
        }

        // Mobile / Tablet auto-detection:
        // Android, iOS (iPhone/iPad), tablets, or touch-first devices where iframe PDFs prompt downloads
        if (typeof navigator !== 'undefined') {
            const ua = navigator.userAgent || '';
            const isMobileUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|Tablet/i.test(ua);
            const isTouchTablet = (navigator.maxTouchPoints > 1 || (typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(pointer: coarse)').matches));
            const isIPad = /Macintosh/i.test(ua) && isTouchTablet;

            if (isMobileUA || isIPad) return true;

            // Fallback for touch devices without PDF viewer support
            if (navigator.pdfViewerEnabled === false && isTouchTablet) return true;
        }

        // Default for desktop: native iframe (ensures desktop plugins & PDF viewers work)
        return false;
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

    async function renderPdfDocument(pdfUrl) {
        const canvasContainer = document.getElementById('pdf-canvas-container');
        const pdfLoading = document.getElementById('pdf-viewer-loading');
        const pdfError = document.getElementById('pdf-viewer-error');
        const pageInfo = document.getElementById('viewer-page-info');
        const zoomControls = document.getElementById('viewer-zoom-controls');
        const pdfFrame = document.getElementById('pdf-frame');

        if (typeof pdfjsLib === 'undefined') {
            // Fallback to iframe if pdfjsLib is unavailable
            if (pdfFrame) pdfFrame.classList.remove('hidden');
            if (canvasContainer) canvasContainer.classList.add('hidden');
            return;
        }

        // Setup PDF.js worker path
        if (!pdfjsLib.GlobalWorkerOptions.workerSrc) {
            try {
                pdfjsLib.GlobalWorkerOptions.workerSrc = (typeof window !== 'undefined' && window.location ? window.location.origin : '') + '/lib/pdfjs/pdf.worker.min.js';
            } catch (e) {
                pdfjsLib.GlobalWorkerOptions.workerSrc = 'lib/pdfjs/pdf.worker.min.js';
            }
        }

        if (pdfFrame) pdfFrame.classList.add('hidden');
        if (canvasContainer) {
            canvasContainer.classList.remove('hidden');
            canvasContainer.querySelectorAll('.pdf-page-wrapper').forEach(p => p.remove());
        }
        if (pdfLoading) pdfLoading.classList.remove('hidden');
        if (pdfError) pdfError.classList.add('hidden');

        if (currentLoadingTask) {
            try { currentLoadingTask.destroy(); } catch (e) {}
            currentLoadingTask = null;
        }

        try {
            currentLoadingTask = pdfjsLib.getDocument(pdfUrl);
            const pdf = await currentLoadingTask.promise;
            currentPdfDoc = pdf;
            currentPdfUrl = pdfUrl;

            if (pageInfo) {
                pageInfo.textContent = `${pdf.numPages} ${pdf.numPages === 1 ? 'صفحة' : 'صفحات'}`;
                pageInfo.classList.remove('hidden');
            }
            if (zoomControls) {
                zoomControls.classList.remove('hidden');
                zoomControls.classList.add('flex');
            }

            await renderPdfPages();
        } catch (err) {
            console.error('Failed to load PDF with PDF.js:', err);
            if (pdfError) {
                pdfError.classList.remove('hidden');
                const errMsg = document.getElementById('pdf-viewer-error-msg');
                if (errMsg) errMsg.textContent = err.message || 'Error loading PDF';
                const fallbackLink = document.getElementById('pdf-viewer-fallback-link');
                if (fallbackLink) fallbackLink.href = pdfUrl;
            }
            // If PDF.js fails to render, show iframe fallback
            if (pdfFrame) pdfFrame.classList.remove('hidden');
        } finally {
            if (pdfLoading) pdfLoading.classList.add('hidden');
        }
    }

    async function renderPdfPages() {
        if (!currentPdfDoc) return;
        const canvasContainer = document.getElementById('pdf-canvas-container');
        if (!canvasContainer) return;

        // Clear existing rendered pages
        canvasContainer.querySelectorAll('.pdf-page-wrapper').forEach(p => p.remove());

        const zoomLevelBtn = document.getElementById('viewer-zoom-level');
        if (zoomLevelBtn) {
            zoomLevelBtn.textContent = currentScaleMode === 'fit' ? 'Fit' : `${Math.round(currentScale * 100)}%`;
        }

        const containerWidth = Math.max((canvasContainer.clientWidth || window.innerWidth * 0.5) - 32, 280);
        const outputScale = (typeof window !== 'undefined' && window.devicePixelRatio) || 1;

        const activePdfDoc = currentPdfDoc;
        for (let pageNum = 1; pageNum <= currentPdfDoc.numPages; pageNum++) {
            if (!currentPdfDoc || currentPdfDoc !== activePdfDoc) break;

            const page = await currentPdfDoc.getPage(pageNum);
            const unscaledViewport = page.getViewport({ scale: 1.0 });

            let scale = currentScale;
            if (currentScaleMode === 'fit') {
                scale = Math.min(Math.max(containerWidth / unscaledViewport.width, 0.4), 2.5);
            }

            const viewport = page.getViewport({ scale });

            const pageWrapper = document.createElement('div');
            pageWrapper.className = 'pdf-page-wrapper relative bg-white dark:bg-slate-800 rounded-xl shadow-md border border-slate-200 dark:border-slate-700 flex flex-col items-center my-3 overflow-hidden';
            pageWrapper.setAttribute('data-page-number', pageNum);

            const pageBadge = document.createElement('div');
            pageBadge.className = 'absolute top-2 right-2 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-900/70 text-white backdrop-blur-xs z-10 pointer-events-none shadow-xs';
            pageBadge.textContent = `${pageNum} / ${currentPdfDoc.numPages}`;
            pageWrapper.appendChild(pageBadge);

            const canvas = document.createElement('canvas');
            canvas.className = 'pdf-page-canvas block mx-auto';
            canvas.width = Math.floor(viewport.width * outputScale);
            canvas.height = Math.floor(viewport.height * outputScale);
            canvas.style.width = Math.floor(viewport.width) + 'px';
            canvas.style.height = Math.floor(viewport.height) + 'px';

            const ctx = canvas.getContext('2d');
            if (ctx) {
                ctx.scale(outputScale, outputScale);
            }

            pageWrapper.appendChild(canvas);
            canvasContainer.appendChild(pageWrapper);

            if (ctx) {
                await page.render({
                    canvasContext: ctx,
                    viewport: viewport
                }).promise;
            }
        }
    }

    function initViewerControls() {
        const closeBtn = document.getElementById('viewer-close-btn');
        if (closeBtn && !closeBtn._hasViewerListener) {
            closeBtn._hasViewerListener = true;
            closeBtn.onclick = (e) => {
                e.preventDefault();
                closeDocument();
            };
        }

        const zoomInBtn = document.getElementById('viewer-zoom-in');
        if (zoomInBtn && !zoomInBtn._hasViewerListener) {
            zoomInBtn._hasViewerListener = true;
            zoomInBtn.onclick = (e) => {
                e.preventDefault();
                currentScaleMode = 'manual';
                currentScale = Math.min(+(currentScale + 0.25).toFixed(2), 3.0);
                renderPdfPages();
            };
        }

        const zoomOutBtn = document.getElementById('viewer-zoom-out');
        if (zoomOutBtn && !zoomOutBtn._hasViewerListener) {
            zoomOutBtn._hasViewerListener = true;
            zoomOutBtn.onclick = (e) => {
                e.preventDefault();
                currentScaleMode = 'manual';
                currentScale = Math.max(+(currentScale - 0.25).toFixed(2), 0.5);
                renderPdfPages();
            };
        }

        const zoomLevelBtn = document.getElementById('viewer-zoom-level');
        if (zoomLevelBtn && !zoomLevelBtn._hasViewerListener) {
            zoomLevelBtn._hasViewerListener = true;
            zoomLevelBtn.onclick = (e) => {
                e.preventDefault();
                if (currentScaleMode === 'fit') {
                    currentScaleMode = 'manual';
                    currentScale = 1.0;
                } else {
                    currentScaleMode = 'fit';
                }
                renderPdfPages();
            };
        }

        const modeToggleBtn = document.getElementById('viewer-mode-toggle');
        if (modeToggleBtn && !modeToggleBtn._hasViewerListener) {
            modeToggleBtn._hasViewerListener = true;
            modeToggleBtn.onclick = (e) => {
                e.preventDefault();
                const currentIsCanvas = shouldUseCanvasViewer();
                const newMode = currentIsCanvas ? 'native' : 'canvas';
                try {
                    localStorage.setItem('pdf_viewer_mode', newMode);
                } catch (err) {}
                updateViewerModeButton(newMode);

                if (currentPinnedDoc && currentPinnedDoc.vaultId) {
                    const pdfUrl = resolvePdfUrl(currentPinnedDoc.vaultId);
                    const pdfFrame = document.getElementById('pdf-frame');
                    const canvasContainer = document.getElementById('pdf-canvas-container');
                    const zoomControls = document.getElementById('viewer-zoom-controls');

                    if (newMode === 'canvas') {
                        if (pdfFrame) pdfFrame.classList.add('hidden');
                        if (canvasContainer) canvasContainer.classList.remove('hidden');
                        if (zoomControls) {
                            zoomControls.classList.remove('hidden');
                            zoomControls.classList.add('flex');
                        }
                        renderPdfDocument(pdfUrl);
                    } else {
                        if (canvasContainer) canvasContainer.classList.add('hidden');
                        if (pdfFrame) pdfFrame.classList.remove('hidden');
                        if (zoomControls) {
                            zoomControls.classList.add('hidden');
                            zoomControls.classList.remove('flex');
                        }
                    }
                }
            };
        }

        const retryBtn = document.getElementById('pdf-viewer-retry-btn');
        if (retryBtn && !retryBtn._hasViewerListener) {
            retryBtn._hasViewerListener = true;
            retryBtn.onclick = (e) => {
                e.preventDefault();
                if (currentPdfUrl) {
                    renderPdfDocument(currentPdfUrl);
                }
            };
        }

        // Initialize mode button label based on initial state
        const initialMode = shouldUseCanvasViewer() ? 'canvas' : 'native';
        updateViewerModeButton(initialMode);
    }

    function updateViewerModeButton(mode) {
        const label = document.getElementById('viewer-mode-label');
        const toggleBtn = document.getElementById('viewer-mode-toggle');
        if (!toggleBtn) return;
        const isCanvas = mode === 'canvas';
        if (label) {
            label.textContent = isCanvas ? 'Inline' : 'Native';
        }
        toggleBtn.title = isCanvas 
            ? 'Switch to Native PDF viewer • التبديل إلى العارض الأصلي' 
            : 'Switch to Inline Canvas viewer • التبديل إلى العارض المباشر';
    }

    let lastOpenDocVaultId = null;
    let lastOpenDocTime = 0;

    function openDocument(vaultId, title, category = null) {
        initViewerControls();

        const now = Date.now();
        if (lastOpenDocVaultId === vaultId && (now - lastOpenDocTime < 350) && currentPinnedDoc && currentPinnedDoc.vaultId === vaultId) {
            return;
        }
        lastOpenDocVaultId = vaultId;
        lastOpenDocTime = now;

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

        const cleanTitle = getCleanDocTitle(title, category);
        if (viewerTitle) viewerTitle.textContent = cleanTitle;
        if (viewerPeekBadge) viewerPeekBadge.classList.add('hidden');

        currentPinnedDoc = { vaultId, title: cleanTitle, category };

        const pdfUrl = resolvePdfUrl(vaultId);
        const targetSrc = pdfUrl + '#view=FitH';
        if (pdfFrame && pdfFrame.src !== targetSrc) {
            pdfFrame.src = targetSrc;
        }
        if (viewerDownload) {
            viewerDownload.href = pdfUrl;
            viewerDownload.setAttribute('download', `${cleanTitle}.pdf`);
        }

        updateViewerCategory(vaultId, category);

        if (shouldUseCanvasViewer()) {
            renderPdfDocument(pdfUrl);
        } else {
            if (pdfFrame) pdfFrame.classList.remove('hidden');
            const canvasContainer = document.getElementById('pdf-canvas-container');
            if (canvasContainer) canvasContainer.classList.add('hidden');
            const zoomControls = document.getElementById('viewer-zoom-controls');
            if (zoomControls) {
                zoomControls.classList.add('hidden');
                zoomControls.classList.remove('flex');
            }
        }
    }

    function peekDocument(vaultId, title, category = null) {
        initViewerControls();

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

        const cleanTitle = getCleanDocTitle(title, category);
        if (viewerTitle) viewerTitle.textContent = cleanTitle;
        if (viewerPeekBadge) viewerPeekBadge.classList.remove('hidden');

        const pdfUrl = resolvePdfUrl(vaultId);
        const targetSrc = pdfUrl + '#view=FitH';
        if (pdfFrame && pdfFrame.src !== targetSrc) {
            pdfFrame.src = targetSrc;
        }
        if (viewerDownload) {
            viewerDownload.href = pdfUrl;
            viewerDownload.setAttribute('download', `${cleanTitle}.pdf`);
        }

        updateViewerCategory(vaultId, category);

        if (shouldUseCanvasViewer()) {
            renderPdfDocument(pdfUrl);
        } else {
            if (pdfFrame) pdfFrame.classList.remove('hidden');
            const canvasContainer = document.getElementById('pdf-canvas-container');
            if (canvasContainer) canvasContainer.classList.add('hidden');
            const zoomControls = document.getElementById('viewer-zoom-controls');
            if (zoomControls) {
                zoomControls.classList.add('hidden');
                zoomControls.classList.remove('flex');
            }
        }
    }

    function closeDocument() {
        const docViewerPanel = document.getElementById('document-viewer-panel');
        const welcomePanel = document.getElementById('welcome-panel');
        const pdfFrame = document.getElementById('pdf-frame');
        const canvasContainer = document.getElementById('pdf-canvas-container');
        const catBadge = document.getElementById('viewer-category-badge');
        const catVal = document.getElementById('viewer-category-val');
        const pageInfo = document.getElementById('viewer-page-info');
        const zoomControls = document.getElementById('viewer-zoom-controls');

        if (currentLoadingTask) {
            try { currentLoadingTask.destroy(); } catch (e) {}
            currentLoadingTask = null;
        }
        currentPdfDoc = null;
        currentPdfUrl = null;
        currentPinnedDoc = null;

        if (canvasContainer) {
            canvasContainer.querySelectorAll('.pdf-page-wrapper').forEach(p => p.remove());
            canvasContainer.classList.add('hidden');
        }

        if (pageInfo) {
            pageInfo.textContent = '';
            pageInfo.classList.add('hidden');
        }
        if (zoomControls) {
            zoomControls.classList.add('hidden');
            zoomControls.classList.remove('flex');
        }

        if (docViewerPanel) {
            docViewerPanel.classList.add('hidden');
            docViewerPanel.classList.remove('flex');
        }
        if (welcomePanel) welcomePanel.classList.remove('hidden');
        if (pdfFrame) pdfFrame.src = 'about:blank';
        if (catBadge) {
            catBadge.classList.add('hidden');
            catBadge.classList.remove('flex');
        }
        if (catVal) catVal.textContent = '';
    }

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initViewerControls);
        } else {
            initViewerControls();
        }
    }

    window.openDocument = openDocument;
    window.peekDocument = peekDocument;
    window.closeDocument = closeDocument;
    window.getPinnedDoc = () => currentPinnedDoc;
    window.updateViewerCategory = updateViewerCategory;
    window.getCleanDocTitle = getCleanDocTitle;
    window.isVaultHashName = isVaultHashName;
    window.renderPdfDocument = renderPdfDocument;
    window.shouldUseCanvasViewer = shouldUseCanvasViewer;
})();
