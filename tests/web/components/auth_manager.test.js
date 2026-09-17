import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('AuthManager, Login Screen & Session UI (Phase 117)', () => {
    const htmlPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/index.html');
    const authJsPath = path.resolve(__dirname, '../../../src/HousingApplication.Web/wwwroot/js/auth-manager.js');
    const htmlContent = fs.readFileSync(htmlPath, 'utf8');
    const authJsContent = fs.readFileSync(authJsPath, 'utf8');

    let originalFetch;

    beforeEach(() => {
        document.body.innerHTML = htmlContent;
        originalFetch = window.fetch;
        window.showToast = vi.fn();
        delete window._authFetchIntercepted;
        delete window.authManager;

        // Execute auth-manager.js script in JSDOM context
        const fn = new Function(authJsContent);
        fn();
    });

    afterEach(() => {
        window.fetch = originalFetch;
        vi.restoreAllMocks();
    });

    it('verifies index.html has complete user profile navbar components', () => {
        const profileWrapper = document.getElementById('user-profile-wrapper');
        expect(profileWrapper).not.toBeNull();

        const profileBtn = document.getElementById('user-profile-btn');
        expect(profileBtn).not.toBeNull();

        const avatarBadge = document.getElementById('user-avatar-badge');
        expect(avatarBadge).not.toBeNull();

        const nameElem = document.getElementById('user-display-name');
        expect(nameElem).not.toBeNull();

        const roleBadge = document.getElementById('user-role-badge');
        expect(roleBadge).not.toBeNull();

        const dropdown = document.getElementById('user-profile-dropdown');
        expect(dropdown).not.toBeNull();
        expect(dropdown.classList.contains('hidden')).toBe(true);

        const btnSwitch = document.getElementById('btn-switch-user');
        expect(btnSwitch).not.toBeNull();

        const btnLogout = document.getElementById('btn-logout');
        expect(btnLogout).not.toBeNull();
    });

    it('verifies index.html has full login screen overlay with preset user chips and form', () => {
        const loginScreen = document.getElementById('login-screen');
        expect(loginScreen).not.toBeNull();

        const loginForm = document.getElementById('login-form');
        expect(loginForm).not.toBeNull();

        const usernameInput = document.getElementById('login-username');
        expect(usernameInput).not.toBeNull();

        const passwordInput = document.getElementById('login-password');
        expect(passwordInput).not.toBeNull();

        const btnTogglePassword = document.getElementById('btn-toggle-password');
        expect(btnTogglePassword).not.toBeNull();

        const submitBtn = document.getElementById('btn-login-submit');
        expect(submitBtn).not.toBeNull();

        const presetsContainer = document.getElementById('login-presets-container');
        expect(presetsContainer).not.toBeNull();

        const errorBox = document.getElementById('login-error');
        expect(errorBox).not.toBeNull();
    });

    it('renders all 10 seeded users split into Admins and Contributors chips', () => {
        const mgr = window.authManager;
        mgr.renderUserChips();

        const container = document.getElementById('login-presets-container');
        expect(container).not.toBeNull();

        // 4 Admins
        const adminNames = ['Emad', 'Bubshait', 'Ehtezaz', 'Mustafa'];
        for (const name of adminNames) {
            const chip = container.querySelector(`button[data-username="${name}"]`);
            expect(chip, `Missing admin chip for ${name}`).not.toBeNull();
        }

        // 6 Contributors
        const contribNames = ['Nawaf', 'Naseem', 'Mulla', 'Mariam', 'Shaima', 'Mona'];
        for (const name of contribNames) {
            const chip = container.querySelector(`button[data-username="${name}"]`);
            expect(chip, `Missing contributor chip for ${name}`).not.toBeNull();
        }
    });

    it('clicking preset user chip automatically pre-fills username and demo password', () => {
        const mgr = window.authManager;
        mgr.renderUserChips();

        const container = document.getElementById('login-presets-container');
        const emadChip = container.querySelector('button[data-username="Emad"]');
        expect(emadChip).not.toBeNull();

        emadChip.click();

        const usernameInput = document.getElementById('login-username');
        const passwordInput = document.getElementById('login-password');

        expect(usernameInput.value).toBe('Emad');
        expect(passwordInput.value).toBe('password123');
    });

    it('toggles password visibility when toggle button is clicked', () => {
        const toggleBtn = document.getElementById('btn-toggle-password');
        const passwordInput = document.getElementById('login-password');

        expect(passwordInput.type).toBe('password');
        toggleBtn.click();
        expect(passwordInput.type).toBe('text');
        toggleBtn.click();
        expect(passwordInput.type).toBe('password');
    });

    it('authenticates Admin user (Emad) and sets full access permissions', async () => {
        const mgr = window.authManager;

        window.fetch = vi.fn().mockImplementation((url) => {
            if (url === '/api/auth/login') {
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: async () => ({
                        status: 'success',
                        message: 'Login successful',
                        user: { id: 1, username: 'Emad', displayName: 'Emad', role: 'Admin' }
                    })
                });
            }
            return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
        });

        let eventDetail = null;
        window.addEventListener('auth:user-changed', (e) => {
            eventDetail = e.detail;
        });

        const success = await mgr.login('Emad', 'password123');
        expect(success).toBe(true);

        // Verification of state
        expect(mgr.currentUser).not.toBeNull();
        expect(mgr.currentUser.username).toBe('Emad');
        expect(mgr.currentUser.role).toBe('Admin');
        expect(mgr.isAdmin()).toBe(true);
        expect(mgr.isContributor()).toBe(false);
        expect(mgr.hasDeletePermission()).toBe(true);

        // Verification of navbar UI
        const nameElem = document.getElementById('user-display-name');
        expect(nameElem.textContent).toBe('Emad');
        const roleBadge = document.getElementById('user-role-badge');
        expect(roleBadge.textContent).toContain('Full Access');

        // Verification of event
        expect(eventDetail).not.toBeNull();
        expect(eventDetail.canDelete).toBe(true);
        expect(eventDetail.isAdmin).toBe(true);
        expect(eventDetail.isContributor).toBe(false);

        // Login modal should be closed
        const loginScreen = document.getElementById('login-screen');
        expect(loginScreen.classList.contains('hidden')).toBe(true);
    });

    it('authenticates Contributor user (Nawaf) and enforces read & upload only (no delete permission)', async () => {
        const mgr = window.authManager;

        window.fetch = vi.fn().mockImplementation((url) => {
            if (url === '/api/auth/login') {
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: async () => ({
                        status: 'success',
                        message: 'Login successful',
                        user: { id: 5, username: 'Nawaf', displayName: 'Nawaf', role: 'Contributor' }
                    })
                });
            }
            return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
        });

        let eventDetail = null;
        window.addEventListener('auth:user-changed', (e) => {
            eventDetail = e.detail;
        });

        const success = await mgr.login('Nawaf', 'password123');
        expect(success).toBe(true);

        // Verification of state
        expect(mgr.currentUser).not.toBeNull();
        expect(mgr.currentUser.username).toBe('Nawaf');
        expect(mgr.currentUser.role).toBe('Contributor');
        expect(mgr.isAdmin()).toBe(false);
        expect(mgr.isContributor()).toBe(true);
        expect(mgr.hasDeletePermission()).toBe(false);

        // Verification of navbar UI
        const nameElem = document.getElementById('user-display-name');
        expect(nameElem.textContent).toBe('Nawaf');
        const roleBadge = document.getElementById('user-role-badge');
        expect(roleBadge.textContent).toContain('Read & Upload');

        // Verification of event
        expect(eventDetail).not.toBeNull();
        expect(eventDetail.canDelete).toBe(false);
        expect(eventDetail.isAdmin).toBe(false);
        expect(eventDetail.isContributor).toBe(true);
    });

    it('displays error on failed login attempt', async () => {
        const mgr = window.authManager;

        window.fetch = vi.fn().mockImplementation((url) => {
            if (url === '/api/auth/login') {
                return Promise.resolve({
                    ok: false,
                    status: 401,
                    json: async () => ({
                        status: 'error',
                        message: 'اسم المستخدم أو كلمة المرور غير صحيحة'
                    })
                });
            }
            return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
        });

        const success = await mgr.login('InvalidUser', 'wrongpass');
        expect(success).toBe(false);
        expect(mgr.currentUser).toBeNull();

        const errorBox = document.getElementById('login-error');
        expect(errorBox.classList.contains('hidden')).toBe(false);
        expect(errorBox.textContent).toContain('اسم المستخدم أو كلمة المرور غير صحيحة');
    });

    it('logs out and returns user to unauthenticated state with login screen open', async () => {
        const mgr = window.authManager;
        mgr.currentUser = { id: 1, username: 'Emad', displayName: 'Emad', role: 'Admin', canDelete: true };

        window.fetch = vi.fn().mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => ({ status: 'success' })
        });

        let eventDetail = null;
        window.addEventListener('auth:user-changed', (e) => {
            eventDetail = e.detail;
        });

        await mgr.logout();

        expect(mgr.currentUser).toBeNull();
        expect(mgr.hasDeletePermission()).toBe(false);

        const loginScreen = document.getElementById('login-screen');
        expect(loginScreen.classList.contains('hidden')).toBe(false);

        const nameElem = document.getElementById('user-display-name');
        expect(nameElem.textContent).toBe('غير مسجل');

        expect(eventDetail).not.toBeNull();
        expect(eventDetail.user).toBeNull();
        expect(eventDetail.canDelete).toBe(false);
    });

    it('correctly evaluates permissions across all 10 users in the system', () => {
        const mgr = window.authManager;

        const admins = ['Emad', 'Bubshait', 'Ehtezaz', 'Mustafa'];
        for (const admin of admins) {
            mgr.currentUser = { username: admin, role: 'Admin', canDelete: true };
            expect(mgr.isAdmin()).toBe(true);
            expect(mgr.isContributor()).toBe(false);
            expect(mgr.hasDeletePermission()).toBe(true);
        }

        const contributors = ['Nawaf', 'Naseem', 'Mulla', 'Mariam', 'Shaima', 'Mona'];
        for (const contrib of contributors) {
            mgr.currentUser = { username: contrib, role: 'Contributor', canDelete: false };
            expect(mgr.isAdmin()).toBe(false);
            expect(mgr.isContributor()).toBe(true);
            expect(mgr.hasDeletePermission()).toBe(false);
        }
    });

    it('fetch interceptor automatically attaches credentials and role headers', async () => {
        const mgr = window.authManager;
        mgr.currentUser = { username: 'Mustafa', role: 'Admin', canDelete: true };

        let capturedInit = null;
        window.fetch = vi.fn().mockImplementation((url, init) => {
            capturedInit = init;
            return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
        });

        mgr.setupFetchInterceptor(true);

        await window.fetch('/api/houses');

        expect(capturedInit).not.toBeNull();
        expect(capturedInit.credentials).toBe('same-origin');
        expect(capturedInit.headers['X-User-Role']).toBe('Admin');
        expect(capturedInit.headers['X-User']).toBe('Mustafa');
    });

    it('fetch interceptor detects 403 Forbidden and displays user-friendly error toast', async () => {
        const mgr = window.authManager;
        mgr.currentUser = { username: 'Shaima', role: 'Contributor', canDelete: false };

        window.fetch = vi.fn().mockResolvedValue({
            ok: false,
            status: 403,
            json: async () => ({ error: 'Forbidden: Contributors do not have permission to delete' })
        });

        mgr.setupFetchInterceptor(true);

        await window.fetch('/api/documents/some-doc', { method: 'DELETE' });

        expect(window.showToast).toHaveBeenCalledWith(
            expect.stringContaining('عذراً: ليس لديك صلاحية حذف الوثائق أو العناصر'),
            'error'
        );
    });
});
