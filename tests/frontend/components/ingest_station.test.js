import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
const {
    initIngestStation,
    openIngestStation,
    closeIngestStation,
    switchTab,
    getActiveTab,
    getCurrentTab,
    handleFileSelected,
    handleBroadcastFileSelected,
    handleFilesSelected,
    removeFile,
    removeBroadcastFile,
    submitSingleIngest,
    submitBroadcastIngest,
    submitHouseBatchIngest,
    submitIngestForm,
    formatFileSize,
    getTodayIsoDate,
    resetIngestForm,
    detectHouseFromFilename,
    getTenantsForHouse,
    resolveLatestTenant,
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
    getHouseBatchQueue,
    handleDirectHouseDrop,
    handleDirectCategoryDrop,
    resetDragCounter,
    // Backward compatibility
    updateModeUI,
    submitBatchIngest,
    getBatchQueue,
    addFilesToBatch,
    renderBatchQueue,
    populateBatchAreas,
} = require('../../../src/api/static/js/ingest-station.js');

function setupDOM() {
    document.body.innerHTML = `
        <header id="top-navbar">
            <button id="btn-ingest-trigger">+ Ingest <kbd>⌘I</kbd></button>
            <button id="btn-search-trigger">Search</button>
        </header>

        <div id="ingest-dropzone-overlay" class="hidden">
            <p id="ingest-dropzone-prompt">Drop PDF to Ingest Document</p>
        </div>

        <div id="ingest-station-modal" class="hidden">
            <div id="ingest-station-card">
                <button id="btn-ingest-close">Close</button>
                
                <!-- 3-Tab Segmented Navigation Bar -->
                <div class="grid grid-cols-3">
                    <button type="button" id="tab-mode-single" class="bg-blue-600 text-white shadow-2xs font-semibold">
                        <span>📄 Single Document</span>
                        <span>1 file → 1 house</span>
                    </button>
                    <button type="button" id="tab-mode-broadcast" class="text-slate-600 hover:text-slate-900 font-medium">
                        <span>📢 Broadcast Notice</span>
                        <span>1 file → Multiple houses</span>
                    </button>
                    <button type="button" id="tab-mode-housebatch" class="text-slate-600 hover:text-slate-900 font-medium">
                        <span>📁 House Batch</span>
                        <span>Multiple files → 1 house</span>
                    </button>
                </div>

                <!-- SECTION 1: Single Document -->
                <div id="section-mode-single">
                    <div id="ingest-file-dropzone">
                        <input id="ingest-file-input" type="file" accept=".pdf" />
                    </div>
                    <div id="ingest-file-info" class="hidden">
                        <p id="ingest-file-name"></p>
                        <p id="ingest-file-size"></p>
                        <button id="btn-remove-file">Change</button>
                    </div>
                    <div id="ingest-preview-container" class="hidden">
                        <iframe id="ingest-pdf-preview" src="about:blank"></iframe>
                    </div>

                    <select id="ingest-area-select">
                        <option value="">Select Area...</option>
                    </select>
                    <select id="ingest-house-select">
                        <option value="">Select House...</option>
                    </select>
                    <select id="ingest-tenant-select">
                        <option value="">(Auto-detect or Select Tenant)</option>
                    </select>
                    <button id="btn-toggle-new-tenant">+ Add New Tenant</button>
                    <div id="ingest-new-tenant-container" class="hidden">
                        <input id="ingest-new-tenant-input" type="text" />
                    </div>
                    <select id="ingest-category-select">
                        <option value="01 - بيانات أساسية">01 - بيانات أساسية</option>
                        <option value="05 - عقود">05 - عقود</option>
                        <option value="06 - كهرباء وماء">06 - كهرباء وماء</option>
                        <option value="13 - رسائل متنوعة" selected>13 - رسائل متنوعة</option>
                    </select>
                    <input id="ingest-title-input" type="text" />
                    <input id="ingest-date-input" type="date" />
                    <textarea id="ingest-notes-input"></textarea>
                </div>

                <!-- SECTION 2: Broadcast Notice -->
                <div id="section-mode-broadcast" class="hidden">
                    <div id="broadcast-dropzone">
                        <input id="broadcast-file-input" type="file" accept=".pdf" />
                    </div>
                    <div id="broadcast-file-info" class="hidden">
                        <p id="broadcast-file-name"></p>
                        <p id="broadcast-file-size"></p>
                        <button id="btn-broadcast-remove-file">Change</button>
                    </div>
                    <div id="broadcast-preview-container" class="hidden">
                        <iframe id="broadcast-pdf-preview" src="about:blank"></iframe>
                    </div>
                    <select id="broadcast-category-select">
                        <option value="09 - إشعارات" selected>09 - إشعارات</option>
                        <option value="13 - رسائل متنوعة">13 - رسائل متنوعة</option>
                    </select>
                    <input id="broadcast-title-input" type="text" />
                    <input id="broadcast-date-input" type="date" />
                    <select id="broadcast-area-select">
                        <option value="">Select Area...</option>
                    </select>
                    <button id="btn-broadcast-select-all">Select All</button>
                    <button id="btn-broadcast-deselect-all">Deselect All</button>
                    <span id="broadcast-selected-count">0 houses selected</span>
                    <input id="broadcast-house-search" type="text" placeholder="Search house # or tenant..." />
                    <div id="broadcast-houses-list"></div>
                </div>

                <!-- SECTION 3: House Batch -->
                <div id="section-mode-housebatch" class="hidden">
                    <select id="housebatch-area-select">
                        <option value="">Select Area...</option>
                    </select>
                    <select id="housebatch-house-select">
                        <option value="">Select House...</option>
                    </select>
                    <select id="housebatch-tenant-select">
                        <option value="">(Auto-detect or Select Tenant)</option>
                    </select>
                    <select id="housebatch-category-select">
                        <option value="06 - كهرباء وماء" selected>06 - كهرباء وماء</option>
                        <option value="13 - رسائل متنوعة">13 - رسائل متنوعة</option>
                    </select>
                    <input id="housebatch-date-select" type="date" />
                    <span id="housebatch-count-badge">0 files</span>
                    <button id="btn-housebatch-add-more">+ Add More Files</button>
                    <input id="housebatch-file-input" type="file" accept=".pdf" multiple class="hidden" />
                    <div id="housebatch-dropzone"></div>
                    <div id="housebatch-files-list"></div>
                </div>

                <!-- Status & Progress -->
                <div id="ingest-status-msg" class="hidden"></div>
                <div id="ingest-batch-progress" class="hidden">
                    <span id="ingest-batch-progress-text"></span>
                    <span id="ingest-batch-progress-pct"></span>
                    <div id="ingest-batch-progress-bar"></div>
                </div>

                <!-- Footer (No AI button) -->
                <button id="btn-ingest-cancel">Cancel</button>
                <button id="btn-ingest-submit">
                    <span id="ingest-submit-spinner" class="hidden"></span>
                    <span id="ingest-submit-text">⚡ Ingest Document</span>
                </button>
            </div>
        </div>
    `;
}

