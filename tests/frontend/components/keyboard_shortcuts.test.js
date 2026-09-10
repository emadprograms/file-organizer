import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import path from 'path';

const scriptPath = path.resolve(__dirname, '../../../src/api/static/js/keyboard-shortcuts.js');
const shortcutsModule = require(scriptPath);

describe('Keyboard Shortcuts Helper Modal Component (Phase 108)', () => {
    function setupDOM() {
        document.body.innerHTML = `
            <header>
                <button id="btn-search-trigger" type="button">Search</button>
                <button id="btn-shortcuts-trigger" type="button" title="Keyboard Shortcuts (?)">?</button>
                <button id="btn-ingest-trigger" type="button">Upload</button>
            </header>

            <div id="keyboard-shortcuts-modal" class="hidden" tabindex="-1">
                <div class="modal-card">
                    <h3 id="shortcuts-modal-title">Keyboard Shortcuts</h3>
                    <button id="shortcuts-modal-close" type="button">X</button>
                    <div id="shortcuts-body">
                        <span>⌘K / Ctrl+K</span>
                        <span>⌘I / Ctrl+I</span>
                        <span>Space</span>
                        <span>Esc</span>
                        <span>?</span>
                    </div>
                    <button id="btn-shortcuts-close" type="button">Close</button>
                </div>
            </div>

            <div id="test-container">
                <input id="test-input" type="text" />
                <textarea id="test-textarea"></textarea>
                <div id="test-editable" contenteditable="true"></div>
            </div>
        `;
    }

    beforeEach(() => {
        setupDOM();
        shortcutsModule.initKeyboardShortcuts();
    });

    afterEach(() => {
        shortcutsModule.destroyKeyboardShortcuts();
        document.body.innerHTML = '';
        vi.restoreAllMocks();
    });

    it('opens the modal when pressing "?" (Shift+/)', () => {
        const modal = document.getElementById('keyboard-shortcuts-modal');
        expect(modal.classList.contains('hidden')).toBe(true);

        const event = new KeyboardEvent('keydown', {
            key: '?',
            bubbles: true,
            cancelable: true,
        });
        document.dispatchEvent(event);

        expect(modal.classList.contains('hidden')).toBe(false);
        expect(shortcutsModule.isShortcutsOpen()).toBe(true);
    });

    it('toggles the modal closed when pressing "?" again', () => {
        const modal = document.getElementById('keyboard-shortcuts-modal');
        shortcutsModule.openShortcutsModal();
        expect(modal.classList.contains('hidden')).toBe(false);

        const event = new KeyboardEvent('keydown', {
            key: '?',
            bubbles: true,
            cancelable: true,
        });
        document.dispatchEvent(event);

        expect(modal.classList.contains('hidden')).toBe(true);
        expect(shortcutsModule.isShortcutsOpen()).toBe(false);
    });

    it('opens the modal when clicking the navbar trigger button #btn-shortcuts-trigger', () => {
        const modal = document.getElementById('keyboard-shortcuts-modal');
        const triggerBtn = document.getElementById('btn-shortcuts-trigger');
        expect(modal.classList.contains('hidden')).toBe(true);

        triggerBtn.click();

        expect(modal.classList.contains('hidden')).toBe(false);
        expect(shortcutsModule.isShortcutsOpen()).toBe(true);
    });

    it('closes the modal when pressing Escape', () => {
        const modal = document.getElementById('keyboard-shortcuts-modal');
        shortcutsModule.openShortcutsModal();
        expect(modal.classList.contains('hidden')).toBe(false);

        const event = new KeyboardEvent('keydown', {
            key: 'Escape',
            bubbles: true,
            cancelable: true,
        });
        document.dispatchEvent(event);

        expect(modal.classList.contains('hidden')).toBe(true);
        expect(shortcutsModule.isShortcutsOpen()).toBe(false);
    });

    it('closes the modal when clicking the header close button #shortcuts-modal-close', () => {
        const modal = document.getElementById('keyboard-shortcuts-modal');
        const closeBtn = document.getElementById('shortcuts-modal-close');
        shortcutsModule.openShortcutsModal();
        expect(modal.classList.contains('hidden')).toBe(false);

        closeBtn.click();

        expect(modal.classList.contains('hidden')).toBe(true);
    });

    it('closes the modal when clicking the footer close button #btn-shortcuts-close', () => {
        const modal = document.getElementById('keyboard-shortcuts-modal');
        const footerCloseBtn = document.getElementById('btn-shortcuts-close');
        shortcutsModule.openShortcutsModal();
        expect(modal.classList.contains('hidden')).toBe(false);

        footerCloseBtn.click();

        expect(modal.classList.contains('hidden')).toBe(true);
    });

    it('closes the modal on backdrop click but preserves it when clicking inside the card', () => {
        const modal = document.getElementById('keyboard-shortcuts-modal');
        const card = modal.querySelector('.modal-card');
        shortcutsModule.openShortcutsModal();
        expect(modal.classList.contains('hidden')).toBe(false);

        // Click inside modal card should NOT close
        card.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(modal.classList.contains('hidden')).toBe(false);

        // Click backdrop directly should close
        modal.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(modal.classList.contains('hidden')).toBe(true);
    });

    it('does NOT trigger the shortcuts modal when typing inside an input element', () => {
        const modal = document.getElementById('keyboard-shortcuts-modal');
        const input = document.getElementById('test-input');
        input.focus();

        const event = new KeyboardEvent('keydown', {
            key: '?',
            bubbles: true,
            cancelable: true,
        });
        input.dispatchEvent(event);

        expect(modal.classList.contains('hidden')).toBe(true);
        expect(shortcutsModule.isShortcutsOpen()).toBe(false);
    });

    it('does NOT trigger the shortcuts modal when typing inside a textarea element', () => {
        const modal = document.getElementById('keyboard-shortcuts-modal');
        const textarea = document.getElementById('test-textarea');
        textarea.focus();

        const event = new KeyboardEvent('keydown', {
            key: '?',
            bubbles: true,
            cancelable: true,
        });
        textarea.dispatchEvent(event);

        expect(modal.classList.contains('hidden')).toBe(true);
    });

    it('does NOT trigger the shortcuts modal when typing inside a contenteditable element', () => {
        const modal = document.getElementById('keyboard-shortcuts-modal');
        const editable = document.getElementById('test-editable');
        editable.focus();

        const event = new KeyboardEvent('keydown', {
            key: '?',
            bubbles: true,
            cancelable: true,
        });
        editable.dispatchEvent(event);

        expect(modal.classList.contains('hidden')).toBe(true);
    });

    it('does NOT trigger when modifier keys (meta, ctrl, alt) are pressed with "?"', () => {
        const modal = document.getElementById('keyboard-shortcuts-modal');

        // Cmd + ?
        document.dispatchEvent(new KeyboardEvent('keydown', {
            key: '?',
            metaKey: true,
            bubbles: true,
            cancelable: true,
        }));
        expect(modal.classList.contains('hidden')).toBe(true);

        // Ctrl + ?
        document.dispatchEvent(new KeyboardEvent('keydown', {
            key: '?',
            ctrlKey: true,
            bubbles: true,
            cancelable: true,
        }));
        expect(modal.classList.contains('hidden')).toBe(true);

        // Alt + ?
        document.dispatchEvent(new KeyboardEvent('keydown', {
            key: '?',
            altKey: true,
            bubbles: true,
            cancelable: true,
        }));
        expect(modal.classList.contains('hidden')).toBe(true);
    });

    it('focuses close button when modal is opened', () => {
        const closeBtn = document.getElementById('shortcuts-modal-close');
        const focusSpy = vi.spyOn(closeBtn, 'focus');

        shortcutsModule.openShortcutsModal();

        expect(focusSpy).toHaveBeenCalled();
    });
});
