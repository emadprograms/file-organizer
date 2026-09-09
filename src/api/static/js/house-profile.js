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

    function renderHouseProfile(profile) {
        const docListEl = document.getElementById('document-list');
        if (!docListEl) return;
        docListEl.innerHTML = '';

        const container = document.createElement('div');
        container.className = 'space-y-4 py-1';
        container.dir = 'rtl';

        // 1. Tenancy Register Header
        const tenantsHeader = document.createElement('div');
        tenantsHeader.className = 'flex items-center justify-between px-1 pb-1 border-b border-slate-100';
        tenantsHeader.innerHTML = `
            <div class="flex items-center gap-1.5">
                <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
                <span class="text-xs font-bold text-slate-800">سجل المستأجرين المتعاقبين</span>
            </div>
            <span class="text-[10px] font-semibold text-slate-500 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-full">
                ${profile.tenants.length} مستأجر
            </span>
        `;
        container.appendChild(tenantsHeader);

        // 2. Tenant Cards
        const tenantsList = document.createElement('div');
        tenantsList.className = 'space-y-2';

        if (profile.tenants.length === 0) {
            tenantsList.innerHTML = '<p class="text-xs text-slate-400 p-4 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">لا يوجد مستأجرون مسجلون لهذا المنزل حالياً.</p>';
        } else {
            profile.tenants.forEach(t => {
                const card = document.createElement('div');
                card.className = `tenant-profile-card p-3.5 rounded-xl border transition-all cursor-pointer group shadow-2xs hover:shadow-sm ${
                    t.is_active 
                        ? 'border-emerald-200 bg-emerald-50/40 hover:border-emerald-300 hover:bg-emerald-50/70' 
                        : 'border-slate-200 bg-white hover:border-blue-300 hover:bg-slate-50/80'
                }`;
                card.dataset.tenantName = t.name;

                const badgeColor = t.is_active 
                    ? 'bg-emerald-100 text-emerald-800 border-emerald-300' 
                    : 'bg-slate-100 text-slate-600 border-slate-200';
                const badgeLabel = t.is_active ? '🟢 المستأجر الحالي' : '⚪ مستأجر سابق';

                card.innerHTML = `
                    <div class="flex items-start justify-between gap-2">
                        <div class="flex items-start gap-2.5 min-w-0">
                            <div class="w-8 h-8 rounded-lg ${t.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'} flex items-center justify-center font-bold text-sm flex-shrink-0 mt-0.5">
                                ${t.is_active ? '👤' : '⌛'}
                            </div>
                            <div class="min-w-0">
                                <div class="flex items-center gap-2 flex-wrap">
                                    <h4 class="text-xs font-bold text-slate-900 group-hover:text-blue-600 transition-colors">${t.name}</h4>
                                    <span class="text-[9px] font-bold px-2 py-0.5 rounded-md border ${badgeColor}">
                                        ${badgeLabel}
                                    </span>
                                </div>
                                <p class="text-[11px] text-slate-500 font-medium mt-1">${t.duration_str_ar}</p>
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center justify-between mt-3 pt-2.5 border-t ${t.is_active ? 'border-emerald-100' : 'border-slate-100'} text-[11px]">
                        <div class="flex items-center gap-2 text-slate-500 font-medium">
                            <span class="bg-white/80 border border-slate-200 px-2 py-0.5 rounded text-[10px] font-semibold text-slate-700">📄 ${t.document_count} مستند</span>
                            <span class="bg-white/80 border border-slate-200 px-2 py-0.5 rounded text-[10px] font-semibold text-slate-700">📁 ${t.category_count} مجلدات</span>
                        </div>
                        <span class="text-blue-600 font-bold text-xs group-hover:translate-x-[-3px] transition-transform inline-flex items-center gap-1">
                            استعراض المجلدات ←
                        </span>
                    </div>
                `;

                card.onclick = () => {
                    window.location.hash = `#/area/${encodeURIComponent(profile.area_id)}/house/${encodeURIComponent(profile.house_id)}/tenant/${encodeURIComponent(profile.house_id + '_' + t.name)}`;
                };

                tenantsList.appendChild(card);
            });
        }
        container.appendChild(tenantsList);

        // 3. Digital Archive Profile
        const archive = profile.archive;
        const archiveBox = document.createElement('div');
        archiveBox.className = 'p-3.5 bg-slate-50/80 rounded-xl border border-slate-200 space-y-3 mt-4';
        archiveBox.innerHTML = `
            <div class="flex items-center gap-1.5 text-xs font-bold text-slate-700">
                <svg class="w-4 h-4 text-blue-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
                <span>بيانات الأرشيف الرقمي للمنزل</span>
            </div>

            <div class="grid grid-cols-2 gap-2 text-xs">
                <div class="bg-white p-2.5 rounded-lg border border-slate-200 shadow-2xs">
                    <span class="text-[10px] text-slate-400 block font-medium">النطاق الزمني للوثائق</span>
                    <span class="font-bold text-slate-800 mt-1 block text-[11px]">${archive.timespan_str_ar}</span>
                </div>
                <div class="bg-white p-2.5 rounded-lg border border-slate-200 shadow-2xs">
                    <span class="text-[10px] text-slate-400 block font-medium">حجم الأرشيف الممسوح</span>
                    <span class="font-bold text-slate-800 mt-1 block text-[11px]">${archive.total_documents} وثيقة (${archive.total_pages} صفحة)</span>
                </div>
            </div>

            ${archive.categories && archive.categories.length > 0 ? `
                <div class="pt-1">
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">التصنيفات الرئيسية المتوفرة:</span>
                    <div class="flex flex-wrap gap-1.5">
                        ${archive.categories.map(c => `
                            <span class="text-[10px] bg-white border border-slate-200 text-slate-700 px-2 py-0.5 rounded-md font-medium">
                                ${c.category} <b class="text-blue-600 font-bold">(${c.document_count})</b>
                            </span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        `;
        container.appendChild(archiveBox);

        docListEl.appendChild(container);
    }

    window.loadHouseProfile = loadHouseProfile;
    window.renderHouseProfile = renderHouseProfile;
})();
