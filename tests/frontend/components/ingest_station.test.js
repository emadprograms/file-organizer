import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
const {
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
    getBatchQueue,
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
                
                <!-- Mode Switcher -->
                <input type="radio" name="ingest_mode" id="ingest-mode-single" value="manual" checked />
                <input type="radio" name="ingest_mode" id="ingest-mode-batch" value="batch" />

                <!-- Single Container -->
                <div id="ingest-single-container">
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
                    <div id="ingest-status-msg" class="hidden"></div>
                </div>

                <!-- Batch Queue Container -->
                <div id="ingest-batch-queue-container" class="hidden">
                    <select id="ingest-batch-area-select">
                        <option value="">Select Area...</option>
                    </select>
                    <select id="ingest-batch-category-select">
                        <option value="06 - كهرباء وماء" selected>06 - كهرباء وماء</option>
                        <option value="13 - رسائل متنوعة">13 - رسائل متنوعة</option>
                    </select>
                    <input id="ingest-batch-date-select" type="date" />
                    <span id="ingest-batch-count-badge">0 files</span>
                    <button id="btn-batch-add-more">+ Add More Files</button>
                    <div id="ingest-batch-empty-dropzone"></div>
                    <div id="ingest-batch-files-list"></div>
                    <div id="ingest-batch-progress" class="hidden">
                        <span id="ingest-batch-progress-text"></span>
                        <span id="ingest-batch-progress-pct"></span>
                        <div id="ingest-batch-progress-bar"></div>
                    </div>
                    <div id="ingest-batch-notice" class="hidden"></div>
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
                    { name: '501', children: [{ name: 'Tenant A' }] },
                    { name: '502', children: [{ name: 'Tenant B' }] },
                ],
            },
            {
                name: 'Area 2',
                children: [
                    { name: '601', children: [] },
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

    it('toggles mode switcher between Single File and Batch Filing modes', () => {
        const modeSingle = document.getElementById('ingest-mode-single');
        const modeBatch = document.getElementById('ingest-mode-batch');
        const singleContainer = document.getElementById('ingest-single-container');
        const batchContainer = document.getElementById('ingest-batch-queue-container');
        const submitText = document.getElementById('ingest-submit-text');
        const fileInput = document.getElementById('ingest-file-input');

        expect(singleContainer.classList.contains('hidden')).toBe(false);
        expect(batchContainer.classList.contains('hidden')).toBe(true);
        expect(submitText.textContent).toBe('⚡ Ingest Document');
        expect(fileInput.multiple).toBe(false);

        modeBatch.checked = true;
        modeBatch.dispatchEvent(new Event('change'));

        expect(singleContainer.classList.contains('hidden')).toBe(true);
        expect(batchContainer.classList.contains('hidden')).toBe(false);
        expect(submitText.textContent).toBe('⚡ Ingest All (0 Files)');
        expect(fileInput.multiple).toBe(true);

        modeSingle.checked = true;
        modeSingle.dispatchEvent(new Event('change'));

        expect(singleContainer.classList.contains('hidden')).toBe(false);
        expect(batchContainer.classList.contains('hidden')).toBe(true);
        expect(submitText.textContent).toBe('⚡ Ingest Document');
        expect(fileInput.multiple).toBe(false);
    });

    it('populates Area and House selects based on active context and handles dropdown changes', () => {
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

    it('toggles Add New Tenant input field', () => {
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

    it('attaches dropped PDF file and previews it', () => {
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

    it('removes selected file when Change button is clicked and clears title input', () => {
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

    it('auto-fills document title from imported PDF filename (cleaning extension and underscores/hyphens)', () => {
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

    it('allows the user to edit the auto-filled title freely', () => {
        const titleInput = document.getElementById('ingest-title-input');

        const mockFile = new File(['%PDF-1.4 content'], 'draft_memo.pdf', { type: 'application/pdf' });
        handleFileSelected(mockFile);
        expect(titleInput.value).toBe('draft memo');

        // Simulate user typing a custom title
        titleInput.value = 'Official Final Memorandum';
        titleInput.dispatchEvent(new Event('input', { bubbles: true }));

        expect(titleInput.value).toBe('Official Final Memorandum');
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

    it('handles multi-file selection and automatically switches to Batch Filing mode', () => {
        const modeBatch = document.getElementById('ingest-mode-batch');
        const file1 = new File(['%PDF-1.4 content'], 'bill_501.pdf', { type: 'application/pdf' });
        const file2 = new File(['%PDF-1.4 content'], 'contract_502.pdf', { type: 'application/pdf' });

        handleFilesSelected([file1, file2]);

        expect(modeBatch.checked).toBe(true);
        expect(getBatchQueue().length).toBe(2);
        const countBadge = document.getElementById('ingest-batch-count-badge');
        expect(countBadge.textContent).toBe('2 files');
    });

    it('auto-fills editable titles and auto-detects house numbers from filenames in batch queue', () => {
        window.currentArea = 'Area 1';
        openIngestStation();

        const file1 = new File(['%PDF-1.4 content'], 'electricity-bill_501.pdf', { type: 'application/pdf' });
        const file2 = new File(['%PDF-1.4 content'], 'maintenance__502_final.pdf', { type: 'application/pdf' });

        handleFilesSelected([file1, file2]);

        const queue = getBatchQueue();
        expect(queue[0].title).toBe('electricity bill 501');
        expect(queue[0].targets[0].house).toBe('501');
        expect(queue[1].title).toBe('maintenance 502 final');
        expect(queue[1].targets[0].house).toBe('502');

        // User edits title
        const titleInputs = document.querySelectorAll('.batch-title-input');
        expect(titleInputs.length).toBe(2);
        titleInputs[0].value = 'Custom Electricity Title';
        titleInputs[0].dispatchEvent(new Event('input'));
        expect(queue[0].title).toBe('Custom Electricity Title');
    });

    it('auto-selects latest tenant for each detected house in batch queue', async () => {
        global.fetch = vi.fn().mockImplementation((url) => {
            if (url.includes('501')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => [
                        { id: 101, name: 'Tenant Past', start_date: '2020-01-01', end_date: '2021-01-01' },
                        { id: 102, name: 'Tenant Active 501', start_date: '2022-01-01', end_date: null },
                    ],
                });
            }
            if (url.includes('502')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => [
                        { id: 201, name: 'Tenant Past 502', start_date: '2019-01-01', end_date: '2020-01-01' },
                        { id: 202, name: 'Tenant Active 502', start_date: '2023-01-01', end_date: null },
                    ],
                });
            }
            return Promise.resolve({ ok: true, json: async () => [] });
        });

        window.currentArea = 'Area 1';
        openIngestStation();

        const file1 = new File(['%PDF-1.4 content'], 'doc_501.pdf', { type: 'application/pdf' });
        const file2 = new File(['%PDF-1.4 content'], 'doc_502.pdf', { type: 'application/pdf' });

        await addFilesToBatch([file1, file2]);

        const queue = getBatchQueue();
        expect(queue[0].targets[0].tenantId).toBe('102');
        expect(queue[1].targets[0].tenantId).toBe('202');
    });

    it('supports broadcasting a single document to multiple houses simultaneously', async () => {
        global.fetch = vi.fn().mockImplementation((url) => {
            if (url.includes('501')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => [{ id: 101, name: 'Tenant 501', start_date: '2023-01-01', end_date: null }],
                });
            }
            if (url.includes('502')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => [{ id: 201, name: 'Tenant 502', start_date: '2023-01-01', end_date: null }],
                });
            }
            return Promise.resolve({ ok: true, json: async () => [] });
        });

        window.currentArea = 'Area 1';
        const modeBatch = document.getElementById('ingest-mode-batch');
        modeBatch.checked = true;
        modeBatch.dispatchEvent(new Event('change'));

        const file = new File(['%PDF-1.4 content'], 'general_notice_circular.pdf', { type: 'application/pdf' });
        await addFilesToBatch([file]);

        const queue = getBatchQueue();
        expect(queue.length).toBe(1);
        expect(queue[0].targets.length).toBe(1);

        // Click + Add House on this document
        const btnAddHouse = document.querySelector('.btn-batch-add-house');
        expect(btnAddHouse).not.toBeNull();
        await btnAddHouse.click();

        expect(queue[0].targets.length).toBe(2);
        expect(queue[0].targets[0].house).toBe('501');
        expect(queue[0].targets[1].house).toBe('502');

        const submitText = document.getElementById('ingest-submit-text');
        expect(submitText.textContent).toBe('⚡ Ingest All (2 Files)');
    });

    it('removes individual files from the batch queue', async () => {
        window.currentArea = 'Area 1';
        openIngestStation();
        const modeBatch = document.getElementById('ingest-mode-batch');
        modeBatch.checked = true;
        modeBatch.dispatchEvent(new Event('change'));

        const file1 = new File(['%PDF-1.4 content'], 'notice_501.pdf', { type: 'application/pdf' });
        const file2 = new File(['%PDF-1.4 content'], 'notice_502.pdf', { type: 'application/pdf' });
        await addFilesToBatch([file1, file2]);

        expect(getBatchQueue().length).toBe(2);

        // Remove first file
        const removeFileBtns = document.querySelectorAll('.btn-remove-batch-file');
        expect(removeFileBtns.length).toBe(2);
        removeFileBtns[0].click();

        expect(getBatchQueue().length).toBe(1);
        expect(getBatchQueue()[0].name).toBe('notice_502.pdf');
    });

    it('submits batch ingestion of multiple documents across houses via POST /api/ingest', async () => {
        window.currentArea = 'Area 1';
        openIngestStation();
        const modeBatch = document.getElementById('ingest-mode-batch');
        modeBatch.checked = true;
        modeBatch.dispatchEvent(new Event('change'));

        const file1 = new File(['%PDF-1.4 content'], 'bill_501.pdf', { type: 'application/pdf' });
        const file2 = new File(['%PDF-1.4 content'], 'contract_502.pdf', { type: 'application/pdf' });
        await addFilesToBatch([file1, file2]);

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

        await submitBatchIngest();

        expect(calls.length).toBe(2);
        expect(calls[0].body.get('house_id')).toBe('501');
        expect(calls[0].body.get('arabic_title')).toBe('bill 501');
        expect(calls[0].body.get('mode')).toBe('manual');
        expect(calls[1].body.get('house_id')).toBe('502');
        expect(calls[1].body.get('arabic_title')).toBe('contract 502');
        expect(calls[1].body.get('mode')).toBe('manual');

        expect(modal.classList.contains('hidden')).toBe(true);
        expect(global.showToast).toHaveBeenCalledWith(
            'Successfully ingested 2 documents',
            'success'
        );
        expect(window.loadTree).toHaveBeenCalled();
    });

    it('propagates shared category and shared primary date across all batch ingest tasks', async () => {
        window.currentArea = 'Area 1';
        openIngestStation();
        const modeBatch = document.getElementById('ingest-mode-batch');
        modeBatch.checked = true;
        modeBatch.dispatchEvent(new Event('change'));

        const categorySelect = document.getElementById('ingest-batch-category-select');
        categorySelect.value = '06 - كهرباء وماء';
        const dateInput = document.getElementById('ingest-batch-date-select');
        dateInput.value = '2026-05-20';

        const file1 = new File(['%PDF-1.4 content'], 'bill_a.pdf', { type: 'application/pdf' });
        await addFilesToBatch([file1]);

        let sentCategory = null;
        let sentDate = null;
        global.fetch = vi.fn().mockImplementation((url, opts) => {
            if (url === '/api/ingest') {
                sentCategory = opts.body.get('category');
                sentDate = opts.body.get('primary_date');
                return Promise.resolve({
                    ok: true,
                    json: async () => ({ status: 'success', vault_id: 'v_batch_456' }),
                });
            }
            return Promise.resolve({ ok: true, json: async () => [] });
        });

        await submitBatchIngest();

        expect(sentCategory).toBe('06 - كهرباء وماء');
        expect(sentDate).toBe('2026-05-20');
    });

    it('displays live progress during batch ingestion and handles errors gracefully', async () => {
        window.currentArea = 'Area 1';
        openIngestStation();
        const modeBatch = document.getElementById('ingest-mode-batch');
        modeBatch.checked = true;
        modeBatch.dispatchEvent(new Event('change'));

        const file1 = new File(['%PDF-1.4 content'], 'file1.pdf', { type: 'application/pdf' });
        const file2 = new File(['%PDF-1.4 content'], 'file2.pdf', { type: 'application/pdf' });
        await addFilesToBatch([file1, file2]);

        const progressEl = document.getElementById('ingest-batch-progress');
        const progressText = document.getElementById('ingest-batch-progress-text');

        let callCount = 0;
        global.fetch = vi.fn().mockImplementation((url) => {
            if (url === '/api/ingest') {
                callCount++;
                expect(progressEl.classList.contains('hidden')).toBe(false);
                if (callCount === 1) {
                    expect(progressText.textContent).toContain('Ingesting 1 of 2');
                    return Promise.resolve({ ok: true, json: async () => ({ status: 'success' }) });
                } else {
                    expect(progressText.textContent).toContain('Ingesting 2 of 2');
                    return Promise.resolve({ ok: false, json: async () => ({ detail: 'Disk full' }) });
                }
            }
            return Promise.resolve({ ok: true, json: async () => [] });
        });

        window.showToast = vi.fn();
        global.showToast = window.showToast;

        await submitBatchIngest();

        expect(global.showToast).toHaveBeenCalledWith(
            expect.stringContaining('1 failed'),
            'error'
        );
    });

    it('validates required fields and submits ingest form successfully', async () => {
        const modal = document.getElementById('ingest-station-modal');
        const statusMsg = document.getElementById('ingest-status-msg');

        // Validation without file
        await submitIngestForm();
        expect(statusMsg.textContent).toContain('Please select or drop a PDF file');

        // Add file
        const mockFile = new File(['%PDF-1.4 content'], 'test.pdf', { type: 'application/pdf' });
        handleFileSelected(mockFile);

        // Validation without area/house
        await submitIngestForm();
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

        await submitIngestForm();

        expect(modal.classList.contains('hidden')).toBe(true);
        expect(global.showToast).toHaveBeenCalledWith(
            expect.stringContaining('Vault ID: v_test_999'),
            'success'
        );
        expect(window.refreshCurrentTab).toHaveBeenCalledWith('Area 1', '501');
        expect(window.loadTree).toHaveBeenCalled();
    });

    it('does not duplicate tenants in ingest-tenant-select when openIngestStation is called', async () => {
        global.fetch = vi.fn().mockImplementation((url) => {
            if (url.includes('/api/areas/Area%201/houses/501/tenants')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => [
                        { id: 101, name: 'Tenant Alpha', start_date: '2021-01-01' },
                        { id: 102, name: 'Tenant Beta', start_date: '2023-01-01' },
                    ],
                });
            }
            return Promise.reject(new Error('not found'));
        });

        window.currentArea = 'Area 1';
        window.currentHouse = '501';

        openIngestStation();
        await new Promise((r) => setTimeout(r, 10));

        const tenantSelect = document.getElementById('ingest-tenant-select');
        const options = Array.from(tenantSelect.options);
        const alphaOptions = options.filter((opt) => opt.textContent.includes('Tenant Alpha'));
        const betaOptions = options.filter((opt) => opt.textContent.includes('Tenant Beta'));

        expect(alphaOptions.length).toBe(1);
        expect(betaOptions.length).toBe(1);
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

    it('ignores stale out-of-order responses in populateTenants', async () => {
        let resolveFirst;
        let resolveSecond;

        global.fetch = vi.fn().mockImplementation((url) => {
            if (url.includes('house_fast')) {
                return new Promise((res) => {
                    resolveSecond = () => res({
                        ok: true,
                        json: async () => [{ id: 201, name: 'Fast House Tenant' }],
                    });
                });
            } else {
                return new Promise((res) => {
                    resolveFirst = () => res({
                        ok: true,
                        json: async () => [{ id: 101, name: 'Slow House Tenant' }],
                    });
                });
            }
        });

        const p1 = populateTenants('Area 1', 'house_slow');
        const p2 = populateTenants('Area 1', 'house_fast');

        // Resolve second (faster) request first
        resolveSecond();
        await p2;

        const tenantSelect = document.getElementById('ingest-tenant-select');
        expect(tenantSelect.options.length).toBe(2);
        expect(tenantSelect.options[1].textContent).toContain('Fast House Tenant');

        // Resolve first (slow) request later
        resolveFirst();
        await p1;

        // Slow response should have been ignored
        expect(tenantSelect.options.length).toBe(2);
        expect(tenantSelect.options[1].textContent).toContain('Fast House Tenant');
    });

    it('handles concurrent populateTenants calls without duplicating tenant options', async () => {
        global.fetch = vi.fn().mockImplementation(() => Promise.resolve({
            ok: true,
            json: async () => [
                { id: 101, name: 'Tenant Alpha', start_date: '2021-01-01' },
                { id: 102, name: 'Tenant Beta', start_date: '2023-01-01' },
            ],
        }));

        await Promise.all([
            populateTenants('Area 1', '501'),
            populateTenants('Area 1', '501'),
        ]);

        const tenantSelect = document.getElementById('ingest-tenant-select');
        const options = Array.from(tenantSelect.options);
        const alphaOptions = options.filter((opt) => opt.textContent.includes('Tenant Alpha'));
        const betaOptions = options.filter((opt) => opt.textContent.includes('Tenant Beta'));

        expect(alphaOptions.length).toBe(1);
        expect(betaOptions.length).toBe(1);
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

        // Verify user can freely change selection to another tenant or back to empty
        tenantSelect.value = '101';
        expect(tenantSelect.value).toBe('101');
        tenantSelect.value = '';
        expect(tenantSelect.value).toBe('');
    });

    it('selects tenant with latest end_date or start_date when all tenants have ended', async () => {
        global.fetch = vi.fn().mockResolvedValueOnce({
            ok: true,
            json: async () => [
                { id: 201, name: 'Historical A', start_date: '2019-01-01', end_date: '2020-12-31' },
                { id: 202, name: 'Historical B', start_date: '2021-01-01', end_date: '2023-05-31' },
                { id: 203, name: 'Historical C', start_date: '2023-01-01', end_date: '2023-05-31' },
            ],
        });

        await populateTenants('Area 1', '501');

        const tenantSelect = document.getElementById('ingest-tenant-select');
        // Historical B and C both ended on 2023-05-31, but Historical C started later (2023-01-01 > 2021-01-01)
        expect(tenantSelect.value).toBe('203');
    });

    it('selects the last tenant in houseNode.children when using DOM fallback', async () => {
        global.fetch = vi.fn().mockRejectedValueOnce(new Error('Network failure'));

        window.globalTreeData = [
            {
                name: 'Area Fallback',
                children: [
                    {
                        name: 'House Fallback',
                        children: [
                            { name: 'First Tenant' },
                            { name: 'Last Tenant' },
                        ],
                    },
                ],
            },
        ];

        await populateTenants('Area Fallback', 'House Fallback');

        const tenantSelect = document.getElementById('ingest-tenant-select');
        expect(tenantSelect.value).toBe('Last Tenant');
    });

    it('selects the latest tenant of the newly selected house when switching between houses', async () => {
        global.fetch = vi.fn().mockImplementation((url) => {
            if (url.includes('house-a')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => [
                        { id: 10, name: 'House A Past', start_date: '2020-01-01', end_date: '2021-01-01' },
                        { id: 11, name: 'House A Active', start_date: '2021-02-01', end_date: null },
                    ],
                });
            }
            if (url.includes('house-b')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => [
                        { id: 20, name: 'House B Past', start_date: '2019-01-01', end_date: '2020-01-01' },
                        { id: 21, name: 'House B Active Latest', start_date: '2024-01-01', end_date: null },
                    ],
                });
            }
            return Promise.reject(new Error('Unknown url'));
        });

        const areaSelect = document.getElementById('ingest-area-select');
        const houseSelect = document.getElementById('ingest-house-select');
        const tenantSelect = document.getElementById('ingest-tenant-select');

        areaSelect.innerHTML = '<option value="Area 1">Area 1</option>';
        areaSelect.value = 'Area 1';
        houseSelect.innerHTML = `
            <option value="">Select House...</option>
            <option value="house-a">House A</option>
            <option value="house-b">House B</option>
        `;

        // Switch to house-a
        houseSelect.value = 'house-a';
        houseSelect.dispatchEvent(new Event('change'));
        await new Promise((r) => setTimeout(r, 10));

        expect(tenantSelect.value).toBe('11');

        // Switch to house-b
        houseSelect.value = 'house-b';
        houseSelect.dispatchEvent(new Event('change'));
        await new Promise((r) => setTimeout(r, 10));

        expect(tenantSelect.value).toBe('21');
    });

    it('respects targetTenantId when explicitly provided', async () => {
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => [
                { id: 101, name: 'Tenant Past', start_date: '2020-01-01', end_date: '2021-12-31' },
                { id: 102, name: 'Tenant Active 1', start_date: '2022-01-01', end_date: null },
                { id: 103, name: 'Tenant Active Latest', start_date: '2023-06-01', end_date: null },
            ],
        });

        // Explicit ID as integer
        await populateTenants('Area 1', '501', 101);
        const tenantSelect = document.getElementById('ingest-tenant-select');
        expect(tenantSelect.value).toBe('101');

        // Explicit ID as string
        await populateTenants('Area 1', '501', '102');
        expect(tenantSelect.value).toBe('102');
    });

    it('selects tenant matching window.currentTenant by name or ID when targetTenantId is not provided', async () => {
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => [
                { id: 101, name: 'Tenant Alpha', start_date: '2020-01-01', end_date: null },
                { id: 102, name: 'Tenant Beta', start_date: '2023-01-01', end_date: null },
            ],
        });

        const tenantSelect = document.getElementById('ingest-tenant-select');

        // Match by tenant name
        window.currentTenant = 'Tenant Alpha';
        await populateTenants('Area 1', '501');
        expect(tenantSelect.value).toBe('101');

        // Match by tenant ID
        window.currentTenant = '101';
        await populateTenants('Area 1', '501');
        expect(tenantSelect.value).toBe('101');
    });

    it("defaults #ingest-date-input to today's date (YYYY-MM-DD) on openIngestStation()", () => {
        const dateInput = document.getElementById('ingest-date-input');
        expect(dateInput.value).toBe('');

        openIngestStation();

        const today = new Date();
        const expectedDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        expect(dateInput.value).toBe(expectedDate);
        expect(dateInput.value).toBe(getTodayIsoDate());
    });

    it("keeps or resets #ingest-date-input to today's date when resetting the form or closing the modal", () => {
        openIngestStation();
        const dateInput = document.getElementById('ingest-date-input');
        const expectedDate = getTodayIsoDate();
        expect(dateInput.value).toBe(expectedDate);

        // User changes the date
        dateInput.value = '2021-04-10';
        expect(dateInput.value).toBe('2021-04-10');

        // Form reset resets date to today's date
        resetIngestForm();
        expect(dateInput.value).toBe(expectedDate);

        // User changes the date again and closes modal
        dateInput.value = '2022-08-15';
        closeIngestStation();
        expect(dateInput.value).toBe(expectedDate);
    });

    it("allows the user to freely edit or clear the primary date", () => {
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

});


