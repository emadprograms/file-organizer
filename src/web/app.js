async function loadTree() {
  const response = await fetch('/api/tree');
  if (!response.ok) return [];
  return await response.json();
}

function createTreeDom(nodes, parentPath = '') {
  const ul = document.createElement('ul');
  ul.className = 'tree-node';
  
  for (const node of nodes) {
    const li = document.createElement('li');
    li.className = 'tree-node';
    li.dataset.id = node.id;
    
    const currentPath = parentPath ? `${parentPath}/${node.id}` : `/${node.type}/${node.id}`;
    li.dataset.path = currentPath;
    
    const itemDiv = document.createElement('div');
    itemDiv.className = 'tree-item';
    
    if (node.children && node.children.length > 0) {
      const toggle = document.createElement('i');
      toggle.dataset.lucide = 'chevron-right';
      toggle.className = 'toggle-icon';
      itemDiv.appendChild(toggle);
    } else {
      const spacer = document.createElement('div');
      spacer.style.width = '24px';
      itemDiv.appendChild(spacer);
    }
    
    const typeIcon = document.createElement('i');
    typeIcon.dataset.lucide = node.type === 'area' ? 'map' : node.type === 'house' ? 'home' : 'user';
    typeIcon.className = 'type-icon';
    itemDiv.appendChild(typeIcon);
    
    const textNode = document.createTextNode(node.name);
    itemDiv.appendChild(textNode);
    
    li.appendChild(itemDiv);
    
    if (node.children && node.children.length > 0) {
      const childrenDom = createTreeDom(node.children, currentPath);
      li.appendChild(childrenDom);
      
      itemDiv.addEventListener('click', (e) => {
        e.stopPropagation();
        li.classList.toggle('expanded');
        if (node.type === 'tenant') {
          window.location.hash = currentPath;
        }
      });
    } else {
      itemDiv.addEventListener('click', (e) => {
        e.stopPropagation();
        window.location.hash = currentPath;
      });
    }
    
    ul.appendChild(li);
  }
  return ul;
}

function expandToPath(path) {
  if (!path || path === '#') return;
  const hashPath = path.replace('#', '');
  
  // Select all items and remove selected
  document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('selected'));
  
  const targetLi = document.querySelector(`li[data-path="${hashPath}"]`);
  if (targetLi) {
    const targetItemDiv = targetLi.querySelector('.tree-item');
    if (targetItemDiv) targetItemDiv.classList.add('selected');
    
    let current = targetLi.parentElement;
    while (current && current.id !== 'sidebar') {
      if (current.tagName === 'LI') {
        current.classList.add('expanded');
      }
      current = current.parentElement;
    }
    targetLi.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

window.addEventListener('hashchange', () => {
  expandToPath(window.location.hash);
});

async function init() {
  const treeData = await loadTree();
  const sidebar = document.getElementById('sidebar');
  sidebar.innerHTML = '';
  
  const treeDom = createTreeDom(treeData);
  sidebar.appendChild(treeDom);
  lucide.createIcons();
  
  expandToPath(window.location.hash);
}

document.addEventListener('DOMContentLoaded', init);
