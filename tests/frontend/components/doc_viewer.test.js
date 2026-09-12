import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Document Viewer & Live Peek Header (Category Badge vs Tenant Select)', () => {
  const htmlContent = fs.readFileSync(
    path.resolve(__dirname, '../../../src/api/static/index.html'),
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
          <a id="viewer-download" href="#">Open</a>
        </div>
        <iframe id="pdf-frame" src="about:blank"></iframe>
      </div>
    `;

    global.currentArea = 'Safra C';
    global.currentHouse = '101';
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
      path.resolve(__dirname, '../../../src/api/static/js/doc-viewer.js'),
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
      const toggleBtn = document.createElement('button');
      toggleBtn.id = 'viewer-mode-toggle';
      toggleBtn.innerHTML = '<svg id="viewer-mode-icon"></svg><span id="viewer-mode-label"></span>';
      document.body.appendChild(toggleBtn);

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
  });
});
