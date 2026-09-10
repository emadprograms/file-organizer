import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('House Profile & Archive ZIP Export', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="document-list"></div>
      <div id="stats-badge"></div>
    `;

    window.isStaticMode = false;
    window.showToast = vi.fn();

    const scriptCode = fs.readFileSync(
      path.resolve(__dirname, '../../../src/api/static/js/house-profile.js'),
      'utf8'
    );
    eval(scriptCode);
  });

  afterEach(() => {
    document.body.innerHTML = '';
    vi.restoreAllMocks();
  });

  it('renders house profile with export ZIP button', () => {
    const mockProfile = {
      area_id: 'Area A',
      house_id: 'House 100',
      tenants: [
        {
          name: 'Tenant A',
          is_active: true,
          duration_str_ar: '2024 (مستمر)',
          category_count: 2,
          document_count: 5
        }
      ],
      archive: {
        total_documents: 10,
        total_pages: 25,
        timespan_str_ar: '2020 – 2024',
        categories: [
          { category: 'عقود', document_count: 6 },
          { category: 'فواتير', document_count: 4 }
        ]
      }
    };

    window.renderHouseProfile(mockProfile);

    const exportBtn = document.getElementById('btn-export-house-zip');
    expect(exportBtn).not.toBeNull();
    expect(exportBtn.textContent).toContain('تحميل أرشيف المنزل');

    exportBtn.click();
    expect(window.showToast).toHaveBeenCalledWith(
      expect.stringContaining('تحميل الأرشيف'),
      'success'
    );
  });
});
