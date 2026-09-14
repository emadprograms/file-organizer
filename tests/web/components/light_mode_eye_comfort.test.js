import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Light Mode Eye Comfort & Card Border Preservation', () => {
  const srcCssPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/css/styles.css');
  const distCssPath = path.resolve(__dirname, '../../../dist/win-x64/wwwroot/css/styles.css');
  const cssContent = fs.readFileSync(srcCssPath, 'utf8');
  const distCssContent = fs.readFileSync(distCssPath, 'utf8');

  describe('1. Calibrated Light Mode Surface Tokens in :root', () => {
    it('defines anti-glare, softened surface and delicate border tokens in :root', () => {
      expect(cssContent).toContain(':root');
      expect(cssContent).toMatch(/--surface-canvas:\s*#edf0f4;/);
      expect(cssContent).toMatch(/--surface-panel:\s*#f7f9fb;/);
      expect(cssContent).toMatch(/--surface-card:\s*#f7f9fb;/);
      expect(cssContent).toMatch(/--surface-elevated:\s*#ffffff;/);
      expect(cssContent).toMatch(/--surface-hover:\s*#edf2f7;/);
      expect(cssContent).toMatch(/--border-subtle:\s*#edf0f4;/);
      expect(cssContent).toMatch(/--border-default:\s*#e2e8f0;/);
      expect(cssContent).toMatch(/--border-emphasis:\s*#cbd5e1;/);
      expect(cssContent).toMatch(/--text-primary:\s*#0f172a;/);
      expect(cssContent).toMatch(/--text-secondary:\s*#334155;/);
      expect(cssContent).toMatch(/--text-muted:\s*#64748b;/);
    });
  });

  describe('2. Scoped html:not(.dark) Surface Calibration Rules', () => {
    it('softens light mode body and content panels to calm neutral canvas (#edf0f4) to eliminate glare', () => {
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+body\s*\{[^}]*background-color:\s*#edf0f4;/);
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+#area-grid-panel,\s*html:not\(\.dark\)\s+#database-inspector-panel,\s*html:not\(\.dark\)\s+#welcome-panel\s*\{[^}]*background-color:\s*#edf0f4;/);
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+#document-viewer-panel\s*\{[^}]*background-color:\s*#edf0f4;/);
    });

    it('preserves clean utility classes for buttons and badges without dark grey overrides', () => {
      expect(cssContent).not.toMatch(/html:not\(\.dark\)\s+\.bg-slate-50\s*\{[^}]*background-color:\s*#edf0f5;/);
      expect(cssContent).not.toMatch(/html:not\(\.dark\)\s+\.bg-slate-100\s*\{[^}]*background-color:\s*#e4e8ef;/);
    });

    it('applies calibrated soft-white background (#f7f9fb) and delicate borders to navbar and document list panels', () => {
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+#top-navbar\s*\{[^}]*background-color:\s*rgba\(247,\s*249,\s*251,\s*0\.94\);[^}]*border-color:\s*#e2e8f0;/);
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+#document-list-panel\s*\{[^}]*background-color:\s*#f7f9fb;[^}]*border-color:\s*#e2e8f0;/);
    });

    it('ensures input fields and text controls retain clean white backgrounds and delicate borders', () => {
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+input:not\(\[type="checkbox"\]\):not\(\[type="radio"\]\),\s*html:not\(\.dark\)\s+select,\s*html:not\(\.dark\)\s+textarea\s*\{[^}]*background-color:\s*#ffffff;[^}]*border-color:\s*#e2e8f0;/);
    });

    it('applies clean white background with subtle shadow for active segmented tabs', () => {
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+#tab-categories\.bg-white,\s*html:not\(\.dark\)\s+#tab-timeline\.bg-white\s*\{[^}]*background-color:\s*#ffffff\s*!important;/);
    });

    it('provides vibrant and delicate selection highlight for document rows and text selection', () => {
      expect(cssContent).toContain('.doc-row-selected {');
      expect(cssContent).toMatch(/\.doc-row-selected\s*\{[^}]*background-color:\s*#eff6ff\s*!important;/);
      expect(cssContent).toMatch(/\.doc-row-selected\s*\{[^}]*border-color:\s*#93c5fd\s*!important;/);
      expect(cssContent).toContain('::selection {');
    });
  });

  describe('3. House Card Colored Indicator Border Preservation', () => {
    it('sets soft white background (#f7f9fb) on cards for glare reduction without stark pure white or dull grey', () => {
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+\.house-card,\s*html:not\(\.dark\)\s+\.category-folder-card\s*\{[^}]*background-color:\s*#f7f9fb;/);
    });

    it('STRICTLY DOES NOT set border-color on html:not(.dark) .house-card or .category-folder-card so tenure stripes are preserved', () => {
      // Find the rule blocks for light mode house-card and category-folder-card
      const cardRuleMatch = cssContent.match(/html:not\(\.dark\)\s+\.house-card,\s*html:not\(\.dark\)\s+\.category-folder-card\s*\{([^}]*)\}/);
      expect(cardRuleMatch).not.toBeNull();
      const cardBlock = cardRuleMatch ? cardRuleMatch[1] : '';
      expect(cardBlock).not.toContain('border-color');

      const hoverRuleMatch = cssContent.match(/html:not\(\.dark\)\s+\.house-card:hover,\s*html:not\(\.dark\)\s+\.category-folder-card:hover\s*\{([^}]*)\}/);
      expect(hoverRuleMatch).not.toBeNull();
      const hoverBlock = hoverRuleMatch ? hoverRuleMatch[1] : '';
      expect(hoverBlock).not.toContain('border-color');
    });

    it('ensures no dark box-shadow rings are present on cards in light mode', () => {
      expect(cssContent).not.toContain('0 0 0 1px rgba(226, 232, 240, 0.8)');
      expect(cssContent).toContain('box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.02);');
      expect(cssContent).toContain('box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -2px rgba(0, 0, 0, 0.04);');
    });
  });

  describe('4. Dark Mode Protection (Dark Rules Intact & Unaffected)', () => {
    it('verifies html.dark tokens remain untouched', () => {
      expect(cssContent).toContain('html.dark {');
      expect(cssContent).toContain('--surface-canvas: #080c14');
      expect(cssContent).toContain('--surface-panel: #0c101c');
      expect(cssContent).toContain('--surface-card: #111827');
      expect(cssContent).toContain('--surface-elevated: #162036');
      expect(cssContent).toContain('--surface-hover: #17223b');
      expect(cssContent).toContain('--border-subtle: #172033');
      expect(cssContent).toContain('--border-default: #1e293b');
      expect(cssContent).toContain('--border-emphasis: #2b3952');
      expect(cssContent).toContain('--text-primary: #f8fafc');
    });

    it('verifies dark mode body, navbar, and panels remain strictly untouched', () => {
      expect(cssContent).toMatch(/html\.dark\s+body\s*\{[^}]*background-color:\s*#080c14;/);
      expect(cssContent).toMatch(/html\.dark\s+#top-navbar\s*\{[^}]*background-color:\s*rgba\(12,\s*16,\s*28,\s*0\.88\);/);
      expect(cssContent).toMatch(/html\.dark\s+#document-list-panel\s*\{[^}]*background-color:\s*#0d121f;/);
      expect(cssContent).toMatch(/html\.dark\s+#tab-categories\.bg-white,\s*html\.dark\s+#tab-timeline\.bg-white\s*\{[^}]*background-color:\s*#1e293b\s*!important;/);
    });
  });

  describe('5. Parity Between Source and Dist Stylesheets', () => {
    it('ensures dist/win-x64/wwwroot/css/styles.css is an exact 100% mirror of src/HousingApplication.Web/wwwroot/css/styles.css', () => {
      expect(distCssContent).toBe(cssContent);
    });
  });
});
