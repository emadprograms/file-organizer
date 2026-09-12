import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Segmented Tabs Emojiless Labels & Dynamic SVG Iconography', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="document-list-panel">
        <div id="tab-back-to-tenants" class="hidden"></div>
        <div class="tabs">
          <button id="tab-categories">
            <svg id="tab-categories-icon" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
            </svg>
            <span id="tab-categories-label">Folders</span>
          </button>
          <button id="tab-timeline">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2z"/>
            </svg>
            <span id="tab-timeline-label">Timeline</span>
          </button>
        </div>
        <div id="document-list"></div>
      </div>
      <div id="current-house-title"></div>
      <div id="area-grid-panel" class="hidden"></div>
      <div id="back-to-grid-btn" class="hidden"></div>
      <div id="welcome-panel" class="hidden"></div>
      <div id="document-viewer-panel" class="hidden"></div>
      <div id="resizer-2" class="hidden"></div>
    `;

    global.currentArea = '';
    global.currentHouse = '';
    global.currentTenant = '';
    global.currentTab = 'categories';
    window.globalTreeData = [];
    window.renderHouseProfile = vi.fn();
    window.loadCategories = vi.fn();
    window.loadTimeline = vi.fn();
    window.refreshCurrentTab = vi.fn();

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

  it('verifies initial folders tab markup has clean text and no emoji', () => {
    const label = document.getElementById('tab-categories-label');
    expect(label.textContent).toBe('Folders');
    expect(label.textContent).not.toContain('📁');
  });

  it('renders clean "سجل المستأجرين" without emoji and Users SVG icon in tenant selection mode', async () => {
    // Calling selectHouse for house overview (no tenant specified)
    await window.selectHouse('Safra C', '500', null);

    const categoriesLabel = document.getElementById('tab-categories-label');
    expect(categoriesLabel.textContent).toBe('سجل المستأجرين');
    expect(categoriesLabel.textContent).not.toContain('📋');

    const categoriesIcon = document.getElementById('tab-categories-icon');
    // Users icon path
    expect(categoriesIcon.innerHTML).toContain('M17 20h5');

    const timelineLabel = document.getElementById('tab-timeline-label');
    expect(timelineLabel.textContent).toBe('House Timeline');
    expect(timelineLabel.textContent).not.toContain('📅');
  });

  it('renders clean "Folders" without emoji and Folder SVG icon in tenant folders mode', async () => {
    // Calling selectHouse with a tenant specified
    await window.selectHouse('Safra C', '500', 'علي الحداد');

    const categoriesLabel = document.getElementById('tab-categories-label');
    expect(categoriesLabel.textContent).toBe('Folders');
    expect(categoriesLabel.textContent).not.toContain('📁');

    const categoriesIcon = document.getElementById('tab-categories-icon');
    // Folder icon path
    expect(categoriesIcon.innerHTML).toContain('M3 7v10');

    const timelineLabel = document.getElementById('tab-timeline-label');
    expect(timelineLabel.textContent).toBe('Tenant Timeline');
    expect(timelineLabel.title).toBe('Tenant Timeline');
  });

  it('sets title tooltip matching label text for both house and tenant timeline modes', async () => {
    const timelineLabel = document.getElementById('tab-timeline-label');
    const categoriesLabel = document.getElementById('tab-categories-label');

    // House mode
    await window.selectHouse('Safra C', '500', null);
    expect(timelineLabel.title).toBe('House Timeline');
    expect(categoriesLabel.title).toBe('سجل المستأجرين');

    // Tenant mode
    await window.selectHouse('Safra C', '500', 'علي الحداد');
    expect(timelineLabel.title).toBe('Tenant Timeline');
    expect(categoriesLabel.title).toBe('Folders');
  });

  it('verifies index.html markup includes min-w-0, whitespace-nowrap, and truncate classes to prevent multiline wrapping on compression', () => {
    const html = fs.readFileSync(
      path.resolve(__dirname, '../../../src/api/static/index.html'),
      'utf8'
    );
    // Tab wrapper allows flex shrinking
    expect(html).toMatch(/class="[^"]*min-w-0[^"]*gap-1[^"]*bg-slate-200\/60/);
    
    // Tab timeline button has min-w-0, overflow-hidden, and whitespace-nowrap
    expect(html).toMatch(/id="tab-timeline"[^>]*class="[^"]*min-w-0[^"]*overflow-hidden[^"]*whitespace-nowrap/);
    
    // Tab timeline label has truncate and whitespace-nowrap
    expect(html).toMatch(/id="tab-timeline-label"[^>]*class="[^"]*truncate[^"]*whitespace-nowrap/);

    // Tab categories button has min-w-0, overflow-hidden, and whitespace-nowrap
    expect(html).toMatch(/id="tab-categories"[^>]*class="[^"]*min-w-0[^"]*overflow-hidden[^"]*whitespace-nowrap/);
    
    // Tab categories label has truncate and whitespace-nowrap
    expect(html).toMatch(/id="tab-categories-label"[^>]*class="[^"]*truncate[^"]*whitespace-nowrap/);
  });

  it('verifies styles.css enforces nowrap, min-width 0, and text truncation so text disappears rather than wrapping', () => {
    const css = fs.readFileSync(
      path.resolve(__dirname, '../../../src/api/static/css/styles.css'),
      'utf8'
    );
    expect(css).toContain('#tab-timeline');
    expect(css).toContain('#tab-timeline-label');
    expect(css).toMatch(/#tab-categories,\s*#tab-timeline\s*\{[^}]*white-space:\s*nowrap/);
    expect(css).toMatch(/#tab-categories-label,\s*#tab-timeline-label\s*\{[^}]*text-overflow:\s*ellipsis/);
    expect(css).toMatch(/#tab-categories-label,\s*#tab-timeline-label\s*\{[^}]*white-space:\s*nowrap/);
  });
});
