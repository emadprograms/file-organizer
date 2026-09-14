import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Light Mode Eye Comfort & Anti-Glare Calibration', () => {
  const srcCssPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/css/styles.css');
  const distCssPath = path.resolve(__dirname, '../../../dist/win-x64/wwwroot/css/styles.css');
  const cssContent = fs.readFileSync(srcCssPath, 'utf8');
  const distCssContent = fs.readFileSync(distCssPath, 'utf8');

  describe('1. Calibrated Light Mode Surface Tokens in :root', () => {
    it('defines anti-glare, softened surface and border tokens in :root', () => {
      expect(cssContent).toContain(':root');
      expect(cssContent).toMatch(/--surface-canvas:\s*#edf0f5;/);
      expect(cssContent).toMatch(/--surface-panel:\s*#f6f8fb;/);
      expect(cssContent).toMatch(/--surface-card:\s*#f9fafb;/);
      expect(cssContent).toMatch(/--surface-elevated:\s*#ffffff;/);
      expect(cssContent).toMatch(/--surface-hover:\s*#eef2f6;/);
      expect(cssContent).toMatch(/--border-subtle:\s*#e2e8f0;/);
      expect(cssContent).toMatch(/--border-default:\s*#cbd5e1;/);
      expect(cssContent).toMatch(/--border-emphasis:\s*#94a3b8;/);
      expect(cssContent).toMatch(/--text-primary:\s*#0f172a;/);
      expect(cssContent).toMatch(/--text-secondary:\s*#334155;/);
      expect(cssContent).toMatch(/--text-muted:\s*#64748b;/);
    });
  });

  describe('2. Scoped html:not(.dark) Surface Calibration Rules', () => {
    it('softens light mode body and utility slate surfaces to eliminate blinding glare', () => {
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+body\s*\{[^}]*background-color:\s*#edf0f5;/);
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+\.bg-slate-50\s*\{[^}]*background-color:\s*#edf0f5;/);
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+\.bg-slate-100\s*\{[^}]*background-color:\s*#e4e8ef;/);
    });

    it('softens pure white backgrounds and white opacity variants in light mode', () => {
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+\.bg-white\s*\{[^}]*background-color:\s*#f8fafc;/);
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+\.bg-white\\\/90\s*\{[^}]*background-color:\s*rgba\(248,\s*250,\s*252,\s*0\.92\);/);
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+\.bg-white\\\/95\s*\{[^}]*background-color:\s*rgba\(248,\s*250,\s*252,\s*0\.96\);/);
    });

    it('applies calibrated backgrounds and borders to main navigation and content panels', () => {
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+#top-navbar\s*\{[^}]*background-color:\s*rgba\(248,\s*250,\s*252,\s*0\.92\);[^}]*border-color:\s*#e2e8f0;/);
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+#document-list-panel\s*\{[^}]*background-color:\s*#f5f7fa;[^}]*border-color:\s*#e2e8f0;/);
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+#area-grid-panel,\s*html:not\(\.dark\)\s+#database-inspector-panel\s*\{[^}]*background-color:\s*#edf0f5;/);
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+#document-viewer-panel\s*\{[^}]*background-color:\s*#e8ecf2;/);
    });

    it('ensures input fields and text controls retain crisp white backgrounds for legibility', () => {
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+input:not\(\[type="checkbox"\]\):not\(\[type="radio"\]\),\s*html:not\(\.dark\)\s+select,\s*html:not\(\.dark\)\s+textarea\s*\{[^}]*background-color:\s*#ffffff;/);
    });

    it('applies crisp white contrast override with !important for active segmented tabs', () => {
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+#tab-categories\.bg-white,\s*html:not\(\.dark\)\s+#tab-timeline\.bg-white\s*\{[^}]*background-color:\s*#ffffff\s*!important;/);
    });

    it('styles house cards and category folder cards with soft off-white surface and refined shadows', () => {
      expect(cssContent).toMatch(/html:not\(\.dark\)\s+\.house-card,\s*html:not\(\.dark\)\s+\.category-folder-card\s*\{[^}]*background-color:\s*#fbfcfd;/);
      expect(cssContent).toContain('box-shadow: 0 1px 2px 0 rgba(15, 23, 42, 0.04), 0 0 0 1px rgba(226, 232, 240, 0.8);');
      expect(cssContent).toContain('box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.07), 0 2px 4px -2px rgba(15, 23, 42, 0.05);');
    });
  });

  describe('3. Dark Mode Protection (Dark Rules Intact & Unaffected)', () => {
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

  describe('4. Parity Between Source and Dist Stylesheets', () => {
    it('ensures dist/win-x64/wwwroot/css/styles.css is an exact 100% mirror of src/HousingApplication.Web/wwwroot/css/styles.css', () => {
      expect(distCssContent).toBe(cssContent);
    });
  });
});
