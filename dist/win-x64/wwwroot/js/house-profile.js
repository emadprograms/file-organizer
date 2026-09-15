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
                        is_resident: (kt.is_resident !== undefined) ? kt.is_resident : 1,
                        notes: kt.notes || null,
                        duration_str_ar: isActive ? `بدء الإيجار ${sDate.substring(0, 4)} (مستمر)` : `فترة الإيجار: ${sDate.substring(0, 4)} – ${eDate.substring(0, 4)}`,
                        document_count: tenantDocCounts[kt.name] || 0,
                        category_count: (tenantCatSets[kt.name] || new Set()).size,
                        categories: Array.from(tenantCatSets[kt.name] || [])
                    };
                });
                tenants.sort((a, b) => {
                    const aRes = (a.is_resident !== 0 && a.is_resident !== false) ? 1 : 0;
                    const bRes = (b.is_resident !== 0 && b.is_resident !== false) ? 1 : 0;
                    if (aRes !== bRes) return bRes - aRes;
                    return (a.is_active === b.is_active ? 0 : a.is_active ? -1 : 1);
                });

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
                const residents = (currentHouseProfile.tenants || []).filter(t => t.is_resident !== 0 && t.is_resident !== false);
                const applicants = (currentHouseProfile.tenants || []).filter(t => t.is_resident === 0 || t.is_resident === false);
                const totalDocs = (currentHouseProfile.archive && currentHouseProfile.archive.total_documents !== undefined)
                    ? currentHouseProfile.archive.total_documents
                    : 0;

                if (applicants.length > 0) {
                    statsBadge.textContent = `${residents.length} مستأجرين · ${applicants.length} طلبات تخصيص · ${totalDocs} وثيقة`;
                } else {
                    statsBadge.textContent = `${residents.length} مستأجرين · ${totalDocs} وثيقة`;
                }
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

    const MANDATORY_INTEGRITY_CATEGORIES = [
        { id: '02', key: 'بيانات شخصية', prefix: '02 - بيانات شخصية', label: 'بيانات شخصية', labelEn: 'Personal Details' },
        { id: '03', key: 'أمر تخصيص', prefix: '03 - أمر تخصيص', label: 'أمر تخصيص', labelEn: 'Allotment Order' },
        { id: '04', key: 'محضر تسليم مفتاح', prefix: '04 - محضر تسليم مفتاح', label: 'محضر تسليم مفتاح', labelEn: 'Key Handover' },
        { id: '05', key: 'عقود', prefix: '05 - عقود', label: 'عقود', labelEn: 'Contracts' },
        { id: '07', key: 'استقطاع إيجار', prefix: '07 - استقطاع إيجار', label: 'استقطاع إيجار', labelEn: 'Rent Deduction' }
    ];

    function computeTenantCompliance(profile, activeTenant) {
        if (!profile || !activeTenant) {
            return {
                isOccupied: false,
                isVacant: true,
                totalRequired: 5,
                presentCount: 0,
                missingCount: 0,
                missingCategories: [],
                presentCategories: [],
                isComplete: false,
                items: MANDATORY_INTEGRITY_CATEGORIES.map(cat => ({
                    ...cat,
                    exists: false,
                    documentCount: 0
                }))
            };
        }

        const tenantCats = (activeTenant.categories && Array.isArray(activeTenant.categories)) ? activeTenant.categories : [];
        const catCounts = activeTenant.category_counts || activeTenant.categoryCounts || {};

        const presentCategories = [];
        const missingCategories = [];

        const items = MANDATORY_INTEGRITY_CATEGORIES.map(cat => {
            let exists = false;
            let docCount = 0;

            // Check in activeTenant.category_counts first
            if (catCounts && typeof catCounts === 'object' && Object.keys(catCounts).length > 0) {
                if ((catCounts[cat.key] || 0) > 0) {
                    exists = true;
                    docCount = catCounts[cat.key];
                } else if ((catCounts[cat.prefix] || 0) > 0) {
                    exists = true;
                    docCount = catCounts[cat.prefix];
                } else if ((catCounts[cat.id] || 0) > 0) {
                    exists = true;
                    docCount = catCounts[cat.id];
                } else {
                    for (const [k, count] of Object.entries(catCounts)) {
                        if (count > 0) {
                            const cleanK = k.replace(/^\d+\s*-\s*/, '').trim();
                            if (cleanK === cat.key || cleanK === cat.label || k.includes(cat.prefix) || k.startsWith(cat.id)) {
                                exists = true;
                                docCount = count;
                                break;
                            }
                        }
                    }
                }
            }

            // Fallback to activeTenant.categories
            if (!exists && tenantCats.length > 0) {
                for (const c of tenantCats) {
                    const clean = String(c).replace(/^\d+\s*-\s*/, '').trim();
                    if (clean === cat.key || clean === cat.label || String(c).includes(cat.prefix) || String(c).startsWith(cat.id)) {
                        exists = true;
                        docCount = 1;
                        break;
                    }
                }
            }

            const itemData = {
                ...cat,
                exists,
                documentCount: exists ? Math.max(docCount, 1) : 0
            };

            if (exists) {
                presentCategories.push(itemData);
            } else {
                missingCategories.push(itemData);
            }

            return itemData;
        });

        const presentCount = presentCategories.length;
        const missingCount = missingCategories.length;
        const isComplete = (missingCount === 0);

        return {
            isOccupied: true,
            isVacant: false,
            totalRequired: 5,
            presentCount,
            missingCount,
            missingCategories,
            presentCategories,
            isComplete,
            items
        };
    }

    function renderHouseProfile(profile) {
        currentHouseProfile = profile;
        const docListEl = document.getElementById('document-list');
        if (!docListEl) return;
        docListEl.innerHTML = '';

        const container = document.createElement('div');
        container.className = 'space-y-2 py-1';
        container.dir = 'rtl';

        const allTenants = (profile && Array.isArray(profile.tenants)) ? profile.tenants : [];
        const residents = allTenants.filter(t => t.is_resident !== 0 && t.is_resident !== false);
        const applicants = allTenants.filter(t => t.is_resident === 0 || t.is_resident === false);

        // Section 0: Tenant File Compliance Checklist (Idea C)
        const activeTenant = residents.find(t => t.is_active) || (residents.length > 0 ? residents[0] : null);
        const compliance = computeTenantCompliance(profile, activeTenant);
        const complianceSection = document.createElement('div');

        if (!activeTenant) {
            complianceSection.className = 'tenant-compliance-card mb-2.5 p-2.5 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/50';
            complianceSection.innerHTML = `
                <div class="flex items-center justify-between gap-2">
                    <div class="flex items-center gap-2">
                        <span class="w-6 h-6 rounded-lg bg-slate-200/80 dark:bg-slate-800 text-slate-500 dark:text-slate-400 flex items-center justify-center text-xs flex-shrink-0">📋</span>
                        <div>
                            <h4 class="text-xs font-bold text-slate-800 dark:text-slate-200">فحص اكتمال ملف الساكن</h4>
                            <p class="text-[10.5px] text-slate-500 dark:text-slate-400">المنزل شاغر حالياً — لا يوجد ساكن حالي لإجراء فحص الوثائق الإلزامية.</p>
                        </div>
                    </div>
                    <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700 flex-shrink-0">شاغر</span>
                </div>
            `;
        } else {
            const isComplete = compliance.isComplete;
            const cardBorder = isComplete 
                ? 'border-emerald-200/90 dark:border-emerald-900/60 bg-emerald-50/30 dark:bg-emerald-950/20' 
                : 'border-amber-200/90 dark:border-amber-900/60 bg-amber-50/30 dark:bg-amber-950/20';
            const headerBorder = isComplete 
                ? 'border-emerald-100 dark:border-emerald-900/40' 
                : 'border-amber-100 dark:border-amber-900/40';
            const badgeClass = isComplete
                ? 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800'
                : 'bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-800';

            const itemsHtml = compliance.items.map(cat => {
                if (cat.exists) {
                    return `
                        <div class="compliance-item p-1.5 px-2 rounded-lg border border-emerald-200/80 dark:border-emerald-800/50 bg-white dark:bg-emerald-950/30 flex flex-col justify-between cursor-pointer hover:border-emerald-400 hover:shadow-2xs transition-all group"
                             data-category-prefix="${cat.prefix}"
                             title="متوفر (${cat.documentCount} وثيقة) - انقر لعرض المجلد">
                            <div class="flex items-center justify-between gap-1 mb-0.5">
                                <span class="text-[9.5px] font-bold text-emerald-700 dark:text-emerald-400 font-mono">${cat.id}</span>
                                <span class="w-3.5 h-3.5 rounded-full bg-emerald-100 dark:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300 flex items-center justify-center text-[9px] font-bold">✓</span>
                            </div>
                            <div class="text-[11px] font-bold text-slate-800 dark:text-slate-100 truncate mb-1" title="${cat.label}">${cat.label}</div>
                            <div class="flex items-center justify-between text-[9.5px] text-emerald-600 dark:text-emerald-400 font-medium">
                                <span>متوفر (${cat.documentCount})</span>
                                <svg class="w-2.5 h-2.5 text-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                            </div>
                        </div>
                    `;
                } else {
                    return `
                        <div class="compliance-item p-1.5 px-2 rounded-lg border border-amber-200/90 dark:border-amber-800/60 bg-white dark:bg-amber-950/30 flex flex-col justify-between transition-all">
                            <div class="flex items-center justify-between gap-1 mb-0.5">
                                <span class="text-[9.5px] font-bold text-amber-700 dark:text-amber-400 font-mono">${cat.id}</span>
                                <span class="w-3.5 h-3.5 rounded-full bg-amber-100 dark:bg-amber-900/60 text-amber-700 dark:text-amber-300 flex items-center justify-center text-[9px] font-bold">⚠️</span>
                            </div>
                            <div class="text-[11px] font-bold text-slate-800 dark:text-slate-100 truncate mb-1" title="${cat.label}">${cat.label}</div>
                            <button type="button" class="btn-compliance-upload w-full py-0.5 px-1.5 rounded-md bg-amber-500 hover:bg-amber-600 active:bg-amber-700 text-white font-bold text-[10px] flex items-center justify-center gap-1 shadow-2xs cursor-pointer transition-all hover:scale-[1.02]"
                                    data-cat-prefix="${cat.prefix}"
                                    data-cat-name="${cat.key}"
                                    title="رفع ${cat.label} للساكن ${activeTenant.name}">
                                <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/></svg>
                                <span>+ رفع</span>
                            </button>
                        </div>
                    `;
                }
            }).join('');

            const isExpanded = typeof localStorage !== 'undefined' ? localStorage.getItem('tenant_compliance_expanded') !== 'false' : true;

            complianceSection.className = `tenant-compliance-card mb-2.5 p-2.5 rounded-xl border ${cardBorder} shadow-2xs`;

            complianceSection.innerHTML = `
                <div class="compliance-header-toggle flex items-center justify-between gap-2 cursor-pointer select-none">
                    <div class="flex items-center gap-2 min-w-0">
                        <span class="text-sm">🛡️</span>
                        <div class="flex items-center gap-1.5 min-w-0 truncate">
                            <h4 class="text-xs font-bold text-slate-900 dark:text-slate-100">فحص اكتمال ملف الساكن</h4>
                            <span class="text-[10px] text-slate-300 dark:text-slate-600">•</span>
                            <span class="text-xs font-semibold text-blue-600 dark:text-blue-400 truncate">${activeTenant.name}</span>
                        </div>
                    </div>
                    <div class="flex items-center gap-1.5 flex-shrink-0">
                        <span class="compliance-score-badge text-[10.5px] font-bold px-2 py-0.5 rounded-md border ${badgeClass}">
                            ${isComplete ? 'مكتمل 5/5 ✓' : `${compliance.presentCount}/5 ناقص ⚠️`}
                        </span>
                        <button type="button" class="btn-toggle-compliance text-[10px] font-medium px-1.5 py-0.5 rounded text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 border border-slate-200 dark:border-slate-700 flex items-center gap-0.5 transition-all">
                            <span class="toggle-text">${isExpanded ? 'إخفاء' : 'عرض'}</span>
                            <svg class="w-3 h-3 transform transition-transform ${isExpanded ? 'rotate-180' : ''} toggle-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                        </button>
                    </div>
                </div>

                <div class="compliance-body-container ${isExpanded ? '' : 'hidden'} mt-2 pt-2 border-t ${headerBorder}">
                    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-1.5">
                        ${itemsHtml}
                    </div>
                </div>
            `;

            const headerToggle = complianceSection.querySelector('.compliance-header-toggle');
            const bodyContainer = complianceSection.querySelector('.compliance-body-container');
            const toggleText = complianceSection.querySelector('.toggle-text');
            const toggleIcon = complianceSection.querySelector('.toggle-icon');

            if (headerToggle && bodyContainer) {
                headerToggle.addEventListener('click', (e) => {
                    const nowHidden = bodyContainer.classList.toggle('hidden');
                    if (toggleText) toggleText.textContent = nowHidden ? 'عرض' : 'إخفاء';
                    if (toggleIcon) toggleIcon.classList.toggle('rotate-180', !nowHidden);
                    if (typeof localStorage !== 'undefined') {
                        localStorage.setItem('tenant_compliance_expanded', (!nowHidden).toString());
                    }
                });
            }

            complianceSection.querySelectorAll('.btn-compliance-upload').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    const catPrefix = btn.dataset.catPrefix;
                    if (typeof window.openIngestStationWithPreset === 'function') {
                        window.openIngestStationWithPreset({
                            area: profile.area_id,
                            house: profile.house_id,
                            tenant: activeTenant.name,
                            category: catPrefix
                        });
                    } else if (typeof window.openIngestStation === 'function') {
                        window.openIngestStation(null, {
                            area: profile.area_id,
                            house: profile.house_id,
                            tenant: activeTenant.name,
                            category: catPrefix
                        });
                    }
                });
            });

            complianceSection.querySelectorAll('.compliance-item[data-category-prefix]').forEach(item => {
                item.addEventListener('click', (e) => {
                    if (e.target.closest('.btn-compliance-upload')) return;
                    const tenantParam = `${profile.house_id}_${activeTenant.name}`;
                    window.location.hash = `#/area/${encodeURIComponent(profile.area_id)}/house/${encodeURIComponent(profile.house_id)}/tenant/${encodeURIComponent(tenantParam)}`;
                });
            });
        }

        container.appendChild(complianceSection);

        const tenantSectionDivider = document.createElement('div');
        tenantSectionDivider.className = 'tenant-section-divider border-b border-slate-200 dark:border-slate-800 my-2.5';
        container.appendChild(tenantSectionDivider);

        // Section 1: Resident Tenants (residents-section)
        const residentsSection = document.createElement('div');
        residentsSection.className = 'residents-section space-y-2';

        if (applicants.length > 0) {
            const residentsHeader = document.createElement('div');
            residentsHeader.className = 'flex items-center justify-between px-1 mb-1.5 residents-header';
            residentsHeader.innerHTML = `
                <h3 class="text-xs font-bold text-slate-700 dark:text-slate-200 flex items-center gap-1.5">
                    <svg class="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
                    <span>المستأجرون</span>
                    <span class="text-[10px] font-semibold text-slate-500 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.2 rounded-full">${residents.length}</span>
                </h3>
            `;
            residentsSection.appendChild(residentsHeader);
        }

        if (residents.length === 0) {
            const emptyEl = document.createElement('p');
            emptyEl.className = 'text-xs text-slate-400 p-4 text-center bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-dashed border-slate-200 dark:border-slate-700';
            emptyEl.textContent = 'لا يوجد مستأجرون مسجلون لهذا المنزل حالياً.';
            residentsSection.appendChild(emptyEl);
        } else {
            residents.forEach(t => {
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
                                    <span class="inline-flex items-center gap-1 text-slate-600" title="${t.document_count || 0} مستند">
                                        <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                                        <span class="font-semibold">${t.document_count || 0}</span>
                                    </span>
                                    <span class="inline-flex items-center gap-1 text-slate-600" title="${t.category_count || 0} مجلدات">
                                        <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                                        <span class="font-semibold">${t.category_count || 0}</span>
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

                residentsSection.appendChild(card);
            });
        }
        container.appendChild(residentsSection);

        // Section 2: Applicants (applicants-section) separated by clean single divider
        if (applicants.length > 0) {
            const divider = document.createElement('hr');
            divider.className = 'border-t border-slate-200/80 dark:border-slate-700/80 my-3';
            container.appendChild(divider);

            const applicantsSection = document.createElement('div');
            applicantsSection.className = 'applicants-section space-y-2';

            const applicantsHeader = document.createElement('div');
            applicantsHeader.className = 'flex items-center justify-between px-1 mb-1.5 applicants-header';
            applicantsHeader.innerHTML = `
                <h3 class="text-xs font-bold text-purple-800 dark:text-purple-300 flex items-center gap-1.5">
                    <svg class="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/></svg>
                    <span>المتقدمون</span>
                    <span class="text-[10px] font-semibold text-purple-700 bg-purple-100 dark:bg-purple-950/60 dark:text-purple-300 px-1.5 py-0.2 rounded-full">${applicants.length}</span>
                </h3>
            `;
            applicantsSection.appendChild(applicantsHeader);

            applicants.forEach(t => {
                const card = document.createElement('div');
                card.className = 'applicant-profile-card tenant-profile-card p-3 rounded-xl border border-dashed border-purple-200 dark:border-purple-800/60 bg-purple-50/20 dark:bg-purple-950/20 hover:border-purple-400 hover:bg-purple-50/40 transition-all cursor-pointer group shadow-2xs hover:shadow-sm';
                card.dataset.tenantName = t.name;

                const appDateStr = t.start_date ? 'أول وثيقة: ' + String(t.start_date).substring(0, 10) : 'بانتظار أول وثيقة (تلقائي)';

                card.innerHTML = `
                    <div class="flex items-center justify-between gap-3">
                        <div class="flex items-center gap-2.5 min-w-0 flex-1">
                            <div class="w-8 h-8 rounded-lg bg-purple-100/80 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 flex items-center justify-center flex-shrink-0">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/></svg>
                            </div>
                            <div class="min-w-0 flex-1">
                                <div class="flex items-center gap-2">
                                    <h4 class="text-xs font-bold text-slate-900 dark:text-slate-100 group-hover:text-purple-600 transition-colors truncate">${t.name}</h4>
                                    <span class="applicant-badge inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border border-purple-200 dark:border-purple-800/60 bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300" title="متقدم - لم يسكن في المنزل">
                                        <span class="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
                                        📋 متقدم (لم يسكن)
                                    </span>
                                </div>
                                <div class="flex items-center gap-2 mt-1 text-[11px] text-slate-500 flex-wrap">
                                    <span class="text-slate-600 dark:text-slate-400 font-medium">${appDateStr}</span>
                                    <span class="text-slate-300 dark:text-slate-600">•</span>
                                    <span class="inline-flex items-center gap-1 text-slate-600 dark:text-slate-400" title="${t.document_count || 0} مستند">
                                        <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                                        <span class="font-semibold">${t.document_count || 0}</span>
                                    </span>
                                    <span class="inline-flex items-center gap-1 text-slate-600 dark:text-slate-400" title="${t.category_count || 0} مجلدات">
                                        <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                                        <span class="font-semibold">${t.category_count || 0}</span>
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div class="flex items-center text-slate-300 group-hover:text-purple-600 group-hover:-translate-x-1 transition-all flex-shrink-0">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
                        </div>
                    </div>
                `;

                card.onclick = () => {
                    window.location.hash = `#/area/${encodeURIComponent(profile.area_id)}/house/${encodeURIComponent(profile.house_id)}/tenant/${encodeURIComponent(profile.house_id + '_' + t.name)}`;
                };

                applicantsSection.appendChild(card);
            });

            container.appendChild(applicantsSection);
        }

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
    window.computeTenantCompliance = computeTenantCompliance;
    window.MANDATORY_INTEGRITY_CATEGORIES = MANDATORY_INTEGRITY_CATEGORIES;
    window.openExportArchiveModal = openExportArchiveModal;
    window.closeExportArchiveModal = closeExportArchiveModal;
    window.setExportFormat = setExportFormat;
    window.initExportArchiveModal = initExportArchiveModal;
    window.initExportArchiveHeaderButton = initExportArchiveHeaderButton;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            loadHouseProfile,
            renderHouseProfile,
            computeTenantCompliance,
            MANDATORY_INTEGRITY_CATEGORIES,
            getTenantTenureCategory,
            TENURE_THEMES,
            openExportArchiveModal,
            closeExportArchiveModal,
            setExportFormat,
            initExportArchiveModal,
            initExportArchiveHeaderButton,
        };
    }
})();
