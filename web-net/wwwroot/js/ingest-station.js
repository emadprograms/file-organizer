// ── Ingest Station Controller (Single Document, Broadcast Notice, House Batch) ──
(function() {
    let activeTab = 'single'; // 'single' | 'broadcast' | 'housebatch'

    // Common / Modal Elements
    let btnIngestTrigger = null;
    let dropzoneOverlay = null;
    let dropzonePrompt = null;
    let ingestModal = null;
    let btnIngestClose = null;
    let btnIngestCancel = null;
    let btnSubmit = null;
    let submitSpinner = null;
    let submitText = null;
    let statusMsg = null;

    // Shared Batch & Broadcast Progress Bar
    let batchProgress = null;
    let batchProgressText = null;
    let batchProgressPct = null;
    let batchProgressBar = null;

    // Tab Navigation Buttons
    let tabModeSingle = null;
    let tabModeBroadcast = null;
    let tabModeHousebatch = null;

    // Section Containers
    let sectionModeSingle = null;
    let sectionModeBroadcast = null;
    let sectionModeHousebatch = null;

    // Section 1: Single Document Elements
    let fileDropzone = null;
    let fileInput = null;
    let fileInfo = null;
    let fileNameEl = null;
    let fileSizeEl = null;
    let btnRemoveFile = null;
    let previewContainer = null;
    let pdfPreview = null;
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

    // Section 2: Broadcast Notice Elements
    let broadcastDropzone = null;
    let broadcastFileInput = null;
    let broadcastFileInfo = null;
    let broadcastFileNameEl = null;
    let broadcastFileSizeEl = null;
    let btnBroadcastRemoveFile = null;
    let broadcastPreviewContainer = null;
    let broadcastPdfPreview = null;
    let broadcastCategorySelect = null;
    let broadcastTitleInput = null;
    let broadcastDateInput = null;
    let broadcastAreaSelect = null;
    let broadcastSelectedCount = null;
    let btnBroadcastSelectAll = null;
    let btnBroadcastDeselectAll = null;
    let broadcastHouseSearch = null;
    let broadcastHousesList = null;

    // Section 3: House Batch Elements
    let housebatchAreaSelect = null;
    let housebatchHouseSelect = null;
    let housebatchTenantSelect = null;
    let housebatchCountBadge = null;
    let btnHousebatchAddMore = null;
    let housebatchDropzone = null;
    let housebatchFileInput = null;
    let housebatchFilesList = null;

    // State
    let selectedFile = null;
    let objectUrl = null;

    let broadcastFile = null;
    let broadcastObjectUrl = null;
    let broadcastHousesData = [];

    let houseBatchQueue = [];

    let isSubmitting = false;
    let dragCounter = 0;
    let tenantFetchSeq = 0;
    let housebatchTenantFetchSeq = 0;
    const tenantCache = new Map();
    let isGlobalListenersAttached = false;

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

    function detectCategoryFromFilename(filename) {
        if (!filename || typeof filename !== 'string') return '13 - رسائل متنوعة';
        const lower = filename.toLowerCase();

        // 1. Contracts (عقد, عقود, contract, lease)
        if (/عقد|عقود|contract|lease/.test(lower)) {
            return '05 - عقود';
        }
        // 2. Electricity / Water / Utility (كهرباء, ماء, فاتورة, electricity, water, bill)
        if (/كهرباء|ماء|مياه|فاتور[ةه]|electricity|water|bill/.test(lower)) {
            return '06 - كهرباء وماء';
        }
        // 3. Maintenance (صيانة, تصليح, repair, maintenance)
        if (/صيان[ةه]|تصليح|repair|maintenance/.test(lower)) {
            return '10 - صيانة';
        }
        // 4. Personal ID / Passport (هوية, شخصية, بطاقة, جواز, id, passport)
        if (/هوي[ةه]|شخصي[ةه]|بطاق[ةه]|جواز|passport|(?:^|[^a-z0-9])id(?:[^a-z0-9]|$)/.test(lower)) {
            return '02 - بيانات شخصية';
        }
        // 5. Handover (تسليم, استلام, مفتاح, handover)
        if (/تسليم|استلام|مفتاح|handover/.test(lower)) {
            return '04 - محضر تسليم مفتاح';
        }
        // 6. Allocation (تخصيص, allocation)
        if (/تخصيص|allocation/.test(lower)) {
            return '03 - أمر تخصيص';
        }
        // 7. Notices & Warnings (إشعار, انذار, notice, warning)
        if (/[إا]شعار|[إا]نذار|notice|warning/.test(lower)) {
            return '09 - إشعارات';
        }
        // 8. Rent Deduction (استقطاع, deduction)
        if (/استقطاع|deduction/.test(lower)) {
            return '07 - استقطاع إيجار';
        }
        // 9. Modifications (تعديل, modification)
        if (/تعديل|modification/.test(lower)) {
            return '12 - تعديلات';
        }
        // 10. Photos & Inspections (صور, معاينة, inspection, photo)
        if (/صور[ةه]?|معاين[ةه]|inspection|photo/.test(lower)) {
            return '11 - صور ومعاينات';
        }

        return '13 - رسائل متنوعة';
    }

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
        broadcastFile = null;
        if (broadcastObjectUrl && typeof window !== 'undefined' && window.URL && typeof window.URL.revokeObjectURL === 'function') {
            window.URL.revokeObjectURL(broadcastObjectUrl);
            broadcastObjectUrl = null;
        }
        isSubmitting = false;
        dragCounter = 0;
        tenantFetchSeq = 0;
        housebatchTenantFetchSeq = 0;
        houseBatchQueue = [];
        broadcastHousesData = [];
        tenantCache.clear();

        // Common
        btnIngestTrigger = document.getElementById('btn-ingest-trigger');
        dropzoneOverlay = document.getElementById('ingest-dropzone-overlay');
        dropzonePrompt = document.getElementById('ingest-dropzone-prompt');
        ingestModal = document.getElementById('ingest-station-modal');
        btnIngestClose = document.getElementById('btn-ingest-close');
        btnIngestCancel = document.getElementById('btn-ingest-cancel');
        btnSubmit = document.getElementById('btn-ingest-submit');
        submitSpinner = document.getElementById('ingest-submit-spinner');
        submitText = document.getElementById('ingest-submit-text');
        statusMsg = document.getElementById('ingest-status-msg');

        // Progress
        batchProgress = document.getElementById('ingest-batch-progress');
        batchProgressText = document.getElementById('ingest-batch-progress-text');
        batchProgressPct = document.getElementById('ingest-batch-progress-pct');
        batchProgressBar = document.getElementById('ingest-batch-progress-bar');

        // Tabs
        tabModeSingle = document.getElementById('tab-mode-single');
        tabModeBroadcast = document.getElementById('tab-mode-broadcast');
        tabModeHousebatch = document.getElementById('tab-mode-housebatch');

        // Sections
        sectionModeSingle = document.getElementById('section-mode-single');
        sectionModeBroadcast = document.getElementById('section-mode-broadcast');
        sectionModeHousebatch = document.getElementById('section-mode-housebatch');

        // Single mode elements
        fileDropzone = document.getElementById('ingest-file-dropzone');
        fileInput = document.getElementById('ingest-file-input');
        fileInfo = document.getElementById('ingest-file-info');
        fileNameEl = document.getElementById('ingest-file-name');
        fileSizeEl = document.getElementById('ingest-file-size');
        btnRemoveFile = document.getElementById('btn-remove-file');
        previewContainer = document.getElementById('ingest-preview-container');
        pdfPreview = document.getElementById('ingest-pdf-preview');
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

        // Broadcast mode elements
        broadcastDropzone = document.getElementById('broadcast-dropzone');
        broadcastFileInput = document.getElementById('broadcast-file-input');
        broadcastFileInfo = document.getElementById('broadcast-file-info');
        broadcastFileNameEl = document.getElementById('broadcast-file-name');
        broadcastFileSizeEl = document.getElementById('broadcast-file-size');
        btnBroadcastRemoveFile = document.getElementById('btn-broadcast-remove-file');
        broadcastPreviewContainer = document.getElementById('broadcast-preview-container');
        broadcastPdfPreview = document.getElementById('broadcast-pdf-preview');
        broadcastCategorySelect = document.getElementById('broadcast-category-select');
        broadcastTitleInput = document.getElementById('broadcast-title-input');
        broadcastDateInput = document.getElementById('broadcast-date-input');
        broadcastAreaSelect = document.getElementById('broadcast-area-select');
        broadcastSelectedCount = document.getElementById('broadcast-selected-count');
        btnBroadcastSelectAll = document.getElementById('btn-broadcast-select-all');
        btnBroadcastDeselectAll = document.getElementById('btn-broadcast-deselect-all');
        broadcastHouseSearch = document.getElementById('broadcast-house-search');
        broadcastHousesList = document.getElementById('broadcast-houses-list');

        // House Batch mode elements
        housebatchAreaSelect = document.getElementById('housebatch-area-select');
        housebatchHouseSelect = document.getElementById('housebatch-house-select');
        housebatchTenantSelect = document.getElementById('housebatch-tenant-select');
        housebatchCountBadge = document.getElementById('housebatch-count-badge');
        btnHousebatchAddMore = document.getElementById('btn-housebatch-add-more');
        housebatchDropzone = document.getElementById('housebatch-dropzone');
        housebatchFileInput = document.getElementById('housebatch-file-input');
        housebatchFilesList = document.getElementById('housebatch-files-list');

        // Trigger button
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

        // Tab switcher buttons
        if (tabModeSingle) {
            tabModeSingle.addEventListener('click', (e) => {
                e.preventDefault();
                switchTab('single');
            });
        }
        if (tabModeBroadcast) {
            tabModeBroadcast.addEventListener('click', (e) => {
                e.preventDefault();
                switchTab('broadcast');
            });
        }
        if (tabModeHousebatch) {
            tabModeHousebatch.addEventListener('click', (e) => {
                e.preventDefault();
                switchTab('housebatch');
            });
        }

        // Single mode event listeners
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files && e.target.files.length > 0) {
                    handleFilesSelected(e.target.files);
                }
            });
        }
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
        if (btnRemoveFile) {
            btnRemoveFile.addEventListener('click', (e) => {
                e.preventDefault();
                removeFile();
            });
        }
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
        if (btnToggleNewTenant) {
            btnToggleNewTenant.addEventListener('click', () => {
                toggleNewTenantInput();
            });
        }

        // Broadcast mode event listeners
        if (broadcastFileInput) {
            broadcastFileInput.addEventListener('change', (e) => {
                if (e.target.files && e.target.files.length > 0) {
                    handleBroadcastFileSelected(e.target.files[0]);
                }
            });
        }
        if (broadcastDropzone && broadcastFileInput) {
            broadcastDropzone.addEventListener('click', () => broadcastFileInput.click());
            broadcastDropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                broadcastDropzone.classList.add('border-blue-500', 'bg-blue-50/60');
            });
            broadcastDropzone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                broadcastDropzone.classList.remove('border-blue-500', 'bg-blue-50/60');
            });
            broadcastDropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                broadcastDropzone.classList.remove('border-blue-500', 'bg-blue-50/60');
                if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                    handleBroadcastFileSelected(e.dataTransfer.files[0]);
                }
            });
        }
        if (btnBroadcastRemoveFile) {
            btnBroadcastRemoveFile.addEventListener('click', (e) => {
                e.preventDefault();
                removeBroadcastFile();
            });
        }
        if (broadcastAreaSelect) {
            broadcastAreaSelect.addEventListener('change', () => {
                populateBroadcastHouses(broadcastAreaSelect.value);
            });
        }
        if (btnBroadcastSelectAll) {
            btnBroadcastSelectAll.addEventListener('click', (e) => {
                e.preventDefault();
                selectAllBroadcastHouses(true);
            });
        }
        if (btnBroadcastDeselectAll) {
            btnBroadcastDeselectAll.addEventListener('click', (e) => {
                e.preventDefault();
                selectAllBroadcastHouses(false);
            });
        }
        if (broadcastHouseSearch) {
            broadcastHouseSearch.addEventListener('input', (e) => {
                filterBroadcastHouses(e.target.value);
            });
        }

        // House Batch mode event listeners
        if (housebatchFileInput) {
            housebatchFileInput.addEventListener('change', (e) => {
                if (e.target.files && e.target.files.length > 0) {
                    addFilesToHouseBatch(e.target.files);
                }
            });
        }
        if (housebatchDropzone && housebatchFileInput) {
            housebatchDropzone.addEventListener('click', () => housebatchFileInput.click());
            housebatchDropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                housebatchDropzone.classList.add('border-blue-500', 'bg-blue-50/60');
            });
            housebatchDropzone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                housebatchDropzone.classList.remove('border-blue-500', 'bg-blue-50/60');
            });
            housebatchDropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                housebatchDropzone.classList.remove('border-blue-500', 'bg-blue-50/60');
                if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                    addFilesToHouseBatch(e.dataTransfer.files);
                }
            });
        }
        if (btnHousebatchAddMore && housebatchFileInput) {
            btnHousebatchAddMore.addEventListener('click', (e) => {
                e.preventDefault();
                housebatchFileInput.click();
            });
        }
        if (housebatchAreaSelect) {
            housebatchAreaSelect.addEventListener('change', () => {
                populateHousebatchHouses(housebatchAreaSelect.value);
            });
        }
        if (housebatchHouseSelect) {
            housebatchHouseSelect.addEventListener('change', () => {
                populateHousebatchTenants(housebatchAreaSelect ? housebatchAreaSelect.value : '', housebatchHouseSelect.value);
            });
        }

        // Submit button click
        if (btnSubmit) {
            btnSubmit.addEventListener('click', (e) => {
                e.preventDefault();
                if (activeTab === 'broadcast') {
                    submitBroadcastIngest();
                } else if (activeTab === 'housebatch') {
                    submitHouseBatchIngest();
                } else {
                    submitSingleIngest();
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

        switchTab('single');
    }

    function switchTab(tabName) {
        if (!['single', 'broadcast', 'housebatch'].includes(tabName)) return;
        activeTab = tabName;

        const tabs = [
            { id: 'tab-mode-single', name: 'single', sectionId: 'section-mode-single' },
            { id: 'tab-mode-broadcast', name: 'broadcast', sectionId: 'section-mode-broadcast' },
            { id: 'tab-mode-housebatch', name: 'housebatch', sectionId: 'section-mode-housebatch' },
        ];

        tabs.forEach(t => {
            const tabEl = document.getElementById(t.id);
            const secEl = document.getElementById(t.sectionId);
            const isActive = t.name === tabName;

            if (secEl) {
                if (isActive) secEl.classList.remove('hidden');
                else secEl.classList.add('hidden');
            }

            if (tabEl) {
                if (isActive) {
                    tabEl.classList.add('bg-white', 'border-blue-600', 'text-blue-700', 'shadow-xs', 'ring-1', 'ring-blue-500/20');
                    tabEl.classList.remove('bg-slate-100/80', 'border-slate-200', 'text-slate-700');
                    tabEl.setAttribute('aria-selected', 'true');
                } else {
                    tabEl.classList.remove('bg-white', 'border-blue-600', 'text-blue-700', 'shadow-xs', 'ring-1', 'ring-blue-500/20');
                    tabEl.classList.add('bg-slate-100/80', 'border-slate-200', 'text-slate-700');
                    tabEl.setAttribute('aria-selected', 'false');
                }
            }
        });

        // Tab-specific context synchronization
        if (tabName === 'single') {
            populateAreas(getCurrentArea(), getCurrentHouse());
            if (dateInput && !dateInput.value) {
                dateInput.value = getTodayIsoDate();
            }
        } else if (tabName === 'broadcast') {
            populateBroadcastAreas(getCurrentArea());
            if (broadcastDateInput && !broadcastDateInput.value) {
                broadcastDateInput.value = getTodayIsoDate();
            }
            populateBroadcastHouses(broadcastAreaSelect ? broadcastAreaSelect.value : '');
        } else if (tabName === 'housebatch') {
            populateHousebatchAreas(getCurrentArea(), getCurrentHouse());
            renderHouseBatchQueue();
        }

        updateSubmitButtonText();
        resetStatusMsg();
    }

    function updateSubmitButtonText() {
        if (!submitText) return;
        if (activeTab === 'single') {
            submitText.textContent = '⚡ Ingest Document';
        } else if (activeTab === 'broadcast') {
            const count = getSelectedBroadcastHouses().length;
            submitText.textContent = `⚡ Broadcast to ${count} Houses`;
        } else if (activeTab === 'housebatch') {
            const count = houseBatchQueue.length;
            submitText.textContent = `⚡ Ingest ${count} Documents`;
        }
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

    function resetDragCounter() {
        dragCounter = 0;
        if (dropzoneOverlay) dropzoneOverlay.classList.add('hidden');
    }

    function handleGlobalDrop(e) {
        e.preventDefault();
        resetDragCounter();

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

            openIngestStation();
            if (pdfFiles.length > 1) {
                switchTab('housebatch');
                addFilesToHouseBatch(pdfFiles);
            } else {
                if (activeTab === 'broadcast') {
                    handleBroadcastFileSelected(pdfFiles[0]);
                } else {
                    switchTab('single');
                    handleFileSelected(pdfFiles[0]);
                }
            }
        }
    }

    function handleFilesSelected(files) {
        if (!files || files.length === 0) return;
        const fileList = Array.from(files).filter(f => f.name.toLowerCase().endsWith('.pdf') || f.type === 'application/pdf');
        if (fileList.length === 0) {
            showStatusMsg('Invalid file format. Please select a PDF document (.pdf).', true);
            return;
        }

        if (fileList.length > 1 || activeTab === 'housebatch') {
            switchTab('housebatch');
            addFilesToHouseBatch(fileList);
        } else if (activeTab === 'broadcast') {
            handleBroadcastFileSelected(fileList[0]);
        } else {
            handleFileSelected(fileList[0]);
        }
    }

    // ── Single Mode Logic ──
    function handleFileSelected(file) {
        if (!file) return;
        if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
            showStatusMsg('Invalid file format. Please select a PDF document (.pdf).', true);
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

    // ── Broadcast Mode Logic ──
    function handleBroadcastFileSelected(file) {
        if (!file) return;
        if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
            showStatusMsg('Invalid file format. Please select a PDF document (.pdf).', true);
            return;
        }

        broadcastFile = file;
        resetStatusMsg();

        if (broadcastFileNameEl) broadcastFileNameEl.textContent = file.name;
        if (broadcastFileSizeEl) broadcastFileSizeEl.textContent = formatFileSize(file.size);
        if (broadcastFileInfo) broadcastFileInfo.classList.remove('hidden');
        if (broadcastDropzone) broadcastDropzone.classList.add('hidden');

        if (typeof window !== 'undefined' && window.URL && typeof window.URL.createObjectURL === 'function') {
            if (broadcastObjectUrl && typeof window.URL.revokeObjectURL === 'function') {
                window.URL.revokeObjectURL(broadcastObjectUrl);
            }
            try {
                broadcastObjectUrl = window.URL.createObjectURL(file);
                if (broadcastPdfPreview) {
                    broadcastPdfPreview.src = `${broadcastObjectUrl}#toolbar=0&view=FitH`;
                }
            } catch (err) {
                console.warn('Could not create ObjectURL for broadcast PDF preview:', err);
            }
        }
        if (broadcastPreviewContainer) broadcastPreviewContainer.classList.remove('hidden');

        if (broadcastTitleInput) {
            broadcastTitleInput.value = file.name.replace(/\.pdf$/i, '').replace(/[-_]+/g, ' ').trim();
        }
    }

    function removeBroadcastFile() {
        broadcastFile = null;
        if (broadcastFileInput) broadcastFileInput.value = '';
        if (broadcastTitleInput) broadcastTitleInput.value = '';
        if (broadcastObjectUrl && typeof window !== 'undefined' && window.URL && typeof window.URL.revokeObjectURL === 'function') {
            window.URL.revokeObjectURL(broadcastObjectUrl);
            broadcastObjectUrl = null;
        }
        if (broadcastPdfPreview) broadcastPdfPreview.src = 'about:blank';
        if (broadcastPreviewContainer) broadcastPreviewContainer.classList.add('hidden');
        if (broadcastFileInfo) broadcastFileInfo.classList.add('hidden');
        if (broadcastDropzone) broadcastDropzone.classList.remove('hidden');
    }

    function populateBroadcastAreas(targetArea = null) {
        if (!broadcastAreaSelect) return;
        const tree = (typeof globalTreeData !== 'undefined' ? globalTreeData : window.globalTreeData) || [];
        const curVal = broadcastAreaSelect.value;
        broadcastAreaSelect.innerHTML = '<option value="">Select Area...</option>';
        tree.forEach(area => {
            const opt = document.createElement('option');
            opt.value = area.name;
            opt.textContent = area.name;
            broadcastAreaSelect.appendChild(opt);
        });

        const activeArea = targetArea || curVal || getCurrentArea();
        if (activeArea) {
            broadcastAreaSelect.value = activeArea;
        }
    }

    async function populateBroadcastHouses(areaName) {
        if (!broadcastHousesList) return;
        broadcastHousesList.innerHTML = '';

        if (!areaName) {
            broadcastHousesList.innerHTML = '<p class="text-xs text-slate-400 p-3 text-center">Please select a Target Area above.</p>';
            updateBroadcastSelectedCount();
            return;
        }

        const houses = getHousesForArea(areaName);
        if (houses.length === 0) {
            broadcastHousesList.innerHTML = '<p class="text-xs text-slate-400 p-3 text-center">No houses found in this area.</p>';
            updateBroadcastSelectedCount();
            return;
        }

        broadcastHousesData = [];

        // 1. Initial render with placeholders
        for (const house of houses) {
            const itemEl = document.createElement('label');
            itemEl.className = 'broadcast-house-item flex items-center justify-between p-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 cursor-pointer transition-colors shadow-2xs';
            itemEl.dataset.house = house;

            itemEl.innerHTML = `
                <div class="flex items-center gap-2.5 min-w-0">
                    <input type="checkbox" class="broadcast-house-checkbox rounded text-blue-600 focus:ring-blue-500 w-4 h-4 cursor-pointer" value="${house}" data-house="${house}" data-tenant-id="" />
                    <span class="text-xs font-bold text-slate-800">House ${house}</span>
                </div>
                <span class="broadcast-tenant-badge text-[11px] px-2 py-0.5 rounded-full font-medium bg-slate-100 text-slate-500 flex-shrink-0">
                    Loading tenant...
                </span>
            `;

            const checkbox = itemEl.querySelector('.broadcast-house-checkbox');
            checkbox.addEventListener('change', () => {
                updateBroadcastSelectedCount();
            });

            broadcastHousesList.appendChild(itemEl);
        }

        // 2. Fetch and populate latest tenant badge for each house
        for (const house of houses) {
            const { tenants, latestTenantId } = await getTenantsForHouse(areaName, house);
            const latestTenant = resolveLatestTenant(tenants);

            const itemEl = broadcastHousesList.querySelector(`.broadcast-house-item[data-house="${house}"]`);
            if (itemEl) {
                const checkbox = itemEl.querySelector('.broadcast-house-checkbox');
                if (checkbox) {
                    checkbox.dataset.tenantId = latestTenantId || '';
                }
                const badge = itemEl.querySelector('.broadcast-tenant-badge');
                if (badge) {
                    if (latestTenant && latestTenant.name) {
                        badge.textContent = `👤 ${latestTenant.name}`;
                        badge.className = 'broadcast-tenant-badge text-[11px] px-2 py-0.5 rounded-full font-medium bg-blue-50 text-blue-700 border border-blue-100 flex-shrink-0';
                    } else {
                        badge.textContent = 'No Tenant';
                        badge.className = 'broadcast-tenant-badge text-[11px] px-2 py-0.5 rounded-full font-medium bg-slate-100 text-slate-500 flex-shrink-0';
                    }
                }
            }

            broadcastHousesData.push({
                house,
                tenantId: latestTenantId || '',
                tenantName: latestTenant ? latestTenant.name : '',
            });
        }

        updateBroadcastSelectedCount();
    }

    function getSelectedBroadcastHouses() {
        if (!broadcastHousesList) return [];
        const checkedBoxes = broadcastHousesList.querySelectorAll('.broadcast-house-checkbox:checked');
        const result = [];
        checkedBoxes.forEach(cb => {
            result.push({
                house: cb.dataset.house || cb.value,
                tenantId: cb.dataset.tenantId || '',
            });
        });
        return result;
    }

    function updateBroadcastSelectedCount() {
        const count = getSelectedBroadcastHouses().length;
        if (broadcastSelectedCount) {
            broadcastSelectedCount.textContent = `${count} selected`;
        }
        updateSubmitButtonText();
    }

    function selectAllBroadcastHouses(select = true) {
        if (!broadcastHousesList) return;
        const items = broadcastHousesList.querySelectorAll('.broadcast-house-item');
        items.forEach(item => {
            if (!select || !item.classList.contains('hidden')) {
                const cb = item.querySelector('.broadcast-house-checkbox');
                if (cb) cb.checked = select;
            }
        });
        updateBroadcastSelectedCount();
    }

    function filterBroadcastHouses(query) {
        if (!broadcastHousesList) return;
        const q = (query || '').trim().toLowerCase();
        const items = broadcastHousesList.querySelectorAll('.broadcast-house-item');
        items.forEach(item => {
            const house = item.dataset.house || '';
            const text = item.textContent.toLowerCase();
            if (!q || house.toLowerCase().includes(q) || text.includes(q)) {
                item.classList.remove('hidden');
            } else {
                item.classList.add('hidden');
            }
        });
    }

    // ── House Batch Mode Logic ──
    function populateHousebatchAreas(targetArea = null, targetHouse = null) {
        if (!housebatchAreaSelect) return;
        const tree = (typeof globalTreeData !== 'undefined' ? globalTreeData : window.globalTreeData) || [];
        const curVal = housebatchAreaSelect.value;
        housebatchAreaSelect.innerHTML = '<option value="">Select Area...</option>';
        tree.forEach(area => {
            const opt = document.createElement('option');
            opt.value = area.name;
            opt.textContent = area.name;
            housebatchAreaSelect.appendChild(opt);
        });

        const activeArea = targetArea || curVal || getCurrentArea();
        if (activeArea) {
            housebatchAreaSelect.value = activeArea;
        }
        populateHousebatchHouses(housebatchAreaSelect.value, targetHouse);
    }

    function populateHousebatchHouses(areaName, targetHouse = null) {
        if (!housebatchHouseSelect) return;
        const curVal = housebatchHouseSelect.value;
        housebatchHouseSelect.innerHTML = '<option value="">Select House...</option>';

        if (!areaName) {
            populateHousebatchTenants('', '');
            return;
        }

        const tree = (typeof globalTreeData !== 'undefined' ? globalTreeData : window.globalTreeData) || [];
        const areaNode = tree.find(a => a.name === areaName);
        if (areaNode && Array.isArray(areaNode.children)) {
            areaNode.children.forEach(house => {
                const opt = document.createElement('option');
                opt.value = house.name;
                opt.textContent = house.name;
                housebatchHouseSelect.appendChild(opt);
            });
        }

        const activeHouse = targetHouse || curVal || getCurrentHouse();
        if (activeHouse) {
            housebatchHouseSelect.value = activeHouse;
        }
        populateHousebatchTenants(areaName, housebatchHouseSelect.value);
    }

    async function populateHousebatchTenants(areaName, houseName) {
        if (!housebatchTenantSelect) return;
        housebatchTenantSelect.innerHTML = '<option value="">(Auto-detect latest tenant)</option>';
        if (!areaName || !houseName) return;

        const currentSeq = ++housebatchTenantFetchSeq;
        const { tenants, latestTenantId } = await getTenantsForHouse(areaName, houseName);
        if (currentSeq !== housebatchTenantFetchSeq) return;

        if (Array.isArray(tenants)) {
            tenants.forEach(t => {
                const opt = document.createElement('option');
                opt.value = String(t.id != null ? t.id : t.name);
                const yearHint = t.start_date ? ` (${t.start_date.substring(0, 4)})` : '';
                opt.textContent = `${t.name}${yearHint}`;
                if (String(opt.value) === String(latestTenantId)) {
                    opt.selected = true;
                }
                housebatchTenantSelect.appendChild(opt);
            });
        }

        if (latestTenantId) {
            housebatchTenantSelect.value = String(latestTenantId);
        }
    }

    function addFilesToHouseBatch(files) {
        if (!files || files.length === 0) return;
        const fileList = Array.from(files).filter(f => f.name.toLowerCase().endsWith('.pdf') || f.type === 'application/pdf');
        if (fileList.length === 0) {
            showStatusMsg('Invalid file format. Please select PDF documents (.pdf).', true);
            return;
        }

        for (const f of fileList) {
            const autoTitle = f.name.replace(/\.pdf$/i, '').replace(/[-_]+/g, ' ').trim();
            houseBatchQueue.push({
                id: 'hbf_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
                file: f,
                name: f.name,
                size: f.size,
                title: autoTitle,
                category: detectCategoryFromFilename(f.name),
                date: getTodayIsoDate(),
            });
        }

        if (housebatchAreaSelect && !housebatchAreaSelect.value) {
            populateHousebatchAreas(getCurrentArea(), getCurrentHouse());
        }

        renderHouseBatchQueue();
    }

    function renderHouseBatchQueue() {
        if (!housebatchFilesList) return;

        if (housebatchCountBadge) {
            housebatchCountBadge.textContent = `${houseBatchQueue.length} file${houseBatchQueue.length === 1 ? '' : 's'}`;
        }

        if (housebatchDropzone) {
            if (houseBatchQueue.length === 0) {
                housebatchDropzone.classList.remove('hidden');
                housebatchFilesList.classList.add('hidden');
            } else {
                housebatchDropzone.classList.add('hidden');
                housebatchFilesList.classList.remove('hidden');
            }
        }

        updateSubmitButtonText();

        housebatchFilesList.innerHTML = '';
        houseBatchQueue.forEach((item, fileIdx) => {
            const row = document.createElement('div');
            row.className = 'bg-white border border-slate-200 rounded-xl p-3 shadow-2xs flex flex-col md:flex-row md:items-center gap-3 housebatch-file-row';
            row.dataset.fileIdx = String(fileIdx);

            const categoryOptions = STANDARD_CATEGORIES.map(cat => 
                `<option value="${cat}" ${cat === item.category ? 'selected' : ''}>${cat}</option>`
            ).join('');

            row.innerHTML = `
                <div class="flex items-center gap-2.5 min-w-0 flex-1 md:w-1/4">
                    <div class="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                    </div>
                    <div class="min-w-0 flex-1">
                        <p class="text-xs font-bold text-slate-800 truncate housebatch-file-name" title="${item.name}">${item.name}</p>
                        <p class="text-[10px] text-slate-400 font-mono housebatch-file-size">${formatFileSize(item.size)}</p>
                    </div>
                </div>
                <div class="flex-1 min-w-[160px]">
                    <label class="block text-[10px] font-semibold text-slate-500 mb-0.5 md:hidden">Document Title</label>
                    <input type="text" class="housebatch-title-input w-full px-2.5 py-1.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-slate-50 focus:bg-white font-medium" value="${item.title || ''}" placeholder="Document title..." />
                </div>
                <div class="w-full md:w-48 flex-shrink-0">
                    <label class="block text-[10px] font-semibold text-slate-500 mb-0.5 md:hidden">Category</label>
                    <select class="housebatch-category-select w-full px-2 py-1.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-slate-50 focus:bg-white font-medium">
                        ${categoryOptions}
                    </select>
                </div>
                <div class="w-full md:w-36 flex-shrink-0">
                    <label class="block text-[10px] font-semibold text-slate-500 mb-0.5 md:hidden">Date</label>
                    <input type="date" class="housebatch-date-input w-full px-2 py-1.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-slate-50 focus:bg-white font-medium" value="${item.date || ''}" />
                </div>
                <button type="button" class="btn-remove-housebatch-file text-slate-400 hover:text-rose-600 p-1.5 rounded-lg hover:bg-rose-50 transition-colors cursor-pointer self-end md:self-center" title="Remove file">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
            `;

            const titleInp = row.querySelector('.housebatch-title-input');
            titleInp.addEventListener('input', (e) => {
                item.title = e.target.value;
            });

            const catSelect = row.querySelector('.housebatch-category-select');
            catSelect.addEventListener('change', (e) => {
                item.category = e.target.value;
            });

            const dateInp = row.querySelector('.housebatch-date-input');
            dateInp.addEventListener('change', (e) => {
                item.date = e.target.value;
            });

            const btnRemove = row.querySelector('.btn-remove-housebatch-file');
            btnRemove.addEventListener('click', () => {
                houseBatchQueue.splice(fileIdx, 1);
                renderHouseBatchQueue();
            });

            housebatchFilesList.appendChild(row);
        });
    }

    // ── Shared Helper Functions ──
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

        const activeArea = targetArea || areaSelect.value || getCurrentArea();
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

        const activeHouse = targetHouse || houseSelect.value || getCurrentHouse();
        if (activeHouse) {
            houseSelect.value = activeHouse;
        }
        populateTenants(areaName, houseSelect.value);
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

        // 1. targetTenantId match
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

        // 2. window.currentTenant match
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

        // 3. Latest tenant resolution
        if (!isFallback && Array.isArray(fetchedTenants) && fetchedTenants.length > 0) {
            const isActive = (t) => !t.end_date || t.end_date === null || (typeof t.end_date === 'string' && (t.end_date.trim() === '' || t.end_date.trim().toLowerCase() === 'present' || t.end_date.trim().toLowerCase() === 'active'));
            const activeTenants = fetchedTenants.filter(isActive);

            if (activeTenants.length > 0) {
                const sortedActive = [...activeTenants].sort((a, b) => {
                    const cmp = compareDatesDesc(a.start_date, b.start_date);
                    if (cmp !== 0) return cmp;
                    return (b.id != null && a.id != null) ? b.id - a.id : 0;
                });
                const chosen = sortedActive[0];
                const opt = availableOptions.find(o => o.value === String(chosen.id) || (o.dataset.name && o.dataset.name === chosen.name));
                if (opt) tenantSelect.value = opt.value;
            } else {
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

    function openIngestStation(initialFiles = null) {
        if (!ingestModal) return;
        ingestModal.classList.remove('hidden');
        resetStatusMsg();

        if (initialFiles) {
            const filesArray = Array.isArray(initialFiles) 
                ? initialFiles 
                : (typeof FileList !== 'undefined' && initialFiles instanceof FileList ? Array.from(initialFiles) : [initialFiles]);
            
            if (filesArray.length > 1) {
                switchTab('housebatch');
                addFilesToHouseBatch(filesArray);
            } else if (filesArray.length === 1) {
                if (activeTab === 'broadcast') {
                    handleBroadcastFileSelected(filesArray[0]);
                } else {
                    switchTab('single');
                    handleFileSelected(filesArray[0]);
                }
            }
        } else {
            switchTab(activeTab);
        }
    }

    function closeIngestStation() {
        if (!ingestModal) return;
        ingestModal.classList.add('hidden');
        resetIngestForm();
    }

    function resetIngestForm() {
        removeFile();
        removeBroadcastFile();
        houseBatchQueue = [];
        renderHouseBatchQueue();
        if (titleInput) titleInput.value = '';
        if (dateInput) dateInput.value = getTodayIsoDate();
        if (broadcastDateInput) broadcastDateInput.value = getTodayIsoDate();
        if (notesInput) notesInput.value = '';
        if (newTenantInput) newTenantInput.value = '';
        if (newTenantContainer) newTenantContainer.classList.add('hidden');
        if (btnToggleNewTenant) btnToggleNewTenant.textContent = '+ Add New Tenant';
        if (categorySelect) categorySelect.value = '13 - رسائل متنوعة';
        if (broadcastCategorySelect) broadcastCategorySelect.value = '09 - إشعارات';
        if (batchProgress) batchProgress.classList.add('hidden');
        resetStatusMsg();
        switchTab('single');
    }

    function resetStatusMsg() {
        if (!statusMsg) return;
        statusMsg.className = 'mx-6 my-2 px-3 py-2 rounded-xl text-xs font-medium hidden';
        statusMsg.textContent = '';
    }

    function showStatusMsg(text, isError = false) {
        if (!statusMsg) return;
        statusMsg.className = `mx-6 my-2 px-3 py-2 rounded-xl text-xs font-medium ${
            isError ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
        }`;
        statusMsg.textContent = text;
        statusMsg.classList.remove('hidden');
    }

    // ── Submission: Single Document ──
    async function submitSingleIngest() {
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
            updateSubmitButtonText();
        }
    }

    // ── Submission: Broadcast Notice ──
    async function submitBroadcastIngest() {
        if (isSubmitting) return;

        if (!broadcastFile) {
            showStatusMsg('Please select or drop a PDF notice to broadcast.', true);
            return;
        }

        const area = broadcastAreaSelect ? broadcastAreaSelect.value.trim() : '';
        if (!area) {
            showStatusMsg('Please select a Target Area to broadcast to.', true);
            return;
        }

        const selectedHouses = getSelectedBroadcastHouses();
        if (selectedHouses.length === 0) {
            showStatusMsg('Please select at least one house to broadcast to.', true);
            return;
        }

        const category = broadcastCategorySelect ? broadcastCategorySelect.value.trim() : '09 - إشعارات';
        const title = (broadcastTitleInput && broadcastTitleInput.value.trim()) 
            ? broadcastTitleInput.value.trim() 
            : broadcastFile.name.replace(/\.pdf$/i, '').replace(/[-_]+/g, ' ').trim();
        const primaryDate = (broadcastDateInput && broadcastDateInput.value.trim()) 
            ? broadcastDateInput.value.trim() 
            : getTodayIsoDate();

        isSubmitting = true;
        if (btnSubmit) btnSubmit.disabled = true;
        if (submitSpinner) submitSpinner.classList.remove('hidden');
        if (batchProgress) batchProgress.classList.remove('hidden');
        resetStatusMsg();

        const total = selectedHouses.length;
        let completedCount = 0;
        let failedCount = 0;
        const errors = [];
        let lastHouse = selectedHouses[0]?.house || '';

        for (let i = 0; i < total; i++) {
            const item = selectedHouses[i];
            const currentNum = i + 1;

            if (batchProgressText) {
                batchProgressText.textContent = `Broadcasting ${currentNum} of ${total}: House ${item.house}...`;
            }
            if (submitText) {
                submitText.textContent = `Broadcasting (${currentNum}/${total})...`;
            }
            const pct = Math.round(((currentNum - 1) / total) * 100);
            if (batchProgressPct) batchProgressPct.textContent = `${pct}%`;
            if (batchProgressBar) batchProgressBar.style.width = `${pct}%`;

            const formData = new FormData();
            formData.append('file', broadcastFile);
            formData.append('mode', 'manual');
            formData.append('area_id', area);
            formData.append('house_id', item.house);
            if (item.tenantId) {
                formData.append('tenant_id', item.tenantId);
            }
            formData.append('category', category);
            formData.append('arabic_title', title);
            formData.append('primary_date', primaryDate);

            try {
                const res = await fetch('/api/ingest', {
                    method: 'POST',
                    body: formData,
                });
                if (res.ok) {
                    completedCount++;
                    lastHouse = item.house;
                } else {
                    failedCount++;
                    const err = await res.json().catch(() => ({}));
                    errors.push(`House ${item.house}: ${err.detail || 'Failed'}`);
                }
            } catch (err) {
                failedCount++;
                errors.push(`House ${item.house}: Network error`);
            }
        }

        if (batchProgressPct) batchProgressPct.textContent = '100%';
        if (batchProgressBar) batchProgressBar.style.width = '100%';

        isSubmitting = false;
        if (btnSubmit) btnSubmit.disabled = false;
        if (submitSpinner) submitSpinner.classList.add('hidden');
        updateSubmitButtonText();

        const toastFn = (typeof showToast === 'function')
            ? showToast
            : ((typeof window !== 'undefined' && typeof window.showToast === 'function') ? window.showToast : null);

        if (failedCount === 0) {
            const successMsg = `Successfully broadcasted to ${completedCount} house${completedCount === 1 ? '' : 's'}`;
            if (toastFn) toastFn(successMsg, 'success');
            else if (typeof alert === 'function') alert(successMsg);

            closeIngestStation();
            if (typeof window.refreshCurrentTab === 'function') window.refreshCurrentTab(area, lastHouse);
            if (typeof window.loadTree === 'function') window.loadTree();
        } else {
            const partialMsg = `Broadcasted to ${completedCount} of ${total} houses. (${failedCount} failed: ${errors.join('; ')})`;
            showStatusMsg(partialMsg, true);
            if (toastFn) toastFn(partialMsg, 'error');
            if (completedCount > 0) {
                if (typeof window.refreshCurrentTab === 'function') window.refreshCurrentTab(area, lastHouse);
                if (typeof window.loadTree === 'function') window.loadTree();
            }
        }
    }

    // ── Submission: House Batch ──
    async function submitHouseBatchIngest() {
        if (isSubmitting) return;

        if (houseBatchQueue.length === 0) {
            showStatusMsg('Please add at least one PDF file to the batch queue.', true);
            return;
        }

        const area = housebatchAreaSelect ? housebatchAreaSelect.value.trim() : '';
        const house = housebatchHouseSelect ? housebatchHouseSelect.value.trim() : '';
        if (!area || !house) {
            showStatusMsg('Please select both a Target Area and Target House for the batch.', true);
            return;
        }

        const tenantId = housebatchTenantSelect ? housebatchTenantSelect.value.trim() : '';

        isSubmitting = true;
        if (btnSubmit) btnSubmit.disabled = true;
        if (submitSpinner) submitSpinner.classList.remove('hidden');
        if (batchProgress) batchProgress.classList.remove('hidden');
        resetStatusMsg();

        const total = houseBatchQueue.length;
        let completedCount = 0;
        let failedCount = 0;
        const errors = [];

        for (let i = 0; i < total; i++) {
            const item = houseBatchQueue[i];
            const currentNum = i + 1;

            if (batchProgressText) {
                batchProgressText.textContent = `Ingesting ${currentNum} of ${total}: ${item.name}...`;
            }
            if (submitText) {
                submitText.textContent = `Ingesting (${currentNum}/${total})...`;
            }
            const pct = Math.round(((currentNum - 1) / total) * 100);
            if (batchProgressPct) batchProgressPct.textContent = `${pct}%`;
            if (batchProgressBar) batchProgressBar.style.width = `${pct}%`;

            const formData = new FormData();
            formData.append('file', item.file);
            formData.append('mode', 'manual');
            formData.append('area_id', area);
            formData.append('house_id', house);
            if (tenantId) {
                formData.append('tenant_id', tenantId);
            }
            formData.append('category', item.category || '13 - رسائل متنوعة');
            formData.append('arabic_title', item.title || item.name.replace(/\.pdf$/i, '').replace(/[-_]+/g, ' ').trim());
            formData.append('primary_date', item.date || getTodayIsoDate());

            try {
                const res = await fetch('/api/ingest', {
                    method: 'POST',
                    body: formData,
                });
                if (res.ok) {
                    completedCount++;
                } else {
                    failedCount++;
                    const err = await res.json().catch(() => ({}));
                    errors.push(`${item.name}: ${err.detail || 'Failed'}`);
                }
            } catch (err) {
                failedCount++;
                errors.push(`${item.name}: Network error`);
            }
        }

        if (batchProgressPct) batchProgressPct.textContent = '100%';
        if (batchProgressBar) batchProgressBar.style.width = '100%';

        isSubmitting = false;
        if (btnSubmit) btnSubmit.disabled = false;
        if (submitSpinner) submitSpinner.classList.add('hidden');
        updateSubmitButtonText();

        const toastFn = (typeof showToast === 'function')
            ? showToast
            : ((typeof window !== 'undefined' && typeof window.showToast === 'function') ? window.showToast : null);

        if (failedCount === 0) {
            const successMsg = `Successfully ingested ${completedCount} document${completedCount === 1 ? '' : 's'}`;
            if (toastFn) toastFn(successMsg, 'success');
            else if (typeof alert === 'function') alert(successMsg);

            closeIngestStation();
            if (typeof window.refreshCurrentTab === 'function') window.refreshCurrentTab(area, house);
            if (typeof window.loadTree === 'function') window.loadTree();
        } else {
            const partialMsg = `Ingested ${completedCount} of ${total} documents. (${failedCount} failed: ${errors.join('; ')})`;
            showStatusMsg(partialMsg, true);
            if (toastFn) toastFn(partialMsg, 'error');
            if (completedCount > 0) {
                if (typeof window.refreshCurrentTab === 'function') window.refreshCurrentTab(area, house);
                if (typeof window.loadTree === 'function') window.loadTree();
            }
        }
    }

    // ── Direct Drag-and-Drop Ingestion (House Card & Category Folder) ──
    async function handleDirectHouseDrop(files, houseId, areaName = null) {
        if (!files || files.length === 0 || !houseId) return;
        const fileList = Array.from(files).filter(f => f.name.toLowerCase().endsWith('.pdf') || f.type === 'application/pdf');
        if (fileList.length === 0) {
            const toastFn = (typeof showToast === 'function') ? showToast : (window.showToast || null);
            if (toastFn) toastFn('Only PDF files are supported for direct ingestion.', 'error');
            return;
        }

        const area = areaName || getCurrentArea() || '';
        const { tenants, latestTenantId } = await getTenantsForHouse(area, String(houseId));
        const todayDate = getTodayIsoDate();
        const toastFn = (typeof showToast === 'function') ? showToast : (window.showToast || null);

        for (const file of fileList) {
            const cleanTitle = file.name.replace(/\.pdf$/i, '').replace(/[-_]+/g, ' ').trim();
            const formData = new FormData();
            formData.append('file', file);
            formData.append('mode', 'manual');
            formData.append('area_id', area);
            formData.append('house_id', String(houseId));
            if (latestTenantId) {
                formData.append('tenant_id', latestTenantId);
            }
            formData.append('category', '13 - رسائل متنوعة');
            formData.append('arabic_title', cleanTitle);
            formData.append('primary_date', todayDate);

            try {
                const res = await fetch('/api/ingest', {
                    method: 'POST',
                    body: formData,
                });
                if (res.ok) {
                    if (toastFn) toastFn(`⚡ Document "${cleanTitle}" filed into House ${houseId}!`, 'success');
                } else {
                    const err = await res.json().catch(() => ({}));
                    if (toastFn) toastFn(`Failed to file "${cleanTitle}": ${err.detail || 'Error'}`, 'error');
                }
            } catch (err) {
                if (toastFn) toastFn(`Network error filing "${cleanTitle}" into House ${houseId}`, 'error');
            }
        }

        if (typeof window.refreshCurrentTab === 'function') window.refreshCurrentTab(area, String(houseId));
        if (typeof window.loadTree === 'function') window.loadTree();
    }

    async function handleDirectCategoryDrop(files, categoryName, houseId = null, areaName = null) {
        if (!files || files.length === 0 || !categoryName) return;
        const fileList = Array.from(files).filter(f => f.name.toLowerCase().endsWith('.pdf') || f.type === 'application/pdf');
        if (fileList.length === 0) {
            const toastFn = (typeof showToast === 'function') ? showToast : (window.showToast || null);
            if (toastFn) toastFn('Only PDF files are supported for direct ingestion.', 'error');
            return;
        }

        const area = areaName || getCurrentArea() || '';
        const house = houseId || getCurrentHouse() || '';
        const { tenants, latestTenantId } = await getTenantsForHouse(area, String(house));
        const todayDate = getTodayIsoDate();
        const toastFn = (typeof showToast === 'function') ? showToast : (window.showToast || null);

        for (const file of fileList) {
            const cleanTitle = file.name.replace(/\.pdf$/i, '').replace(/[-_]+/g, ' ').trim();
            const formData = new FormData();
            formData.append('file', file);
            formData.append('mode', 'manual');
            formData.append('area_id', area);
            formData.append('house_id', String(house));
            if (latestTenantId) {
                formData.append('tenant_id', latestTenantId);
            }
            formData.append('category', categoryName);
            formData.append('arabic_title', cleanTitle);
            formData.append('primary_date', todayDate);

            try {
                const res = await fetch('/api/ingest', {
                    method: 'POST',
                    body: formData,
                });
                if (res.ok) {
                    if (toastFn) toastFn(`⚡ Document "${cleanTitle}" filed into ${categoryName} for House ${house}!`, 'success');
                } else {
                    const err = await res.json().catch(() => ({}));
                    if (toastFn) toastFn(`Failed to file "${cleanTitle}": ${err.detail || 'Error'}`, 'error');
                }
            } catch (err) {
                if (toastFn) toastFn(`Network error filing "${cleanTitle}" into ${categoryName}`, 'error');
            }
        }

        if (typeof window.loadCategories === 'function') window.loadCategories(area, String(house));
        if (typeof window.refreshCurrentTab === 'function') window.refreshCurrentTab(area, String(house));
        if (typeof window.loadTree === 'function') window.loadTree();
    }

    // Expose globals
    window.initIngestStation = initIngestStation;
    window.openIngestStation = openIngestStation;
    window.closeIngestStation = closeIngestStation;
    window.switchTab = switchTab;
    window.getActiveTab = () => activeTab;
    window.getCurrentTab = () => activeTab;
    window.handleFileSelected = handleFileSelected;
    window.handleBroadcastFileSelected = handleBroadcastFileSelected;
    window.handleFilesSelected = handleFilesSelected;
    window.removeFile = removeFile;
    window.removeBroadcastFile = removeBroadcastFile;
    window.submitSingleIngest = submitSingleIngest;
    window.submitBroadcastIngest = submitBroadcastIngest;
    window.submitHouseBatchIngest = submitHouseBatchIngest;
    window.submitIngestForm = submitSingleIngest;
    window.formatFileSize = formatFileSize;
    window.getTodayIsoDate = getTodayIsoDate;
    window.resetIngestForm = resetIngestForm;
    window.detectCategoryFromFilename = detectCategoryFromFilename;
    window.detectHouseFromFilename = detectHouseFromFilename;
    window.getTenantsForHouse = getTenantsForHouse;
    window.resolveLatestTenant = resolveLatestTenant;
    window.populateAreas = populateAreas;
    window.populateHouses = populateHouses;
    window.populateTenants = populateTenants;
    window.populateBroadcastAreas = populateBroadcastAreas;
    window.populateBroadcastHouses = populateBroadcastHouses;
    window.getSelectedBroadcastHouses = getSelectedBroadcastHouses;
    window.selectAllBroadcastHouses = selectAllBroadcastHouses;
    window.filterBroadcastHouses = filterBroadcastHouses;
    window.populateHousebatchAreas = populateHousebatchAreas;
    window.populateHousebatchHouses = populateHousebatchHouses;
    window.populateHousebatchTenants = populateHousebatchTenants;
    window.addFilesToHouseBatch = addFilesToHouseBatch;
    window.renderHouseBatchQueue = renderHouseBatchQueue;
    window.getHouseBatchQueue = () => houseBatchQueue;
    window.handleDirectHouseDrop = handleDirectHouseDrop;
    window.handleDirectCategoryDrop = handleDirectCategoryDrop;
    window.resetDragCounter = resetDragCounter;

    // Backward compatibility shims
    window.updateModeUI = () => switchTab(activeTab);
    window.submitBatchIngest = submitHouseBatchIngest;
    window.getBatchQueue = () => houseBatchQueue;
    window.addFilesToBatch = addFilesToHouseBatch;
    window.renderBatchQueue = renderHouseBatchQueue;
    window.populateBatchAreas = populateHousebatchAreas;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            initIngestStation,
            openIngestStation,
            closeIngestStation,
            switchTab,
            getActiveTab: () => activeTab,
            getCurrentTab: () => activeTab,
            handleFileSelected,
            handleBroadcastFileSelected,
            handleFilesSelected,
            removeFile,
            removeBroadcastFile,
            submitSingleIngest,
            submitBroadcastIngest,
            submitHouseBatchIngest,
            submitIngestForm: submitSingleIngest,
            formatFileSize,
            populateAreas,
            populateHouses,
            populateTenants,
            populateBroadcastAreas,
            populateBroadcastHouses,
            getSelectedBroadcastHouses,
            selectAllBroadcastHouses,
            filterBroadcastHouses,
            populateHousebatchAreas,
            populateHousebatchHouses,
            populateHousebatchTenants,
            addFilesToHouseBatch,
            renderHouseBatchQueue,
            getHouseBatchQueue: () => houseBatchQueue,
            getTodayIsoDate,
            resetIngestForm,
            detectCategoryFromFilename,
            detectHouseFromFilename,
            getTenantsForHouse,
            resolveLatestTenant,
            handleDirectHouseDrop,
            handleDirectCategoryDrop,
            resetDragCounter,
            // Backwards compatibility
            updateModeUI: () => switchTab(activeTab),
            submitBatchIngest: submitHouseBatchIngest,
            getBatchQueue: () => houseBatchQueue,
            addFilesToBatch: addFilesToHouseBatch,
            renderBatchQueue: renderHouseBatchQueue,
            populateBatchAreas: populateHousebatchAreas,
        };
    }
})();
