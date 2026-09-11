import { describe, it, expect, beforeEach, vi } from 'vitest';

const { renderTimeline } = require('../../../src/api/static/js/timeline-view.js');

describe('Timeline View - Smaller Pinned Badge (QCK-21)', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="document-list"></div>
            <div id="stats-badge" class="hidden"></div>
        `;
        global.currentTenant = null;
        global.currentTimeline = [];
    });

    it('renders smaller emoji and text for pinned document in timeline', () => {
        const mockDocs = [
            {
                vault_id: 'doc_pinned_1',
                brief_arabic_title: 'عقد إيجار موثق',
                dates: ['2024-01-15'],
                primary_tenant: 'Tenant A',
                category: '01 - عقود',
                is_manual: 1
            }
        ];

        renderTimeline(mockDocs);

        const badge = document.querySelector('.doc-pinned-badge');
        expect(badge).not.toBeNull();
        expect(badge.textContent).toContain('Pinned');
        expect(badge.textContent).toContain('🔒');

        // Verify smaller text sizing on container
        expect(badge.className).toContain('text-[8.5px]');
        expect(badge.className).toContain('font-medium');

        // Verify smaller emoji sizing inside child span
        const emojiSpan = badge.querySelector('span');
        expect(emojiSpan).not.toBeNull();
        expect(emojiSpan.textContent).toBe('🔒');
        expect(emojiSpan.className).toContain('text-[8px]');
    });

    it('does not render pinned badge for non-pinned documents', () => {
        const mockDocs = [
            {
                vault_id: 'doc_unpinned_1',
                brief_arabic_title: 'فاتورة كهرباء',
                dates: ['2024-02-10'],
                primary_tenant: 'Tenant B',
                category: '06 - فواتير',
                is_manual: 0
            }
        ];

        renderTimeline(mockDocs);

        const badge = document.querySelector('.doc-pinned-badge');
        expect(badge).toBeNull();
    });

    it('handles mixed timeline documents correctly', () => {
        const mockDocs = [
            {
                vault_id: 'doc_pinned',
                brief_arabic_title: 'مستند مثبت',
                dates: ['2024-03-01'],
                is_manual: 1
            },
            {
                vault_id: 'doc_auto',
                brief_arabic_title: 'مستند تلقائي',
                dates: ['2024-03-02'],
                is_manual: 0
            }
        ];

        renderTimeline(mockDocs);

        const badges = document.querySelectorAll('.doc-pinned-badge');
        expect(badges.length).toBe(1);

        const cards = document.querySelectorAll('#document-list > div');
        expect(cards[0].querySelector('.doc-pinned-badge')).not.toBeNull();
        expect(cards[1].querySelector('.doc-pinned-badge')).toBeNull();
    });
});
