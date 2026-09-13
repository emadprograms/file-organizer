// ── Sidebar & Area Tree Component ─────────────────────────────────────────
(function() {
    async function loadTree() {
        isTreeLoading = true;
        renderSidebar();
        try {
            let res = null;
            try {
                res = await fetch(API_TREE);
                if (!res.ok) throw new Error();
            } catch (e) {
                res = await fetch('./tree.json');
                if (res && res.ok) {
                    isStaticMode = true;
                }
            }
            if (!res || !res.ok) throw new Error('Failed to load tree');
            const treeData = await res.json();
            globalTreeData = treeData;
            isTreeLoading = false;
            
            renderSidebar();
            if (typeof window.handleHashChange === 'function') {
                window.handleHashChange();
            }
        } catch (err) {
            isTreeLoading = false;
            const houseListEl = document.getElementById('house-list');
            if (houseListEl) {
                houseListEl.innerHTML = '<div class="p-2 text-rose-500 text-xs">Error loading data. <button onclick="window.loadTree()" class="ml-1 underline text-blue-500 hover:text-blue-700">Retry</button></div>';
            }
        }
    }

    function renderSidebar() {
        const houseListEl = document.getElementById('house-list');
        const areaGridPanel = document.getElementById('area-grid-panel');
        if (!houseListEl) return;
        houseListEl.innerHTML = '';
        if (isTreeLoading) {
            houseListEl.innerHTML = '<p class="text-slate-500 text-xs px-2 py-1">Loading...</p>';
            return;
        }
        if (!globalTreeData || globalTreeData.length === 0) {
            houseListEl.innerHTML = '<p class="text-slate-500 text-xs px-2 py-1">No areas found.</p>';
            return;
        }

        const ul = document.createElement('ul');
        ul.className = 'space-y-1';
        globalTreeData.forEach(areaNode => {
            const li = document.createElement('li');
            const btn = document.createElement('button');
            btn.className = 'area-grid-btn w-full text-left px-3 py-2 rounded-lg text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white focus:outline-none flex items-center justify-between transition-colors border border-transparent';
            btn.dataset.areaName = areaNode.name;
            if (currentArea === areaNode.name && areaGridPanel && !areaGridPanel.classList.contains('hidden')) {
                btn.classList.add('bg-slate-800', 'text-white', 'border-slate-700');
                btn.classList.remove('text-slate-300');
            }
            const houseCount = (areaNode.children || []).length;
            btn.innerHTML = `
                <div class="flex items-center gap-2 truncate">
                    <span class="text-slate-400 flex-shrink-0">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                    </span>
                    <span class="truncate">${areaNode.name}</span>
                </div>
                <span class="text-[10px] font-mono text-slate-400 bg-slate-800/80 border border-slate-700/60 px-2 py-0.5 rounded-full">${houseCount} Houses</span>
            `;
            btn.onclick = (e) => {
                e.stopPropagation();
                if (typeof window.selectAreaGrid === 'function') {
                    window.selectAreaGrid(areaNode);
                }
            };
            li.appendChild(btn);
            ul.appendChild(li);
        });
        houseListEl.appendChild(ul);
    }

    function isSidebarCollapsed() {
        const sidebar = document.getElementById('main-sidebar');
        if (!sidebar) return false;
        return sidebar.classList.contains('hidden');
    }

    function toggleSidebar(forceCollapsed) {
        const sidebar = document.getElementById('main-sidebar');
        const resizer = document.getElementById('resizer-1');
        const toggleBtn = document.getElementById('sidebar-toggle-btn');
        if (!sidebar) return;

        const currentCollapsed = isSidebarCollapsed();
        const willCollapse = typeof forceCollapsed === 'boolean' ? forceCollapsed : !currentCollapsed;

        if (willCollapse) {
            if (sidebar.style.width && sidebar.style.width !== '0px') {
                try {
                    localStorage.setItem('sidebar_width', sidebar.style.width);
                } catch (e) {}
            }
            sidebar.classList.add('hidden');
            if (resizer) resizer.classList.add('hidden');

            if (toggleBtn) {
                toggleBtn.title = 'Expand sidebar (Ctrl+B) • توسيع الشريط الجانبي';
                toggleBtn.setAttribute('aria-expanded', 'false');
                toggleBtn.classList.add('text-blue-600', 'dark:text-blue-400', 'bg-blue-50', 'dark:bg-blue-900/30', 'border-blue-200', 'dark:border-blue-800');
            }
            try {
                localStorage.setItem('sidebar_collapsed', 'true');
            } catch (e) {}
        } else {
            try {
                const savedWidth = localStorage.getItem('sidebar_width');
                if (savedWidth) {
                    sidebar.style.width = savedWidth;
                }
            } catch (e) {}

            sidebar.classList.remove('hidden');
            if (resizer) resizer.classList.remove('hidden');

            if (toggleBtn) {
                toggleBtn.title = 'Collapse sidebar (Ctrl+B) • طي الشريط الجانبي';
                toggleBtn.setAttribute('aria-expanded', 'true');
                toggleBtn.classList.remove('text-blue-600', 'dark:text-blue-400', 'bg-blue-50', 'dark:bg-blue-900/30', 'border-blue-200', 'dark:border-blue-800');
            }
            try {
                localStorage.setItem('sidebar_collapsed', 'false');
            } catch (e) {}
        }
    }

    function initSidebarCollapse() {
        const toggleBtn = document.getElementById('sidebar-toggle-btn');
        const collapseBtn = document.getElementById('sidebar-collapse-btn');

        if (toggleBtn && !toggleBtn._hasSidebarListener) {
            toggleBtn._hasSidebarListener = true;
            toggleBtn.onclick = (e) => {
                e.preventDefault();
                toggleSidebar();
            };
        }

        if (collapseBtn && !collapseBtn._hasSidebarListener) {
            collapseBtn._hasSidebarListener = true;
            collapseBtn.onclick = (e) => {
                e.preventDefault();
                toggleSidebar(true);
            };
        }

        try {
            const savedState = localStorage.getItem('sidebar_collapsed');
            if (savedState === 'true') {
                toggleSidebar(true);
            }
        } catch (e) {}

        if (typeof window !== 'undefined' && !window._sidebarShortcutAttached) {
            window._sidebarShortcutAttached = true;
            document.addEventListener('keydown', (e) => {
                const isB = e.code === 'KeyB' || (e.key && e.key.toLowerCase() === 'b');
                if (isB && (e.ctrlKey || e.metaKey) && !e.altKey) {
                    const activeEl = document.activeElement;
                    const tag = ((activeEl && activeEl.tagName) || (e.target && e.target.tagName) || '').toLowerCase();
                    if (tag === 'input' || tag === 'textarea' || tag === 'select' || (activeEl && activeEl.isContentEditable) || (e.target && e.target.isContentEditable)) {
                        return;
                    }
                    e.preventDefault();
                    toggleSidebar();
                }
            });
        }
    }

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initSidebarCollapse);
        } else {
            initSidebarCollapse();
        }
    }

    window.loadTree = loadTree;
    window.renderSidebar = renderSidebar;
    window.isSidebarCollapsed = isSidebarCollapsed;
    window.toggleSidebar = toggleSidebar;
    window.initSidebarCollapse = initSidebarCollapse;
})();
