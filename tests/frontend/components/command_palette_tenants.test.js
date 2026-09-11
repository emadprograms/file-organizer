import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Command Palette Tenant Search Timeline Color Coding', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="command-palette-modal" class="hidden">
        <div id="command-palette-card">
          <input id="search-input" />
          <button id="btn-command-palette-close"></button>
          <div id="command-palette-result-count"></div>
          <div id="search-results"></div>
        </div>
      </div>
      <button id="btn-search-trigger"></button>
    `;

    const scriptCode = fs.readFileSync(
      path.resolve(__dirname, '../../../src/api/static/js/command-palette.js'),
      'utf8'
    );
    eval(scriptCode);
  });

  afterEach(() => {
    document.body.innerHTML = '';
    vi.restoreAllMocks();
  });

  it('renders green timeline badge and hover styles for active tenant residing < 5 years', () => {
    const results = [
      {
        id: '101_tenant_short',
        type: 'tenant',
        title: 'Ali Short',
        subtitle: 'House 101 (2024 - Present) • Safra C',
        url: '/#/area/Safra C/house/101',
        extra_info: '2024 - Present',
        is_current: true,
        duration_category: 'short'
      }
    ];

    window.renderSearchResults(results);

    const item = document.querySelector('.command-palette-result-item');
    expect(item).not.toBeNull();
    expect(item.className).toContain('hover:bg-emerald-50/70');
    expect(item.className).toContain('hover:border-emerald-300');

    const badge = item.querySelector('span.text-\\[10px\\]');
    expect(badge).not.toBeNull();
    expect(badge.textContent).toBe('2024 - Present');
    expect(badge.className).toContain('text-emerald-700');
    expect(badge.className).toContain('bg-emerald-50');
    expect(badge.className).toContain('border-emerald-300');
  });

  it('renders amber / yellow timeline badge and hover styles for active tenant residing 5-10 years', () => {
    const results = [
      {
        id: '102_tenant_med',
        type: 'tenant',
        title: 'Hassan Medium',
        subtitle: 'House 102 (2019 - Present) • Safra C',
        url: '/#/area/Safra C/house/102',
        extra_info: '2019 - Present',
        is_current: true,
        duration_category: 'medium'
      }
    ];

    window.renderSearchResults(results);

    const item = document.querySelector('.command-palette-result-item');
    expect(item).not.toBeNull();
    expect(item.className).toContain('hover:bg-amber-50/70');
    expect(item.className).toContain('hover:border-amber-300');

    const badge = item.querySelector('span.text-\\[10px\\]');
    expect(badge).not.toBeNull();
    expect(badge.textContent).toBe('2019 - Present');
    expect(badge.className).toContain('text-amber-700');
    expect(badge.className).toContain('bg-amber-50');
    expect(badge.className).toContain('border-amber-300');
  });

  it('renders rose / red timeline badge and hover styles for active tenant residing > 10 years', () => {
    const results = [
      {
        id: '103_tenant_long',
        type: 'tenant',
        title: 'Khalid Long',
        subtitle: 'House 103 (2012 - Present) • Safra C',
        url: '/#/area/Safra C/house/103',
        extra_info: '2012 - Present',
        is_current: true,
        duration_category: 'long'
      }
    ];

    window.renderSearchResults(results);

    const item = document.querySelector('.command-palette-result-item');
    expect(item).not.toBeNull();
    expect(item.className).toContain('hover:bg-rose-50/70');
    expect(item.className).toContain('hover:border-rose-300');

    const badge = item.querySelector('span.text-\\[10px\\]');
    expect(badge).not.toBeNull();
    expect(badge.textContent).toBe('2012 - Present');
    expect(badge.className).toContain('text-rose-700');
    expect(badge.className).toContain('bg-rose-50');
    expect(badge.className).toContain('border-rose-300');
  });

  it('renders neutral grey timeline badge and hover styles for past tenants (not living there)', () => {
    const results = [
      {
        id: '101_tenant_past',
        type: 'tenant',
        title: 'Old Ali',
        subtitle: 'House 101 (2015 - 2020) • Safra C',
        url: '/#/area/Safra C/house/101',
        extra_info: '2015 - 2020',
        is_current: false,
        duration_category: null
      }
    ];

    window.renderSearchResults(results);

    const item = document.querySelector('.command-palette-result-item');
    expect(item).not.toBeNull();
    expect(item.className).toContain('hover:bg-slate-100/70');
    expect(item.className).toContain('hover:border-slate-300');

    const badge = item.querySelector('span.text-\\[10px\\]');
    expect(badge).not.toBeNull();
    expect(badge.textContent).toBe('2015 - 2020');
    expect(badge.className).toContain('text-slate-600');
    expect(badge.className).toContain('bg-slate-100');
    expect(badge.className).toContain('border-slate-200');
    expect(badge.className).not.toContain('text-emerald');
  });

  it('falls back gracefully to infer tenure category from extra_info when duration_category is absent', () => {
    const currentYear = new Date().getFullYear();
    const shortStart = currentYear - 2;
    const medStart = currentYear - 7;
    const longStart = currentYear - 15;

    const results = [
      {
        id: 'inferred_short',
        type: 'tenant',
        title: 'Inferred Short',
        url: '/#/',
        extra_info: `${shortStart} - Present`,
        is_current: true
      },
      {
        id: 'inferred_med',
        type: 'tenant',
        title: 'Inferred Medium',
        url: '/#/',
        extra_info: `${medStart} - Present`,
        is_current: true
      },
      {
        id: 'inferred_long',
        type: 'tenant',
        title: 'Inferred Long',
        url: '/#/',
        extra_info: `${longStart} - Present`,
        is_current: true
      }
    ];

    window.renderSearchResults(results);

    const items = document.querySelectorAll('.command-palette-result-item');
    expect(items.length).toBe(3);

    // Item 1: short (<5y) -> emerald
    expect(items[0].querySelector('span.text-\\[10px\\]').className).toContain('text-emerald-700');

    // Item 2: medium (5-10y) -> amber
    expect(items[1].querySelector('span.text-\\[10px\\]').className).toContain('text-amber-700');

    // Item 3: long (>10y) -> rose
    expect(items[2].querySelector('span.text-\\[10px\\]').className).toContain('text-rose-700');
  });
});
