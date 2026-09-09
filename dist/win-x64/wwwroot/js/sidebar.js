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

    window.loadTree = loadTree;
    window.renderSidebar = renderSidebar;
})();
