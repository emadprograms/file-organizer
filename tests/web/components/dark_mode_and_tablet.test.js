import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Dark Mode & Tablet Overhaul - Design System & Styling Architecture', () => {
  const cssPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/css/styles.css');
  const htmlPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/index.html');
  const cssContent = fs.readFileSync(cssPath, 'utf8');
  const htmlContent = fs.readFileSync(htmlPath, 'utf8');

  describe('1. Semantic Palette Tokens & Surface Elevation', () => {
    it('defines semantic CSS design tokens for root and dark mode in styles.css', () => {
      expect(cssContent).toContain(':root');
      expect(cssContent).toContain('--surface-canvas');
      expect(cssContent).toContain('--surface-panel');
      expect(cssContent).toContain('--surface-card');
      expect(cssContent).toContain('--border-default');
      expect(cssContent).toContain('--text-primary');

      expect(cssContent).toContain('html.dark {');
      expect(cssContent).toContain('--surface-canvas: #080c14');
      expect(cssContent).toContain('--surface-card: #111827');
      expect(cssContent).toContain('--border-default: #1e293b');
      expect(cssContent).toContain('--text-primary: #f8fafc');
    });

    it('enforces deep dark slate canvas for body, panels, and sidebars in dark mode', () => {
      expect(cssContent).toMatch(/html\.dark\s+body\s*\{[^}]*background-color:\s*#080c14/);
      expect(cssContent).toMatch(/html\.dark\s+#main-sidebar\s*\{[^}]*background-color:\s*#0b0f19/);
      expect(cssContent).toMatch(/html\.dark\s+#top-navbar\s*\{[^}]*backdrop-filter:\s*blur\(12px\)/);
      expect(cssContent).toMatch(/html\.dark\s+#document-list-panel\s*\{[^}]*background-color:\s*#0d121f/);
      expect(cssContent).toMatch(/html\.dark\s+#area-grid-panel,\s*html\.dark\s+#database-inspector-panel/);
    });

    it('provides multi-level surface elevation with rim lighting on dark cards and panels', () => {
      expect(cssContent).toContain('box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.4), inset 0 1px 0 0 rgba(255, 255, 255, 0.04);');
      expect(cssContent).toContain('html.dark .house-card');
      expect(cssContent).toContain('html.dark .tenant-profile-card');
      expect(cssContent).toContain('html.dark .category-folder-card');
    });
  });

  describe('2. Elimination of Crude/Naive Overrides & Opacity Support', () => {
    it('provides dedicated dark background colors for translucent utility variants', () => {
      // Handles bg-slate-50 opacity variants
      expect(cssContent).toContain('html.dark .bg-slate-50\\/40');
      expect(cssContent).toContain('html.dark .bg-slate-50\\/50');
      expect(cssContent).toContain('html.dark .bg-slate-50\\/70');
      expect(cssContent).toContain('html.dark .bg-slate-50\\/80');

      // Handles bg-white opacity variants
      expect(cssContent).toContain('html.dark .bg-white\\/90');
      expect(cssContent).toContain('html.dark .bg-white\\/95');

      // Handles bg-slate-200 capsule variants
      expect(cssContent).toContain('html.dark .bg-slate-200\\/60');
      expect(cssContent).toContain('html.dark .bg-slate-200\\/80');
    });

    it('ensures dividing lines render with dark borders rather than blinding white rules', () => {
      expect(cssContent).toContain('html.dark .divide-slate-100 > * + *');
      expect(cssContent).toContain('html.dark .divide-slate-200 > * + *');
      expect(cssContent).toContain('html.dark .border-slate-100');
      expect(cssContent).toContain('html.dark .border-slate-200');
    });

    it('maintains accessible text contrast ratios in dark mode', () => {
      expect(cssContent).toMatch(/html\.dark\s+\.text-slate-900\s*\{[^}]*color:\s*#f8fafc/);
      expect(cssContent).toMatch(/html\.dark\s+\.text-slate-800\s*\{[^}]*color:\s*#f1f5f9/);
      expect(cssContent).toMatch(/html\.dark\s+\.text-slate-700\s*\{[^}]*color:\s*#e2e8f0/);
      expect(cssContent).toMatch(/html\.dark\s+\.text-slate-600\s*\{[^}]*color:\s*#cbd5e1/);
      expect(cssContent).toMatch(/html\.dark\s+\.text-slate-500\s*\{[^}]*color:\s*#94a3b8/);
    });
  });

  describe('3. Harmonized Status Badges & Tenure Palette (Non-Blinding)', () => {
    it('harmonizes Emerald status badges and tenure cards (< 5y) with muted dark backgrounds and vibrant indicators', () => {
      expect(cssContent).toContain('html.dark .bg-emerald-50');
      expect(cssContent).toContain('html.dark .bg-emerald-100');
      expect(cssContent).toContain('html.dark .border-emerald-200');
      expect(cssContent).toContain('html.dark .border-emerald-300');
      expect(cssContent).toContain('html.dark .text-emerald-700');
      expect(cssContent).toMatch(/html\.dark\s+\.text-emerald-600,\s*html\.dark\s+\.text-emerald-700,\s*html\.dark\s+\.text-emerald-800\s*\{[^}]*color:\s*#34d399\s*!important/);
    });

    it('harmonizes Amber status badges, tenure cards (5–10y), pinned badges, and sticky notes', () => {
      expect(cssContent).toContain('html.dark .bg-amber-50');
      expect(cssContent).toContain('html.dark .bg-amber-100');
      expect(cssContent).toContain('html.dark .border-amber-200');
      expect(cssContent).toContain('html.dark .border-amber-300');
      expect(cssContent).toMatch(/html\.dark\s+\.text-amber-700,\s*html\.dark\s+\.text-amber-800,\s*html\.dark\s+\.text-amber-900\s*\{[^}]*color:\s*#fbbf24\s*!important/);
      expect(cssContent).toContain('html.dark .doc-pinned-badge');
      expect(cssContent).toContain('html.dark .doc-note-badge');
      expect(cssContent).toContain('html.dark .bg-amber-50\\/80.border-l-4.border-l-amber-400');
    });

    it('harmonizes Rose status badges and tenure cards (> 10y, vacated, errors) with refined dark ruby styling', () => {
      expect(cssContent).toContain('html.dark .bg-rose-50');
      expect(cssContent).toContain('html.dark .bg-rose-100');
      expect(cssContent).toContain('html.dark .border-rose-200');
      expect(cssContent).toContain('html.dark .border-rose-300');
      expect(cssContent).toMatch(/html\.dark\s+\.text-rose-600,\s*html\.dark\s+\.text-rose-700,\s*html\.dark\s+\.text-rose-800\s*\{[^}]*color:\s*#fb7185\s*!important/);
    });

    it('harmonizes Purple applicant badges and cards with elegant dark violet styling', () => {
      expect(cssContent).toContain('html.dark .bg-purple-50');
      expect(cssContent).toContain('html.dark .bg-purple-100');
      expect(cssContent).toContain('html.dark .border-purple-200');
      expect(cssContent).toMatch(/html\.dark\s+\.text-purple-600,\s*html\.dark\s+\.text-purple-700,\s*html\.dark\s+\.text-purple-800\s*\{[^}]*color:\s*#c084fc\s*!important/);
    });

    it('harmonizes Blue folder icons, stats badges, and count pills with glowing dark sapphire styling', () => {
      expect(cssContent).toContain('html.dark .folder-icon-box');
      expect(cssContent).toContain('html.dark #stats-badge');
      expect(cssContent).toContain('html.dark #grid-area-stats');
      expect(cssContent).toMatch(/html\.dark\s+\.text-blue-600,\s*html\.dark\s+\.text-blue-700\s*\{[^}]*color:\s*#60a5fa\s*!important/);
    });

    it('harmonizes neutral badges (dates, counts, inactive)', () => {
      expect(cssContent).toContain('html.dark .doc-date-badge');
      expect(cssContent).toContain('html.dark .doc-count-badge');
      expect(cssContent).toContain('html.dark .tenants-count');
    });
  });

  describe('4. Hover States (No Pastel/White Flash)', () => {
    it('prevents glaring white or light flashes when hovering over buttons, cards, and list rows in dark mode', () => {
      expect(cssContent).toContain('html.dark .hover\\:bg-slate-50:hover');
      expect(cssContent).toContain('html.dark .hover\\:bg-slate-100:hover');
      expect(cssContent).toContain('html.dark .hover\\:bg-blue-50:hover');
      expect(cssContent).toContain('html.dark .hover\\:bg-emerald-50:hover');
      expect(cssContent).toContain('html.dark .hover\\:bg-amber-50:hover');
      expect(cssContent).toContain('html.dark .hover\\:bg-rose-50:hover');
      expect(cssContent).toContain('html.dark .hover\\:bg-purple-50:hover');
      expect(cssContent).toContain('html.dark .hover\\:border-slate-300:hover');
    });
  });

  describe('5. Segmented Tabs in Dark Mode', () => {
    it('styles active tab with distinct elevated dark surface and active blue text', () => {
      expect(cssContent).toMatch(/html\.dark\s+#tab-categories\.bg-white,\s*html\.dark\s+#tab-timeline\.bg-white\s*\{[^}]*background-color:\s*#1e293b\s*!important/);
      expect(cssContent).toMatch(/html\.dark\s+#tab-categories\.bg-white,\s*html\.dark\s+#tab-timeline\.bg-white\s*\{[^}]*color:\s*#60a5fa\s*!important/);
    });

    it('styles inactive tabs with muted text that brightens on hover', () => {
      expect(cssContent).toMatch(/html\.dark\s+#tab-categories:not\(\.bg-white\),\s*html\.dark\s+#tab-timeline:not\(\.bg-white\)\s*\{[^}]*color:\s*#94a3b8\s*!important/);
      expect(cssContent).toMatch(/html\.dark\s+#tab-categories:not\(\.bg-white\):hover,\s*html\.dark\s+#tab-timeline:not\(\.bg-white\):hover\s*\{[^}]*color:\s*#f1f5f9\s*!important/);
    });
  });

  describe('6. Modals, Dialogs & Form Controls', () => {
    it('styles modal dialog cards with 3D elevation and backdrop blur in dark mode', () => {
      expect(cssContent).toMatch(/html\.dark\s+\.bg-slate-900\\\/60,\s*html\.dark\s+\.bg-slate-900\\\/50\s*\{[^}]*backdrop-filter:\s*blur\(8px\)/);
      expect(cssContent).toContain('html.dark #quick-look-modal > div');
      expect(cssContent).toContain('html.dark #tenant-modal > div');
      expect(cssContent).toContain('html.dark #delete-house-modal > div');
      expect(cssContent).toContain('html.dark #add-house-modal > div');
      expect(cssContent).toContain('html.dark #export-archive-modal > div');
    });

    it('styles modal headers, footers, close buttons, and secondary cancel buttons in dark mode', () => {
      expect(cssContent).toContain('html.dark #tenant-modal-cancel');
      expect(cssContent).toContain('html.dark #delete-house-cancel');
      expect(cssContent).toContain('html.dark #btn-add-house-cancel');
      expect(cssContent).toContain('html.dark #btn-cancel-export-archive');
      expect(cssContent).toContain('html.dark #tenant-modal-close');
      expect(cssContent).toContain('html.dark #shortcuts-modal-close');
    });

    it('styles form inputs, selects, textareas, and keyboard shortcuts kbd elements in dark mode', () => {
      expect(cssContent).toMatch(/html\.dark\s+input:not\(\[type="checkbox"\]\):not\(\[type="radio"\]\),\s*html\.dark\s+select,\s*html\.dark\s+textarea\s*\{[^}]*background-color:\s*#090d16\s*!important/);
      expect(cssContent).toContain('html.dark kbd');
      expect(cssContent).toContain('html.dark input::placeholder');
    });
  });

  describe('7. Database Inspector & Data Tables', () => {
    it('provides dark table head, zebra alternating rows, row hover, and cell borders', () => {
      expect(cssContent).toContain('html.dark #db-data-table');
      expect(cssContent).toContain('html.dark #db-data-table thead');
      expect(cssContent).toContain('html.dark #db-data-table thead th');
      expect(cssContent).toContain('html.dark #db-data-table tbody tr:nth-child(even)');
      expect(cssContent).toContain('html.dark #db-data-table tbody tr:nth-child(odd)');
      expect(cssContent).toContain('html.dark #db-data-table tbody tr:hover');
      expect(cssContent).toContain('html.dark #db-data-table td');
      expect(cssContent).toContain('html.dark #db-table-tabs button');
    });
  });

  describe('8. PDF Viewer & Canvas Treatment', () => {
    it('styles PDF canvas container and page wrappers with soft dark bezels to eliminate glare', () => {
      expect(cssContent).toMatch(/html\.dark\s+#pdf-canvas-container\s*\{[^}]*background-color:\s*#080c14\s*!important/);
      expect(cssContent).toContain('html.dark .pdf-page-wrapper');
      expect(cssContent).toContain('box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.7)');
    });
  });

  describe('9. Tablet & Touchscreen Responsive Architecture (iPad 768px – 1024px)', () => {
    it('defines tablet viewport media query with fluid navbar trigger scaling and balanced 2-column grid', () => {
      expect(cssContent).toContain('@media (min-width: 768px) and (max-width: 1024px)');
      expect(cssContent).toContain('#btn-search-trigger');
      expect(cssContent).toContain('max-width: 210px !important');
      expect(cssContent).toContain('#area-grid-container');
      expect(cssContent).toContain('grid-template-columns: repeat(2, minmax(0, 1fr)) !important');
    });

    it('provides enhanced card surface depth and rim lighting for high-DPI retina tablet screens', () => {
      expect(cssContent).toContain('box-shadow: 0 4px 14px -2px rgba(0, 0, 0, 0.5), inset 0 1px 0 0 rgba(255, 255, 255, 0.06) !important;');
    });

    it('provides gentle tap feedback on touchscreens and smooth momentum scrolling', () => {
      expect(cssContent).toContain('transform: scale(0.985)');
      expect(cssContent).toContain('-webkit-overflow-scrolling: touch');
      expect(cssContent).toContain('overscroll-behavior-y: contain');
    });
  });

  describe('10. HTML Template Structure Verification', () => {
    it('verifies index.html body has dark mode background transition classes', () => {
      expect(htmlContent).toContain('dark:bg-slate-950');
      expect(htmlContent).toContain('dark:text-slate-100');
    });

    it('verifies index.html top navbar has dark background and dark border', () => {
      const topNavbarMatch = htmlContent.match(/id="top-navbar"[^>]*class="([^"]*)"/);
      expect(topNavbarMatch).not.toBeNull();
      expect(topNavbarMatch[1]).toContain('dark:bg-slate-900/90');
      expect(topNavbarMatch[1]).toContain('dark:border-slate-800');
    });

    it('verifies index.html area-grid-panel and database-inspector-panel have dark mode background classes', () => {
      expect(htmlContent).toContain('id="area-grid-panel" class="flex-1 p-6 bg-slate-50 dark:bg-slate-950');
      expect(htmlContent).toContain('id="database-inspector-panel" class="flex-1 p-6 bg-slate-50 dark:bg-slate-950');
    });

    it('verifies index.html document-list-panel has dark mode surface classes', () => {
      expect(htmlContent).toContain('id="document-list-panel" class="bg-white dark:bg-slate-900');
    });
  });

  describe('11. House Card Duration Indicator Left Border Preservation in Dark Mode', () => {
    it('does NOT set shorthand border-color on html.dark .house-card or html.dark .house-card:hover so single-side duration borders are never clobbered', () => {
      const cardRuleMatch = cssContent.match(/html\.dark\s+\.house-card\s*\{([^}]*)\}/);
      expect(cardRuleMatch).not.toBeNull();
      const cardBlock = cardRuleMatch ? cardRuleMatch[1] : '';
      expect(cardBlock).not.toMatch(/(^|;|\s)border-color:/);
      expect(cardBlock).toContain('border-top-color: #1e293b;');
      expect(cardBlock).toContain('border-right-color: #1e293b;');
      expect(cardBlock).toContain('border-bottom-color: #1e293b;');

      const hoverRuleMatch = cssContent.match(/html\.dark\s+\.house-card:hover\s*\{([^}]*)\}/);
      expect(hoverRuleMatch).not.toBeNull();
      const hoverBlock = hoverRuleMatch ? hoverRuleMatch[1] : '';
      expect(hoverBlock).not.toMatch(/(^|;|\s)border-color:/);
      expect(hoverBlock).toContain('border-top-color: #3b82f6;');
      expect(hoverBlock).toContain('border-right-color: #3b82f6;');
      expect(hoverBlock).toContain('border-bottom-color: #3b82f6;');
    });

    it('asserts house cards retain emerald duration indicator border (#047857) for < 5y in dark mode at rest and on hover', () => {
      expect(cssContent).toMatch(/html\.dark\s+\.house-card\.border-l-emerald-500,\s*html\.dark\s+\.house-card\.border-l-emerald-500:hover,\s*html\.dark\s+\.border-l-emerald-500\s*\{[^}]*border-left-color:\s*#047857\s*!important/);
    });

    it('asserts house cards retain amber duration indicator border (#b45309) for 5-10y in dark mode at rest and on hover', () => {
      expect(cssContent).toMatch(/html\.dark\s+\.house-card\.border-l-amber-500,\s*html\.dark\s+\.house-card\.border-l-amber-500:hover,\s*html\.dark\s+\.border-l-amber-500\s*\{[^}]*border-left-color:\s*#b45309\s*!important/);
    });

    it('asserts house cards retain rose duration indicator border (#b91c1c) for > 10y in dark mode at rest and on hover', () => {
      expect(cssContent).toMatch(/html\.dark\s+\.house-card\.border-l-rose-500,\s*html\.dark\s+\.house-card\.border-l-rose-500:hover,\s*html\.dark\s+\.border-l-rose-500\s*\{[^}]*border-left-color:\s*#b91c1c\s*!important/);
    });

    it('asserts house cards retain slate indicator border (#475569) for vacant houses in dark mode at rest and on hover', () => {
      expect(cssContent).toMatch(/html\.dark\s+\.house-card\.border-l-slate-300,\s*html\.dark\s+\.house-card\.border-l-slate-300:hover,\s*html\.dark\s+\.house-card\.dark\\:border-l-slate-600,\s*html\.dark\s+\.house-card\.dark\\:border-l-slate-600:hover,\s*html\.dark\s+\.border-l-slate-300,\s*html\.dark\s+\.dark\\:border-l-slate-600\s*\{[^}]*border-left-color:\s*#475569\s*!important/);
    });

    it('styles border-rose-200/80 in dark mode for long duration tenant list items inside cards', () => {
      expect(cssContent).toMatch(/html\.dark\s+\.border-rose-200,\s*html\.dark\s+\.border-rose-200\\\/80\s*\{[^}]*border-color:\s*rgba\(244,\s*63,\s*94,\s*0\.28\)\s*!important/);
    });
  });
});
