import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Unified Single Header Bar Component & Area Grid (QCK-16)', () => {
  const htmlPath = path.resolve(__dirname, '../../../src/api/static/index.html');
  const htmlContent = fs.readFileSync(htmlPath, 'utf8');

  it('verifies index.html has consolidated single top-navbar and removed secondary header', () => {
    document.body.innerHTML = htmlContent;

    const topNavbar = document.getElementById('top-navbar');
    expect(topNavbar).not.toBeNull();

    // Elements relocated into #top-navbar
    const statsBadge = topNavbar.querySelector('#grid-area-stats');
    expect(statsBadge).not.toBeNull();

    const tenureLegend = topNavbar.querySelector('#grid-tenure-legend');
    expect(tenureLegend).not.toBeNull();
    expect(tenureLegend.textContent).toContain('< 5y');
    expect(tenureLegend.textContent).toContain('5–10y');
    expect(tenureLegend.textContent).toContain('> 10y');

    const addHouseBtn = topNavbar.querySelector('#open-add-house-modal-btn');
    expect(addHouseBtn).not.toBeNull();
    expect(addHouseBtn.textContent).toContain('+ إضافة منزل جديد');

    // Invisible compatibility anchor for tests
    const gridAreaTitle = topNavbar.querySelector('#grid-area-title');
    expect(gridAreaTitle).not.toBeNull();

    // Area Grid Panel must not contain redundant secondary header
    const areaGridPanel = document.getElementById('area-grid-panel');
    expect(areaGridPanel).not.toBeNull();
    expect(areaGridPanel.querySelector('#grid-area-subtitle')).toBeNull();
    
    // House cards container should be direct child of area-grid-panel
    const container = areaGridPanel.querySelector('#area-grid-container');
    expect(container).not.toBeNull();
    expect(container.parentElement.id).toBe('area-grid-panel');
  });

  describe('Dynamic visibility transitions in area-grid.js and router.js', () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <header id="top-navbar">
          <button id="back-to-grid-btn" class="hidden"></button>
          <h1 id="current-house-title"></h1>
          <span id="grid-area-title" class="hidden"></span>
          <div id="stats-badge" class="hidden"></div>
          <div id="grid-area-stats" class="hidden">0 Houses</div>
          <div id="grid-tenure-legend" class="hidden"></div>
          <button id="open-add-house-modal-btn" class="hidden"></button>
        </header>
        <div id="welcome-panel" class="hidden"></div>
        <div id="document-list-panel" class="hidden"></div>
        <div id="document-viewer-panel" class="hidden"></div>
        <div id="database-inspector-panel" class="hidden"></div>
        <div id="resizer-2" class="hidden"></div>
        <div id="tab-back-to-tenants" class="hidden"></div>
        <div id="area-grid-panel" class="hidden">
          <div id="area-grid-container"></div>
        </div>
      `;

      global.currentArea = '';
      global.currentHouse = null;
      global.currentTenant = null;
      global.currentTab = 'categories';
      global.currentViewMode = 'overview';
      window.currentArea = '';
      window.currentHouse = null;
      window.currentTenant = null;

      const areaGridCode = fs.readFileSync(
        path.resolve(__dirname, '../../../src/api/static/js/area-grid.js'),
        'utf8'
      );
      eval(areaGridCode);

      const routerCode = fs.readFileSync(
        path.resolve(__dirname, '../../../src/api/static/js/router.js'),
        'utf8'
      );
      eval(routerCode);
    });

    afterEach(() => {
      document.body.innerHTML = '';
      vi.restoreAllMocks();
    });

    it('shows grid-area-stats, tenure legend, and add-house button upon renderAreaGrid', () => {
      const areaNode = {
        name: 'Safra D',
        children: [
          { id: '101', name: 'House 101', duration_category: 'short', tenants: [] },
          { id: '102', name: 'House 102', duration_category: 'medium', tenants: [] }
        ]
      };

      window.renderAreaGrid(areaNode);

      const stats = document.getElementById('grid-area-stats');
      expect(stats.classList.contains('hidden')).toBe(false);
      expect(stats.textContent).toBe('2 Houses');

      const legend = document.getElementById('grid-tenure-legend');
      expect(legend.classList.contains('hidden')).toBe(false);
      expect(legend.classList.contains('flex')).toBe(true);

      const addBtn = document.getElementById('open-add-house-modal-btn');
      expect(addBtn.classList.contains('hidden')).toBe(false);
      expect(addBtn.classList.contains('inline-flex')).toBe(true);

      const currentHouseTitle = document.getElementById('current-house-title');
      expect(currentHouseTitle.textContent).toBe('Safra D — Houses Overview');
    });

    it('hides grid-area-stats, tenure legend, and add-house button when openHouseFromGrid is triggered', () => {
      const areaNode = {
        name: 'Safra D',
        children: [
          { id: '101', name: 'House 101', duration_category: 'short', tenants: [] }
        ]
      };
      window.renderAreaGrid(areaNode);

      // Verify shown before
      expect(document.getElementById('grid-area-stats').classList.contains('hidden')).toBe(false);

      // Trigger house card navigation
      window.openHouseFromGrid('Safra D', '101');

      expect(document.getElementById('grid-area-stats').classList.contains('hidden')).toBe(true);
      expect(document.getElementById('grid-tenure-legend').classList.contains('hidden')).toBe(true);
      expect(document.getElementById('open-add-house-modal-btn').classList.contains('hidden')).toBe(true);
    });

    it('hides area controls when switching to database view mode', () => {
      const areaNode = {
        name: 'Safra D',
        children: [{ id: '101', name: 'House 101', duration_category: 'short', tenants: [] }]
      };
      window.renderAreaGrid(areaNode);

      window.switchToViewMode('db');

      expect(document.getElementById('grid-area-stats').classList.contains('hidden')).toBe(true);
      expect(document.getElementById('grid-tenure-legend').classList.contains('hidden')).toBe(true);
      expect(document.getElementById('open-add-house-modal-btn').classList.contains('hidden')).toBe(true);
    });
  });
});
