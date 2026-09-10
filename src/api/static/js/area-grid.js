// ── Area Houses Grid Component ────────────────────────────────────────────
(function() {
    function selectAreaGrid(areaNode) {
        currentArea = areaNode.name;
        currentHouse = null;
        currentTenant = null;
        window.currentArea = areaNode.name;
        window.currentHouse = null;
        window.currentTenant = null;
        window.location.hash = `#/area/${encodeURIComponent(areaNode.name)}`;
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

        const welcomePanel = document.getElementById('welcome-panel');
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
        const houseCardsContainer = document.getElementById('area-grid-container') || document.getElementById('house-cards-container');

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

            const tenants = (house.children || []).filter(c => c.type === 'tenant');
            const totalDocs = house.total_documents || 0;

            let tenantsHtml = '';
            if (tenants.length === 0) {
                tenantsHtml = `
                    <div class="py-2.5 px-3 bg-slate-50 rounded-lg border border-slate-100 text-center">
                        <p class="text-[11px] text-slate-400 italic">No tenants recorded</p>
                    </div>
                `;
            } else {
                tenantsHtml = `
                    <div class="space-y-1.5">
                        ${tenants.map((t, idx) => {
                            const isCurrent = (house.current_tenant && t.name === house.current_tenant) 
                                || (t.subtitle && (t.subtitle.includes('Present') || t.subtitle.includes('الآن')))
                                || (idx === 0 && !t.subtitle?.includes('-'));
                            const dotColor = isCurrent ? '🟢' : '⚪';
                            const cardBg = isCurrent ? 'bg-emerald-50/70 border-emerald-200/80' : 'bg-slate-50 border-slate-200/60';
                            const nameClass = isCurrent ? 'font-bold text-slate-900' : 'font-medium text-slate-700';
                            const statusBadge = isCurrent 
                                ? '<span class="text-[9px] bg-emerald-100 text-emerald-800 font-bold px-1.5 py-0.2 rounded border border-emerald-300">Current</span>' 
                                : '<span class="text-[9px] bg-slate-100 text-slate-500 font-medium px-1.5 py-0.2 rounded border border-slate-200">Past</span>';
                            
                            return `
                                <div class="tenant-overview-item flex items-center justify-between text-xs p-1.5 rounded-lg border ${cardBg}">
                                    <div class="flex items-center gap-1.5 min-w-0">
                                        <span class="text-xs flex-shrink-0">${dotColor}</span>
                                        <span class="tenant-name ${nameClass} truncate text-xs" title="${t.name}">${t.name}</span>
                                        ${statusBadge}
                                    </div>
                                    <span class="tenure-text text-[10px] font-mono text-slate-500 ml-2 flex-shrink-0" title="${t.subtitle || ''}">
                                        ${t.subtitle || ''}
                                    </span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
            }

            card.innerHTML = `
                <div>
                    <div class="flex items-start justify-between gap-2 mb-3">
                        <h3 class="font-bold text-slate-900 text-sm group-hover:text-blue-600 transition-colors line-clamp-1" title="${house.name}">
                            🏠 ${house.name}
                        </h3>
                        <span class="tenure-badge text-[10px] px-2 py-0.5 rounded border flex-shrink-0 ${badgeClass}">${badgeLabel}</span>
                    </div>

                    <div class="tenants-overview-section">
                        <div class="flex items-center justify-between text-[11px] mb-2">
                            <span class="font-bold text-slate-400 uppercase tracking-wider text-[10px] flex items-center gap-1">
                                <span>👥</span>
                                <span>Tenants Overview</span>
                            </span>
                            <span class="tenants-count text-[10px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">
                                ${tenants.length} ${tenants.length === 1 ? 'Tenant' : 'Tenants'}
                            </span>
                        </div>
                        ${tenantsHtml}
                    </div>
                </div>

                <div class="mt-4 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span class="text-slate-400 text-[11px] font-medium flex items-center gap-1">
                        <span>📄 Total Archive</span>
                    </span>
                    <span class="doc-count font-bold text-slate-700 bg-blue-50/80 text-blue-700 px-2 py-0.5 rounded-md text-[11px] border border-blue-100">
                        ${totalDocs} Docs
                    </span>
                </div>
            `;

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

        window.location.hash = `#/area/${encodeURIComponent(areaName)}/house/${encodeURIComponent(houseId)}`;
    }

    window.selectAreaGrid = selectAreaGrid;
    window.renderAreaGrid = renderAreaGrid;
    window.openHouseFromGrid = openHouseFromGrid;
})();
