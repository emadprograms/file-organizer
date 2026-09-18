// ── Document Page Editor Component (Split, Extract, Delete & Reorder Pages) ───────
(function() {
    let editorModal = null;
    let editorTitle = null;
    let editorSubtitle = null;
    let editorPageCountBadge = null;
    let editorGrid = null;
    let editorCloseBtn = null;
    let editorLoading = null;
    let editorSelectedCount = null;
    let btnSelectAll = null;
    let btnDeselectAll = null;
    let btnDeleteSelected = null;
    let btnRotateSelected = null;
    let btnCopySelected = null;
    let btnExtractSelected = null;

    // Sub-modal elements for Extract, Move & Copy
    let extractModal = null;
    let extractModeMoveRadio = null;
    let extractModeCopyRadio = null;
    let extractModeMoveLabel = null;
    let extractModeCopyLabel = null;
    let extractCategorySelect = null;
    let extractCustomCatContainer = null;
    let extractCustomCatInput = null;
    let extractTenantSelect = null;
    let extractTitleInput = null;
    let extractDateInput = null;
    let extractNotesInput = null;
    let btnExtractCancel = null;
    let btnExtractConfirm = null;
    let btnExtractConfirmText = null;

    let btnEditorZoomOut = null;
    let btnEditorZoomIn = null;
    let btnEditorZoomReset = null;
    let editorZoomLevelLabel = null;

    const EDITOR_ZOOM_LEVELS = [
        { scale: 0.70, minW: 160, maxW: 210, thumbH: 190, label: '70%' },
        { scale: 0.85, minW: 190, maxW: 250, thumbH: 230, label: '85%' },
        { scale: 1.00, minW: 230, maxW: 300, thumbH: 280, label: '100%' },
        { scale: 1.20, minW: 280, maxW: 360, thumbH: 340, label: '120%' },
        { scale: 1.45, minW: 340, maxW: 440, thumbH: 420, label: '145%' },
        { scale: 1.75, minW: 420, maxW: 540, thumbH: 520, label: '175%' },
        { scale: 2.10, minW: 520, maxW: 680, thumbH: 640, label: '210%' }
    ];
    const DEFAULT_EDITOR_ZOOM_INDEX = 2; // 100%
    let currentEditorZoomIndex = DEFAULT_EDITOR_ZOOM_INDEX;

    let activeEditorDoc = null;
    let activePdfDoc = null;
    let selectedPageNumbers = new Set();
    let currentPageOrder = []; // Array of page numbers 1..N
    let isReordering = false;
    let isRotating = false;
    let cardRotations = {}; // pageNum -> degrees (0, 90, 180, 270)
    let draggedPages = []; // array of page numbers currently being dragged

    const STANDARD_FOLDERS = [
        "01 - بيانات أساسية",
        "02 - بيانات شخصية",
        "03 - أمر تخصيص",
        "04 - محضر تسليم مفتاح",
        "05 - عقود",
        "06 - كهرباء وماء",
        "07 - استقطاع إيجار",
        "08 - وقف استقطاع بدل",
        "09 - إشعارات",
        "10 - صيانة",
        "11 - صور ومعاينات",
        "12 - تعديلات",
        "13 - رسائل متنوعة",
    ];

    function getResolvedArea(doc) {
        if (doc && doc.area_id && doc.area_id !== 'default') return doc.area_id;
        if (typeof currentArea !== 'undefined' && currentArea && currentArea !== 'default') return currentArea;
        if (typeof window !== 'undefined' && window.currentArea && window.currentArea !== 'default') return window.currentArea;
        if (typeof window !== 'undefined' && window.location && window.location.hash) {
            const match = window.location.hash.match(/#\/area\/([^/]+)/);
            if (match) return decodeURIComponent(match[1]).replace(/^area_/, '');
        }
        return (doc && doc.area_id) || 'default';
    }

    function getResolvedHouse(doc) {
        if (doc && doc.house_id && doc.house_id !== 'default') return doc.house_id;
        if (typeof currentHouse !== 'undefined' && currentHouse && currentHouse !== 'default') return currentHouse;
        if (typeof window !== 'undefined' && window.currentHouse && window.currentHouse !== 'default') return window.currentHouse;
        if (typeof window !== 'undefined' && window.location && window.location.hash) {
            const match = window.location.hash.match(/house\/([^/]+)/);
            if (match) return decodeURIComponent(match[1]);
        }
        return (doc && doc.house_id) || 'default';
    }

    function resolvePdfUrl(area, house, vaultId, cacheBust = null) {
        let url;
        if (typeof getPdfUrl === 'function' && area && area !== 'default' && house && house !== 'default') {
            url = getPdfUrl(area, house, vaultId);
        } else if (area && area !== 'default' && house && house !== 'default') {
            url = `/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/pdf/${encodeURIComponent(vaultId)}`;
        } else {
            url = `/api/pdf/${encodeURIComponent(vaultId)}`;
        }
        if (cacheBust) {
            url += (url.includes('?') ? '&' : '?') + 't=' + cacheBust;
        }
        return url;
    }

    function getApiUrl(path) {
        if (typeof window !== 'undefined' && window.location && window.location.origin && window.location.origin !== 'null' && window.location.origin !== 'file://') {
            try {
                return new URL(path, window.location.origin).toString();
            } catch (e) {}
        }
        return path;
    }

    function initPageEditor() {
        editorModal = document.getElementById('doc-page-editor-modal');
        if (!editorModal) return;

        editorTitle = document.getElementById('page-editor-title');
        editorSubtitle = document.getElementById('page-editor-subtitle');
        editorPageCountBadge = document.getElementById('page-editor-count-badge');
        editorGrid = document.getElementById('page-editor-grid');
        editorCloseBtn = document.getElementById('page-editor-close-btn');
        editorLoading = document.getElementById('page-editor-loading');
        editorSelectedCount = document.getElementById('page-editor-selected-count');
        btnSelectAll = document.getElementById('btn-editor-select-all');
        btnDeselectAll = document.getElementById('btn-editor-deselect-all');
        btnDeleteSelected = document.getElementById('btn-editor-delete-selected');
        btnRotateSelected = document.getElementById('btn-editor-rotate-selected');
        btnCopySelected = document.getElementById('btn-editor-copy-selected');
        btnExtractSelected = document.getElementById('btn-editor-extract-selected');

        extractModal = document.getElementById('extract-pages-submodal');
        extractModeMoveRadio = document.getElementById('extract-mode-move');
        extractModeCopyRadio = document.getElementById('extract-mode-copy');
        extractModeMoveLabel = document.getElementById('extract-mode-move-label');
        extractModeCopyLabel = document.getElementById('extract-mode-copy-label');
        extractCategorySelect = document.getElementById('extract-target-category');
        extractCustomCatContainer = document.getElementById('extract-custom-cat-container');
        extractCustomCatInput = document.getElementById('extract-custom-cat-input');
        extractTenantSelect = document.getElementById('extract-target-tenant');
        extractTitleInput = document.getElementById('extract-target-title');
        extractDateInput = document.getElementById('extract-target-date');
        extractNotesInput = document.getElementById('extract-target-notes');
        btnExtractCancel = document.getElementById('btn-extract-cancel');
        btnExtractConfirm = document.getElementById('btn-extract-confirm');
        btnExtractConfirmText = document.getElementById('btn-extract-confirm-text');

        if (editorCloseBtn) editorCloseBtn.onclick = closePageEditor;
        if (btnSelectAll) btnSelectAll.onclick = selectAllPages;
        if (btnDeselectAll) btnDeselectAll.onclick = deselectAllPages;
        if (btnDeleteSelected) btnDeleteSelected.onclick = handleDeleteSelectedPages;
        if (btnRotateSelected) btnRotateSelected.onclick = () => rotateSelectedPages(90);
        if (btnCopySelected) btnCopySelected.onclick = () => openExtractSubmodal('copy');
        if (btnExtractSelected) btnExtractSelected.onclick = () => openExtractSubmodal('move');

        if (btnExtractCancel) btnExtractCancel.onclick = closeExtractSubmodal;
        if (btnExtractConfirm) btnExtractConfirm.onclick = executeExtractPages;

        if (extractModeMoveRadio) extractModeMoveRadio.onchange = updateExtractModeUI;
        if (extractModeCopyRadio) extractModeCopyRadio.onchange = updateExtractModeUI;

        if (extractCategorySelect) {
            extractCategorySelect.onchange = () => {
                if (extractCategorySelect.value === '__custom__') {
                    if (extractCustomCatContainer) extractCustomCatContainer.classList.remove('hidden');
                    if (extractCustomCatInput) extractCustomCatInput.focus();
                } else {
                    if (extractCustomCatContainer) extractCustomCatContainer.classList.add('hidden');
                    if (extractTitleInput && (!extractTitleInput.value || STANDARD_FOLDERS.includes(extractTitleInput.value))) {
                        extractTitleInput.value = extractCategorySelect.value;
                    }
                }
            };
        }

        // Keyboard shortcuts: Escape to close, Ctrl +/-/0 to zoom
        const handleEditorKeyDown = (e) => {
            if (e._editorKeyHandled) return;
            e._editorKeyHandled = true;

            const curEditorModal = document.getElementById('doc-page-editor-modal') || editorModal;
            const curExtractModal = document.getElementById('doc-page-extract-modal') || document.getElementById('extract-pages-submodal') || extractModal;
            if (e.key === 'Escape') {
                if (curExtractModal && !curExtractModal.classList.contains('hidden')) {
                    e.preventDefault();
                    closeExtractSubmodal();
                } else if (curEditorModal && !curEditorModal.classList.contains('hidden') && curEditorModal.style.display !== 'none') {
                    e.preventDefault();
                    closePageEditor();
                }
            } else if (e.ctrlKey || e.metaKey) {
                if (curEditorModal && !curEditorModal.classList.contains('hidden') && curEditorModal.style.display !== 'none') {
                    if (e.key === '=' || e.key === '+' || e.code === 'NumpadAdd') {
                        e.preventDefault();
                        zoomInEditorCards();
                    } else if (e.key === '-' || e.key === '_' || e.code === 'NumpadSubtract') {
                        e.preventDefault();
                        zoomOutEditorCards();
                    } else if (e.key === '0' || e.code === 'Numpad0') {
                        e.preventDefault();
                        resetEditorCardZoom();
                    }
                }
            }
        };

        if (typeof window !== 'undefined') {
            if (window._editorZoomKeydownHandler) {
                if (typeof document !== 'undefined') {
                    document.removeEventListener('keydown', window._editorZoomKeydownHandler);
                }
                window.removeEventListener('keydown', window._editorZoomKeydownHandler);
            }
            window._editorZoomKeydownHandler = handleEditorKeyDown;
            window.addEventListener('keydown', window._editorZoomKeydownHandler);
            if (typeof document !== 'undefined') {
                document.addEventListener('keydown', window._editorZoomKeydownHandler);
            }
        }

        btnEditorZoomOut = document.getElementById('btn-editor-zoom-out');
        btnEditorZoomIn = document.getElementById('btn-editor-zoom-in');
        btnEditorZoomReset = document.getElementById('btn-editor-zoom-reset');
        editorZoomLevelLabel = document.getElementById('editor-zoom-level-label');

        initEditorZoom();
    }

    let editorZoomRerenderTimer = null;
    function scheduleZoomRerender() {
        if (editorZoomRerenderTimer) clearTimeout(editorZoomRerenderTimer);
        editorZoomRerenderTimer = setTimeout(async () => {
            if (!activePdfDoc || !editorGrid) return;
            const cards = editorGrid.querySelectorAll('.page-editor-card');
            for (const card of cards) {
                const pageNum = parseInt(card.getAttribute('data-page-num'), 10);
                if (pageNum && !isNaN(pageNum)) {
                    await renderPageCanvas(card, pageNum);
                }
            }
        }, 200);
    }

    function applyEditorCardZoom() {
        const config = EDITOR_ZOOM_LEVELS[currentEditorZoomIndex] || EDITOR_ZOOM_LEVELS[DEFAULT_EDITOR_ZOOM_INDEX];
        const modal = document.getElementById('doc-page-editor-modal') || editorModal;
        if (modal) {
            modal.style.setProperty('--editor-card-min-width', `${config.minW}px`);
            modal.style.setProperty('--editor-card-max-width', `${config.maxW}px`);
            modal.style.setProperty('--editor-thumb-height', `${config.thumbH}px`);
        }

        const grid = document.getElementById('page-editor-grid') || editorGrid;
        if (grid) {
            grid.style.setProperty('--editor-card-min-width', `${config.minW}px`);
            grid.style.setProperty('--editor-card-max-width', `${config.maxW}px`);
            grid.style.setProperty('--editor-thumb-height', `${config.thumbH}px`);
        }

        const lbl = document.getElementById('editor-zoom-level-label') || editorZoomLevelLabel;
        if (lbl) lbl.textContent = config.label;

        const bOut = document.getElementById('btn-editor-zoom-out') || btnEditorZoomOut;
        const bIn = document.getElementById('btn-editor-zoom-in') || btnEditorZoomIn;
        if (bOut) bOut.disabled = currentEditorZoomIndex === 0;
        if (bIn) bIn.disabled = currentEditorZoomIndex === EDITOR_ZOOM_LEVELS.length - 1;

        try {
            localStorage.setItem('editor_card_zoom_level', config.scale.toString());
        } catch (e) {}

        scheduleZoomRerender();
    }

    function zoomInEditorCards() {
        if (currentEditorZoomIndex < EDITOR_ZOOM_LEVELS.length - 1) {
            currentEditorZoomIndex++;
            applyEditorCardZoom();
        }
    }

    function zoomOutEditorCards() {
        if (currentEditorZoomIndex > 0) {
            currentEditorZoomIndex--;
            applyEditorCardZoom();
        }
    }

    function resetEditorCardZoom() {
        currentEditorZoomIndex = DEFAULT_EDITOR_ZOOM_INDEX;
        applyEditorCardZoom();
    }

    function initEditorZoom() {
        try {
            const saved = (typeof localStorage !== 'undefined' && localStorage) ? localStorage.getItem('editor_card_zoom_level') : null;
            if (saved !== null) {
                const parsed = parseFloat(saved);
                const closestIdx = EDITOR_ZOOM_LEVELS.reduce((prev, curr, idx) => {
                    return Math.abs(curr.scale - parsed) < Math.abs(EDITOR_ZOOM_LEVELS[prev].scale - parsed) ? idx : prev;
                }, DEFAULT_EDITOR_ZOOM_INDEX);
                currentEditorZoomIndex = closestIdx;
            } else {
                currentEditorZoomIndex = DEFAULT_EDITOR_ZOOM_INDEX;
            }
        } catch (e) {
            currentEditorZoomIndex = DEFAULT_EDITOR_ZOOM_INDEX;
        }

        applyEditorCardZoom();

        const bOut = document.getElementById('btn-editor-zoom-out') || btnEditorZoomOut;
        const bIn = document.getElementById('btn-editor-zoom-in') || btnEditorZoomIn;
        const bReset = document.getElementById('btn-editor-zoom-reset') || btnEditorZoomReset;
        if (bOut) bOut.onclick = zoomOutEditorCards;
        if (bIn) bIn.onclick = zoomInEditorCards;
        if (bReset) bReset.onclick = resetEditorCardZoom;

        const modal = document.getElementById('doc-page-editor-modal') || editorModal;
        if (modal) {
            modal.onwheel = (e) => {
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    if (e.deltaY < 0) {
                        zoomInEditorCards();
                    } else if (e.deltaY > 0) {
                        zoomOutEditorCards();
                    }
                }
            };
        }
    }

    function updateExtractModeUI() {
        const isMove = extractModeMoveRadio ? extractModeMoveRadio.checked : true;
        if (extractModeMoveLabel) {
            if (isMove) {
                extractModeMoveLabel.classList.add('border-blue-500', 'bg-blue-50/50', 'dark:bg-blue-950/20');
                extractModeMoveLabel.classList.remove('border-slate-200', 'dark:border-slate-700');
            } else {
                extractModeMoveLabel.classList.remove('border-blue-500', 'bg-blue-50/50', 'dark:bg-blue-950/20');
                extractModeMoveLabel.classList.add('border-slate-200', 'dark:border-slate-700');
            }
        }
        if (extractModeCopyLabel) {
            if (!isMove) {
                extractModeCopyLabel.classList.add('border-blue-500', 'bg-blue-50/50', 'dark:bg-blue-950/20');
                extractModeCopyLabel.classList.remove('border-slate-200', 'dark:border-slate-700');
            } else {
                extractModeCopyLabel.classList.remove('border-blue-500', 'bg-blue-50/50', 'dark:bg-blue-950/20');
                extractModeCopyLabel.classList.add('border-slate-200', 'dark:border-slate-700');
            }
        }
        if (btnExtractConfirmText) {
            btnExtractConfirmText.textContent = isMove ? 'Confirm & Move (تأكيد النقل والفصل)' : 'Confirm & Copy (تأكيد النسخ)';
        }
    }

    async function openPageEditor(doc, fallbackCategory = null) {
        if (!doc) return;
        initPageEditor();
        if (!editorModal) return;

        const vaultId = doc.vault_id || doc.id || doc.vaultId;
        if (!vaultId) return;

        activeEditorDoc = {
            ...doc,
            vault_id: vaultId,
            area_id: getResolvedArea(doc),
            house_id: getResolvedHouse(doc),
            category: doc.category || fallbackCategory || ''
        };

        selectedPageNumbers.clear();
        currentPageOrder = [];
        activePdfDoc = null;

        const effectiveTitle = activeEditorDoc.brief_arabic_title || activeEditorDoc.arabic_title || activeEditorDoc.filename || activeEditorDoc.title || 'Document';
        if (editorTitle) editorTitle.textContent = effectiveTitle;
        
        const initialTenant = activeEditorDoc.tenant || activeEditorDoc.tenant_name || activeEditorDoc.primary_tenant || '';
        if (editorSubtitle) {
            const cat = activeEditorDoc.category || 'عام';
            const ten = initialTenant ? initialTenant : 'جاري التحميل...';
            editorSubtitle.textContent = `${cat} • ${ten}`;
        }

        if (editorPageCountBadge) editorPageCountBadge.textContent = '...';
        if (editorGrid) editorGrid.innerHTML = '';
        if (editorLoading) editorLoading.classList.remove('hidden');

        updateSelectionUI();

        applyEditorCardZoom();
        editorModal.classList.remove('hidden');
        editorModal.style.display = 'flex';

        // Asynchronously fetch authoritative metadata directly from SQLite
        const metadataPromise = (async () => {
            try {
                let meta = null;
                const mRes = await fetch(getApiUrl(`/api/documents/${encodeURIComponent(vaultId)}/metadata`));
                if (mRes.ok) {
                    meta = await mRes.json();
                } else {
                    const fallbackArea = activeEditorDoc.area_id || 'default';
                    const fallbackHouse = activeEditorDoc.house_id || 'default';
                    const altRes = await fetch(getApiUrl(`/api/areas/${encodeURIComponent(fallbackArea)}/houses/${encodeURIComponent(fallbackHouse)}/documents/${encodeURIComponent(vaultId)}/metadata`));
                    if (altRes.ok) meta = await altRes.json();
                }
                if (meta && activeEditorDoc && (activeEditorDoc.vault_id === vaultId)) {
                    const resolvedTenantId = meta.tenantId || meta.tenant_id;
                    const resolvedTenantName = meta.tenantName || meta.tenant_name;
                    const resolvedAreaId = meta.areaId || meta.area_id;
                    const resolvedHouseId = meta.houseId || meta.house_id;
                    const resolvedCategory = meta.category;
                    const resolvedArabicTitle = meta.arabicTitle || meta.arabic_title;
                    const resolvedPrimaryDate = meta.primaryDate || meta.primary_date;
                    const resolvedPageCount = typeof meta.pageCount === 'number' ? meta.pageCount : (typeof meta.page_count === 'number' ? meta.page_count : 0);

                    if (resolvedTenantId) activeEditorDoc.tenant_id = resolvedTenantId;
                    if (resolvedTenantName) activeEditorDoc.tenant_name = resolvedTenantName;
                    if (resolvedAreaId && resolvedAreaId !== 'default') activeEditorDoc.area_id = resolvedAreaId;
                    if (resolvedHouseId && resolvedHouseId !== 'default') activeEditorDoc.house_id = resolvedHouseId;
                    if (resolvedCategory) activeEditorDoc.category = resolvedCategory;
                    if (resolvedArabicTitle) activeEditorDoc.brief_arabic_title = resolvedArabicTitle;
                    if (resolvedPrimaryDate) activeEditorDoc.primary_date = resolvedPrimaryDate;
                    if (resolvedPageCount > 0) activeEditorDoc.page_count = resolvedPageCount;

                    if (editorTitle && resolvedArabicTitle) {
                        editorTitle.textContent = resolvedArabicTitle;
                    }
                    if (editorSubtitle) {
                        const displayTenant = resolvedTenantName ? resolvedTenantName : 'كامل المنزل (عام)';
                        editorSubtitle.textContent = `${activeEditorDoc.category || 'عام'} • ${displayTenant}`;
                    }
                }
            } catch (mErr) {
                console.warn('Document metadata fetch warning:', mErr);
            } finally {
                if (editorSubtitle && (!activeEditorDoc.tenant_name && !initialTenant)) {
                    editorSubtitle.textContent = `${activeEditorDoc.category || 'عام'} • كامل المنزل (عام)`;
                }
            }
        })();

        await metadataPromise;

        const area = activeEditorDoc.area_id;
        const house = activeEditorDoc.house_id;

        try {
            const pdfUrl = resolvePdfUrl(area, house, vaultId, Date.now());
            
            if (typeof pdfjsLib !== 'undefined') {
                const loadingTask = pdfjsLib.getDocument({ url: pdfUrl });
                activePdfDoc = await loadingTask.promise;
                const totalPages = activePdfDoc.numPages;

                if (editorPageCountBadge) {
                    editorPageCountBadge.textContent = `${totalPages} صفحة • ${totalPages} page${totalPages > 1 ? 's' : ''}`;
                }

                currentPageOrder = Array.from({ length: totalPages }, (_, i) => i + 1);
                await renderThumbnails();
            } else {
                // Fallback if pdfjs is not available
                const totalPages = activeEditorDoc.page_count || 1;
                currentPageOrder = Array.from({ length: totalPages }, (_, i) => i + 1);
                renderFallbackCards();
            }
        } catch (err) {
            console.error('Failed to load document in page editor:', err);
            const totalPages = activeEditorDoc.page_count || 1;
            currentPageOrder = Array.from({ length: totalPages }, (_, i) => i + 1);
            renderFallbackCards();
        } finally {
            if (editorLoading) editorLoading.classList.add('hidden');
        }

        await metadataPromise;
    }

    function closePageEditor() {
        if (!editorModal) return;
        closeExtractSubmodal();
        editorModal.classList.add('hidden');
        editorModal.style.display = 'none';
        if (editorGrid) editorGrid.innerHTML = '';
        activeEditorDoc = null;
        activePdfDoc = null;
        selectedPageNumbers.clear();
        currentPageOrder = [];
        cardRotations = {};
        draggedPages = [];
    }

    async function renderThumbnails() {
        if (!editorGrid || !activePdfDoc) return;
        editorGrid.innerHTML = '';

        for (let i = 0; i < currentPageOrder.length; i++) {
            const pageNum = currentPageOrder[i];
            const card = createPageCard(pageNum, i + 1, currentPageOrder.length);
            editorGrid.appendChild(card);

            // Render PDF canvas asynchronously
            renderPageCanvas(card, pageNum);
        }
    }

    function renderFallbackCards() {
        if (!editorGrid) return;
        editorGrid.innerHTML = '';
        for (let i = 0; i < currentPageOrder.length; i++) {
            const pageNum = currentPageOrder[i];
            const card = createPageCard(pageNum, i + 1, currentPageOrder.length);
            editorGrid.appendChild(card);
            if (cardRotations[pageNum]) {
                const placeholder = card.querySelector('.thumbnail-placeholder');
                if (placeholder) placeholder.style.transform = `rotate(${cardRotations[pageNum]}deg)`;
            }
        }
    }

    function createPageCard(actualPageNum, displayPos, totalPages) {
        const card = document.createElement('div');
        card.className = 'page-editor-card relative bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md transition-all flex flex-col overflow-hidden cursor-pointer select-none group';
        card.setAttribute('data-page-num', actualPageNum);
        card.setAttribute('data-display-pos', displayPos);
        card.setAttribute('draggable', 'true');

        const isSelected = selectedPageNumbers.has(actualPageNum);
        if (isSelected) {
            card.classList.add('border-blue-500', 'ring-2', 'ring-blue-400/50', 'bg-blue-50/20');
        }

        const canDelete = (typeof window !== 'undefined' && window.authManager) ? window.authManager.hasDeletePermission() : true;
        const deleteBtnHtml = canDelete
            ? `<button type="button" class="btn-card-delete p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/50 transition-colors cursor-pointer" title="Delete page • حذف الصفحة">
                <svg class="w-4 h-4 text-rose-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>`
            : '<div class="w-4"></div>';

        card.innerHTML = `
            <!-- Card Top Bar: Actions & Selection -->
            <div class="px-3 py-2 bg-slate-50 dark:bg-slate-900 border-b border-slate-100 dark:border-slate-700/80 flex items-center justify-between gap-1 flex-shrink-0">
                <div class="flex items-center gap-1">
                    ${deleteBtnHtml}
                    <button type="button" class="btn-card-rotate p-1.5 rounded-lg text-slate-400 hover:text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-950/50 transition-colors cursor-pointer" title="Rotate 90° clockwise • تدوير الصفحة 90 درجة">
                        <svg class="w-4 h-4 text-amber-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                    </button>
                </div>
                <div class="flex items-center gap-1">
                    <button type="button" class="btn-move-left p-1 rounded-md text-slate-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950/40 disabled:opacity-30 disabled:pointer-events-none transition-all" title="Move earlier • تقديم الصفحة" ${displayPos <= 1 ? 'disabled' : ''}>
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/></svg>
                    </button>
                    <button type="button" class="btn-move-right p-1 rounded-md text-slate-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950/40 disabled:opacity-30 disabled:pointer-events-none transition-all" title="Move later • تأخير الصفحة" ${displayPos >= totalPages ? 'disabled' : ''}>
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/></svg>
                    </button>
                    <div class="card-checkbox-pill w-5 h-5 rounded-md border flex items-center justify-center transition-all ml-1 ${isSelected ? 'bg-blue-600 border-blue-600 text-white shadow-2xs' : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-transparent'}">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>
                    </div>
                </div>
            </div>

            <!-- Card Thumbnail Body -->
            <div class="card-thumbnail-container flex-1 min-h-[160px] sm:min-h-[200px] p-3 flex items-center justify-center bg-slate-100/50 dark:bg-slate-900/40 overflow-hidden" style="min-height: var(--editor-thumb-height, 280px); height: var(--editor-thumb-height, 280px);">
                <div class="thumbnail-placeholder text-center text-slate-400 flex flex-col items-center gap-2">
                    <svg class="w-8 h-8 opacity-40 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                    <span class="text-xs font-mono">Page ${actualPageNum}</span>
                </div>
            </div>

            <!-- Card Footer: Page Label -->
            <div class="px-3 py-1.5 bg-slate-50 dark:bg-slate-900 border-t border-slate-100 dark:border-slate-700/80 flex items-center justify-between text-xs font-semibold text-slate-600 dark:text-slate-300">
                <span class="font-mono">Page ${displayPos}</span>
                <span class="text-[11px] text-slate-400 font-normal">#${actualPageNum}</span>
            </div>
        `;

        // Card tap / click toggles selection
        card.onclick = (e) => {
            if (e.target.closest('.btn-card-delete') || e.target.closest('.btn-card-rotate') || e.target.closest('.btn-move-left') || e.target.closest('.btn-move-right')) {
                return;
            }
            togglePageSelection(actualPageNum);
        };

        // 1-tap delete button on card
        const btnDel = card.querySelector('.btn-card-delete');
        if (btnDel) {
            btnDel.onclick = (e) => {
                e.stopPropagation();
                handleDeleteSinglePage(actualPageNum, displayPos);
            };
        }

        // 1-tap rotate button on card (90 degrees clockwise)
        const btnRot = card.querySelector('.btn-card-rotate');
        if (btnRot) {
            btnRot.onclick = (e) => {
                e.stopPropagation();
                rotatePage(actualPageNum, 90);
            };
        }

        // Move left / right buttons
        const btnLeft = card.querySelector('.btn-move-left');
        if (btnLeft) {
            btnLeft.onclick = (e) => {
                e.stopPropagation();
                shiftPageOrder(displayPos - 1, -1);
            };
        }

        const btnRight = card.querySelector('.btn-move-right');
        if (btnRight) {
            btnRight.onclick = (e) => {
                e.stopPropagation();
                shiftPageOrder(displayPos - 1, 1);
            };
        }

        // Drag and drop events
        card.ondragstart = (e) => handleCardDragStart(e, actualPageNum, card);
        card.ondragover = (e) => handleCardDragOver(e, card);
        card.ondragleave = (e) => handleCardDragLeave(e, card);
        card.ondrop = (e) => handleCardDrop(e, card);
        card.ondragend = (e) => handleCardDragEnd(e);

        return card;
    }

    async function renderPageCanvas(cardEl, pageNum) {
        if (!activePdfDoc || !cardEl) return;
        try {
            const page = await activePdfDoc.getPage(pageNum);
            const container = cardEl.querySelector('.card-thumbnail-container');
            if (!container) return;

            const targetWidth = Math.max(container.clientWidth || 240, 160);
            const targetHeight = Math.max(container.clientHeight || 280, 190);
            const unscaled = page.getViewport({ scale: 1.0 });
            const scaleX = targetWidth / unscaled.width;
            const scaleY = targetHeight / unscaled.height;
            const scale = Math.min(scaleX, scaleY);
            const viewport = page.getViewport({ scale });

            const outputScale = (typeof window !== 'undefined' && window.devicePixelRatio) || 1;
            const canvas = document.createElement('canvas');
            canvas.className = 'max-w-full max-h-full object-contain rounded shadow-2xs block mx-auto pointer-events-none select-none';
            canvas.width = Math.floor(viewport.width * outputScale);
            canvas.height = Math.floor(viewport.height * outputScale);
            canvas.style.maxWidth = '100%';
            canvas.style.maxHeight = '100%';
            canvas.style.width = 'auto';
            canvas.style.height = 'auto';

            const ctx = canvas.getContext('2d');
            if (ctx) {
                ctx.scale(outputScale, outputScale);
            }

            await page.render({ canvasContext: ctx, viewport }).promise;

            if (cardRotations[pageNum]) {
                canvas.style.transform = `rotate(${cardRotations[pageNum]}deg)`;
            }

            container.innerHTML = '';
            container.appendChild(canvas);
        } catch (err) {
            console.warn(`Could not render thumbnail for page ${pageNum}:`, err);
        }
    }

    function togglePageSelection(pageNum) {
        if (selectedPageNumbers.has(pageNum)) {
            selectedPageNumbers.delete(pageNum);
        } else {
            selectedPageNumbers.add(pageNum);
        }
        updateCardSelectionState(pageNum);
        updateSelectionUI();
    }

    function updateCardSelectionState(pageNum) {
        if (!editorGrid) return;
        const card = editorGrid.querySelector(`div[data-page-num="${pageNum}"]`);
        if (!card) return;

        const isSelected = selectedPageNumbers.has(pageNum);
        const pill = card.querySelector('.card-checkbox-pill');

        if (isSelected) {
            card.classList.add('border-blue-500', 'ring-2', 'ring-blue-400/50', 'bg-blue-50/20');
            card.classList.remove('border-slate-200', 'dark:border-slate-700');
            if (pill) {
                pill.className = 'card-checkbox-pill w-5 h-5 rounded-md border flex items-center justify-center transition-all ml-1 bg-blue-600 border-blue-600 text-white shadow-2xs';
            }
        } else {
            card.classList.remove('border-blue-500', 'ring-2', 'ring-blue-400/50', 'bg-blue-50/20');
            card.classList.add('border-slate-200', 'dark:border-slate-700');
            if (pill) {
                pill.className = 'card-checkbox-pill w-5 h-5 rounded-md border flex items-center justify-center transition-all ml-1 border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-transparent';
            }
        }
    }

    function selectAllPages() {
        currentPageOrder.forEach(p => selectedPageNumbers.add(p));
        currentPageOrder.forEach(p => updateCardSelectionState(p));
        updateSelectionUI();
    }

    function deselectAllPages() {
        selectedPageNumbers.clear();
        currentPageOrder.forEach(p => updateCardSelectionState(p));
        updateSelectionUI();
    }

    function updateSelectionUI() {
        const count = selectedPageNumbers.size;
        if (editorSelectedCount) {
            editorSelectedCount.textContent = count > 0 ? `(${count} selected • محدد)` : '';
        }

        if (btnDeleteSelected) {
            const canDelete = (typeof window !== 'undefined' && window.authManager) ? window.authManager.hasDeletePermission() : true;
            if (!canDelete) {
                btnDeleteSelected.classList.add('hidden');
                btnDeleteSelected.disabled = true;
            } else {
                btnDeleteSelected.classList.remove('hidden');
                btnDeleteSelected.disabled = count === 0;
                const textSpan = btnDeleteSelected.querySelector('.btn-text');
                if (textSpan) {
                    textSpan.textContent = count > 0 ? `Delete Selected (${count})` : 'Delete Selected';
                }
            }
        }

        if (btnRotateSelected) {
            btnRotateSelected.disabled = count === 0;
            const textSpan = btnRotateSelected.querySelector('.btn-text');
            if (textSpan) {
                textSpan.textContent = count > 0 ? `Rotate 90° (${count})` : 'Rotate 90° (تدوير)';
            }
        }

        if (btnCopySelected) {
            btnCopySelected.disabled = count === 0;
            const textSpan = btnCopySelected.querySelector('.btn-text');
            if (textSpan) {
                textSpan.textContent = count > 0 ? `Copy Selected (${count})...` : 'Copy Pages...';
            }
        }

        if (btnExtractSelected) {
            btnExtractSelected.disabled = count === 0;
            const textSpan = btnExtractSelected.querySelector('.btn-text');
            if (textSpan) {
                textSpan.textContent = count > 0 ? `Move Selected (${count})...` : 'Move Pages...';
            }
        }
    }

    async function applyAndPersistPageOrder(newOrder) {
        if (isReordering) return;
        const previousOrder = [...currentPageOrder];
        isReordering = true;

        try {
            currentPageOrder = newOrder;
            if (activePdfDoc) {
                await renderThumbnails();
            } else {
                renderFallbackCards();
            }

            // Automatically persist reordering to backend
            if (activeEditorDoc) {
                const area = activeEditorDoc.area_id;
                const house = activeEditorDoc.house_id;
                const vaultId = activeEditorDoc.vault_id || activeEditorDoc.id;
                let endpoint;
                if (area && area !== 'default' && house && house !== 'default') {
                    endpoint = `/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(vaultId)}/reorder-pages`;
                } else {
                    endpoint = `/api/documents/${encodeURIComponent(vaultId)}/reorder-pages`;
                }

                try {
                    const res = await fetch(getApiUrl(endpoint), {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ page_order: currentPageOrder })
                    });
                    if (res.ok) {
                        // The PDF on disk is now physically rewritten into the new order.
                        // Reset currentPageOrder to 1..N so future shifts/drags are relative to the new file.
                        currentPageOrder = Array.from({ length: currentPageOrder.length }, (_, idx) => idx + 1);

                        // Reload activePdfDoc with cache-busting
                        const cacheBust = Date.now();
                        const pdfUrl = resolvePdfUrl(area, house, vaultId, cacheBust);
                        if (typeof pdfjsLib !== 'undefined') {
                            try {
                                const loadingTask = pdfjsLib.getDocument({ url: pdfUrl });
                                activePdfDoc = await loadingTask.promise;
                                await renderThumbnails();
                            } catch (loadErr) {
                                console.warn('Could not reload activePdfDoc after reorder:', loadErr);
                            }
                        }

                        // Notify document viewer panel to reload the PDF with cache-busting
                        if (typeof window !== 'undefined' && typeof window.reloadCurrentDocument === 'function') {
                            window.reloadCurrentDocument(true);
                        }
                    } else {
                        // Revert local swap on failure
                        currentPageOrder = previousOrder;
                        if (activePdfDoc) await renderThumbnails();
                        else renderFallbackCards();
                    }
                } catch (err) {
                    console.warn('Reorder pages API warning:', err);
                    currentPageOrder = previousOrder;
                    if (activePdfDoc) await renderThumbnails();
                    else renderFallbackCards();
                }
            }
        } finally {
            isReordering = false;
        }
    }

    async function shiftPageOrder(currentIndex, direction) {
        if (isReordering) return;
        const targetIndex = currentIndex + direction;
        if (targetIndex < 0 || targetIndex >= currentPageOrder.length) return;

        const newOrder = [...currentPageOrder];
        const temp = newOrder[currentIndex];
        newOrder[currentIndex] = newOrder[targetIndex];
        newOrder[targetIndex] = temp;

        await applyAndPersistPageOrder(newOrder);
    }

    async function movePagesToTarget(pagesToMove, targetPageNum, dropBefore) {
        if (!pagesToMove || pagesToMove.length === 0 || !targetPageNum) return;
        if (pagesToMove.includes(targetPageNum)) return; // Dropped on self

        // Filter out moved pages while keeping target
        const remaining = currentPageOrder.filter(p => !pagesToMove.includes(p));
        const targetIdx = remaining.indexOf(targetPageNum);
        if (targetIdx === -1) return;

        const insertIdx = dropBefore ? targetIdx : targetIdx + 1;
        const newOrder = [
            ...remaining.slice(0, insertIdx),
            ...pagesToMove,
            ...remaining.slice(insertIdx)
        ];

        // If order hasn't changed, ignore
        if (newOrder.length === currentPageOrder.length && newOrder.every((p, i) => p === currentPageOrder[i])) {
            return;
        }

        await applyAndPersistPageOrder(newOrder);
    }

    function handleCardDragStart(e, pageNum, cardEl) {
        if (isReordering || isRotating) {
            if (e && e.preventDefault) e.preventDefault();
            return;
        }
        // Multi-page drag: if dragged card is selected and multiple are selected, move all selected
        if (selectedPageNumbers.has(pageNum) && selectedPageNumbers.size > 1) {
            draggedPages = currentPageOrder.filter(p => selectedPageNumbers.has(p));
        } else {
            draggedPages = [pageNum];
        }

        if (e && e.dataTransfer) {
            e.dataTransfer.effectAllowed = 'move';
            try {
                e.dataTransfer.setData('text/plain', JSON.stringify({ draggedPages }));
            } catch (err) {}
        }

        if (cardEl) cardEl.classList.add('dragging');
        if (draggedPages.length > 1 && editorGrid) {
            draggedPages.forEach(p => {
                const otherCard = editorGrid.querySelector(`div[data-page-num="${p}"]`);
                if (otherCard) otherCard.classList.add('dragging');
            });
        }
    }

    function handleCardDragOver(e, card) {
        if (e && e.preventDefault) e.preventDefault();
        if (!draggedPages || draggedPages.length === 0) return;
        if (e && e.dataTransfer) e.dataTransfer.dropEffect = 'move';

        const targetPageNum = parseInt(card.getAttribute('data-page-num'), 10);
        if (draggedPages.includes(targetPageNum)) {
            card.classList.remove('page-drop-before', 'page-drop-after');
            return;
        }

        const rect = card.getBoundingClientRect();
        const midX = (rect && rect.width > 0) ? (rect.left + rect.width / 2) : 0;
        const isBefore = (rect && rect.width > 0 && e && typeof e.clientX === 'number') ? (e.clientX < midX) : true;

        if (isBefore) {
            card.classList.add('page-drop-before');
            card.classList.remove('page-drop-after');
        } else {
            card.classList.add('page-drop-after');
            card.classList.remove('page-drop-before');
        }
    }

    function handleCardDragLeave(e, card) {
        card.classList.remove('page-drop-before', 'page-drop-after');
    }

    async function handleCardDrop(e, targetCard) {
        if (e) {
            if (e.preventDefault) e.preventDefault();
            if (e.stopPropagation) e.stopPropagation();
        }

        if (editorGrid) {
            editorGrid.querySelectorAll('.page-editor-card').forEach(c => {
                c.classList.remove('dragging', 'page-drop-before', 'page-drop-after');
            });
        }

        if (!draggedPages || draggedPages.length === 0) return;

        const targetPageNum = parseInt(targetCard.getAttribute('data-page-num'), 10);
        if (!targetPageNum) return;

        const rect = targetCard.getBoundingClientRect();
        const midX = (rect && rect.width > 0) ? (rect.left + rect.width / 2) : 0;
        const dropBefore = (rect && rect.width > 0 && e && typeof e.clientX === 'number') ? (e.clientX < midX) : true;

        const pages = [...draggedPages];
        draggedPages = [];
        await movePagesToTarget(pages, targetPageNum, dropBefore);
    }

    function handleCardDragEnd(e) {
        if (editorGrid) {
            editorGrid.querySelectorAll('.page-editor-card').forEach(c => {
                c.classList.remove('dragging', 'page-drop-before', 'page-drop-after');
            });
        }
        draggedPages = [];
    }

    async function rotatePage(pageNum, angle = 90) {
        await rotatePages([pageNum], angle);
    }

    async function rotateSelectedPages(angle = 90) {
        if (selectedPageNumbers.size === 0) return;
        const pages = Array.from(selectedPageNumbers);
        await rotatePages(pages, angle);
    }

    async function rotatePages(pagesToRotate, angle = 90) {
        if (!activeEditorDoc || isRotating || isReordering || !pagesToRotate || pagesToRotate.length === 0) return;
        isRotating = true;

        // Immediate visual feedback via CSS rotation transform
        pagesToRotate.forEach(p => {
            cardRotations[p] = ((cardRotations[p] || 0) + angle) % 360;
            if (editorGrid) {
                const card = editorGrid.querySelector(`div[data-page-num="${p}"]`);
                if (card) {
                    const thumb = card.querySelector('.card-thumbnail-container canvas, .card-thumbnail-container img, .card-thumbnail-container .thumbnail-placeholder');
                    if (thumb) {
                        thumb.style.transform = `rotate(${cardRotations[p]}deg)`;
                    }
                }
            }
        });

        const area = activeEditorDoc.area_id;
        const house = activeEditorDoc.house_id;
        const vaultId = activeEditorDoc.vault_id || activeEditorDoc.id;

        try {
            let endpoint;
            if (area && area !== 'default' && house && house !== 'default') {
                endpoint = `/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(vaultId)}/rotate-pages`;
            } else {
                endpoint = `/api/documents/${encodeURIComponent(vaultId)}/rotate-pages`;
            }

            const rotationsMap = {};
            pagesToRotate.forEach(p => {
                rotationsMap[p.toString()] = angle;
            });

            const res = await fetch(getApiUrl(endpoint), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    rotations: rotationsMap,
                    pages: pagesToRotate,
                    angle: angle
                })
            });

            if (res.ok) {
                // Rotation permanently persisted to disk
                pagesToRotate.forEach(p => delete cardRotations[p]);

                const cacheBust = Date.now();
                const pdfUrl = resolvePdfUrl(area, house, vaultId, cacheBust);
                if (typeof pdfjsLib !== 'undefined') {
                    try {
                        const loadingTask = pdfjsLib.getDocument({ url: pdfUrl });
                        activePdfDoc = await loadingTask.promise;
                        await renderThumbnails();
                    } catch (loadErr) {
                        console.warn('Could not reload activePdfDoc after rotate:', loadErr);
                    }
                } else {
                    renderFallbackCards();
                }

                if (typeof window !== 'undefined' && typeof window.reloadCurrentDocument === 'function') {
                    window.reloadCurrentDocument(true);
                }

                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
                if (toast) {
                    const count = pagesToRotate.length;
                    toast(`تم تدوير وحفظ ${count > 1 ? count + ' صفحات' : 'الصفحة'} بنجاح • Rotated ${count} page${count > 1 ? 's' : ''} (90°)`, 'success');
                }
            } else {
                // Revert visual transform on error
                pagesToRotate.forEach(p => {
                    cardRotations[p] = ((cardRotations[p] || 0) - angle + 360) % 360;
                    if (editorGrid) {
                        const card = editorGrid.querySelector(`div[data-page-num="${p}"]`);
                        if (card) {
                            const thumb = card.querySelector('.card-thumbnail-container canvas, .card-thumbnail-container img, .card-thumbnail-container .thumbnail-placeholder');
                            if (thumb) {
                                thumb.style.transform = cardRotations[p] ? `rotate(${cardRotations[p]}deg)` : '';
                            }
                        }
                    }
                });
                const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
                if (toast) toast('Failed to rotate pages • فشل تدوير الصفحات', 'error');
            }
        } catch (err) {
            console.error('Rotate pages error:', err);
            pagesToRotate.forEach(p => {
                cardRotations[p] = ((cardRotations[p] || 0) - angle + 360) % 360;
                if (editorGrid) {
                    const card = editorGrid.querySelector(`div[data-page-num="${p}"]`);
                    if (card) {
                        const thumb = card.querySelector('.card-thumbnail-container canvas, .card-thumbnail-container img, .card-thumbnail-container .thumbnail-placeholder');
                        if (thumb) {
                            thumb.style.transform = cardRotations[p] ? `rotate(${cardRotations[p]}deg)` : '';
                        }
                    }
                }
            });
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast('Error rotating pages • خطأ أثناء تدوير الصفحات', 'error');
        } finally {
            isRotating = false;
        }
    }

    async function handleDeleteSinglePage(pageNum, displayPos) {
        if (!activeEditorDoc) return;

        const canDelete = (typeof window !== 'undefined' && window.authManager) ? window.authManager.hasDeletePermission() : true;
        if (!canDelete) {
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast('عذراً: ليس لديك صلاحية حذف صفحات الوثائق (قراءة ورفع فقط) • Page deletion is restricted for Contributor accounts.', 'error');
            return;
        }

        const confirmMsg = `Are you sure you want to delete Page ${displayPos}? This cannot be undone.\n\nهل أنت متأكد من حذف الصفحة ${displayPos} نهائياً؟`;
        if (!window.confirm(confirmMsg)) return;

        await executeDeletePages([pageNum]);
    }

    async function handleDeleteSelectedPages() {
        if (!activeEditorDoc || selectedPageNumbers.size === 0) return;

        const canDelete = (typeof window !== 'undefined' && window.authManager) ? window.authManager.hasDeletePermission() : true;
        if (!canDelete) {
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast('عذراً: ليس لديك صلاحية حذف صفحات الوثائق (قراءة ورفع فقط) • Page deletion is restricted for Contributor accounts.', 'error');
            return;
        }

        const count = selectedPageNumbers.size;
        const confirmMsg = `Are you sure you want to delete ${count} selected page${count > 1 ? 's' : ''}? This cannot be undone.\n\nهل أنت متأكد من حذف ${count} صفحة محددة نهائياً؟`;
        if (!window.confirm(confirmMsg)) return;

        await executeDeletePages(Array.from(selectedPageNumbers));
    }

    async function executeDeletePages(pagesToDelete) {
        if (!activeEditorDoc || pagesToDelete.length === 0) return;

        const canDelete = (typeof window !== 'undefined' && window.authManager) ? window.authManager.hasDeletePermission() : true;
        if (!canDelete) {
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast('عذراً: ليس لديك صلاحية حذف صفحات الوثائق (قراءة ورفع فقط) • Page deletion is restricted for Contributor accounts.', 'error');
            return;
        }
        const area = activeEditorDoc.area_id || 'default';
        const house = activeEditorDoc.house_id || 'default';
        const vaultId = activeEditorDoc.vault_id || activeEditorDoc.id;
        const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);

        if (editorLoading) editorLoading.classList.remove('hidden');

        try {
            let res = await fetch(getApiUrl(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(vaultId)}/delete-pages`), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ page_numbers: pagesToDelete })
            });

            // Fallback to universal endpoint if area/house route failed
            if (!res.ok) {
                const altRes = await fetch(getApiUrl(`/api/documents/${encodeURIComponent(vaultId)}/delete-pages`), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ page_numbers: pagesToDelete })
                });
                if (altRes.ok) {
                    res = altRes;
                }
            }

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || errData.error || errData.message || 'Failed to delete pages');
            }

            const data = await res.json();

            if (toast) {
                toast(`Successfully deleted ${pagesToDelete.length} page${pagesToDelete.length > 1 ? 's' : ''}`, 'success');
            }

            if (data.document_deleted || data.remaining_pages === 0) {
                // Entire document is gone
                closePageEditor();
                if (typeof window !== 'undefined' && typeof window.closeDocument === 'function') {
                    window.closeDocument();
                }
            } else {
                // Remove pages from local order and reload
                currentPageOrder = currentPageOrder.filter(p => !pagesToDelete.includes(p));
                pagesToDelete.forEach(p => selectedPageNumbers.delete(p));
                activeEditorDoc.page_count = data.remaining_pages;
                
                // Re-open editor with updated state (and cache-busting)
                await openPageEditor(activeEditorDoc);
            }

            // Live refresh UI & Document Viewer
            if (typeof window !== 'undefined' && typeof window.reloadCurrentDocument === 'function') {
                window.reloadCurrentDocument(true);
            }
            if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                await window.refreshCurrentTab(area, house);
            } else if (typeof refreshCurrentTab === 'function') {
                await refreshCurrentTab(area, house);
            }
            if (typeof window !== 'undefined' && typeof window.loadTree === 'function') {
                await window.loadTree();
            }
        } catch (err) {
            console.error('Delete pages error:', err);
            if (toast) toast(err.message || 'Failed to delete pages', 'error');
            else alert(err.message || 'Failed to delete pages');
        } finally {
            if (editorLoading) editorLoading.classList.add('hidden');
        }
    }

    async function openExtractSubmodal(initialMode = 'move') {
        if (!activeEditorDoc) return;
        if (selectedPageNumbers.size === 0) {
            const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);
            if (toast) toast('Please select at least one page to separate • يرجى تحديد صفحة واحدة على الأقل', 'info');
            else alert('Please select at least one page to separate • يرجى تحديد صفحة واحدة على الأقل');
            return;
        }

        if (!extractModal) {
            extractModal = document.getElementById('extract-pages-submodal');
        }
        if (!extractModal) return;

        // Set Move vs Copy Mode
        if (extractModeMoveRadio && extractModeCopyRadio) {
            if (initialMode === 'copy') {
                extractModeCopyRadio.checked = true;
                extractModeMoveRadio.checked = false;
            } else {
                extractModeMoveRadio.checked = true;
                extractModeCopyRadio.checked = false;
            }
            updateExtractModeUI();
        }

        // 1. Immediately display on top of everything
        extractModal.style.zIndex = '9999';
        extractModal.classList.remove('hidden');
        extractModal.style.display = 'flex';
        if (editorModal) editorModal.classList.add('opacity-40');

        const count = selectedPageNumbers.size;
        const submodalCountBadge = document.getElementById('extract-pages-count-badge');
        if (submodalCountBadge) {
            submodalCountBadge.textContent = `${count} صفحة محددة • ${count} page${count > 1 ? 's' : ''}`;
        }

        // Populate Categories
        if (extractCategorySelect) {
            extractCategorySelect.innerHTML = '';
            STANDARD_FOLDERS.forEach(cat => {
                const opt = document.createElement('option');
                opt.value = cat;
                opt.textContent = cat;
                extractCategorySelect.appendChild(opt);
            });

            // Default suggestion based on common forms:
            extractCategorySelect.value = "04 - محضر تسليم مفتاح";

            const customOpt = document.createElement('option');
            customOpt.value = '__custom__';
            customOpt.textContent = '➕ Custom Category...';
            extractCategorySelect.appendChild(customOpt);
        }

        if (extractCustomCatContainer) extractCustomCatContainer.classList.add('hidden');
        if (extractCustomCatInput) extractCustomCatInput.value = '';

        // Pre-fill Title & Date immediately
        if (extractTitleInput) {
            extractTitleInput.value = extractCategorySelect ? extractCategorySelect.value : 'مستند مستخرج';
        }
        if (extractDateInput) {
            const rawDate = activeEditorDoc.primary_date || activeEditorDoc.date || '';
            const match = String(rawDate).trim().match(/^\d{4}-\d{2}-\d{2}/);
            extractDateInput.value = match ? match[0] : '';
        }
        if (extractNotesInput) {
            extractNotesInput.value = '';
        }

        // Populate Tenants immediately with general option and resident tenant
        if (extractTenantSelect) {
            extractTenantSelect.innerHTML = '';

            const generalOpt = document.createElement('option');
            generalOpt.value = '';
            generalOpt.textContent = 'كامل المنزل (عام) • General House Document';
            extractTenantSelect.appendChild(generalOpt);

            if (activeEditorDoc.tenant_name && activeEditorDoc.tenant_id) {
                const initOpt = document.createElement('option');
                initOpt.value = activeEditorDoc.tenant_id;
                initOpt.textContent = `${activeEditorDoc.tenant_name} (ساكن)`;
                initOpt.selected = true;
                extractTenantSelect.appendChild(initOpt);
            }

            const area = activeEditorDoc.area_id;
            const house = activeEditorDoc.house_id;
            if (area && house && area !== 'default' && house !== 'default') {
                try {
                    const tRes = await fetch(getApiUrl(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/tenants`));
                    if (tRes.ok) {
                        const tenants = await tRes.json();
                        if (Array.isArray(tenants) && tenants.length > 0) {
                            extractTenantSelect.innerHTML = '';
                            extractTenantSelect.appendChild(generalOpt);
                            let tenantMatched = false;
                            tenants.forEach(t => {
                                const opt = document.createElement('option');
                                opt.value = t.id;
                                opt.textContent = t.is_resident === 1 ? `${t.name} (ساكن)` : `${t.name} (متقدم)`;
                                if (t.id === activeEditorDoc.tenant_id) {
                                    opt.selected = true;
                                    tenantMatched = true;
                                }
                                extractTenantSelect.appendChild(opt);
                            });
                            if (!tenantMatched && !activeEditorDoc.tenant_id) {
                                generalOpt.selected = true;
                            }
                        }
                    }
                } catch (_) {}
            }
        }
    }

    function closeExtractSubmodal() {
        if (!extractModal) {
            extractModal = document.getElementById('extract-pages-submodal');
        }
        if (extractModal) {
            extractModal.classList.add('hidden');
            extractModal.style.display = 'none';
        }
        if (editorModal) editorModal.classList.remove('opacity-40');
    }

    async function executeExtractPages() {
        if (!activeEditorDoc || selectedPageNumbers.size === 0) return;

        let targetCat = extractCategorySelect ? extractCategorySelect.value : '';
        if (targetCat === '__custom__' && extractCustomCatInput) {
            targetCat = extractCustomCatInput.value.trim();
        }
        if (!targetCat) {
            alert('Please select or specify a target category.');
            return;
        }

        const targetTenantVal = extractTenantSelect ? extractTenantSelect.value : '';
        const targetTenantId = targetTenantVal ? parseInt(targetTenantVal, 10) : (activeEditorDoc.tenant_id || null);
        const targetTitle = extractTitleInput ? extractTitleInput.value.trim() : targetCat;
        const targetDate = extractDateInput ? extractDateInput.value.trim() : '';
        const targetNotes = extractNotesInput ? extractNotesInput.value.trim() : '';
        const isMove = extractModeMoveRadio ? extractModeMoveRadio.checked : true;

        const area = activeEditorDoc.area_id || 'default';
        const house = activeEditorDoc.house_id || 'default';
        const vaultId = activeEditorDoc.vault_id || activeEditorDoc.id;
        const toast = (typeof showToast === 'function') ? showToast : (typeof window !== 'undefined' ? window.showToast : null);

        if (btnExtractConfirm) btnExtractConfirm.disabled = true;
        if (btnExtractConfirmText) btnExtractConfirmText.textContent = isMove ? 'Moving...' : 'Copying...';

        try {
            const reqBody = JSON.stringify({
                page_numbers: Array.from(selectedPageNumbers),
                target_category: targetCat,
                target_tenant_id: targetTenantId,
                target_title: targetTitle,
                target_date: targetDate,
                target_notes: targetNotes,
                delete_from_source: isMove
            });

            // Primary call to area/house route
            let res = await fetch(getApiUrl(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(vaultId)}/extract-pages`), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: reqBody
            });

            // Fallback to universal endpoint if area/house route failed
            if (!res.ok) {
                const altRes = await fetch(getApiUrl(`/api/documents/${encodeURIComponent(vaultId)}/extract-pages`), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: reqBody
                });
                if (altRes.ok) {
                    res = altRes;
                }
            }

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || errData.error || errData.message || 'Failed to extract pages');
            }

            const data = await res.json();

            const actionVerb = isMove ? 'moved & separated' : 'copied';
            const actionVerbAr = isMove ? 'تم النقل والفصل' : 'تم النسخ';
            if (toast) {
                toast(`Successfully ${actionVerb} into "${data.new_title || targetCat}"! (${actionVerbAr})`, 'success');
            }

            closeExtractSubmodal();

            if (isMove) {
                closePageEditor();
                if (data.document_deleted || data.remaining_pages === 0) {
                    if (typeof window !== 'undefined' && typeof window.closeDocument === 'function') {
                        window.closeDocument();
                    }
                }
            } else {
                // In Copy mode, source document is unchanged.
                // Clear selection and re-render selection UI
                selectedPageNumbers.clear();
                updateSelectionUI();
                if (editorGrid) {
                    editorGrid.querySelectorAll('.page-editor-card').forEach(card => {
                        card.classList.remove('border-blue-500', 'ring-2', 'ring-blue-400/50', 'bg-blue-50/20');
                        const checkmark = card.querySelector('.page-card-checkmark');
                        if (checkmark) checkmark.classList.add('opacity-0');
                    });
                }
            }

            // Live refresh UI & Document Viewer Panel
            if (typeof window !== 'undefined' && typeof window.reloadCurrentDocument === 'function') {
                window.reloadCurrentDocument(true);
            }
            if (typeof window !== 'undefined' && typeof window.refreshCurrentTab === 'function') {
                await window.refreshCurrentTab(area, house);
            } else if (typeof refreshCurrentTab === 'function') {
                await refreshCurrentTab(area, house);
            }
            if (typeof window !== 'undefined' && typeof window.loadTree === 'function') {
                await window.loadTree();
            }

            // If move succeeded and created a new document, open it
            if (isMove && data.new_vault_id && typeof window !== 'undefined' && typeof window.openDocument === 'function') {
                window.openDocument(data.new_vault_id, data.new_title || targetCat, data.new_category);
            }
        } catch (err) {
            console.error('Extract pages error:', err);
            if (toast) toast(err.message || 'Failed to extract pages', 'error');
            else alert(err.message || 'Failed to extract pages');
        } finally {
            if (btnExtractConfirm) btnExtractConfirm.disabled = false;
            updateExtractModeUI();
        }
    }

    // Expose globals
    window.openPageEditor = openPageEditor;
    window.closePageEditor = closePageEditor;
    window.initPageEditor = initPageEditor;
    window.zoomInEditorCards = zoomInEditorCards;
    window.zoomOutEditorCards = zoomOutEditorCards;
    window.resetEditorCardZoom = resetEditorCardZoom;
    window.applyEditorCardZoom = applyEditorCardZoom;
    window.getEditorCardZoomLevel = () => (EDITOR_ZOOM_LEVELS[currentEditorZoomIndex] || {}).scale;
    window.rotatePage = rotatePage;
    window.rotateSelectedPages = rotateSelectedPages;
    window.movePagesToTarget = movePagesToTarget;
    window.handleCardDrop = handleCardDrop;
    window.handleCardDragStart = handleCardDragStart;
    window.getCurrentPageOrder = () => [...currentPageOrder];

    if (typeof window !== 'undefined') {
        window.addEventListener('auth:user-changed', () => {
            updateSelectionUI();
            if (activeEditorDoc) {
                if (activePdfDoc) renderThumbnails();
                else renderFallbackCards();
            }
        });
    }

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            openPageEditor,
            closePageEditor,
            initPageEditor,
            zoomInEditorCards,
            zoomOutEditorCards,
            resetEditorCardZoom,
            applyEditorCardZoom,
            getEditorCardZoomLevel: () => (EDITOR_ZOOM_LEVELS[currentEditorZoomIndex] || {}).scale,
            rotatePage,
            rotateSelectedPages,
            movePagesToTarget,
            handleCardDrop,
            handleCardDragStart,
            getCurrentPageOrder: () => [...currentPageOrder]
        };
    }
})();
