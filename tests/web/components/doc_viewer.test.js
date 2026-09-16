import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Document Viewer & Live Peek Header (Category Badge vs Tenant Select)', () => {
  const htmlContent = fs.readFileSync(
    path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/index.html'),
    'utf8'
  );

  let store = {};
  const localStorageMock = {
    getItem: vi.fn(key => (key in store ? store[key] : null)),
    setItem: vi.fn((key, val) => { store[key] = String(val); }),
    removeItem: vi.fn(key => { delete store[key]; }),
    clear: vi.fn(() => { store = {}; })
  };

  beforeEach(() => {
    store = {};
    vi.stubGlobal('localStorage', localStorageMock);
    document.body.innerHTML = `
      <div id="welcome-panel"></div>
      <div id="resizer-2" class="hidden"></div>
      <div id="document-viewer-panel" class="hidden">
        <div class="header">
          <div id="viewer-title">Document</div>
          <span id="viewer-peek-badge" class="hidden">Live Peek</span>
          <div id="viewer-category-badge" class="hidden">
            <span id="viewer-category-val"></span>
          </div>
          <button id="viewer-translate-btn"><span id="viewer-translate-label">English</span></button>
          <button id="viewer-mode-toggle"><span id="viewer-mode-label">Computer</span><svg id="viewer-mode-icon"></svg></button>
          <a id="viewer-download" href="#">Open</a>
        </div>
        <div class="viewport">
          <iframe id="pdf-frame" src="about:blank"></iframe>
          <div id="pdf-canvas-container" class="hidden"></div>
          <div id="document-translation-overlay" class="hidden"></div>
        </div>
      </div>
    `;

    global.Tesseract = {
      createWorker: vi.fn().mockResolvedValue({
        recognize: vi.fn().mockImplementation(async (canvas) => ({
          data: {
            lines: [
              {
                text: 'مكتب وكيل وزارة الداخلية',
                bbox: { x0: 100, y0: 40, x1: 500, y1: 75 },
                words: []
              },
              {
                text: 'أمر تخصيص مسكن',
                bbox: { x0: 150, y0: 90, x1: 450, y1: 125 },
                words: []
              }
            ]
          }
        })),
        terminate: vi.fn().mockResolvedValue()
      })
    };

    global.pdfjsLib = {
      GlobalWorkerOptions: {},
      getDocument: vi.fn().mockReturnValue({
        promise: Promise.resolve({
          numPages: 1,
          getPage: vi.fn().mockResolvedValue({
            getViewport: vi.fn().mockReturnValue({ width: 600, height: 800, scale: 1.0 }),
            render: vi.fn().mockReturnValue({ promise: Promise.resolve() }),
            getTextContent: vi.fn().mockResolvedValue({ items: [] })
          })
        })
      })
    };

    global.currentArea = 'Safra C';
    global.currentHouse = '101';
    global.getPdfUrl = (area, house, vaultId) => `/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/pdf/${encodeURIComponent(vaultId)}`;
    global.currentTimeline = [
      { vault_id: 'doc_1', title: 'عقد إيجار 101', category: '05 - عقود' }
    ];
    global.globalTreeData = [
      {
        name: 'Safra C',
        houses: [
          {
            house_number: '101',
            categories: [
              {
                name: '06 - كهرباء وماء',
                documents: [{ vault_id: 'doc_2', title: 'فاتورة ماء' }]
              }
            ]
          }
        ]
      }
    ];

    const scriptCode = fs.readFileSync(
      path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/doc-viewer.js'),
      'utf8'
    );
    eval(scriptCode);
  });

  afterEach(() => {
    document.body.innerHTML = '';
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('verifies index.html has removed viewer-tenant-select and added viewer-category-badge', () => {
    expect(htmlContent).not.toContain('id="viewer-tenant-select"');
    expect(htmlContent).not.toContain('id="viewer-tenant-label"');
    expect(htmlContent).toContain('id="viewer-category-badge"');
    expect(htmlContent).toContain('id="viewer-category-val"');
  });

  it('displays category badge and hides peek badge when openDocument is called with explicit category', () => {
    window.openDocument('doc_99', 'مستند اختباري', '03 - أمر تخصيص');

    const viewerPanel = document.getElementById('document-viewer-panel');
    const titleEl = document.getElementById('viewer-title');
    const peekBadge = document.getElementById('viewer-peek-badge');
    const catBadge = document.getElementById('viewer-category-badge');
    const catVal = document.getElementById('viewer-category-val');

    expect(viewerPanel.classList.contains('hidden')).toBe(false);
    expect(titleEl.textContent).toBe('مستند اختباري');
    expect(peekBadge.classList.contains('hidden')).toBe(true);
    expect(catBadge.classList.contains('hidden')).toBe(false);
    expect(catVal.textContent).toBe('03 - أمر تخصيص');
  });

  it('displays category badge and shows peek badge when peekDocument is called', () => {
    window.peekDocument('doc_99', 'معاينة مباشرة', '10 - صيانة');

    const viewerPanel = document.getElementById('document-viewer-panel');
    const titleEl = document.getElementById('viewer-title');
    const peekBadge = document.getElementById('viewer-peek-badge');
    const catBadge = document.getElementById('viewer-category-badge');
    const catVal = document.getElementById('viewer-category-val');

    expect(viewerPanel.classList.contains('hidden')).toBe(false);
    expect(titleEl.textContent).toBe('معاينة مباشرة');
    expect(peekBadge.classList.contains('hidden')).toBe(false);
    expect(catBadge.classList.contains('hidden')).toBe(false);
    expect(catVal.textContent).toBe('10 - صيانة');
  });

  it('resolves category from currentTimeline if not explicitly passed', () => {
    window.openDocument('doc_1', 'عقد إيجار 101');

    const catBadge = document.getElementById('viewer-category-badge');
    const catVal = document.getElementById('viewer-category-val');

    expect(catBadge.classList.contains('hidden')).toBe(false);
    expect(catVal.textContent).toBe('05 - عقود');
  });

  it('resolves category from globalTreeData if not in timeline and not explicitly passed', () => {
    window.peekDocument('doc_2', 'فاتورة ماء');

    const catBadge = document.getElementById('viewer-category-badge');
    const catVal = document.getElementById('viewer-category-val');

    expect(catBadge.classList.contains('hidden')).toBe(false);
    expect(catVal.textContent).toBe('06 - كهرباء وماء');
  });

  it('hides category badge and viewer on closeDocument()', () => {
    window.openDocument('doc_1', 'عقد إيجار 101', '05 - عقود');

    const viewerPanel = document.getElementById('document-viewer-panel');
    const catBadge = document.getElementById('viewer-category-badge');
    const catVal = document.getElementById('viewer-category-val');

    expect(viewerPanel.classList.contains('hidden')).toBe(false);
    expect(catBadge.classList.contains('hidden')).toBe(false);

    window.closeDocument();

    expect(viewerPanel.classList.contains('hidden')).toBe(true);
    expect(catBadge.classList.contains('hidden')).toBe(true);
    expect(catVal.textContent).toBe('');
  });

  describe('Tablet Inline PDF & Vault Hash Title Sanitization (Android Tablet Support)', () => {
    it('isVaultHashName correctly identifies raw vault hashes and ignores normal filenames', () => {
      expect(window.isVaultHashName('doc_ac132cf0a3824f96.pdf')).toBe(true);
      expect(window.isVaultHashName('ac132cf0a3824f96.pdf')).toBe(true);
      expect(window.isVaultHashName('doc_03e6137c5dd841c2bad7b6bb71f622f3.pdf')).toBe(true);
      expect(window.isVaultHashName('03e6137c5dd841c2bad7b6bb71f622f3')).toBe(true);

      expect(window.isVaultHashName('contract.pdf')).toBe(false);
      expect(window.isVaultHashName('عقد إيجار')).toBe(false);
      expect(window.isVaultHashName('فاتورة كهرباء 2026.pdf')).toBe(false);
      expect(window.isVaultHashName(null)).toBe(false);
    });

    it('getCleanDocTitle replaces raw vault hash filenames with category or fallback', () => {
      // 1. Raw vault hash filename without arabic title -> returns category
      const docWithHash = {
        vault_id: 'ac132cf0a3824f96',
        filename: 'doc_ac132cf0a3824f96.pdf',
        brief_arabic_title: '',
        category: '13 - رسائل متنوعة'
      };
      expect(window.getCleanDocTitle(docWithHash)).toBe('13 - رسائل متنوعة');

      // 2. Normal Arabic title -> preserves Arabic title
      const docWithArabic = {
        vault_id: 'ac132cf0a3824f96',
        filename: 'doc_ac132cf0a3824f96.pdf',
        brief_arabic_title: 'محضر تسليم مفتاح',
        category: '04 - محضر تسليم مفتاح'
      };
      expect(window.getCleanDocTitle(docWithArabic)).toBe('محضر تسليم مفتاح');

      // 3. String hash passed directly -> returns fallback
      expect(window.getCleanDocTitle('doc_ac132cf0a3824f96.pdf', '05 - عقود')).toBe('05 - عقود');
    });

    it('openDocument sanitizes vault hash titles so ac132cf.. is never displayed in viewer header', () => {
      window.openDocument('ac132cf0a3824f96', 'doc_ac132cf0a3824f96.pdf', '05 - عقود');

      const titleEl = document.getElementById('viewer-title');
      expect(titleEl.textContent).not.toContain('ac132cf');
      expect(titleEl.textContent).toBe('05 - عقود');
    });

    it('detects tablet / mobile device when navigator.pdfViewerEnabled is false', () => {
      const originalNavigator = global.navigator;
      try {
        Object.defineProperty(global, 'navigator', {
          value: { pdfViewerEnabled: false, userAgent: 'Mozilla/5.0 (Linux; Android 14; Tablet)' },
          configurable: true,
          writable: true
        });
        localStorage.removeItem('pdf_viewer_mode');
        expect(window.shouldUseCanvasViewer()).toBe(true);
      } finally {
        Object.defineProperty(global, 'navigator', {
          value: originalNavigator,
          configurable: true,
          writable: true
        });
      }
    });

    it('close button in header dismisses the viewer panel', () => {
      window.openDocument('doc_1', 'مستند اختباري', '05 - عقود');
      const viewerPanel = document.getElementById('document-viewer-panel');
      expect(viewerPanel.classList.contains('hidden')).toBe(false);

      window.closeDocument();
      expect(viewerPanel.classList.contains('hidden')).toBe(true);
    });

    it('renders PDF in official viewer.html on tablet/mobile', () => {
      const originalNavigator = global.navigator;
      try {
        Object.defineProperty(global, 'navigator', {
          value: { pdfViewerEnabled: false, userAgent: 'Mozilla/5.0 (Linux; Android 14; Tablet)' },
          configurable: true,
          writable: true
        });
        localStorage.removeItem('pdf_viewer_mode');

        const pdfUrl = '/api/areas/Safra/houses/101/pdf/doc_test';
        const viewerSrc = window.resolveViewerSrc(pdfUrl);
        expect(viewerSrc).toContain('/lib/pdfjs/web/viewer.html?file=');
        expect(viewerSrc).toContain(encodeURIComponent(pdfUrl));

        window.openDocument('doc_test', 'عقد', '05 - عقود');
        const frame = document.getElementById('pdf-frame');
        expect(frame.src).toContain('/lib/pdfjs/web/viewer.html?file=');
      } finally {
        Object.defineProperty(global, 'navigator', {
          value: originalNavigator,
          configurable: true,
          writable: true
        });
      }
    });

    it('expand button toggles fullscreen-viewer class on viewer panel', () => {
      const panel = document.getElementById('document-viewer-panel');
      const expandBtn = document.createElement('button');
      expandBtn.id = 'viewer-expand-btn';
      panel.querySelector('.header').appendChild(expandBtn);

      window.initViewerControls();

      expect(panel.classList.contains('fullscreen-viewer')).toBe(false);
      window.toggleFullscreen();
      expect(panel.classList.contains('fullscreen-viewer')).toBe(true);
      window.toggleFullscreen();
      expect(panel.classList.contains('fullscreen-viewer')).toBe(false);
    });

    it('defaults to Computer on standard desktop computer without touch', () => {
      const originalNavigator = global.navigator;
      try {
        Object.defineProperty(global, 'navigator', {
          value: {
            pdfViewerEnabled: true,
            maxTouchPoints: 0,
            userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
          },
          configurable: true,
          writable: true
        });
        localStorage.removeItem('pdf_viewer_mode');
        expect(window.shouldUseOfficialViewer()).toBe(false);
      } finally {
        Object.defineProperty(global, 'navigator', {
          value: originalNavigator,
          configurable: true,
          writable: true
        });
      }
    });

    it('defaults to Tab on touchscreen devices', () => {
      const originalNavigator = global.navigator;
      try {
        Object.defineProperty(global, 'navigator', {
          value: {
            pdfViewerEnabled: true,
            maxTouchPoints: 5,
            userAgent: 'Mozilla/5.0 (Linux; Android 14; Tablet) AppleWebKit/537.36'
          },
          configurable: true,
          writable: true
        });
        localStorage.removeItem('pdf_viewer_mode');
        expect(window.shouldUseOfficialViewer()).toBe(true);
      } finally {
        Object.defineProperty(global, 'navigator', {
          value: originalNavigator,
          configurable: true,
          writable: true
        });
      }
    });

    it('toggles viewer mode between Computer and Tab and updates UI and localStorage', () => {
      const toggleBtn = document.getElementById('viewer-mode-toggle');

      localStorage.removeItem('pdf_viewer_mode');
      window.initViewerControls();

      // Test explicit update to tab mode
      window.updateViewerModeButton('tab');
      const label = document.getElementById('viewer-mode-label');
      const icon = document.getElementById('viewer-mode-icon');
      expect(label.textContent).toBe('Tab');
      expect(toggleBtn.title).toContain('Tab');
      expect(icon.innerHTML).toContain('M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z');

      // Test explicit update to computer mode
      window.updateViewerModeButton('computer');
      expect(label.textContent).toBe('Computer');
      expect(toggleBtn.title).toContain('Computer');
      expect(icon.innerHTML).toContain('M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z');

      // Test clicking the toggle button
      localStorage.setItem('pdf_viewer_mode', 'computer');
      toggleBtn.click();
      expect(localStorage.getItem('pdf_viewer_mode')).toBe('tab');
      expect(label.textContent).toBe('Tab');

      toggleBtn.click();
      expect(localStorage.getItem('pdf_viewer_mode')).toBe('computer');
      expect(label.textContent).toBe('Computer');

      toggleBtn.remove();
    });

    it('reuses existing PDFViewerApplication instance in Tab mode without resetting iframe src', () => {
      localStorage.setItem('pdf_viewer_mode', 'tab');
      const pdfFrame = document.getElementById('pdf-frame');

      let openedUrl = null;
      const mockOpen = vi.fn(({ url }) => { openedUrl = url; });
      Object.defineProperty(pdfFrame, 'contentWindow', {
        value: {
          PDFViewerApplication: {
            initialized: true,
            open: mockOpen
          }
        },
        configurable: true,
        writable: true
      });

      pdfFrame.src = '/lib/pdfjs/web/viewer.html?file=initial.pdf';

      window.openDocument('doc_second', 'فاتورة كهرباء', '06 - كهرباء وماء');

      // Frame src should NOT be changed because instance was reused
      expect(pdfFrame.src).toContain('/lib/pdfjs/web/viewer.html?file=initial.pdf');
      expect(mockOpen).toHaveBeenCalledWith({
        url: window.resolvePdfUrl('doc_second')
      });
      expect(openedUrl).toBe(window.resolvePdfUrl('doc_second'));
    });
  });

  describe('Offline English Translation Overlay Feature', () => {
    it('verifies index.html contains viewer-translate-btn and document-translation-overlay', () => {
      expect(htmlContent).toContain('id="viewer-translate-btn"');
      expect(htmlContent).toContain('id="viewer-translate-label"');
      expect(htmlContent).toContain('id="document-translation-overlay"');
    });

    it('getEnglishCategory translates standard categories accurately with icons', () => {
      expect(window.getEnglishCategory('05 - عقود').en).toBe('Lease & Tenancy Contract');
      expect(window.getEnglishCategory('05 - عقود').icon).toBe('📜');
      expect(window.getEnglishCategory('06 - كهرباء وماء').en).toBe('Electricity & Water (EWA) Utility Bill');
      expect(window.getEnglishCategory('03 - أمر تخصيص').en).toBe('Housing Allocation Order');
      expect(window.getEnglishCategory('04 - محضر تسليم مفتاح').en).toBe('Key Handover Minutes');
      expect(window.getEnglishCategory('07 - استقطاع إيجار').en).toBe('Rent Deduction Notice');
      expect(window.getEnglishCategory('09 - إشعارات').en).toBe('Official Notices & Eviction Warnings');
      expect(window.getEnglishCategory('10 - صيانة').en).toBe('Maintenance & Repair Request');
      expect(window.getEnglishCategory(null).en).toBe('Official Housing Document');
    });

    it('translateArabicText translates military ranks, administrative entities, and phrases', () => {
      expect(window.translateArabicText('محضر اجتماع لجنة دراسة الخدمات الإسكانية'))
        .toContain('Minutes of Meeting Housing Services Committee');

      expect(window.translateArabicText('مكتب وكيل وزارة الداخلية'))
        .toBe('Office of the Undersecretary of the Ministry of Interior');

      expect(window.translateArabicText('العقيد / مدير إدارة المحاكم العسكرية'))
        .toContain('Colonel / Director Directorate of Military Courts');

      expect(window.translateArabicText('إشعار بإخلاء الوحدة السكنية'))
        .toBe('Housing Unit Eviction Notice');

      expect(window.translateArabicText('عقد إيجار موثق'))
        .toBe('Notarized Tenancy Contract');

      // Preserves existing English
      expect(window.translateArabicText('A formal confidential letter from the Ministry'))
        .toBe('A formal confidential letter from the Ministry');

      // Converts Eastern Arabic numerals
      expect(window.translateArabicText('٢٠٢٥/١٢/٢٤'))
        .toBe('2025/12/24');
    });

    it('toggles translation mode, saves preference in localStorage, and updates button state', () => {
      localStorage.removeItem('doc_viewer_translate');
      const btn = document.getElementById('viewer-translate-btn');
      const label = document.getElementById('viewer-translate-label');

      expect(window.isDocumentTranslationActive()).toBe(false);
      expect(btn.getAttribute('aria-pressed')).toBe('false');

      // Toggle ON
      window.toggleDocumentTranslation();
      expect(window.isDocumentTranslationActive()).toBe(true);
      expect(localStorage.getItem('doc_viewer_translate')).toBe('true');
      expect(btn.getAttribute('aria-pressed')).toBe('true');
      expect(label.textContent).toBe('English (Active)');

      // Toggle OFF
      window.toggleDocumentTranslation();
      expect(window.isDocumentTranslationActive()).toBe(false);
      expect(localStorage.getItem('doc_viewer_translate')).toBe('false');
      expect(btn.getAttribute('aria-pressed')).toBe('false');
      expect(label.textContent).toBe('English');
    });

    it('renders in-place Google Translate style overlay directly over document canvas with bounding boxes', async () => {
      // Enable translation
      localStorage.setItem('doc_viewer_translate', 'true');
      eval(fs.readFileSync(path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/doc-viewer.js'), 'utf8'));

      window.openDocument('doc_contract_99', 'عقد إيجار', '05 - عقود');

      // Wait for async translation rendering
      await window.renderDocumentTranslation();

      const canvasContainer = document.getElementById('pdf-canvas-container');
      const pdfFrame = document.getElementById('pdf-frame');
      expect(canvasContainer.classList.contains('hidden')).toBe(false);
      expect(pdfFrame.classList.contains('hidden')).toBe(true);

      const pageWrapper = canvasContainer.querySelector('.pdf-page-wrapper');
      expect(pageWrapper).not.toBeNull();

      const translationLayer = pageWrapper.querySelector('.pdf-translation-layer');
      expect(translationLayer).not.toBeNull();

      const boxes = translationLayer.querySelectorAll('.in-place-translated-box');
      expect(boxes.length).toBeGreaterThanOrEqual(2);

      // Box 1: Ministry of Interior
      const box1 = boxes[0];
      expect(box1.textContent).toBe('Office of the Undersecretary of the Ministry of Interior');
      expect(box1.getAttribute('data-original-text')).toBe('مكتب وكيل وزارة الداخلية');
      expect(box1.getAttribute('title')).toContain('مكتب وكيل وزارة الداخلية');
      expect(box1.style.backgroundColor).toBe('rgb(255, 255, 255)');
      expect(box1.style.position).toBe('absolute');

      // Box 2: Housing Allocation Order
      const box2 = boxes[1];
      expect(box2.textContent).toBe('Housing Allocation Order');
      expect(box2.getAttribute('data-original-text')).toBe('أمر تخصيص مسكن');

      // Box hover peek behavior
      box1.dispatchEvent(new Event('mouseenter'));
      expect(box1.style.opacity).toBe('0.12');
      box1.dispatchEvent(new Event('mouseleave'));
      expect(box1.style.opacity).toBe('1');

      // Page Peek Original button interaction
      const peekBtn = translationLayer.querySelector('.btn-peek-scan');
      expect(peekBtn).not.toBeNull();
      peekBtn.click();
      expect(box1.style.opacity).toBe('0');
      expect(box2.style.opacity).toBe('0');
      peekBtn.click();
      expect(box1.style.opacity).toBe('1');
      expect(box2.style.opacity).toBe('1');
    });

    it('translates newly uploaded documents without database AI metadata using offline OCR', async () => {
      // Simulate new upload with no database metadata
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404
      });

      localStorage.setItem('doc_viewer_translate', 'true');
      eval(fs.readFileSync(path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/doc-viewer.js'), 'utf8'));

      window.openDocument('doc_new_upload_without_ai', 'ملف جديد ممسوح ضوئيا', '13 - رسائل متنوعة');
      await window.renderDocumentTranslation();

      const canvasContainer = document.getElementById('pdf-canvas-container');
      const pageWrapper = canvasContainer.querySelector('.pdf-page-wrapper');
      const translationLayer = pageWrapper.querySelector('.pdf-translation-layer');
      expect(translationLayer).not.toBeNull();

      const boxes = translationLayer.querySelectorAll('.in-place-translated-box');
      expect(boxes.length).toBeGreaterThanOrEqual(1);
      expect(boxes[0].textContent).toContain('Office of the Undersecretary');
    });

    it('closeDocument dismisses and clears translation layers', async () => {
      localStorage.setItem('doc_viewer_translate', 'true');
      eval(fs.readFileSync(path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/doc-viewer.js'), 'utf8'));
      window.openDocument('doc_test_close', 'مستند إغلاق', '05 - عقود');
      await window.renderDocumentTranslation();

      const canvasContainer = document.getElementById('pdf-canvas-container');
      expect(canvasContainer.querySelectorAll('.pdf-translation-layer').length).toBeGreaterThan(0);

      window.closeDocument();
      expect(canvasContainer.querySelectorAll('.pdf-translation-layer').length).toBe(0);
    });
  });

  describe('Tab Mode & Multi-Page Document Regression Suite', () => {
    it('in Tab mode, openDocument renders official viewer.html and keeps pdf-canvas-container hidden', () => {
      localStorage.setItem('pdf_viewer_mode', 'tab');
      localStorage.setItem('doc_viewer_translate', 'false');
      eval(fs.readFileSync(path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/doc-viewer.js'), 'utf8'));

      expect(window.shouldUseOfficialViewer()).toBe(true);

      window.openDocument('doc_tab_test', 'عقد إيجار رسمي', '05 - عقود');

      const pdfFrame = document.getElementById('pdf-frame');
      const canvasContainer = document.getElementById('pdf-canvas-container');

      expect(canvasContainer.classList.contains('hidden')).toBe(true);
      expect(pdfFrame.classList.contains('hidden')).toBe(false);
      expect(pdfFrame.src).toContain('/lib/pdfjs/web/viewer.html?file=');
      expect(pdfFrame.src).toContain(encodeURIComponent('/api/areas/Safra%20C/houses/101/pdf/doc_tab_test'));
    });

    it('in Tab mode, toggling translation ON and then OFF cleanly restores pdfFrame and viewer.html', async () => {
      localStorage.setItem('pdf_viewer_mode', 'tab');
      localStorage.setItem('doc_viewer_translate', 'false');
      eval(fs.readFileSync(path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/doc-viewer.js'), 'utf8'));

      window.openDocument('doc_tab_toggle', 'عقد إيجار رسمي', '05 - عقود');

      const pdfFrame = document.getElementById('pdf-frame');
      const canvasContainer = document.getElementById('pdf-canvas-container');
      expect(canvasContainer.classList.contains('hidden')).toBe(true);
      expect(pdfFrame.classList.contains('hidden')).toBe(false);

      // Toggle translation ON
      window.toggleDocumentTranslation();
      expect(window.isDocumentTranslationActive()).toBe(true);
      await window.renderDocumentTranslation();

      expect(pdfFrame.classList.contains('hidden')).toBe(true);
      expect(canvasContainer.classList.contains('hidden')).toBe(false);

      // Toggle translation OFF
      window.toggleDocumentTranslation();
      expect(window.isDocumentTranslationActive()).toBe(false);

      // REGRESSION ASSERTION: Tab mode must restore pdfFrame and hide canvasContainer
      expect(canvasContainer.classList.contains('hidden')).toBe(true);
      expect(pdfFrame.classList.contains('hidden')).toBe(false);
      expect(pdfFrame.src).toContain('/lib/pdfjs/web/viewer.html');
    });

    it('renders multi-page documents without compressing or squashing pages into one viewport', async () => {
      // Mock 3-page PDF
      global.pdfjsLib = {
        GlobalWorkerOptions: {},
        getDocument: vi.fn().mockReturnValue({
          promise: Promise.resolve({
            numPages: 3,
            getPage: vi.fn().mockImplementation((pageNum) => Promise.resolve({
              getViewport: vi.fn().mockReturnValue({ width: 800, height: 1100, scale: 1.0 }),
              render: vi.fn().mockReturnValue({ promise: Promise.resolve() }),
              getTextContent: vi.fn().mockResolvedValue({ items: [] })
            }))
          })
        })
      };

      localStorage.setItem('doc_viewer_translate', 'true');
      eval(fs.readFileSync(path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/doc-viewer.js'), 'utf8'));

      window.openDocument('doc_multipage', 'عقد متعدد الصفحات', '05 - عقود');
      await window.renderDocumentTranslation();

      const canvasContainer = document.getElementById('pdf-canvas-container');
      const pageWrappers = canvasContainer.querySelectorAll('.pdf-page-wrapper');
      expect(pageWrappers.length).toBe(3);

      pageWrappers.forEach((wrapper) => {
        // Must have flex-shrink: 0 to prevent CSS flexbox from compressing all pages into one screen
        expect(wrapper.classList.contains('flex-shrink-0')).toBe(true);
        expect(wrapper.style.flexShrink).toBe('0');
        // Must have explicit minHeight and height
        expect(parseInt(wrapper.style.minHeight, 10)).toBeGreaterThanOrEqual(1100);
        expect(parseInt(wrapper.style.height, 10)).toBeGreaterThanOrEqual(1100);

        const canvas = wrapper.querySelector('canvas.pdf-page-canvas');
        expect(canvas).not.toBeNull();
        expect(canvas.classList.contains('flex-shrink-0')).toBe(true);
        expect(canvas.style.flexShrink).toBe('0');
        expect(parseInt(canvas.style.minHeight, 10)).toBeGreaterThanOrEqual(1100);
      });
    });

    it('clicking viewer-mode-toggle switches between Tab mode and Computer mode seamlessly', () => {
      localStorage.setItem('pdf_viewer_mode', 'tab');
      eval(fs.readFileSync(path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/doc-viewer.js'), 'utf8'));

      window.openDocument('doc_mode_switch', 'عقد للتبديل', '05 - عقود');
      const modeBtn = document.getElementById('viewer-mode-toggle');
      const modeLabel = document.getElementById('viewer-mode-label');
      const pdfFrame = document.getElementById('pdf-frame');
      const canvasContainer = document.getElementById('pdf-canvas-container');

      expect(modeLabel.textContent).toBe('Tab');
      expect(pdfFrame.src).toContain('/lib/pdfjs/web/viewer.html');
      expect(canvasContainer.classList.contains('hidden')).toBe(true);

      // Switch to Computer mode
      modeBtn.click();
      expect(localStorage.getItem('pdf_viewer_mode')).toBe('computer');
      expect(modeLabel.textContent).toBe('Computer');
      expect(pdfFrame.src).toContain('/api/areas/Safra%20C/houses/101/pdf/doc_mode_switch#view=FitH');
      expect(pdfFrame.classList.contains('hidden')).toBe(false);
      expect(canvasContainer.classList.contains('hidden')).toBe(true);

      // Switch back to Tab mode
      modeBtn.click();
      expect(localStorage.getItem('pdf_viewer_mode')).toBe('tab');
      expect(modeLabel.textContent).toBe('Tab');
      expect(pdfFrame.src).toContain('/lib/pdfjs/web/viewer.html');
      expect(pdfFrame.classList.contains('hidden')).toBe(false);
      expect(canvasContainer.classList.contains('hidden')).toBe(true);
    });

    it('switching viewer mode while translation is active deactivates translation and displays iframe viewer', async () => {
      localStorage.setItem('pdf_viewer_mode', 'computer');
      localStorage.setItem('doc_viewer_translate', 'true');
      eval(fs.readFileSync(path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/doc-viewer.js'), 'utf8'));

      window.openDocument('doc_trans_switch', 'مستند نشط', '05 - عقود');
      await window.renderDocumentTranslation();

      const pdfFrame = document.getElementById('pdf-frame');
      const canvasContainer = document.getElementById('pdf-canvas-container');
      const modeBtn = document.getElementById('viewer-mode-toggle');

      expect(window.isDocumentTranslationActive()).toBe(true);
      expect(pdfFrame.classList.contains('hidden')).toBe(true);
      expect(canvasContainer.classList.contains('hidden')).toBe(false);

      // User toggles to Tab mode
      modeBtn.click();

      // Translation must be deactivated
      expect(window.isDocumentTranslationActive()).toBe(false);
      expect(localStorage.getItem('doc_viewer_translate')).toBe('false');

      // Tab mode viewer must be shown
      expect(canvasContainer.classList.contains('hidden')).toBe(true);
      expect(pdfFrame.classList.contains('hidden')).toBe(false);
      expect(pdfFrame.src).toContain('/lib/pdfjs/web/viewer.html');
    });
  });
});
