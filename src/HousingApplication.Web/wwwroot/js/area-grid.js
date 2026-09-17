// ── Area Houses Grid Component ────────────────────────────────────────────
(function() {
    let currentAreaNode = null;
    let currentIntegrityFilter = 'all';

    const MANDATORY_INTEGRITY_CATEGORIES = [
        { id: '02', key: 'بيانات شخصية', prefix: '02 - بيانات شخصية', label: 'بيانات شخصية', labelEn: 'Personal Details' },
        { id: '03', key: 'أمر تخصيص', prefix: '03 - أمر تخصيص', label: 'أمر تخصيص', labelEn: 'Allotment Order' },
        { id: '04', key: 'محضر تسليم مفتاح', prefix: '04 - محضر تسليم مفتاح', label: 'محضر تسليم مفتاح', labelEn: 'Key Handover' },
        { id: '05', key: 'عقود', prefix: '05 - عقود', label: 'عقود', labelEn: 'Contracts' },
        { id: '07', key: 'استقطاع إيجار', prefix: '07 - استقطاع إيجار', label: 'استقطاع إيجار', labelEn: 'Rent Deduction' }
    ];

    function computeHouseIntegrity(house) {
        if (!house) {
            return {
                isOccupied: false,
                isVacant: true,
                totalRequired: 5,
                presentCount: 0,
                missingCount: 0,
                missingCategories: [],
                presentCategories: [],
                isComplete: false,
                status: 'vacant',
                label: 'Vacant'
            };
        }

        const occupied = isHouseOccupied(house);
        if (!occupied) {
            return {
                isOccupied: false,
                isVacant: true,
                totalRequired: 5,
                presentCount: 0,
                missingCount: 0,
                missingCategories: [],
                presentCategories: [],
                isComplete: false,
                status: 'vacant',
                label: 'Vacant'
            };
        }

        const catCounts = house.active_tenant_category_counts || house.activeTenantCategoryCounts || house.category_counts || house.categoryCounts || {};
        const presentCategories = [];
        const missingCategories = [];

        MANDATORY_INTEGRITY_CATEGORIES.forEach(cat => {
            let isPresent = false;
            if ((catCounts[cat.key] || 0) > 0 || (catCounts[cat.prefix] || 0) > 0 || (catCounts[cat.id] || 0) > 0) {
                isPresent = true;
            } else {
                for (const [k, count] of Object.entries(catCounts)) {
                    if (count > 0) {
                        const cleanK = k.replace(/^\d+\s*-\s*/, '').trim();
                        if (cleanK === cat.key || cleanK === cat.label || k.includes(cat.prefix) || k.startsWith(cat.id)) {
                            isPresent = true;
                            break;
                        }
                    }
                }
            }

            if (isPresent) {
                presentCategories.push(cat);
            } else {
                missingCategories.push(cat);
            }
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
            status: isComplete ? 'complete' : 'incomplete',
            label: `${presentCount}/5`
        };
    }

    function getIntegrityFilter() {
        return currentIntegrityFilter;
    }

    function setIntegrityFilter(filter) {
        currentIntegrityFilter = filter || 'all';
        if (currentAreaNode) {
            renderAreaGrid(currentAreaNode);
        }
    }

    function parseYearOrDate(val, isEnd = false) {
        if (!val) return isEnd ? new Date() : null;
        const str = String(val).trim();
        if (!str || str.toLowerCase() === 'present' || str === 'الآن' || str === 'none' || str === 'null') {
            return new Date();
        }
        // Check ISO format YYYY-MM-DD or YYYY-MM
        const iso = str.match(/^(\d{4})(?:-(\d{1,2})(?:-(\d{1,2}))?)?/);
        if (iso) {
            const y = parseInt(iso[1], 10);
            const m = iso[2] ? parseInt(iso[2], 10) - 1 : (isEnd ? 11 : 0);
            const d = iso[3] ? parseInt(iso[3], 10) : (isEnd ? 28 : 1);
            return new Date(y, m, d);
        }
        // Check DD-MM-YYYY or DD/MM/YYYY
        const dmy = str.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})/);
        if (dmy) {
            const d = parseInt(dmy[1], 10);
            const m = parseInt(dmy[2], 10) - 1;
            const y = parseInt(dmy[3], 10);
            return new Date(y, m, d);
        }
        // Fallback: any 4-digit year
        const match = str.match(/(\d{4})/);
        if (match) {
            const y = parseInt(match[1], 10);
            return new Date(y, isEnd ? 11 : 0, isEnd ? 28 : 1);
        }
        return null;
    }

    function isTenantActive(t) {
        if (!t) return false;
        // Applicants are never resident tenants
        if (t.is_resident === 0 || t.is_resident === false) return false;

        // If explicitly assigned duration_category by backend, it is an active resident
        if (t.duration_category) return true;

        // Check end_date
        if (!t.end_date) return true;
        const eStr = String(t.end_date).trim().toLowerCase();
        if (eStr === 'present' || eStr === 'الآن' || eStr === 'none' || eStr === 'null' || eStr === '') return true;

        // Check subtitle for 'Present' or 'الآن'
        if (t.subtitle && /(?:Present|الآن)/i.test(t.subtitle)) return true;

        // If end_date is a date string, compare to today's date YYYY-MM-DD
        const todayStr = new Date().toISOString().slice(0, 10);
        if (eStr >= todayStr) return true;

        return false;
    }

    function getActiveTenantStayDays(t) {
        if (!t) return 0;
        const now = new Date();

        if (t.start_date) {
            const sDate = parseYearOrDate(t.start_date, false);
            if (sDate) {
                const diffMs = now.getTime() - sDate.getTime();
                if (diffMs > 0) {
                    return diffMs / (1000 * 60 * 60 * 24);
                }
            }
        }

        if (t.subtitle) {
            const yMatch = t.subtitle.match(/\((\d+)\s*(?:y|سنة|عام)\)/i);
            if (yMatch) {
                return parseInt(yMatch[1], 10) * 365.25;
            }
            const rangeMatch = t.subtitle.match(/(\d{4})\s*[-–]\s*(?:Present|الآن)/i);
            if (rangeMatch) {
                const sY = parseInt(rangeMatch[1], 10);
                const sDate = new Date(sY, 0, 1);
                return Math.max(0, (now.getTime() - sDate.getTime()) / (1000 * 60 * 60 * 24));
            }
            const anyYear = t.subtitle.match(/(\d{4})/);
            if (anyYear) {
                const sY = parseInt(anyYear[1], 10);
                const sDate = new Date(sY, 0, 1);
                return Math.max(0, (now.getTime() - sDate.getTime()) / (1000 * 60 * 60 * 24));
            }
        }

        if (t.duration_category === 'long') return 11 * 365.25;
        if (t.duration_category === 'medium') return 7 * 365.25;
        if (t.duration_category === 'short') return 2 * 365.25;

        return 1;
    }

    function getPastTenantStayDays(tenant) {
        if (!tenant) return 0;
        if (tenant.is_resident === 0 || tenant.is_resident === false) return 0;

        if (tenant.start_date && tenant.end_date) {
            const sDate = parseYearOrDate(tenant.start_date, false);
            const eDate = parseYearOrDate(tenant.end_date, true);
            if (sDate && eDate) {
                const diffMs = eDate.getTime() - sDate.getTime();
                if (diffMs > 0) return diffMs / (1000 * 60 * 60 * 24);
            }
        }

        if (tenant.subtitle) {
            const rangeMatch = tenant.subtitle.match(/(\d{4})\s*[-–]\s*(\d{4})/);
            if (rangeMatch) {
                const sY = parseInt(rangeMatch[1], 10);
                const eY = parseInt(rangeMatch[2], 10);
                return Math.max(0, eY - sY) * 365.25;
            }
        }

        return 0;
    }

    function getTenantStayDays(tenant) {
        if (!tenant) return 0;
        if (tenant.is_resident === 0 || tenant.is_resident === false) return 0;
        if (isTenantActive(tenant)) {
            return getActiveTenantStayDays(tenant);
        }
        return getPastTenantStayDays(tenant);
    }

    function getHouseActiveStayDays(house) {
        if (!house) return 0;

        let maxActiveDays = 0;
        let hasActive = false;

        const tenants = (house.children || []).filter(c => c.type === 'tenant' || c.name);

        for (const t of tenants) {
            const isNamedCurrent = Boolean(house.current_tenant && t.name === house.current_tenant);
            if (isNamedCurrent || isTenantActive(t)) {
                hasActive = true;
                const days = getActiveTenantStayDays(t);
                if (days > maxActiveDays) {
                    maxActiveDays = days;
                }
            }
        }

        if (house.subtitle) {
            const now = new Date();
            const yMatch = house.subtitle.match(/\((\d+)\s*(?:y|سنة|عام)\)/i);
            if (yMatch) {
                hasActive = true;
                const days = parseInt(yMatch[1], 10) * 365.25;
                if (days > maxActiveDays) maxActiveDays = days;
            } else {
                const sinceMatch = house.subtitle.match(/(?:Since|من|بدء الإيجار)\s*(\d{4})/i);
                if (sinceMatch) {
                    hasActive = true;
                    const sY = parseInt(sinceMatch[1], 10);
                    const sDate = new Date(sY, 0, 1);
                    const days = Math.max(0, (now.getTime() - sDate.getTime()) / (1000 * 60 * 60 * 24));
                    if (days > maxActiveDays) maxActiveDays = days;
                } else {
                    const rangeMatch = house.subtitle.match(/(\d{4})\s*[-–]\s*(?:Present|الآن)/i);
                    if (rangeMatch) {
                        hasActive = true;
                        const sY = parseInt(rangeMatch[1], 10);
                        const sDate = new Date(sY, 0, 1);
                        const days = Math.max(0, (now.getTime() - sDate.getTime()) / (1000 * 60 * 60 * 24));
                        if (days > maxActiveDays) maxActiveDays = days;
                    }
                }
            }
        }

        if (typeof house.tenure_duration_years === 'number' && house.tenure_duration_years > 0) {
            hasActive = true;
            const days = house.tenure_duration_years * 365.25;
            if (days > maxActiveDays) maxActiveDays = days;
        }

        if (house.current_tenant && house.current_tenant.trim()) {
            hasActive = true;
        }

        if (maxActiveDays === 0 && (hasActive || house.duration_category)) {
            if (house.duration_category === 'long') maxActiveDays = 11 * 365.25;
            else if (house.duration_category === 'medium') maxActiveDays = 7 * 365.25;
            else if (house.duration_category === 'short') maxActiveDays = 2 * 365.25;
            else if (hasActive) maxActiveDays = 1;
        }

        return maxActiveDays;
    }

    function isHouseOccupied(house) {
        if (!house) return false;
        if (house.current_tenant && house.current_tenant.trim()) return true;
        if (house.duration_category) return true;
        if (getHouseActiveStayDays(house) > 0) return true;
        const tenants = (house.children || []).filter(c => c.type === 'tenant' || c.name);
        return tenants.some(t => isTenantActive(t));
    }

    function getHousePastMaxStayDays(house) {
        if (!house || !house.children) return 0;
        let maxPast = 0;
        const tenants = house.children.filter(c => c.type === 'tenant' || c.name);
        for (const t of tenants) {
            if (t.is_resident === 0 || t.is_resident === false) continue;
            if (isTenantActive(t)) continue;

            let stay = 0;
            if (t.start_date && t.end_date) {
                const sDate = parseYearOrDate(t.start_date, false);
                const eDate = parseYearOrDate(t.end_date, true);
                if (sDate && eDate) {
                    const diffMs = eDate.getTime() - sDate.getTime();
                    if (diffMs > 0) stay = diffMs / (1000 * 60 * 60 * 24);
                }
            } else if (t.subtitle) {
                const rangeMatch = t.subtitle.match(/(\d{4})\s*[-–]\s*(\d{4})/);
                if (rangeMatch) {
                    const sY = parseInt(rangeMatch[1], 10);
                    const eY = parseInt(rangeMatch[2], 10);
                    stay = Math.max(0, eY - sY) * 365.25;
                }
            }
            if (stay > maxPast) maxPast = stay;
        }

        if (house.subtitle) {
            const rangeMatch = house.subtitle.match(/(\d{4})\s*[-–]\s*(\d{4})/);
            if (rangeMatch) {
                const sY = parseInt(rangeMatch[1], 10);
                const eY = parseInt(rangeMatch[2], 10);
                const stay = Math.max(0, eY - sY) * 365.25;
                if (stay > maxPast) maxPast = stay;
            }
        }

        return maxPast;
    }

    function getHouseMaxStayDays(house) {
        if (!house) return 0;
        if (isHouseOccupied(house)) {
            return getHouseActiveStayDays(house);
        }
        return 0;
    }

    function compareHouseNumbers(a, b) {
        const nameA = String(a && (a.name || a.id) || '');
        const nameB = String(b && (b.name || b.id) || '');
        return nameA.localeCompare(nameB, undefined, { numeric: true, sensitivity: 'base' });
    }

    function compareHouseLongestStay(a, b) {
        const occA = isHouseOccupied(a);
        const occB = isHouseOccupied(b);

        // 1. Occupied houses always sort before vacant houses
        if (occA && !occB) return -1;
        if (!occA && occB) return 1;

        // 2. Both occupied: sort by active tenant stay descending
        if (occA && occB) {
            const stayA = getHouseMaxStayDays(a);
            const stayB = getHouseMaxStayDays(b);
            if (Math.abs(stayB - stayA) >= 0.5) {
                return stayB - stayA; // Descending: longest stay first
            }
            return compareHouseNumbers(a, b);
        }

        // 3. Both vacant: sort by longest past tenant stay descending
        const pastA = getHousePastMaxStayDays(a);
        const pastB = getHousePastMaxStayDays(b);
        if (Math.abs(pastB - pastA) >= 0.5) {
            return pastB - pastA;
        }

        // 4. Tie-break by house number
        return compareHouseNumbers(a, b);
    }

    function compareHouseIntegrityWorst(a, b) {
        const occA = isHouseOccupied(a);
        const occB = isHouseOccupied(b);

        // 1. Occupied before vacant
        if (occA && !occB) return -1;
        if (!occA && occB) return 1;

        // 2. Both occupied
        if (occA && occB) {
            const intA = computeHouseIntegrity(a);
            const intB = computeHouseIntegrity(b);

            // Incomplete houses first
            if (!intA.isComplete && intB.isComplete) return -1;
            if (intA.isComplete && !intB.isComplete) return 1;

            // Both incomplete: fewest present documents first (0/5 before 4/5)
            if (!intA.isComplete && !intB.isComplete) {
                if (intA.presentCount !== intB.presentCount) {
                    return intA.presentCount - intB.presentCount;
                }
            }

            // Both complete or same present count: tie-break by house number
            return compareHouseNumbers(a, b);
        }

        // 3. Both vacant: sort by house number
        return compareHouseNumbers(a, b);
    }

    function compareHouseIntegrityBest(a, b) {
        const occA = isHouseOccupied(a);
        const occB = isHouseOccupied(b);

        // 1. Occupied before vacant
        if (occA && !occB) return -1;
        if (!occA && occB) return 1;

        // 2. Both occupied
        if (occA && occB) {
            const intA = computeHouseIntegrity(a);
            const intB = computeHouseIntegrity(b);

            // Complete houses first
            if (intA.isComplete && !intB.isComplete) return -1;
            if (!intA.isComplete && intB.isComplete) return 1;

            // Both incomplete: most present documents first (4/5 before 1/5)
            if (!intA.isComplete && !intB.isComplete) {
                if (intB.presentCount !== intA.presentCount) {
                    return intB.presentCount - intA.presentCount;
                }
            }

            // Tie-break by house number
            return compareHouseNumbers(a, b);
        }

        // 3. Both vacant
        return compareHouseNumbers(a, b);
    }

    function updateActiveFilterBadge(incompleteCount, completeCount, vacantCount) {
        const badge = document.getElementById('grid-view-active-filter-badge');
        if (!badge) return;

        if (currentIntegrityFilter === 'incomplete') {
            const countStr = typeof incompleteCount === 'number' ? ` (${incompleteCount})` : '';
            badge.textContent = `Incomplete${countStr}`;
            badge.className = 'text-[10px] px-2 py-0.5 rounded-full font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-800';
            badge.classList.remove('hidden');
        } else if (currentIntegrityFilter === 'complete') {
            const countStr = typeof completeCount === 'number' ? ` (${completeCount})` : '';
            badge.textContent = `Complete${countStr}`;
            badge.className = 'text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800';
            badge.classList.remove('hidden');
        } else if (currentIntegrityFilter === 'vacant') {
            const countStr = typeof vacantCount === 'number' ? ` (${vacantCount})` : '';
            badge.textContent = `Vacant${countStr}`;
            badge.className = 'text-[10px] px-2 py-0.5 rounded-full font-bold bg-slate-200 text-slate-800 dark:bg-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-600';
            badge.classList.remove('hidden');
        } else {
            badge.textContent = '';
            badge.className = 'hidden';
        }
    }

    function initGridViewOptions() {
        if (typeof document === 'undefined') return;
        const btn = document.getElementById('btn-grid-view-options');
        const popover = document.getElementById('grid-view-popover');
        if (!btn || !popover) return;

        btn.onclick = (e) => {
            e.stopPropagation();
            const isOpen = !popover.classList.contains('hidden');
            if (isOpen) {
                closeGridViewOptions();
            } else {
                openGridViewOptions();
            }
        };

        popover.onclick = (e) => {
            e.stopPropagation();
        };

        if (!document._gridViewListenersAttached) {
            document._gridViewListenersAttached = true;

            document.addEventListener('click', (e) => {
                const livePopover = document.getElementById('grid-view-popover');
                const liveBtn = document.getElementById('btn-grid-view-options');
                if (livePopover && !livePopover.classList.contains('hidden')) {
                    if (!livePopover.contains(e.target) && (!liveBtn || !liveBtn.contains(e.target))) {
                        closeGridViewOptions();
                    }
                }
            });

            document.addEventListener('keydown', (e) => {
                const livePopover = document.getElementById('grid-view-popover');
                if (e.key === 'Escape' && livePopover && !livePopover.classList.contains('hidden')) {
                    closeGridViewOptions();
                }
            });
        }
    }

    function openGridViewOptions() {
        const btn = document.getElementById('btn-grid-view-options');
        const popover = document.getElementById('grid-view-popover');
        const chevron = document.getElementById('grid-view-chevron');
        if (!popover) return;
        popover.classList.remove('hidden');
        if (btn) btn.setAttribute('aria-expanded', 'true');
        if (chevron) chevron.classList.add('rotate-180');
    }

    function closeGridViewOptions() {
        const btn = document.getElementById('btn-grid-view-options');
        const popover = document.getElementById('grid-view-popover');
        const chevron = document.getElementById('grid-view-chevron');
        if (!popover) return;
        popover.classList.add('hidden');
        if (btn) btn.setAttribute('aria-expanded', 'false');
        if (chevron) chevron.classList.remove('rotate-180');
    }

    function renderIntegrityFilterPills(totalCount, incompleteCount, completeCount, vacantCount) {
        const container = document.getElementById('grid-integrity-pills');
        const summary = document.getElementById('grid-integrity-summary');
        if (!container) return;

        const filters = [
            { id: 'all', label: 'All Houses', count: totalCount, activeClass: 'bg-blue-600 text-white shadow-xs', icon: '' },
            { id: 'incomplete', label: '⚠️ Incomplete', count: incompleteCount, activeClass: 'bg-amber-600 text-white shadow-xs', icon: '' },
            { id: 'complete', label: '✓ Complete', count: completeCount, activeClass: 'bg-emerald-600 text-white shadow-xs', icon: '' },
            { id: 'vacant', label: 'Vacant', count: vacantCount, activeClass: 'bg-slate-700 text-white shadow-xs', icon: '' }
        ];

        container.innerHTML = filters.map(f => {
            const isActive = (currentIntegrityFilter === f.id);
            const btnClass = isActive
                ? `${f.activeClass} font-bold ring-1 ring-black/10 dark:ring-white/20`
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 font-medium';

            return `
                <button type="button" class="grid-filter-pill px-2.5 py-1.5 rounded-xl text-xs transition-all cursor-pointer flex items-center justify-between gap-1.5 select-none ${btnClass}" data-filter="${f.id}">
                    <span class="truncate">${f.label}</span>
                    <span class="text-[10px] px-1.5 py-0.5 rounded-full ${isActive ? 'bg-white/25 text-white' : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300'} font-bold">${f.count}</span>
                </button>
            `;
        }).join('');

        container.querySelectorAll('.grid-filter-pill').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                setIntegrityFilter(btn.dataset.filter);
            });
        });

        if (summary) {
            if (incompleteCount > 0) {
                summary.innerHTML = `
                    <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60">
                        <span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
                        <span>${incompleteCount} req. docs</span>
                    </span>
                `;
            } else {
                summary.innerHTML = `
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60">
                        <svg class="w-3 h-3 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
                        <span>100% compliant</span>
                    </span>
                `;
            }
        }

        updateActiveFilterBadge(incompleteCount, completeCount, vacantCount);
    }

    function formatLatestTenantStay(house) {
        if (!house) return 'Vacant';
        const occupied = isHouseOccupied(house);

        if (occupied) {
            const days = getHouseActiveStayDays(house);
            let startYear = null;
            if (house.subtitle) {
                const sMatch = house.subtitle.match(/(?:Since|من|بدء الإيجار)\s*(\d{4})/i) || house.subtitle.match(/(\d{4})/);
                if (sMatch) startYear = sMatch[1];
            }
            if (!startYear) {
                const activeT = (house.children || []).find(t => (house.current_tenant && t.name === house.current_tenant) || isTenantActive(t));
                if (activeT && activeT.start_date) {
                    const m = String(activeT.start_date).match(/(\d{4})/);
                    if (m) startYear = m[1];
                }
            }

            if (days >= 365.25) {
                const years = Math.floor(days / 365.25);
                const remDays = days % 365.25;
                const months = Math.floor(remDays / 30.4375);
                let durationStr = `${years} ${years === 1 ? 'Year' : 'Years'}`;
                if (years < 5 && months > 0) {
                    durationStr = `${years} ${years === 1 ? 'Year' : 'Years'}, ${months} ${months === 1 ? 'Mo' : 'Mos'}`;
                }
                return startYear ? `${durationStr} (Since ${startYear})` : durationStr;
            } else if (days > 0) {
                const months = Math.max(1, Math.round(days / 30.4375));
                const durationStr = `${months} ${months === 1 ? 'Month' : 'Months'}`;
                return startYear ? `${durationStr} (Since ${startYear})` : durationStr;
            } else {
                return startYear ? `Recent (Since ${startYear})` : 'Recent Resident';
            }
        }

        // Vacant house: check past tenant stay if any
        const pastDays = getHousePastMaxStayDays(house);
        if (pastDays >= 365.25) {
            const pastYears = Math.floor(pastDays / 365.25);
            return `Vacant (Past: ${pastYears}y)`;
        }
        return 'Vacant';
    }

    function getHouseSortPreference() {
        try {
            if (typeof localStorage !== 'undefined') {
                const val = localStorage.getItem('house_sort_by');
                if (['longest_stay', 'number', 'integrity_worst', 'integrity_best'].includes(val)) {
                    return val;
                }
            }
        } catch (_) {}
        return 'number';
    }

    function initHouseSortControl() {
        if (typeof document === 'undefined') return;
        const select = document.getElementById('grid-house-sort-select');
        if (!select) return;
        select.value = getHouseSortPreference();
        select.onchange = (e) => {
            const val = e.target.value;
            try {
                if (typeof localStorage !== 'undefined') {
                    localStorage.setItem('house_sort_by', val);
                }
            } catch (_) {}
            if (currentAreaNode) {
                renderAreaGrid(currentAreaNode);
            }
        };
    }

    function selectAreaGrid(areaNode) {
        if (!areaNode) return;
        if (typeof window !== 'undefined' && window.globalTreeData && Array.isArray(window.globalTreeData)) {
            const fresh = window.globalTreeData.find(a => a.name === areaNode.name || a.id === areaNode.id);
            if (fresh) areaNode = fresh;
        }
        try { currentArea = areaNode.name; } catch (_) {}
        try { currentHouse = null; } catch (_) {}
        try { currentTenant = null; } catch (_) {}
        if (typeof window !== 'undefined') {
            window.currentArea = areaNode.name;
            window.currentHouse = null;
            window.currentTenant = null;
            if (window.location) {
                window.location.hash = `#/area/${encodeURIComponent(areaNode.name)}`;
            }
        }
        renderAreaGrid(areaNode);
    }

    function renderAreaGrid(areaNode) {
        if (!areaNode) return;
        if (typeof window !== 'undefined' && window.globalTreeData && Array.isArray(window.globalTreeData)) {
            const fresh = window.globalTreeData.find(a => a.name === areaNode.name || a.id === areaNode.id);
            if (fresh) areaNode = fresh;
        }
        document.querySelectorAll('.area-grid-btn').forEach(b => {
            if (b.dataset.areaName === areaNode.name) {
                b.classList.add('bg-slate-800', 'text-white', 'border-slate-700');
                b.classList.remove('text-slate-300');
            } else {
                b.classList.remove('bg-slate-800', 'text-white', 'border-slate-700');
                b.classList.add('text-slate-300');
            }
        });

        const welcomePanel = document.getElementById('welcome-panel');
        const documentEmptyState = document.getElementById('document-empty-state');
        const docListPanel = document.getElementById('document-list-panel');
        const docViewerPanel = document.getElementById('document-viewer-panel');
        const resizer2 = document.getElementById('resizer-2');
        const backToGridBtn = document.getElementById('back-to-grid-btn');
        const tabBackToTenants = document.getElementById('tab-back-to-tenants');
        const areaGridPanel = document.getElementById('area-grid-panel');
        const currentHouseTitle = document.getElementById('current-house-title');
        const statsBadge = document.getElementById('stats-badge');
        const gridAreaTitle = document.getElementById('grid-area-title');
        const gridAreaStats = document.getElementById('grid-area-stats');
        const gridTenureLegend = document.getElementById('grid-tenure-legend');
        const gridHouseSortContainer = document.getElementById('grid-house-sort-container');
        const gridHouseSortSelect = document.getElementById('grid-house-sort-select');
        const gridViewOptionsWrapper = document.getElementById('grid-view-options-wrapper');
        const gridIntegrityToolbar = document.getElementById('grid-integrity-toolbar');
        const openAddHouseBtn = document.getElementById('open-add-house-modal-btn');
        const houseCardsContainer = document.getElementById('area-grid-container') || document.getElementById('house-cards-container');

        if (welcomePanel) welcomePanel.classList.add('hidden');
        if (documentEmptyState) {
            documentEmptyState.classList.add('hidden');
            documentEmptyState.classList.remove('flex');
        }
        if (docListPanel) {
            docListPanel.classList.add('hidden');
            docListPanel.classList.remove('flex');
        }
        if (docViewerPanel) docViewerPanel.classList.add('hidden');
        if (resizer2) resizer2.classList.add('hidden');
        if (backToGridBtn) backToGridBtn.classList.add('hidden');
        if (tabBackToTenants) {
            tabBackToTenants.classList.add('hidden');
            tabBackToTenants.classList.remove('flex');
        }

        if (areaGridPanel) {
            areaGridPanel.classList.remove('hidden');
            areaGridPanel.classList.add('flex');
        }

        if (currentHouseTitle) currentHouseTitle.textContent = `${areaNode.name} — Houses Overview`;
        if (statsBadge) statsBadge.classList.add('hidden');

        currentAreaNode = areaNode;
        initHouseSortControl();
        initGridViewOptions();

        if (gridViewOptionsWrapper) {
            gridViewOptionsWrapper.classList.remove('hidden');
            gridViewOptionsWrapper.classList.add('flex');
        }

        if (gridHouseSortContainer) {
            gridHouseSortContainer.classList.remove('hidden');
            gridHouseSortContainer.classList.add('flex');
        }
        if (gridTenureLegend) {
            gridTenureLegend.classList.remove('hidden');
            gridTenureLegend.classList.add('flex');
        }
        if (gridIntegrityToolbar) {
            gridIntegrityToolbar.classList.remove('hidden');
        }
        const sortBy = getHouseSortPreference();
        if (gridHouseSortSelect) {
            gridHouseSortSelect.value = sortBy;
        }

        if (gridAreaTitle) gridAreaTitle.textContent = areaNode.name;
        const rawHouses = areaNode.children || [];

        // 1. Calculate integrity counts across all houses in the area
        let incompleteCount = 0;
        let completeCount = 0;
        let vacantCount = 0;

        rawHouses.forEach(h => {
            const intg = computeHouseIntegrity(h);
            if (intg.isVacant) {
                vacantCount++;
            } else if (intg.isComplete) {
                completeCount++;
            } else {
                incompleteCount++;
            }
        });

        renderIntegrityFilterPills(rawHouses.length, incompleteCount, completeCount, vacantCount);

        // 2. Filter houses by currentIntegrityFilter
        let filteredHouses = rawHouses;
        if (currentIntegrityFilter === 'incomplete') {
            filteredHouses = rawHouses.filter(h => {
                const intg = computeHouseIntegrity(h);
                return intg.isOccupied && !intg.isComplete;
            });
        } else if (currentIntegrityFilter === 'complete') {
            filteredHouses = rawHouses.filter(h => {
                const intg = computeHouseIntegrity(h);
                return intg.isOccupied && intg.isComplete;
            });
        } else if (currentIntegrityFilter === 'vacant') {
            filteredHouses = rawHouses.filter(h => !isHouseOccupied(h));
        }

        const houses = [...filteredHouses];
        if (sortBy === 'longest_stay') {
            houses.sort(compareHouseLongestStay);
        } else if (sortBy === 'integrity_worst') {
            houses.sort(compareHouseIntegrityWorst);
        } else if (sortBy === 'integrity_best') {
            houses.sort(compareHouseIntegrityBest);
        } else {
            houses.sort(compareHouseNumbers);
        }

        if (gridAreaStats) {
            gridAreaStats.textContent = `${rawHouses.length} Houses`;
            gridAreaStats.classList.remove('hidden');
        }
        if (gridTenureLegend) {
            gridTenureLegend.classList.remove('hidden');
            gridTenureLegend.classList.add('flex');
        }
        if (!houseCardsContainer) return;
        houseCardsContainer.innerHTML = '';

        if (rawHouses.length > 0 && houses.length === 0) {
            let emptyTitle = 'No houses found';
            let emptyMsg = 'No houses match the current filter in this area.';
            let emptyIcon = '🔍';

            if (currentIntegrityFilter === 'incomplete') {
                emptyTitle = 'All Houses Compliant!';
                emptyMsg = 'Every occupied house in this area has all 5 mandatory documents in place.';
                emptyIcon = '🎉';
            } else if (currentIntegrityFilter === 'complete') {
                emptyTitle = 'No Fully Complete Houses';
                emptyMsg = 'No occupied houses currently have all 5 mandatory documents.';
                emptyIcon = '⚠️';
            } else if (currentIntegrityFilter === 'vacant') {
                emptyTitle = 'No Vacant Houses';
                emptyMsg = 'All houses in this area are currently occupied or recorded with active tenants.';
                emptyIcon = '🏠';
            }

            const filterNotice = document.createElement('div');
            filterNotice.className = 'col-span-full py-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-8 shadow-2xs';
            filterNotice.innerHTML = `
                <div class="w-12 h-12 mx-auto rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 flex items-center justify-center text-2xl mb-3">
                    ${emptyIcon}
                </div>
                <h4 class="text-sm font-bold text-slate-800 dark:text-slate-200 mb-1">${emptyTitle}</h4>
                <p class="text-xs text-slate-500 dark:text-slate-400 mb-4 max-w-sm mx-auto">${emptyMsg}</p>
                <button type="button" class="btn-reset-grid-filter px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-2xs transition-all cursor-pointer">
                    Show All Houses (${rawHouses.length})
                </button>
            `;
            const resetBtn = filterNotice.querySelector('.btn-reset-grid-filter');
            if (resetBtn) {
                resetBtn.onclick = () => setIntegrityFilter('all');
            }
            houseCardsContainer.appendChild(filterNotice);
        }

        houses.forEach(house => {
            const card = document.createElement('div');
            card.className = 'house-card group bg-white rounded-xl p-4 border border-slate-200 shadow-2xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between';
            card.dataset.houseId = house.id;

            let borderClass = 'border-l-[5px] border-l-slate-300 dark:border-l-slate-600 hover:border-slate-400';
            let badgeClass = 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700 font-medium';
            let badgeLabel = 'Vacant';

            if (house.duration_category === 'short') {
                borderClass = 'border-l-[5px] border-l-emerald-500 hover:border-emerald-400';
                badgeClass = 'bg-emerald-50 text-emerald-800 border-emerald-300 font-semibold';
                badgeLabel = '< 5 Yrs';
            } else if (house.duration_category === 'medium') {
                borderClass = 'border-l-[5px] border-l-amber-500 hover:border-amber-400';
                badgeClass = 'bg-amber-50 text-amber-800 border-amber-300 font-semibold';
                badgeLabel = '5–10 Yrs';
            } else if (house.duration_category === 'long') {
                borderClass = 'border-l-[5px] border-l-rose-500 hover:border-rose-400';
                badgeClass = 'bg-rose-50 text-rose-800 border-rose-300 font-semibold';
                badgeLabel = '> 10 Yrs';
            }
            card.className += ` ${borderClass}`;

            const allTenants = (house.children || []).filter(c => c.type === 'tenant');
            const residents = allTenants.filter(t => t.is_resident !== 0 && t.is_resident !== false);
            const applicants = allTenants.filter(t => t.is_resident === 0 || t.is_resident === false);
            const orderedTenants = [...residents, ...applicants];
            const totalDocs = house.total_documents || 0;

            let countBadgeText = '0 Tenants';
            if (residents.length > 0 && applicants.length > 0) {
                countBadgeText = `${residents.length} ${residents.length === 1 ? 'Tenant' : 'Tenants'} • ${applicants.length} ${applicants.length === 1 ? 'Applicant' : 'Applicants'}`;
            } else if (residents.length > 0) {
                countBadgeText = `${residents.length} ${residents.length === 1 ? 'Tenant' : 'Tenants'}`;
            } else if (applicants.length > 0) {
                countBadgeText = `${applicants.length} ${applicants.length === 1 ? 'Applicant' : 'Applicants'}`;
            }

            let tenantsHtml = '';
            if (orderedTenants.length === 0) {
                tenantsHtml = `
                    <div class="py-2.5 px-3 bg-slate-50 rounded-lg border border-slate-100 text-center">
                        <p class="text-[11px] text-slate-400 italic">No tenants recorded</p>
                    </div>
                `;
            } else {
                tenantsHtml = `
                    <div class="space-y-1.5">
                        ${orderedTenants.map((t, idx) => {
                            let cardBg;
                            let nameClass;
                            let tenantIcon;
                            let tenureText;

                            if (t.is_resident === 0) {
                                cardBg = 'bg-purple-50/30 border-purple-200/60 dark:bg-purple-950/20 dark:border-purple-800/40';
                                nameClass = 'font-medium text-purple-900 dark:text-purple-200';
                                tenantIcon = `<span class="w-5 h-5 rounded-md bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 flex items-center justify-center flex-shrink-0" title="Applicant • متقدم">
                                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
                                </span>`;
                                tenureText = t.subtitle ? `${t.subtitle} • متقدم` : 'Applicant • متقدم';
                            } else {
                                const isCurrent = Boolean(
                                    (house.current_tenant && t.name === house.current_tenant) 
                                    || (t.is_active === true)
                                    || (t.subtitle && (t.subtitle.includes('Present') || t.subtitle.includes('الآن')))
                                );

                                let currentCardBg = 'bg-emerald-50/70 border-emerald-200/80';
                                let currentIconBg = 'bg-emerald-100 text-emerald-700';
                                const durCat = t.duration_category || house.duration_category || 'short';
                                if (durCat === 'medium') {
                                    currentCardBg = 'bg-amber-50/70 border-amber-200/80';
                                    currentIconBg = 'bg-amber-100 text-amber-700';
                                } else if (durCat === 'long') {
                                    currentCardBg = 'bg-rose-50/70 border-rose-200/80';
                                    currentIconBg = 'bg-rose-100 text-rose-700';
                                }

                                cardBg = isCurrent 
                                    ? currentCardBg 
                                    : 'bg-slate-50 border-slate-200/60';
                                nameClass = isCurrent ? 'font-bold text-slate-900' : 'font-medium text-slate-700';
                                tenantIcon = isCurrent
                                    ? `<span class="w-5 h-5 rounded-md ${currentIconBg} flex items-center justify-center flex-shrink-0" title="Residing Tenant">
                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
                                       </span>`
                                    : `<span class="w-5 h-5 rounded-md bg-slate-200/80 text-slate-500 flex items-center justify-center flex-shrink-0" title="Past Tenant">
                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                                       </span>`;
                                tenureText = t.subtitle || '';
                            }
                            
                            return `
                                <div class="tenant-overview-item flex items-center justify-between text-xs p-1.5 rounded-lg border ${cardBg}">
                                    <div class="flex items-center gap-2 min-w-0">
                                        ${tenantIcon}
                                        <span class="tenant-name ${nameClass} truncate text-xs" title="${t.name}">${t.name}</span>
                                    </div>
                                    <span class="tenure-text text-[10px] font-mono text-slate-500 ml-2 flex-shrink-0" title="${tenureText}">
                                        ${tenureText}
                                    </span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
            }

            const integrity = computeHouseIntegrity(house);
            let integrityBadgeHtml = '';
            let missingWarningHtml = '';

            if (integrity.isVacant) {
                integrityBadgeHtml = `
                    <span class="integrity-badge text-[10px] font-semibold px-2 py-0.5 rounded-md border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 select-none" title="منزل شاغر">
                        شاغر
                    </span>
                `;
            } else if (integrity.isComplete) {
                integrityBadgeHtml = `
                    <span class="integrity-badge inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md border border-emerald-300 dark:border-emerald-800/80 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 shadow-2xs" title="الملف مكتمل: 5/5 وثائق إلزامية متوفرة">
                        <svg class="w-2.5 h-2.5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>
                        <span>5/5</span>
                    </span>
                `;
            } else {
                const missingListStr = integrity.missingCategories.map(c => c.label).join('، ');
                integrityBadgeHtml = `
                    <span class="integrity-badge inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md border border-amber-300 dark:border-amber-800/80 bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 shadow-2xs" title="وثائق ناقصة: ${missingListStr}">
                        <span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
                        <span>${integrity.presentCount}/5</span>
                    </span>
                `;

                missingWarningHtml = `
                    <div class="card-warning-divider mb-2">
                        <div class="missing-docs-strip flex items-center justify-between text-[10.5px] px-2 py-1 rounded bg-amber-50/90 dark:bg-amber-950/50 border border-amber-200/80 dark:border-amber-900/60 text-amber-800 dark:text-amber-300" title="وثائق ناقصة: ${missingListStr}">
                            <div class="flex items-center gap-1.5 min-w-0">
                                <span class="text-amber-600 dark:text-amber-400 font-bold flex-shrink-0">⚠️ ناقص:</span>
                                <span class="truncate font-medium text-[10px]">${missingListStr}</span>
                            </div>
                            <span class="font-bold text-[9.5px] bg-amber-200/80 dark:bg-amber-900/80 text-amber-900 dark:text-amber-200 px-1 rounded flex-shrink-0 mr-1">${integrity.missingCount}</span>
                        </div>
                    </div>
                `;
            }

            const scrollClass = orderedTenants.length > 3 ? 'max-h-[118px] overflow-y-auto pr-1' : '';

            let footerHtml = '';
            if (sortBy === 'longest_stay') {
                const stayFormatted = formatLatestTenantStay(house);
                let stayBadgeClass = 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700';
                if (house.duration_category === 'long') {
                    stayBadgeClass = 'bg-rose-50/80 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border-rose-200/80 dark:border-rose-900/50';
                } else if (house.duration_category === 'medium') {
                    stayBadgeClass = 'bg-amber-50/80 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border-amber-200/80 dark:border-amber-900/50';
                } else if (house.duration_category === 'short') {
                    stayBadgeClass = 'bg-emerald-50/80 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200/80 dark:border-emerald-900/50';
                }

                footerHtml = `
                    <div class="card-footer pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs gap-1.5">
                        <span class="text-slate-400 text-[11px] font-medium flex items-center gap-1 min-w-0">
                            <svg class="w-3.5 h-3.5 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                            <span class="truncate">Latest Stay</span>
                        </span>
                        <span class="stay-duration-badge font-bold ${stayBadgeClass} px-2 py-0.5 rounded-md text-[11px] border truncate max-w-[140px]" title="${stayFormatted}">
                            ${stayFormatted}
                        </span>
                    </div>
                `;
            } else {
                footerHtml = `
                    <div class="card-footer pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs gap-1.5">
                        <span class="text-slate-400 text-[11px] font-medium flex items-center gap-1 min-w-0">
                            <span>Total Archive</span>
                        </span>
                        <span class="doc-count font-bold text-slate-700 dark:text-slate-300 bg-blue-50/80 dark:bg-blue-950/40 text-blue-700 dark:text-blue-400 px-2 py-0.5 rounded-md text-[11px] border border-blue-100 dark:border-blue-900/50">
                            ${totalDocs} Docs
                        </span>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="card-main-content flex-1 min-h-0 flex flex-col">
                    <div class="flex items-center justify-between gap-2 pb-2.5 mb-2.5 border-b border-slate-100 dark:border-slate-800 flex-shrink-0">
                        <div class="flex items-center gap-1.5 min-w-0 flex-1">
                            <h3 class="font-bold text-slate-900 dark:text-slate-100 text-sm group-hover:text-blue-600 transition-colors flex-shrink-0 whitespace-nowrap" title="${house.name}">
                                🏠 ${house.name}
                            </h3>
                            <span class="tenants-count text-[10px] font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-full border border-slate-200 dark:border-slate-700 min-w-0 truncate" title="${countBadgeText}">
                                ${countBadgeText}
                            </span>
                        </div>
                        <div class="flex items-center gap-1.5 flex-shrink-0">
                            ${integrityBadgeHtml}
                            <span class="tenure-badge text-[10px] px-2 py-0.5 rounded border flex-shrink-0 ${badgeClass}">${badgeLabel}</span>
                        </div>
                    </div>

                    <div class="tenants-overview-section ${scrollClass}">
                        ${tenantsHtml}
                    </div>
                </div>

                <div class="card-bottom-zone mt-auto pt-2 flex flex-col flex-shrink-0">
                    ${missingWarningHtml}
                    ${footerHtml}
                </div>
            `;

            if (orderedTenants.length > 3) {
                const tenantsSection = card.querySelector('.tenants-overview-section');
                if (tenantsSection) {
                    tenantsSection.addEventListener('click', (e) => {
                        if (e.offsetX > e.currentTarget.clientWidth) {
                            e.stopPropagation();
                        }
                    });
                }
            }

            // Direct drag & drop ingestion onto house card
            card.addEventListener('dragover', (e) => {
                if (e.dataTransfer && e.dataTransfer.types && Array.from(e.dataTransfer.types).includes('Files')) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.dataTransfer.dropEffect = 'copy';
                    card.classList.add('ring-2', 'ring-blue-500', 'bg-blue-50/40');
                }
            });

            card.addEventListener('dragleave', (e) => {
                card.classList.remove('ring-2', 'ring-blue-500', 'bg-blue-50/40');
            });

            card.addEventListener('drop', (e) => {
                if (e.dataTransfer && e.dataTransfer.types && Array.from(e.dataTransfer.types).includes('Files')) {
                    e.preventDefault();
                    e.stopPropagation();
                    card.classList.remove('ring-2', 'ring-blue-500', 'bg-blue-50/40');
                    if (typeof window.resetDragCounter === 'function') {
                        window.resetDragCounter();
                    } else {
                        const overlay = document.getElementById('ingest-dropzone-overlay');
                        if (overlay) overlay.classList.add('hidden');
                    }
                    if (typeof window.handleDirectHouseDrop === 'function') {
                        window.handleDirectHouseDrop(e.dataTransfer.files, house.id, areaNode.name);
                    }
                }
            });

            card.onclick = () => {
                openHouseFromGrid(areaNode.name, house.id);
            };

            houseCardsContainer.appendChild(card);
        });

        // Add House Card (dashed outline with plus icon at end of grid)
        const addCard = document.createElement('div');
        addCard.id = 'add-house-grid-card';
        addCard.className = 'add-house-card group bg-slate-50/60 hover:bg-blue-50/40 border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-xl p-6 transition-all duration-200 cursor-pointer flex flex-col items-center justify-center text-center min-h-[200px] select-none';
        addCard.setAttribute('role', 'button');
        addCard.setAttribute('tabindex', '0');
        addCard.setAttribute('aria-label', 'Add New House / إضافة منزل جديد');
        addCard.title = 'Add New House / إضافة منزل جديد';
        addCard.innerHTML = `
            <div class="w-14 h-14 rounded-full bg-white border border-slate-200 text-slate-400 group-hover:text-blue-600 group-hover:border-blue-300 group-hover:scale-110 shadow-2xs flex items-center justify-center transition-all duration-200 mb-3">
                <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/></svg>
            </div>
            <h3 class="font-bold text-slate-700 group-hover:text-blue-600 text-sm transition-colors">إضافة منزل جديد</h3>
            <p class="text-xs font-medium text-slate-400 mt-1">Add New House</p>
        `;
        addCard.onclick = () => {
            openAddHouseModal(areaNode.name);
        };
        addCard.onkeydown = (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                openAddHouseModal(areaNode.name);
            }
        };
        houseCardsContainer.appendChild(addCard);
    }

    function openHouseFromGrid(areaName, houseId) {
        currentArea = areaName;
        currentHouse = houseId;
        currentTenant = null;

        const areaGridPanel = document.getElementById('area-grid-panel');
        if (areaGridPanel) {
            areaGridPanel.classList.add('hidden');
            areaGridPanel.classList.remove('flex');
        }
        const gridViewOptionsWrapper = document.getElementById('grid-view-options-wrapper');
        if (gridViewOptionsWrapper) {
            gridViewOptionsWrapper.classList.add('hidden');
            gridViewOptionsWrapper.classList.remove('flex');
        }
        closeGridViewOptions();
        const gridAreaStats = document.getElementById('grid-area-stats');
        const gridTenureLegend = document.getElementById('grid-tenure-legend');
        const gridHouseSortContainer = document.getElementById('grid-house-sort-container');
        const gridIntegrityToolbar = document.getElementById('grid-integrity-toolbar');
        const openAddHouseBtn = document.getElementById('open-add-house-modal-btn');
        if (gridAreaStats) gridAreaStats.classList.add('hidden');
        if (gridTenureLegend) {
            gridTenureLegend.classList.add('hidden');
            gridTenureLegend.classList.remove('flex', 'grid');
        }
        if (gridHouseSortContainer) {
            gridHouseSortContainer.classList.add('hidden');
            gridHouseSortContainer.classList.remove('flex', 'block');
        }
        if (gridIntegrityToolbar) {
            gridIntegrityToolbar.classList.add('hidden');
        }
        if (openAddHouseBtn) {
            openAddHouseBtn.classList.add('hidden');
            openAddHouseBtn.classList.remove('inline-flex');
        }

        window.location.hash = `#/area/${encodeURIComponent(areaName)}/house/${encodeURIComponent(houseId)}`;
    }

    function openAddHouseModal(preselectedArea) {
        const modal = document.getElementById('add-house-modal');
        if (!modal) return;

        const areaSelect = document.getElementById('add-house-area-select');
        const idInput = document.getElementById('add-house-id-input');
        const tenantInput = document.getElementById('add-house-tenant-name-input');
        const dateInput = document.getElementById('add-house-tenant-date-input');
        const statusEl = document.getElementById('add-house-status');
        const spinner = document.getElementById('add-house-spinner');
        const submitBtn = document.getElementById('btn-add-house-submit');

        if (statusEl) {
            statusEl.classList.add('hidden');
            statusEl.textContent = '';
            statusEl.className = 'p-2.5 rounded-lg text-xs font-medium hidden';
        }
        if (spinner) spinner.classList.add('hidden');
        if (submitBtn) submitBtn.disabled = false;

        if (idInput) idInput.value = '';
        if (tenantInput) tenantInput.value = '';
        if (dateInput) {
            try {
                dateInput.value = new Date().toISOString().split('T')[0];
            } catch (e) {
                dateInput.value = '';
            }
        }

        // Populate area options
        if (areaSelect) {
            areaSelect.innerHTML = '';
            const tree = (typeof globalTreeData !== 'undefined' ? globalTreeData : window.globalTreeData) || [];
            const targetArea = preselectedArea || (typeof currentArea !== 'undefined' ? currentArea : window.currentArea);

            if (tree.length > 0) {
                tree.forEach(a => {
                    const opt = document.createElement('option');
                    opt.value = a.name || a.id;
                    opt.textContent = a.name || a.id;
                    if (targetArea && (a.name === targetArea || a.id === targetArea)) {
                        opt.selected = true;
                    }
                    areaSelect.appendChild(opt);
                });
            } else if (targetArea) {
                const opt = document.createElement('option');
                opt.value = targetArea;
                opt.textContent = targetArea;
                opt.selected = true;
                areaSelect.appendChild(opt);
            }
        }

        modal.classList.remove('hidden');
        if (idInput) {
            setTimeout(() => idInput.focus(), 50);
        }
    }

    function closeAddHouseModal() {
        const modal = document.getElementById('add-house-modal');
        if (modal) modal.classList.add('hidden');
    }

    async function handleAddHouseSubmit(e) {
        if (e && typeof e.preventDefault === 'function') e.preventDefault();

        const areaSelect = document.getElementById('add-house-area-select');
        const idInput = document.getElementById('add-house-id-input');
        const tenantInput = document.getElementById('add-house-tenant-name-input');
        const dateInput = document.getElementById('add-house-tenant-date-input');
        const statusEl = document.getElementById('add-house-status');
        const spinner = document.getElementById('add-house-spinner');
        const submitBtn = document.getElementById('btn-add-house-submit');

        const areaId = areaSelect ? areaSelect.value.trim() : '';
        const houseId = idInput ? idInput.value.trim() : '';
        const tenantName = tenantInput ? tenantInput.value.trim() : '';
        const startDate = dateInput ? dateInput.value.trim() : '';

        if (!areaId) {
            showModalError('يرجى تحديد المنطقة / Please select an area.');
            return;
        }

        if (!houseId) {
            showModalError('يرجى إدخال رقم أو اسم المنزل / House number or name is required.');
            if (idInput) idInput.focus();
            return;
        }

        if (statusEl) {
            statusEl.classList.add('hidden');
            statusEl.textContent = '';
        }
        if (spinner) spinner.classList.remove('hidden');
        if (submitBtn) submitBtn.disabled = true;

        try {
            const payload = {
                house_id: houseId,
                area_id: areaId,
                initial_tenant_name: tenantName || null,
                start_date: startDate || null,
            };

            const res = await fetch(`/api/areas/${encodeURIComponent(areaId)}/houses`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                let errText = `Error ${res.status}`;
                try {
                    const errData = await res.json();
                    errText = errData.detail || errData.error || errData.message || errText;
                } catch (_) {}
                throw new Error(errText);
            }

            const data = await res.json();
            closeAddHouseModal();
            if (typeof showToast === 'function') {
                showToast('تمت إضافة المنزل بنجاح', 'success');
            } else if (typeof window.showToast === 'function') {
                window.showToast('تمت إضافة المنزل بنجاح', 'success');
            }

            await loadAreaGrid(areaId);
            return data;
        } catch (err) {
            showModalError(err.message || 'فشل إضافة المنزل / Failed to create house');
        } finally {
            if (spinner) spinner.classList.add('hidden');
            if (submitBtn) submitBtn.disabled = false;
        }
    }

    function showModalError(msg) {
        const statusEl = document.getElementById('add-house-status');
        if (statusEl) {
            statusEl.className = 'p-2.5 rounded-lg text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200';
            statusEl.textContent = msg;
            statusEl.classList.remove('hidden');
        }
    }

    async function loadAreaGrid(areaId) {
        if (typeof window.loadTree === 'function') {
            await window.loadTree();
        }
        const tree = (typeof globalTreeData !== 'undefined' ? globalTreeData : window.globalTreeData) || [];
        const target = areaId || (typeof currentArea !== 'undefined' ? currentArea : window.currentArea);
        if (target && tree.length > 0) {
            const areaNode = tree.find(a => a.name === target || a.id === target);
            if (areaNode) {
                renderAreaGrid(areaNode);
            }
        }
    }

    function initAddHouseModal() {
        const openBtn = document.getElementById('open-add-house-modal-btn');
        if (openBtn) {
            openBtn.onclick = () => {
                const targetArea = (typeof currentArea !== 'undefined' ? currentArea : window.currentArea);
                openAddHouseModal(targetArea);
            };
        }

        const closeBtn = document.getElementById('add-house-close');
        if (closeBtn) closeBtn.onclick = closeAddHouseModal;

        const cancelBtn = document.getElementById('btn-add-house-cancel');
        if (cancelBtn) cancelBtn.onclick = closeAddHouseModal;

        const submitBtn = document.getElementById('btn-add-house-submit');
        if (submitBtn) submitBtn.onclick = handleAddHouseSubmit;

        const form = document.getElementById('add-house-form');
        if (form) form.onsubmit = handleAddHouseSubmit;

        const modal = document.getElementById('add-house-modal');
        if (modal) {
            modal.onclick = (e) => {
                if (e.target === modal) closeAddHouseModal();
            };
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const m = document.getElementById('add-house-modal');
                if (m && !m.classList.contains('hidden')) {
                    closeAddHouseModal();
                }
            }
        });
    }

    if (typeof document !== 'undefined') {
        const initAll = () => {
            initAddHouseModal();
            initHouseSortControl();
            initGridViewOptions();
        };
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initAll);
        } else {
            initAll();
        }
    }

    window.selectAreaGrid = selectAreaGrid;
    window.renderAreaGrid = renderAreaGrid;
    window.openHouseFromGrid = openHouseFromGrid;
    window.openAddHouseModal = openAddHouseModal;
    window.closeAddHouseModal = closeAddHouseModal;
    window.handleAddHouseSubmit = handleAddHouseSubmit;
    window.initAddHouseModal = initAddHouseModal;
    window.loadAreaGrid = loadAreaGrid;
    window.compareHouseNumbers = compareHouseNumbers;
    window.compareHouseLongestStay = compareHouseLongestStay;
    window.getHouseMaxStayDays = getHouseMaxStayDays;
    window.getHouseActiveStayDays = getHouseActiveStayDays;
    window.getHousePastMaxStayDays = getHousePastMaxStayDays;
    window.isHouseOccupied = isHouseOccupied;
    window.isTenantActive = isTenantActive;
    window.getActiveTenantStayDays = getActiveTenantStayDays;
    window.getPastTenantStayDays = getPastTenantStayDays;
    window.formatLatestTenantStay = formatLatestTenantStay;
    window.getHouseSortPreference = getHouseSortPreference;
    window.initHouseSortControl = initHouseSortControl;
    window.initGridViewOptions = initGridViewOptions;
    window.openGridViewOptions = openGridViewOptions;
    window.closeGridViewOptions = closeGridViewOptions;
    window.updateActiveFilterBadge = updateActiveFilterBadge;
    window.MANDATORY_INTEGRITY_CATEGORIES = MANDATORY_INTEGRITY_CATEGORIES;
    window.computeHouseIntegrity = computeHouseIntegrity;
    window.compareHouseIntegrityWorst = compareHouseIntegrityWorst;
    window.compareHouseIntegrityBest = compareHouseIntegrityBest;
    window.getIntegrityFilter = getIntegrityFilter;
    window.setIntegrityFilter = setIntegrityFilter;
    window.renderIntegrityFilterPills = renderIntegrityFilterPills;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            selectAreaGrid,
            renderAreaGrid,
            openHouseFromGrid,
            openAddHouseModal,
            closeAddHouseModal,
            handleAddHouseSubmit,
            initAddHouseModal,
            loadAreaGrid,
            compareHouseNumbers,
            compareHouseLongestStay,
            getHouseMaxStayDays,
            getHouseActiveStayDays,
            getHousePastMaxStayDays,
            isHouseOccupied,
            isTenantActive,
            getActiveTenantStayDays,
            getPastTenantStayDays,
            formatLatestTenantStay,
            getHouseSortPreference,
            initHouseSortControl,
            initGridViewOptions,
            openGridViewOptions,
            closeGridViewOptions,
            updateActiveFilterBadge,
            MANDATORY_INTEGRITY_CATEGORIES,
            computeHouseIntegrity,
            compareHouseIntegrityWorst,
            compareHouseIntegrityBest,
            getIntegrityFilter,
            setIntegrityFilter,
            renderIntegrityFilterPills,
        };
    }
})();
