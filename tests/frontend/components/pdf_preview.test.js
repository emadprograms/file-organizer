/**
 * Unit tests for the PDF hover preview feature (pdf_preview.test.js)
 *
 * These tests exercise the preview logic in a jsdom environment,
 * covering: positioning, debounce/cancel, URL caching, viewport
 * edge-flip, and attachPreview event wiring.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// ── Minimal DOM scaffold ────────────────────────────────────────────────────
function setupDOM() {
  document.body.innerHTML = `
    <div id="pdf-preview-tooltip" style="width:380px;height:520px;opacity:0;">
      <div class="preview-header" id="pdf-preview-title">Preview</div>
      <iframe id="pdf-preview-iframe" src="about:blank"></iframe>
    </div>
  `;
}

// ── Inline preview logic (mirrors index.html) ──────────────────────────────
// We reimplement the logic as importable functions so Vitest can test it
// without loading the full HTML page (which requires a live server).

function buildPreviewModule({ viewportW = 1280, viewportH = 800 } = {}) {
  const tooltip   = document.getElementById('pdf-preview-tooltip');
  const iframe    = document.getElementById('pdf-preview-iframe');
  const titleEl   = document.getElementById('pdf-preview-title');

  const PREVIEW_GAP      = 12;
  const PREVIEW_DELAY_MS = 350;

  let showTimer   = null;
  let hideTimer   = null;
  let currentUrl  = null;

  // Stub offsetWidth/Height (jsdom returns 0 by default)
  Object.defineProperty(tooltip, 'offsetWidth',  { configurable: true, get: () => 380 });
  Object.defineProperty(tooltip, 'offsetHeight', { configurable: true, get: () => 520 });

  function positionTooltip(mx, my) {
    const tw = tooltip.offsetWidth;
    const th = tooltip.offsetHeight;
    const vw = viewportW;
    const vh = viewportH;

    let left = mx + PREVIEW_GAP;
    let top  = my - 60;

    if (left + tw > vw - 8) left = mx - tw - PREVIEW_GAP;
    if (top + th > vh - 8)  top  = vh - th - 8;
    if (top < 8)             top  = 8;

    tooltip.style.left = `${left}px`;
    tooltip.style.top  = `${top}px`;
    return { left, top };
  }

  function showPreview(vaultId, title, mx, my, area = 'TestArea', house = 'TestHouse') {
    const pdfUrl = `/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/pdf/${vaultId}#toolbar=0&view=FitH`;

    clearTimeout(hideTimer);
    clearTimeout(showTimer);

    showTimer = setTimeout(() => {
      if (currentUrl !== pdfUrl) {
        currentUrl     = pdfUrl;
        iframe.src     = pdfUrl;
        titleEl.textContent = title;
      }
      positionTooltip(mx, my);
      tooltip.classList.add('visible');
    }, PREVIEW_DELAY_MS);

    return showTimer;
  }

  function hidePreview() {
    clearTimeout(showTimer);
    hideTimer = setTimeout(() => {
      tooltip.classList.remove('visible');
    }, 100);
    return hideTimer;
  }

  function attachPreview(el, vaultId, title) {
    el.addEventListener('mouseenter', (e) =>
      showPreview(vaultId, title, e.clientX ?? 100, e.clientY ?? 100));
    el.addEventListener('mouseleave', hidePreview);
  }

  return { tooltip, iframe, titleEl, positionTooltip, showPreview, hidePreview, attachPreview, PREVIEW_DELAY_MS };
}

// ── Tests ──────────────────────────────────────────────────────────────────

describe('PDF Hover Preview — positioning', () => {
  beforeEach(setupDOM);
  afterEach(() => { document.body.innerHTML = ''; vi.useRealTimers(); });

  it('places tooltip right of cursor by default', () => {
    const { positionTooltip } = buildPreviewModule();
    const { left, top } = positionTooltip(400, 300);
    expect(left).toBe(412);   // 400 + 12 gap
    expect(top).toBe(240);    // 300 - 60 offset
  });

  it('flips left when tooltip would overflow the right viewport edge', () => {
    // Cursor at x=950 → 950+12+380 = 1342 > 1280-8 = 1272, so flip
    const { positionTooltip } = buildPreviewModule({ viewportW: 1280 });
    const { left } = positionTooltip(950, 300);
    expect(left).toBe(950 - 380 - 12);  // flip: mx - tw - gap
  });

  it('clamps tooltip to bottom of viewport', () => {
    // Cursor at y=700 → top = 700-60 = 640; 640+520 = 1160 > 800-8 = 792
    const { positionTooltip } = buildPreviewModule({ viewportH: 800 });
    const { top } = positionTooltip(400, 700);
    expect(top).toBe(800 - 520 - 8);    // vh - th - 8
  });

  it('clamps tooltip to top of viewport (min 8px)', () => {
    // Cursor at y=20 → top = 20-60 = -40 → clamped to 8
    const { positionTooltip } = buildPreviewModule();
    const { top } = positionTooltip(400, 20);
    expect(top).toBe(8);
  });
});

describe('PDF Hover Preview — show / hide debounce', () => {
  beforeEach(() => { setupDOM(); vi.useFakeTimers(); });
  afterEach(() => { document.body.innerHTML = ''; vi.useRealTimers(); });

  it('does NOT show immediately on hover — respects delay', () => {
    const { tooltip, showPreview, PREVIEW_DELAY_MS } = buildPreviewModule();
    showPreview('v1', 'Doc', 100, 100);
    expect(tooltip.classList.contains('visible')).toBe(false);
    vi.advanceTimersByTime(PREVIEW_DELAY_MS - 1);
    expect(tooltip.classList.contains('visible')).toBe(false);
  });

  it('shows after full delay elapses', () => {
    const { tooltip, showPreview, PREVIEW_DELAY_MS } = buildPreviewModule();
    showPreview('v1', 'Doc', 100, 100);
    vi.advanceTimersByTime(PREVIEW_DELAY_MS);
    expect(tooltip.classList.contains('visible')).toBe(true);
  });

  it('cancels pending show when hidePreview is called before delay', () => {
    const { tooltip, showPreview, hidePreview, PREVIEW_DELAY_MS } = buildPreviewModule();
    showPreview('v1', 'Doc', 100, 100);
    hidePreview();
    vi.advanceTimersByTime(PREVIEW_DELAY_MS + 500);
    expect(tooltip.classList.contains('visible')).toBe(false);
  });

  it('hides tooltip after mouseleave + 100ms', () => {
    const { tooltip, showPreview, hidePreview, PREVIEW_DELAY_MS } = buildPreviewModule();
    showPreview('v1', 'Doc', 100, 100);
    vi.advanceTimersByTime(PREVIEW_DELAY_MS);
    expect(tooltip.classList.contains('visible')).toBe(true);

    hidePreview();
    vi.advanceTimersByTime(99);
    expect(tooltip.classList.contains('visible')).toBe(true);   // still visible

    vi.advanceTimersByTime(1);
    expect(tooltip.classList.contains('visible')).toBe(false);  // now hidden
  });
});

describe('PDF Hover Preview — iframe URL and title', () => {
  beforeEach(() => { setupDOM(); vi.useFakeTimers(); });
  afterEach(() => { document.body.innerHTML = ''; vi.useRealTimers(); });

  it('sets correct PDF URL on the iframe with toolbar suppressed', () => {
    const { iframe, showPreview, PREVIEW_DELAY_MS } = buildPreviewModule();
    showPreview('abc123', 'My Doc', 100, 100, 'Eastside', '55 - House');
    vi.advanceTimersByTime(PREVIEW_DELAY_MS);
    expect(iframe.src).toContain('/api/areas/Eastside/houses/55%20-%20House/pdf/abc123');
    expect(iframe.src).toContain('toolbar=0');
    expect(iframe.src).toContain('view=FitH');
  });

  it('sets the preview title in the header bar', () => {
    const { titleEl, showPreview, PREVIEW_DELAY_MS } = buildPreviewModule();
    showPreview('v99', 'Contract 2024', 100, 100);
    vi.advanceTimersByTime(PREVIEW_DELAY_MS);
    expect(titleEl.textContent).toBe('Contract 2024');
  });

  it('does NOT reload iframe when hovering same vault_id again', () => {
    const { iframe, showPreview, PREVIEW_DELAY_MS } = buildPreviewModule();
    showPreview('v1', 'Doc', 100, 100);
    vi.advanceTimersByTime(PREVIEW_DELAY_MS);
    const firstSrc = iframe.src;

    // Re-hover the same vault — src must not change
    showPreview('v1', 'Doc', 110, 110);
    vi.advanceTimersByTime(PREVIEW_DELAY_MS);
    expect(iframe.src).toBe(firstSrc);
  });

  it('DOES reload iframe when a different vault_id is hovered', () => {
    const { iframe, showPreview, PREVIEW_DELAY_MS } = buildPreviewModule();
    showPreview('v1', 'Doc A', 100, 100);
    vi.advanceTimersByTime(PREVIEW_DELAY_MS);
    const firstSrc = iframe.src;

    showPreview('v2', 'Doc B', 100, 100);
    vi.advanceTimersByTime(PREVIEW_DELAY_MS);
    expect(iframe.src).not.toBe(firstSrc);
    expect(iframe.src).toContain('pdf/v2');
  });
});

describe('PDF Hover Preview — attachPreview wiring', () => {
  beforeEach(() => { setupDOM(); vi.useFakeTimers(); });
  afterEach(() => { document.body.innerHTML = ''; vi.useRealTimers(); });

  it('shows preview when mouseenter fires on wired element', () => {
    const { tooltip, attachPreview, PREVIEW_DELAY_MS } = buildPreviewModule();

    const el = document.createElement('div');
    document.body.appendChild(el);
    attachPreview(el, 'vXYZ', 'Test Title');

    el.dispatchEvent(new MouseEvent('mouseenter', { clientX: 200, clientY: 200, bubbles: true }));
    vi.advanceTimersByTime(PREVIEW_DELAY_MS);

    expect(tooltip.classList.contains('visible')).toBe(true);
  });

  it('hides preview when mouseleave fires on wired element', () => {
    const { tooltip, attachPreview, PREVIEW_DELAY_MS } = buildPreviewModule();

    const el = document.createElement('div');
    document.body.appendChild(el);
    attachPreview(el, 'vXYZ', 'Test Title');

    el.dispatchEvent(new MouseEvent('mouseenter', { clientX: 200, clientY: 200, bubbles: true }));
    vi.advanceTimersByTime(PREVIEW_DELAY_MS);
    expect(tooltip.classList.contains('visible')).toBe(true);

    el.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true }));
    vi.advanceTimersByTime(200);
    expect(tooltip.classList.contains('visible')).toBe(false);
  });
});

describe('PDF Preview & macOS Quick Look — Live Component Tests', () => {
  let fs;
  let pdfPreviewCode;

  beforeEach(async () => {
    fs = await import('fs');
    pdfPreviewCode = fs.readFileSync('src/api/static/js/pdf-preview.js', 'utf-8');

    document.body.innerHTML = `
      <div id="pdf-preview-tooltip" style="width:380px;height:520px;opacity:0;">
        <div class="preview-header" id="pdf-preview-title">Preview</div>
        <iframe id="pdf-preview-iframe" src="about:blank"></iframe>
      </div>
      <div id="quick-look-modal" class="hidden">
        <span id="quick-look-title"></span>
        <span id="doc-inspector-subtitle"></span>
        <span id="quick-look-badge" class="hidden"></span>
        <span id="doc-inspector-tenant-val"></span>
        <span id="doc-inspector-category-val"></span>
        <span id="doc-inspector-date-val"></span>
        <span id="doc-inspector-pages-val"></span>
        <span id="doc-inspector-manual-badge" class="hidden"></span>
        <span id="doc-inspector-vault-id"></span>
        <span id="doc-inspector-batch"></span>
        <span id="doc-inspector-cat-text"></span>
        <span id="doc-inspector-tenant-text"></span>
        <textarea id="doc-inspector-notes-input"></textarea>
        <span id="doc-inspector-notes-status"></span>
        <button id="doc-inspector-save-notes-btn"></button>
        <div id="doc-inspector-pages-section" class="hidden">
          <div id="doc-inspector-pages-list"></div>
        </div>
        <button id="quick-look-close"></button>
        <button id="quick-look-open-full"></button>
      </div>
      <div id="card-1" class="group/doc" data-vault-id="vault99">
        <div class="flex items-center gap-2 min-w-0">
          <span class="doc-icon-preview">Icon</span>
          <span class="truncate">Contract 2026</span>
        </div>
        <div class="flex items-center gap-1 flex-shrink-0">
          <button class="doc-menu-btn">Menu</button>
        </div>
      </div>
    `;

    // Stub offsetWidth/Height on tooltip
    const tooltip = document.getElementById('pdf-preview-tooltip');
    Object.defineProperty(tooltip, 'offsetWidth',  { configurable: true, get: () => 380 });
    Object.defineProperty(tooltip, 'offsetHeight', { configurable: true, get: () => 520 });

    vi.useFakeTimers();

    // Execute live component in window context
    const runFn = new Function(pdfPreviewCode);
    runFn();
    window.initPdfPreview();
  });

  afterEach(() => {
    document.body.innerHTML = '';
    vi.useRealTimers();
  });

  it('triggers right-panel live peek on element mouseenter after delay', () => {
    let peeked = null;
    window.peekDocument = (vaultId, title) => { peeked = { vaultId, title }; };

    const card = document.getElementById('card-1');
    window.attachPreview(card, 'vault123', 'Sample Doc');
    card.dispatchEvent(new MouseEvent('mouseenter'));
    expect(peeked).toBe(null);

    vi.advanceTimersByTime(window.PEEK_DELAY_MS || 250);
    expect(peeked).toEqual({ vaultId: 'vault123', title: 'Sample Doc' });
  });

  it('cancels pending live peek when window scrolls', () => {
    let peeked = null;
    window.peekDocument = (vaultId, title) => { peeked = { vaultId, title }; };

    const card = document.getElementById('card-1');
    window.attachPreview(card, 'vault123', 'Sample Doc');
    card.dispatchEvent(new MouseEvent('mouseenter'));

    window.dispatchEvent(new Event('scroll'));
    vi.advanceTimersByTime(window.PEEK_DELAY_MS || 250);
    expect(peeked).toBe(null);
  });

  it('cancels pending live peek when Escape key is pressed', () => {
    let peeked = null;
    window.peekDocument = (vaultId, title) => { peeked = { vaultId, title }; };

    const card = document.getElementById('card-1');
    window.attachPreview(card, 'vault123', 'Sample Doc');
    card.dispatchEvent(new MouseEvent('mouseenter'));

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    vi.advanceTimersByTime(window.PEEK_DELAY_MS || 250);
    expect(peeked).toBe(null);
  });

  it('opens and closes Document Inspector modal via Spacebar', () => {
    const modal = document.getElementById('quick-look-modal');
    const qlTitle = document.getElementById('quick-look-title');
    const vaultIdEl = document.getElementById('doc-inspector-vault-id');

    const card = document.getElementById('card-1');
    window.setSelectedDoc({ vault_id: 'vault99', filename: 'Contract.pdf', notes: 'Initial note' }, 'Contract 2026', card);

    expect(card.classList.contains('doc-row-selected')).toBe(true);
    expect(modal.classList.contains('hidden')).toBe(true);

    // Press Space to open Inspector
    document.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', code: 'Space', bubbles: true }));
    expect(modal.classList.contains('hidden')).toBe(false);
    expect(qlTitle.textContent).toBe('Contract 2026');
    expect(vaultIdEl.textContent).toBe('vault99');
    expect(document.getElementById('doc-inspector-notes-input').value).toBe('Initial note');

    // Press Space again to close Inspector
    document.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', code: 'Space', bubbles: true }));
    expect(modal.classList.contains('hidden')).toBe(true);
  });

  it('closes Quick Look modal when Escape is pressed', () => {
    const modal = document.getElementById('quick-look-modal');
    window.openQuickLook('v77', 'Notice.pdf');
    expect(modal.classList.contains('hidden')).toBe(false);

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    expect(modal.classList.contains('hidden')).toBe(true);
  });

  it('does NOT trigger Spacebar Quick Look when user is typing in an input field', () => {
    const modal = document.getElementById('quick-look-modal');
    window.setSelectedDoc({ vault_id: 'v1' }, 'Test Doc');

    const input = document.createElement('input');
    document.body.appendChild(input);
    input.focus();

    input.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', code: 'Space', bubbles: true }));
    expect(modal.classList.contains('hidden')).toBe(true);
  });

  it('hides hover preview on menu button hover', () => {
    let peeked = null;
    window.peekDocument = (vaultId, title) => { peeked = { vaultId, title }; };

    const card = document.getElementById('card-1');
    window.attachPreview(card, 'vault123', 'Sample Doc');
    card.dispatchEvent(new MouseEvent('mouseenter'));
    window.cancelPeek();
    vi.advanceTimersByTime(300);
    expect(peeked).toBe(null);
  });

  it('calls peekDocument in the right panel after hover delay elapses', () => {
    let peeked = null;
    window.peekDocument = (vaultId, title) => { peeked = { vaultId, title }; };

    const card = document.getElementById('card-1');
    window.attachPreview(card, 'vault999', 'Title Deed 2026');

    card.dispatchEvent(new MouseEvent('mouseenter'));
    expect(peeked).toBe(null);

    vi.advanceTimersByTime(window.PEEK_DELAY_MS || 250);
    expect(peeked).toEqual({ vaultId: 'vault999', title: 'Title Deed 2026' });
  });

  it('cancels live peek when mouse leaves before delay', () => {
    let peeked = null;
    window.peekDocument = (vaultId, title) => { peeked = { vaultId, title }; };

    const card = document.getElementById('card-1');
    window.attachPreview(card, 'vault999', 'Title Deed 2026');

    card.dispatchEvent(new MouseEvent('mouseenter'));
    vi.advanceTimersByTime(100);
    card.dispatchEvent(new MouseEvent('mouseleave'));
    vi.advanceTimersByTime(250);

    expect(peeked).toBe(null);
  });

  it('updates document card in DOM with yellow highlight and Note badge when notes are saved', () => {
    const card = document.getElementById('card-1');
    expect(card.classList.contains('border-l-amber-400')).toBe(false);
    expect(card.querySelector('.doc-note-badge')).toBe(null);

    // Call updateDocRowInDOM directly with notes
    window.updateDocRowInDOM('vault99', 'Important lease agreement note');

    expect(card.classList.contains('border-l-amber-400')).toBe(true);
    expect(card.classList.contains('bg-amber-50/80')).toBe(true);
    const badge = card.querySelector('.doc-note-badge');
    expect(badge).not.toBe(null);
    expect(badge.textContent).toContain('Important leas');
    expect(badge.getAttribute('title')).toBe('Important lease agreement note');

    // Removing notes removes the highlight and badge
    window.updateDocRowInDOM('vault99', '');
    expect(card.classList.contains('border-l-amber-400')).toBe(false);
    expect(card.querySelector('.doc-note-badge')).toBe(null);
  });

  it('does NOT close inspector modal when Spacebar is typed inside notes textarea', () => {
    const modal = document.getElementById('quick-look-modal');
    window.openQuickLook('vault99', 'Contract 2026');
    expect(modal.classList.contains('hidden')).toBe(false);

    const textarea = document.getElementById('doc-inspector-notes-input');
    textarea.focus();

    // Fire Spacebar event inside the focused textarea
    const spaceEvt = new KeyboardEvent('keydown', { key: ' ', code: 'Space', bubbles: true });
    textarea.dispatchEvent(spaceEvt);

    // Modal should remain open for typing!
    expect(modal.classList.contains('hidden')).toBe(false);
  });

  it('auto-expands category folder when category contains a noted document', async () => {
    const fs = await import('fs');
    const catCode = fs.readFileSync('src/api/static/js/categories-view.js', 'utf-8');

    // Scaffold list container
    const listEl = document.createElement('div');
    listEl.id = 'document-list';
    document.body.appendChild(listEl);

    // Define currentCategories with 2 categories: one without notes, one with notes
    window.currentCategories = [
      {
        tenant: 'Tenant A',
        name: '01 - Personal',
        document_count: 1,
        documents: [{ vault_id: 'doc1', brief_arabic_title: 'Doc 1', notes: '' }]
      },
      {
        tenant: 'Tenant A',
        name: '02 - Contracts',
        document_count: 1,
        documents: [{ vault_id: 'doc2', brief_arabic_title: 'Doc 2', notes: 'Urgent renewal needed' }]
      }
    ];
    window.currentTenant = 'Tenant A';
    window.isStaticMode = false;

    // Run categories-view component
    const runCat = new Function(catCode);
    runCat();
    window.renderCategories();

    const folderCards = listEl.querySelectorAll('.category-folder-card');
    expect(folderCards.length).toBe(2);

    // Folder 1 (no notes) should be hidden/minimized
    const folder1Docs = folderCards[0].querySelector('.category-docs');
    expect(folder1Docs.classList.contains('hidden')).toBe(true);

    // Folder 2 (has noted doc) should be AUTO-EXPANDED (not hidden!)
    const folder2Docs = folderCards[1].querySelector('.category-docs');
    expect(folder2Docs.classList.contains('hidden')).toBe(false);

    // Inside folder 2, doc2 must have yellow highlight and Note badge
    const doc2El = folder2Docs.querySelector('[data-vault-id="doc2"]');
    expect(doc2El.classList.contains('border-l-amber-400')).toBe(true);
    expect(doc2El.querySelector('.doc-note-badge')).not.toBe(null);
  });

  it('renders single (i) icon on the left before document title, and none before 3-dots on right', async () => {
    const fs = await import('fs');
    const catCode = fs.readFileSync('src/api/static/js/categories-view.js', 'utf-8');
    const timeCode = fs.readFileSync('src/api/static/js/timeline-view.js', 'utf-8');

    // 1. Check Categories View
    const catListEl = document.createElement('div');
    catListEl.id = 'document-list';
    document.body.innerHTML = '';
    document.body.appendChild(catListEl);

    window.currentCategories = [
      {
        tenant: 'Tenant 1',
        name: '05 - عقود',
        document_count: 1,
        documents: [{ vault_id: 'doc_cat_1', brief_arabic_title: 'عقد إيجار شقة', notes: '' }]
      }
    ];
    window.currentTenant = 'Tenant 1';
    new Function(catCode)();
    window.renderCategories();

    const docRow = catListEl.querySelector('[data-vault-id="doc_cat_1"]');
    expect(docRow).not.toBe(null);

    // Verify left section has the (i) icon before the title
    const leftContainer = docRow.querySelector('.flex.items-center.gap-2.min-w-0');
    expect(leftContainer).not.toBe(null);
    const leftInfoIcon = leftContainer.querySelector('.doc-icon-preview');
    expect(leftInfoIcon).not.toBe(null);
    expect(leftInfoIcon.title).toContain('Spacebar');

    // Verify right section has ONLY the 3-dots button and NO info icon
    const rightContainer = docRow.querySelector('.flex.items-center.gap-1.flex-shrink-0');
    expect(rightContainer).not.toBe(null);
    expect(rightContainer.querySelectorAll('.doc-icon-preview').length).toBe(0);
    expect(rightContainer.querySelector('.doc-menu-btn')).not.toBe(null);
    // Total info icons on this row must be EXACTLY 1 (on left)
    expect(docRow.querySelectorAll('.doc-icon-preview').length).toBe(1);

    // 2. Check Timeline View
    const timeListEl = document.createElement('div');
    timeListEl.id = 'document-list';
    document.body.innerHTML = '';
    document.body.appendChild(timeListEl);

    window.currentTimeline = [
      { vault_id: 'doc_time_1', primary_tenant: 'Tenant 1', dates: ['2026-01-01'], brief_arabic_title: 'خطاب صيانة', notes: '' }
    ];
    new Function(timeCode)();
    window.renderTimeline();

    const timeCard = timeListEl.querySelector('[data-vault-id="doc_time_1"]');
    expect(timeCard).not.toBe(null);
    // Left title group has (i) preview
    const topLeftGroup = timeCard.querySelector('.flex.items-start.gap-1\\.5.min-w-0');
    expect(topLeftGroup).not.toBe(null);
    expect(topLeftGroup.querySelector('.doc-icon-preview')).not.toBe(null);

    // Right group has ONLY menu btn (and badges) and NO info icon
    const topRightGroup = timeCard.querySelector('.flex.items-center.gap-1.flex-shrink-0');
    expect(topRightGroup).not.toBe(null);
    expect(topRightGroup.querySelectorAll('.doc-icon-preview').length).toBe(0);
    expect(topRightGroup.querySelector('.doc-menu-btn')).not.toBe(null);
    // Exactly one info icon per card
    expect(timeCard.querySelectorAll('.doc-icon-preview').length).toBe(1);
  });

  it('displays note snippet (first characters) in note badge with full note in title attribute', async () => {
    const fs = await import('fs');
    const apiCode = fs.readFileSync('src/api/static/js/api.js', 'utf-8');
    const catCode = fs.readFileSync('src/api/static/js/categories-view.js', 'utf-8');
    new Function(apiCode)();

    const listEl = document.createElement('div');
    listEl.id = 'document-list';
    document.body.innerHTML = '';
    document.body.appendChild(listEl);

    window.currentCategories = [
      {
        tenant: 'Tenant 1',
        name: '01 - Personal',
        document_count: 2,
        documents: [
          { vault_id: 'doc_short', brief_arabic_title: 'Short Note Doc', notes: 'Paid in cash' },
          { vault_id: 'doc_long', brief_arabic_title: 'Long Note Doc', notes: 'Urgent contract amendment required before end of month' }
        ]
      }
    ];
    window.currentTenant = 'Tenant 1';
    new Function(catCode)();
    window.renderCategories();

    const shortBadge = listEl.querySelector('[data-vault-id="doc_short"] .doc-note-badge');
    expect(shortBadge).not.toBe(null);
    expect(shortBadge.textContent).toBe('📝 Paid in cash');
    expect(shortBadge.getAttribute('title')).toBe('Paid in cash');

    const longBadge = listEl.querySelector('[data-vault-id="doc_long"] .doc-note-badge');
    expect(longBadge).not.toBe(null);
    // Truncated snippet with ellipsis
    expect(longBadge.textContent).toBe('📝 Urgent contrac…');
    // Full note retained in title
    expect(longBadge.getAttribute('title')).toBe('Urgent contract amendment required before end of month');
  });

  it('populateFolderOptions excludes deleted/empty custom folders (document_count === 0)', async () => {
    const fs = await import('fs');
    const docMgrCode = fs.readFileSync('src/api/static/js/doc-manager.js', 'utf-8');

    document.body.innerHTML = `
      <select id="doc-modal-folder-select"></select>
      <div id="doc-custom-folder-container" class="hidden"></div>
      <input id="doc-custom-folder-input" />
    `;

    new Function(docMgrCode)();

    // currentCategories has standard folders, an active custom folder, and a deleted/empty custom folder '14-test'
    window.currentCategories = [
      { name: '05 - عقود', document_count: 3 },
      { name: '14 - ActiveCustom', document_count: 2 },
      { name: '14-test', document_count: 0 } // Deleted / empty custom folder!
    ];

    window.populateFolderOptions('05 - عقود');

    const selectEl = document.getElementById('doc-modal-folder-select');
    const optionValues = Array.from(selectEl.options).map(o => o.value);

    // Standard folders must be present
    expect(optionValues).toContain('01 - بيانات أساسية');
    expect(optionValues).toContain('05 - عقود');

    // Active custom folder must be present
    expect(optionValues).toContain('14 - ActiveCustom');

    // Deleted/empty custom folder '14-test' must NOT be present!
    expect(optionValues).not.toContain('14-test');
  });
});
