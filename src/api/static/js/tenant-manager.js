// ── Tenant Management Modal Controller ────────────────────────────────────
(function() {
    let tenantModal = null;
    let tenantModalTitle = null;
    let tenantModalRows = null;
    let tenantModalClose = null;
    let tenantModalCancel = null;
    let tenantModalSave = null;
    let btnAddTenantRow = null;
    let tenantModalStatus = null;
    let btnManageTenants = null;
    let viewerTenantSelect = null;
    let viewerTenantLabel = null;
    let currentViewingVaultId = null;

    function initTenantManager() {
        tenantModal = document.getElementById('tenant-modal');
        tenantModalTitle = document.getElementById('tenant-modal-title');
        tenantModalRows = document.getElementById('tenant-modal-rows');
        tenantModalClose = document.getElementById('tenant-modal-close');
        tenantModalCancel = document.getElementById('tenant-modal-cancel');
        tenantModalSave = document.getElementById('tenant-modal-save');
        btnAddTenantRow = document.getElementById('btn-add-tenant-row');
        tenantModalStatus = document.getElementById('tenant-modal-status');
        btnManageTenants = document.getElementById('btn-manage-tenants');
        viewerTenantSelect = document.getElementById('viewer-tenant-select');
        viewerTenantLabel = document.getElementById('viewer-tenant-label');

        if (btnManageTenants) btnManageTenants.addEventListener('click', openTenantModal);
        if (tenantModalClose) tenantModalClose.addEventListener('click', closeTenantModal);
        if (tenantModalCancel) tenantModalCancel.addEventListener('click', closeTenantModal);
        if (tenantModalSave) tenantModalSave.addEventListener('click', saveTenantsAndReallocate);
        if (btnAddTenantRow) btnAddTenantRow.addEventListener('click', () => addTenantRow());

        if (viewerTenantSelect) {
            viewerTenantSelect.addEventListener('change', async (e) => {
                const newTenantId = parseInt(e.target.value);
                if (!currentViewingVaultId || !newTenantId) return;

                try {
                    const res = await fetch(`/api/areas/${encodeURIComponent(currentArea)}/houses/${encodeURIComponent(currentHouse)}/documents/${encodeURIComponent(currentViewingVaultId)}/tenant`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ tenant_id: newTenantId })
                    });
                    if (res.ok) {
                        if (typeof window.refreshCurrentTab === 'function') {
                            window.refreshCurrentTab(currentArea, currentHouse);
                        }
                    }
                } catch (err) {
                    console.error('Failed to update document tenant:', err);
                }
            });
        }
    }

    function openTenantModal() {
        if (!currentHouse || !currentArea) {
            alert('Please select a house first.');
            return;
        }
        if (!tenantModal) return;
        tenantModalTitle.textContent = `Manage Tenants: ${currentHouse} (${currentArea})`;
        tenantModalRows.innerHTML = '<p class="text-sm text-gray-500">Loading tenants...</p>';
        tenantModalStatus.classList.add('hidden');
        tenantModal.classList.remove('hidden');
        loadTenantsForModal();
    }

    function closeTenantModal() {
        if (!tenantModal) return;
        tenantModal.classList.add('hidden');
        tenantModalStatus.classList.add('hidden');
    }

    async function loadTenantsForModal() {
        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(currentArea)}/houses/${encodeURIComponent(currentHouse)}/tenants`);
            if (!res.ok) throw new Error('Failed to load tenants');
            const tenants = await res.json();
            tenantModalRows.innerHTML = '';
            if (!tenants || tenants.length === 0) {
                addTenantRow();
            } else {
                tenants.forEach(t => addTenantRow(t));
            }
        } catch (err) {
            console.error(err);
            tenantModalRows.innerHTML = '<p class="text-sm text-red-500">Error loading tenants.</p>';
        }
    }

    function addTenantRow(t = null) {
        const row = document.createElement('div');
        row.className = 'tenant-row flex flex-col sm:flex-row items-start sm:items-center gap-2.5 p-3.5 bg-slate-50/80 rounded-xl border border-slate-200 transition-all shadow-2xs';
        if (t && t.id) row.dataset.id = t.id;

        const nameVal = t ? (t.name || '') : '';
        const startVal = t ? (t.start_date || '') : '';
        const endVal = t ? (t.end_date || '') : '';
        const isPresent = !endVal || endVal === 'present' || String(endVal).toLowerCase() === 'none';

        row.innerHTML = `
            <div class="flex-1 w-full sm:w-auto">
                <label class="block text-[10px] text-slate-500 font-bold tracking-wider uppercase mb-1">NAME / الاسم</label>
                <input type="text" value="${nameVal.replace(/"/g, '&quot;')}" placeholder="Tenant Name" 
                       class="tenant-name-input w-full px-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-white font-medium shadow-2xs" required />
            </div>
            <div class="w-full sm:w-36">
                <label class="block text-[10px] text-slate-500 font-bold tracking-wider uppercase mb-1">START DATE</label>
                <input type="date" value="${startVal}" 
                       class="tenant-start-input w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-white font-medium shadow-2xs" required />
            </div>
            <div class="w-full sm:w-36">
                <label class="block text-[10px] text-slate-500 font-bold tracking-wider uppercase mb-1">END DATE</label>
                <input type="date" value="${isPresent ? '' : endVal}" ${isPresent ? 'disabled' : ''}
                       class="tenant-end-input w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-medium shadow-2xs ${isPresent ? 'bg-slate-100 text-slate-400' : 'bg-white'}" />
            </div>
            <div class="flex items-center gap-2 pt-2 sm:pt-5">
                <label class="flex items-center gap-1.5 text-xs text-slate-600 select-none cursor-pointer font-medium">
                    <input type="checkbox" class="tenant-present-check rounded border-slate-300 text-blue-600 focus:ring-blue-500" ${isPresent ? 'checked' : ''} />
                    <span>Present</span>
                </label>
                <button type="button" class="btn-remove-row text-slate-400 hover:text-rose-600 p-1 rounded-lg hover:bg-slate-200/60 transition-colors" title="Delete Tenant">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>
            </div>
        `;

        const presentCheck = row.querySelector('.tenant-present-check');
        const endInput = row.querySelector('.tenant-end-input');
        presentCheck.addEventListener('change', (e) => {
            if (e.target.checked) {
                endInput.value = '';
                endInput.disabled = true;
                endInput.className = "tenant-end-input w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-100 text-slate-400 font-medium shadow-2xs";
            } else {
                endInput.disabled = false;
                endInput.className = "tenant-end-input w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-white font-medium shadow-2xs";
            }
        });

        row.querySelector('.btn-remove-row').addEventListener('click', () => {
            row.remove();
            if (tenantModalRows.children.length === 0) {
                addTenantRow();
            }
        });

        tenantModalRows.appendChild(row);
    }

    async function saveTenantsAndReallocate() {
        const rows = Array.from(tenantModalRows.querySelectorAll('.tenant-row'));
        const tenantsPayload = [];

        for (const r of rows) {
            const name = r.querySelector('.tenant-name-input').value.trim();
            const start = r.querySelector('.tenant-start-input').value;
            const isPresent = r.querySelector('.tenant-present-check').checked;
            const end = isPresent ? null : (r.querySelector('.tenant-end-input').value || null);

            if (!name) {
                showTenantStatus('All tenants must have a name.', true);
                return;
            }
            if (!start) {
                showTenantStatus(`Please provide a start date for ${name}.`, true);
                return;
            }

            tenantsPayload.push({
                id: r.dataset.id ? parseInt(r.dataset.id) : null,
                name: name,
                start_date: start,
                end_date: end,
                house_id: currentHouse
            });
        }

        const saveBtnText = document.getElementById('tenant-save-btn-text');
        saveBtnText.textContent = 'Saving...';
        tenantModalSave.disabled = true;

        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(currentArea)}/houses/${encodeURIComponent(currentHouse)}/tenants`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tenants: tenantsPayload,
                    reallocate: true
                })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Failed to save tenants.');
            }

            const data = await res.json();
            showTenantStatus(`✓ Saved! ${data.reallocated_count} documents reallocated across ${data.tenants_count} tenants.`, false);

            setTimeout(() => {
                closeTenantModal();
                if (typeof window.refreshCurrentTab === 'function') window.refreshCurrentTab(currentArea, currentHouse);
                if (typeof window.loadTree === 'function') window.loadTree();
            }, 1000);
        } catch (err) {
            showTenantStatus(`Error: ${err.message}`, true);
        } finally {
            saveBtnText.textContent = '💾 Save Changes';
            tenantModalSave.disabled = false;
        }
    }

    function showTenantStatus(msg, isError = false) {
        tenantModalStatus.textContent = msg;
        tenantModalStatus.className = isError 
            ? "px-6 py-1 text-xs font-semibold text-red-600 block" 
            : "px-6 py-1 text-xs font-semibold text-emerald-600 block";
    }

    async function updateViewerTenantSelect(vaultId) {
        currentViewingVaultId = vaultId;
        if (!viewerTenantSelect || isStaticMode || !currentArea || !currentHouse) {
            if (viewerTenantSelect) viewerTenantSelect.classList.add('hidden');
            if (viewerTenantLabel) viewerTenantLabel.classList.add('hidden');
            return;
        }

        try {
            const res = await fetch(`/api/areas/${encodeURIComponent(currentArea)}/houses/${encodeURIComponent(currentHouse)}/tenants`);
            if (!res.ok) return;
            const tenants = await res.json();
            if (!tenants || tenants.length === 0) {
                viewerTenantSelect.classList.add('hidden');
                viewerTenantLabel.classList.add('hidden');
                return;
            }

            let currentDocTenantName = null;
            const timelineMatch = currentTimeline.find(d => d.vault_id === vaultId);
            if (timelineMatch) currentDocTenantName = timelineMatch.primary_tenant;

            viewerTenantSelect.innerHTML = '';
            tenants.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t.id;
                opt.textContent = t.name + (t.start_date ? ` (${t.start_date.substring(0,4)})` : '');
                if (currentDocTenantName && (t.name.trim() === currentDocTenantName.trim() || currentDocTenantName.includes(t.name.trim()))) {
                    opt.selected = true;
                }
                viewerTenantSelect.appendChild(opt);
            });

            viewerTenantLabel.classList.remove('hidden');
            viewerTenantSelect.classList.remove('hidden');
        } catch (err) {
            console.warn('Failed to load tenants for viewer dropdown:', err);
        }
    }

    window.openTenantModal = openTenantModal;
    window.closeTenantModal = closeTenantModal;
    window.updateViewerTenantSelect = updateViewerTenantSelect;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTenantManager);
    } else {
        initTenantManager();
    }
})();
