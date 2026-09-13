// ── Theme Manager (Light & Dark Mode) ───────────────────────────────────────
(function() {
    const STORAGE_KEY = 'theme';

    const MOON_ICON = `<svg class="w-4 h-4 text-slate-500 hover:text-slate-800 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>`;
    const SUN_ICON = `<svg class="w-4 h-4 text-amber-400 hover:text-amber-300 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>`;

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

    function getSystemPreference() {
        if (typeof window !== 'undefined' && window.matchMedia) {
            return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        return 'light';
    }

    function getStoredTheme() {
        try {
            if (typeof localStorage !== 'undefined') {
                return localStorage.getItem(STORAGE_KEY);
            }
        } catch (e) {
            // LocalStorage might be disabled in sandboxed iframe
        }
        return null;
    }

    function getTheme() {
        const stored = getStoredTheme();
        if (stored === 'dark' || stored === 'light') {
            return stored;
        }
        if (typeof document !== 'undefined' && document.documentElement) {
            if (document.documentElement.classList.contains('dark')) {
                return 'dark';
            }
        }
        return getSystemPreference();
    }

    function updateToggleButton(theme) {
        if (typeof document === 'undefined') return;
        const btn = document.getElementById('btn-theme-toggle');
        if (!btn) return;

        if (theme === 'dark') {
            btn.innerHTML = SUN_ICON;
            btn.title = 'Switch to Light Mode (Shift+D) / تفعيل الوضع الفاتح';
            btn.setAttribute('aria-label', 'Switch to Light Mode');
        } else {
            btn.innerHTML = MOON_ICON;
            btn.title = 'Switch to Dark Mode (Shift+D) / تفعيل الوضع الداكن';
            btn.setAttribute('aria-label', 'Switch to Dark Mode');
        }
    }

    function applyTheme(theme, persist = true) {
        const targetTheme = theme === 'dark' ? 'dark' : 'light';

        if (typeof document !== 'undefined' && document.documentElement) {
            if (targetTheme === 'dark') {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }
        }

        if (persist) {
            try {
                if (typeof localStorage !== 'undefined') {
                    localStorage.setItem(STORAGE_KEY, targetTheme);
                }
            } catch (e) {
                // ignore
            }
        }

        updateToggleButton(targetTheme);

        if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function') {
            try {
                window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: targetTheme } }));
            } catch (e) {
                // ignore
            }
        }

        return targetTheme;
    }

    function setTheme(theme) {
        return applyTheme(theme, true);
    }

    function toggleTheme() {
        const current = getTheme();
        const next = current === 'dark' ? 'light' : 'dark';
        return setTheme(next);
    }

    function handleKeyDown(e) {
        if (!e) return;
        const activeEl = typeof document !== 'undefined' ? document.activeElement : null;
        if (isEditableTarget(activeEl) || isEditableTarget(e.target)) {
            return;
        }

        // Shortcut: Shift + D (or 'D') without Ctrl/Meta/Alt
        if (e.shiftKey && (e.key === 'D' || e.key === 'd') && !e.metaKey && !e.ctrlKey && !e.altKey) {
            e.preventDefault();
            toggleTheme();
        }
    }

    function initTheme() {
        // Apply current theme (without persisting if no preference was previously stored)
        const stored = getStoredTheme();
        const activeTheme = getTheme();
        applyTheme(activeTheme, Boolean(stored));

        if (typeof document !== 'undefined') {
            const btn = document.getElementById('btn-theme-toggle');
            if (btn) {
                btn.onclick = (e) => {
                    e.preventDefault();
                    toggleTheme();
                };
            }

            // Keyboard shortcut Shift+D
            document.removeEventListener('keydown', handleKeyDown);
            document.addEventListener('keydown', handleKeyDown);
        }

        // Listen for OS system theme change if no explicit manual preference
        if (typeof window !== 'undefined' && window.matchMedia) {
            try {
                const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
                const handlePrefChange = (e) => {
                    if (!getStoredTheme()) {
                        setTheme(e.matches ? 'dark' : 'light');
                    }
                };
                if (typeof mediaQuery.addEventListener === 'function') {
                    mediaQuery.addEventListener('change', handlePrefChange);
                } else if (typeof mediaQuery.addListener === 'function') {
                    mediaQuery.addListener(handlePrefChange);
                }
            } catch (e) {
                // ignore
            }
        }
    }

    const themeManager = {
        getTheme,
        setTheme,
        toggleTheme,
        initTheme,
        updateToggleButton,
    };

    if (typeof window !== 'undefined') {
        window.themeManager = themeManager;
        window.getTheme = getTheme;
        window.setTheme = setTheme;
        window.toggleTheme = toggleTheme;
        window.initTheme = initTheme;
    }

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = themeManager;
    }
})();
