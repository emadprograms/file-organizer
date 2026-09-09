// ── Database Inspector Component ──────────────────────────────────────────
(function() {
    let currentDbTable = 'houses';
    let dbTableOffset = 0;
    const dbTableLimit = 50;
    let dbTableTotal = 0;
    let dbTableSearchTerm = '';

    function initDbInspector() {
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
    }

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

    window.initDbInspector = initDbInspector;
    window.loadDbInspector = loadDbInspector;
    window.loadDbTableRows = loadDbTableRows;
})();
