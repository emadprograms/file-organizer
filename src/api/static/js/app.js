// ── Application Core Controller ───────────────────────────────────────────
(function() {
    // DOM Elements
    let houseListEl = null;
    let currentHouseTitle = null;
    let statsBadge = null;
    let viewModeTreeBtn = null;
    let viewModeGridBtn = null;
    let viewModeDbBtn = null;
    let backToGridBtn = null;
    let areaGridPanel = null;
    let databaseInspectorPanel = null;
    let gridAreaTitle = null;
    let gridAreaStats = null;
    let houseCardsContainer = null;
    let sidebarSectionTitle = null;
    let tabTimeline = null;
    let tabCategories = null;
    let tabTimelineLabel = null;
    let tabCategoriesLabel = null;
    let docListPanel = null;
    let docViewerPanel = null;
    let welcomePanel = null;
    let docListEl = null;
    let pdfFrame = null;
    let viewerTitle = null;
    let viewerDownload = null;

    // PDF Hover Preview State & Elements
    let previewTooltip = null;
    let previewIframe = null;
    let previewTitleEl = null;
    let previewShowTimer = null;
    let previewHideTimer = null;
    let previewCurrentUrl = null;
    const PREVIEW_GAP = 12;
    const PREVIEW_DELAY_MS = 350;

    // Database Inspector State
    let currentDbTable = 'houses';
    let dbTableOffset = 0;
    const dbTableLimit = 50;
    let dbTableTotal = 0;
    let dbTableSearchTerm = '';

    const FOLDER_PREFIXES = {
        "بيانات شخصية": "01",
        "عقد الإيجار": "02",
        "سند أمر": "03",
        "إشعار": "04",
        "مخالصة": "05",
        "سند قبض": "06",
        "استقطاع": "07",
        "إلغاء استقطاع": "08",
        "حكم قضائي": "09",
        "طلب إخلاء": "10",
        "مستندات أخرى": "99"
    };

    function initApp() {
        houseListEl = document.getElementById('house-list');
        currentHouseTitle = document.getElementById('current-house-title');
        statsBadge = document.getElementById('stats-badge');
        viewModeTreeBtn = document.getElementById('view-mode-tree');
        viewModeGridBtn = document.getElementById('view-mode-grid');
        viewModeDbBtn = document.getElementById('view-mode-db');
        backToGridBtn = document.getElementById('back-to-grid-btn');
        areaGridPanel = document.getElementById('area-grid-panel');
        databaseInspectorPanel = document.getElementById('database-inspector-panel');
        gridAreaTitle = document.getElementById('grid-area-title');
        gridAreaStats = document.getElementById('grid-area-stats');
        houseCardsContainer = document.getElementById('area-grid-container') || document.getElementById('house-cards-container');
        sidebarSectionTitle = document.getElementById('sidebar-section-title');
        tabTimeline = document.getElementById('tab-timeline');
        tabCategories = document.getElementById('tab-categories');
        tabTimelineLabel = document.getElementById('tab-timeline-label');
        tabCategoriesLabel = document.getElementById('tab-categories-label');
        docListPanel = document.getElementById('document-list-panel');
        docViewerPanel = document.getElementById('document-viewer-panel');
        welcomePanel = document.getElementById('welcome-panel');
        docListEl = document.getElementById('document-list');
        pdfFrame = document.getElementById('pdf-frame');
        viewerTitle = document.getElementById('viewer-title');
        viewerDownload = document.getElementById('viewer-download');

        // Hover Preview elements
        previewTooltip = document.getElementById('pdf-preview-tooltip');
        previewIframe = document.getElementById('pdf-preview-iframe');
        previewTitleEl = document.getElementById('pdf-preview-title');

        if (previewTooltip) {
            previewTooltip.addEventListener('mouseenter', () => clearTimeout(previewHideTimer));
            previewTooltip.addEventListener('mouseleave', hidePreview);
        }

        // View mode tabs
        if (viewModeTreeBtn) viewModeTreeBtn.addEventListener('click', () => switchToViewMode('tree'));
        if (viewModeGridBtn) viewModeGridBtn.addEventListener('click', () => switchToViewMode('grid'));
        if (viewModeDbBtn) viewModeDbBtn.addEventListener('click', () => switchToViewMode('db'));
        
        if (backToGridBtn) {
            backToGridBtn.addEventListener('click', () => {
                if (currentArea) {
                    const areaNode = globalTreeData.find(a => a.name === currentArea);
                    if (areaNode) {
                        selectAreaGrid(areaNode);
                    } else {
                        window.location.hash = `/grid/area/${encodeURIComponent(currentArea)}`;
                    }
                } else if (globalTreeData.length > 0) {
                    selectAreaGrid(globalTreeData[0]);
                }
            });
        }

        // Tabs
        if (tabTimeline) {
            tabTimeline.addEventListener('click', () => {
                if (currentTab === 'timeline') return;
                currentTab = 'timeline';
                tabTimeline.className = "flex-1 py-1.5 px-3 text-xs font-semibold rounded-md bg-white text-blue-600 shadow-xs flex items-center justify-center gap-1.5 transition-all";
                tabCategories.className = "flex-1 py-1.5 px-3 text-xs font-medium rounded-md text-slate-600 hover:text-slate-900 flex items-center justify-center gap-1.5 transition-all";
                if (currentArea && currentHouse) {
                    refreshCurrentTab(currentArea, currentHouse);
                }
            });
        }

        if (tabCategories) {
            tabCategories.addEventListener('click', () => {
                if (currentTab === 'categories') return;
                currentTab = 'categories';
                tabCategories.className = "flex-1 py-1.5 px-3 text-xs font-semibold rounded-md bg-white text-blue-600 shadow-xs flex items-center justify-center gap-1.5 transition-all";
                tabTimeline.className = "flex-1 py-1.5 px-3 text-xs font-medium rounded-md text-slate-600 hover:text-slate-900 flex items-center justify-center gap-1.5 transition-all";
                if (currentArea && currentHouse) {
                    refreshCurrentTab(currentArea, currentHouse);
                }
            });
        }

        // DB Inspector listeners
        const dbRefreshBtn = document.getElementById('db-refresh-btn');
        if (dbRefreshBtn) dbRefreshBtn.addEventListener('click', () => loadDbInspector());

        const dbTableSearch = document.getElementById('db-table-search');
        if (dbTableSearch) {
            dbTableSearch.addEventListener('input', (e) => {
                dbTableSearchTerm = e.target.value.trim();
                dbTableOffset = 0;
                loadDbTableRows();
            });
        }

        const dbPrevPage = document.getElementById('db-prev-page');
        if (dbPrevPage) {
            dbPrevPage.addEventListener('click', () => {
                if (dbTableOffset >= dbTableLimit) {
                    dbTableOffset -= dbTableLimit;
                    loadDbTableRows();
                }
            });
        }

        const dbNextPage = document.getElementById('db-next-page');
        if (dbNextPage) {
            dbNextPage.addEventListener('click', () => {
                if (dbTableOffset + dbTableLimit < dbTableTotal) {
                    dbTableOffset += dbTableLimit;
                    loadDbTableRows();
                }
            });
        }

        // Setup resizers
        setupResizer('resizer-1', 'main-sidebar', false);
        setupResizer('resizer-2', 'document-list-panel', true);

        // Load initial tree
        loadTree();
    }

    // ── PDF Hover Preview Functions ──────────────────────────────────────────
    function positionTooltip(mouseX, mouseY) {
        if (!previewTooltip) return;
        const tw = previewTooltip.offsetWidth;
        const th = previewTooltip.offsetHeight;
        const vw = window.innerWidth;
        const vh = window.innerHeight;

        let left = mouseX + PREVIEW_GAP;
        let top = mouseY - 60;

        if (left + tw > vw - 8) left = mouseX - tw - PREVIEW_GAP;
        if (top + th > vh - 8) top = vh - th - 8;
        if (top < 8) top = 8;

        previewTooltip.style.left = `${left}px`;
        previewTooltip.style.top = `${top}px`;
    }

    function showPreview(vaultId, title, mouseX, mouseY) {
        if (!previewTooltip || !previewIframe) return;
        const pdfUrl = getPdfUrl(currentArea, currentHouse, vaultId) + '#toolbar=0&view=FitH';

        clearTimeout(previewHideTimer);
        clearTimeout(previewShowTimer);

        previewShowTimer = setTimeout(() => {
            if (previewCurrentUrl !== pdfUrl) {
                previewCurrentUrl = pdfUrl;
                previewIframe.src = pdfUrl;
                if (previewTitleEl) previewTitleEl.textContent = title;
            }
            positionTooltip(mouseX, mouseY);
            previewTooltip.classList.add('visible');
        }, PREVIEW_DELAY_MS);
    }

    function hidePreview() {
        clearTimeout(previewShowTimer);
        previewHideTimer = setTimeout(() => {
            if (previewTooltip) previewTooltip.classList.remove('visible');
        }, 100);
    }

    function attachPreview(el, vaultId, title) {
        el.addEventListener('mouseenter', (e) => showPreview(vaultId, title, e.clientX, e.clientY));
        el.addEventListener('mousemove', (e) => {
            if (previewTooltip && previewTooltip.classList.contains('visible')) {
                positionTooltip(e.clientX, e.clientY);
            }
        });
        el.addEventListener('mouseleave', hidePreview);
    }

    // ── Tree & Sidebar ───────────────────────────────────────────────────────
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
            handleHashChange();
        } catch (err) {
            isTreeLoading = false;
            if (houseListEl) {
                houseListEl.innerHTML = '<div class="p-2 text-rose-500 text-xs">Error loading data. <button onclick="window.loadTree()" class="ml-1 underline text-blue-500 hover:text-blue-700">Retry</button></div>';
            }
        }
    }

    function renderSidebar() {
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

        if (currentViewMode === 'tree') {
            const ul = document.createElement('ul');
            ul.className = 'space-y-0.5';
            createTreeNodes(globalTreeData, ul, '', '');
            houseListEl.appendChild(ul);
        } else {
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
                    selectAreaGrid(areaNode);
                };
                li.appendChild(btn);
                ul.appendChild(li);
            });
            houseListEl.appendChild(ul);
        }
    }

    function createTreeNodes(nodes, parentEl, parentPath, parentArea) {
        nodes.forEach(node => {
            const li = document.createElement('li');
            const currentPath = parentPath ? `${parentPath}/${node.type}/${node.id}` : `/${node.type}/${node.id}`;
            li.dataset.path = currentPath;
            li.className = 'tree-node group/node select-none';

            const btn = document.createElement('button');
            btn.className = 'w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800/80 hover:text-white focus:outline-none flex items-center tree-item transition-all';
            
            const icon = document.createElement('span');
            icon.className = 'tree-chevron mr-2 text-slate-400 text-[10px] w-3.5 h-3.5 inline-flex items-center justify-center flex-shrink-0 font-mono select-none transition-colors';
            icon.innerHTML = (node.children && node.children.length > 0) ? '▶' : '•';
            btn.appendChild(icon);

            const typeIcon = document.createElement('span');
            typeIcon.className = 'mr-1.5 flex-shrink-0 flex items-center justify-center';
            if (node.type === 'area') {
                typeIcon.innerHTML = `<svg class="w-4 h-4 text-blue-400 flex-shrink-0 tree-type-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>`;
            } else if (node.type === 'house') {
                typeIcon.innerHTML = `<svg class="w-3.5 h-3.5 text-slate-400 group-hover/node:text-slate-300 flex-shrink-0 tree-type-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>`;
            } else if (node.type === 'tenant') {
                typeIcon.innerHTML = `<svg class="w-3.5 h-3.5 text-slate-400 group-hover/node:text-slate-300 flex-shrink-0 tree-type-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>`;
            }
            btn.appendChild(typeIcon);
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'flex items-center justify-between w-full overflow-hidden min-w-0';
            
            const nameSpan = document.createElement('span');
            nameSpan.textContent = node.name;
            nameSpan.className = (node.type === 'area') 
                ? 'truncate text-left font-semibold text-slate-200 text-xs tracking-tight' 
                : (node.type === 'house' ? 'truncate text-left text-xs font-medium text-slate-200' : 'truncate text-left text-xs text-slate-300');
            contentDiv.appendChild(nameSpan);

            const metaDiv = document.createElement('div');
            metaDiv.className = 'flex items-center ml-2 flex-shrink-0 gap-1.5';

            if (node.subtitle) {
                const subSpan = document.createElement('span');
                subSpan.textContent = node.subtitle;
                if (node.duration_category === 'short') {
                    subSpan.className = 'text-[9px] leading-none text-green-700 text-emerald-400 bg-emerald-950/80 border border-emerald-500/40 px-2 py-0.5 rounded-full font-bold shadow-2xs';
                } else if (node.duration_category === 'medium') {
                    subSpan.className = 'text-[9px] leading-none text-yellow-700 text-amber-300 bg-amber-950/80 border border-amber-500/40 px-2 py-0.5 rounded-full font-bold shadow-2xs';
                } else if (node.duration_category === 'long') {
                    subSpan.className = 'text-[9px] leading-none text-red-700 text-rose-300 bg-rose-950/80 border border-rose-500/40 px-2 py-0.5 rounded-full font-bold shadow-2xs';
                } else {
                    subSpan.className = 'text-[9px] leading-none text-slate-400 bg-slate-800 border border-slate-700 px-1.5 py-0.5 rounded-full font-medium';
                }
                metaDiv.appendChild(subSpan);
            } else if (node.type === 'area' && node.children && node.children.length > 0) {
                const countSpan = document.createElement('span');
                countSpan.className = 'text-[10px] font-mono text-slate-400 bg-slate-800/90 border border-slate-700/60 px-1.5 py-0.2 rounded-full font-normal';
                countSpan.textContent = `${node.children.length}`;
                metaDiv.appendChild(countSpan);
            }

            contentDiv.appendChild(metaDiv);
            btn.appendChild(contentDiv);
            li.appendChild(btn);

            let childrenContainer = null;
            if (node.children && node.children.length > 0) {
                childrenContainer = document.createElement('ul');
                childrenContainer.className = 'pl-2.5 hidden space-y-0.5 mt-0.5 border-l border-slate-800 ml-3.5';
                createTreeNodes(node.children, childrenContainer, currentPath, node.type === 'area' ? node.name : parentArea);
                li.appendChild(childrenContainer);

                btn.onclick = (e) => {
                    e.stopPropagation();
                    const isHidden = childrenContainer.classList.contains('hidden');
                    if (isHidden) {
                        childrenContainer.classList.remove('hidden');
                        icon.innerHTML = '▼';
                    } else {
                        childrenContainer.classList.add('hidden');
                        icon.innerHTML = '▶';
                    }
                    if (node.type === 'house' && parentArea) {
                        window.location.hash = currentPath;
                    }
                };
            }

            if (node.type === 'tenant') {
                btn.setAttribute('data-tenant-name', node.name);
                if (typeof window.handleTenantTreeDragOver === 'function') {
                    btn.ondragover = (e) => window.handleTenantTreeDragOver(e, btn, parentPath);
                    btn.ondragleave = (e) => window.handleTenantTreeDragLeave(e, btn);
                    btn.ondrop = (e) => window.handleTenantTreeDrop(e, node.name, btn, parentPath);
                }

                btn.onclick = (e) => {
                    e.stopPropagation();
                    window.location.hash = currentPath;
                };
            } else if (node.type === 'house' && (!node.children || node.children.length === 0)) {
                btn.onclick = (e) => {
                    e.stopPropagation();
                    window.location.hash = currentPath;
                };
            }

            parentEl.appendChild(li);
        });
    }

    // ── Area Grid View ───────────────────────────────────────────────────────
    function selectAreaGrid(areaNode) {
        currentArea = areaNode.name;
        currentHouse = null;
        currentTenant = null;
        window.location.hash = `/grid/area/${encodeURIComponent(areaNode.name)}`;
        renderAreaGrid(areaNode);
    }

    function renderAreaGrid(areaNode) {
        document.querySelectorAll('.area-grid-btn').forEach(b => {
            if (b.dataset.areaName === areaNode.name) {
                b.classList.add('bg-slate-800', 'text-white', 'border-slate-700');
                b.classList.remove('text-slate-300');
            } else {
                b.classList.remove('bg-slate-800', 'text-white', 'border-slate-700');
                b.classList.add('text-slate-300');
            }
        });

        if (welcomePanel) welcomePanel.classList.add('hidden');
        if (docListPanel) {
            docListPanel.classList.add('hidden');
            docListPanel.classList.remove('flex');
        }
        if (docViewerPanel) docViewerPanel.classList.add('hidden');
        const resizer2 = document.getElementById('resizer-2');
        if (resizer2) resizer2.classList.add('hidden');
        if (backToGridBtn) backToGridBtn.classList.add('hidden');

        if (areaGridPanel) {
            areaGridPanel.classList.remove('hidden');
            areaGridPanel.classList.add('flex');
        }

        if (currentHouseTitle) currentHouseTitle.textContent = `${areaNode.name} — Houses Overview`;
        if (statsBadge) statsBadge.classList.add('hidden');

        if (gridAreaTitle) gridAreaTitle.textContent = areaNode.name;
        const houses = areaNode.children || [];
        if (gridAreaStats) gridAreaStats.textContent = `${houses.length} Houses`;

        if (!houseCardsContainer) return;
        houseCardsContainer.innerHTML = '';
        if (houses.length === 0) {
            houseCardsContainer.innerHTML = '<p class="text-slate-500 text-xs col-span-full py-8 text-center">No houses found in this area.</p>';
            return;
        }

        houses.forEach(house => {
            const card = document.createElement('div');
            card.className = 'house-card group bg-white rounded-xl p-4 border border-slate-200 shadow-2xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between';
            card.dataset.houseId = house.id;

            let borderClass = 'border-l-[5px] border-l-slate-300';
            let badgeClass = 'bg-slate-100 text-slate-700 border-slate-200';
            let badgeLabel = '⚪ Unknown';

            if (house.duration_category === 'short') {
                borderClass = 'border-l-[5px] border-l-emerald-500 hover:border-emerald-400';
                badgeClass = 'bg-emerald-50 text-emerald-800 border-emerald-300 font-semibold';
                badgeLabel = '🟢 < 5 Yrs';
            } else if (house.duration_category === 'medium') {
                borderClass = 'border-l-[5px] border-l-amber-500 hover:border-amber-400';
                badgeClass = 'bg-amber-50 text-amber-800 border-amber-300 font-semibold';
                badgeLabel = '🟡 5–10 Yrs';
            } else if (house.duration_category === 'long') {
                borderClass = 'border-l-[5px] border-l-rose-500 hover:border-rose-400';
                badgeClass = 'bg-rose-50 text-rose-800 border-rose-300 font-semibold';
                badgeLabel = '🔴 > 10 Yrs';
            }
            card.className += ` ${borderClass}`;

            const tenantName = house.current_tenant || (house.children && house.children.length > 0 ? house.children[0].name : 'No Active Tenant');
            const tenureSubtitle = house.subtitle || (house.children && house.children.length > 0 && house.children[0].subtitle ? house.children[0].subtitle : 'Tenure unrecorded');

            let categoryPillsHtml = '';
            if (house.category_counts && Object.keys(house.category_counts).length > 0) {
                const sortedCats = Object.entries(house.category_counts).sort((a, b) => b[1] - a[1]);
                categoryPillsHtml = sortedCats.map(([cat, count]) => `
                    <span class="inline-flex items-center text-[10px] bg-slate-50 text-slate-700 px-2 py-0.5 rounded border border-slate-200">
                        ${cat}: <b class="ml-1 text-slate-900">${count}</b>
                    </span>
                `).join('');
            } else {
                categoryPillsHtml = '<span class="text-[10px] text-slate-400">No documents</span>';
            }

            card.innerHTML = `
                <div>
                    <div class="flex items-start justify-between gap-2 mb-2">
                        <h3 class="font-bold text-slate-900 text-sm group-hover:text-blue-600 transition-colors line-clamp-1" title="${house.name}">
                            🏠 ${house.name}
                        </h3>
                        <span class="tenure-badge text-[10px] px-2 py-0.5 rounded border flex-shrink-0 ${badgeClass}">${badgeLabel}</span>
                    </div>
                    
                    <div class="space-y-1 text-xs text-slate-600 mt-2">
                        <div class="flex items-center gap-1.5">
                            <span class="text-slate-400 flex-shrink-0">👤</span>
                            <span class="tenant-name font-semibold text-slate-800 truncate" title="${tenantName}">${tenantName}</span>
                        </div>
                        <div class="flex items-center gap-1.5 text-[11px] text-slate-500">
                            <span class="text-slate-400 flex-shrink-0">📅</span>
                            <span class="tenure-text truncate" title="${tenureSubtitle}">${tenureSubtitle}</span>
                        </div>
                    </div>
                </div>

                <div class="mt-4 pt-3 border-t border-slate-100">
                    <div class="flex items-center justify-between text-xs mb-2">
                        <span class="text-slate-500 text-[11px]">Total Documents:</span>
                        <span class="doc-count font-bold text-slate-800 bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-[11px] border border-blue-100">${house.total_documents || 0} Docs</span>
                    </div>
                    <div class="flex flex-wrap gap-1 max-h-20 overflow-hidden">
                        ${categoryPillsHtml}
                    </div>
                </div>
            `;

            card.onclick = () => {
                openHouseFromGrid(areaNode.name, house.id);
            };

            houseCardsContainer.appendChild(card);
        });
    }

    function openHouseFromGrid(areaName, houseId) {
        currentArea = areaName;
        currentHouse = houseId;
        currentTenant = null;

        if (areaGridPanel) {
            areaGridPanel.classList.add('hidden');
            areaGridPanel.classList.remove('flex');
        }

        window.location.hash = `/area/${encodeURIComponent(areaName)}/house/${encodeURIComponent(houseId)}`;
    }

    // ── Mode Switching ───────────────────────────────────────────────────────
    function switchToViewMode(mode) {
        if (currentViewMode === mode) return;
        currentViewMode = mode;

        const activeBtnClass = "flex-1 py-1.5 px-1.5 text-xs font-semibold rounded-lg bg-slate-800 text-white shadow-xs border border-slate-700 flex items-center justify-center gap-1.5 transition-all";
        const inactiveBtnClass = "flex-1 py-1.5 px-1.5 text-xs font-semibold rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 flex items-center justify-center gap-1.5 transition-all";

        if (viewModeTreeBtn) viewModeTreeBtn.className = mode === 'tree' ? activeBtnClass : inactiveBtnClass;
        if (viewModeGridBtn) viewModeGridBtn.className = mode === 'grid' ? activeBtnClass : inactiveBtnClass;
        if (viewModeDbBtn) viewModeDbBtn.className = mode === 'db' ? activeBtnClass : inactiveBtnClass;

        if (currentViewMode === 'tree') {
            if (sidebarSectionTitle) sidebarSectionTitle.textContent = "Areas & Houses";

            if (areaGridPanel) {
                areaGridPanel.classList.add('hidden');
                areaGridPanel.classList.remove('flex');
            }
            if (databaseInspectorPanel) {
                databaseInspectorPanel.classList.add('hidden');
                databaseInspectorPanel.classList.remove('flex');
            }
            if (backToGridBtn) backToGridBtn.classList.add('hidden');

            renderSidebar();

            if (currentArea && currentHouse) {
                if (welcomePanel) welcomePanel.classList.add('hidden');
                if (docListPanel) {
                    docListPanel.classList.remove('hidden');
                    docListPanel.classList.add('flex');
                }
                const resizer2 = document.getElementById('resizer-2');
                if (resizer2) resizer2.classList.remove('hidden');
            } else {
                if (welcomePanel) welcomePanel.classList.remove('hidden');
                if (docListPanel) {
                    docListPanel.classList.add('hidden');
                    docListPanel.classList.remove('flex');
                }
                if (docViewerPanel) docViewerPanel.classList.add('hidden');
                if (currentHouseTitle) currentHouseTitle.textContent = 'Select an Area';
            }
        } else if (currentViewMode === 'grid') {
            if (sidebarSectionTitle) sidebarSectionTitle.textContent = "Areas";

            if (databaseInspectorPanel) {
                databaseInspectorPanel.classList.add('hidden');
                databaseInspectorPanel.classList.remove('flex');
            }

            renderSidebar();

            if (!isTreeLoading && globalTreeData && globalTreeData.length > 0) {
                if (currentArea) {
                    const areaNode = globalTreeData.find(a => a.name === currentArea);
                    if (areaNode) {
                        selectAreaGrid(areaNode);
                    } else {
                        selectAreaGrid(globalTreeData[0]);
                    }
                } else {
                    selectAreaGrid(globalTreeData[0]);
                }
            }
        } else if (currentViewMode === 'db') {
            if (sidebarSectionTitle) sidebarSectionTitle.textContent = "Database";

            if (welcomePanel) welcomePanel.classList.add('hidden');
            if (docListPanel) {
                docListPanel.classList.add('hidden');
                docListPanel.classList.remove('flex');
            }
            if (docViewerPanel) docViewerPanel.classList.add('hidden');
            const resizer2 = document.getElementById('resizer-2');
            if (resizer2) resizer2.classList.add('hidden');
            if (backToGridBtn) backToGridBtn.classList.add('hidden');
            if (areaGridPanel) {
                areaGridPanel.classList.add('hidden');
                areaGridPanel.classList.remove('flex');
            }

            if (databaseInspectorPanel) {
                databaseInspectorPanel.classList.remove('hidden');
                databaseInspectorPanel.classList.add('flex');
            }

            if (currentHouseTitle) currentHouseTitle.textContent = "Database Inspector";
            if (statsBadge) statsBadge.classList.add('hidden');
            window.location.hash = "/database";

            loadDbInspector();
        }
    }

    // ── Database Inspector ───────────────────────────────────────────────────
    async function loadDbInspector(tableName = null) {
        if (tableName) currentDbTable = tableName;
        try {
            const infoRes = await fetch('/api/db/info');
            if (!infoRes.ok) throw new Error('Failed to fetch DB info');
            const info = await infoRes.json();

            const statusBadge = document.getElementById('db-status-badge');
            const pathBadge = document.getElementById('db-path-badge');
            if (statusBadge) {
                if (info.connected) {
                    statusBadge.textContent = 'Connected';
                    statusBadge.className = 'bg-emerald-50 text-emerald-700 text-xs font-semibold px-3 py-1 rounded-full border border-emerald-200';
                    if (pathBadge) pathBadge.textContent = info.db_path || 'organizer.db';
                } else {
                    statusBadge.textContent = 'Disconnected';
                    statusBadge.className = 'bg-rose-50 text-rose-700 text-xs font-semibold px-3 py-1 rounded-full border border-rose-200';
                    if (pathBadge) pathBadge.textContent = 'No DB Found';
                }
            }

            const tabsContainer = document.getElementById('db-table-tabs');
            if (tabsContainer) {
                tabsContainer.innerHTML = '';
                const tables = ['areas', 'houses', 'tenants', 'batches', 'pages', 'documents'];
                tables.forEach(t => {
                    const count = info.tables && info.tables[t] !== undefined ? info.tables[t] : 0;
                    const btn = document.createElement('button');
                    const isActive = t === currentDbTable;
                    btn.className = `px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                        isActive
                            ? 'bg-blue-600 text-white shadow-xs'
                            : 'bg-white text-slate-700 hover:bg-slate-50 border border-slate-200'
                    }`;
                    btn.innerHTML = `<span>${t}</span><span class="px-1.5 py-0.2 text-[10px] rounded-full ${isActive ? 'bg-blue-700 text-blue-100' : 'bg-slate-100 text-slate-600 font-bold'}">${count}</span>`;
                    btn.onclick = () => {
                        currentDbTable = t;
                        dbTableOffset = 0;
                        loadDbInspector(t);
                    };
                    tabsContainer.appendChild(btn);
                });
            }

            await loadDbTableRows();
        } catch (err) {
            console.error('Failed to load DB info:', err);
        }
    }

    async function loadDbTableRows() {
        const thead = document.getElementById('db-table-head');
        const tbody = document.getElementById('db-table-body');
        const paginationInfo = document.getElementById('db-pagination-info');
        const prevBtn = document.getElementById('db-prev-page');
        const nextBtn = document.getElementById('db-next-page');

        if (!tbody) return;
        tbody.innerHTML = '<tr><td colspan="15" class="text-center py-8 text-slate-400">Loading records...</td></tr>';

        try {
            let url = `/api/db/tables/${currentDbTable}?limit=${dbTableLimit}&offset=${dbTableOffset}`;
            if (dbTableSearchTerm) {
                url += `&search=${encodeURIComponent(dbTableSearchTerm)}`;
            }
            const res = await fetch(url);
            if (!res.ok) throw new Error('Failed to fetch table rows');
            const data = await res.json();

            dbTableTotal = data.total;

            if (thead) {
                thead.innerHTML = '<tr>' + data.columns.map(c => `<th class="px-3 py-2 border-b border-slate-200 uppercase tracking-wider font-bold text-slate-600 text-[11px]">${c}</th>`).join('') + '</tr>';
            }

            if (data.rows.length === 0) {
                tbody.innerHTML = `<tr><td colspan="${data.columns.length || 1}" class="text-center py-8 text-slate-400">No records found in table '${currentDbTable}'.</td></tr>`;
            } else {
                tbody.innerHTML = data.rows.map((row, idx) => {
                    const bg = idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50';
                    const cells = data.columns.map(c => {
                        const val = row[c];
                        const display = val === null || val === undefined ? '<span class="text-slate-300 italic">null</span>' : String(val);
                        return `<td class="px-3 py-1.5 border-b border-slate-100 max-w-xs truncate font-mono text-[11px]" title="${display.replace(/"/g, '&quot;')}">${display}</td>`;
                    }).join('');
                    return `<tr class="${bg} hover:bg-blue-50/60 transition-colors">${cells}</tr>`;
                }).join('');
            }

            const start = dbTableTotal === 0 ? 0 : dbTableOffset + 1;
            const end = Math.min(dbTableOffset + data.rows.length, dbTableTotal);
            if (paginationInfo) paginationInfo.textContent = `Showing ${start}–${end} of ${dbTableTotal} records`;
            if (prevBtn) prevBtn.disabled = dbTableOffset === 0;
            if (nextBtn) nextBtn.disabled = (dbTableOffset + dbTableLimit) >= dbTableTotal;

        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="15" class="text-center py-8 text-rose-500">Failed to load data: ${err.message}</td></tr>`;
        }
    }

    // ── Hash Router ──────────────────────────────────────────────────────────
    function handleHashChange() {
        const hash = decodeURIComponent(window.location.hash.replace('#', ''));
        if (!hash) return;

        if (hash === '/database' || hash === '/db') {
            if (currentViewMode !== 'db') {
                switchToViewMode('db');
            }
            return;
        }

        if (hash.startsWith('/grid/area/')) {
            const areaName = decodeURIComponent(hash.replace('/grid/area/', ''));
            if (currentViewMode !== 'grid') {
                currentViewMode = 'grid';
                const activeBtnClass = "flex-1 py-1.5 px-1.5 text-xs font-semibold rounded-lg bg-slate-800 text-white shadow-xs border border-slate-700 flex items-center justify-center gap-1.5 transition-all";
                const inactiveBtnClass = "flex-1 py-1.5 px-1.5 text-xs font-semibold rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 flex items-center justify-center gap-1.5 transition-all";
                if (viewModeGridBtn) viewModeGridBtn.className = activeBtnClass;
                if (viewModeTreeBtn) viewModeTreeBtn.className = inactiveBtnClass;
                if (viewModeDbBtn) viewModeDbBtn.className = inactiveBtnClass;
                if (sidebarSectionTitle) sidebarSectionTitle.textContent = "Areas";
                renderSidebar();
            }
            const areaNode = globalTreeData.find(a => a.name === areaName);
            if (areaNode) {
                renderAreaGrid(areaNode);
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

        let tenantName = null;
        if (tenantId && houseId && tenantId.startsWith(houseId + '_')) {
            tenantName = tenantId.substring(houseId.length + 1);
        }

        if (tenantName && currentTab !== 'categories' && tabCategories && tabTimeline) {
            currentTab = 'categories';
            tabCategories.className = "flex-1 py-1.5 px-3 text-xs font-semibold rounded-md bg-white text-blue-600 shadow-xs flex items-center justify-center gap-1.5 transition-all";
            tabTimeline.className = "flex-1 py-1.5 px-3 text-xs font-medium rounded-md text-slate-600 hover:text-slate-900 flex items-center justify-center gap-1.5 transition-all";
        }

        if (areaId && houseId) {
            selectHouse(areaId, houseId, tenantName);
        }

        document.querySelectorAll('.tree-item').forEach(el => {
            el.classList.remove('tree-item-active', 'bg-blue-600', 'text-white', 'font-semibold');
            el.classList.add('text-slate-300');
        });

        const targetLi = document.querySelector(`li[data-path="${hash}"]`);
        if (targetLi) {
            const btn = targetLi.querySelector('.tree-item');
            if (btn) {
                btn.classList.add('tree-item-active', 'bg-blue-600', 'text-white', 'font-semibold');
                btn.classList.remove('text-slate-300');
            }

            let current = targetLi.parentElement;
            while (current && current.id !== 'house-list') {
                if (current.tagName === 'UL') {
                    current.classList.remove('hidden');
                    const parentLi = current.parentElement;
                    if (parentLi && parentLi.tagName === 'LI') {
                        const icon = parentLi.querySelector('.tree-item span.tree-chevron') || parentLi.querySelector('.tree-item span');
                        if (icon) icon.innerHTML = '▼';
                    }
                }
                current = current.parentElement;
            }
            targetLi.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    window.addEventListener('hashchange', handleHashChange);

    // ── House Selection & Details ────────────────────────────────────────────
    async function selectHouse(areaId, houseId, tenantName) {
        currentArea = areaId;
        currentHouse = houseId;
        currentTenant = tenantName;

        if (currentHouseTitle) {
            if (tenantName) {
                currentHouseTitle.innerHTML = `
                    <div class="flex items-center gap-2 flex-wrap">
                        <span>${houseId} - ${tenantName}</span>
                        <button id="btn-back-to-house-register" type="button" class="text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 border border-blue-200 px-2 py-0.5 rounded-md transition-all cursor-pointer inline-flex items-center gap-1 shadow-2xs" title="العودة لسجل المستأجرين">
                            <span>← سجل المنزل</span>
                        </button>
                    </div>
                `;
                const backBtn = document.getElementById('btn-back-to-house-register');
                if (backBtn) {
                    backBtn.onclick = (e) => {
                        e.preventDefault();
                        window.location.hash = `#/area/${encodeURIComponent(areaId)}/house/${encodeURIComponent(houseId)}`;
                    };
                }
            } else {
                currentHouseTitle.textContent = `${houseId}`;
            }
        }

        if (tabCategoriesLabel) {
            tabCategoriesLabel.textContent = tenantName ? '📁 Folders' : '📋 سجل المستأجرين';
        }
        if (tabTimelineLabel) {
            tabTimelineLabel.textContent = tenantName ? 'Timeline' : 'Timeline';
        }

        if (areaGridPanel) {
            areaGridPanel.classList.add('hidden');
            areaGridPanel.classList.remove('flex');
        }

        if (backToGridBtn) {
            if (currentViewMode === 'grid') {
                backToGridBtn.classList.remove('hidden');
                backToGridBtn.classList.add('flex');
                backToGridBtn.innerHTML = `
                    <svg class="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
                    <span>← Back to ${areaId} Grid</span>
                `;
            } else {
                backToGridBtn.classList.add('hidden');
            }
        }

        if (welcomePanel) welcomePanel.classList.add('hidden');
        if (docListPanel) {
            docListPanel.classList.remove('hidden');
            docListPanel.classList.add('flex');
        }
        const resizer2 = document.getElementById('resizer-2');
        if (resizer2) resizer2.classList.remove('hidden');
        if (docViewerPanel) docViewerPanel.classList.add('hidden');

        await refreshCurrentTab(areaId, houseId);
    }

    async function refreshCurrentTab(areaId, houseId) {
        if (currentTab === 'timeline') {
            await loadTimeline(areaId, houseId);
        } else {
            if (!currentTenant) {
                await loadHouseProfile(areaId, houseId);
            } else {
                await loadCategories(areaId, houseId);
            }
        }
    }

    // ── House Profile & Tenancy Register Loading & Rendering ──────────────────
    let currentHouseProfile = null;

    async function loadHouseProfile(areaId, houseId) {
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

    // ── Timeline Loading & Rendering ─────────────────────────────────────────
    async function loadTimeline(areaId, houseId) {
        if (!docListEl) return;
        docListEl.innerHTML = '<p class="text-xs text-slate-500 p-3">Loading documents...</p>';
        try {
            if (isStaticMode) {
                const stateData = await fetchHouseState(areaId, houseId);
                const groups = getDocumentGroups(stateData);
                currentTimeline = groups.map(g => ({
                    vault_id: g.vault_id || '',
                    primary_tenant: g.primary_tenant || '',
                    dates: g.dates || [],
                    brief_arabic_title: g.brief_arabic_title || ''
                }));
                currentTimeline.sort((a, b) => {
                    const dateA = (a.dates && a.dates[0] && a.dates[0] !== 'NONE') ? a.dates[0] : '0000-00-00';
                    const dateB = (b.dates && b.dates[0] && b.dates[0] !== 'NONE') ? b.dates[0] : '0000-00-00';
                    return dateB.localeCompare(dateA);
                });
            } else {
                const res = await fetch(`/api/areas/${encodeURIComponent(areaId)}/houses/${encodeURIComponent(houseId)}/timeline`);
                if (!res.ok) throw new Error('Failed to load timeline');
                currentTimeline = await res.json();
            }
            
            const displayTimeline = currentTenant 
                ? currentTimeline.filter(doc => doc.primary_tenant === currentTenant)
                : currentTimeline;

            if (statsBadge) {
                statsBadge.textContent = `${displayTimeline.length} Documents`;
                statsBadge.classList.remove('hidden');
            }
            
            renderTimeline();
        } catch (err) {
            console.error(err);
            docListEl.innerHTML = '<p class="text-xs text-rose-500 p-3">Error loading timeline.</p>';
        }
    }

    function renderTimeline() {
        if (!docListEl) return;
        docListEl.innerHTML = '';
        
        let displayTimeline = currentTimeline;
        if (currentTenant) {
            displayTimeline = currentTimeline.filter(doc => doc.primary_tenant === currentTenant);
        }
        
        if (displayTimeline.length === 0) {
            docListEl.innerHTML = '<p class="text-xs text-slate-400 p-3 text-center">No documents found for this selection.</p>';
            return;
        }
        
        displayTimeline.forEach(doc => {
            const card = document.createElement('div');
            card.className = 'p-3 bg-white rounded-xl rounded-md border border-slate-200 shadow-2xs hover:shadow-sm hover:border-blue-400 cursor-pointer transition-all flex flex-col gap-2 group relative';
            card.draggable = true;
            card.setAttribute('data-vault-id', doc.vault_id);
            if (typeof window.handleDocDragStart === 'function') {
                card.ondragstart = (e) => window.handleDocDragStart(e, doc, doc.category);
                card.ondragend = (e) => window.handleDocDragEnd(e);
            }
            
            const title = doc.brief_arabic_title || 'Untitled Document';
            const date = (doc.dates && doc.dates.length > 0) ? doc.dates[0] : 'Unknown Date';
            const isManual = Boolean(doc.is_manual);
            const lockBadgeHtml = isManual 
                ? `<span title="Manually assigned - protected from auto-reallocation" class="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded flex items-center gap-1 font-semibold flex-shrink-0">🔒 Pinned</span>`
                : '';
            
            card.innerHTML = `
                <div class="flex justify-between items-start gap-2">
                    <h4 class="text-xs font-semibold text-slate-800 group-hover:text-blue-600 transition-colors line-clamp-2 leading-snug">${title}</h4>
                    <div class="flex items-center gap-1 flex-shrink-0">
                        ${lockBadgeHtml}
                        <button class="doc-menu-btn opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-700 transition-opacity" data-vault-id="${doc.vault_id}" title="Manage Document (Rename, Move, Copy)">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"/></svg>
                        </button>
                    </div>
                </div>
                <div class="flex items-center justify-between text-[11px] text-slate-500 pt-1.5 border-t border-slate-100">
                    <span class="flex items-center gap-1 font-mono text-[10px] text-slate-400">
                        <svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
                        <span>${date}</span>
                    </span>
                    <span class="bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md font-medium text-[10px] border border-slate-200 truncate max-w-[140px]">${doc.primary_tenant || 'No Tenant'}</span>
                </div>
            `;
            
            const menuBtn = card.querySelector('.doc-menu-btn');
            if (menuBtn) {
                menuBtn.onclick = (e) => {
                    e.stopPropagation();
                    if (typeof window.openDocModal === 'function') {
                        window.openDocModal(doc, doc.category);
                    }
                };
            }

            card.onclick = () => openDocument(doc.vault_id, title);
            attachPreview(card, doc.vault_id, title);
            docListEl.appendChild(card);
        });
    }

    // ── Categories Loading & Rendering ───────────────────────────────────────
    async function loadCategories(areaId, houseId) {
        if (!docListEl) return;
        docListEl.innerHTML = '<p class="text-xs text-slate-500 p-3">Loading categories...</p>';
        try {
            if (isStaticMode) {
                const stateData = await fetchHouseState(areaId, houseId);
                const groups = getDocumentGroups(stateData);
                const catMap = {};
                
                groups.forEach(g => {
                    const tenant = g.primary_tenant;
                    const catRaw = g.folder_path || g.category;
                    if (tenant && catRaw) {
                        const prefix = FOLDER_PREFIXES[catRaw] || '';
                        const catNumbered = prefix ? `${prefix} - ${catRaw}` : catRaw;
                        const key = `${tenant}:::${catNumbered}`;
                        if (!catMap[key]) {
                            catMap[key] = {
                                tenant: tenant,
                                name: catNumbered,
                                documents: []
                            };
                        }
                        catMap[key].documents.push({
                            vault_id: g.vault_id || '',
                            filename: g.filename || '',
                            start_page: g.start_page || 1,
                            end_page: g.end_page || 1,
                            date: (g.dates && g.dates[0]) ? g.dates[0] : '',
                            tenant: tenant,
                            brief_arabic_title: g.brief_arabic_title || '',
                            is_manual: g.is_manual || 0,
                            category: catNumbered
                        });
                    }
                });
                
                currentCategories = Object.values(catMap).map(c => ({
                    tenant: c.tenant,
                    name: c.name,
                    document_count: c.documents.length,
                    documents: c.documents
                }));
            } else {
                const res = await fetch(`/api/areas/${encodeURIComponent(areaId)}/houses/${encodeURIComponent(houseId)}/categories`);
                if (!res.ok) throw new Error('Failed to load categories');
                currentCategories = await res.json();
            }
            
            const totalDocs = currentCategories.reduce((sum, cat) => sum + cat.document_count, 0);
            if (statsBadge) {
                statsBadge.textContent = `${currentCategories.length} Categories (${totalDocs} Docs)`;
                statsBadge.classList.remove('hidden');
            }
            
            renderCategories();
        } catch (err) {
            console.error(err);
            docListEl.innerHTML = '<p class="text-xs text-rose-500 p-3">Error loading categories.</p>';
        }
    }

    function renderCategories() {
        if (!docListEl) return;
        docListEl.innerHTML = '';
        
        let displayCategories = [];
        
        if (currentTenant) {
            displayCategories = currentCategories.filter(cat => cat.tenant === currentTenant);
        } else {
            const agg = {};
            currentCategories.forEach(cat => {
                if (!agg[cat.name]) {
                    agg[cat.name] = { count: 0, documents: [] };
                }
                agg[cat.name].count += cat.document_count;
                if (cat.documents) {
                    agg[cat.name].documents = agg[cat.name].documents.concat(cat.documents);
                }
            });
            for (const [name, data] of Object.entries(agg)) {
                displayCategories.push({ name: name, document_count: data.count, documents: data.documents });
            }
        }
        
        displayCategories.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
        
        if (displayCategories.length === 0) {
            docListEl.innerHTML = '<p class="text-xs text-slate-400 p-3 text-center">No folders found for this selection.</p>';
            return;
        }
        
        displayCategories.forEach(cat => {
            const card = document.createElement('div');
            card.className = 'p-3 bg-white rounded-xl border border-slate-200 shadow-2xs hover:border-slate-300 transition-all mb-2 cursor-pointer category-folder-card';
            card.setAttribute('data-category-name', cat.name);
            
            if (typeof window.handleCategoryDragOver === 'function') {
                card.ondragover = (e) => window.handleCategoryDragOver(e, card);
                card.ondragleave = (e) => window.handleCategoryDragLeave(e, card);
                card.ondrop = (e) => window.handleCategoryDrop(e, cat.name, card);
            }

            card.innerHTML = `
                <div class="flex justify-between items-center">
                    <div class="flex items-center gap-2 min-w-0">
                        <div class="w-6 h-6 rounded-lg bg-blue-50 text-blue-600 border border-blue-100 flex items-center justify-center flex-shrink-0">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                        </div>
                        <h4 class="text-xs font-semibold text-slate-800 truncate">${cat.name}</h4>
                    </div>
                    <span class="bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full text-[10px] font-bold border border-slate-200 flex-shrink-0">${cat.document_count} Documents</span>
                </div>
                <div class="category-docs hidden mt-2.5 pt-2.5 border-t border-slate-100 space-y-1">
                </div>
            `;
            
            if (cat.documents && cat.documents.length > 0) {
                const docsContainer = card.querySelector('.category-docs');
                cat.documents.forEach(doc => {
                    const docEl = document.createElement('div');
                    docEl.className = 'text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-2.5 py-1.5 rounded-lg cursor-pointer transition-colors flex items-center justify-between gap-2 font-medium group/doc';
                    docEl.draggable = true;
                    docEl.setAttribute('data-vault-id', doc.vault_id);
                    if (typeof window.handleDocDragStart === 'function') {
                        docEl.ondragstart = (e) => window.handleDocDragStart(e, doc, cat.name);
                        docEl.ondragend = (e) => window.handleDocDragEnd(e);
                    }

                    const title = doc.brief_arabic_title || doc.filename || 'Document';
                    const isManual = Boolean(doc.is_manual);
                    const lockIcon = isManual ? '<span title="Manually assigned - protected from auto-reallocation" class="text-[10px] text-amber-600 flex-shrink-0">🔒</span>' : '';

                    docEl.innerHTML = `
                        <div class="flex items-center gap-2 min-w-0 flex-1">
                            <svg class="w-3.5 h-3.5 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                            <span class="truncate">${title}</span>
                            ${lockIcon}
                        </div>
                        <button class="doc-menu-btn opacity-0 group-hover/doc:opacity-100 p-1 hover:bg-blue-100 rounded text-slate-400 hover:text-slate-700 transition-opacity flex-shrink-0" data-vault-id="${doc.vault_id}" title="Manage Document (Rename, Move, Copy)">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"/></svg>
                        </button>
                    `;

                    const menuBtn = docEl.querySelector('.doc-menu-btn');
                    if (menuBtn) {
                        menuBtn.onclick = (e) => {
                            e.stopPropagation();
                            if (typeof window.openDocModal === 'function') {
                                window.openDocModal(doc, cat.name);
                            }
                        };
                    }

                    docEl.onclick = (e) => {
                        e.stopPropagation();
                        openDocument(doc.vault_id, title);
                    };
                    attachPreview(docEl, doc.vault_id, title);
                    docsContainer.appendChild(docEl);
                });
            }
            
            card.onclick = () => {
                const docsContainer = card.querySelector('.category-docs');
                if (docsContainer) {
                    docsContainer.classList.toggle('hidden');
                }
            };
            docListEl.appendChild(card);
        });
    }

    // ── Document Viewer ──────────────────────────────────────────────────────
    function openDocument(vaultId, title) {
        if (!docViewerPanel) return;
        docViewerPanel.classList.remove('hidden');
        docViewerPanel.classList.add('flex');
        
        if (viewerTitle) viewerTitle.textContent = title;
        const pdfUrl = getPdfUrl(currentArea, currentHouse, vaultId);
        if (pdfFrame) pdfFrame.src = pdfUrl + '#view=FitH';
        if (viewerDownload) viewerDownload.href = pdfUrl;
        if (typeof window.updateViewerTenantSelect === 'function') {
            window.updateViewerTenantSelect(vaultId);
        }
    }

    function closeDocument() {
        if (!docViewerPanel) return;
        docViewerPanel.classList.add('hidden');
        docViewerPanel.classList.remove('flex');
        if (pdfFrame) pdfFrame.src = 'about:blank';
    }

    // ── Resizer ──────────────────────────────────────────────────────────────
    function setupResizer(resizerId, panelId, isPercentage = false) {
        const resizer = document.getElementById(resizerId);
        const panel = document.getElementById(panelId);
        if (!resizer || !panel) return;
        let isResizing = false;
        let startX;
        let startWidth;

        resizer.addEventListener('mousedown', (e) => {
            isResizing = true;
            startX = e.clientX;
            startWidth = panel.getBoundingClientRect().width;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            const deltaX = e.clientX - startX;
            let newWidth = startWidth + deltaX;
            
            if (isPercentage) {
                const parentWidth = panel.parentElement.getBoundingClientRect().width;
                let percentage = (newWidth / parentWidth) * 100;
                percentage = Math.max(20, Math.min(percentage, 60));
                panel.style.width = `${percentage}%`;
            } else {
                newWidth = Math.max(200, Math.min(newWidth, window.innerWidth * 0.5));
                panel.style.width = `${newWidth}px`;
            }
        });

        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                document.body.style.cursor = 'default';
                document.body.style.userSelect = '';
            }
        });
    }

    // Expose globals needed across modules
    window.refreshCurrentTab = refreshCurrentTab;
    window.openDocument = openDocument;
    window.closeDocument = closeDocument;
    window.loadCategories = loadCategories;
    window.loadTimeline = loadTimeline;
    window.loadTree = loadTree;
    window.renderSidebar = renderSidebar;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initApp);
    } else {
        initApp();
    }
})();
