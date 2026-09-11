// ── House Profile & Tenancy Register Component ─────────────────────────────
(function() {
    let currentHouseProfile = null;

    async function loadHouseProfile(areaId, houseId) {
        const docListEl = document.getElementById('document-list');
        const statsBadge = document.getElementById('stats-badge');
        if (!docListEl) return;
        docListEl.innerHTML = `
            <div class="py-8 text-center text-slate-400">
                <div class="inline-block animate-spin w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full mb-2"></div>
                <p class="text-xs">جاري تحميل سجل المنزل والأرشيف...</p>
            </div>
        `;

        try {
            if (isStaticMode) {
                const stateData = await fetchHouseState(areaId, houseId);
                const groups = getDocumentGroups(stateData);
                const knownTenants = stateData.known_tenants || [];
                
                const tenantDocCounts = {};
                const tenantCatSets = {};
                groups.forEach(g => {
                    const t = g.primary_tenant;
                    if (t) {
                        tenantDocCounts[t] = (tenantDocCounts[t] || 0) + 1;
                        if (!tenantCatSets[t]) tenantCatSets[t] = new Set();
                        if (g.category || g.folder_path) tenantCatSets[t].add(g.category || g.folder_path);
                    }
                });

                const tenants = knownTenants.map((kt, idx) => {
                    const sDate = kt.start_date || '2020-01-01';
                    const eDate = kt.end_date || null;
                    const isActive = (!eDate || eDate === 'PRESENT' || eDate === '');
                    return {
                        id: idx + 1,
                        name: kt.name,
                        start_date: sDate,
                        end_date: isActive ? null : eDate,
                        is_active: isActive,
                        duration_str_ar: isActive ? `بدء الإيجار ${sDate.substring(0, 4)} (مستمر)` : `فترة الإيجار: ${sDate.substring(0, 4)} – ${eDate.substring(0, 4)}`,
                        document_count: tenantDocCounts[kt.name] || 0,
                        category_count: (tenantCatSets[kt.name] || new Set()).size
                    };
                });
                tenants.sort((a, b) => (a.is_active === b.is_active ? 0 : a.is_active ? -1 : 1));

                const validDates = [];
                const catCounts = {};
                groups.forEach(g => {
                    (g.dates || []).forEach(d => {
                        if (d && d !== 'NONE') validDates.push(d);
                    });
                    const cat = g.folder_path || g.category || 'غير مصنف';
                    catCounts[cat] = (catCounts[cat] || 0) + 1;
                });

                validDates.sort();
                const oldest = validDates.length ? validDates[0] : null;
                const newest = validDates.length ? validDates[validDates.length - 1] : null;

                currentHouseProfile = {
                    house_id: houseId,
                    area_id: areaId,
                    tenants: tenants,
                    archive: {
                        total_documents: groups.length,
                        total_pages: groups.length,
                        batch_count: 1,
                        oldest_date: oldest,
                        newest_date: newest,
                        timespan_str_ar: oldest && newest ? `من ${oldest.substring(0, 4)} إلى ${newest.substring(0, 4)}` : 'سجلات متوفرة',
                        categories: Object.entries(catCounts).map(([cat, cnt]) => ({ category: cat, document_count: cnt }))
                    }
                };
            } else {
                const res = await fetch(`/api/areas/${encodeURIComponent(areaId)}/houses/${encodeURIComponent(houseId)}/profile`);
                if (!res.ok) throw new Error('Failed to load house profile');
                currentHouseProfile = await res.json();
            }

            if (statsBadge) {
                statsBadge.textContent = `${currentHouseProfile.tenants.length} مستأجرين · ${currentHouseProfile.archive.total_documents} وثيقة`;
                statsBadge.classList.remove('hidden');
            }

            renderHouseProfile(currentHouseProfile);
        } catch (err) {
            console.error(err);
            docListEl.innerHTML = '<p class="text-xs text-rose-500 p-3 text-center">خطأ أثناء تحميل سجل المستأجرين والأرشيف.</p>';
        }
    }

    function getTenantTenureCategory(t) {
        if (!t) return 'short';
        if (t.duration_category) return t.duration_category;

        let years = null;
        if (t.start_date) {
            try {
                const sY = parseInt(String(t.start_date).substring(0, 4), 10);
                let eY = new Date().getFullYear();
                if (t.end_date && t.end_date !== 'PRESENT' && t.end_date !== 'None' && t.end_date !== 'null') {
                    eY = parseInt(String(t.end_date).substring(0, 4), 10);
                }
                if (!isNaN(sY) && !isNaN(eY)) {
                    years = Math.max(0, eY - sY);
                }
            } catch {}
        }

        if (years === null && t.duration_str_ar) {
            const match = t.duration_str_ar.match(/(\d+)\s*(?:سنوات|سنة|عام)/);
            if (match) {
                years = parseInt(match[1], 10);
            } else if (t.duration_str_ar.includes('سنتين') || t.duration_str_ar.includes('سنتان')) {
                years = 2;
            } else if (t.duration_str_ar.includes('سنة واحدة') || t.duration_str_ar.includes('عام واحد')) {
                years = 1;
            } else if (t.duration_str_ar.includes('أقل من سنة') || t.duration_str_ar.includes('أقل من عام')) {
                years = 0;
            }
        }

        if (years === null) return 'short';
        if (years < 5) return 'short';
        if (years <= 10) return 'medium';
        return 'long';
    }

    const TENURE_THEMES = {
        short: {
            card: 'border-emerald-200 bg-emerald-50/40 hover:border-emerald-300 hover:bg-emerald-50/70',
            avatar: 'bg-emerald-100/80 text-emerald-700',
            badge: 'border-emerald-300 bg-emerald-100 text-emerald-800',
            dot: 'bg-emerald-500',
            emoji: '🟢'
        },
        medium: {
            card: 'border-amber-200 bg-amber-50/40 hover:border-amber-300 hover:bg-amber-50/70',
            avatar: 'bg-amber-100/80 text-amber-700',
            badge: 'border-amber-300 bg-amber-100 text-amber-800',
            dot: 'bg-amber-500',
            emoji: '🟡'
        },
        long: {
            card: 'border-rose-200 bg-rose-50/40 hover:border-rose-300 hover:bg-rose-50/70',
            avatar: 'bg-rose-100/80 text-rose-700',
            badge: 'border-rose-300 bg-rose-100 text-rose-800',
            dot: 'bg-rose-500',
            emoji: '🔴'
        }
    };

    if (typeof window !== 'undefined') {
        window.getTenantTenureCategory = getTenantTenureCategory;
        window.TENURE_THEMES = TENURE_THEMES;
    }

    function renderHouseProfile(profile) {
        currentHouseProfile = profile;
        const docListEl = document.getElementById('document-list');
        if (!docListEl) return;
        docListEl.innerHTML = '';

        const container = document.createElement('div');
        container.className = 'space-y-2 py-1';
        container.dir = 'rtl';

        // Tenant Cards
        const tenantsList = document.createElement('div');
        tenantsList.className = 'space-y-2';

        if (profile.tenants.length === 0) {
            tenantsList.innerHTML = '<p class="text-xs text-slate-400 p-4 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">لا يوجد مستأجرون مسجلون لهذا المنزل حالياً.</p>';
        } else {
            profile.tenants.forEach(t => {
                const durCat = getTenantTenureCategory(t);
                const theme = TENURE_THEMES[durCat] || TENURE_THEMES.short;

                const card = document.createElement('div');
                card.className = `tenant-profile-card p-3 rounded-xl border transition-all cursor-pointer group shadow-2xs hover:shadow-sm ${
                    t.is_active 
                        ? theme.card 
                        : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/80'
                }`;
                card.dataset.tenantName = t.name;

                const cleanDuration = (t.duration_str_ar || '')
                    .replace(/^بدء الإيجار\s*/, '')
                    .replace(/^فترة الإيجار:\s*/, '');

                const avatarIcon = t.is_active
                    ? `<div class="w-8 h-8 rounded-lg ${theme.avatar} flex items-center justify-center flex-shrink-0">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
                       </div>`
                    : `<div class="w-8 h-8 rounded-lg bg-slate-100 text-slate-500 flex items-center justify-center flex-shrink-0">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                       </div>`;

                const badgeHtml = t.is_active
                    ? `<span class="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${theme.badge}" title="المستأجر الحالي">
                        <span class="w-1.5 h-1.5 rounded-full ${theme.dot}"></span>
                        حالي
                       </span>`
                    : `<span class="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border border-slate-200 bg-slate-100 text-slate-600" title="مستأجر سابق">
                        <span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                        سابق
                       </span>`;

                card.innerHTML = `
                    <div class="flex items-center justify-between gap-3">
                        <div class="flex items-center gap-2.5 min-w-0 flex-1">
                            ${avatarIcon}
                            <div class="min-w-0 flex-1">
                                <div class="flex items-center gap-2">
                                    <h4 class="text-xs font-bold text-slate-900 group-hover:text-blue-600 transition-colors truncate">${t.name}</h4>
                                    ${badgeHtml}
                                </div>
                                <div class="flex items-center gap-2 mt-1 text-[11px] text-slate-500 flex-wrap">
                                    <span class="text-slate-600 font-medium">${cleanDuration}</span>
                                    <span class="text-slate-300">•</span>
                                    <span class="inline-flex items-center gap-1 text-slate-600" title="${t.document_count} مستند">
                                        <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                                        <span class="font-semibold">${t.document_count}</span>
                                    </span>
                                    <span class="inline-flex items-center gap-1 text-slate-600" title="${t.category_count} مجلدات">
                                        <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                                        <span class="font-semibold">${t.category_count}</span>
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div class="flex items-center text-slate-300 group-hover:text-blue-600 group-hover:-translate-x-1 transition-all flex-shrink-0">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
                        </div>
                    </div>
                `;

                card.onclick = () => {
                    window.location.hash = `#/area/${encodeURIComponent(profile.area_id)}/house/${encodeURIComponent(profile.house_id)}/tenant/${encodeURIComponent(profile.house_id + '_' + t.name)}`;
                };

                tenantsList.appendChild(card);
            });
        }
        container.appendChild(tenantsList);
        docListEl.appendChild(container);
        initExportArchiveHeaderButton();
    }

    // ── Export Archive Modal Controller ──────────────────────────────────────────
    let currentExportProfile = null;
    let selectedExportFormat = 'zip';

    function setExportFormat(format) {
        selectedExportFormat = format;
        const optZip = document.getElementById('export-opt-zip');
        const optPdf = document.getElementById('export-opt-pdf');
        const radioZip = document.getElementById('export-radio-zip');
        const radioPdf = document.getElementById('export-radio-pdf');

        if (format === 'pdf') {
            if (optPdf) {
                optPdf.classList.add('border-rose-500', 'bg-rose-50/50');
                optPdf.classList.remove('border-slate-200', 'bg-white');
            }
            if (optZip) {
                optZip.classList.remove('border-blue-500', 'bg-blue-50/50');
                optZip.classList.add('border-slate-200', 'bg-white');
            }
            if (radioPdf) radioPdf.classList.remove('hidden');
            if (radioZip) radioZip.classList.add('hidden');
        } else {
            selectedExportFormat = 'zip';
            if (optZip) {
                optZip.classList.add('border-blue-500', 'bg-blue-50/50');
                optZip.classList.remove('border-slate-200', 'bg-white');
            }
            if (optPdf) {
                optPdf.classList.remove('border-rose-500', 'bg-rose-50/50');
                optPdf.classList.add('border-slate-200', 'bg-white');
            }
            if (radioZip) radioZip.classList.remove('hidden');
            if (radioPdf) radioPdf.classList.add('hidden');
        }
    }

    function closeExportArchiveModal() {
        const modal = document.getElementById('export-archive-modal');
        if (modal) modal.classList.add('hidden');
        const spinner = document.getElementById('export-archive-spinner');
        if (spinner) spinner.classList.add('hidden');
        const confirmBtn = document.getElementById('btn-confirm-export-archive');
        if (confirmBtn) confirmBtn.disabled = false;
    }

    function triggerDirectExport(profile, format, tenantId) {
        if (!profile) return;
        const areaParam = encodeURIComponent(profile.area_id);
        const houseParam = encodeURIComponent(profile.house_id);
        const endpoint = format === 'pdf' ? 'export-pdf' : 'export-zip';
        let downloadUrl = `/api/areas/${areaParam}/houses/${houseParam}/${endpoint}`;
        if (tenantId) {
            downloadUrl += `?tenant_id=${encodeURIComponent(tenantId)}`;
        }

        const safeArea = (profile.area_id || '').replace(/[^\w\-]/g, '_');
        const safeHouse = (profile.house_id || '').replace(/[^\w\-]/g, '_');
        const ext = format === 'pdf' ? 'pdf' : 'zip';
        const filename = `archive_${safeArea}_${safeHouse}${tenantId ? `_tenant_${tenantId}` : ''}.${ext}`;

        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        const toastFn = (typeof showToast === 'function') ? showToast : ((typeof window !== 'undefined' && typeof window.showToast === 'function') ? window.showToast : null);
        if (toastFn) {
            const formatMsg = format === 'pdf' ? 'ملف PDF المدمج' : 'الأرشيف المضغوط (ZIP)';
            toastFn(`تم بدء تحميل ${formatMsg} للمنزل`, 'success');
        }
    }

    function initExportArchiveHeaderButton() {
        const exportHeaderBtn = document.getElementById('btn-export-house-archive');
        const legacyZipBtn = document.getElementById('btn-export-house-zip');

        const handleExportClick = async () => {
            const area = (typeof currentArea !== 'undefined' && currentArea) ? currentArea : (window.currentArea || '');
            const house = (typeof currentHouse !== 'undefined' && currentHouse) ? currentHouse : (window.currentHouse || '');
            if (!house) {
                const toastFn = (typeof showToast === 'function') ? showToast : ((typeof window !== 'undefined' && typeof window.showToast === 'function') ? window.showToast : null);
                if (toastFn) toastFn('Please select a house first', 'warning');
                return;
            }
            if (currentHouseProfile && currentHouseProfile.house_id === house) {
                openExportArchiveModal(currentHouseProfile);
            } else {
                try {
                    const res = await fetch(`/api/areas/${encodeURIComponent(area)}/houses/${encodeURIComponent(house)}/profile`);
                    if (res.ok) {
                        currentHouseProfile = await res.json();
                        openExportArchiveModal(currentHouseProfile);
                    } else {
                        openExportArchiveModal({ area_id: area, house_id: house, tenants: [] });
                    }
                } catch (e) {
                    openExportArchiveModal({ area_id: area, house_id: house, tenants: [] });
                }
            }
        };

        if (exportHeaderBtn) {
            exportHeaderBtn.onclick = handleExportClick;
        }
        if (legacyZipBtn && legacyZipBtn !== exportHeaderBtn) {
            legacyZipBtn.onclick = handleExportClick;
        }
    }

    function initExportArchiveModal() {
        initExportArchiveHeaderButton();
        const modal = document.getElementById('export-archive-modal');
        if (!modal || modal.dataset.initialized === 'true') return;
        modal.dataset.initialized = 'true';

        const optZip = document.getElementById('export-opt-zip');
        const optPdf = document.getElementById('export-opt-pdf');
        const closeBtn = document.getElementById('export-archive-modal-close');
        const cancelBtn = document.getElementById('btn-cancel-export-archive');
        const confirmBtn = document.getElementById('btn-confirm-export-archive');

        if (optZip) optZip.onclick = () => setExportFormat('zip');
        if (optPdf) optPdf.onclick = () => setExportFormat('pdf');
        if (closeBtn) closeBtn.onclick = () => closeExportArchiveModal();
        if (cancelBtn) cancelBtn.onclick = () => closeExportArchiveModal();

        if (confirmBtn) {
            confirmBtn.onclick = () => {
                if (!currentExportProfile) return;
                const tenantSelect = document.getElementById('export-archive-tenant-select');
                const tenantId = tenantSelect ? tenantSelect.value : '';

                const spinner = document.getElementById('export-archive-spinner');
                if (spinner) spinner.classList.remove('hidden');
                confirmBtn.disabled = true;

                triggerDirectExport(currentExportProfile, selectedExportFormat, tenantId || null);

                setTimeout(() => {
                    closeExportArchiveModal();
                }, 600);
            };
        }

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeExportArchiveModal();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const curModal = document.getElementById('export-archive-modal');
                if (curModal && !curModal.classList.contains('hidden')) {
                    closeExportArchiveModal();
                }
            }
        });
    }

    function openExportArchiveModal(profile) {
        currentExportProfile = profile;
        const modal = document.getElementById('export-archive-modal');
        if (!modal) {
            // Fallback for headless environments without modal DOM
            triggerDirectExport(profile, 'zip', null);
            return;
        }

        initExportArchiveModal();
        setExportFormat('zip');

        const tenantSelect = document.getElementById('export-archive-tenant-select');
        if (tenantSelect) {
            tenantSelect.innerHTML = '<option value="">كامل السجل • All Records</option>';
            if (profile && Array.isArray(profile.tenants)) {
                profile.tenants.forEach(t => {
                    const opt = document.createElement('option');
                    opt.value = (t.id !== undefined && t.id !== null) ? String(t.id) : (t.name || '');
                    if (t.is_active) {
                        const dur = t.duration_str_ar ? ` (${t.duration_str_ar})` : ' (المستأجر الحالي)';
                        opt.textContent = `${t.name}${dur}`;
                    } else {
                        const dur = t.duration_str_ar ? ` (${t.duration_str_ar})` : '';
                        opt.textContent = `${t.name}${dur}`;
                    }
                    tenantSelect.appendChild(opt);
                });
            }
        }

        modal.classList.remove('hidden');
        modal.focus();
    }

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                initExportArchiveModal();
                initExportArchiveHeaderButton();
            });
        } else {
            initExportArchiveModal();
            initExportArchiveHeaderButton();
        }
    }

    window.loadHouseProfile = loadHouseProfile;
    window.renderHouseProfile = renderHouseProfile;
    window.openExportArchiveModal = openExportArchiveModal;
    window.closeExportArchiveModal = closeExportArchiveModal;
    window.setExportFormat = setExportFormat;
    window.initExportArchiveModal = initExportArchiveModal;
    window.initExportArchiveHeaderButton = initExportArchiveHeaderButton;
})();
