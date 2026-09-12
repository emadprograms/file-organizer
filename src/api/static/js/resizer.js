// ── Draggable Resizer Utility ─────────────────────────────────────────────
(function() {
    function setupResizer(resizerId, panelId, isPercentage = false) {
        const resizer = document.getElementById(resizerId);
        const panel = document.getElementById(panelId);
        if (!resizer || !panel) return;
        let isResizing = false;
        let startX;
        let startWidth;

        if (panelId === 'main-sidebar') {
            try {
                const savedWidth = localStorage.getItem('sidebar_width');
                if (savedWidth) {
                    panel.style.width = savedWidth;
                }
            } catch (e) {}
        }

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
                if (panelId === 'main-sidebar' && panel.style.width) {
                    try {
                        localStorage.setItem('sidebar_width', panel.style.width);
                    } catch (e) {}
                }
            }
        });
    }

    window.setupResizer = setupResizer;
})();
