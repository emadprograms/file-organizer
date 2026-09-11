import { describe, it, expect, beforeEach } from 'vitest';

const {
    getFolderIconSvg,
    FOLDER_ICONS,
    EMPTY_FOLDER_SVG,
    renderCategories,
} = require('../../../src/api/static/js/categories-view.js');

function extractPathD(svgHtml) {
    const match = svgHtml.match(/d="([^"]+)"/);
    return match ? match[1] : '';
}

describe('Category Folder Icons (01-13 descriptive, 14+ empty folder)', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="document-list"></div>
        `;
        global.currentArea = 'Safra C';
        global.currentHouse = '514';
        global.currentTab = 'categories';
    });

    it('defines unique, valid SVG icons for all standard folders 01 through 13', () => {
        const standardPrefixes = [
            '01', '02', '03', '04', '05', '06',
            '07', '08', '09', '10', '11', '12', '13'
        ];

        standardPrefixes.forEach(prefix => {
            const svg = FOLDER_ICONS[prefix];
            expect(svg).toBeDefined();
            expect(svg).toContain('<svg');
            expect(svg).toContain('</svg>');
            expect(svg).not.toBe(EMPTY_FOLDER_SVG);
        });

        // Ensure all 13 icons are distinct
        const iconValues = standardPrefixes.map(p => FOLDER_ICONS[p]);
        const uniqueValues = new Set(iconValues);
        expect(uniqueValues.size).toBe(13);
    });

    it('returns the correct descriptive icon for standard folders with numeric prefixes', () => {
        expect(getFolderIconSvg('01 - بيانات أساسية')).toBe(FOLDER_ICONS['01']);
        expect(getFolderIconSvg('02 - بيانات شخصية')).toBe(FOLDER_ICONS['02']);
        expect(getFolderIconSvg('03 - أمر تخصيص')).toBe(FOLDER_ICONS['03']);
        expect(getFolderIconSvg('04 - محضر تسليم مفتاح')).toBe(FOLDER_ICONS['04']);
        expect(getFolderIconSvg('05 - عقود')).toBe(FOLDER_ICONS['05']);
        expect(getFolderIconSvg('06 - كهرباء وماء')).toBe(FOLDER_ICONS['06']);
        expect(getFolderIconSvg('07 - استقطاع إيجار')).toBe(FOLDER_ICONS['07']);
        expect(getFolderIconSvg('08 - وقف استقطاع بدل')).toBe(FOLDER_ICONS['08']);
        expect(getFolderIconSvg('09 - إشعارات')).toBe(FOLDER_ICONS['09']);
        expect(getFolderIconSvg('10 - صيانة')).toBe(FOLDER_ICONS['10']);
        expect(getFolderIconSvg('11 - صور ومعاينات')).toBe(FOLDER_ICONS['11']);
        expect(getFolderIconSvg('12 - تعديلات')).toBe(FOLDER_ICONS['12']);
        expect(getFolderIconSvg('13 - رسائل متنوعة')).toBe(FOLDER_ICONS['13']);
    });

    it('returns the correct descriptive icon for standard folders without numeric prefix', () => {
        expect(getFolderIconSvg('بيانات أساسية')).toBe(FOLDER_ICONS['01']);
        expect(getFolderIconSvg('بيانات شخصية')).toBe(FOLDER_ICONS['02']);
        expect(getFolderIconSvg('أمر تخصيص')).toBe(FOLDER_ICONS['03']);
        expect(getFolderIconSvg('محضر تسليم مفتاح')).toBe(FOLDER_ICONS['04']);
        expect(getFolderIconSvg('عقود')).toBe(FOLDER_ICONS['05']);
        expect(getFolderIconSvg('كهرباء وماء')).toBe(FOLDER_ICONS['06']);
        expect(getFolderIconSvg('استقطاع إيجار')).toBe(FOLDER_ICONS['07']);
        expect(getFolderIconSvg('وقف استقطاع بدل')).toBe(FOLDER_ICONS['08']);
        expect(getFolderIconSvg('إشعارات')).toBe(FOLDER_ICONS['09']);
        expect(getFolderIconSvg('صيانة')).toBe(FOLDER_ICONS['10']);
        expect(getFolderIconSvg('صور ومعاينات')).toBe(FOLDER_ICONS['11']);
        expect(getFolderIconSvg('تعديلات')).toBe(FOLDER_ICONS['12']);
        expect(getFolderIconSvg('رسائل متنوعة')).toBe(FOLDER_ICONS['13']);
    });

    it('returns empty folder icon for custom folders 14 onwards and user-created categories', () => {
        expect(getFolderIconSvg('14 - تصاريح بناء')).toBe(EMPTY_FOLDER_SVG);
        expect(getFolderIconSvg('15 - فواتير ومطالبات')).toBe(EMPTY_FOLDER_SVG);
        expect(getFolderIconSvg('20 - مستندات قانونية')).toBe(EMPTY_FOLDER_SVG);
        expect(getFolderIconSvg('مجلد مخصص')).toBe(EMPTY_FOLDER_SVG);
        expect(getFolderIconSvg('')).toBe(EMPTY_FOLDER_SVG);
        expect(getFolderIconSvg(null)).toBe(EMPTY_FOLDER_SVG);
    });

    it('renders descriptive icons on category cards in renderCategories for 01-13 and empty folder for 14+', () => {
        const testCategories = [
            { name: '01 - بيانات أساسية', document_count: 1, documents: [] },
            { name: '04 - محضر تسليم مفتاح', document_count: 2, documents: [] },
            { name: '10 - صيانة', document_count: 1, documents: [] },
            { name: '14 - تصاريح بناء', document_count: 3, documents: [] },
        ];

        window.currentCategories = testCategories;
        global.currentCategories = testCategories;

        renderCategories();

        const cards = document.querySelectorAll('.category-folder-card');
        expect(cards.length).toBe(4);

        // Card 0: 01 - بيانات أساسية
        const iconBox0 = cards[0].querySelector('.folder-icon-box');
        expect(iconBox0).not.toBeNull();
        expect(iconBox0.querySelector('path').getAttribute('d')).toBe(extractPathD(FOLDER_ICONS['01']));

        // Card 1: 04 - محضر تسليم مفتاح
        const iconBox1 = cards[1].querySelector('.folder-icon-box');
        expect(iconBox1).not.toBeNull();
        expect(iconBox1.querySelector('path').getAttribute('d')).toBe(extractPathD(FOLDER_ICONS['04']));

        // Card 2: 10 - صيانة
        const iconBox2 = cards[2].querySelector('.folder-icon-box');
        expect(iconBox2).not.toBeNull();
        expect(iconBox2.querySelector('path').getAttribute('d')).toBe(extractPathD(FOLDER_ICONS['10']));

        // Card 3: 14 - تصاريح بناء (custom folder)
        const iconBox3 = cards[3].querySelector('.folder-icon-box');
        expect(iconBox3).not.toBeNull();
        expect(iconBox3.querySelector('path').getAttribute('d')).toBe(extractPathD(EMPTY_FOLDER_SVG));
    });

    it('renders descriptive icons on category cards in renderCategories for all 13 standard folders and empty folder for custom folders', () => {
        const categoryNames = [
            '01 - بيانات أساسية',
            '02 - بيانات شخصية',
            '03 - أمر تخصيص',
            '04 - محضر تسليم مفتاح',
            '05 - عقود',
            '06 - كهرباء وماء',
            '07 - استقطاع إيجار',
            '08 - وقف استقطاع بدل',
            '09 - إشعارات',
            '10 - صيانة',
            '11 - صور ومعاينات',
            '12 - تعديلات',
            '13 - رسائل متنوعة',
            '14 - تصاريح بناء',
            '15 - فواتير ومطالبات'
        ];

        const testCategories = categoryNames.map(name => ({
            name,
            document_count: 1,
            documents: []
        }));

        window.currentCategories = testCategories;
        global.currentCategories = testCategories;

        renderCategories();

        const cards = document.querySelectorAll('.category-folder-card');
        expect(cards.length).toBe(15);

        for (let i = 0; i < 13; i++) {
            const prefix = String(i + 1).padStart(2, '0');
            const iconBox = cards[i].querySelector('.folder-icon-box');
            expect(iconBox, `Card ${categoryNames[i]} missing icon box`).not.toBeNull();
            expect(iconBox.querySelector('path').getAttribute('d')).toBe(extractPathD(FOLDER_ICONS[prefix]));
        }

        // Custom folders 14 and 15
        const iconBox14 = cards[13].querySelector('.folder-icon-box');
        expect(iconBox14.querySelector('path').getAttribute('d')).toBe(extractPathD(EMPTY_FOLDER_SVG));

        const iconBox15 = cards[14].querySelector('.folder-icon-box');
        expect(iconBox15.querySelector('path').getAttribute('d')).toBe(extractPathD(EMPTY_FOLDER_SVG));
    });
});
