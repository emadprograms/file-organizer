// ── Router & View Controller ──────────────────────────────────────────────
(function() {
    function switchToViewMode(mode) {
        if (currentViewMode === mode) return;
        currentViewMode = mode;

        const sidebarSectionTitle = document.getElementById('sidebar-section-title');
        const welcomePanel = document.getElementById('welcome-panel');
        const docListPanel = document.getElementById('document-list-panel');
        const docViewerPanel = document.getElementById('document-viewer-panel');
        const resizer2 = document.getElementById('resizer-2');
        const backToGridBtn = document.getElementById('back-to-grid-btn');
        const tabBackToTenants = document.getElementById('tab-back-to-tenants');
        const areaGridPanel = document.getElementById('area-grid-panel');
        const databaseInspectorPanel = document.getElementById('database-inspector-panel');
        const currentHouseTitle = document.getElementById('current-house-title');
        const statsBadge = document.getElementById('stats-badge');

        if (currentViewMode === 'db') {
            if (sidebarSectionTitle) sidebarSectionTitle.textContent = "Database";

            if (welcomePanel) welcomePanel.classList.add('hidden');
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
                areaGridPanel.classList.add('hidden');
                areaGridPanel.classList.remove('flex');
            }
            const gridAreaStats = document.getElementById('grid-area-stats');
            const gridTenureLegend = document.getElementById('grid-tenure-legend');
            const openAddHouseBtn = document.getElementById('open-add-house-modal-btn');
            if (gridAreaStats) gridAreaStats.classList.add('hidden');
            if (gridTenureLegend) {
                gridTenureLegend.classList.add('hidden');
                gridTenureLegend.classList.remove('flex');
            }
            if (openAddHouseBtn) {
                openAddHouseBtn.classList.add('hidden');
                openAddHouseBtn.classList.remove('inline-flex');
            }

            if (databaseInspectorPanel) {
                databaseInspectorPanel.classList.remove('hidden');
                databaseInspectorPanel.classList.add('flex');
            }

            if (currentHouseTitle) currentHouseTitle.textContent = "Database Inspector";
            if (statsBadge) statsBadge.classList.add('hidden');
            window.location.hash = "/database";

            if (typeof window.loadDbInspector === 'function') {
                window.loadDbInspector();
            }
        } else {
            currentViewMode = 'overview';
            if (sidebarSectionTitle) sidebarSectionTitle.textContent = "Areas";

            if (databaseInspectorPanel) {
                databaseInspectorPanel.classList.add('hidden');
                databaseInspectorPanel.classList.remove('flex');
            }

            if (typeof window.renderSidebar === 'function') {
                window.renderSidebar();
            }

            if (!isTreeLoading && globalTreeData && globalTreeData.length > 0) {
                if (currentArea) {
                    const areaNode = globalTreeData.find(a => a.name === currentArea);
                    if (areaNode && typeof window.selectAreaGrid === 'function') {
                        window.selectAreaGrid(areaNode);
                    } else if (typeof window.selectAreaGrid === 'function') {
                        window.selectAreaGrid(globalTreeData[0]);
                    }
                } else if (typeof window.selectAreaGrid === 'function') {
                    window.selectAreaGrid(globalTreeData[0]);
                }
            }
        }
    }

    function handleHashChange() {
        const rawHash = decodeURIComponent(window.location.hash.replace('#', ''));
        const hash = rawHash.startsWith('/') ? rawHash : '/' + rawHash;
        if (!rawHash || hash === '/') {
            if (globalTreeData && globalTreeData.length > 0 && typeof window.selectAreaGrid === 'function') {
                window.selectAreaGrid(globalTreeData[0]);
            }
            return;
        }

        if (hash === '/database' || hash === '/db') {
            if (currentViewMode !== 'db') {
                switchToViewMode('db');
            }
            return;
        }

        if (hash.startsWith('/grid/area/')) {
            const areaName = decodeURIComponent(hash.replace('/grid/area/', ''));
            const areaNode = globalTreeData.find(a => a.name === areaName);
            if (areaNode && typeof window.selectAreaGrid === 'function') {
                window.selectAreaGrid(areaNode);
            }
            return;
        }

        const parts = hash.split('/');
        let areaId = null, houseId = null, tenantId = null;
        for (let i = 0; i < parts.length; i++) {
            if (parts[i] === 'area' && i + 1 < parts.length) areaId = decodeURIComponent(parts[i+1]).replace(/^area_/, '');
            if (parts[i] === 'house' && i + 1 < parts.length) houseId = decodeURIComponent(parts[i+1]);
            if (parts[i] === 'tenant' && i + 1 < parts.length) tenantId = decodeURIComponent(parts[i+1]);
        }

        if (areaId && !houseId) {
            const areaNode = globalTreeData.find(a => a.name === areaId);
            if (areaNode && typeof window.selectAreaGrid === 'function') {
                window.selectAreaGrid(areaNode);
            }
            return;
        }

        let tenantName = null;
        if (tenantId && houseId && tenantId.startsWith(houseId + '_')) {
            tenantName = tenantId.substring(houseId.length + 1);
        }

        const tabCategories = document.getElementById('tab-categories');
        const tabTimeline = document.getElementById('tab-timeline');
        if (tenantName && currentTab !== 'categories' && tabCategories && tabTimeline) {
            currentTab = 'categories';
            tabCategories.className = "flex-1 py-1.5 px-3 text-xs font-semibold rounded-md bg-white text-blue-600 shadow-xs flex items-center justify-center gap-1.5 transition-all";
            tabTimeline.className = "flex-1 py-1.5 px-3 text-xs font-medium rounded-md text-slate-600 hover:text-slate-900 flex items-center justify-center gap-1.5 transition-all";
        }

        if (areaId && houseId) {
            selectHouse(areaId, houseId, tenantName);
        }

        document.querySelectorAll('.area-grid-btn').forEach(b => {
            if (b.dataset.areaName === areaId) {
                b.classList.add('bg-slate-800', 'text-white', 'border-slate-700');
                b.classList.remove('text-slate-300');
            } else {
                b.classList.remove('bg-slate-800', 'text-white', 'border-slate-700');
                b.classList.add('text-slate-300');
            }
        });
    }

    async function selectHouse(areaId, houseId, tenantName) {
        currentArea = areaId;
        currentHouse = houseId;
        currentTenant = tenantName;
        window.currentArea = areaId;
        window.currentHouse = houseId;
        window.currentTenant = tenantName;

        const currentHouseTitle = document.getElementById('current-house-title');
        const tabCategoriesLabel = document.getElementById('tab-categories-label');
        const tabTimelineLabel = document.getElementById('tab-timeline-label');
        const areaGridPanel = document.getElementById('area-grid-panel');
        const tabBackToTenants = document.getElementById('tab-back-to-tenants');
        const backToGridBtn = document.getElementById('back-to-grid-btn');
        const welcomePanel = document.getElementById('welcome-panel');
        const docListPanel = document.getElementById('document-list-panel');
        const docViewerPanel = document.getElementById('document-viewer-panel');
        const resizer2 = document.getElementById('resizer-2');

        if (currentHouseTitle) {
            if (tenantName) {
                currentHouseTitle.innerHTML = `
                    <div class="flex items-center gap-2">
                        <span class="text-slate-500 font-medium">${houseId}</span>
                        <span class="text-slate-300 font-light">/</span>
                        <span class="text-slate-900 font-bold">${tenantName}</span>
                    </div>
                `;
            } else {
                currentHouseTitle.textContent = `${houseId}`;
            }
        }

        if (tabCategoriesLabel) {
            tabCategoriesLabel.textContent = tenantName ? 'Folders' : 'سجل المستأجرين';
        }
        const tabCategoriesIcon = document.getElementById('tab-categories-icon') || document.querySelector('#tab-categories svg');
        if (tabCategoriesIcon) {
            if (tenantName) {
                tabCategoriesIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>';
            } else {
                tabCategoriesIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>';
            }
        }
        if (tabTimelineLabel) {
            tabTimelineLabel.textContent = tenantName ? 'Tenant Timeline' : 'House Timeline';
        }

        if (areaGridPanel) {
            areaGridPanel.classList.add('hidden');
            areaGridPanel.classList.remove('flex');
        }
        const gridAreaStats = document.getElementById('grid-area-stats');
        const gridTenureLegend = document.getElementById('grid-tenure-legend');
        const openAddHouseBtn = document.getElementById('open-add-house-modal-btn');
        if (gridAreaStats) gridAreaStats.classList.add('hidden');
        if (gridTenureLegend) {
            gridTenureLegend.classList.add('hidden');
            gridTenureLegend.classList.remove('flex');
        }
        if (openAddHouseBtn) {
            openAddHouseBtn.classList.add('hidden');
            openAddHouseBtn.classList.remove('inline-flex');
        }

        if (tabBackToTenants) {
            if (tenantName) {
                tabBackToTenants.classList.remove('hidden');
                tabBackToTenants.classList.add('flex');
            } else {
                tabBackToTenants.classList.add('hidden');
                tabBackToTenants.classList.remove('flex');
            }
        }

        if (backToGridBtn) {
            backToGridBtn.classList.remove('hidden');
            backToGridBtn.classList.add('flex');
            const gridLabel = `${areaId} Houses`;
            backToGridBtn.innerHTML = `
                <svg class="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
                <span>${gridLabel}</span>
            `;
        }

        if (welcomePanel) welcomePanel.classList.add('hidden');
        if (docListPanel) {
            docListPanel.classList.remove('hidden');
            docListPanel.classList.add('flex');
        }
        if (resizer2) resizer2.classList.remove('hidden');
        if (docViewerPanel) docViewerPanel.classList.add('hidden');

        await refreshCurrentTab(areaId, houseId);
    }

    async function refreshCurrentTab(areaId, houseId) {
        if (currentTab === 'timeline') {
            if (typeof window.loadTimeline === 'function') {
                await window.loadTimeline(areaId, houseId);
            }
        } else {
            if (!currentTenant) {
                if (typeof window.loadHouseProfile === 'function') {
                    await window.loadHouseProfile(areaId, houseId);
                }
            } else {
                if (typeof window.loadCategories === 'function') {
                    await window.loadCategories(areaId, houseId);
                }
            }
        }
    }

    window.addEventListener('hashchange', handleHashChange);

    window.switchToViewMode = switchToViewMode;
    window.handleHashChange = handleHashChange;
    window.selectHouse = selectHouse;
    window.refreshCurrentTab = refreshCurrentTab;
})();
