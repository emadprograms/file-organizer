import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Area Grid House Card Component - Scrollbar for > 3 Tenancies', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="area-grid-panel" class="flex">
        <h2 id="grid-area-title">Safra C</h2>
        <div id="grid-area-stats"></div>
        <div id="grid-tenure-legend"></div>
        <div id="area-grid-container"></div>
      </div>
    `;

    global.currentArea = 'Safra C';
    global.window.location = { hash: '' };

    const scriptCode = fs.readFileSync(
      path.resolve(__dirname, '../../../src/api/static/js/area-grid.js'),
      'utf8'
    );
    eval(scriptCode);
  });

  afterEach(() => {
    document.body.innerHTML = '';
    vi.restoreAllMocks();
  });

  it('does NOT add scrollbar classes when a house card has 3 or fewer tenants', () => {
    const areaNode = {
      name: 'Safra C',
      children: [
        {
          id: '101',
          name: '101 - Three Tenants House',
          duration_category: 'short',
          total_documents: 5,
          children: [
            { type: 'tenant', name: 'Tenant 1', subtitle: '2020 - 2021' },
            { type: 'tenant', name: 'Tenant 2', subtitle: '2021 - 2022' },
            { type: 'tenant', name: 'Tenant 3', subtitle: '2022 - Present' }
          ]
        }
      ]
    };

    window.renderAreaGrid(areaNode);

    const card = document.querySelector('.house-card[data-house-id="101"]');
    expect(card).not.toBeNull();

    const tenantsSection = card.querySelector('.tenants-overview-section');
    expect(tenantsSection).not.toBeNull();
    expect(tenantsSection.classList.contains('overflow-y-auto')).toBe(false);
    expect(tenantsSection.classList.contains('max-h-[118px]')).toBe(false);
  });

  it('adds scrollbar classes (max-h-[118px] overflow-y-auto pr-1) when a house card has more than 3 tenants', () => {
    const areaNode = {
      name: 'Safra C',
      children: [
        {
          id: '102',
          name: '102 - Four Tenants House',
          duration_category: 'medium',
          total_documents: 12,
          children: [
            { type: 'tenant', name: 'Tenant 1', subtitle: '2015 - 2017' },
            { type: 'tenant', name: 'Tenant 2', subtitle: '2017 - 2019' },
            { type: 'tenant', name: 'Tenant 3', subtitle: '2019 - 2022' },
            { type: 'tenant', name: 'Tenant 4', subtitle: '2022 - Present' }
          ]
        }
      ]
    };

    window.renderAreaGrid(areaNode);

    const card = document.querySelector('.house-card[data-house-id="102"]');
    expect(card).not.toBeNull();

    const tenantsSection = card.querySelector('.tenants-overview-section');
    expect(tenantsSection).not.toBeNull();
    expect(tenantsSection.classList.contains('overflow-y-auto')).toBe(true);
    expect(tenantsSection.classList.contains('max-h-[118px]')).toBe(true);
    expect(tenantsSection.classList.contains('pr-1')).toBe(true);
  });

  it('stops click propagation when clicking on the scrollbar track/thumb to prevent navigating away', () => {
    const areaNode = {
      name: 'Safra C',
      children: [
        {
          id: '103',
          name: '103 - Many Tenants House',
          duration_category: 'long',
          total_documents: 15,
          children: [
            { type: 'tenant', name: 'Tenant 1', subtitle: '2010 - 2013' },
            { type: 'tenant', name: 'Tenant 2', subtitle: '2013 - 2016' },
            { type: 'tenant', name: 'Tenant 3', subtitle: '2016 - 2020' },
            { type: 'tenant', name: 'Tenant 4', subtitle: '2020 - 2023' },
            { type: 'tenant', name: 'Tenant 5', subtitle: '2023 - Present' }
          ]
        }
      ]
    };

    window.renderAreaGrid(areaNode);

    const card = document.querySelector('.house-card[data-house-id="103"]');
    const tenantsSection = card.querySelector('.tenants-overview-section');

    // Simulate clicking on the scrollbar (offsetX > clientWidth)
    Object.defineProperty(tenantsSection, 'clientWidth', { value: 200, configurable: true });

    let cardClicked = false;
    card.onclick = () => { cardClicked = true; };

    const scrollbarClickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
    Object.defineProperty(scrollbarClickEvent, 'offsetX', { value: 205 });

    tenantsSection.dispatchEvent(scrollbarClickEvent);
    expect(cardClicked).toBe(false);

    // Normal click inside tenant content (offsetX <= clientWidth) bubbles to card
    const normalClickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
    Object.defineProperty(normalClickEvent, 'offsetX', { value: 50 });

    tenantsSection.dispatchEvent(normalClickEvent);
    expect(cardClicked).toBe(true);
  });
});
