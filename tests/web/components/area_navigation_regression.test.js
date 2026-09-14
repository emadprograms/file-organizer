import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Area Navigation & House Card Click Regression Tests', () => {
  const mockTreeData = [
    {
      id: 'area_Safra C',
      name: 'Safra C',
      type: 'area',
      children: [
        {
          id: '101',
          name: '101',
          type: 'house',
          duration_category: 'short',
          current_tenant: 'Tenant Alpha',
          total_documents: 5,
          children: [
            {
              type: 'tenant',
              name: 'Tenant Alpha',
              subtitle: '2024 - Present',
              is_resident: 1,
              is_active: true
            }
          ]
        },
        {
          id: '102',
          name: '102',
          type: 'house',
          duration_category: 'medium',
          current_tenant: 'Tenant Beta',
          total_documents: 8,
          children: [
            {
              type: 'tenant',
              name: 'Tenant Beta',
              subtitle: '2018 - Present',
              is_resident: 1,
              is_active: true
            }
          ]
        }
      ]
    },
    {
      id: 'area_Safra D',
      name: 'Safra D',
      type: 'area',
      children: []
    }
  ];

  function setupDOM() {
    document.body.innerHTML = `
      <div id="toast-container"></div>
      <aside id="main-sidebar">
        <h2 id="sidebar-section-title">Areas</h2>
        <div id="house-list">
          <p class="text-slate-500 text-xs px-2 py-1">Loading...</p>
        </div>
      </aside>
      <header id="top-navbar">
        <h1 id="current-house-title">Select an Area</h1>
        <span id="grid-area-title" class="hidden"></span>
        <div id="grid-area-stats" class="hidden"></div>
        <div id="grid-tenure-legend" class="hidden"></div>
        <button id="open-add-house-modal-btn" class="hidden"></button>
        <button id="back-to-grid-btn" class="hidden"></button>
        <button id="tab-back-to-tenants" class="hidden"></button>
        <span id="stats-badge" class="hidden"></span>
        <button id="tab-categories">
          <span id="tab-categories-label"></span>
          <svg id="tab-categories-icon"></svg>
        </button>
        <button id="tab-timeline">
          <span id="tab-timeline-label"></span>
        </button>
      </header>
      <main id="main-content">
        <div id="welcome-panel" class="hidden"></div>
        <div id="document-empty-state" class="hidden"></div>
        <div id="document-list-panel" class="hidden"></div>
        <div id="document-viewer-panel" class="hidden"></div>
        <div id="database-inspector-panel" class="hidden"></div>
        <div id="resizer-2" class="hidden"></div>
        <div id="area-grid-panel" class="hidden flex-col">
          <div id="area-grid-container" class="grid"></div>
        </div>
      </main>
    `;
  }

  function loadScripts() {
    const scripts = ['area-grid.js', 'router.js', 'sidebar.js'];
    for (const file of scripts) {
      const filePath = path.resolve(__dirname, `../../../src/HousingApplication.Web/wwwroot/js/${file}`);
      const code = fs.readFileSync(filePath, 'utf8');
      eval(code);
    }
  }

  beforeEach(() => {
    setupDOM();

    global.API_TREE = '/api/tree';
    global.API_HOUSES_BASE = '/api/houses';
    global.isStaticMode = false;
    global.currentArea = null;
    global.currentHouse = null;
    global.currentTenant = null;
    global.currentTab = 'categories';
    global.currentTimeline = [];
    global.currentCategories = [];
    global.globalTreeData = [];
    global.currentViewMode = 'overview';
    global.isTreeLoading = true;
    global.escapeHtml = (str) => (str ? String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;') : '');
    window.escapeHtml = global.escapeHtml;

    window.location.hash = '#/area/Safra%20C';

    global.fetch = vi.fn().mockImplementation(async (url) => {
      if (url === '/api/tree' || url === global.API_TREE) {
        return {
          ok: true,
          json: async () => JSON.parse(JSON.stringify(mockTreeData))
        };
      }
      return { ok: false, status: 404 };
    });

    loadScripts();
  });

  afterEach(() => {
    document.body.innerHTML = '';
    vi.restoreAllMocks();
  });

  it('loads tree data once and does NOT enter an infinite async recursion loop on area navigation', async () => {
    window.location.hash = '#/area/Safra%20C';

    await window.loadTree();

    // fetch(/api/tree) MUST be called exactly once, never looped infinitely
    expect(global.fetch).toHaveBeenCalledTimes(1);

    // Tree loading MUST be false
    expect(global.isTreeLoading).toBe(false);

    // Sidebar house-list MUST NOT display "Loading..."
    const houseListEl = document.getElementById('house-list');
    expect(houseListEl).not.toBeNull();
    expect(houseListEl.textContent).not.toContain('Loading...');
    expect(houseListEl.textContent).toContain('Safra C');
    expect(houseListEl.textContent).toContain('Safra D');

    // Area grid panel MUST be visible and cards rendered
    const areaGridPanel = document.getElementById('area-grid-panel');
    expect(areaGridPanel.classList.contains('hidden')).toBe(false);

    const cards = document.querySelectorAll('.house-card');
    expect(cards.length).toBe(2);
  });

  it('allows clicking house card to open house profile without interference or re-renders', async () => {
    window.location.hash = '#/area/Safra%20C';
    await window.loadTree();

    const card101 = document.querySelector('.house-card[data-house-id="101"]');
    expect(card101).not.toBeNull();

    // Click on house card
    card101.click();

    // Hash should transition to house profile
    expect(window.location.hash).toBe('#/area/Safra%20C/house/101');

    // Manually trigger handleHashChange to simulate browser routing on hash change
    window.handleHashChange();

    // Area grid panel must be hidden
    const areaGridPanel = document.getElementById('area-grid-panel');
    expect(areaGridPanel.classList.contains('hidden')).toBe(true);

    // Title should reflect house 101
    const currentHouseTitle = document.getElementById('current-house-title');
    expect(currentHouseTitle.textContent).toContain('101');

    // loadTree() must NOT have been called again on card click
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it('protects against re-entrant concurrent loadTree calls via activeLoadPromise guard', async () => {
    const p1 = window.loadTree();
    const p2 = window.loadTree();
    const p3 = window.loadTree();

    await Promise.all([p1, p2, p3]);

    // Despite 3 concurrent calls, fetch was only called once
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.isTreeLoading).toBe(false);

    const houseListEl = document.getElementById('house-list');
    expect(houseListEl.textContent).not.toContain('Loading...');
  });

  it('navigates back to grid cleanly without triggering an infinite reload storm', async () => {
    window.location.hash = '#/area/Safra%20C/house/101';
    await window.loadTree();

    // Currently in house view
    expect(window.currentHouse).toBe('101');

    // Navigate back to area grid by changing hash to area
    window.location.hash = '#/area/Safra%20C';
    window.handleHashChange();

    // Still only 1 fetch call (no infinite reload storm)
    expect(global.fetch).toHaveBeenCalledTimes(1);

    // Area grid panel visible again with cards
    const areaGridPanel = document.getElementById('area-grid-panel');
    expect(areaGridPanel.classList.contains('hidden')).toBe(false);
    expect(document.querySelectorAll('.house-card').length).toBe(2);
  });
});
