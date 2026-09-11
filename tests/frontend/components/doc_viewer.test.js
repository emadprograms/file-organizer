import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Document Viewer & Live Peek Header (Category Badge vs Tenant Select)', () => {
  const htmlContent = fs.readFileSync(
    path.resolve(__dirname, '../../../src/api/static/index.html'),
    'utf8'
  );

  beforeEach(() => {
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
});
