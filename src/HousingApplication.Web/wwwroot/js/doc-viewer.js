// ── Document Viewer Component ─────────────────────────────────────────────
(function() {
    let currentPinnedDoc = null;
    let currentPdfDoc = null;
    let currentPdfUrl = null;
    let currentScale = 1.0;
    let currentScaleMode = 'fit'; // 'fit' or 'manual'
    let currentLoadingTask = null;

    // ── Offline English Translation Knowledge Base & Engine ──────────────
    const CATEGORY_TRANSLATIONS = {
        '01 - بيانات أساسية': { en: 'Basic Application Details', icon: '📝' },
        '02 - بيانات شخصية': { en: 'Personal Identity & CPR Documents', icon: '🪪' },
        '03 - أمر تخصيص': { en: 'Housing Allocation Order', icon: '🏛️' },
        '04 - محضر تسليم مفتاح': { en: 'Key Handover Minutes', icon: '🔑' },
        '05 - عقود': { en: 'Lease & Tenancy Contract', icon: '📜' },
        '06 - كهرباء وماء': { en: 'Electricity & Water (EWA) Utility Bill', icon: '⚡' },
        '07 - استقطاع إيجار': { en: 'Rent Deduction Notice', icon: '💳' },
        '08 - وقف استقطاع بدل': { en: 'Stop Housing Allowance Deduction Request', icon: '🛑' },
        '09 - إشعارات': { en: 'Official Notices & Eviction Warnings', icon: '⚠️' },
        '10 - صيانة': { en: 'Maintenance & Repair Request', icon: '🔧' },
        '11 - صور ومعاينات': { en: 'Site Inspection Report & Photos', icon: '📷' },
        '12 - تعديلات': { en: 'Housing Renovation & Modifications', icon: '🏗️' },
        '13 - رسائل متنوعة': { en: 'Official Correspondence & Letters', icon: '✉️' }
    };

    const ARABIC_PHRASES = [
        { ar: 'مكتب وكيل وزارة الداخلية', en: 'Office of the Undersecretary of the Ministry of Interior' },
        { ar: 'لجنة دراسة الخدمات الإسكانية للسادة الضباط والرتب الأخرى', en: 'Housing Services Committee for Officers and Other Ranks' },
        { ar: 'لجنة دراسة الخدمات الإسكانية للضباط', en: 'Housing Services Committee for Officers' },
        { ar: 'لجنة دراسة الخدمات الإسكانية', en: 'Housing Services Committee' },
        { ar: 'الوكيل المساعد للشئون الإدارية', en: 'Assistant Undersecretary for Administrative Affairs' },
        { ar: 'وكيل وزارة الداخلية', en: 'Undersecretary of the Ministry of Interior' },
        { ar: 'إدارة الإمداد والتنوين', en: 'Directorate of Supply and Catering' },
        { ar: 'إدارة الإمداد والتموين', en: 'Directorate of Supply and Catering' },
        { ar: 'إدارة المحاكم العسكرية', en: 'Directorate of Military Courts' },
        { ar: 'هيئة الكهرباء والماء', en: 'Electricity & Water Authority (EWA)' },
        { ar: 'فرع إسكان الشرطة', en: 'Police Housing Branch' },
        { ar: 'فرع القضايا العامة', en: 'General Cases Branch' },
        { ar: 'رئاسة الأمن العام', en: 'Public Security Headquarters' },
        { ar: 'وزارة الداخلية', en: 'Ministry of Interior' },
        { ar: 'القيادة العامة', en: 'General Command' },
        { ar: 'مملكة البحرين', en: 'Kingdom of Bahrain' },
        { ar: 'شئون الجمارك', en: 'Customs Affairs' },
        { ar: 'الوكيل المساعد', en: 'Assistant Undersecretary' },
        { ar: 'وكيل الوزارة', en: 'Undersecretary of the Ministry' },
        { ar: 'إشعار بإخلاء الوحدة السكنية', en: 'Housing Unit Eviction Notice' },
        { ar: 'إشعارات الإخلاء', en: 'Eviction Notices' },
        { ar: 'إشعارات إخلاء', en: 'Eviction Notices' },
        { ar: 'إشعار إخلاء', en: 'Eviction Notice' },
        { ar: 'إقرار إخلاء وحدة سكنية', en: 'Housing Unit Evacuation Undertaking' },
        { ar: 'إقرار إخلاء', en: 'Evacuation Undertaking' },
        { ar: 'إقرار وتعهد', en: 'Declaration and Undertaking' },
        { ar: 'طلب الانتفاع بالوحدة السكنية', en: 'Application to Benefit from Housing Unit' },
        { ar: 'طلب انتفاع بالمسكن', en: 'Housing Occupancy Application' },
        { ar: 'طلب انتفاع', en: 'Housing Beneficiary Application' },
        { ar: 'المخالفين لنظام الانتفاع', en: 'Violators of Housing Occupancy Regulations' },
        { ar: 'مخالفي نظام الانتفاع', en: 'Housing Occupancy Regulation Violators' },
        { ar: 'نظام الانتفاع بالوحدات السكنية', en: 'Housing Occupancy Regulations' },
        { ar: 'محضر تسليم مفتاح', en: 'Key Handover Minutes' },
        { ar: 'محضر تسليم', en: 'Handover Minutes' },
        { ar: 'محضر استلام', en: 'Handover Confirmation Record' },
        { ar: 'محضر اجتماع', en: 'Minutes of Meeting' },
        { ar: 'أمر تخصيص مسكن', en: 'Housing Allocation Order' },
        { ar: 'أمر تخصيص', en: 'Housing Allocation Order' },
        { ar: 'طلب صيانة وإصلاح', en: 'Maintenance & Repair Request' },
        { ar: 'طلب صيانة', en: 'Maintenance Request' },
        { ar: 'عقد إيجار موثق', en: 'Notarized Tenancy Contract' },
        { ar: 'عقد إيجار', en: 'Lease & Tenancy Contract' },
        { ar: 'فاتورة كهرباء وماء', en: 'Electricity & Water Utility Bill' },
        { ar: 'فاتورة كهرباء', en: 'Electricity Bill' },
        { ar: 'فاتورة ماء', en: 'Water Bill' },
        { ar: 'فاتورة استهلاك', en: 'Utility Consumption Bill' },
        { ar: 'استقطاع إيجار شهري', en: 'Monthly Rent Deduction' },
        { ar: 'استقطاع إيجار', en: 'Rent Deduction Notice' },
        { ar: 'وقف استقطاع بدل سكن', en: 'Stop Housing Allowance Deduction Request' },
        { ar: 'وقف بدل سكن', en: 'Stop Housing Allowance Request' },
        { ar: 'سري للغاية وعاجل جداً', en: 'Top Secret and Most Urgent' },
        { ar: 'سري للغاية وعاجل', en: 'Top Secret and Urgent' },
        { ar: 'سري وعاجل', en: 'Confidential and Urgent' },
        { ar: 'عاجل وسري', en: 'Urgent and Confidential' },
        { ar: 'سري للغاية', en: 'Top Secret' },
        { ar: 'عاجل جداً', en: 'Most Urgent' },
        { ar: 'سري', en: 'Confidential' },
        { ar: 'عاجل', en: 'Urgent' },
        { ar: 'وثيقة رسمية صادرة من', en: 'Official document issued by' },
        { ar: 'وثيقة رسمية صادرة عن', en: 'Official document issued by' },
        { ar: 'وثيقة رسمية', en: 'Official document' },
        { ar: 'خطاب رسمي صادر من', en: 'Official letter issued by' },
        { ar: 'خطاب رسمي صادر عن', en: 'Official letter issued by' },
        { ar: 'خطاب رسمي', en: 'Official letter' },
        { ar: 'يحتوي المستند على', en: 'This document contains' },
        { ar: 'يوثق المستند', en: 'This document records' },
        { ar: 'هذا المستند عبارة عن', en: 'This document is' },
        { ar: 'نرفق لسعادتكم', en: 'Enclosed for Your Excellency' },
        { ar: 'الموضوع يتضمن', en: 'The subject entails' },
        { ar: 'الموضوع:', en: 'Subject:' },
        { ar: 'الموضوع', en: 'Subject' },
        { ar: 'بخصوص', en: 'regarding' },
        { ar: 'برقم صادر', en: 'with outgoing reference' },
        { ar: 'برقم قيد', en: 'with registration number' },
        { ar: 'برقم', en: 'under reference' },
        { ar: 'بتاريخ', en: 'dated' },
        { ar: 'الموافق', en: 'corresponding to' },
        { ar: 'المؤرخ في', en: 'dated' },
        { ar: 'موجه إلى', en: 'addressed to' },
        { ar: 'موجهة إلى', en: 'addressed to' },
        { ar: 'موجهة من', en: 'issued by' },
        { ar: 'موجه من', en: 'issued by' },
        { ar: 'صادر من', en: 'issued from' },
        { ar: 'صادر عن', en: 'issued by' },
        { ar: 'الوحدة السكنية رقم', en: 'housing unit no.' },
        { ar: 'الوحدة السكنية', en: 'housing unit' },
        { ar: 'وحدة سكنية', en: 'housing unit' },
        { ar: 'المسكن رقم', en: 'house no.' },
        { ar: 'مسكن', en: 'residence' },
        { ar: 'منطقة سافرة', en: 'Safra Area' },
        { ar: 'منطقة سافر', en: 'Safra Area' },
        { ar: 'منطقة مسافر', en: 'Saafer Area' },
        { ar: 'منطقة', en: 'area' },
        { ar: 'مجمع', en: 'block' },
        { ar: 'طريق', en: 'road' },
        { ar: 'شارع', en: 'avenue' },
        { ar: 'الطرف الأول', en: 'First Party (Lessor)' },
        { ar: 'الطرف الثاني', en: 'Second Party (Tenant)' },
        { ar: 'المستأجر', en: 'Tenant' },
        { ar: 'المؤجر', en: 'Lessor / Landlord' },
        { ar: 'قيمة الإيجار الشهري', en: 'Monthly Rental Value' },
        { ar: 'الإيجار الشهري', en: 'Monthly Rent' },
        { ar: 'مدة العقد', en: 'Contract Duration' },
        { ar: 'تاريخ بدء العقد', en: 'Contract Start Date' },
        { ar: 'تاريخ انتهاء العقد', en: 'Contract End Date' },
        { ar: 'توقيع', en: 'Signature' },
        { ar: 'ختم', en: 'Official Stamp' },
        { ar: 'اعتماد', en: 'Approval' },
        { ar: 'مرفقات', en: 'Attachments' },
        { ar: 'نسخة إلى', en: 'Copy to' },
        { ar: 'إقرار', en: 'Declaration / Acknowledgment' },
        { ar: 'فريق أول', en: 'General' },
        { ar: 'فريق', en: 'Lieutenant General' },
        { ar: 'لواء', en: 'Major General' },
        { ar: 'عميد', en: 'Brigadier' },
        { ar: 'العقيد', en: 'Colonel' },
        { ar: 'عقيد', en: 'Colonel' },
        { ar: 'المقدم', en: 'Lieutenant Colonel' },
        { ar: 'مقدم', en: 'Lieutenant Colonel' },
        { ar: 'الرائد', en: 'Major' },
        { ar: 'رائد', en: 'Major' },
        { ar: 'النقيب', en: 'Captain' },
        { ar: 'نقيب', en: 'Captain' },
        { ar: 'ملازم أول', en: 'First Lieutenant' },
        { ar: 'ملازم ثاني', en: 'Second Lieutenant' },
        { ar: 'ملازم متقاعد', en: 'Retired Lieutenant' },
        { ar: 'ملازم', en: 'Lieutenant' },
        { ar: 'وكيل أول', en: 'Senior Warrant Officer' },
        { ar: 'وكيل ضابط', en: 'Warrant Officer' },
        { ar: 'رقيب أول', en: 'Master Sergeant' },
        { ar: 'رقيب', en: 'Sergeant' },
        { ar: 'العريف', en: 'Corporal' },
        { ar: 'عريف', en: 'Corporal' },
        { ar: 'شرطي أول', en: 'First Constable' },
        { ar: 'شرطي', en: 'Constable' },
        { ar: 'مدير إدارة', en: 'Director of' },
        { ar: 'مدير مكتب', en: 'Director of the Office of' },
        { ar: 'مدير', en: 'Director' },
        { ar: 'رئيس فرع', en: 'Head of Branch' },
        { ar: 'رئيس', en: 'Head' },
        { ar: 'مقرر اللجنة', en: 'Committee Rapporteur' },
        { ar: 'مقرر', en: 'Rapporteur' },
        { ar: 'الباحث القانوني', en: 'Legal Researcher' },
        { ar: 'سعادة', en: 'His Excellency' },
        { ar: 'معالي', en: 'His Excellency (Minister)' },
        { ar: 'معاليكم', en: 'Your Excellency' },
        { ar: 'المحترم', en: 'Esq.' }
    ];
    ARABIC_PHRASES.sort((a, b) => b.ar.length - a.ar.length);

    function getEnglishCategory(category) {
        if (!category || typeof category !== 'string') {
            return { en: 'Official Housing Document', icon: '📄' };
        }
        const clean = category.trim();
        if (CATEGORY_TRANSLATIONS[clean]) {
            return CATEGORY_TRANSLATIONS[clean];
        }
        for (const [key, val] of Object.entries(CATEGORY_TRANSLATIONS)) {
            if (clean.includes(key.substring(5)) || key.includes(clean)) {
                return val;
            }
        }
        return { en: translateArabicText(clean) || 'Official Housing Document', icon: '📄' };
    }

    function translateArabicText(text) {
        if (!text || typeof text !== 'string') return '';
        let result = text.trim();
        if (!result) return '';

        const arabicCharCount = (result.match(/[\u0600-\u06FF]/g) || []).length;
        const latinCharCount = (result.match(/[a-zA-Z]/g) || []).length;
        if (latinCharCount > 0 && arabicCharCount < latinCharCount) {
            return result;
        }

        for (const item of ARABIC_PHRASES) {
            if (result.includes(item.ar)) {
                result = result.replaceAll(item.ar, item.en);
            }
        }

        const arabicNumerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
        arabicNumerals.forEach((ch, idx) => {
            result = result.replaceAll(ch, String(idx));
        });

        return result.replace(/\s+/g, ' ').trim();
    }

    function escapeHtml(str) {
        if (!str || typeof str !== 'string') return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatContentParagraphs(text) {
        if (!text || typeof text !== 'string') return '<p class="italic text-slate-400">No content explanation available for this page.</p>';
        const clean = text.trim();
        if (!clean) return '<p class="italic text-slate-400">No content explanation available for this page.</p>';

        const paragraphs = clean.split(/\n\s*\n|\r\n\s*\r\n/);
        return paragraphs.map(p => {
            const pTrim = p.trim();
            if (!pTrim) return '';
            return `<p class="leading-relaxed mb-2 last:mb-0">${escapeHtml(pTrim)}</p>`;
        }).filter(Boolean).join('');
    }

    const docMetadataCache = new Map();

    async function fetchDocumentMetadata(vaultId) {
        if (!vaultId) return null;
        if (docMetadataCache.has(vaultId)) {
            return docMetadataCache.get(vaultId);
        }

        const area = (typeof currentArea !== 'undefined' ? currentArea : window.currentArea) || 'default';
        const house = (typeof currentHouse !== 'undefined' ? currentHouse : window.currentHouse) || 'default';

        let meta = null;
        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(vaultId)}/metadata`);
            if (res.ok) {
                meta = await res.json();
            }
        } catch (e) {}

        if (!meta) {
            try {
                const altRes = await fetch(`/api/documents/${encodeURIComponent(vaultId)}/metadata`);
                if (altRes.ok) {
                    meta = await altRes.json();
                }
            } catch (e) {}
        }

        if (meta) {
            docMetadataCache.set(vaultId, meta);
        }
        return meta;
    }

    let isTranslationActive = false;
    try {
        isTranslationActive = (typeof localStorage !== 'undefined') ? (localStorage.getItem('doc_viewer_translate') === 'true') : false;
    } catch (e) {}

    function updateTranslationButtonState() {
        const btn = document.getElementById('viewer-translate-btn');
        const label = document.getElementById('viewer-translate-label');
        if (!btn) return;

        if (isTranslationActive) {
            btn.classList.remove('bg-blue-950/40', 'text-blue-300', 'border-blue-600/50', 'hover:bg-blue-800/60');
            btn.classList.add('bg-blue-600', 'text-white', 'border-blue-500', 'shadow-xs', 'ring-2', 'ring-blue-400/40');
            btn.setAttribute('aria-pressed', 'true');
            btn.title = 'Translation active (English overlay enabled) — Click to view original scan • الترجمة مفعلة — انقر لإظهار المسح الأصلي';
            if (label) label.textContent = 'English (Active)';
        } else {
            btn.classList.add('bg-blue-950/40', 'text-blue-300', 'border-blue-600/50', 'hover:bg-blue-800/60');
            btn.classList.remove('bg-blue-600', 'text-white', 'border-blue-500', 'shadow-xs', 'ring-2', 'ring-blue-400/40');
            btn.setAttribute('aria-pressed', 'false');
            btn.title = 'Translate document to English (Offline) • ترجمة المستند للإنجليزية';
            if (label) label.textContent = 'English';
        }
    }

    function toggleDocumentTranslation() {
        isTranslationActive = !isTranslationActive;
        try {
            if (typeof localStorage !== 'undefined') {
                localStorage.setItem('doc_viewer_translate', isTranslationActive ? 'true' : 'false');
            }
        } catch (e) {}

        updateTranslationButtonState();

        const overlay = document.getElementById('document-translation-overlay');
        if (isTranslationActive) {
            renderDocumentTranslation();
        } else {
            if (overlay) {
                overlay.classList.add('hidden');
                overlay.classList.remove('flex');
                overlay.innerHTML = '';
            }
        }
    }

    async function renderDocumentTranslation() {
        if (!currentPinnedDoc || !currentPinnedDoc.vaultId) return;
        const vaultId = currentPinnedDoc.vaultId;

        const overlay = document.getElementById('document-translation-overlay');
        if (!overlay) return;

        overlay.classList.remove('hidden');
        overlay.classList.add('flex');

        if (!docMetadataCache.has(vaultId)) {
            overlay.innerHTML = `
                <div class="flex flex-col items-center justify-center p-8 bg-white/95 dark:bg-slate-900/95 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800 gap-3 my-auto max-w-sm text-center">
                    <svg class="w-8 h-8 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                    </svg>
                    <div class="text-sm font-semibold text-slate-800 dark:text-slate-100">Translating Document (Offline)</div>
                    <div class="text-xs text-slate-500 dark:text-slate-400">Loading intelligence record from archive database...</div>
                </div>
            `;
        }

        const meta = await fetchDocumentMetadata(vaultId);

        if (!currentPinnedDoc || currentPinnedDoc.vaultId !== vaultId || !isTranslationActive) {
            return;
        }

        overlay.innerHTML = '';

        const pages = (meta && Array.isArray(meta.pages) && meta.pages.length > 0) ? meta.pages : null;

        if (!pages) {
            const docTitle = currentPinnedDoc.title || 'Official Document';
            const catInfo = getEnglishCategory(currentPinnedDoc.category || (meta && meta.category));
            const tenant = currentPinnedDoc.tenant_name || currentPinnedDoc.tenant || (meta && meta.tenant_name) || '';
            const house = (typeof currentHouse !== 'undefined' ? currentHouse : window.currentHouse) || (meta && meta.house_id) || '';
            const date = (meta && meta.primary_date) || '';

            const fallbackCard = document.createElement('div');
            fallbackCard.className = 'translation-page-sheet relative bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-200/90 dark:border-slate-800 p-6 sm:p-8 space-y-4 text-slate-800 dark:text-slate-100 my-auto select-text';
            fallbackCard.innerHTML = `
                <div class="flex items-center justify-between gap-2 pb-3 border-b border-slate-200/80 dark:border-slate-800">
                    <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200/60 dark:border-blue-800/60">
                        <span>${catInfo.icon}</span>
                        <span>${escapeHtml(catInfo.en)}</span>
                    </span>
                    <button type="button" class="btn-peek-scan text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 flex items-center gap-1.5 transition-all cursor-pointer select-none">
                        <svg class="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                        <span>Peek Scan</span>
                    </button>
                </div>
                <div class="p-3 bg-blue-50/50 dark:bg-blue-950/20 rounded-xl border border-blue-100 dark:border-blue-900/40">
                    <span class="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider block mb-0.5">Document Title:</span>
                    <div class="text-sm font-semibold text-slate-900 dark:text-slate-100">${escapeHtml(docTitle)}</div>
                </div>
                <div class="text-xs text-slate-600 dark:text-slate-400 space-y-1.5">
                    ${house ? `<div><strong>House:</strong> ${escapeHtml(house)}</div>` : ''}
                    ${tenant ? `<div><strong>Tenant:</strong> ${escapeHtml(tenant)}</div>` : ''}
                    ${date ? `<div><strong>Date:</strong> ${escapeHtml(date)}</div>` : ''}
                </div>
                <div class="text-slate-700 dark:text-slate-300 text-sm leading-relaxed border-t border-slate-100 dark:border-slate-800 pt-3">
                    <p>This is an official document stored in the housing archive under category <strong>${escapeHtml(catInfo.en)}</strong>. Individual OCR page transcriptions are not indexed in the database for this specific file, but the full high-resolution scanned document is available beneath this overlay. Click or hold <strong>Peek Scan</strong> to examine the original scan.</p>
                </div>
            `;
            attachPeekBehavior(fallbackCard);
            overlay.appendChild(fallbackCard);
            return;
        }

        const totalPages = pages.length;
        pages.forEach((p, idx) => {
            const pageNum = p.page_number || p.pageNumber || idx + 1;
            const catInfo = getEnglishCategory(p.fine_category || p.fineCategory || (meta && meta.category) || (currentPinnedDoc && currentPinnedDoc.category));
            const dateText = p.raw_date || p.rawDate || (meta && meta.primary_date) || '';

            const origContent = p.content_explanation || p.contentExplanation || '';
            const origSubject = p.subject || '';
            const origSender = p.sender || '';
            const origReceiver = p.receiver || '';

            let contentText = '';
            if (origContent) {
                const hasEnglish = /[a-zA-Z]/.test(origContent);
                contentText = hasEnglish ? origContent : translateArabicText(origContent);
            } else {
                contentText = `Official archive record (${catInfo.en}). Associated with house ${(meta && meta.house_id) || ''}${(meta && meta.tenant_name) ? ', tenant ' + meta.tenant_name : ''}. High-resolution scan registered in archive.`;
            }

            const subjectText = origSubject ? (/[a-zA-Z]/.test(origSubject) ? origSubject : translateArabicText(origSubject)) : '';
            const senderText = origSender ? (/[a-zA-Z]/.test(origSender) ? origSender : translateArabicText(origSender)) : '';
            const receiverText = origReceiver ? (/[a-zA-Z]/.test(origReceiver) ? origReceiver : translateArabicText(origReceiver)) : '';

            const pageCard = document.createElement('div');
            pageCard.className = 'translation-page-sheet relative bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-200/90 dark:border-slate-800 p-5 sm:p-7 md:p-8 space-y-4 text-slate-800 dark:text-slate-100 select-text transition-all';
            pageCard.setAttribute('data-page-number', pageNum);

            pageCard.innerHTML = `
                <!-- Header Row -->
                <div class="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-200/80 dark:border-slate-800">
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200/60 dark:border-blue-800/60 shadow-2xs">
                            <span>${catInfo.icon}</span>
                            <span>${escapeHtml(catInfo.en)}</span>
                        </span>
                        <span class="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-mono font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                            Page ${pageNum} of ${totalPages}
                        </span>
                        ${dateText ? `
                        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                            <svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
                            <span>${escapeHtml(dateText)}</span>
                        </span>` : ''}
                    </div>
                    <div class="flex items-center gap-1.5">
                        <button type="button" class="btn-peek-scan text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 flex items-center gap-1.5 transition-all cursor-pointer select-none" title="Hold or click to peek at original Arabic scan underneath">
                            <svg class="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                            <span>Peek Scan</span>
                        </button>
                    </div>
                </div>

                <!-- Routing Block (From / To) -->
                ${(senderText || receiverText) ? `
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs bg-slate-50 dark:bg-slate-950/40 p-3 rounded-xl border border-slate-200/70 dark:border-slate-800/80">
                    ${senderText ? `
                    <div class="flex items-start gap-1.5 min-w-0">
                        <span class="font-bold text-slate-500 uppercase text-[10px] tracking-wider flex-shrink-0 mt-0.5">FROM:</span>
                        <span class="text-slate-700 dark:text-slate-200 font-medium">${escapeHtml(senderText)}</span>
                    </div>` : ''}
                    ${receiverText ? `
                    <div class="flex items-start gap-1.5 min-w-0">
                        <span class="font-bold text-slate-500 uppercase text-[10px] tracking-wider flex-shrink-0 mt-0.5">TO:</span>
                        <span class="text-slate-700 dark:text-slate-200 font-medium">${escapeHtml(receiverText)}</span>
                    </div>` : ''}
                </div>` : ''}

                <!-- Subject Block -->
                ${subjectText ? `
                <div class="p-3 bg-blue-50/50 dark:bg-blue-950/20 rounded-xl border border-blue-100 dark:border-blue-900/40">
                    <span class="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider block mb-0.5">Subject / Title:</span>
                    <div class="text-sm font-semibold text-slate-900 dark:text-slate-100">${escapeHtml(subjectText)}</div>
                </div>` : ''}

                <!-- Content Explanation / Translated Body -->
                <div class="space-y-2">
                    <span class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">Document Content & Translation:</span>
                    <div class="text-slate-700 dark:text-slate-200 text-sm sm:text-[15px] leading-relaxed space-y-2 font-normal">
                        ${formatContentParagraphs(contentText)}
                    </div>
                </div>

                <!-- Collapsible Original Arabic Record -->
                ${(origSubject || origSender || origReceiver || origContent) ? `
                <details class="group mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80">
                    <summary class="cursor-pointer text-xs font-semibold text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 flex items-center justify-between select-none">
                        <span class="flex items-center gap-1.5">
                            <svg class="w-3.5 h-3.5 text-slate-400 group-open:rotate-90 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                            <span>Original Arabic Scan Transcription</span>
                        </span>
                        <span class="text-[10px] font-mono text-slate-400">النص الأصلي</span>
                    </summary>
                    <div class="mt-2.5 p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200/60 dark:border-slate-800 font-arabic text-xs text-slate-600 dark:text-slate-400 space-y-2" dir="rtl">
                        ${origSubject ? `<div><strong class="text-slate-700 dark:text-slate-300">الموضوع:</strong> ${escapeHtml(origSubject)}</div>` : ''}
                        ${(origSender || origReceiver) ? `
                        <div class="flex flex-wrap gap-x-4 gap-y-1">
                            ${origSender ? `<div><strong class="text-slate-700 dark:text-slate-300">من:</strong> ${escapeHtml(origSender)}</div>` : ''}
                            ${origReceiver ? `<div><strong class="text-slate-700 dark:text-slate-300">إلى:</strong> ${escapeHtml(origReceiver)}</div>` : ''}
                        </div>` : ''}
                        ${origContent ? `<div class="leading-relaxed border-t border-slate-200/40 dark:border-slate-800 pt-1.5 mt-1.5">${escapeHtml(origContent)}</div>` : ''}
                    </div>
                </details>` : ''}
            `;

            attachPeekBehavior(pageCard);
            overlay.appendChild(pageCard);
        });
    }

    function attachPeekBehavior(card) {
        if (!card) return;
        card.querySelectorAll('.btn-peek-scan').forEach(btn => {
            let timeout = null;
            const startPeek = () => { card.classList.add('peeking'); };
            const stopPeek = () => {
                card.classList.remove('peeking');
                if (timeout) { clearTimeout(timeout); timeout = null; }
            };

            btn.addEventListener('pointerdown', startPeek);
            btn.addEventListener('pointerup', stopPeek);
            btn.addEventListener('pointerleave', stopPeek);
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                if (card.classList.contains('peeking')) {
                    stopPeek();
                } else {
                    startPeek();
                    timeout = setTimeout(stopPeek, 4000);
                }
            });
        });
    }


    function isVaultHashName(name) {
        if (!name || typeof name !== 'string') return false;
        const clean = name.trim();
        // Matches patterns like doc_ac132cf0...pdf, ac132cf0...pdf, or hex hash >= 16 chars
        return /^(?:doc_)?[0-9a-f]{16,}(?:\.pdf)?$/i.test(clean);
    }

    function getCleanDocTitle(doc, fallbackCategory = null) {
        if (!doc) return fallbackCategory || 'وثيقة';
        if (typeof doc === 'string') {
            return isVaultHashName(doc) ? (fallbackCategory || 'وثيقة') : doc.trim();
        }
        const arabicTitle = doc.brief_arabic_title || doc.arabic_title;
        if (arabicTitle && !isVaultHashName(arabicTitle)) {
            return arabicTitle.trim();
        }
        const title = doc.title;
        if (title && !isVaultHashName(title)) {
            return title.trim();
        }
        const filename = doc.filename || doc.file_name || doc.name;
        if (filename && !isVaultHashName(filename)) {
            return filename.trim();
        }
        const category = doc.category || doc.folder || doc.subfolder || fallbackCategory;
        if (category && typeof category === 'string' && category.trim()) {
            return category.trim();
        }
        return 'وثيقة';
    }

    function resolvePdfUrl(vaultId) {
        if (typeof getPdfUrl === 'function' && typeof currentArea !== 'undefined' && typeof currentHouse !== 'undefined') {
            return getPdfUrl(currentArea, currentHouse, vaultId);
        }
        return `/api/areas/default/houses/default/pdf/${encodeURIComponent(vaultId)}`;
    }

    function shouldUseOfficialViewer() {
        let stored = null;
        try {
            stored = (typeof localStorage !== 'undefined') ? localStorage.getItem('pdf_viewer_mode') : null;
        } catch (e) {}

        if (stored === 'tab' || stored === 'tablet' || stored === 'pdfjs' || stored === 'official' || stored === 'canvas') return true;
        if (stored === 'computer' || stored === 'native') return false;

        // In automated test runners (Playwright/Puppeteer), prefer native iframe for desktop assertions unless explicitly set
        if (typeof navigator !== 'undefined' && navigator.webdriver) {
            return false;
        }

        // Touchscreen / Tablet auto-detection:
        // Android, iOS (iPhone/iPad), tablets, or touch-first devices where iframe PDFs prompt downloads
        if (typeof navigator !== 'undefined') {
            const ua = navigator.userAgent || '';
            const isMobileUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|Tablet/i.test(ua);
            const isTouchScreen = (navigator.maxTouchPoints > 0 || (typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(pointer: coarse)').matches));
            const isIPad = /Macintosh/i.test(ua) && navigator.maxTouchPoints > 1;

            if (isMobileUA || isIPad || isTouchScreen) return true;

            // Fallback for devices without native PDF viewer plugin
            if (navigator.pdfViewerEnabled === false) return true;
        }

        // Default for computer: native iframe (ensures desktop plugins & PDF viewers work)
        return false;
    }

    function shouldUseCanvasViewer() {
        return shouldUseOfficialViewer();
    }

    function resolveViewerSrc(pdfUrl) {
        if (shouldUseOfficialViewer()) {
            return `/lib/pdfjs/web/viewer.html?file=${encodeURIComponent(pdfUrl)}`;
        }
        return pdfUrl + '#view=FitH';
    }

    function loadPdfIntoFrame(pdfFrame, pdfUrl) {
        if (!pdfFrame) return;
        const targetSrc = resolveViewerSrc(pdfUrl);

        let reusedViewer = false;
        if (shouldUseOfficialViewer()) {
            try {
                const frameWin = pdfFrame.contentWindow;
                if (frameWin && frameWin.PDFViewerApplication && frameWin.PDFViewerApplication.initialized && typeof frameWin.PDFViewerApplication.open === 'function') {
                    frameWin.PDFViewerApplication.open({ url: pdfUrl });
                    reusedViewer = true;
                }
            } catch (e) {
                reusedViewer = false;
            }
        }

        if (!reusedViewer && pdfFrame.src !== targetSrc) {
            pdfFrame.src = targetSrc;
        }
        pdfFrame.classList.remove('hidden');
    }

    function updateViewerCategory(vaultId, explicitCategory) {
        const catBadge = document.getElementById('viewer-category-badge');
        const catVal = document.getElementById('viewer-category-val');
        if (!catBadge || !catVal) return;

        let foundCategory = explicitCategory || null;

        // If doc object was passed as category
        if (foundCategory && typeof foundCategory === 'object') {
            foundCategory = foundCategory.category || foundCategory.folder || foundCategory.subfolder || null;
        }

        // 1. Try finding in currentTimeline
        if (!foundCategory && typeof currentTimeline !== 'undefined' && Array.isArray(currentTimeline)) {
            const item = currentTimeline.find(d => d && (d.vault_id === vaultId || d.id === vaultId));
            if (item && item.category) {
                foundCategory = item.category;
            }
        }

        // 2. Try finding in window.getSelectedDoc()
        if (!foundCategory && typeof window.getSelectedDoc === 'function') {
            const sel = window.getSelectedDoc();
            if (sel && (sel.vaultId === vaultId || sel.doc?.vault_id === vaultId) && sel.doc?.category) {
                foundCategory = sel.doc.category;
            }
        }

        // 3. Try finding in globalTreeData
        if (!foundCategory) {
            const tree = (typeof globalTreeData !== 'undefined' ? globalTreeData : window.globalTreeData) || [];
            const area = (typeof currentArea !== 'undefined' ? currentArea : window.currentArea);
            const house = (typeof currentHouse !== 'undefined' ? currentHouse : window.currentHouse);
            if (tree && area && house) {
                const areaNode = tree.find(a => a.name === area);
                const houseNode = areaNode?.houses?.find(h => String(h.house_number || h.name) === String(house));
                if (houseNode && houseNode.categories) {
                    for (const cat of houseNode.categories) {
                        if (cat.documents && cat.documents.some(d => (d.vault_id === vaultId || d.id === vaultId))) {
                            foundCategory = cat.name;
                            break;
                        }
                    }
                }
            }
        }

        if (foundCategory) {
            catVal.textContent = foundCategory;
            catBadge.classList.remove('hidden');
            catBadge.classList.add('flex');
        } else {
            catVal.textContent = '';
            catBadge.classList.add('hidden');
            catBadge.classList.remove('flex');

            // Asynchronous fetch from metadata API if not static mode
            if (typeof isStaticMode === 'undefined' || !isStaticMode) {
                const area = (typeof currentArea !== 'undefined' ? currentArea : window.currentArea) || 'default';
                const house = (typeof currentHouse !== 'undefined' ? currentHouse : window.currentHouse) || 'default';
                fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/documents/${encodeURIComponent(vaultId)}/metadata`)
                    .then(res => res.ok ? res.json() : null)
                    .then(meta => {
                        if (meta && meta.category && catBadge && catVal && (!currentPinnedDoc || currentPinnedDoc.vaultId === vaultId)) {
                            catVal.textContent = meta.category;
                            catBadge.classList.remove('hidden');
                            catBadge.classList.add('flex');
                        }
                    })
                    .catch(() => {});
            }
        }
    }

    async function renderPdfDocument(pdfUrl) {
        const canvasContainer = document.getElementById('pdf-canvas-container');
        const pdfLoading = document.getElementById('pdf-viewer-loading');
        const pdfError = document.getElementById('pdf-viewer-error');
        const pageInfo = document.getElementById('viewer-page-info');
        const zoomControls = document.getElementById('viewer-zoom-controls');
        const pdfFrame = document.getElementById('pdf-frame');

        if (typeof pdfjsLib === 'undefined') {
            // Fallback to iframe if pdfjsLib is unavailable
            if (pdfFrame) pdfFrame.classList.remove('hidden');
            if (canvasContainer) canvasContainer.classList.add('hidden');
            return;
        }

        // Setup PDF.js worker path
        if (!pdfjsLib.GlobalWorkerOptions.workerSrc) {
            try {
                pdfjsLib.GlobalWorkerOptions.workerSrc = (typeof window !== 'undefined' && window.location ? window.location.origin : '') + '/lib/pdfjs/pdf.worker.min.js';
            } catch (e) {
                pdfjsLib.GlobalWorkerOptions.workerSrc = 'lib/pdfjs/pdf.worker.min.js';
            }
        }

        if (pdfFrame) pdfFrame.classList.add('hidden');
        if (canvasContainer) {
            canvasContainer.classList.remove('hidden');
            canvasContainer.querySelectorAll('.pdf-page-wrapper').forEach(p => p.remove());
        }
        if (pdfLoading) pdfLoading.classList.remove('hidden');
        if (pdfError) pdfError.classList.add('hidden');

        if (currentLoadingTask) {
            try { currentLoadingTask.destroy(); } catch (e) {}
            currentLoadingTask = null;
        }

        try {
            currentLoadingTask = pdfjsLib.getDocument(pdfUrl);
            const pdf = await currentLoadingTask.promise;
            currentPdfDoc = pdf;
            currentPdfUrl = pdfUrl;

            if (pageInfo) {
                pageInfo.textContent = `${pdf.numPages} ${pdf.numPages === 1 ? 'صفحة' : 'صفحات'}`;
                pageInfo.classList.remove('hidden');
            }
            if (zoomControls) {
                zoomControls.classList.remove('hidden');
                zoomControls.classList.add('flex');
            }

            await renderPdfPages();
        } catch (err) {
            console.error('Failed to load PDF with PDF.js:', err);
            if (pdfError) {
                pdfError.classList.remove('hidden');
                const errMsg = document.getElementById('pdf-viewer-error-msg');
                if (errMsg) errMsg.textContent = err.message || 'Error loading PDF';
                const fallbackLink = document.getElementById('pdf-viewer-fallback-link');
                if (fallbackLink) fallbackLink.href = pdfUrl;
            }
            // If PDF.js fails to render, show iframe fallback
            if (pdfFrame) pdfFrame.classList.remove('hidden');
        } finally {
            if (pdfLoading) pdfLoading.classList.add('hidden');
        }
    }

    async function renderPdfPages() {
        if (!currentPdfDoc) return;
        const canvasContainer = document.getElementById('pdf-canvas-container');
        if (!canvasContainer) return;

        // Clear existing rendered pages
        canvasContainer.querySelectorAll('.pdf-page-wrapper').forEach(p => p.remove());

        const zoomLevelBtn = document.getElementById('viewer-zoom-level');
        if (zoomLevelBtn) {
            zoomLevelBtn.textContent = currentScaleMode === 'fit' ? 'Fit' : `${Math.round(currentScale * 100)}%`;
        }

        const containerWidth = Math.max((canvasContainer.clientWidth || window.innerWidth * 0.5) - 32, 280);
        const outputScale = (typeof window !== 'undefined' && window.devicePixelRatio) || 1;

        const activePdfDoc = currentPdfDoc;
        for (let pageNum = 1; pageNum <= currentPdfDoc.numPages; pageNum++) {
            if (!currentPdfDoc || currentPdfDoc !== activePdfDoc) break;

            const page = await currentPdfDoc.getPage(pageNum);
            const unscaledViewport = page.getViewport({ scale: 1.0 });

            let scale = currentScale;
            if (currentScaleMode === 'fit') {
                scale = Math.min(Math.max(containerWidth / unscaledViewport.width, 0.4), 2.5);
            }

            const viewport = page.getViewport({ scale });

            const pageWrapper = document.createElement('div');
            pageWrapper.className = 'pdf-page-wrapper relative bg-white dark:bg-slate-800 rounded-xl shadow-md border border-slate-200 dark:border-slate-700 flex flex-col items-center my-3 overflow-hidden';
            pageWrapper.setAttribute('data-page-number', pageNum);

            const pageBadge = document.createElement('div');
            pageBadge.className = 'absolute top-2 right-2 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-900/70 text-white backdrop-blur-xs z-10 pointer-events-none shadow-xs';
            pageBadge.textContent = `${pageNum} / ${currentPdfDoc.numPages}`;
            pageWrapper.appendChild(pageBadge);

            const canvas = document.createElement('canvas');
            canvas.className = 'pdf-page-canvas block mx-auto';
            canvas.width = Math.floor(viewport.width * outputScale);
            canvas.height = Math.floor(viewport.height * outputScale);
            canvas.style.width = Math.floor(viewport.width) + 'px';
            canvas.style.height = Math.floor(viewport.height) + 'px';

            const ctx = canvas.getContext('2d');
            if (ctx) {
                ctx.scale(outputScale, outputScale);
            }

            pageWrapper.appendChild(canvas);
            canvasContainer.appendChild(pageWrapper);

            if (ctx) {
                await page.render({
                    canvasContext: ctx,
                    viewport: viewport
                }).promise;
            }
        }
    }

    function toggleFullscreen() {
        const panel = document.getElementById('document-viewer-panel');
        if (!panel) return;
        const isFullscreen = panel.classList.toggle('fullscreen-viewer');
        const expandIcon = document.getElementById('viewer-expand-icon');
        const collapseIcon = document.getElementById('viewer-collapse-icon');
        const expandBtn = document.getElementById('viewer-expand-btn');
        if (expandIcon && collapseIcon) {
            if (isFullscreen) {
                expandIcon.classList.add('hidden');
                collapseIcon.classList.remove('hidden');
                if (expandBtn) expandBtn.title = 'Exit fullscreen • تصغير الشاشة';
            } else {
                expandIcon.classList.remove('hidden');
                collapseIcon.classList.add('hidden');
                if (expandBtn) expandBtn.title = 'Toggle fullscreen • شاشة كاملة';
            }
        }
    }

    function initViewerControls() {
        const closeBtn = document.getElementById('viewer-close-btn');
        if (closeBtn && !closeBtn._hasViewerListener) {
            closeBtn._hasViewerListener = true;
            closeBtn.onclick = (e) => {
                e.preventDefault();
                closeDocument();
            };
        }

        const expandBtn = document.getElementById('viewer-expand-btn');
        if (expandBtn && !expandBtn._hasViewerListener) {
            expandBtn._hasViewerListener = true;
            expandBtn.onclick = (e) => {
                e.preventDefault();
                toggleFullscreen();
            };
        }

        const editPagesBtn = document.getElementById('viewer-edit-pages-btn');
        if (editPagesBtn && !editPagesBtn._hasViewerListener) {
            editPagesBtn._hasViewerListener = true;
            editPagesBtn.onclick = (e) => {
                e.preventDefault();
                if (currentPinnedDoc && typeof window.openPageEditor === 'function') {
                    const area = (typeof currentArea !== 'undefined' ? currentArea : window.currentArea);
                    const house = (typeof currentHouse !== 'undefined' ? currentHouse : window.currentHouse);
                    window.openPageEditor({
                        vault_id: currentPinnedDoc.vaultId,
                        title: currentPinnedDoc.title,
                        category: currentPinnedDoc.category,
                        area_id: area,
                        house_id: house,
                        tenant: currentPinnedDoc.tenant || currentPinnedDoc.tenant_name || '',
                        tenant_name: currentPinnedDoc.tenant_name || currentPinnedDoc.tenant || '',
                        tenant_id: currentPinnedDoc.tenant_id || null
                    }, currentPinnedDoc.category);
                }
            };
        }

        const modeToggleBtn = document.getElementById('viewer-mode-toggle');
        if (modeToggleBtn && !modeToggleBtn._hasViewerListener) {
            modeToggleBtn._hasViewerListener = true;
            modeToggleBtn.onclick = (e) => {
                e.preventDefault();
                const currentIsTab = shouldUseOfficialViewer();
                const newMode = currentIsTab ? 'computer' : 'tab';
                try {
                    localStorage.setItem('pdf_viewer_mode', newMode);
                } catch (err) {}
                updateViewerModeButton(newMode);

                if (currentPinnedDoc && currentPinnedDoc.vaultId) {
                    const pdfUrl = resolvePdfUrl(currentPinnedDoc.vaultId);
                    const pdfFrame = document.getElementById('pdf-frame');
                    if (pdfFrame) {
                        pdfFrame.src = resolveViewerSrc(pdfUrl);
                        pdfFrame.classList.remove('hidden');
                    }
                }
            };
        }

        const translateBtn = document.getElementById('viewer-translate-btn');
        if (translateBtn && !translateBtn._hasViewerListener) {
            translateBtn._hasViewerListener = true;
            translateBtn.onclick = (e) => {
                e.preventDefault();
                toggleDocumentTranslation();
            };
        }
        updateTranslationButtonState();

        const initialMode = shouldUseOfficialViewer() ? 'tab' : 'computer';
        updateViewerModeButton(initialMode);
    }

    function updateViewerModeButton(mode) {
        const label = document.getElementById('viewer-mode-label');
        const iconSvg = document.getElementById('viewer-mode-icon');
        const toggleBtn = document.getElementById('viewer-mode-toggle');
        if (!toggleBtn) return;
        const isTab = mode === 'tab' || mode === 'tablet' || mode === 'pdfjs' || mode === 'official' || mode === 'canvas' || (mode === null && shouldUseOfficialViewer());
        if (label) {
            label.textContent = isTab ? 'Tab' : 'Computer';
        }
        if (iconSvg) {
            if (isTab) {
                iconSvg.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>';
            } else {
                iconSvg.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>';
            }
        }
        toggleBtn.title = isTab 
            ? 'Using Tab viewer — Click to switch to Computer viewer • وضع التابلت — انقر للتبديل إلى وضع الكمبيوتر' 
            : 'Using Computer viewer — Click to switch to Tab viewer • وضع الكمبيوتر — انقر للتبديل إلى وضع التابلت';
    }

    let lastOpenDocVaultId = null;
    let lastOpenDocTime = 0;

    function openDocument(vaultId, title, category = null) {
        initViewerControls();

        const now = Date.now();
        if (lastOpenDocVaultId === vaultId && (now - lastOpenDocTime < 350) && currentPinnedDoc && currentPinnedDoc.vaultId === vaultId) {
            return;
        }
        lastOpenDocVaultId = vaultId;
        lastOpenDocTime = now;

        const docViewerPanel = document.getElementById('document-viewer-panel');
        const welcomePanel = document.getElementById('welcome-panel');
        const documentEmptyState = document.getElementById('document-empty-state');
        const resizer2 = document.getElementById('resizer-2');
        const viewerTitle = document.getElementById('viewer-title');
        const viewerPeekBadge = document.getElementById('viewer-peek-badge');
        const pdfFrame = document.getElementById('pdf-frame');
        const viewerDownload = document.getElementById('viewer-download');

        if (!docViewerPanel) return;
        if (welcomePanel) welcomePanel.classList.add('hidden');
        if (documentEmptyState) {
            documentEmptyState.classList.add('hidden');
            documentEmptyState.classList.remove('flex');
        }
        if (resizer2) resizer2.classList.remove('hidden');

        docViewerPanel.classList.remove('hidden');
        docViewerPanel.classList.add('flex');

        const cleanTitle = getCleanDocTitle(title, category);
        if (viewerTitle) viewerTitle.textContent = cleanTitle;
        let tenantName = '';
        let tenantId = null;
        if (typeof currentTimeline !== 'undefined' && Array.isArray(currentTimeline)) {
            const item = currentTimeline.find(d => d && (d.vault_id === vaultId || d.id === vaultId));
            if (item) {
                tenantName = item.tenant || item.tenant_name || item.primary_tenant || '';
                tenantId = item.tenant_id || item.tenantId || null;
            }
        }
        if (!tenantName && typeof window.getSelectedDoc === 'function') {
            const sel = window.getSelectedDoc();
            if (sel && (sel.vaultId === vaultId || sel.doc?.vault_id === vaultId)) {
                tenantName = sel.doc?.tenant || sel.doc?.tenant_name || '';
                tenantId = sel.doc?.tenant_id || null;
            }
        }

        currentPinnedDoc = {
            vaultId,
            title: cleanTitle,
            category,
            tenant: tenantName,
            tenant_name: tenantName,
            tenant_id: tenantId
        };

        const pdfUrl = resolvePdfUrl(vaultId);
        loadPdfIntoFrame(pdfFrame, pdfUrl);
        if (viewerDownload) {
            viewerDownload.href = pdfUrl;
            viewerDownload.setAttribute('download', `${cleanTitle}.pdf`);
        }

        updateViewerCategory(vaultId, category);

        if (isTranslationActive) {
            renderDocumentTranslation();
        } else {
            const overlay = document.getElementById('document-translation-overlay');
            if (overlay) {
                overlay.classList.add('hidden');
                overlay.classList.remove('flex');
            }
        }
    }

    function peekDocument(vaultId, title, category = null) {
        initViewerControls();

        const docViewerPanel = document.getElementById('document-viewer-panel');
        const welcomePanel = document.getElementById('welcome-panel');
        const documentEmptyState = document.getElementById('document-empty-state');
        const resizer2 = document.getElementById('resizer-2');
        const viewerTitle = document.getElementById('viewer-title');
        const viewerPeekBadge = document.getElementById('viewer-peek-badge');
        const pdfFrame = document.getElementById('pdf-frame');
        const viewerDownload = document.getElementById('viewer-download');

        if (!docViewerPanel) return;
        if (welcomePanel) welcomePanel.classList.add('hidden');
        if (documentEmptyState) {
            documentEmptyState.classList.add('hidden');
            documentEmptyState.classList.remove('flex');
        }
        if (resizer2) resizer2.classList.remove('hidden');

        docViewerPanel.classList.remove('hidden');
        docViewerPanel.classList.add('flex');

        const cleanTitle = getCleanDocTitle(title, category);
        if (viewerTitle) viewerTitle.textContent = cleanTitle;
        if (viewerPeekBadge) viewerPeekBadge.classList.remove('hidden');

        currentPinnedDoc = {
            vaultId,
            title: cleanTitle,
            category,
            tenant: '',
            tenant_name: '',
            tenant_id: null
        };

        const pdfUrl = resolvePdfUrl(vaultId);
        loadPdfIntoFrame(pdfFrame, pdfUrl);
        if (viewerDownload) {
            viewerDownload.href = pdfUrl;
            viewerDownload.setAttribute('download', `${cleanTitle}.pdf`);
        }

        updateViewerCategory(vaultId, category);

        if (isTranslationActive) {
            renderDocumentTranslation();
        } else {
            const overlay = document.getElementById('document-translation-overlay');
            if (overlay) {
                overlay.classList.add('hidden');
                overlay.classList.remove('flex');
            }
        }
    }

    function closeDocument() {
        const docViewerPanel = document.getElementById('document-viewer-panel');
        const welcomePanel = document.getElementById('welcome-panel');
        const documentEmptyState = document.getElementById('document-empty-state');
        const pdfFrame = document.getElementById('pdf-frame');
        const catBadge = document.getElementById('viewer-category-badge');
        const catVal = document.getElementById('viewer-category-val');
        const overlay = document.getElementById('document-translation-overlay');

        currentPinnedDoc = null;

        if (pdfFrame) pdfFrame.src = 'about:blank';

        if (overlay) {
            overlay.classList.add('hidden');
            overlay.classList.remove('flex');
            overlay.innerHTML = '';
        }

        if (docViewerPanel) {
            docViewerPanel.classList.remove('fullscreen-viewer');
            docViewerPanel.classList.add('hidden');
            docViewerPanel.classList.remove('flex');
            const expandIcon = document.getElementById('viewer-expand-icon');
            const collapseIcon = document.getElementById('viewer-collapse-icon');
            if (expandIcon) expandIcon.classList.remove('hidden');
            if (collapseIcon) collapseIcon.classList.add('hidden');
        }

        const activeHouse = (typeof currentHouse !== 'undefined' && currentHouse) || (typeof window !== 'undefined' && window.currentHouse);
        if (activeHouse) {
            if (welcomePanel) welcomePanel.classList.add('hidden');
            if (documentEmptyState) {
                documentEmptyState.classList.remove('hidden');
                documentEmptyState.classList.add('flex');
            }
        } else {
            if (welcomePanel) welcomePanel.classList.remove('hidden');
            if (documentEmptyState) {
                documentEmptyState.classList.add('hidden');
                documentEmptyState.classList.remove('flex');
            }
        }
        if (catBadge) {
            catBadge.classList.add('hidden');
            catBadge.classList.remove('flex');
        }
        if (catVal) catVal.textContent = '';
    }

    function reloadCurrentDocument(forceCacheBust = false) {
        if (!currentPinnedDoc || !currentPinnedDoc.vaultId) return;
        const vaultId = currentPinnedDoc.vaultId;
        const pdfFrame = document.getElementById('pdf-frame');
        let pdfUrl = resolvePdfUrl(vaultId);
        if (forceCacheBust) {
            const sep = pdfUrl.includes('?') ? '&' : '?';
            pdfUrl = `${pdfUrl}${sep}t=${Date.now()}`;
        }
        loadPdfIntoFrame(pdfFrame, pdfUrl);
    }

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initViewerControls);
        } else {
            initViewerControls();
        }
    }

    window.openDocument = openDocument;
    window.peekDocument = peekDocument;
    window.closeDocument = closeDocument;
    window.reloadCurrentDocument = reloadCurrentDocument;
    window.getPinnedDoc = () => currentPinnedDoc;
    window.updateViewerCategory = updateViewerCategory;
    window.getCleanDocTitle = getCleanDocTitle;
    window.isVaultHashName = isVaultHashName;
    window.renderPdfDocument = renderPdfDocument;
    window.shouldUseCanvasViewer = shouldUseOfficialViewer;
    window.shouldUseOfficialViewer = shouldUseOfficialViewer;
    window.shouldUseTabViewer = shouldUseOfficialViewer;
    window.updateViewerModeButton = updateViewerModeButton;
    window.resolveViewerSrc = resolveViewerSrc;
    window.toggleFullscreen = toggleFullscreen;
    window.initViewerControls = initViewerControls;
    window.toggleDocumentTranslation = toggleDocumentTranslation;
    window.renderDocumentTranslation = renderDocumentTranslation;
    window.isDocumentTranslationActive = () => isTranslationActive;
    window.translateArabicText = translateArabicText;
    window.getEnglishCategory = getEnglishCategory;
    window.updateTranslationButtonState = updateTranslationButtonState;
})();
