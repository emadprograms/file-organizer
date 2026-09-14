import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Document Empty State Component & View State Transitions', () => {
  const srcHtmlPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/index.html');
  const distHtmlPath = path.resolve(__dirname, '../../../dist/win-x64/wwwroot/index.html');
  const srcCssPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/css/styles.css');
  const distCssPath = path.resolve(__dirname, '../../../dist/win-x64/wwwroot/css/styles.css');

  const srcHtml = fs.readFileSync(srcHtmlPath, 'utf8');
  const distHtml = fs.readFileSync(distHtmlPath, 'utf8');
  const srcCss = fs.readFileSync(srcCssPath, 'utf8');
  const distCss = fs.readFileSync(distCssPath, 'utf8');

  describe('1. Markup & Bilingual Copy Verification', () => {
    it('verifies index.html in src and dist defines #document-empty-state with concise bilingual guidance', () => {
      [srcHtml, distHtml].forEach(html => {
        expect(html).toContain('id="document-empty-state"');
        expect(html).toContain('Select a document to preview');
        expect(html).toContain('اختر مستنداً للمعاينة');
        // Ensure wordy paragraphs and repetitive pill buttons are eliminated
        expect(html).not.toContain('Click any PDF file from the list to preview it here.');
        expect(html).not.toContain('انقر على أي ملف من القائمة لعرضه وتصفحه في هذه المساحة مباشرة');
        expect(html).not.toContain('Click any document to open inline preview');
      });
    });
  });

  describe('2. Light & Dark Mode Background Calibration in CSS', () => {
    it('sets calm light grey #edf0f4 in light mode for #document-empty-state', () => {
      [srcCss, distCss].forEach(css => {
        expect(css).toMatch(/html:not\(\.dark\)\s+#document-empty-state\s*\{[^}]*background-color:\s*#edf0f4;/);
      });
    });

    it('sets deep dark #080c14 in dark mode for #document-empty-state', () => {
      [srcCss, distCss].forEach(css => {
        expect(css).toMatch(/html\.dark\s+#document-empty-state\s*\{[^}]*background-color:\s*#080c14;/);
      });
    });
  });

  describe('3. Dynamic DOM State Transitions (House Entry, Preview, and Close)', () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <div id="sidebar-section-title"></div>
        <div id="current-house-title"></div>
        <div id="stats-badge"></div>
        <div id="tab-categories">
          <span id="tab-categories-label"></span>
          <svg id="tab-categories-icon"></svg>
        </div>
        <div id="tab-timeline">
          <span id="tab-timeline-label"></span>
        </div>
        <div id="tab-back-to-tenants" class="hidden"></div>
        <div id="back-to-grid-btn" class="hidden"></div>
        <div id="area-grid-panel" class="hidden"></div>
        <div id="database-inspector-panel" class="hidden"></div>
        <div id="document-list-panel" class="hidden"></div>
        <div id="resizer-2" class="hidden"></div>
        <div id="welcome-panel"></div>
        <div id="document-empty-state" class="hidden">
          <p>Select a document to preview</p>
        </div>
        <div id="document-viewer-panel" class="hidden">
          <div id="viewer-title"></div>
          <span id="viewer-peek-badge" class="hidden"></span>
          <div id="viewer-category-badge" class="hidden">
            <span id="viewer-category-val"></span>
          </div>
          <iframe id="pdf-frame" src="about:blank"></iframe>
          <a id="viewer-download" href="#"></a>
          <button id="viewer-close-btn"></button>
          <button id="viewer-expand-btn"></button>
          <button id="viewer-mode-toggle"></button>
        </div>
      `;

      global.currentArea = null;
      global.currentHouse = null;
      global.currentTenant = null;
      global.currentTab = 'categories';
      global.currentViewMode = 'overview';
      global.globalTreeData = [];
      global.refreshCurrentTab = vi.fn();

      // Load router and doc-viewer scripts
      const routerCode = fs.readFileSync(
        path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/router.js'),
        'utf8'
      );
      eval(routerCode);

      const docViewerCode = fs.readFileSync(
        path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/doc-viewer.js'),
        'utf8'
      );
      eval(docViewerCode);

      const areaGridCode = fs.readFileSync(
        path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/area-grid.js'),
        'utf8'
      );
      eval(areaGridCode);
    });

    afterEach(() => {
      document.body.innerHTML = '';
      vi.restoreAllMocks();
    });

    it('shows #document-empty-state and hides #welcome-panel and #document-viewer-panel when entering a house', async () => {
      const emptyState = document.getElementById('document-empty-state');
      const welcomePanel = document.getElementById('welcome-panel');
      const docViewerPanel = document.getElementById('document-viewer-panel');
      const docListPanel = document.getElementById('document-list-panel');

      expect(emptyState.classList.contains('hidden')).toBe(true);

      await window.selectHouse('Safra C', '101');

      // Empty state placeholder is visible with light grey canvas
      expect(emptyState.classList.contains('hidden')).toBe(false);
      expect(emptyState.classList.contains('flex')).toBe(true);

      // Welcome panel and document viewer panel are hidden
      expect(welcomePanel.classList.contains('hidden')).toBe(true);
      expect(docViewerPanel.classList.contains('hidden')).toBe(true);

      // Document list panel is active
      expect(docListPanel.classList.contains('hidden')).toBe(false);
      expect(docListPanel.classList.contains('flex')).toBe(true);
    });

    it('hides #document-empty-state when opening a document in the viewer', async () => {
      await window.selectHouse('Safra C', '101');

      const emptyState = document.getElementById('document-empty-state');
      const docViewerPanel = document.getElementById('document-viewer-panel');

      expect(emptyState.classList.contains('hidden')).toBe(false);

      window.openDocument('doc_abc123', 'Electricity Bill');

      expect(emptyState.classList.contains('hidden')).toBe(true);
      expect(emptyState.classList.contains('flex')).toBe(false);
      expect(docViewerPanel.classList.contains('hidden')).toBe(false);
    });

    it('hides #document-empty-state during peekDocument', async () => {
      await window.selectHouse('Safra C', '101');

      const emptyState = document.getElementById('document-empty-state');
      const docViewerPanel = document.getElementById('document-viewer-panel');

      window.peekDocument('doc_abc123', 'Contract Preview');

      expect(emptyState.classList.contains('hidden')).toBe(true);
      expect(docViewerPanel.classList.contains('hidden')).toBe(false);
    });

    it('restores #document-empty-state when closing document if a house is currently selected', async () => {
      await window.selectHouse('Safra C', '101');
      window.openDocument('doc_abc123', 'Contract');

      const emptyState = document.getElementById('document-empty-state');
      const welcomePanel = document.getElementById('welcome-panel');
      const docViewerPanel = document.getElementById('document-viewer-panel');

      expect(emptyState.classList.contains('hidden')).toBe(true);

      window.closeDocument();

      // Doc viewer hidden
      expect(docViewerPanel.classList.contains('hidden')).toBe(true);
      // Empty state displayed for house
      expect(emptyState.classList.contains('hidden')).toBe(false);
      expect(emptyState.classList.contains('flex')).toBe(true);
      // Welcome panel remains hidden
      expect(welcomePanel.classList.contains('hidden')).toBe(true);
    });

    it('restores #welcome-panel and hides #document-empty-state when closing document if no house is selected', () => {
      global.currentHouse = null;
      window.currentHouse = null;

      window.openDocument('doc_abc123', 'Contract');
      window.closeDocument();

      const emptyState = document.getElementById('document-empty-state');
      const welcomePanel = document.getElementById('welcome-panel');

      expect(emptyState.classList.contains('hidden')).toBe(true);
      expect(welcomePanel.classList.contains('hidden')).toBe(false);
    });

    it('hides #document-empty-state when switching to database inspector or area grid overview', () => {
      const emptyState = document.getElementById('document-empty-state');
      emptyState.classList.remove('hidden');
      emptyState.classList.add('flex');

      window.switchToViewMode('db');
      expect(emptyState.classList.contains('hidden')).toBe(true);

      emptyState.classList.remove('hidden');
      emptyState.classList.add('flex');

      window.renderAreaGrid({ name: 'Safra C', children: [] });
      expect(emptyState.classList.contains('hidden')).toBe(true);
    });
  });
});
