// ── Ingest Station Controller (Multi-File User Batch Filing & Single Mode) ──
(function() {
    let btnIngestTrigger = null;
    let dropzoneOverlay = null;
    let dropzonePrompt = null;
    let ingestModal = null;
    let btnIngestClose = null;
    let btnIngestCancel = null;
    let fileDropzone = null;
    let fileInput = null;
    let fileInfo = null;
    let fileNameEl = null;
    let fileSizeEl = null;
    let btnRemoveFile = null;
    let previewContainer = null;
    let pdfPreview = null;
    let modeSingle = null;
    let modeBatch = null;
    let batchNotice = null;
    let areaSelect = null;
    let houseSelect = null;
    let tenantSelect = null;
    let btnToggleNewTenant = null;
    let newTenantContainer = null;
    let newTenantInput = null;
    let categorySelect = null;
    let titleInput = null;
    let dateInput = null;
    let notesInput = null;
    let statusMsg = null;
    let btnSubmit = null;
    let submitSpinner = null;
    let submitText = null;

    // Batch UI Elements
    let ingestSingleContainer = null;
    let ingestBatchQueueContainer = null;
    let batchAreaSelect = null;
    let batchCategorySelect = null;
    let batchDateSelect = null;
    let batchFilesList = null;
    let batchCountBadge = null;
    let batchEmptyDropzone = null;
    let btnBatchAddMore = null;
    let batchProgress = null;
    let batchProgressText = null;
    let batchProgressPct = null;
    let batchProgressBar = null;

    let selectedFile = null;
    let objectUrl = null;
    let isSubmitting = false;
    let dragCounter = 0;
    let tenantFetchSeq = 0;
    let batchQueue = [];
    const tenantCache = new Map();

    const STANDARD_CATEGORIES = [
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

    function formatFileSize(bytes) {
        if (!bytes || bytes <= 0) return '0 B';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    }

    function getTodayIsoDate() {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    function getCurrentArea() {
        return (typeof currentArea !== 'undefined' && currentArea) ? currentArea : (window.currentArea || null);
    }

    function getCurrentHouse() {
        return (typeof currentHouse !== 'undefined' && currentHouse) ? currentHouse : (window.currentHouse || null);
    }

    function updateDropzonePrompt() {
        if (!dropzonePrompt) return;
        const area = getCurrentArea();
        const house = getCurrentHouse();
        if (area && house) {
            dropzonePrompt.textContent = `Drop PDF to Ingest into ${area} / ${house}`;
        } else if (area) {
            dropzonePrompt.textContent = `Drop PDF to Ingest into ${area}`;
        } else {
            dropzonePrompt.textContent = 'Drop PDF to Ingest Document';
        }
    }

    let isGlobalListenersAttached = false;

    function handleKeyDown(e) {
        if ((e.metaKey || e.ctrlKey) && e.key && e.key.toLowerCase() === 'i') {
            e.preventDefault();
            const modal = document.getElementById('ingest-station-modal');
            if (modal && !modal.classList.contains('hidden')) {
                closeIngestStation();
            } else {
                openIngestStation();
            }
        } else if (e.key === 'Escape') {
            const modal = document.getElementById('ingest-station-modal');
            if (modal && !modal.classList.contains('hidden')) {
                e.preventDefault();
                closeIngestStation();
            }
        }
    }

    function initIngestStation() {
        // Reset state
        selectedFile = null;
        if (objectUrl && typeof window !== 'undefined' && window.URL && typeof window.URL.revokeObjectURL === 'function') {
            window.URL.revokeObjectURL(objectUrl);
            objectUrl = null;
        }
        isSubmitting = false;
        dragCounter = 0;
        tenantFetchSeq = 0;
        batchQueue = [];
        tenantCache.clear();

        btnIngestTrigger = document.getElementById('btn-ingest-trigger');
        dropzoneOverlay = document.getElementById('ingest-dropzone-overlay');
        dropzonePrompt = document.getElementById('ingest-dropzone-prompt');
        ingestModal = document.getElementById('ingest-station-modal');
        btnIngestClose = document.getElementById('btn-ingest-close');
        btnIngestCancel = document.getElementById('btn-ingest-cancel');
        fileDropzone = document.getElementById('ingest-file-dropzone');
        fileInput = document.getElementById('ingest-file-input');
        fileInfo = document.getElementById('ingest-file-info');
        fileNameEl = document.getElementById('ingest-file-name');
        fileSizeEl = document.getElementById('ingest-file-size');
        btnRemoveFile = document.getElementById('btn-remove-file');
        previewContainer = document.getElementById('ingest-preview-container');
        pdfPreview = document.getElementById('ingest-pdf-preview');
        modeSingle = document.getElementById('ingest-mode-single');
        modeBatch = document.getElementById('ingest-mode-batch');
        batchNotice = document.getElementById('ingest-batch-notice');
        areaSelect = document.getElementById('ingest-area-select');
        houseSelect = document.getElementById('ingest-house-select');
        tenantSelect = document.getElementById('ingest-tenant-select');
        btnToggleNewTenant = document.getElementById('btn-toggle-new-tenant');
        newTenantContainer = document.getElementById('ingest-new-tenant-container');
        newTenantInput = document.getElementById('ingest-new-tenant-input');
        categorySelect = document.getElementById('ingest-category-select');
        titleInput = document.getElementById('ingest-title-input');
        dateInput = document.getElementById('ingest-date-input');
        notesInput = document.getElementById('ingest-notes-input');
        statusMsg = document.getElementById('ingest-status-msg');
        btnSubmit = document.getElementById('btn-ingest-submit');
        submitSpinner = document.getElementById('ingest-submit-spinner');
        submitText = document.getElementById('ingest-submit-text');

        // Batch elements
        ingestSingleContainer = document.getElementById('ingest-single-container');
        ingestBatchQueueContainer = document.getElementById('ingest-batch-queue-container');
        batchAreaSelect = document.getElementById('ingest-batch-area-select');
        batchCategorySelect = document.getElementById('ingest-batch-category-select');
        batchDateSelect = document.getElementById('ingest-batch-date-select');
        batchFilesList = document.getElementById('ingest-batch-files-list');
        batchCountBadge = document.getElementById('ingest-batch-count-badge');
        batchEmptyDropzone = document.getElementById('ingest-batch-empty-dropzone');
        btnBatchAddMore = document.getElementById('btn-batch-add-more');
        batchProgress = document.getElementById('ingest-batch-progress');
        batchProgressText = document.getElementById('ingest-batch-progress-text');
        batchProgressPct = document.getElementById('ingest-batch-progress-pct');
        batchProgressBar = document.getElementById('ingest-batch-progress-bar');

        // Trigger button click
        if (btnIngestTrigger) {
            btnIngestTrigger.addEventListener('click', (e) => {
                e.preventDefault();
                openIngestStation();
            });
        }

        // Close & Cancel buttons
        if (btnIngestClose) btnIngestClose.addEventListener('click', closeIngestStation);
        if (btnIngestCancel) btnIngestCancel.addEventListener('click', closeIngestStation);

        // Backdrop click
        if (ingestModal) {
            ingestModal.addEventListener('click', (e) => {
                if (e.target === ingestModal) {
                    closeIngestStation();
                }
            });
        }

        // File input change
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files && e.target.files.length > 0) {
                    handleFilesSelected(e.target.files);
                }
            });
        }

        // Local Single Dropzone inside modal
        if (fileDropzone && fileInput) {
            fileDropzone.addEventListener('click', () => fileInput.click());
            fileDropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                fileDropzone.classList.add('border-blue-500', 'bg-blue-50/60');
            });
            fileDropzone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                fileDropzone.classList.remove('border-blue-500', 'bg-blue-50/60');
            });
            fileDropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                fileDropzone.classList.remove('border-blue-500', 'bg-blue-50/60');
                if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                    handleFilesSelected(e.dataTransfer.files);
                }
            });
        }

        // Batch empty dropzone
        if (batchEmptyDropzone && fileInput) {
            batchEmptyDropzone.addEventListener('click', () => fileInput.click());
            batchEmptyDropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                batchEmptyDropzone.classList.add('border-blue-500', 'bg-blue-50/60');
            });
            batchEmptyDropzone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                batchEmptyDropzone.classList.remove('border-blue-500', 'bg-blue-50/60');
            });
            batchEmptyDropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                batchEmptyDropzone.classList.remove('border-blue-500', 'bg-blue-50/60');
                if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                    handleFilesSelected(e.dataTransfer.files);
                }
            });
        }

        // Batch add more button
        if (btnBatchAddMore && fileInput) {
            btnBatchAddMore.addEventListener('click', (e) => {
                e.preventDefault();
                fileInput.click();
            });
        }

        // Remove file button (Single mode)
        if (btnRemoveFile) {
            btnRemoveFile.addEventListener('click', (e) => {
                e.preventDefault();
                removeFile();
            });
        }

        // Mode radio switches
        if (modeSingle) {
            modeSingle.addEventListener('change', updateModeUI);
        }
        if (modeBatch) {
            modeBatch.addEventListener('change', updateModeUI);
        }

        // Area & House selects (Single mode)
        if (areaSelect) {
            areaSelect.addEventListener('change', () => {
                populateHouses(areaSelect.value);
            });
        }
        if (houseSelect) {
            houseSelect.addEventListener('change', () => {
                populateTenants(areaSelect ? areaSelect.value : '', houseSelect.value);
            });
        }

        // Shared Area select (Batch mode)
        if (batchAreaSelect) {
            batchAreaSelect.addEventListener('change', async () => {
                const newArea = batchAreaSelect.value;
                const availableHouses = getHousesForArea(newArea);
                for (const item of batchQueue) {
                    for (const target of item.targets) {
                        target.house = detectHouseFromFilename(item.name, availableHouses) || availableHouses[0] || '';
                        await updateTargetTenants(item, target);
                    }
                }
                renderBatchQueue();
            });
        }

        // Tenant toggle button
        if (btnToggleNewTenant) {
            btnToggleNewTenant.addEventListener('click', () => {
                toggleNewTenantInput();
            });
        }

        // Submit button
        if (btnSubmit) {
            btnSubmit.addEventListener('click', (e) => {
                e.preventDefault();
                if (modeBatch && modeBatch.checked) {
                    submitBatchIngest();
                } else {
                    submitIngestForm();
                }
            });
        }

        // Global listeners (attached once)
        if (!isGlobalListenersAttached) {
            document.addEventListener('keydown', handleKeyDown);
            window.addEventListener('dragenter', handleGlobalDragEnter);
            window.addEventListener('dragover', handleGlobalDragOver);
            window.addEventListener('dragleave', handleGlobalDragLeave);
            window.addEventListener('drop', handleGlobalDrop);
            isGlobalListenersAttached = true;
        }

        updateModeUI();
    }

    function handleGlobalDragEnter(e) {
        if (!dropzoneOverlay) return;
        if (e.dataTransfer && e.dataTransfer.types) {
            const types = Array.from(e.dataTransfer.types);
            if (types.includes('Files')) {
                dragCounter++;
                updateDropzonePrompt();
                dropzoneOverlay.classList.remove('hidden');
            }
        }
    }

    function handleGlobalDragOver(e) {
        e.preventDefault();
    }

    function handleGlobalDragLeave(e) {
        if (!dropzoneOverlay) return;
        dragCounter--;
        if (dragCounter <= 0) {
            dragCounter = 0;
            dropzoneOverlay.classList.add('hidden');
        }
    }

    function handleGlobalDrop(e) {
        e.preventDefault();
        dragCounter = 0;
        if (dropzoneOverlay) dropzoneOverlay.classList.add('hidden');

        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const files = Array.from(e.dataTransfer.files);
            const pdfFiles = files.filter(f => f.name.toLowerCase().endsWith('.pdf') || f.type === 'application/pdf');
            if (pdfFiles.length === 0) {
                if (typeof showToast === 'function') {
                    showToast('Only PDF files are supported for ingestion.', 'error');
                } else {
                    alert('Only PDF files are supported for ingestion.');
                }
                return;
            }
            openIngestStation(pdfFiles);
        }
    }

    function handleFilesSelected(files) {
        if (!files || files.length === 0) return;
        const fileList = Array.from(files).filter(f => f.name.toLowerCase().endsWith('.pdf') || f.type === 'application/pdf');
        if (fileList.length === 0) {
            showStatusMsg('Invalid file format. Please select a PDF document (.pdf).', true);
            return;
        }

        const isBatch = modeBatch && modeBatch.checked;
        if (fileList.length > 1 || isBatch) {
            if (modeBatch && !modeBatch.checked) {
                modeBatch.checked = true;
                if (modeSingle) modeSingle.checked = false;
                updateModeUI();
            }
            addFilesToBatch(fileList);
        } else {
            handleFileSelected(fileList[0]);
        }
    }

    function handleFileSelected(file) {
        if (!file) return;
        if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
            showStatusMsg('Invalid file format. Please select a PDF document (.pdf).', true);
            return;
        }

        if (modeBatch && modeBatch.checked) {
            addFilesToBatch([file]);
            return;
        }

        selectedFile = file;
        resetStatusMsg();

        if (fileNameEl) fileNameEl.textContent = file.name;
        if (fileSizeEl) fileSizeEl.textContent = formatFileSize(file.size);
        if (fileInfo) fileInfo.classList.remove('hidden');
        if (fileDropzone) fileDropzone.classList.add('hidden');

        // Create PDF preview URL
        if (typeof window !== 'undefined' && window.URL && typeof window.URL.createObjectURL === 'function') {
            if (objectUrl && typeof window.URL.revokeObjectURL === 'function') {
                window.URL.revokeObjectURL(objectUrl);
            }
            try {
                objectUrl = window.URL.createObjectURL(file);
                if (pdfPreview) {
                    pdfPreview.src = `${objectUrl}#toolbar=0&view=FitH`;
                }
            } catch (err) {
                console.warn('Could not create ObjectURL for PDF preview:', err);
            }
        }
        if (previewContainer) previewContainer.classList.remove('hidden');

        // Auto-populate Title unconditionally from imported PDF filename
        if (titleInput) {
            titleInput.value = file.name.replace(/\.pdf$/i, '').replace(/[-_]+/g, ' ').trim();
        }
    }

    function removeFile() {
        selectedFile = null;
        if (fileInput) fileInput.value = '';
        if (titleInput) titleInput.value = '';
        if (objectUrl && typeof window !== 'undefined' && window.URL && typeof window.URL.revokeObjectURL === 'function') {
            window.URL.revokeObjectURL(objectUrl);
            objectUrl = null;
        }
        if (pdfPreview) pdfPreview.src = 'about:blank';
        if (previewContainer) previewContainer.classList.add('hidden');
        if (fileInfo) fileInfo.classList.add('hidden');
        if (fileDropzone) fileDropzone.classList.remove('hidden');
    }

    function updateModeUI() {
        const isBatch = modeBatch && modeBatch.checked;

        if (fileInput) {
            fileInput.multiple = isBatch;
        }

        if (ingestSingleContainer && ingestBatchQueueContainer) {
            if (isBatch) {
                ingestSingleContainer.classList.add('hidden');
                ingestBatchQueueContainer.classList.remove('hidden');
                populateBatchAreas();

                if (batchDateSelect && !batchDateSelect.value) {
                    batchDateSelect.value = getTodayIsoDate();
                }

                if (selectedFile && batchQueue.length === 0) {
                    addFilesToBatch([selectedFile]);
                } else {
                    renderBatchQueue();
                }
            } else {
                ingestSingleContainer.classList.remove('hidden');
                ingestBatchQueueContainer.classList.add('hidden');

                if (submitText) {
                    submitText.textContent = '⚡ Ingest Document';
                }
            }
        }

        if (batchNotice) {
            if (isBatch) {
                batchNotice.classList.remove('hidden');
            } else {
                batchNotice.classList.add('hidden');
            }
        }
    }

    function getHousesForArea(areaName) {
        if (!areaName) return [];
        const tree = (typeof globalTreeData !== 'undefined' ? globalTreeData : window.globalTreeData) || [];
        const areaNode = tree.find(a => a.name === areaName);
        if (areaNode && Array.isArray(areaNode.children)) {
            return areaNode.children.map(h => h.name);
        }
        return [];
    }

    function detectHouseFromFilename(filename, availableHouses = []) {
        if (!filename) return null;

        // 1. Direct match with available houses in current area
        if (availableHouses.length > 0) {
            const sortedHouses = [...availableHouses].sort((a, b) => b.length - a.length);
            for (const h of sortedHouses) {
                const escaped = h.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                const regex = new RegExp(`(?:^|[^0-9a-zA-Z])${escaped}(?:[^0-9a-zA-Z]|$)`, 'i');
                if (regex.test(filename)) {
                    return h;
                }
            }
        }

        // 2. Regex search for house/villa/منزل/فيلا number (e.g. 500, 514)
        const match = filename.match(/(?:house|villa|منزل|فيلا)?\s*(\d{3,4})/i);
        if (match && match[1]) {
            const num = match[1];
            if (availableHouses.length > 0) {
                const found = availableHouses.find(h => h === num || h.includes(num));
                if (found) return found;
            }
            return num;
        }

        return null;
    }

    async function getTenantsForHouse(areaName, houseName) {
        if (!areaName || !houseName) return { tenants: [], latestTenantId: '' };
        const cacheKey = `${areaName}:${houseName}`;
        if (tenantCache.has(cacheKey)) {
            return tenantCache.get(cacheKey);
        }

        let tenants = [];
        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(areaName)}/houses/${encodeURIComponent(houseName)}/tenants`);
            if (res.ok) {
                const data = await res.json();
                if (Array.isArray(data)) tenants = data;
            } else {
                throw new Error('Tenant fetch failed');
            }
        } catch (e) {
            const tree = (typeof globalTreeData !== 'undefined' ? globalTreeData : window.globalTreeData) || [];
            const areaNode = tree.find(a => a.name === areaName);
            const houseNode = areaNode?.children?.find(h => h.name === houseName);
            if (houseNode && Array.isArray(houseNode.children)) {
                tenants = houseNode.children.map(t => ({
                    id: t.id != null ? t.id : t.name,
                    name: t.name || '',
                    start_date: t.start_date || '',
                    end_date: t.end_date || ''
                }));
            }
        }

        const seen = new Set();
        const uniqueTenants = [];
        for (const t of tenants) {
            const normName = (t.name || '').trim().toLowerCase();
            if (t.id != null && seen.has(`id:${t.id}`)) continue;
            if (normName && seen.has(`name:${normName}`)) continue;
            if (t.id != null) seen.add(`id:${t.id}`);
            if (normName) seen.add(`name:${normName}`);
            uniqueTenants.push(t);
        }

        const latest = resolveLatestTenant(uniqueTenants);
        const latestTenantId = latest ? (latest.id != null ? String(latest.id) : (latest.name || '')) : '';
        const result = { tenants: uniqueTenants, latestTenantId };
        tenantCache.set(cacheKey, result);
        return result;
    }

    function resolveLatestTenant(tenants) {
        if (!tenants || tenants.length === 0) return null;

        const isActive = (t) => !t.end_date || t.end_date === null || (typeof t.end_date === 'string' && (t.end_date.trim() === '' || t.end_date.trim().toLowerCase() === 'present' || t.end_date.trim().toLowerCase() === 'active'));
        const activeTenants = tenants.filter(isActive);

        if (activeTenants.length > 0) {
            const sortedActive = [...activeTenants].sort((a, b) => {
                const cmp = compareDatesDesc(a.start_date, b.start_date);
                if (cmp !== 0) return cmp;
                return (b.id != null && a.id != null) ? b.id - a.id : 0;
            });
            return sortedActive[0];
        }

        const sortedEnded = [...tenants].sort((a, b) => {
            const aLatest = a.end_date || a.start_date;
            const bLatest = b.end_date || b.start_date;
            const cmp = compareDatesDesc(aLatest, bLatest);
            if (cmp !== 0) return cmp;
            return compareDatesDesc(a.start_date, b.start_date);
        });
        return sortedEnded[0];
    }

    async function updateTargetTenants(item, target) {
        const area = (batchAreaSelect && batchAreaSelect.value) ? batchAreaSelect.value : (getCurrentArea() || '');
        if (!area || !target.house) {
            target.tenants = [];
            target.tenantId = '';
            return;
        }
        const { tenants, latestTenantId } = await getTenantsForHouse(area, target.house);
        target.tenants = tenants;
        target.tenantId = latestTenantId;
    }

    async function addFilesToBatch(files) {
        if (!files || files.length === 0) return;

        const sharedArea = (batchAreaSelect && batchAreaSelect.value) ? batchAreaSelect.value : (getCurrentArea() || '');
        if (batchAreaSelect && !batchAreaSelect.value && sharedArea) {
            batchAreaSelect.value = sharedArea;
        }
        if (batchDateSelect && !batchDateSelect.value) {
            batchDateSelect.value = getTodayIsoDate();
        }

        const availableHouses = getHousesForArea(batchAreaSelect ? batchAreaSelect.value : '');

        const newItems = [];
        for (const file of files) {
            if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
                continue;
            }
            const detectedHouse = detectHouseFromFilename(file.name, availableHouses) || getCurrentHouse() || (availableHouses[0] || '');
            const autoTitle = file.name.replace(/\.pdf$/i, '').replace(/[-_]+/g, ' ').trim();

            const item = {
                id: 'bf_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
                file: file,
                name: file.name,
                size: file.size,
                title: autoTitle,
                targets: [
                    {
                        house: detectedHouse,
                        tenantId: '',
                        tenants: [],
                    }
                ]
            };
            batchQueue.push(item);
            newItems.push(item);
        }

        renderBatchQueue();

        for (const item of newItems) {
            for (const target of item.targets) {
                if (target.house) {
                    await updateTargetTenants(item, target);
                }
            }
        }
        renderBatchQueue();
    }

    function renderBatchQueue() {
        if (!batchFilesList) return;

        if (batchCountBadge) {
            batchCountBadge.textContent = `${batchQueue.length} file${batchQueue.length === 1 ? '' : 's'}`;
        }

        if (batchEmptyDropzone) {
            if (batchQueue.length === 0) {
                batchEmptyDropzone.classList.remove('hidden');
                batchFilesList.classList.add('hidden');
            } else {
                batchEmptyDropzone.classList.add('hidden');
                batchFilesList.classList.remove('hidden');
            }
        }

        let totalTasks = 0;
        batchQueue.forEach(item => {
            totalTasks += (item.targets && item.targets.length > 0) ? item.targets.length : 1;
        });

        if (submitText && modeBatch && modeBatch.checked) {
            submitText.textContent = `⚡ Ingest All (${totalTasks} Files)`;
        }

        batchFilesList.innerHTML = '';
        const availableHouses = getHousesForArea(batchAreaSelect ? batchAreaSelect.value : '');

        batchQueue.forEach((item, fileIdx) => {
            const card = document.createElement('div');
            card.className = 'bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs space-y-3 batch-file-card';
            card.dataset.fileIdx = String(fileIdx);

            // Header: Name, size, remove file button
            const header = document.createElement('div');
            header.className = 'flex items-center justify-between gap-3';
            header.innerHTML = `
                <div class="flex items-center gap-2.5 min-w-0 flex-1">
                    <div class="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                    </div>
                    <div class="min-w-0 flex-1">
                        <p class="text-xs font-bold text-slate-800 truncate batch-file-name" title="${item.name}">${item.name}</p>
                        <p class="text-[10px] text-slate-400 font-mono">${formatFileSize(item.size)}</p>
                    </div>
                </div>
                <button type="button" class="btn-remove-batch-file text-slate-400 hover:text-rose-600 p-1 rounded-lg hover:bg-rose-50 transition-colors cursor-pointer" title="Remove file">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
            `;
            card.appendChild(header);

            // Title row
            const titleRow = document.createElement('div');
            titleRow.innerHTML = `
                <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Document Title</label>
                <input type="text" class="batch-title-input w-full px-3 py-1.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-slate-50 focus:bg-white font-medium" value="${item.title || ''}" placeholder="Document title..." />
            `;
            const titleInputEl = titleRow.querySelector('.batch-title-input');
            titleInputEl.addEventListener('input', (e) => {
                item.title = e.target.value;
            });
            card.appendChild(titleRow);

            // Target houses section
            const targetsSection = document.createElement('div');
            targetsSection.className = 'space-y-2';

            const targetsHeader = document.createElement('div');
            targetsHeader.className = 'flex items-center justify-between';
            targetsHeader.innerHTML = `
                <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Target House(s) &amp; Assigned Tenant</label>
                <button type="button" class="btn-batch-add-house text-[11px] font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1 cursor-pointer">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                    <span>+ Add House</span>
                </button>
            `;
            const btnAddHouse = targetsHeader.querySelector('.btn-batch-add-house');
            btnAddHouse.addEventListener('click', async () => {
                const nextHouse = availableHouses.find(h => !item.targets.some(t => t.house === h)) || availableHouses[0] || '';
                const newTarget = { house: nextHouse, tenantId: '', tenants: [] };
                item.targets.push(newTarget);
                renderBatchQueue();
                await updateTargetTenants(item, newTarget);
                renderBatchQueue();
            });
            targetsSection.appendChild(targetsHeader);

            const targetsList = document.createElement('div');
            targetsList.className = 'batch-targets-list space-y-1.5';

            item.targets.forEach((target, targetIdx) => {
                const targetRow = document.createElement('div');
                targetRow.className = 'flex items-center gap-2 p-2 rounded-lg bg-slate-50 border border-slate-200 batch-target-row';
                targetRow.dataset.targetIdx = String(targetIdx);

                const selectsContainer = document.createElement('div');
                selectsContainer.className = 'flex-1 grid grid-cols-1 sm:grid-cols-2 gap-2';

                // House select
                const houseWrapper = document.createElement('div');
                const houseSel = document.createElement('select');
                houseSel.className = 'batch-house-select w-full px-2.5 py-1.5 text-xs border border-slate-200 rounded-lg bg-white font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none';
                houseSel.innerHTML = '<option value="">Select House...</option>';
                availableHouses.forEach(h => {
                    const opt = document.createElement('option');
                    opt.value = h;
                    opt.textContent = `House ${h}`;
                    if (h === target.house) opt.selected = true;
                    houseSel.appendChild(opt);
                });
                houseWrapper.appendChild(houseSel);

                // Tenant select
                const tenantWrapper = document.createElement('div');
                const tenantSel = document.createElement('select');
                tenantSel.className = 'batch-tenant-select w-full px-2.5 py-1.5 text-xs border border-slate-200 rounded-lg bg-white font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none';
                tenantSel.innerHTML = '<option value="">(Auto-detect Tenant)</option>';
                if (Array.isArray(target.tenants)) {
                    target.tenants.forEach(t => {
                        const opt = document.createElement('option');
                        opt.value = String(t.id != null ? t.id : t.name);
                        const yearHint = t.start_date ? ` (${t.start_date.substring(0, 4)})` : '';
                        opt.textContent = `${t.name}${yearHint}`;
                        if (String(opt.value) === String(target.tenantId)) {
                            opt.selected = true;
                        }
                        tenantSel.appendChild(opt);
                    });
                }
                tenantWrapper.appendChild(tenantSel);

                selectsContainer.appendChild(houseWrapper);
                selectsContainer.appendChild(tenantWrapper);
                targetRow.appendChild(selectsContainer);

                // House change listener
                houseSel.addEventListener('change', async (e) => {
                    target.house = e.target.value;
                    await updateTargetTenants(item, target);
                    renderBatchQueue();
                });

                // Tenant change listener
                tenantSel.addEventListener('change', (e) => {
                    target.tenantId = e.target.value;
                });

                // Remove target button
                if (item.targets.length > 1) {
                    const btnRemoveTarget = document.createElement('button');
                    btnRemoveTarget.type = 'button';
                    btnRemoveTarget.className = 'btn-remove-target text-slate-400 hover:text-rose-600 p-1 rounded hover:bg-rose-50 transition-colors cursor-pointer';
                    btnRemoveTarget.title = 'Remove this house target';
                    btnRemoveTarget.innerHTML = `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>`;
                    btnRemoveTarget.addEventListener('click', () => {
                        item.targets.splice(targetIdx, 1);
                        renderBatchQueue();
                    });
                    targetRow.appendChild(btnRemoveTarget);
                }

                targetsList.appendChild(targetRow);
            });

            targetsSection.appendChild(targetsList);
            card.appendChild(targetsSection);

            // Remove file button listener
            const btnRemove = header.querySelector('.btn-remove-batch-file');
            btnRemove.addEventListener('click', () => {
                batchQueue.splice(fileIdx, 1);
                renderBatchQueue();
            });

            batchFilesList.appendChild(card);
        });
    }

    function populateBatchAreas() {
        if (!batchAreaSelect) return;
        const tree = (typeof globalTreeData !== 'undefined' ? globalTreeData : window.globalTreeData) || [];
        const currentVal = batchAreaSelect.value;

        batchAreaSelect.innerHTML = '<option value="">Select Area...</option>';
        tree.forEach(area => {
            const opt = document.createElement('option');
            opt.value = area.name;
            opt.textContent = area.name;
            batchAreaSelect.appendChild(opt);
        });

        const activeArea = currentVal || getCurrentArea();
        if (activeArea) {
            batchAreaSelect.value = activeArea;
        }
    }

    function populateAreas(targetArea = null, targetHouse = null) {
        if (!areaSelect) return;
        const tree = (typeof globalTreeData !== 'undefined' ? globalTreeData : window.globalTreeData) || [];
        
        areaSelect.innerHTML = '<option value="">Select Area...</option>';
        tree.forEach(area => {
            const opt = document.createElement('option');
            opt.value = area.name;
            opt.textContent = area.name;
            areaSelect.appendChild(opt);
        });

        const activeArea = targetArea || getCurrentArea();
        if (activeArea) {
            areaSelect.value = activeArea;
        }
        populateHouses(areaSelect.value, targetHouse);
    }

    function populateHouses(areaName, targetHouse = null) {
        if (!houseSelect) return;
        houseSelect.innerHTML = '<option value="">Select House...</option>';

        if (!areaName) {
            populateTenants('', '');
            return;
        }

        const tree = (typeof globalTreeData !== 'undefined' ? globalTreeData : window.globalTreeData) || [];
        const areaNode = tree.find(a => a.name === areaName);
        if (areaNode && Array.isArray(areaNode.children)) {
            areaNode.children.forEach(house => {
                const opt = document.createElement('option');
                opt.value = house.name;
                opt.textContent = house.name;
                houseSelect.appendChild(opt);
            });
        }

        const activeHouse = targetHouse || getCurrentHouse();
        if (activeHouse) {
            houseSelect.value = activeHouse;
        }
        populateTenants(areaName, houseSelect.value);
    }

    function compareDatesDesc(aDate, bDate) {
        if (!aDate && !bDate) return 0;
        if (!aDate) return 1;
        if (!bDate) return -1;
        const strA = String(aDate).trim();
        const strB = String(bDate).trim();
        const timeA = new Date(strA).getTime();
        const timeB = new Date(strB).getTime();
        if (!isNaN(timeA) && !isNaN(timeB) && timeA !== timeB) {
            return timeB - timeA;
        }
        return strB.localeCompare(strA);
    }

    async function populateTenants(areaName, houseName, targetTenantId = null) {
        if (!tenantSelect) return;
        tenantSelect.innerHTML = '<option value="">(Auto-detect or Select Tenant)</option>';

        if (!areaName || !houseName) return;

        const currentSeq = ++tenantFetchSeq;
        let fetchedTenants = null;
        let fallbackChildren = null;
        let isFallback = false;

        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(areaName)}/houses/${encodeURIComponent(houseName)}/tenants`);
            if (currentSeq !== tenantFetchSeq) return;
            if (!res.ok) throw new Error('Failed to fetch tenants');
            const tenants = await res.json();
            if (currentSeq !== tenantFetchSeq) return;
            tenantSelect.innerHTML = '<option value="">(Auto-detect or Select Tenant)</option>';
            const seen = new Set();
            fetchedTenants = [];
            if (Array.isArray(tenants)) {
                tenants.forEach(t => {
                    const normName = (t.name || '').trim().toLowerCase();
                    if (t.id != null && seen.has(`id:${t.id}`)) return;
                    if (normName && seen.has(`name:${normName}`)) return;
                    if (t.id != null) seen.add(`id:${t.id}`);
                    if (normName) seen.add(`name:${normName}`);

                    const opt = document.createElement('option');
                    opt.value = t.id;
                    opt.dataset.id = t.id != null ? String(t.id) : '';
                    opt.dataset.name = t.name || '';
                    const yearHint = t.start_date ? ` (${t.start_date.substring(0, 4)})` : '';
                    opt.textContent = `${t.name}${yearHint}`;
                    tenantSelect.appendChild(opt);
                    fetchedTenants.push(t);
                });
            }
        } catch (err) {
            if (currentSeq !== tenantFetchSeq) return;
            isFallback = true;
            // Fallback: check tree node children
            const tree = (typeof globalTreeData !== 'undefined' ? globalTreeData : window.globalTreeData) || [];
            const areaNode = tree.find(a => a.name === areaName);
            const houseNode = areaNode?.children?.find(h => h.name === houseName);
            tenantSelect.innerHTML = '<option value="">(Auto-detect or Select Tenant)</option>';
            const seen = new Set();
            fallbackChildren = [];
            if (houseNode && Array.isArray(houseNode.children)) {
                fallbackChildren = houseNode.children;
                houseNode.children.forEach(tNode => {
                    const normName = (tNode.name || '').trim().toLowerCase();
                    if (normName && seen.has(`name:${normName}`)) return;
                    if (normName) seen.add(`name:${normName}`);

                    const opt = document.createElement('option');
                    opt.value = tNode.name;
                    opt.dataset.id = tNode.id != null ? String(tNode.id) : '';
                    opt.dataset.name = tNode.name || '';
                    opt.textContent = tNode.name;
                    tenantSelect.appendChild(opt);
                });
            }
        }

        if (currentSeq !== tenantFetchSeq) return;

        const availableOptions = Array.from(tenantSelect.options).filter(opt => opt.value !== '');
        if (availableOptions.length === 0) {
            tenantSelect.value = '';
            return;
        }

        // 1. If targetTenantId is provided and exists in the options, select it.
        if (targetTenantId != null && targetTenantId !== '') {
            const targetStr = String(targetTenantId).trim();
            const targetMatch = availableOptions.find(opt =>
                opt.value === targetStr ||
                opt.dataset.id === targetStr ||
                (opt.dataset.name && opt.dataset.name.trim().toLowerCase() === targetStr.toLowerCase())
            );
            if (targetMatch) {
                tenantSelect.value = targetMatch.value;
                return;
            }
        }

        // 2. Else if window.currentTenant is set and matches a tenant in the options (by ID or name), select it.
        const currentTenant = typeof window !== 'undefined' ? window.currentTenant : null;
        if (currentTenant != null && currentTenant !== '') {
            let curId = null;
            let curName = null;
            if (typeof currentTenant === 'object') {
                curId = currentTenant.id != null ? String(currentTenant.id).trim() : null;
                curName = currentTenant.name != null ? String(currentTenant.name).trim().toLowerCase() : null;
            } else {
                const s = String(currentTenant).trim();
                curId = s;
                curName = s.toLowerCase();
            }
            const currentMatch = availableOptions.find(opt => {
                if (curId && (opt.value === curId || opt.dataset.id === curId)) return true;
                if (curName && ((opt.dataset.name && opt.dataset.name.trim().toLowerCase() === curName) || opt.value.trim().toLowerCase() === curName)) return true;
                return false;
            });
            if (currentMatch) {
                tenantSelect.value = currentMatch.value;
                return;
            }
        }

        // 3. Otherwise (by default when a house is selected), identify the latest tenant:
        if (!isFallback && Array.isArray(fetchedTenants) && fetchedTenants.length > 0) {
            const isActive = (t) => !t.end_date || t.end_date === null || (typeof t.end_date === 'string' && (t.end_date.trim() === '' || t.end_date.trim().toLowerCase() === 'present' || t.end_date.trim().toLowerCase() === 'active'));
            const activeTenants = fetchedTenants.filter(isActive);

            if (activeTenants.length > 0) {
                // Priority 1: An active tenant. If multiple exist, the one with latest start_date.
                const sortedActive = [...activeTenants].sort((a, b) => {
                    const cmp = compareDatesDesc(a.start_date, b.start_date);
                    if (cmp !== 0) return cmp;
                    return (b.id != null && a.id != null) ? b.id - a.id : 0;
                });
                const chosen = sortedActive[0];
                const opt = availableOptions.find(o => o.value === String(chosen.id) || (o.dataset.name && o.dataset.name === chosen.name));
                if (opt) tenantSelect.value = opt.value;
            } else {
                // Priority 2: If all tenants have ended, the tenant with latest end_date or start_date.
                const sortedEnded = [...fetchedTenants].sort((a, b) => {
                    const aLatest = a.end_date || a.start_date;
                    const bLatest = b.end_date || b.start_date;
                    const cmp = compareDatesDesc(aLatest, bLatest);
                    if (cmp !== 0) return cmp;
                    return compareDatesDesc(a.start_date, b.start_date);
                });
                const chosen = sortedEnded[0];
                const opt = availableOptions.find(o => o.value === String(chosen.id) || (o.dataset.name && o.dataset.name === chosen.name));
                if (opt) tenantSelect.value = opt.value;
            }
        } else if (isFallback && Array.isArray(fallbackChildren) && fallbackChildren.length > 0) {
            // Priority 3 (DOM fallback): The last tenant in houseNode.children.
            const lastTenant = fallbackChildren[fallbackChildren.length - 1];
            const lastVal = typeof lastTenant === 'string' ? lastTenant : (lastTenant?.name || '');
            const opt = availableOptions.find(o => o.value === lastVal || (o.dataset.name && o.dataset.name === lastVal));
            if (opt) {
                tenantSelect.value = opt.value;
            } else if (availableOptions.length > 0) {
                tenantSelect.value = availableOptions[availableOptions.length - 1].value;
            }
        }
    }

    function toggleNewTenantInput(forceShow = null) {
        if (!newTenantContainer) return;
        const shouldShow = forceShow !== null ? forceShow : newTenantContainer.classList.contains('hidden');
        if (shouldShow) {
            newTenantContainer.classList.remove('hidden');
            if (btnToggleNewTenant) btnToggleNewTenant.textContent = '✕ Cancel New Tenant';
            if (newTenantInput) newTenantInput.focus();
        } else {
            newTenantContainer.classList.add('hidden');
            if (btnToggleNewTenant) btnToggleNewTenant.textContent = '+ Add New Tenant';
            if (newTenantInput) newTenantInput.value = '';
        }
    }

    function findMatchingCategory(suggestedCat) {
        if (!suggestedCat || !categorySelect) return null;
        const clean = suggestedCat.replace(/\s+/g, '');
        for (const opt of categorySelect.options) {
            const optClean = opt.value.replace(/\s+/g, '');
            if (optClean === clean || opt.value.includes(suggestedCat) || suggestedCat.includes(opt.value)) {
                return opt.value;
            }
        }
        return null;
    }

    function openIngestStation(initialFiles = null) {
        if (!ingestModal) return;
        ingestModal.classList.remove('hidden');
        resetStatusMsg();

        if (dateInput && !dateInput.value) {
            dateInput.value = getTodayIsoDate();
        }
        if (batchDateSelect && !batchDateSelect.value) {
            batchDateSelect.value = getTodayIsoDate();
        }

        const activeArea = getCurrentArea();
        const activeHouse = getCurrentHouse();
        populateAreas(activeArea, activeHouse);
        populateBatchAreas();

        updateModeUI();

        if (initialFiles) {
            if (Array.isArray(initialFiles) || (typeof FileList !== 'undefined' && initialFiles instanceof FileList)) {
                handleFilesSelected(Array.from(initialFiles));
            } else {
                handleFilesSelected([initialFiles]);
            }
        }
    }

    function closeIngestStation() {
        if (!ingestModal) return;
        ingestModal.classList.add('hidden');
        resetIngestForm();
    }

    function resetIngestForm() {
        removeFile();
        batchQueue = [];
        renderBatchQueue();
        if (titleInput) titleInput.value = '';
        if (dateInput) dateInput.value = getTodayIsoDate();
        if (batchDateSelect) batchDateSelect.value = getTodayIsoDate();
        if (notesInput) notesInput.value = '';
        if (newTenantInput) newTenantInput.value = '';
        if (newTenantContainer) newTenantContainer.classList.add('hidden');
        if (btnToggleNewTenant) btnToggleNewTenant.textContent = '+ Add New Tenant';
        if (categorySelect) categorySelect.value = '13 - رسائل متنوعة';
        if (batchCategorySelect) batchCategorySelect.value = '06 - كهرباء وماء';
        if (modeSingle) modeSingle.checked = true;
        if (modeBatch) modeBatch.checked = false;
        if (batchNotice) batchNotice.classList.add('hidden');
        if (batchProgress) batchProgress.classList.add('hidden');
        if (submitText) submitText.textContent = '⚡ Ingest Document';
        resetStatusMsg();
        updateModeUI();
    }

    function resetStatusMsg() {
        if (!statusMsg) return;
        statusMsg.className = 'px-3 py-2 rounded-xl text-xs font-medium hidden';
        statusMsg.textContent = '';
    }

    function showStatusMsg(text, isError = false) {
        if (!statusMsg) return;
        statusMsg.className = `px-3 py-2 rounded-xl text-xs font-medium ${
            isError ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
        }`;
        statusMsg.textContent = text;
        statusMsg.classList.remove('hidden');
    }

    async function submitIngestForm() {
        if (isSubmitting) return;

        if (!selectedFile) {
            showStatusMsg('Please select or drop a PDF file to ingest.', true);
            return;
        }

        const area = areaSelect ? areaSelect.value.trim() : '';
        const house = houseSelect ? houseSelect.value.trim() : '';

        if (!area || !house) {
            showStatusMsg('Please select both a Target Area and Target House.', true);
            return;
        }

        isSubmitting = true;
        if (btnSubmit) btnSubmit.disabled = true;
        if (submitSpinner) submitSpinner.classList.remove('hidden');
        if (submitText) submitText.textContent = 'Ingesting...';
        resetStatusMsg();

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('mode', 'manual');
        formData.append('area_id', area);
        formData.append('house_id', house);

        // Tenant resolution
        const isNewTenantVisible = newTenantContainer && !newTenantContainer.classList.contains('hidden');
        const newTenantName = newTenantInput ? newTenantInput.value.trim() : '';

        if (isNewTenantVisible && newTenantName) {
            formData.append('tenant_name', newTenantName);
        } else if (tenantSelect && tenantSelect.value) {
            formData.append('tenant_id', tenantSelect.value);
        }

        if (categorySelect && categorySelect.value) {
            formData.append('category', categorySelect.value);
        }
        if (titleInput && titleInput.value.trim()) {
            formData.append('arabic_title', titleInput.value.trim());
        }
        if (dateInput && dateInput.value.trim()) {
            formData.append('primary_date', dateInput.value.trim());
        }
        if (notesInput && notesInput.value.trim()) {
            formData.append('notes', notesInput.value.trim());
        }

        try {
            const res = await fetch('/api/ingest', {
                method: 'POST',
                body: formData,
            });

            if (res.ok) {
                const data = await res.json();
                closeIngestStation();

                const vaultId = data.vault_id || (data.vault_ids && data.vault_ids[0]) || '';
                const successMsg = vaultId 
                    ? `Document successfully ingested (Vault ID: ${vaultId})`
                    : (data.message || 'Document successfully ingested');

                const toastFn = (typeof showToast === 'function') 
                    ? showToast 
                    : ((typeof window !== 'undefined' && typeof window.showToast === 'function') ? window.showToast : null);

                if (toastFn) {
                    toastFn(successMsg, 'success');
                } else if (typeof alert === 'function') {
                    alert(successMsg);
                }

                if (typeof window.refreshCurrentTab === 'function') {
                    window.refreshCurrentTab(area, house);
                }
                if (typeof window.loadTree === 'function') {
                    window.loadTree();
                }
            } else {
                const err = await res.json().catch(() => ({}));
                showStatusMsg(err.detail || 'Ingestion failed.', true);
            }
        } catch (err) {
            console.error('Ingestion failed:', err);
            showStatusMsg('Network error while ingesting document.', true);
        } finally {
            isSubmitting = false;
            if (btnSubmit) btnSubmit.disabled = false;
            if (submitSpinner) submitSpinner.classList.add('hidden');
            if (submitText) submitText.textContent = '⚡ Ingest Document';
        }
    }

    async function submitBatchIngest() {
        if (isSubmitting) return;

        if (batchQueue.length === 0) {
            showStatusMsg('Please add at least one PDF file to the batch queue.', true);
            return;
        }

        const sharedArea = batchAreaSelect ? batchAreaSelect.value.trim() : '';
        if (!sharedArea) {
            showStatusMsg('Please select a Shared Area for the batch.', true);
            return;
        }

        const sharedCategory = batchCategorySelect ? batchCategorySelect.value.trim() : '';
        if (!sharedCategory) {
            showStatusMsg('Please select a Shared Category for the batch.', true);
            return;
        }

        const sharedDate = batchDateSelect ? batchDateSelect.value.trim() : '';
        if (!sharedDate) {
            showStatusMsg('Please select a Shared Primary Date for the batch.', true);
            return;
        }

        for (const item of batchQueue) {
            for (const target of item.targets) {
                if (!target.house || !target.house.trim()) {
                    showStatusMsg(`Please select a Target House for document "${item.name}".`, true);
                    return;
                }
            }
        }

        isSubmitting = true;
        if (btnSubmit) btnSubmit.disabled = true;
        if (submitSpinner) submitSpinner.classList.remove('hidden');
        if (batchProgress) batchProgress.classList.remove('hidden');
        resetStatusMsg();

        const tasks = [];
        batchQueue.forEach(item => {
            item.targets.forEach(target => {
                tasks.push({
                    file: item.file,
                    name: item.name,
                    title: item.title || item.name.replace(/\.pdf$/i, '').replace(/[-_]+/g, ' ').trim(),
                    house: target.house.trim(),
                    tenantId: target.tenantId,
                });
            });
        });

        const totalTasks = tasks.length;
        let completedCount = 0;
        let failedCount = 0;
        const errors = [];
        let lastArea = sharedArea;
        let lastHouse = tasks[0]?.house || '';

        for (let i = 0; i < totalTasks; i++) {
            const task = tasks[i];
            const currentNum = i + 1;
            const progressMsg = `Ingesting ${currentNum} of ${totalTasks}: ${task.name}...`;

            if (batchProgressText) batchProgressText.textContent = progressMsg;
            if (submitText) submitText.textContent = `Ingesting (${currentNum}/${totalTasks})...`;
            const pct = Math.round(((currentNum - 1) / totalTasks) * 100);
            if (batchProgressPct) batchProgressPct.textContent = `${pct}%`;
            if (batchProgressBar) batchProgressBar.style.width = `${pct}%`;

            const formData = new FormData();
            formData.append('file', task.file);
            formData.append('mode', 'manual');
            formData.append('area_id', sharedArea);
            formData.append('house_id', task.house);
            if (task.tenantId) {
                formData.append('tenant_id', task.tenantId);
            }
            formData.append('category', sharedCategory);
            formData.append('arabic_title', task.title);
            formData.append('primary_date', sharedDate);

            try {
                const res = await fetch('/api/ingest', {
                    method: 'POST',
                    body: formData,
                });

                if (res.ok) {
                    completedCount++;
                    lastHouse = task.house;
                } else {
                    failedCount++;
                    const err = await res.json().catch(() => ({}));
                    errors.push(`${task.name} (${task.house}): ${err.detail || 'Ingestion failed'}`);
                }
            } catch (err) {
                failedCount++;
                errors.push(`${task.name} (${task.house}): Network error`);
            }
        }

        if (batchProgressPct) batchProgressPct.textContent = '100%';
        if (batchProgressBar) batchProgressBar.style.width = '100%';

        isSubmitting = false;
        if (btnSubmit) btnSubmit.disabled = false;
        if (submitSpinner) submitSpinner.classList.add('hidden');
        if (submitText) submitText.textContent = `⚡ Ingest All (${totalTasks} Files)`;

        const toastFn = (typeof showToast === 'function') 
            ? showToast 
            : ((typeof window !== 'undefined' && typeof window.showToast === 'function') ? window.showToast : null);

        if (failedCount === 0) {
            const successMsg = `Successfully ingested ${completedCount} document${completedCount === 1 ? '' : 's'}`;
            if (toastFn) {
                toastFn(successMsg, 'success');
            } else if (typeof alert === 'function') {
                alert(successMsg);
            }
            closeIngestStation();

            if (typeof window.refreshCurrentTab === 'function') {
                window.refreshCurrentTab(lastArea, lastHouse);
            }
            if (typeof window.loadTree === 'function') {
                window.loadTree();
            }
        } else {
            const partialMsg = `Ingested ${completedCount} of ${totalTasks} documents. (${failedCount} failed: ${errors.join('; ')})`;
            showStatusMsg(partialMsg, true);
            if (toastFn) {
                toastFn(partialMsg, 'error');
            }
            if (completedCount > 0) {
                if (typeof window.refreshCurrentTab === 'function') {
                    window.refreshCurrentTab(lastArea, lastHouse);
                }
                if (typeof window.loadTree === 'function') {
                    window.loadTree();
                }
            }
        }
    }

    // Expose globals
    window.initIngestStation = initIngestStation;
    window.openIngestStation = openIngestStation;
    window.closeIngestStation = closeIngestStation;
    window.handleFileSelected = handleFileSelected;
    window.handleFilesSelected = handleFilesSelected;
    window.removeFile = removeFile;
    window.submitIngestForm = submitIngestForm;
    window.submitBatchIngest = submitBatchIngest;
    window.formatFileSize = formatFileSize;
    window.getTodayIsoDate = getTodayIsoDate;
    window.resetIngestForm = resetIngestForm;
    window.detectHouseFromFilename = detectHouseFromFilename;
    window.getTenantsForHouse = getTenantsForHouse;
    window.renderBatchQueue = renderBatchQueue;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            initIngestStation,
            openIngestStation,
            closeIngestStation,
            handleFileSelected,
            handleFilesSelected,
            removeFile,
            submitIngestForm,
            submitBatchIngest,
            formatFileSize,
            populateAreas,
            populateBatchAreas,
            populateHouses,
            populateTenants,
            updateModeUI,
            getTodayIsoDate,
            resetIngestForm,
            detectHouseFromFilename,
            getTenantsForHouse,
            addFilesToBatch,
            renderBatchQueue,
            getBatchQueue: () => batchQueue,
        };
    }
})();
