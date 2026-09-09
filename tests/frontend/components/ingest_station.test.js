import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
const {
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
                
                <!-- Left Column -->
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
                <input type="radio" name="ingest_mode" id="ingest-mode-single" value="manual" checked />
                <input type="radio" name="ingest_mode" id="ingest-mode-batch" value="auto_split" />
                <div id="ingest-batch-notice" class="hidden"></div>

                <!-- Right Column -->
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

                <!-- Footer -->
                <button id="btn-ingest-autofill">
                    <span id="ingest-autofill-spinner" class="hidden"></span>
                    <span id="ingest-autofill-text">✨ Auto-Fill with AI</span>
                </button>
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

    it('toggles mode switcher between Single Document and Multi-Document Batch', () => {
        const modeSingle = document.getElementById('ingest-mode-single');
        const modeBatch = document.getElementById('ingest-mode-batch');
        const batchNotice = document.getElementById('ingest-batch-notice');
        const submitText = document.getElementById('ingest-submit-text');

        modeBatch.checked = true;
        modeBatch.dispatchEvent(new Event('change'));

        expect(batchNotice.classList.contains('hidden')).toBe(false);
        expect(submitText.textContent).toBe('⚡ Ingest Batch');

        modeSingle.checked = true;
        modeSingle.dispatchEvent(new Event('change'));

        expect(batchNotice.classList.contains('hidden')).toBe(true);
        expect(submitText.textContent).toBe('⚡ Ingest Document');
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

    it('auto-fills metadata when ✨ Auto-Fill with AI is triggered', async () => {
        const mockFile = new File(['%PDF-1.4 content'], 'doc.pdf', { type: 'application/pdf' });
        handleFileSelected(mockFile);

        // Mock fetch for /api/ingest/preview-ai
        global.fetch = vi.fn().mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                status: 'success',
                page_count: 2,
                suggested_title: 'عقد إيجار سنوي',
                suggested_category: '05 - عقود',
                suggested_date: '2024-03-15',
                suggested_tenant_name: 'سالم الكعبي',
            }),
        });

        await autofillWithAi();

        const titleInput = document.getElementById('ingest-title-input');
        const categorySelect = document.getElementById('ingest-category-select');
        const dateInput = document.getElementById('ingest-date-input');
        const newTenantInput = document.getElementById('ingest-new-tenant-input');
        const statusMsg = document.getElementById('ingest-status-msg');

        expect(titleInput.value).toBe('عقد إيجار سنوي');
        expect(categorySelect.value).toBe('05 - عقود');
        expect(dateInput.value).toBe('2024-03-15');
        expect(newTenantInput.value).toBe('سالم الكعبي');
        expect(statusMsg.textContent).toContain('AI metadata suggestions applied');
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
});