describe('Ingest Station Component', () => {
    beforeEach(() => {
        setupDOM();
        window.currentArea = null;
        window.currentHouse = null;
        window.currentTenant = null;
        window.globalTreeData = [
            {
                name: 'Area 1',
                children: [
                    { name: '501', id: '501', children: [{ id: 101, name: 'Tenant A' }] },
                    { name: '502', id: '502', children: [{ id: 102, name: 'Tenant B' }] },
                ],
            },
            {
                name: 'Area 2',
                children: [
                    { name: '601', id: '601', children: [] },
                ],
            },
        ];
        // Mock URL.createObjectURL
        window.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
        window.URL.revokeObjectURL = vi.fn();
        initIngestStation();
    });

    afterEach(() => {
        vi.restoreAllMocks();
        document.body.innerHTML = '';
    });

    it('formats file sizes accurately', () => {
        expect(formatFileSize(0)).toBe('0 B');
        expect(formatFileSize(500)).toBe('500 B');
        expect(formatFileSize(2048)).toBe('2.0 KB');
        expect(formatFileSize(1048576)).toBe('1.00 MB');
    });

    it('opens modal on navbar trigger button click', () => {
        const trigger = document.getElementById('btn-ingest-trigger');
        const modal = document.getElementById('ingest-station-modal');

        expect(modal.classList.contains('hidden')).toBe(true);
        trigger.click();
        expect(modal.classList.contains('hidden')).toBe(false);
    });

    it('closes modal on close button and cancel button click', () => {
        const trigger = document.getElementById('btn-ingest-trigger');
        const modal = document.getElementById('ingest-station-modal');
        const closeBtn = document.getElementById('btn-ingest-close');
        const cancelBtn = document.getElementById('btn-ingest-cancel');

        trigger.click();
        expect(modal.classList.contains('hidden')).toBe(false);

        closeBtn.click();
        expect(modal.classList.contains('hidden')).toBe(true);

        trigger.click();
        expect(modal.classList.contains('hidden')).toBe(false);

        cancelBtn.click();
        expect(modal.classList.contains('hidden')).toBe(true);
    });

    it('toggles modal on Cmd+I and Ctrl+I shortcuts, and closes on Escape', () => {
        const modal = document.getElementById('ingest-station-modal');

        // Cmd+I to open
        document.dispatchEvent(new KeyboardEvent('keydown', { key: 'i', metaKey: true }));
        expect(modal.classList.contains('hidden')).toBe(false);

        // Cmd+I to close
        document.dispatchEvent(new KeyboardEvent('keydown', { key: 'i', metaKey: true }));
        expect(modal.classList.contains('hidden')).toBe(true);

        // Ctrl+I to open
        document.dispatchEvent(new KeyboardEvent('keydown', { key: 'i', ctrlKey: true }));
        expect(modal.classList.contains('hidden')).toBe(false);

        // Escape to close
        document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
        expect(modal.classList.contains('hidden')).toBe(true);
    });

    it('switches between Single Document, Broadcast Notice, and House Batch tabs', () => {
        const tabSingle = document.getElementById('tab-mode-single');
        const tabBroadcast = document.getElementById('tab-mode-broadcast');
        const tabHousebatch = document.getElementById('tab-mode-housebatch');

        const sectionSingle = document.getElementById('section-mode-single');
        const sectionBroadcast = document.getElementById('section-mode-broadcast');
        const sectionHousebatch = document.getElementById('section-mode-housebatch');
        const submitText = document.getElementById('ingest-submit-text');

        // Initial default: Single Document
        expect(getActiveTab()).toBe('single');
        expect(sectionSingle.classList.contains('hidden')).toBe(false);
        expect(sectionBroadcast.classList.contains('hidden')).toBe(true);
        expect(sectionHousebatch.classList.contains('hidden')).toBe(true);
        expect(submitText.textContent).toBe('⚡ Ingest Document');

        // Switch to Broadcast Notice
        tabBroadcast.click();
        expect(getActiveTab()).toBe('broadcast');
        expect(sectionSingle.classList.contains('hidden')).toBe(true);
        expect(sectionBroadcast.classList.contains('hidden')).toBe(false);
        expect(sectionHousebatch.classList.contains('hidden')).toBe(true);
        expect(submitText.textContent).toBe('⚡ Broadcast to 0 Houses');

        // Switch to House Batch
        tabHousebatch.click();
        expect(getActiveTab()).toBe('housebatch');
        expect(sectionSingle.classList.contains('hidden')).toBe(true);
        expect(sectionBroadcast.classList.contains('hidden')).toBe(true);
        expect(sectionHousebatch.classList.contains('hidden')).toBe(false);
        expect(submitText.textContent).toBe('⚡ Ingest 0 Documents');

        // Switch back to Single Document
        tabSingle.click();
        expect(getActiveTab()).toBe('single');
        expect(sectionSingle.classList.contains('hidden')).toBe(false);
        expect(sectionBroadcast.classList.contains('hidden')).toBe(true);
        expect(sectionHousebatch.classList.contains('hidden')).toBe(true);
        expect(submitText.textContent).toBe('⚡ Ingest Document');
    });

    it('populates Area and House selects based on active context and handles dropdown changes in Single mode', () => {
        window.currentArea = 'Area 1';
        window.currentHouse = '502';

        openIngestStation();

        const areaSelect = document.getElementById('ingest-area-select');
        const houseSelect = document.getElementById('ingest-house-select');

        expect(areaSelect.value).toBe('Area 1');
        expect(houseSelect.value).toBe('502');

        // Change area to Area 2
        areaSelect.value = 'Area 2';
        areaSelect.dispatchEvent(new Event('change'));

        expect(houseSelect.options.length).toBeGreaterThan(1);
        expect(houseSelect.options[1].value).toBe('601');
    });

    it('toggles Add New Tenant input field in Single mode', () => {
        const toggleBtn = document.getElementById('btn-toggle-new-tenant');
        const container = document.getElementById('ingest-new-tenant-container');

        expect(container.classList.contains('hidden')).toBe(true);

        toggleBtn.click();
        expect(container.classList.contains('hidden')).toBe(false);
        expect(toggleBtn.textContent).toContain('Cancel');

        toggleBtn.click();
        expect(container.classList.contains('hidden')).toBe(true);
        expect(toggleBtn.textContent).toContain('+ Add New Tenant');
    });

    it('handles global drag and drop overlay and contextual prompt', () => {
        const overlay = document.getElementById('ingest-dropzone-overlay');
        const prompt = document.getElementById('ingest-dropzone-prompt');

        window.currentArea = 'Zone North';
        window.currentHouse = 'Villa 42';

        // Dragenter with Files
        const dragEvent = new Event('dragenter');
        dragEvent.dataTransfer = { types: ['Files'] };
        window.dispatchEvent(dragEvent);

        expect(overlay.classList.contains('hidden')).toBe(false);
        expect(prompt.textContent).toBe('Drop PDF to Ingest into Zone North / Villa 42');

        // Dragleave
        const leaveEvent = new Event('dragleave');
        window.dispatchEvent(leaveEvent);
        expect(overlay.classList.contains('hidden')).toBe(true);
    });

    it('attaches dropped PDF file and previews it in Single mode', () => {
        const modal = document.getElementById('ingest-station-modal');
        const fileInfo = document.getElementById('ingest-file-info');
        const fileName = document.getElementById('ingest-file-name');
        const titleInput = document.getElementById('ingest-title-input');
        const pdfPreview = document.getElementById('ingest-pdf-preview');

        const mockFile = new File(['%PDF-1.4 content'], 'lease_agreement.pdf', { type: 'application/pdf' });

        const dropEvent = new Event('drop');
        dropEvent.dataTransfer = { files: [mockFile] };
        window.dispatchEvent(dropEvent);

        expect(modal.classList.contains('hidden')).toBe(false);
        expect(fileInfo.classList.contains('hidden')).toBe(false);
        expect(fileName.textContent).toBe('lease_agreement.pdf');
        expect(titleInput.value).toBe('lease agreement');
        expect(pdfPreview.src).toContain('blob:mock-url');
    });

    it('removes selected file when Change button is clicked and clears title input in Single mode', () => {
        const mockFile = new File(['%PDF-1.4 content'], 'receipt.pdf', { type: 'application/pdf' });
        handleFileSelected(mockFile);

        const fileInfo = document.getElementById('ingest-file-info');
        const dropzone = document.getElementById('ingest-file-dropzone');
        const btnRemove = document.getElementById('btn-remove-file');
        const titleInput = document.getElementById('ingest-title-input');

        expect(fileInfo.classList.contains('hidden')).toBe(false);
        expect(dropzone.classList.contains('hidden')).toBe(true);
        expect(titleInput.value).toBe('receipt');

        btnRemove.click();

        expect(fileInfo.classList.contains('hidden')).toBe(true);
        expect(dropzone.classList.contains('hidden')).toBe(false);
        expect(titleInput.value).toBe('');
        expect(window.URL.revokeObjectURL).toHaveBeenCalled();
    });

    it('auto-fills document title from imported PDF filename', () => {
        const titleInput = document.getElementById('ingest-title-input');

        const mockFile = new File(['%PDF-1.4 content'], 'contract_2024.pdf', { type: 'application/pdf' });
        handleFileSelected(mockFile);

        expect(titleInput.value).toBe('contract 2024');

        const complexFile = new File(['%PDF-1.4 content'], 'lease--agreement__v2-final.PDF', { type: 'application/pdf' });
        handleFileSelected(complexFile);

        expect(titleInput.value).toBe('lease agreement v2 final');
    });

    it('replaces the title input with the new file base name unconditionally when a new PDF is selected', () => {
        const titleInput = document.getElementById('ingest-title-input');

        const file1 = new File(['%PDF-1.4 content'], 'old_contract.pdf', { type: 'application/pdf' });
        handleFileSelected(file1);
        expect(titleInput.value).toBe('old contract');

        // User edits the title
        titleInput.value = 'User Edited Contract';

        // Selecting a new file replaces the title unconditionally
        const file2 = new File(['%PDF-1.4 content'], 'new_agreement_2025.pdf', { type: 'application/pdf' });
        handleFileSelected(file2);
        expect(titleInput.value).toBe('new agreement 2025');
    });

    it('clears title input when removeFile is called directly', () => {
        const titleInput = document.getElementById('ingest-title-input');
        const mockFile = new File(['%PDF-1.4 content'], 'test_document.pdf', { type: 'application/pdf' });

        handleFileSelected(mockFile);
        expect(titleInput.value).toBe('test document');

        removeFile();
        expect(titleInput.value).toBe('');
    });

    it('verifies that AI autofill button #btn-ingest-autofill does NOT exist in the DOM', () => {
        const btnAutofill = document.getElementById('btn-ingest-autofill');
        expect(btnAutofill).toBeNull();
    });

    it('handles multi-file selection and automatically switches to House Batch mode', () => {
        const file1 = new File(['%PDF-1.4 content'], 'bill_501.pdf', { type: 'application/pdf' });
        const file2 = new File(['%PDF-1.4 content'], 'contract_502.pdf', { type: 'application/pdf' });

        handleFilesSelected([file1, file2]);

        expect(getActiveTab()).toBe('housebatch');
        expect(getHouseBatchQueue().length).toBe(2);
        const countBadge = document.getElementById('housebatch-count-badge');
        expect(countBadge.textContent).toBe('2 files');
        const submitText = document.getElementById('ingest-submit-text');
        expect(submitText.textContent).toBe('⚡ Ingest 2 Documents');
    });

    it('auto-fills editable titles and renders file list in house batch queue', () => {
        window.currentArea = 'Area 1';
        openIngestStation();
        switchTab('housebatch');

        const file1 = new File(['%PDF-1.4 content'], 'electricity-bill_501.pdf', { type: 'application/pdf' });
        const file2 = new File(['%PDF-1.4 content'], 'maintenance__502_final.pdf', { type: 'application/pdf' });

        addFilesToHouseBatch([file1, file2]);

        const queue = getHouseBatchQueue();
        expect(queue[0].title).toBe('electricity bill 501');
        expect(queue[1].title).toBe('maintenance 502 final');

        // User edits title
        const titleInputs = document.querySelectorAll('.housebatch-title-input');
        expect(titleInputs.length).toBe(2);
        titleInputs[0].value = 'Custom Electricity Title';
        titleInputs[0].dispatchEvent(new Event('input'));
        expect(queue[0].title).toBe('Custom Electricity Title');
    });

    it('removes individual files from the house batch queue', () => {
        window.currentArea = 'Area 1';
        openIngestStation();
        switchTab('housebatch');

        const file1 = new File(['%PDF-1.4 content'], 'notice_501.pdf', { type: 'application/pdf' });
        const file2 = new File(['%PDF-1.4 content'], 'notice_502.pdf', { type: 'application/pdf' });
        addFilesToHouseBatch([file1, file2]);

        expect(getHouseBatchQueue().length).toBe(2);

        // Remove first file
        const removeFileBtns = document.querySelectorAll('.btn-remove-housebatch-file');
        expect(removeFileBtns.length).toBe(2);
        removeFileBtns[0].click();

        expect(getHouseBatchQueue().length).toBe(1);
        expect(getHouseBatchQueue()[0].name).toBe('notice_502.pdf');
    });

    it('submits house batch ingestion of multiple documents to 1 house via POST /api/ingest', async () => {
        window.currentArea = 'Area 1';
        window.currentHouse = '501';
        openIngestStation();
        switchTab('housebatch');

        const houseSelect = document.getElementById('housebatch-house-select');
        houseSelect.value = '501';

        const file1 = new File(['%PDF-1.4 content'], 'bill_501.pdf', { type: 'application/pdf' });
        const file2 = new File(['%PDF-1.4 content'], 'contract_501.pdf', { type: 'application/pdf' });
        addFilesToHouseBatch([file1, file2]);

        const modal = document.getElementById('ingest-station-modal');
        window.refreshCurrentTab = vi.fn();
        window.loadTree = vi.fn();
        window.showToast = vi.fn();
        global.showToast = window.showToast;

        const calls = [];
        global.fetch = vi.fn().mockImplementation((url, opts) => {
            if (url === '/api/ingest') {
                calls.push(opts);
                return Promise.resolve({
                    ok: true,
                    json: async () => ({ status: 'success', vault_id: 'v_batch_123' }),
                });
            }
            return Promise.resolve({ ok: true, json: async () => [] });
        });

        await submitHouseBatchIngest();

        expect(calls.length).toBe(2);
        expect(calls[0].body.get('house_id')).toBe('501');
        expect(calls[0].body.get('arabic_title')).toBe('bill 501');
        expect(calls[0].body.get('mode')).toBe('manual');
        expect(calls[1].body.get('house_id')).toBe('501');
        expect(calls[1].body.get('arabic_title')).toBe('contract 501');
        expect(calls[1].body.get('mode')).toBe('manual');

        expect(modal.classList.contains('hidden')).toBe(true);
        expect(global.showToast).toHaveBeenCalledWith(
            'Successfully ingested 2 documents',
            'success'
        );
        expect(window.loadTree).toHaveBeenCalled();
    });

    it('populates houses checklist in Broadcast Notice and handles Select All and Deselect All', async () => {
        global.fetch = vi.fn().mockImplementation((url) => {
            if (url.includes('/api/areas/Area%201/houses/501/tenants')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => [{ id: 101, name: 'Tenant A', start_date: '2023-01-01', end_date: null }],
                });
            }
            if (url.includes('/api/areas/Area%201/houses/502/tenants')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => [{ id: 102, name: 'Tenant B', start_date: '2023-01-01', end_date: null }],
                });
            }
            return Promise.resolve({ ok: true, json: async () => [] });
        });

        window.currentArea = 'Area 1';
        openIngestStation();
        switchTab('broadcast');

        await populateBroadcastHouses('Area 1');

        const checklist = document.getElementById('broadcast-houses-list');
        const checkboxes = checklist.querySelectorAll('.broadcast-house-checkbox');
        expect(checkboxes.length).toBe(2);

        // Select All
        const btnSelectAll = document.getElementById('btn-broadcast-select-all');
        btnSelectAll.click();
        expect(getSelectedBroadcastHouses().length).toBe(2);
        const submitText = document.getElementById('ingest-submit-text');
        expect(submitText.textContent).toBe('⚡ Broadcast to 2 Houses');

        // Deselect All
        const btnDeselectAll = document.getElementById('btn-broadcast-deselect-all');
        btnDeselectAll.click();
        expect(getSelectedBroadcastHouses().length).toBe(0);
        expect(submitText.textContent).toBe('⚡ Broadcast to 0 Houses');
    });

    it('filters broadcast houses with search input', async () => {
        window.currentArea = 'Area 1';
        openIngestStation();
        switchTab('broadcast');

        await populateBroadcastHouses('Area 1');

        const searchInput = document.getElementById('broadcast-house-search');
        searchInput.value = '501';
        filterBroadcastHouses('501');

        const items = document.querySelectorAll('.broadcast-house-item');
        expect(items.length).toBe(2);
        expect(items[0].classList.contains('hidden')).toBe(false);
        expect(items[1].classList.contains('hidden')).toBe(true);
    });

    it('submits broadcast notice to multiple houses via POST /api/ingest', async () => {
        global.fetch = vi.fn().mockImplementation((url, opts) => {
            if (url === '/api/ingest') {
                return Promise.resolve({
                    ok: true,
                    json: async () => ({ status: 'success', vault_id: 'v_bc_1' }),
                });
            }
            return Promise.resolve({ ok: true, json: async () => [] });
        });

        window.currentArea = 'Area 1';
        openIngestStation();
        switchTab('broadcast');

        const areaSelect = document.getElementById('broadcast-area-select');
        areaSelect.value = 'Area 1';

        await populateBroadcastHouses('Area 1');
        selectAllBroadcastHouses(true);

        const noticeFile = new File(['%PDF-1.4 circular'], 'circular_notice.pdf', { type: 'application/pdf' });
        handleBroadcastFileSelected(noticeFile);

        const modal = document.getElementById('ingest-station-modal');
        window.showToast = vi.fn();
        global.showToast = window.showToast;
        window.loadTree = vi.fn();

        await submitBroadcastIngest();

        expect(modal.classList.contains('hidden')).toBe(true);
        expect(global.showToast).toHaveBeenCalledWith(
            'Successfully broadcasted to 2 houses',
            'success'
        );
    });

    it('handles direct drag-and-drop on a house card (handleDirectHouseDrop)', async () => {
        const calls = [];
        global.fetch = vi.fn().mockImplementation((url, opts) => {
            if (url.includes('/api/areas/Area%201/houses/501/tenants')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => [{ id: 101, name: 'Tenant A', start_date: '2023-01-01', end_date: null }],
                });
            }
            if (url === '/api/ingest') {
                calls.push(opts);
                return Promise.resolve({
                    ok: true,
                    json: async () => ({ status: 'success', vault_id: 'v_direct_h' }),
                });
            }
            return Promise.resolve({ ok: true, json: async () => [] });
        });

        window.showToast = vi.fn();
        global.showToast = window.showToast;

        const file = new File(['%PDF-1.4 invoice'], 'invoice-jan-2026.pdf', { type: 'application/pdf' });
        await handleDirectHouseDrop([file], '501', 'Area 1');

        expect(calls.length).toBe(1);
        expect(calls[0].body.get('house_id')).toBe('501');
        expect(calls[0].body.get('category')).toBe('13 - رسائل متنوعة');
        expect(calls[0].body.get('arabic_title')).toBe('invoice jan 2026');
        expect(calls[0].body.get('tenant_id')).toBe('101');
        expect(global.showToast).toHaveBeenCalledWith(
            '⚡ Document "invoice jan 2026" filed into House 501!',
            'success'
        );
    });

    it('handles direct drag-and-drop on a category folder card (handleDirectCategoryDrop)', async () => {
        const calls = [];
        global.fetch = vi.fn().mockImplementation((url, opts) => {
            if (url.includes('/api/areas/Area%201/houses/501/tenants')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => [{ id: 101, name: 'Tenant A', start_date: '2023-01-01', end_date: null }],
                });
            }
            if (url === '/api/ingest') {
                calls.push(opts);
                return Promise.resolve({
                    ok: true,
                    json: async () => ({ status: 'success', vault_id: 'v_direct_c' }),
                });
            }
            return Promise.resolve({ ok: true, json: async () => [] });
        });

        window.showToast = vi.fn();
        global.showToast = window.showToast;

        const file = new File(['%PDF-1.4 lease'], 'official_contract_2026.pdf', { type: 'application/pdf' });
        await handleDirectCategoryDrop([file], '05 - عقود', '501', 'Area 1');

        expect(calls.length).toBe(1);
        expect(calls[0].body.get('house_id')).toBe('501');
        expect(calls[0].body.get('category')).toBe('05 - عقود');
        expect(calls[0].body.get('arabic_title')).toBe('official contract 2026');
        expect(calls[0].body.get('tenant_id')).toBe('101');
        expect(global.showToast).toHaveBeenCalledWith(
            '⚡ Document "official contract 2026" filed into 05 - عقود for House 501!',
            'success'
        );
    });

    it('defaults date inputs to today date (YYYY-MM-DD)', () => {
        openIngestStation();
        const dateInput = document.getElementById('ingest-date-input');
        const expectedDate = getTodayIsoDate();
        expect(dateInput.value).toBe(expectedDate);
    });

    it('allows the user to freely edit or clear the primary date in Single mode', () => {
        openIngestStation();
        const dateInput = document.getElementById('ingest-date-input');
        expect(dateInput.value).toBe(getTodayIsoDate());

        // User edits the date
        dateInput.value = '2023-11-20';
        dateInput.dispatchEvent(new Event('input', { bubbles: true }));
        dateInput.dispatchEvent(new Event('change', { bubbles: true }));
        expect(dateInput.value).toBe('2023-11-20');

        // User clears the date
        dateInput.value = '';
        dateInput.dispatchEvent(new Event('input', { bubbles: true }));
        dateInput.dispatchEvent(new Event('change', { bubbles: true }));
        expect(dateInput.value).toBe('');
    });

    it('validates required fields and submits single ingest form successfully', async () => {
        const modal = document.getElementById('ingest-station-modal');
        const statusMsg = document.getElementById('ingest-status-msg');

        // Validation without file
        await submitSingleIngest();
        expect(statusMsg.textContent).toContain('Please select or drop a PDF file');

        // Add file
        const mockFile = new File(['%PDF-1.4 content'], 'test.pdf', { type: 'application/pdf' });
        handleFileSelected(mockFile);

        // Validation without area/house
        await submitSingleIngest();
        expect(statusMsg.textContent).toContain('Please select both a Target Area and Target House');

        // Fill area and house
        populateAreas('Area 1');
        populateHouses('Area 1', '501');

        // Mock successful POST /api/ingest
        window.refreshCurrentTab = vi.fn();
        window.loadTree = vi.fn();
        window.showToast = vi.fn();
        global.showToast = window.showToast;

        global.fetch = vi.fn().mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                status: 'success',
                mode: 'manual',
                vault_id: 'v_test_999',
                message: 'Document successfully ingested.',
            }),
        });

        await submitSingleIngest();

        expect(modal.classList.contains('hidden')).toBe(true);
        expect(global.showToast).toHaveBeenCalledWith(
            expect.stringContaining('Vault ID: v_test_999'),
            'success'
        );
        expect(window.refreshCurrentTab).toHaveBeenCalledWith('Area 1', '501');
        expect(window.loadTree).toHaveBeenCalled();
    });

    it('deduplicates duplicate tenant IDs and normalized names in populateTenants', async () => {
        global.fetch = vi.fn().mockResolvedValueOnce({
            ok: true,
            json: async () => [
                { id: 101, name: 'Tenant Alpha', start_date: '2021-01-01' },
                { id: 101, name: 'Tenant Alpha Dup', start_date: '2021-01-01' },
                { id: 103, name: 'tenant alpha', start_date: '2022-01-01' },
                { id: 104, name: 'Tenant Gamma', start_date: '2023-01-01' },
            ],
        });

        await populateTenants('Area 1', '501');

        const tenantSelect = document.getElementById('ingest-tenant-select');
        const options = Array.from(tenantSelect.options).filter((opt) => opt.value !== '');
        expect(options.length).toBe(2);
        expect(options[0].value).toBe('101');
        expect(options[1].value).toBe('104');
    });

    it('selects latest active tenant by default when a house with tenants is populated', async () => {
        global.fetch = vi.fn().mockResolvedValueOnce({
            ok: true,
            json: async () => [
                { id: 101, name: 'Tenant Past', start_date: '2020-01-01', end_date: '2021-12-31' },
                { id: 102, name: 'Tenant Active Older', start_date: '2022-01-01', end_date: null },
                { id: 103, name: 'Tenant Active Latest', start_date: '2023-06-01', end_date: '' },
            ],
        });

        await populateTenants('Area 1', '501');

        const tenantSelect = document.getElementById('ingest-tenant-select');
        expect(tenantSelect.value).toBe('103');
    });
});
