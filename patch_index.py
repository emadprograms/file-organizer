import re

with open('src/api/static/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the title 'Vaults' with 'Navigation' or keep it.
# Replace loadHouses with loadTree and tree building logic.

new_script = """
        // API Base URL
        const API_HOURSES_BASE = '/api/houses';
        const API_TREE = '/api/tree';
        let currentHouse = null;
        let currentTenant = null;

        // Elements
        const houseListEl = document.getElementById('house-list');
        const currentHouseTitle = document.getElementById('current-house-title');
        const statsBadge = document.getElementById('stats-badge');
        
        const docListPanel = document.getElementById('document-list-panel');
        const docViewerPanel = document.getElementById('document-viewer-panel');
        const welcomePanel = document.getElementById('welcome-panel');
        const docListEl = document.getElementById('document-list');
        
        const pdfFrame = document.getElementById('pdf-frame');
        const viewerTitle = document.getElementById('viewer-title');
        const viewerDownload = document.getElementById('viewer-download');

        // State
        let currentTimeline = [];

        async function loadTree() {
            try {
                const res = await fetch(API_TREE);
                if (!res.ok) throw new Error('Failed to load tree');
                const treeData = await res.json();
                
                houseListEl.innerHTML = '';
                if (treeData.length === 0) {
                    houseListEl.innerHTML = '<p class="text-gray-400 text-sm">No vaults found.</p>';
                    return;
                }
                
                const ul = document.createElement('ul');
                ul.className = 'pl-2 space-y-1';
                createTreeNodes(treeData, ul, '');
                houseListEl.appendChild(ul);

                // Check hash on load
                handleHashChange();
            } catch (err) {
                houseListEl.innerHTML = '<p class="text-red-400 text-sm">Error loading data.</p>';
            }
        }

        function createTreeNodes(nodes, parentEl, parentPath) {
            nodes.forEach(node => {
                const li = document.createElement('li');
                const currentPath = parentPath ? `${parentPath}/${node.id}` : `/${node.type}/${node.id}`;
                li.dataset.path = currentPath;
                li.className = 'tree-node';

                const btn = document.createElement('button');
                btn.className = 'w-full text-left px-2 py-1 rounded text-sm text-gray-700 hover:bg-blue-50 focus:outline-none flex items-center tree-item';
                
                const icon = document.createElement('span');
                icon.className = 'mr-2 text-gray-400 inline-block w-4 text-center';
                icon.innerHTML = (node.children && node.children.length > 0) ? '▶' : '•';
                
                const nameSpan = document.createElement('span');
                nameSpan.textContent = node.name;
                nameSpan.className = 'truncate';

                btn.appendChild(icon);
                btn.appendChild(nameSpan);
                li.appendChild(btn);

                let childrenContainer = null;
                if (node.children && node.children.length > 0) {
                    childrenContainer = document.createElement('ul');
                    childrenContainer.className = 'pl-4 hidden space-y-1 mt-1';
                    createTreeNodes(node.children, childrenContainer, currentPath);
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
                    };
                }

                if (node.type === 'tenant') {
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

        function handleHashChange() {
            const hash = window.location.hash.replace('#', '');
            if (!hash) return;

            // Clear previous selections
            document.querySelectorAll('.tree-item').forEach(el => {
                el.classList.remove('bg-blue-100', 'text-blue-800', 'font-medium');
            });

            const targetLi = document.querySelector(`li[data-path="${hash}"]`);
            if (targetLi) {
                const btn = targetLi.querySelector('.tree-item');
                if (btn) btn.classList.add('bg-blue-100', 'text-blue-800', 'font-medium');

                // Expand parents
                let current = targetLi.parentElement;
                while (current && current.id !== 'house-list') {
                    if (current.tagName === 'UL') {
                        current.classList.remove('hidden');
                        const parentLi = current.parentElement;
                        if (parentLi && parentLi.tagName === 'LI') {
                            const icon = parentLi.querySelector('.tree-item span');
                            if (icon) icon.innerHTML = '▼';
                        }
                    }
                    current = current.parentElement;
                }
                
                targetLi.scrollIntoView({ behavior: 'smooth', block: 'center' });

                // Extract houseId and select it
                // hash format: /area/area_id/house/house_id/tenant/tenant_id
                const parts = hash.split('/');
                let houseId = null;
                for (let i = 0; i < parts.length; i++) {
                    if (parts[i] === 'house' && i + 1 < parts.length) {
                        houseId = parts[i+1];
                    }
                }
                
                if (houseId) {
                    selectHouse(houseId);
                }
            }
        }

        window.addEventListener('hashchange', handleHashChange);

        async function selectHouse(houseId) {
            currentHouse = houseId;
            currentHouseTitle.textContent = houseId;
            
            welcomePanel.classList.add('hidden');
            docListPanel.classList.remove('hidden');
            docListPanel.classList.add('flex');
            docViewerPanel.classList.add('hidden'); // hide until a doc is selected
            
            await loadTimeline(houseId);
        }

        async function loadTimeline(houseId) {
            docListEl.innerHTML = '<p class="text-sm text-gray-500 p-2">Loading documents...</p>';
            try {
                const res = await fetch(`${API_HOURSES_BASE}/${houseId}/timeline`);
                if (!res.ok) throw new Error('Failed to load timeline');
                currentTimeline = await res.json();
                
                statsBadge.textContent = `${currentTimeline.length} Documents`;
                statsBadge.classList.remove('hidden');
                
                renderTimeline();
            } catch (err) {
                docListEl.innerHTML = '<p class="text-sm text-red-500 p-2">Error loading timeline.</p>';
            }
        }

        function renderTimeline() {
            docListEl.innerHTML = '';
            if (currentTimeline.length === 0) {
                docListEl.innerHTML = '<p class="text-sm text-gray-500 p-2">No documents found.</p>';
                return;
            }
            
            currentTimeline.forEach(doc => {
                const card = document.createElement('div');
                card.className = 'p-3 border rounded-md cursor-pointer hover:border-blue-400 hover:shadow-sm bg-white transition-all';
                
                const title = doc.brief_arabic_title || 'Untitled Document';
                const date = (doc.dates && doc.dates.length > 0) ? doc.dates[0] : 'Unknown Date';
                
                card.innerHTML = `
                    <div class="flex justify-between items-start">
                        <h4 class="text-sm font-semibold text-gray-800 line-clamp-2">${title}</h4>
                    </div>
                    <div class="mt-2 flex items-center justify-between text-xs text-gray-500">
                        <span>${date}</span>
                        <span class="bg-gray-100 px-2 py-0.5 rounded">${doc.primary_tenant || 'No Tenant'}</span>
                    </div>
                `;
                
                card.onclick = () => openDocument(doc.vault_id, title);
                docListEl.appendChild(card);
            });
        }

        function openDocument(vaultId, title) {
            docViewerPanel.classList.remove('hidden');
            docViewerPanel.classList.add('flex');
            
            viewerTitle.textContent = title;
            const pdfUrl = `${API_HOURSES_BASE}/${currentHouse}/pdf/${vaultId}`;
            pdfFrame.src = pdfUrl;
            viewerDownload.href = pdfUrl;
        }

        // Init
        loadTree();
"""

new_content = re.sub(r'// API Base URL.*loadHouses\(\);', new_script.strip(), content, flags=re.DOTALL)

with open('src/api/static/index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Patched index.html")
