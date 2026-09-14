// ── Draggable Resizer Utility ─────────────────────────────────────────────
(function() {
    function setupResizer(resizerId, panelId, isPercentage = false) {
        const resizer = document.getElementById(resizerId);
        const panel = document.getElementById(panelId);
        if (!resizer || !panel) return;
        let isResizing = false;
        let startX = 0;
        let startWidth = 0;
        let activeTouchId = null;

        const storageKey = panelId === 'main-sidebar' ? 'sidebar_width' : `${panelId.replace(/-/g, '_')}_width`;
        try {
            const savedWidth = localStorage.getItem(storageKey);
            if (savedWidth) {
                panel.style.width = savedWidth;
            }
        } catch (e) {}

        function getPanelWidth() {
            let rectWidth = 0;
            if (typeof panel.getBoundingClientRect === 'function') {
                const rect = panel.getBoundingClientRect();
                rectWidth = rect ? rect.width : 0;
            }
            if (!rectWidth && panel.style.width) {
                if (panel.style.width.endsWith('%')) {
                    const parentW = (panel.parentElement && typeof panel.parentElement.getBoundingClientRect === 'function' && panel.parentElement.getBoundingClientRect().width) || window.innerWidth || 1024;
                    rectWidth = (parseFloat(panel.style.width) / 100) * parentW;
                } else {
                    rectWidth = parseFloat(panel.style.width);
                }
            }
            return rectWidth || (isPercentage ? 330 : 288);
        }

        function startResize(clientX) {
            if (isResizing) return;
            isResizing = true;
            startX = clientX;
            startWidth = getPanelWidth();
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
            resizer.classList.add('is-resizing');
        }

        function handleMove(clientX) {
            if (!isResizing) return;
            const deltaX = clientX - startX;
            let newWidth = startWidth + deltaX;

            if (isPercentage) {
                const parentW = (panel.parentElement && typeof panel.parentElement.getBoundingClientRect === 'function' && panel.parentElement.getBoundingClientRect().width) || window.innerWidth || 1024;
                let percentage = (newWidth / parentW) * 100;
                percentage = Math.max(20, Math.min(percentage, 60));
                panel.style.width = `${percentage}%`;
            } else {
                newWidth = Math.max(200, Math.min(newWidth, window.innerWidth * 0.5));
                panel.style.width = `${newWidth}px`;
            }
        }

        function endResize() {
            if (!isResizing) return;
            isResizing = false;
            activeTouchId = null;
            document.body.style.cursor = 'default';
            document.body.style.userSelect = '';
            resizer.classList.remove('is-resizing');
            if (panel.style.width) {
                try {
                    localStorage.setItem(storageKey, panel.style.width);
                } catch (e) {}
            }
        }

        // ── Mouse Listeners ──
        resizer.addEventListener('mousedown', (e) => {
            if (e.button !== undefined && e.button !== 0) return;
            startResize(e.clientX);
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            handleMove(e.clientX);
        });

        document.addEventListener('mouseup', () => {
            if (isResizing) {
                endResize();
            }
        });

        // ── Touch Listeners (Tablets / Mobile) ──
        resizer.addEventListener('touchstart', (e) => {
            if (e.touches && e.touches.length > 0) {
                activeTouchId = e.touches[0].identifier;
                startResize(e.touches[0].clientX);
                if (e.cancelable) {
                    e.preventDefault();
                }
            }
        }, { passive: false });

        document.addEventListener('touchmove', (e) => {
            if (!isResizing) return;
            if (e.touches) {
                let touch = null;
                for (let i = 0; i < e.touches.length; i++) {
                    if (e.touches[i].identifier === activeTouchId) {
                        touch = e.touches[i];
                        break;
                    }
                }
                if (!touch && e.touches.length > 0) {
                    touch = e.touches[0];
                }
                if (touch) {
                    handleMove(touch.clientX);
                    if (e.cancelable) {
                        e.preventDefault();
                    }
                }
            }
        }, { passive: false });

        document.addEventListener('touchend', () => {
            if (isResizing) {
                endResize();
            }
        });

        document.addEventListener('touchcancel', () => {
            if (isResizing) {
                endResize();
            }
        });

        // ── Pointer Listeners (Stylus / Pointer-enabled devices) ──
        if (typeof window !== 'undefined' && 'PointerEvent' in window) {
            resizer.addEventListener('pointerdown', (e) => {
                if (e.button !== undefined && e.button !== 0) return;
                startResize(e.clientX);
                if (typeof resizer.setPointerCapture === 'function') {
                    try {
                        resizer.setPointerCapture(e.pointerId);
                    } catch (err) {}
                }
            });

            document.addEventListener('pointermove', (e) => {
                if (isResizing) {
                    handleMove(e.clientX);
                }
            });

            document.addEventListener('pointerup', (e) => {
                if (isResizing) {
                    if (typeof resizer.releasePointerCapture === 'function') {
                        try {
                            resizer.releasePointerCapture(e.pointerId);
                        } catch (err) {}
                    }
                    endResize();
                }
            });

            document.addEventListener('pointercancel', (e) => {
                if (isResizing) {
                    if (typeof resizer.releasePointerCapture === 'function') {
                        try {
                            resizer.releasePointerCapture(e.pointerId);
                        } catch (err) {}
                    }
                    endResize();
                }
            });
        }
    }

    window.setupResizer = setupResizer;
})();
