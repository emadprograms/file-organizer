// ── Application Core Controller ───────────────────────────────────────────
(function() {
    function initApp() {
        const viewModeTreeBtn = document.getElementById('view-mode-tree');
        const viewModeGridBtn = document.getElementById('view-mode-grid');
        const viewModeDbBtn = document.getElementById('view-mode-db');
        const backToGridBtn = document.getElementById('back-to-grid-btn');
        const backToTenantsBtn = document.getElementById('back-to-tenants-btn');
        const tabTimeline = document.getElementById('tab-timeline');
        const tabCategories = document.getElementById('tab-categories');

        // View mode & navigation controls
        if (viewModeTreeBtn) viewModeTreeBtn.addEventListener('click', () => switchToViewMode('overview'));
        if (viewModeGridBtn) viewModeGridBtn.addEventListener('click', () => switchToViewMode('overview'));
        if (viewModeDbBtn) {
            viewModeDbBtn.addEventListener('click', () => {
                if (currentViewMode === 'db') {
                    switchToViewMode('overview');
                } else {
                    switchToViewMode('db');
                }
            });
        }
        
        if (backToGridBtn) {
            backToGridBtn.addEventListener('click', () => {
                if (currentArea) {
                    const areaNode = globalTreeData.find(a => a.name === currentArea);
                    if (areaNode && typeof window.selectAreaGrid === 'function') {
                        window.selectAreaGrid(areaNode);
                    } else {
                        window.location.hash = `#/area/${encodeURIComponent(currentArea)}`;
                    }
                } else if (globalTreeData.length > 0 && typeof window.selectAreaGrid === 'function') {
                    window.selectAreaGrid(globalTreeData[0]);
                }
            });
        }

        if (backToTenantsBtn) {
            backToTenantsBtn.addEventListener('click', () => {
                if (currentArea && currentHouse) {
                    window.location.hash = `#/area/${encodeURIComponent(currentArea)}/house/${encodeURIComponent(currentHouse)}`;
                }
            });
        }

        // Segmented Tabs
        if (tabTimeline) {
            tabTimeline.addEventListener('click', () => {
                if (currentTab === 'timeline') return;
                currentTab = 'timeline';
                tabTimeline.className = "flex-1 py-1.5 px-3 text-xs font-semibold rounded-md bg-white text-blue-600 shadow-xs flex items-center justify-center gap-1.5 transition-all";
                if (tabCategories) tabCategories.className = "flex-1 py-1.5 px-3 text-xs font-medium rounded-md text-slate-600 hover:text-slate-900 flex items-center justify-center gap-1.5 transition-all";
                if (currentArea && currentHouse && typeof window.refreshCurrentTab === 'function') {
                    window.refreshCurrentTab(currentArea, currentHouse);
                }
            });
        }

        if (tabCategories) {
            tabCategories.addEventListener('click', () => {
                if (currentTab === 'categories') return;
                currentTab = 'categories';
                tabCategories.className = "flex-1 py-1.5 px-3 text-xs font-semibold rounded-md bg-white text-blue-600 shadow-xs flex items-center justify-center gap-1.5 transition-all";
                if (tabTimeline) tabTimeline.className = "flex-1 py-1.5 px-3 text-xs font-medium rounded-md text-slate-600 hover:text-slate-900 flex items-center justify-center gap-1.5 transition-all";
                if (currentArea && currentHouse && typeof window.refreshCurrentTab === 'function') {
                    window.refreshCurrentTab(currentArea, currentHouse);
                }
            });
        }

        // Initialize sub-components
        if (typeof window.initPdfPreview === 'function') {
            window.initPdfPreview();
        }
        if (typeof window.initDbInspector === 'function') {
            window.initDbInspector();
        }
        if (typeof window.setupResizer === 'function') {
            window.setupResizer('resizer-1', 'main-sidebar', false);
            window.setupResizer('resizer-2', 'document-list-panel', true);
        }

        // Load initial area hierarchy
        if (typeof window.loadTree === 'function') {
            window.loadTree();
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initApp);
    } else {
        initApp();
    }
})();
