/**
 * AuthManager - Manages authentication, user session, RBAC permissions, and UI synchronization.
 * Bilingual Arabic (RTL primary) and English support.
 */
(function() {
    'use strict';

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    class AuthManager {
        constructor() {
            this.currentUser = null;
            this.users = [];
            this.isLoading = false;
            this._listeners = [];
            this.isInitialized = false;

            // Pre-seed fallback users list for offline/fast-init support
            this.fallbackUsers = [
                { id: 1, username: 'Emad', displayName: 'Emad', role: 'Admin' },
                { id: 2, username: 'Bubshait', displayName: 'Bubshait', role: 'Admin' },
                { id: 3, username: 'Ehtezaz', displayName: 'Ehtezaz', role: 'Admin' },
                { id: 4, username: 'Mustafa', displayName: 'Mustafa', role: 'Admin' },
                { id: 5, username: 'Nawaf', displayName: 'Nawaf', role: 'Contributor' },
                { id: 6, username: 'Naseem', displayName: 'Naseem', role: 'Contributor' },
                { id: 7, username: 'Mulla', displayName: 'Mulla', role: 'Contributor' },
                { id: 8, username: 'Mariam', displayName: 'Mariam', role: 'Contributor' },
                { id: 9, username: 'Shaima', displayName: 'Shaima', role: 'Contributor' },
                { id: 10, username: 'Mona', displayName: 'Mona', role: 'Contributor' }
            ];
        }

        async init() {
            if (this.isInitialized) return;
            this.isInitialized = true;

            this.setupFetchInterceptor();
            this.bindDomEvents();

            // Load user list and verify active session
            await this.loadUsers();
            await this.checkSession();
        }

        setupFetchInterceptor(force = false) {
            if (window._authFetchIntercepted && !force) return;
            window._authFetchIntercepted = true;

            const originalFetch = window.fetch;
            const self = this;

            window.fetch = async function(resource, init = {}) {
                const options = { ...init };

                // Ensure same-origin credentials for cookies
                if (!options.credentials) {
                    options.credentials = 'same-origin';
                }

                // If user is logged in, attach headers for additional backend verification
                if (self.currentUser) {
                    const role = self.currentUser.role || 'Admin';
                    const uname = self.currentUser.username || 'Emad';
                    options.headers = options.headers || {};
                    if (options.headers instanceof Headers) {
                        options.headers.set('X-User-Role', role);
                        options.headers.set('X-User', uname);
                    } else if (Array.isArray(options.headers)) {
                        options.headers = options.headers.filter(h => h[0] !== 'X-User-Role' && h[0] !== 'X-User');
                        options.headers.push(['X-User-Role', role]);
                        options.headers.push(['X-User', uname]);
                    } else {
                        options.headers['X-User-Role'] = role;
                        options.headers['X-User'] = uname;
                    }
                }

                const response = await originalFetch.call(this, resource, options);

                // Handle 401 Unauthorized for API requests
                if (response.status === 401) {
                    const urlStr = typeof resource === 'string' ? resource : resource.url || '';
                    if (urlStr.includes('/api/') && !urlStr.includes('/api/auth/login') && !urlStr.includes('/api/auth/me')) {
                        self.currentUser = null;
                        self.updateNavbarProfile();
                        self.openLoginModal('انتهت الجلسة. يرجى تسجيل الدخول مجدداً • Session expired. Please log in.');
                    }
                }

                // Handle 403 Forbidden (RBAC Delete Guards)
                if (response.status === 403) {
                    const urlStr = typeof resource === 'string' ? resource : resource.url || '';
                    if (urlStr.includes('/api/')) {
                        if (typeof window.showToast === 'function') {
                            window.showToast('عذراً: ليس لديك صلاحية حذف الوثائق أو العناصر (قراءة ورفع فقط) • Deletion is restricted for Contributor accounts.', 'error');
                        }
                    }
                }

                return response;
            };
        }

        bindDomEvents() {
            // Login Form submission
            const form = document.getElementById('login-form');
            if (form) {
                form.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const usernameInput = document.getElementById('login-username');
                    const passwordInput = document.getElementById('login-password');
                    const username = usernameInput ? usernameInput.value.trim() : '';
                    const password = passwordInput ? passwordInput.value : '';

                    if (!username) {
                        this.showLoginError('يرجى إدخال اسم المستخدم • Please enter username');
                        return;
                    }

                    await this.login(username, password);
                });
            }

            // Password Toggle Visibility Button
            const togglePasswordBtn = document.getElementById('btn-toggle-password');
            if (togglePasswordBtn) {
                togglePasswordBtn.addEventListener('click', () => {
                    const passwordInput = document.getElementById('login-password');
                    if (!passwordInput) return;
                    const isPassword = passwordInput.type === 'password';
                    passwordInput.type = isPassword ? 'text' : 'password';
                    const icon = togglePasswordBtn.querySelector('svg');
                    if (icon) {
                        icon.innerHTML = isPassword
                            ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18"/>'
                            : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>';
                    }
                });
            }

            // Top Navbar Profile Button & Dropdown
            const profileBtn = document.getElementById('user-profile-btn');
            const profileDropdown = document.getElementById('user-profile-dropdown');
            if (profileBtn && profileDropdown) {
                profileBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const isExpanded = profileBtn.getAttribute('aria-expanded') === 'true';
                    this.toggleProfileDropdown(!isExpanded);
                });

                document.addEventListener('click', (e) => {
                    if (!profileDropdown.contains(e.target) && !profileBtn.contains(e.target)) {
                        this.toggleProfileDropdown(false);
                    }
                });
            }

            // Logout Button
            const logoutBtn = document.getElementById('btn-logout');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', async () => {
                    this.toggleProfileDropdown(false);
                    await this.logout();
                });
            }

            // Switch User Button in Profile Dropdown
            const switchUserBtn = document.getElementById('btn-switch-user');
            if (switchUserBtn) {
                switchUserBtn.addEventListener('click', () => {
                    this.toggleProfileDropdown(false);
                    this.openLoginModal();
                });
            }

            // Close login modal button
            const closeLoginBtn = document.getElementById('btn-close-login');
            if (closeLoginBtn) {
                closeLoginBtn.addEventListener('click', () => {
                    this.closeLoginModal();
                });
            }
        }

        async loadUsers() {
            try {
                const res = await fetch('/api/auth/users');
                if (res.ok) {
                    const data = await res.json();
                    if (Array.isArray(data) && data.length > 0) {
                        this.users = data;
                    } else {
                        this.users = [...this.fallbackUsers];
                    }
                } else {
                    this.users = [...this.fallbackUsers];
                }
            } catch (err) {
                this.users = [...this.fallbackUsers];
            }
            this.renderUserChips();
        }

        renderUserChips() {
            const container = document.getElementById('login-presets-container');
            if (!container) return;

            const admins = this.users.filter(u => u.role === 'Admin');
            const contributors = this.users.filter(u => u.role === 'Contributor');

            let html = `
                <div class="space-y-3">
                    <div>
                        <div class="flex items-center justify-between mb-1.5 px-0.5">
                            <span class="text-[11px] font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                                <span>مدراء النظام (صلاحيات كاملة • Full Access)</span>
                            </span>
                            <span class="text-[10px] text-slate-400">قراءة + رفع + حذف</span>
                        </div>
                        <div class="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
                            ${admins.map(u => `
                                <button type="button" data-username="${escapeHtml(u.username)}" class="btn-user-chip flex items-center gap-2 p-2 rounded-xl border border-emerald-200 dark:border-emerald-800/60 bg-emerald-50/50 dark:bg-emerald-950/30 hover:bg-emerald-100/70 dark:hover:bg-emerald-900/50 text-slate-800 dark:text-slate-100 transition-all text-xs font-semibold cursor-pointer text-right group">
                                    <div class="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold text-[11px] flex-shrink-0 group-hover:scale-105 transition-transform">
                                        ${escapeHtml(u.displayName.charAt(0).toUpperCase())}
                                    </div>
                                    <span class="truncate">${escapeHtml(u.displayName)}</span>
                                </button>
                            `).join('')}
                        </div>
                    </div>

                    <div>
                        <div class="flex items-center justify-between mb-1.5 px-0.5">
                            <span class="text-[11px] font-bold text-blue-600 dark:text-blue-400 flex items-center gap-1">
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
                                <span>الموظفون (قراءة ورفع فقط • Read &amp; Upload)</span>
                            </span>
                            <span class="text-[10px] text-slate-400">الحذف محجوب</span>
                        </div>
                        <div class="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                            ${contributors.map(u => `
                                <button type="button" data-username="${escapeHtml(u.username)}" class="btn-user-chip flex items-center gap-2 p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-blue-50/70 dark:hover:bg-blue-950/40 hover:border-blue-300 dark:hover:border-blue-700 text-slate-800 dark:text-slate-100 transition-all text-xs font-semibold cursor-pointer text-right group">
                                    <div class="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-[11px] flex-shrink-0 group-hover:scale-105 transition-transform">
                                        ${escapeHtml(u.displayName.charAt(0).toUpperCase())}
                                    </div>
                                    <span class="truncate">${escapeHtml(u.displayName)}</span>
                                </button>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;

            container.innerHTML = html;

            // Attach click handler to each chip
            container.querySelectorAll('.btn-user-chip').forEach(btn => {
                btn.addEventListener('click', () => {
                    const uname = btn.getAttribute('data-username');
                    if (uname) {
                        this.selectPresetUser(uname);
                    }
                });
            });
        }

        selectPresetUser(username) {
            const usernameInput = document.getElementById('login-username');
            const passwordInput = document.getElementById('login-password');
            if (usernameInput) {
                usernameInput.value = username;
            }
            if (passwordInput) {
                // Auto-fill demo password for frictionless operation
                passwordInput.value = 'password123';
            }
            this.clearLoginError();

            // Highlight selected chip
            document.querySelectorAll('.btn-user-chip').forEach(btn => {
                if (btn.getAttribute('data-username') === username) {
                    btn.classList.add('ring-2', 'ring-blue-500', 'border-blue-500');
                } else {
                    btn.classList.remove('ring-2', 'ring-blue-500', 'border-blue-500');
                }
            });
        }

        async checkSession() {
            try {
                const res = await fetch('/api/auth/me');
                if (res.ok) {
                    const data = await res.json();
                    if (data && data.authenticated && data.user) {
                        const rawRole = data.user.role || (data.user.can_delete ? 'Admin' : 'Contributor');
                        const isAdminRole = rawRole.toLowerCase() === 'admin';
                        const role = isAdminRole ? 'Admin' : 'Contributor';
                        this.currentUser = {
                            ...data.user,
                            displayName: data.user.displayName || data.user.display_name || data.user.username,
                            role: role,
                            canDelete: isAdminRole || Boolean(data.user.can_delete)
                        };
                        this.updateNavbarProfile();
                        this.closeLoginModal();
                        this.notifyStateChanged();
                        return;
                    }
                }
            } catch (err) {
                console.warn('[AuthManager] Failed to check session:', err);
            }

            // Unauthenticated state
            this.currentUser = null;
            this.updateNavbarProfile();
            this.notifyStateChanged();
        }

        async login(username, password) {
            this.clearLoginError();
            this.setLoading(true);

            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                const data = await res.json().catch(() => ({}));

                const isSuccess = res.ok && (data.success === true || data.status === 'success');
                if (!isSuccess) {
                    const errMessage = data.message || data.error || 'بيانات الدخول غير صحيحة • Invalid credentials';
                    this.showLoginError(errMessage);
                    return false;
                }

                const user = data.user || {};
                const rawRole = user.role || (user.can_delete ? 'Admin' : 'Contributor');
                const isAdminRole = rawRole.toLowerCase() === 'admin';
                const role = isAdminRole ? 'Admin' : 'Contributor';
                this.currentUser = {
                    ...user,
                    displayName: user.displayName || user.display_name || user.username || username,
                    role: role,
                    canDelete: isAdminRole || Boolean(user.can_delete)
                };

                this.updateNavbarProfile();
                this.closeLoginModal();
                this.notifyStateChanged();

                if (typeof window.showToast === 'function') {
                    const roleLabel = isAdminRole ? 'صلاحيات كاملة' : 'قراءة ورفع فقط';
                    window.showToast(`مرحباً ${this.currentUser.displayName} (${roleLabel})`, 'success');
                }

                return true;
            } catch (err) {
                console.error('[AuthManager] Login failed:', err);
                this.showLoginError('فشل الاتصال بالخادم • Network error occurred');
                return false;
            } finally {
                this.setLoading(false);
            }
        }

        async logout() {
            try {
                await fetch('/api/auth/logout', { method: 'POST' });
            } catch (err) {
                console.warn('[AuthManager] Logout request error:', err);
            }

            this.currentUser = null;
            this.updateNavbarProfile();
            this.openLoginModal('تم تسجيل الخروج بنجاح • Logged out successfully');
            this.notifyStateChanged();

            if (typeof window.showToast === 'function') {
                window.showToast('تم تسجيل الخروج • Logged out', 'success');
            }
        }

        setLoading(loading) {
            this.isLoading = loading;
            const submitBtn = document.getElementById('btn-login-submit');
            if (submitBtn) {
                submitBtn.disabled = loading;
                const spinner = submitBtn.querySelector('.login-spinner');
                const btnText = submitBtn.querySelector('.login-btn-text');
                if (spinner) spinner.classList.toggle('hidden', !loading);
                if (btnText) btnText.textContent = loading ? 'جاري التحقق...' : 'تسجيل الدخول • Sign In';
            }
        }

        showLoginError(msg) {
            const errorContainer = document.getElementById('login-error');
            if (errorContainer) {
                errorContainer.classList.remove('hidden');
                const textElem = errorContainer.querySelector('.error-text');
                if (textElem) textElem.textContent = msg;
                else errorContainer.textContent = msg;
            }
        }

        clearLoginError() {
            const errorContainer = document.getElementById('login-error');
            if (errorContainer) {
                errorContainer.classList.add('hidden');
            }
        }

        openLoginModal(notice = null) {
            const modal = document.getElementById('login-screen');
            if (!modal) return;

            modal.classList.remove('hidden');
            modal.setAttribute('aria-hidden', 'false');

            const closeBtn = document.getElementById('btn-close-login');
            if (closeBtn) {
                closeBtn.classList.remove('hidden');
            }

            if (notice) {
                this.showLoginError(notice);
            } else {
                this.clearLoginError();
            }

            // Auto-focus username input
            setTimeout(() => {
                const usernameInput = document.getElementById('login-username');
                if (usernameInput) usernameInput.focus();
            }, 100);
        }

        closeLoginModal() {
            const modal = document.getElementById('login-screen');
            if (!modal) return;
            modal.classList.add('hidden');
            modal.setAttribute('aria-hidden', 'true');
        }

        toggleProfileDropdown(show) {
            const dropdown = document.getElementById('user-profile-dropdown');
            const profileBtn = document.getElementById('user-profile-btn');
            if (!dropdown || !profileBtn) return;

            if (show) {
                dropdown.classList.remove('hidden');
                profileBtn.setAttribute('aria-expanded', 'true');
            } else {
                dropdown.classList.add('hidden');
                profileBtn.setAttribute('aria-expanded', 'false');
            }
        }

        updateNavbarProfile() {
            const avatarBadge = document.getElementById('user-avatar-badge');
            const nameElem = document.getElementById('user-display-name');
            const roleBadge = document.getElementById('user-role-badge');
            const dropdownAvatar = document.getElementById('dropdown-avatar-badge');
            const dropdownName = document.getElementById('dropdown-user-name');
            const dropdownRoleBadge = document.getElementById('dropdown-role-badge');
            const dropdownRoleDesc = document.getElementById('dropdown-role-desc');

            if (!this.currentUser) {
                if (avatarBadge) {
                    avatarBadge.textContent = '?';
                    avatarBadge.className = 'w-6 h-6 rounded-full bg-slate-500 text-white font-bold text-[11px] flex items-center justify-center shadow-xs';
                }
                if (nameElem) nameElem.textContent = 'غير مسجل';
                if (roleBadge) {
                    roleBadge.textContent = 'تسجيل الدخول';
                    roleBadge.className = 'text-[9px] font-semibold text-slate-500 leading-tight';
                }
                return;
            }

            const isAdmin = this.currentUser.role === 'Admin';
            const initial = (this.currentUser.displayName || this.currentUser.username || 'U').charAt(0).toUpperCase();

            // Top navbar button updates
            if (avatarBadge) {
                avatarBadge.textContent = initial;
                avatarBadge.className = `w-6 h-6 rounded-full ${isAdmin ? 'bg-emerald-600' : 'bg-blue-600'} text-white font-bold text-[11px] flex items-center justify-center shadow-xs flex-shrink-0`;
            }

            if (nameElem) {
                nameElem.textContent = this.currentUser.displayName || this.currentUser.username;
            }

            if (roleBadge) {
                if (isAdmin) {
                    roleBadge.textContent = 'صلاحيات كاملة • Full Access';
                    roleBadge.className = 'text-[9px] font-semibold text-emerald-600 dark:text-emerald-400 leading-tight truncate';
                } else {
                    roleBadge.textContent = 'قراءة ورفع فقط • Read & Upload';
                    roleBadge.className = 'text-[9px] font-semibold text-blue-600 dark:text-blue-400 leading-tight truncate';
                }
            }

            // Profile Dropdown updates
            if (dropdownAvatar) {
                dropdownAvatar.textContent = initial;
                dropdownAvatar.className = `w-10 h-10 rounded-xl ${isAdmin ? 'bg-emerald-600' : 'bg-blue-600'} text-white font-bold text-base flex items-center justify-center shadow-sm flex-shrink-0`;
            }
            if (dropdownName) {
                dropdownName.textContent = this.currentUser.displayName || this.currentUser.username;
            }
            if (dropdownRoleBadge) {
                if (isAdmin) {
                    dropdownRoleBadge.textContent = 'مدير نظام • Admin';
                    dropdownRoleBadge.className = 'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800';
                } else {
                    dropdownRoleBadge.textContent = 'موظف • Contributor';
                    dropdownRoleBadge.className = 'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-950/80 dark:text-blue-300 border border-blue-200 dark:border-blue-800';
                }
            }
            if (dropdownRoleDesc) {
                if (isAdmin) {
                    dropdownRoleDesc.textContent = 'صلاحيات كاملة: قراءة، رفع، تعديل وحذف كافة الوثائق والمنازل.';
                } else {
                    dropdownRoleDesc.textContent = 'صلاحيات محدودة: قراءة واستعراض ورفع الوثائق. خاصية الحذف محجوبة بالكامل.';
                }
            }
        }

        notifyStateChanged() {
            const event = new CustomEvent('auth:user-changed', {
                detail: {
                    user: this.currentUser,
                    canDelete: this.hasDeletePermission(),
                    isAdmin: this.isAdmin(),
                    isContributor: this.isContributor()
                }
            });
            window.dispatchEvent(event);

            for (const fn of this._listeners) {
                try { fn(this.currentUser); } catch (e) { console.error(e); }
            }
        }

        onStateChanged(fn) {
            if (typeof fn === 'function') {
                this._listeners.push(fn);
            }
        }

        hasDeletePermission() {
            if (!this.currentUser) return false;
            const role = (this.currentUser.role || '').toLowerCase();
            if (role === 'contributor') return false;
            if (this.currentUser.canDelete === false || this.currentUser.can_delete === false) return false;
            return true;
        }

        isAdmin() {
            if (!this.currentUser) return true;
            const role = (this.currentUser.role || '').toLowerCase();
            return role === 'admin';
        }

        isContributor() {
            if (!this.currentUser) return false;
            const role = (this.currentUser.role || '').toLowerCase();
            return role === 'contributor';
        }

        getUser() {
            return this.currentUser;
        }
    }

    // Attach singleton to window
    window.authManager = new AuthManager();

    // Auto-init on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => window.authManager.init());
    } else {
        window.authManager.init();
    }
})();
