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
            let badgeLabel = 'Unknown';

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
                            const cardBg = isCurrent 
                                ? 'bg-emerald-50/70 border-emerald-200/80' 
                                : 'bg-slate-50 border-slate-200/60';
                            const nameClass = isCurrent ? 'font-bold text-slate-900' : 'font-medium text-slate-700';
                            const tenantIcon = isCurrent
                                ? `<span class="w-5 h-5 rounded-md bg-emerald-100 text-emerald-700 flex items-center justify-center flex-shrink-0" title="Residing Tenant">
                                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
                                   </span>`
                                : `<span class="w-5 h-5 rounded-md bg-slate-200/80 text-slate-500 flex items-center justify-center flex-shrink-0" title="Past Tenant">
                                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                                   </span>`;
                            
                            return `
                                <div class="tenant-overview-item flex items-center justify-between text-xs p-1.5 rounded-lg border ${cardBg}">
                                    <div class="flex items-center gap-2 min-w-0">
                                        ${tenantIcon}
                                        <span class="tenant-name ${nameClass} truncate text-xs" title="${t.name}">${t.name}</span>
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
                    <div class="flex items-center justify-between gap-2 pb-2.5 mb-2.5 border-b border-slate-100">
                        <div class="flex items-center gap-2 min-w-0">
                            <h3 class="font-bold text-slate-900 text-sm group-hover:text-blue-600 transition-colors truncate" title="${house.name}">
                                🏠 ${house.name}
                            </h3>
                            <span class="tenants-count text-[10px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200 flex-shrink-0">
                                ${tenants.length} ${tenants.length === 1 ? 'Tenant' : 'Tenants'}
                            </span>
                        </div>
                        <span class="tenure-badge text-[10px] px-2 py-0.5 rounded border flex-shrink-0 ${badgeClass}">${badgeLabel}</span>
                    </div>

                    <div class="tenants-overview-section">
                        ${tenantsHtml}
                    </div>
                </div>

                <div class="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span class="text-slate-400 text-[11px] font-medium flex items-center gap-1">
                        <span>Total Archive</span>
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
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initAddHouseModal);
        } else {
            initAddHouseModal();
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
        };
    }
})();
