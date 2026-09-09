// ── Ingest Station Controller (Phase 99: UI-01 & UI-02) ───────────────────
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
    let btnAutofill = null;
    let autofillSpinner = null;
    let autofillText = null;
    let btnSubmit = null;
    let submitSpinner = null;
    let submitText = null;

    let selectedFile = null;
    let objectUrl = null;
    let isSubmitting = false;
    let isAutofilling = false;
    let dragCounter = 0;

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
        isAutofilling = false;
        dragCounter = 0;
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
        btnAutofill = document.getElementById('btn-ingest-autofill');
        autofillSpinner = document.getElementById('ingest-autofill-spinner');
        autofillText = document.getElementById('ingest-autofill-text');
        btnSubmit = document.getElementById('btn-ingest-submit');
        submitSpinner = document.getElementById('ingest-submit-spinner');
        submitText = document.getElementById('ingest-submit-text');

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


        // Local Dropzone inside modal
        if (fileDropzone && fileInput) {
            fileDropzone.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', (e) => {
                if (e.target.files && e.target.files.length > 0) {
                    handleFileSelected(e.target.files[0]);
                }
            });

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
                    handleFileSelected(e.dataTransfer.files[0]);
                }
            });
        }

        // Remove file button
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

        // Area & House selects
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

        // Tenant toggle button
        if (btnToggleNewTenant) {
            btnToggleNewTenant.addEventListener('click', () => {
                toggleNewTenantInput();
            });
        }

        // Auto-fill button
        if (btnAutofill) {
            btnAutofill.addEventListener('click', (e) => {
                e.preventDefault();
                autofillWithAi();
            });
        }

        // Submit button
        if (btnSubmit) {
            btnSubmit.addEventListener('click', (e) => {
                e.preventDefault();
                submitIngestForm();
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
            const file = e.dataTransfer.files[0];
            if (file.name.toLowerCase().endsWith('.pdf') || file.type === 'application/pdf') {
                openIngestStation(file);
            } else {
                if (typeof showToast === 'function') {
                    showToast('Only PDF files are supported for ingestion.', 'error');
                } else {
                    alert('Only PDF files are supported for ingestion.');
                }
            }
        }
    }

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

        // Auto-populate Title if empty
        if (titleInput && !titleInput.value.trim()) {
            const baseName = file.name.replace(/\.pdf$/i, '').replace(/[-_]/g, ' ');
            titleInput.value = baseName;
        }
    }

    function removeFile() {
        selectedFile = null;
        if (fileInput) fileInput.value = '';
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
        if (batchNotice) {
            if (isBatch) {
                batchNotice.classList.remove('hidden');
            } else {
                batchNotice.classList.add('hidden');
            }
        }
        if (submitText) {
            submitText.textContent = isBatch ? '⚡ Ingest Batch' : '⚡ Ingest Document';
        }
    }

    function populateAreas(targetArea = null) {
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
        populateHouses(areaSelect.value);
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

    async function populateTenants(areaName, houseName, targetTenantId = null) {
        if (!tenantSelect) return;
        tenantSelect.innerHTML = '<option value="">(Auto-detect or Select Tenant)</option>';

        if (!areaName || !houseName) return;

        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(areaName)}/houses/${encodeURIComponent(houseName)}/tenants`);
            if (res.ok) {
                const tenants = await res.json();
                if (Array.isArray(tenants)) {
                    tenants.forEach(t => {
                        const opt = document.createElement('option');
                        opt.value = t.id;
                        const yearHint = t.start_date ? ` (${t.start_date.substring(0, 4)})` : '';
                        opt.textContent = `${t.name}${yearHint}`;
                        tenantSelect.appendChild(opt);
                    });
                }
            }
        } catch (err) {
            // Fallback: check tree node children
            const tree = (typeof globalTreeData !== 'undefined' ? globalTreeData : window.globalTreeData) || [];
            const areaNode = tree.find(a => a.name === areaName);
            const houseNode = areaNode?.children?.find(h => h.name === houseName);
            if (houseNode && Array.isArray(houseNode.children)) {
                houseNode.children.forEach(tNode => {
                    const opt = document.createElement('option');
                    opt.value = tNode.name;
                    opt.textContent = tNode.name;
                    tenantSelect.appendChild(opt);
                });
            }
        }

        if (targetTenantId) {
            tenantSelect.value = targetTenantId;
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

    function openIngestStation(initialFile = null) {
        if (!ingestModal) return;
        ingestModal.classList.remove('hidden');
        resetStatusMsg();

        const activeArea = getCurrentArea();
        const activeHouse = getCurrentHouse();
        populateAreas(activeArea);
        if (activeHouse) {
            populateHouses(activeArea, activeHouse);
        }

        if (initialFile) {
            handleFileSelected(initialFile);
        }
    }

    function closeIngestStation() {
        if (!ingestModal) return;
        ingestModal.classList.add('hidden');
        resetIngestForm();
    }

    function resetIngestForm() {
        removeFile();
        if (titleInput) titleInput.value = '';
        if (dateInput) dateInput.value = '';
        if (notesInput) notesInput.value = '';
        if (newTenantInput) newTenantInput.value = '';
        if (newTenantContainer) newTenantContainer.classList.add('hidden');
        if (btnToggleNewTenant) btnToggleNewTenant.textContent = '+ Add New Tenant';
        if (categorySelect) categorySelect.value = '13 - رسائل متنوعة';
        if (modeSingle) modeSingle.checked = true;
        if (modeBatch) modeBatch.checked = false;
        if (batchNotice) batchNotice.classList.add('hidden');
        if (submitText) submitText.textContent = '⚡ Ingest Document';
        resetStatusMsg();
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

    async function autofillWithAi() {
        if (isAutofilling) return;
        if (!selectedFile) {
            showStatusMsg('Please select or drop a PDF file first.', true);
            return;
        }

        isAutofilling = true;
        if (btnAutofill) btnAutofill.disabled = true;
        if (autofillSpinner) autofillSpinner.classList.remove('hidden');
        if (autofillText) autofillText.textContent = 'Analyzing...';
        resetStatusMsg();

        const formData = new FormData();
        formData.append('file', selectedFile);
        if (areaSelect && areaSelect.value) formData.append('area_id', areaSelect.value);
        if (houseSelect && houseSelect.value) formData.append('house_id', houseSelect.value);

        try {
            const res = await fetch('/api/ingest/preview-ai', {
                method: 'POST',
                body: formData,
            });

            if (res.ok) {
                const data = await res.json();
                
                if (data.suggested_title && titleInput) {
                    titleInput.value = data.suggested_title;
                }
                if (data.suggested_category && categorySelect) {
                    const matched = findMatchingCategory(data.suggested_category);
                    if (matched) categorySelect.value = matched;
                }
                if (data.suggested_date && dateInput) {
                    dateInput.value = data.suggested_date;
                }
                if (data.suggested_tenant_name) {
                    let matchedTenant = false;
                    if (tenantSelect) {
                        for (const opt of tenantSelect.options) {
                            if (opt.text.toLowerCase().includes(data.suggested_tenant_name.toLowerCase())) {
                                tenantSelect.value = opt.value;
                                matchedTenant = true;
                                break;
                            }
                        }
                    }
                    if (!matchedTenant) {
                        toggleNewTenantInput(true);
                        if (newTenantInput) newTenantInput.value = data.suggested_tenant_name;
                    }
                }
                if (data.suggested_area_id && areaSelect && !areaSelect.value) {
                    areaSelect.value = data.suggested_area_id;
                    populateHouses(data.suggested_area_id);
                }
                if (data.suggested_house_id && houseSelect && !houseSelect.value) {
                    houseSelect.value = data.suggested_house_id;
                    populateTenants(areaSelect ? areaSelect.value : '', data.suggested_house_id);
                }

                showStatusMsg('✨ AI metadata suggestions applied successfully!', false);
            } else {
                const err = await res.json().catch(() => ({}));
                showStatusMsg(err.detail || 'AI auto-fill could not analyze document.', true);
            }
        } catch (err) {
            console.error('AI preview failed:', err);
            showStatusMsg('Error connecting to AI preview service.', true);
        } finally {
            isAutofilling = false;
            if (btnAutofill) btnAutofill.disabled = false;
            if (autofillSpinner) autofillSpinner.classList.add('hidden');
            if (autofillText) autofillText.textContent = '✨ Auto-Fill with AI';
        }
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

        const isBatch = modeBatch && modeBatch.checked;
        const mode = isBatch ? 'auto_split' : 'manual';

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('mode', mode);
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

        // Single document metadata
        if (!isBatch) {
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

                // Immediate UI refresh
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
            if (submitText) submitText.textContent = isBatch ? '⚡ Ingest Batch' : '⚡ Ingest Document';
        }
    }

    // Expose globals
    window.initIngestStation = initIngestStation;
    window.openIngestStation = openIngestStation;
    window.closeIngestStation = closeIngestStation;
    window.handleFileSelected = handleFileSelected;
    window.removeFile = removeFile;
    window.autofillWithAi = autofillWithAi;
    window.submitIngestForm = submitIngestForm;
    window.formatFileSize = formatFileSize;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            initIngestStation,
            openIngestStation,
            closeIngestStation,
            handleFileSelected,
            removeFile,
            autofillWithAi,
            submitIngestForm,
            formatFileSize,
            populateAreas,
            populateHouses,
            populateTenants,
            updateModeUI,
        };
    }
})();
