import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import path from 'path';
import fs from 'fs';

const scriptPath = path.resolve(__dirname, '../../../src/api/static/js/theme-manager.js');
const themeManager = require(scriptPath);

describe('Theme Manager Component (Dark Mode Support)', () => {
    let store = {};
    const localStorageMock = {
        getItem: vi.fn(key => (key in store ? store[key] : null)),
        setItem: vi.fn((key, val) => { store[key] = String(val); }),
        removeItem: vi.fn(key => { delete store[key]; }),
        clear: vi.fn(() => { store = {}; })
    };

    function setupDOM() {
        document.documentElement.className = '';
        document.body.innerHTML = `
            <header id="top-navbar">
                <button id="btn-theme-toggle" type="button" aria-label="Toggle Theme">
                    <svg class="moon"></svg>
                </button>
            </header>
            <div id="test-content">
                <input id="test-input" type="text" />
                <textarea id="test-textarea"></textarea>
                <div id="test-editable" contenteditable="true"></div>
            </div>
        `;
    }

    beforeEach(() => {
        store = {};
        vi.stubGlobal('localStorage', localStorageMock);
        setupDOM();
        vi.stubGlobal('matchMedia', vi.fn().mockImplementation(query => ({
            matches: false,
            media: query,
            onchange: null,
            addListener: vi.fn(),
            removeListener: vi.fn(),
            addEventListener: vi.fn(),
            removeEventListener: vi.fn(),
            dispatchEvent: vi.fn(),
        })));
    });

    afterEach(() => {
        document.documentElement.className = '';
        store = {};
        vi.restoreAllMocks();
    });

    it('initializes with light theme by default if no preference is stored', () => {
        themeManager.initTheme();
        expect(themeManager.getTheme()).toBe('light');
        expect(document.documentElement.classList.contains('dark')).toBe(false);
        const btn = document.getElementById('btn-theme-toggle');
        expect(btn.getAttribute('aria-label')).toBe('Switch to Dark Mode');
    });

    it('initializes with dark theme if system prefers dark and no preference is stored', () => {
        vi.stubGlobal('matchMedia', vi.fn().mockImplementation(query => ({
            matches: query.includes('dark'),
            media: query,
            addEventListener: vi.fn(),
            removeEventListener: vi.fn(),
        })));

        themeManager.initTheme();
        expect(themeManager.getTheme()).toBe('dark');
        expect(document.documentElement.classList.contains('dark')).toBe(true);
        const btn = document.getElementById('btn-theme-toggle');
        expect(btn.getAttribute('aria-label')).toBe('Switch to Light Mode');
    });

    it('initializes with stored theme from localStorage', () => {
        localStorage.setItem('theme', 'dark');
        themeManager.initTheme();
        expect(themeManager.getTheme()).toBe('dark');
        expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    it('toggles theme between light and dark upon calling toggleTheme()', () => {
        themeManager.initTheme();
        expect(themeManager.getTheme()).toBe('light');
        expect(document.documentElement.classList.contains('dark')).toBe(false);

        const newTheme = themeManager.toggleTheme();
        expect(newTheme).toBe('dark');
        expect(themeManager.getTheme()).toBe('dark');
        expect(document.documentElement.classList.contains('dark')).toBe(true);
        expect(localStorage.getItem('theme')).toBe('dark');

        const backTheme = themeManager.toggleTheme();
        expect(backTheme).toBe('light');
        expect(themeManager.getTheme()).toBe('light');
        expect(document.documentElement.classList.contains('dark')).toBe(false);
        expect(localStorage.getItem('theme')).toBe('light');
    });

    it('dispatches themechange CustomEvent when theme changes', () => {
        themeManager.initTheme();
        const listener = vi.fn();
        window.addEventListener('themechange', listener);

        themeManager.setTheme('dark');
        expect(listener).toHaveBeenCalled();
        expect(listener.mock.calls[0][0].detail.theme).toBe('dark');

        window.removeEventListener('themechange', listener);
    });

    it('toggles theme when clicking #btn-theme-toggle in navbar', () => {
        themeManager.initTheme();
        const btn = document.getElementById('btn-theme-toggle');
        expect(document.documentElement.classList.contains('dark')).toBe(false);

        btn.click();
        expect(document.documentElement.classList.contains('dark')).toBe(true);
        expect(localStorage.getItem('theme')).toBe('dark');
        expect(btn.getAttribute('aria-label')).toBe('Switch to Light Mode');

        btn.click();
        expect(document.documentElement.classList.contains('dark')).toBe(false);
        expect(localStorage.getItem('theme')).toBe('light');
        expect(btn.getAttribute('aria-label')).toBe('Switch to Dark Mode');
    });

    it('toggles theme on Shift+D keyboard shortcut when not typing in an input', () => {
        themeManager.initTheme();
        expect(document.documentElement.classList.contains('dark')).toBe(false);

        const event = new KeyboardEvent('keydown', {
            key: 'D',
            shiftKey: true,
            bubbles: true,
            cancelable: true,
        });
        document.dispatchEvent(event);

        expect(document.documentElement.classList.contains('dark')).toBe(true);
        expect(localStorage.getItem('theme')).toBe('dark');
    });

    it('does not toggle theme on Shift+D when user is typing in an input, textarea or contenteditable', () => {
        themeManager.initTheme();
        expect(document.documentElement.classList.contains('dark')).toBe(false);

        const input = document.getElementById('test-input');
        input.focus();

        const event = new KeyboardEvent('keydown', {
            key: 'D',
            shiftKey: true,
            bubbles: true,
            cancelable: true,
        });
        input.dispatchEvent(event);

        expect(document.documentElement.classList.contains('dark')).toBe(false);
        expect(localStorage.getItem('theme')).toBeNull();
    });

    it('verifies index.html has Tailwind darkMode config and theme toggle button', () => {
        const htmlPath = path.resolve(__dirname, '../../../web-net/wwwroot/index.html');
        const html = fs.readFileSync(htmlPath, 'utf8');

        expect(html).toContain("darkMode: 'class'");
        expect(html).toContain('id="btn-theme-toggle"');
        expect(html).toContain('js/theme-manager.js');
    });
});
