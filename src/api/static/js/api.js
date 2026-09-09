// ── Shared Global State & API Helpers ─────────────────────────────────────
const API_HOUSES_BASE = '/api/houses';
const API_TREE = '/api/tree';

let isStaticMode = false;
let searchIndexData = null;
let currentArea = null;
let currentHouse = null;
let currentTenant = null;
let currentTab = 'categories';
let currentTimeline = [];
let currentCategories = [];
let globalTreeData = [];
let currentViewMode = 'overview'; // 'overview' or 'db'
let isTreeLoading = true;

function getPdfUrl(areaId, houseId, vaultId) {
    if (isStaticMode) {
        return `./${encodeURIComponent(areaId)}/${encodeURIComponent(houseId)}/.source_files/vault/doc_${vaultId}.pdf`;
    }
    return `/api/areas/${encodeURIComponent(areaId)}/houses/${encodeURIComponent(houseId)}/pdf/${vaultId}`;
}

function getDocumentGroups(stateData) {
    const routed = stateData.routed_documents || [];
    if (Array.isArray(routed) && routed.length > 0 && routed[0].vault_id) return routed;
    const grouped = stateData.grouped_documents || [];
    if (Array.isArray(grouped) && grouped.length > 0 && grouped[0].vault_id) return grouped;
    if (Array.isArray(routed) && routed.length > 0) return routed;
    if (Array.isArray(grouped) && grouped.length > 0) return grouped;
    return [];
}

async function fetchHouseState(areaId, houseId) {
    const houseNum = houseId.includes(' - ') ? houseId.split(' - ')[0] : houseId;
    const stateUrl = `./${encodeURIComponent(areaId)}/${encodeURIComponent(houseId)}/.source_files/${encodeURIComponent(houseNum)}_state.json`;
    const res = await fetch(stateUrl);
    if (!res.ok) throw new Error(`Failed to load state from ${stateUrl}`);
    return await res.json();
}

function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const isError = type === 'error';
    toast.className = `px-4 py-2.5 rounded-xl text-xs font-semibold shadow-lg border transition-all transform translate-y-2 opacity-0 pointer-events-auto flex items-center gap-2 max-w-sm ${
        isError 
            ? 'bg-rose-50 text-rose-800 border-rose-200' 
            : 'bg-emerald-50 text-emerald-800 border-emerald-200'
    }`;
    toast.innerHTML = `
        <span>${isError ? '⚠️' : '✓'}</span>
        <span>${message}</span>
    `;

    container.appendChild(toast);
    requestAnimationFrame(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    });

    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 250);
    }, 3200);
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function getNoteSnippet(notes, maxLen = 14) {
    if (!notes || typeof notes !== 'string') return '';
    const clean = notes.trim().replace(/\s+/g, ' ');
    if (!clean) return '';
    if (clean.length <= maxLen) return clean;
    return clean.substring(0, maxLen).trim() + '…';
}

window.escapeHtml = escapeHtml;
window.getNoteSnippet = getNoteSnippet;
