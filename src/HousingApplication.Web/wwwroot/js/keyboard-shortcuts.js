// ── Keyboard Shortcuts Helper Modal Controller ──────────────────────────────
(function() {
    let isInitialized = false;

    function isEditableTarget(target) {
        if (!target) return false;
        const tag = (target.tagName || '').toLowerCase();
        if (tag === 'input' || tag === 'textarea' || tag === 'select') {
            return true;
        }
        if (target.isContentEditable) {
            return true;
        }
        if (typeof target.getAttribute === 'function' && target.getAttribute('contenteditable') === 'true') {
            return true;
        }
        return false;
    }

    function isShortcutsOpen() {
        const modal = document.getElementById('keyboard-shortcuts-modal');
        return Boolean(modal && !modal.classList.contains('hidden'));
    }

    function openShortcutsModal() {
        const modal = document.getElementById('keyboard-shortcuts-modal');
        if (!modal) return;
        modal.classList.remove('hidden');

        // Focus close button for accessibility
        const closeBtn = document.getElementById('shortcuts-modal-close');
        if (closeBtn && typeof closeBtn.focus === 'function') {
            closeBtn.focus();
        }
    }

    function closeShortcutsModal() {
        const modal = document.getElementById('keyboard-shortcuts-modal');
        if (!modal) return;
        modal.classList.add('hidden');
    }

    function toggleShortcutsModal() {
        if (isShortcutsOpen()) {
            closeShortcutsModal();
        } else {
            openShortcutsModal();
        }
    }

    function handleKeyDown(e) {
        if (!e) return;

        // Never intercept keyboard shortcuts when typing in inputs or contenteditable elements
        const activeEl = document.activeElement;
        if (isEditableTarget(activeEl) || isEditableTarget(e.target)) {
            return;
        }

        // Toggle shortcuts guide when '?' (Shift+/) is pressed without Meta/Ctrl/Alt modifiers
        if (e.key === '?' && !e.metaKey && !e.ctrlKey && !e.altKey) {
            e.preventDefault();
            toggleShortcutsModal();
            return;
        }

        // Close on Escape if the modal is currently open
        if (e.key === 'Escape') {
            if (isShortcutsOpen()) {
                e.preventDefault();
                closeShortcutsModal();
            }
        }
    }

    function initKeyboardShortcuts() {
        const triggerBtn = document.getElementById('btn-shortcuts-trigger');
        if (triggerBtn) {
            triggerBtn.onclick = (e) => {
                e.preventDefault();
                toggleShortcutsModal();
            };
        }

        const closeBtn = document.getElementById('shortcuts-modal-close');
        if (closeBtn) {
            closeBtn.onclick = (e) => {
                e.preventDefault();
                closeShortcutsModal();
            };
        }

        const footerCloseBtn = document.getElementById('btn-shortcuts-close');
        if (footerCloseBtn) {
            footerCloseBtn.onclick = (e) => {
                e.preventDefault();
                closeShortcutsModal();
            };
        }

        const modal = document.getElementById('keyboard-shortcuts-modal');
        if (modal) {
            modal.onclick = (e) => {
                if (e.target === modal) {
                    closeShortcutsModal();
                }
            };
        }

        if (!isInitialized) {
            document.addEventListener('keydown', handleKeyDown);
            isInitialized = true;
        }
    }

    function destroyKeyboardShortcuts() {
        if (typeof document !== 'undefined') {
            document.removeEventListener('keydown', handleKeyDown);
        }
        isInitialized = false;
    }

    // Expose global methods on window
    if (typeof window !== 'undefined') {
        window.openShortcutsModal = openShortcutsModal;
        window.closeShortcutsModal = closeShortcutsModal;
        window.toggleShortcutsModal = toggleShortcutsModal;
        window.isShortcutsOpen = isShortcutsOpen;
        window.isEditableTarget = isEditableTarget;
        window.initKeyboardShortcuts = initKeyboardShortcuts;
        window.destroyKeyboardShortcuts = destroyKeyboardShortcuts;
        window.handleShortcutsKeyDown = handleKeyDown;
    }

    // Node / Vitest module export
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            isEditableTarget,
            isShortcutsOpen,
            openShortcutsModal,
            closeShortcutsModal,
            toggleShortcutsModal,
            handleKeyDown,
            initKeyboardShortcuts,
            destroyKeyboardShortcuts,
        };
    }

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initKeyboardShortcuts);
        } else {
            initKeyboardShortcuts();
        }
    }
})();
