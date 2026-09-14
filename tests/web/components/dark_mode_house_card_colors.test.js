import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('House Card Duration Indicator Colors in Dark Mode', () => {
  const cssPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/css/styles.css');
  const cssContent = fs.readFileSync(cssPath, 'utf8');

  beforeEach(() => {
    document.documentElement.className = 'dark';
    document.body.innerHTML = `
      <div id="area-grid-panel" class="flex">
        <h2 id="grid-area-title">Test Area</h2>
        <div id="grid-area-stats"></div>
        <div id="grid-tenure-legend"></div>
        <div id="area-grid-container"></div>
      </div>
    `;

    global.currentArea = 'Test Area';
    global.window.location = { hash: '' };

    const scriptCode = fs.readFileSync(
      path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/area-grid.js'),
      'utf8'
    );
    eval(scriptCode);
  });

  afterEach(() => {
    document.documentElement.className = '';
    document.body.innerHTML = '';
    vi.restoreAllMocks();
  });

  it('renders house cards with correct tenure duration border classes in Area Grid', () => {
    const areaNode = {
      name: 'Test Area',
      children: [
        {
          id: '101',
          name: 'House Short (<5y)',
          duration_category: 'short',
          total_documents: 2,
          children: [{ type: 'tenant', name: 'Tenant A', subtitle: '2023 - Present', is_resident: 1, is_active: true }]
        },
        {
          id: '102',
          name: 'House Medium (5-10y)',
          duration_category: 'medium',
          total_documents: 4,
          children: [{ type: 'tenant', name: 'Tenant B', subtitle: '2016 - Present', is_resident: 1, is_active: true }]
        },
        {
          id: '103',
          name: 'House Long (>10y)',
          duration_category: 'long',
          total_documents: 8,
          children: [{ type: 'tenant', name: 'Tenant C', subtitle: '2010 - Present', is_resident: 1, is_active: true }]
        },
        {
          id: '104',
          name: 'House Vacant',
          duration_category: null,
          total_documents: 0,
          children: []
        }
      ]
    };

    window.renderAreaGrid(areaNode);

    const cardShort = document.querySelector('.house-card[data-house-id="101"]');
    const cardMedium = document.querySelector('.house-card[data-house-id="102"]');
    const cardLong = document.querySelector('.house-card[data-house-id="103"]');
    const cardVacant = document.querySelector('.house-card[data-house-id="104"]');

    expect(cardShort).not.toBeNull();
    expect(cardMedium).not.toBeNull();
    expect(cardLong).not.toBeNull();
    expect(cardVacant).not.toBeNull();

    // Verify duration indicator classes
    expect(cardShort.className).toContain('border-l-emerald-500');
    expect(cardMedium.className).toContain('border-l-amber-500');
    expect(cardLong.className).toContain('border-l-rose-500');
    expect(cardVacant.className).toContain('border-l-slate-300');
    expect(cardVacant.className).toContain('dark:border-l-slate-600');
  });

  it('preserves emerald left border color (#10b981) for short tenure cards in styles.css', () => {
    // Matches explicit emerald rule at rest and on hover with !important
    const emeraldMatch = cssContent.match(/html\.dark\s+\.house-card\.border-l-emerald-500[^{]*\{([^}]*)\}/);
    expect(emeraldMatch).not.toBeNull();
    expect(emeraldMatch[1]).toContain('border-left-color: #10b981 !important;');
  });

  it('preserves amber left border color (#f59e0b) for medium tenure cards in styles.css', () => {
    const amberMatch = cssContent.match(/html\.dark\s+\.house-card\.border-l-amber-500[^{]*\{([^}]*)\}/);
    expect(amberMatch).not.toBeNull();
    expect(amberMatch[1]).toContain('border-left-color: #f59e0b !important;');
  });

  it('preserves rose left border color (#f43f5e) for long tenure cards in styles.css', () => {
    const roseMatch = cssContent.match(/html\.dark\s+\.house-card\.border-l-rose-500[^{]*\{([^}]*)\}/);
    expect(roseMatch).not.toBeNull();
    expect(roseMatch[1]).toContain('border-left-color: #f43f5e !important;');
  });

  it('preserves slate left border color (#475569) for vacant cards in styles.css', () => {
    const slateMatch = cssContent.match(/html\.dark\s+\.house-card\.border-l-slate-300[^{]*\{([^}]*)\}/);
    expect(slateMatch).not.toBeNull();
    expect(slateMatch[1]).toContain('border-left-color: #475569 !important;');
  });

  it('ensures dark house-card and hover state do not use shorthand border-color that overrides left border', () => {
    const cardBlock = cssContent.match(/html\.dark\s+\.house-card\s*\{([^}]*)\}/)?.[1] || '';
    expect(cardBlock).not.toMatch(/(^|;|\s)border-color:/);
    expect(cardBlock).toContain('border-top-color: #1e293b;');
    expect(cardBlock).toContain('border-right-color: #1e293b;');
    expect(cardBlock).toContain('border-bottom-color: #1e293b;');

    const hoverBlock = cssContent.match(/html\.dark\s+\.house-card:hover\s*\{([^}]*)\}/)?.[1] || '';
    expect(hoverBlock).not.toMatch(/(^|;|\s)border-color:/);
    expect(hoverBlock).toContain('border-top-color: #3b82f6;');
    expect(hoverBlock).toContain('border-right-color: #3b82f6;');
    expect(hoverBlock).toContain('border-bottom-color: #3b82f6;');
  });

  it('renders long tenure tenant row with border-rose-200/80 which has dark mode styling', () => {
    const areaNode = {
      name: 'Test Area',
      children: [
        {
          id: '103',
          name: 'House Long',
          duration_category: 'long',
          children: [
            { type: 'tenant', name: 'Tenant Long', subtitle: '2005 - Present', is_resident: 1, is_active: true }
          ]
        }
      ]
    };

    window.renderAreaGrid(areaNode);
    const tenantRow = document.querySelector('.tenant-overview-item');
    expect(tenantRow).not.toBeNull();
    expect(tenantRow.className).toContain('border-rose-200/80');

    // Ensure dark mode rule covers border-rose-200/80
    expect(cssContent).toMatch(/html\.dark\s+\.border-rose-200,\s*html\.dark\s+\.border-rose-200\\\/80\s*\{[^}]*border-color:\s*rgba\(244,\s*63,\s*94,\s*0\.28\)\s*!important/);
  });
});
