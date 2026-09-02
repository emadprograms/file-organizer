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
    const pdfUrl = `/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/pdf/${vaultId}#view=FitH`;

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

  it('sets correct PDF URL on the iframe', () => {
    const { iframe, showPreview, PREVIEW_DELAY_MS } = buildPreviewModule();
    showPreview('abc123', 'My Doc', 100, 100, 'Eastside', '55 - House');
    vi.advanceTimersByTime(PREVIEW_DELAY_MS);
    expect(iframe.src).toContain('/api/areas/Eastside/houses/55%20-%20House/pdf/abc123');
    expect(iframe.src).toContain('#view=FitH');
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
