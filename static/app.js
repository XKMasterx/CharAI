/**
 * CharAI Local - Frontend Engine
 * Character.ai clone with full streaming, swipes, web-search, NSFW settings, Image Uploads, and Multi-user Account Isolation.
 */

// Automatically attach Authorization header to all internal /api/ calls
const _originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
  if (typeof url === 'string' && url.startsWith('/api/')) {
    options = options || {};
    const token = localStorage.getItem('charai_token');
    if (token) {
      if (!options.headers) {
        options.headers = {};
      }
      if (options.headers instanceof Headers) {
        if (!options.headers.has('Authorization')) {
          options.headers.set('Authorization', 'Bearer ' + token);
        }
      } else if (Array.isArray(options.headers)) {
        options.headers.push(['Authorization', 'Bearer ' + token]);
      } else {
        if (!options.headers['Authorization']) {
          options.headers['Authorization'] = 'Bearer ' + token;
        }
      }
    }
  }
  return _originalFetch.call(this, url, options);
};

// Application State
const state = {
  characters: [],
  activeCharacter: null,
  chats: [],
  activeChat: null,
  messages: [],
  settings: {},
  isStreaming: false,
  ttsEnabled: false,
  pendingChatImageUrl: '',
  user: null
};

// DOM Elements
const DOM = {
  sidebar: document.getElementById('sidebar'),
  sidebarBackdrop: document.getElementById('sidebar-backdrop'),
  btnToggleSidebar: document.getElementById('btn-toggle-sidebar'),
  btnShowSidebar: document.getElementById('btn-show-sidebar'),
  characterList: document.getElementById('character-list'),
  characterSearch: document.getElementById('character-search'),
  sidebarNsfwIndicator: document.getElementById('sidebar-nsfw-indicator'),
  btnCreateChar: document.getElementById('btn-create-char'),
  btnImportChar: document.getElementById('btn-import-char'),
  fileImportInput: document.getElementById('file-import-input'),

  // Header
  headerCharInfo: document.getElementById('header-char-info'),
  headerCharAvatar: document.getElementById('header-char-avatar'),
  headerCharName: document.getElementById('header-char-name'),
  headerCharTagline: document.getElementById('header-char-tagline'),
  headerCharNsfwBadge: document.getElementById('header-char-nsfw-badge'),
  currentChatTitle: document.getElementById('current-chat-title'),
  btnSessionsDropdown: document.getElementById('btn-sessions-dropdown'),
  sessionsDropdownMenu: document.getElementById('sessions-dropdown-menu'),
  btnNewChatDropdown: document.getElementById('btn-new-chat-dropdown'),
  newChatDropdownMenu: document.getElementById('new-chat-dropdown-menu'),
  btnCreateChatWithGreeting: document.getElementById('btn-create-chat-with-greeting'),
  btnCreateChatEmpty: document.getElementById('btn-create-chat-empty'),
  btnCharDetails: document.getElementById('btn-char-details'),
  btnSoundToggle: document.getElementById('btn-sound-toggle'),
  btnLanguageDropdown: document.getElementById('btn-language-dropdown'),
  languageDropdownMenu: document.getElementById('language-dropdown-menu'),

  // Chat Feed & Input
  messagesFeed: document.getElementById('messages-feed'),
  typingIndicator: document.getElementById('typing-indicator'),
  typingStatusText: document.getElementById('typing-status-text'),
  startersBar: document.getElementById('starters-bar'),
  chatTextarea: document.getElementById('chat-textarea'),
  charCounter: document.getElementById('char-counter'),
  btnSkipContinue: document.getElementById('btn-skip-continue'),
  btnSendMessage: document.getElementById('btn-send-message'),

  // Chat Image Attachments
  btnAttachImage: document.getElementById('btn-attach-image'),
  chatFileInput: document.getElementById('chat-file-input'),
  chatAttachmentBar: document.getElementById('chat-attachment-bar'),
  attachmentPreviewImg: document.getElementById('attachment-preview-img'),
  attachmentFilename: document.getElementById('attachment-filename'),
  btnRemoveAttachment: document.getElementById('btn-remove-attachment'),

  // User Profile, Settings & Auth
  sidebarUserName: document.getElementById('sidebar-user-name'),
  sidebarProviderStatus: document.getElementById('sidebar-provider-status'),
  btnOpenSettings: document.getElementById('btn-open-settings'),
  userProfileBtn: document.getElementById('user-profile-btn'),
  userAvatarBadge: document.getElementById('user-avatar-badge'),
  btnAuthToggle: document.getElementById('btn-auth-toggle'),

  // Web Search in Character Modal
  searchProfileInput: document.getElementById('search-profile-input'),
  btnSearchProfile: document.getElementById('btn-search-profile'),
  searchProfileStatus: document.getElementById('search-profile-status'),

  // Avatar Upload in Character Modal
  avatarDropzone: document.getElementById('avatar-dropzone'),
  btnUploadAvatar: document.getElementById('btn-upload-avatar'),
  charAvatarFileInput: document.getElementById('char-avatar-file-input'),

  // Modals
  modalCharacter: document.getElementById('modal-character'),
  formCharacter: document.getElementById('form-character'),
  modalCharTitle: document.getElementById('modal-char-title'),
  charFormId: document.getElementById('char-form-id'),
  charName: document.getElementById('char-name'),
  charTitle: document.getElementById('char-title'),
  charTagline: document.getElementById('char-tagline'),
  charGreeting: document.getElementById('char-greeting'),
  charPersona: document.getElementById('char-persona'),
  charAvatarUrl: document.getElementById('char-avatar-url'),
  charAvatarPreview: document.getElementById('char-avatar-preview'),
  charIsNsfw: document.getElementById('char-is-nsfw'),
  presetAvatarsList: document.getElementById('preset-avatars-list'),

  modalSettings: document.getElementById('modal-settings'),
  formSettings: document.getElementById('form-settings'),
  settingsGeminiFields: document.getElementById('settings-gemini-fields'),
  settingsOllamaFields: document.getElementById('settings-ollama-fields'),
  settingsOpenaiFields: document.getElementById('settings-openai-fields'),
  setGeminiKey: document.getElementById('set-gemini-key'),
  setGeminiModel: document.getElementById('set-gemini-model'),
  setOllamaUrl: document.getElementById('set-ollama-url'),
  setOllamaModel: document.getElementById('set-ollama-model'),
  setOpenaiUrl: document.getElementById('set-openai-url'),
  setOpenaiKey: document.getElementById('set-openai-key'),
  setOpenaiModel: document.getElementById('set-openai-model'),
  setNsfwMode: document.getElementById('set-nsfw-mode'),
  setRoleplayTone: document.getElementById('set-roleplay-tone'),
  setLanguage: document.getElementById('set-language'),
  setUserName: document.getElementById('set-user-name'),
  setUserPersona: document.getElementById('set-user-persona'),

  modalCharView: document.getElementById('modal-char-view'),
  viewCharTitle: document.getElementById('view-char-title'),
  viewCharBody: document.getElementById('view-char-body'),
  viewCharFooter: document.getElementById('view-char-footer'),

  modalLightbox: document.getElementById('modal-lightbox'),
  lightboxImg: document.getElementById('lightbox-img'),
  btnCloseLightbox: document.getElementById('btn-close-lightbox'),

  // Auth & Account Modals
  modalAuth: document.getElementById('modal-auth'),
  modalUserAccount: document.getElementById('modal-user-account'),
  tabBtnLogin: document.getElementById('tab-btn-login'),
  tabBtnRegister: document.getElementById('tab-btn-register'),
  formAuthLogin: document.getElementById('form-auth-login'),
  formAuthRegister: document.getElementById('form-auth-register'),
  authErrorMsg: document.getElementById('auth-error-msg'),
  btnContinueAsGuest: document.getElementById('btn-continue-as-guest'),
  formUpdateProfile: document.getElementById('form-update-profile'),
  btnAccountLogout: document.getElementById('btn-account-logout'),
  accountDisplayName: document.getElementById('account-display-name'),
  accountUsername: document.getElementById('account-username'),
  accountAvatarPreview: document.getElementById('account-avatar-preview'),
  accountAvatarImg: document.getElementById('account-avatar-img'),
  btnTriggerUserAvatarUpload: document.getElementById('btn-trigger-user-avatar-upload'),
  btnUserAvatarFileBtn: document.getElementById('btn-user-avatar-file-btn'),
  userAvatarFileInput: document.getElementById('user-avatar-file-input'),
  profileInputAvatar: document.getElementById('profile-input-avatar'),
  userAvatarPresetsList: document.getElementById('user-avatar-presets-list'),
  profileInputDisplay: document.getElementById('profile-input-display'),
  profileInputPassword: document.getElementById('profile-input-password'),
  profileSaveMsg: document.getElementById('profile-save-msg')
};

// Initialize Application
async function init() {
  setupEventListeners();
  const user = await checkAuthSession();
  await loadSettings();
  await loadCharacters();
  // Prompt account login/register on first visit if not yet signed in or chosen guest
  if (!user && !localStorage.getItem('guest_mode_dismissed')) {
    openAuthModal();
  }
}

// -------------------------------------------------------------
// Settings Management
// -------------------------------------------------------------
const DEFAULT_GROQ_KEY = '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';

async function loadSettings() {
  try {
    const res = await fetch('/api/settings');
    const serverSettings = await res.json();
    
    // Check cached settings in localStorage (survives Render cold restarts)
    let cached = null;
    try {
      const raw = localStorage.getItem('charai_cached_settings');
      if (raw) cached = JSON.parse(raw);
    } catch (_) {}

    const isStale = (k) => !k || k.startsWith('gsk_Pr6N') || k.startsWith('gsk_GKPH') || k.startsWith('gsk_1twr') || k.length < 20;

    if (cached && isStale(cached.openai_api_key)) {
      cached.openai_api_key = DEFAULT_GROQ_KEY;
      cached.provider = 'openai';
      cached.openai_base_url = 'https://api.groq.com/openai/v1';
      cached.openai_model = 'qwen/qwen3.8-27b';
      try { localStorage.setItem('charai_cached_settings', JSON.stringify(cached)); } catch (_) {}
    }

    if (isStale(serverSettings.openai_api_key)) {
      serverSettings.openai_api_key = DEFAULT_GROQ_KEY;
      serverSettings.provider = 'openai';
      serverSettings.openai_base_url = 'https://api.groq.com/openai/v1';
      serverSettings.openai_model = 'qwen/qwen3.8-27b';
      fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings: serverSettings })
      }).catch(() => {});
    }

    state.settings = serverSettings;
    try {
      localStorage.setItem('charai_cached_settings', JSON.stringify(state.settings));
    } catch (_) {}

    updateUIWithSettings();
  } catch (err) {
    console.error('Fehler beim Laden der Einstellungen:', err);
    try {
      const raw = localStorage.getItem('charai_cached_settings');
      if (raw) {
        state.settings = JSON.parse(raw);
        updateUIWithSettings();
      }
    } catch (_) {}
  }
}

function updateUIWithSettings() {
  const lang = state.settings.language || 'auto';
  if (typeof applyI18nToDOM === 'function') {
    applyI18nToDOM(lang);
  }

  const userName = state.settings.user_name || 'Reisender';
  DOM.sidebarUserName.textContent = userName;

  DOM.sidebarProviderStatus.textContent = '⚡ Groq (Aktiv)';
  DOM.sidebarProviderStatus.style.color = '#f97316';

  const isGlobalNsfw = ['true', true, '1'].includes(state.settings.nsfw_mode);
  if (DOM.sidebarNsfwIndicator) {
    DOM.sidebarNsfwIndicator.style.display = isGlobalNsfw ? 'inline-block' : 'none';
  }

  const prov = state.settings.provider || 'openai';
  const radios = document.getElementsByName('provider');
  for (const r of radios) {
    if (r.value === prov) r.checked = true;
  }
  handleProviderFieldsVisibility(prov);

  if (DOM.setGeminiKey) DOM.setGeminiKey.value = state.settings.gemini_api_key || '';
  if (DOM.setGeminiModel) DOM.setGeminiModel.value = state.settings.gemini_model || 'gemini-1.5-flash';
  if (DOM.setOllamaUrl) DOM.setOllamaUrl.value = state.settings.ollama_base_url || 'http://localhost:11434';
  if (DOM.setOllamaModel) DOM.setOllamaModel.value = state.settings.ollama_model || 'llama3.2';
  if (DOM.setOpenaiUrl) DOM.setOpenaiUrl.value = state.settings.openai_base_url || 'https://api.groq.com/openai/v1';
  if (DOM.setOpenaiKey) DOM.setOpenaiKey.value = state.settings.openai_api_key || '';
  if (DOM.setOpenaiModel) DOM.setOpenaiModel.value = state.settings.openai_model || 'qwen/qwen3.8-27b';

  DOM.setNsfwMode.checked = ['true', true, '1'].includes(state.settings.nsfw_mode);
  DOM.setRoleplayTone.value = state.settings.roleplay_tone || 'standard';

  if (DOM.setLanguage) {
    DOM.setLanguage.value = lang;
  }
  const langLabels = {
    auto: 'Automatisch',
    de: 'Deutsch',
    en: 'English',
    es: 'Español',
    fr: 'Français',
    it: 'Italiano',
    ja: '日本語',
    ru: 'Русский',
    zh: '中文',
    pt: 'Português',
    tr: 'Türkçe',
    pl: 'Polski',
    nl: 'Nederlands',
    ar: 'العربية',
    ko: '한국어'
  };
  if (DOM.btnLanguageDropdown) {
    DOM.btnLanguageDropdown.title = `Sprache: ${langLabels[lang] || lang}`;
  }
  if (DOM.languageDropdownMenu) {
    DOM.languageDropdownMenu.querySelectorAll('.dropdown-item').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === lang);
    });
  }

  DOM.setUserName.value = state.settings.user_name || '';
  DOM.setUserPersona.value = state.settings.user_persona || '';
}

function handleProviderFieldsVisibility(provider) {
  if (DOM.settingsGeminiFields) DOM.settingsGeminiFields.style.display = 'none';
  if (DOM.settingsOllamaFields) DOM.settingsOllamaFields.style.display = 'none';
  if (DOM.settingsOpenaiFields) DOM.settingsOpenaiFields.style.display = 'none';
}

// -------------------------------------------------------------
// Authentication & Account Management
// -------------------------------------------------------------
async function checkAuthSession() {
  const token = localStorage.getItem('charai_token');
  if (!token) {
    updateUserUI(null);
    return null;
  }
  try {
    const res = await fetch('/api/auth/me');
    if (res.ok) {
      const data = await res.json();
      state.user = data.user;
      updateUserUI(data.user);
      return data.user;
    }
  } catch (err) {
    console.error('Auth session check failed:', err);
  }
  updateUserUI(null);
  return null;
}

function updateUserUI(user) {
  if (user) {
    const name = user.display_name || user.username;
    const avatar = user.avatar || '/static/avatars/default.svg';
    DOM.sidebarUserName.textContent = name;
    if (DOM.accountDisplayName) DOM.accountDisplayName.textContent = name;
    if (DOM.accountUsername) DOM.accountUsername.textContent = '@' + user.username;
    if (DOM.accountAvatarImg) DOM.accountAvatarImg.src = avatar;
    if (DOM.profileInputAvatar) DOM.profileInputAvatar.value = avatar;

    document.querySelectorAll('.user-preset-avatar').forEach(el => {
      if (el.dataset.path === avatar) {
        el.classList.add('selected');
      } else {
        el.classList.remove('selected');
      }
    });

    if (DOM.userAvatarBadge) {
      if (avatar && avatar !== '/static/avatars/default.svg') {
        DOM.userAvatarBadge.innerHTML = `<img src="${avatar}" class="user-avatar-img-sidebar" alt="Avatar">`;
      } else {
        DOM.userAvatarBadge.textContent = name.charAt(0).toUpperCase();
      }
    }
    if (DOM.profileInputDisplay) DOM.profileInputDisplay.value = user.display_name || '';
    if (DOM.btnAuthToggle) {
      DOM.btnAuthToggle.title = `Angemeldet als ${user.username} (Konto verwalten)`;
      DOM.btnAuthToggle.style.color = '#a855f7';
    }
  } else {
    DOM.sidebarUserName.textContent = 'Gast';
    if (DOM.userAvatarBadge) DOM.userAvatarBadge.textContent = '👤';
    if (DOM.accountAvatarImg) DOM.accountAvatarImg.src = '/static/avatars/default.svg';
    if (DOM.profileInputAvatar) DOM.profileInputAvatar.value = '/static/avatars/default.svg';
    if (DOM.btnAuthToggle) {
      DOM.btnAuthToggle.title = 'Anmelden / Konto erstellen';
      DOM.btnAuthToggle.style.color = '';
    }
  }
}

function openAuthModal(defaultTab = 'login') {
  hideAuthError();
  switchAuthTab(defaultTab);
  if (DOM.modalAuth) DOM.modalAuth.style.display = 'flex';
}

function switchAuthTab(tab) {
  hideAuthError();
  if (tab === 'login') {
    if (DOM.tabBtnLogin) DOM.tabBtnLogin.classList.add('active');
    if (DOM.tabBtnRegister) DOM.tabBtnRegister.classList.remove('active');
    if (DOM.formAuthLogin) DOM.formAuthLogin.style.display = 'block';
    if (DOM.formAuthRegister) DOM.formAuthRegister.style.display = 'none';
  } else {
    if (DOM.tabBtnRegister) DOM.tabBtnRegister.classList.add('active');
    if (DOM.tabBtnLogin) DOM.tabBtnLogin.classList.remove('active');
    if (DOM.formAuthRegister) DOM.formAuthRegister.style.display = 'block';
    if (DOM.formAuthLogin) DOM.formAuthLogin.style.display = 'none';
  }
}

function showAuthError(msg) {
  if (DOM.authErrorMsg) {
    DOM.authErrorMsg.textContent = msg;
    DOM.authErrorMsg.className = 'auth-alert error';
    DOM.authErrorMsg.style.display = 'block';
  }
}

function hideAuthError() {
  if (DOM.authErrorMsg) {
    DOM.authErrorMsg.style.display = 'none';
  }
}

async function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById('auth-login-username').value.trim();
  const password = document.getElementById('auth-login-password').value;
  hideAuthError();

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) {
      showAuthError(data.detail || 'Anmeldung fehlgeschlagen.');
      return;
    }
    localStorage.setItem('charai_token', data.token);
    state.user = data.user;
    updateUserUI(data.user);
    if (DOM.modalAuth) DOM.modalAuth.style.display = 'none';
    
    // Reload data for this user
    await loadSettings();
    await loadCharacters();
  } catch (err) {
    showAuthError('Netzwerkfehler: ' + err.message);
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const username = document.getElementById('auth-reg-username').value.trim();
  const display_name = document.getElementById('auth-reg-display').value.trim();
  const password = document.getElementById('auth-reg-password').value;
  const confirm = document.getElementById('auth-reg-confirm').value;
  hideAuthError();

  if (password !== confirm) {
    showAuthError('Die Passwörter stimmen nicht überein.');
    return;
  }

  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, display_name })
    });
    const data = await res.json();
    if (!res.ok) {
      showAuthError(data.detail || 'Registrierung fehlgeschlagen.');
      return;
    }
    localStorage.setItem('charai_token', data.token);
    state.user = data.user;
    updateUserUI(data.user);
    if (DOM.modalAuth) DOM.modalAuth.style.display = 'none';
    
    // Reload data for this user
    await loadSettings();
    await loadCharacters();
  } catch (err) {
    showAuthError('Netzwerkfehler: ' + err.message);
  }
}

async function handleLogout() {
  try {
    await fetch('/api/auth/logout', { method: 'POST' });
  } catch (err) {
    console.error('Logout error:', err);
  }
  localStorage.removeItem('charai_token');
  state.user = null;
  updateUserUI(null);
  if (DOM.modalUserAccount) DOM.modalUserAccount.style.display = 'none';
  
  // Reload clean guest data
  await loadSettings();
  await loadCharacters();
  openAuthModal('login');
}

async function handleUpdateProfile(e) {
  e.preventDefault();
  if (!state.user) return;
  const display_name = DOM.profileInputDisplay.value.trim();
  const new_password = DOM.profileInputPassword.value;
  const avatar = DOM.profileInputAvatar ? DOM.profileInputAvatar.value : undefined;

  try {
    const body = { display_name };
    if (avatar) body.avatar = avatar;
    if (new_password) body.new_password = new_password;

    const res = await fetch('/api/auth/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (res.ok) {
      state.user = data.user;
      updateUserUI(data.user);
      if (DOM.profileSaveMsg) {
        DOM.profileSaveMsg.textContent = 'Profil erfolgreich aktualisiert!';
        DOM.profileSaveMsg.style.display = 'block';
        setTimeout(() => { DOM.profileSaveMsg.style.display = 'none'; }, 3000);
      }
      DOM.profileInputPassword.value = '';
      if (state.activeChat) {
        await loadMessages(state.activeChat.id);
      }
    } else {
      alert(data.detail || 'Fehler beim Speichern');
    }
  } catch (err) {
    alert('Fehler: ' + err.message);
  }
}

// -------------------------------------------------------------
// Character Management
// -------------------------------------------------------------
async function loadCharacters() {
  try {
    const res = await fetch('/api/characters');
    state.characters = await res.json();
    renderCharacterList(state.characters);

    if (state.characters.length > 0) {
      const savedCharId = localStorage.getItem('last_active_char_id');
      const found = state.characters.find(c => c.id === savedCharId);
      selectCharacter(found || state.characters[0]);
    } else {
      state.activeCharacter = null;
      state.activeChat = null;
      state.chats = [];
      state.messages = [];
      localStorage.removeItem('last_active_char_id');
      DOM.headerCharName.textContent = 'Kein Charakter';
      DOM.headerCharTagline.textContent = 'Erstelle einen neuen Charakter, um zu starten.';
      DOM.headerCharAvatar.src = '/static/avatars/default.svg';
      DOM.headerCharNsfwBadge.style.display = 'none';
      DOM.currentChatTitle.textContent = 'Kein Chat';
      DOM.sessionsDropdownMenu.innerHTML = '';
      DOM.messagesFeed.innerHTML = `
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center; padding:24px; color:var(--text-muted);">
          <div style="font-size:48px; margin-bottom:12px;">🎭</div>
          <h3 style="font-size:18px; color:var(--text-primary); margin-bottom:8px;">Keine Charaktere vorhanden</h3>
          <p style="font-size:14px; max-width:400px; margin-bottom:20px; line-height:1.5;">Alle Charaktere wurden gelöscht. Du kannst jederzeit oben links auf <strong>+ Neuer Charakter</strong> klicken oder per Wikipedia-Recherche neue Figuren generieren!</p>
          <button class="btn btn-primary" id="btn-empty-create-char">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 5v14M5 12h14"/></svg>
            <span>Neuen Charakter erstellen</span>
          </button>
        </div>
      `;
      const emptyBtn = document.getElementById('btn-empty-create-char');
      if (emptyBtn) {
        emptyBtn.addEventListener('click', () => openCharacterModal());
      }
      DOM.startersBar.innerHTML = '';
    }
  } catch (err) {
    console.error('Fehler beim Laden der Charaktere:', err);
  }
}

function renderCharacterList(characters) {
  DOM.characterList.innerHTML = '';
  if (!characters || characters.length === 0) {
    DOM.characterList.innerHTML = `
      <div style="padding:24px 14px; text-align:center; color:var(--text-muted); font-size:13px; line-height:1.5;">
        Keine Charaktere vorhanden.<br>
        <span style="font-size:11px; color:var(--text-secondary);">Klicke oben auf "+ Neuer Charakter".</span>
      </div>
    `;
    return;
  }
  characters.forEach(char => {
    const item = document.createElement('div');
    item.className = 'character-item';
    if (state.activeCharacter && state.activeCharacter.id === char.id) {
      item.classList.add('active');
    }

    const isNsfw = Boolean(char.is_nsfw);

    item.innerHTML = `
      <img src="${escapeHtml(char.avatar)}" class="char-item-avatar" alt="${escapeHtml(char.name)}" onerror="this.src='/static/avatars/default.svg'">
      <div class="char-item-info">
        <div class="char-item-name-row">
          <span class="char-item-name">${escapeHtml(char.name)}</span>
          ${isNsfw ? '<span class="badge-nsfw">18+</span>' : ''}
        </div>
        <div class="char-item-tagline">${escapeHtml(char.tagline || char.title || '')}</div>
      </div>
    `;

    item.addEventListener('click', () => {
      selectCharacter(char);
      if (window.innerWidth <= 768) {
        DOM.sidebar.classList.remove('open');
      }
    });

    DOM.characterList.appendChild(item);
  });
}

async function selectCharacter(char) {
  state.activeCharacter = char;
  localStorage.setItem('last_active_char_id', char.id);

  renderCharacterList(state.characters);

  DOM.headerCharName.textContent = char.name;
  DOM.headerCharTagline.textContent = char.tagline || char.title || '';
  DOM.headerCharAvatar.src = char.avatar;
  DOM.headerCharAvatar.onerror = () => { DOM.headerCharAvatar.src = '/static/avatars/default.svg'; };

  if (DOM.headerCharNsfwBadge) {
    DOM.headerCharNsfwBadge.style.display = char.is_nsfw ? 'inline-block' : 'none';
  }

  await loadChatsForCharacter(char.id);
  renderStarters();
}

// -------------------------------------------------------------
// Web Search / Auto-Profile Generation
// -------------------------------------------------------------
async function handleSearchProfile(query) {
  const q = (query || DOM.searchProfileInput.value).trim();
  if (!q) return;

  DOM.searchProfileStatus.style.display = 'block';
  DOM.searchProfileStatus.innerHTML = `⏳ Durchsuche Wikipedia &amp; Webquellen nach <strong>${escapeHtml(q)}</strong>...`;
  DOM.btnSearchProfile.disabled = true;

  try {
    const res = await fetch('/api/characters/search-profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: q })
    });

    if (!res.ok) throw new Error(`Serverfehler (${res.status})`);

    const data = await res.json();

    const fieldsToAnimate = [
      DOM.charName, DOM.charTitle, DOM.charTagline, DOM.charGreeting, DOM.charPersona
    ];

    DOM.charName.value = data.name || '';
    DOM.charTitle.value = data.title || '';
    DOM.charTagline.value = data.tagline || '';
    DOM.charGreeting.value = data.greeting || '';
    DOM.charPersona.value = data.persona || '';

    if (data.avatar) {
      DOM.charAvatarUrl.value = data.avatar;
      DOM.charAvatarPreview.src = data.avatar;
    }

    fieldsToAnimate.forEach(el => {
      el.classList.add('highlight-pulse');
      setTimeout(() => el.classList.remove('highlight-pulse'), 800);
    });

    DOM.searchProfileStatus.innerHTML = `✅ <strong>${escapeHtml(data.name)}</strong> erfolgreich recherchiert und Profil ausgefüllt!`;
  } catch (err) {
    DOM.searchProfileStatus.innerHTML = `❌ Fehler bei der Recherche: ${escapeHtml(err.message)}`;
  } finally {
    DOM.btnSearchProfile.disabled = false;
  }
}

// -------------------------------------------------------------
// Image Uploads (Avatar & Chat)
// -------------------------------------------------------------
async function uploadImageFile(file, category = 'chat') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);

  const res = await fetch('/api/upload/file', {
    method: 'POST',
    body: formData
  });

  if (!res.ok) throw new Error('Upload fehlgeschlagen');
  const data = await res.json();
  return data.url;
}

async function uploadBase64Image(base64Data, category = 'chat') {
  const res = await fetch('/api/upload', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: base64Data, category })
  });

  if (!res.ok) throw new Error('Base64 Upload fehlgeschlagen');
  const data = await res.json();
  return data.url;
}

function handleChatAttachment(url, displayName = 'Bild angehängt') {
  state.pendingChatImageUrl = url;
  DOM.attachmentPreviewImg.src = url;
  DOM.attachmentFilename.textContent = displayName;
  DOM.chatAttachmentBar.style.display = 'flex';
}

function removeChatAttachment() {
  state.pendingChatImageUrl = '';
  DOM.attachmentPreviewImg.src = '';
  DOM.chatAttachmentBar.style.display = 'none';
  DOM.chatFileInput.value = '';
}

function openLightbox(imgUrl) {
  DOM.lightboxImg.src = imgUrl;
  DOM.modalLightbox.style.display = 'flex';
}

// -------------------------------------------------------------
// Chat Sessions
// -------------------------------------------------------------
async function loadChatsForCharacter(charId) {
  try {
    const res = await fetch(`/api/characters/${charId}/chats`);
    state.chats = await res.json();

    if (state.chats.length === 0) {
      const activeRes = await fetch(`/api/characters/${charId}/active-chat`);
      state.activeChat = await activeRes.json();
      state.chats = [state.activeChat];
    } else {
      state.activeChat = state.chats[0];
    }

    renderSessionsMenu();
    await loadMessages(state.activeChat.id);
  } catch (err) {
    console.error('Fehler beim Laden der Chats:', err);
  }
}

function renderSessionsMenu() {
  if (!state.activeChat) return;
  DOM.currentChatTitle.textContent = state.activeChat.title || 'Chat';

  DOM.sessionsDropdownMenu.innerHTML = '';

  const lang = (state.settings && state.settings.language) || 'auto';
  const yourChatsTxt = typeof getTranslation === 'function' ? getTranslation('your_chats_header', lang) : 'Deine Chats';
  const headerTitle = document.createElement('div');
  headerTitle.className = 'dropdown-header-title';
  headerTitle.textContent = yourChatsTxt;
  DOM.sessionsDropdownMenu.appendChild(headerTitle);

  state.chats.forEach(chat => {
    const row = document.createElement('div');
    row.className = 'session-dropdown-row' + (chat.id === state.activeChat.id ? ' active' : '');

    const titleBtn = document.createElement('button');
    titleBtn.className = 'session-title-btn';
    titleBtn.innerHTML = `<span>💬</span> <span>${escapeHtml(chat.title)}</span>`;
    titleBtn.title = escapeHtml(chat.title);
    const selectChat = async (e) => {
      if (e) e.stopPropagation();
      DOM.sessionsDropdownMenu.classList.remove('show');
      state.activeChat = chat;
      DOM.currentChatTitle.textContent = chat.title;
      renderSessionsMenu();
      await loadMessages(chat.id);
    };
    titleBtn.addEventListener('click', selectChat);

    const delBtn = document.createElement('button');
    delBtn.className = 'session-delete-btn';
    delBtn.title = typeof getTranslation === 'function' ? getTranslation('btn_delete_char', lang) : 'Löschen';
    delBtn.setAttribute('aria-label', 'Chat löschen');
    delBtn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="3 6 5 6 21 6"/>
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
      </svg>
    `;
    const deleteThisChat = async (e) => {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      const confirmMsg = typeof getTranslation === 'function' 
        ? getTranslation('confirm_delete_chat', lang) 
        : `Möchtest du den Chat "${chat.title}" wirklich unwiderruflich löschen?`;
      if (!confirm(confirmMsg)) return;
      await handleDeleteChat(chat.id);
    };
    delBtn.addEventListener('click', deleteThisChat);
    delBtn.addEventListener('touchend', deleteThisChat);

    row.appendChild(titleBtn);
    row.appendChild(delBtn);
    DOM.sessionsDropdownMenu.appendChild(row);
  });

  // Action options inside session menu
  const divider = document.createElement('div');
  divider.className = 'dropdown-divider';
  DOM.sessionsDropdownMenu.appendChild(divider);

  const btnWithGreeting = document.createElement('button');
  btnWithGreeting.className = 'dropdown-item';
  const withGreetingTxt = typeof getTranslation === 'function' ? getTranslation('new_chat_with_greeting', lang) : '💬 Neuer Chat (Mit Anfangstext)';
  btnWithGreeting.innerHTML = `<span>${withGreetingTxt}</span>`;
  btnWithGreeting.addEventListener('click', () => {
    DOM.sessionsDropdownMenu.classList.remove('show');
    handleCreateNewChat(true);
  });
  DOM.sessionsDropdownMenu.appendChild(btnWithGreeting);

  const btnEmpty = document.createElement('button');
  btnEmpty.className = 'dropdown-item';
  const emptyTxt = typeof getTranslation === 'function' ? getTranslation('new_chat_empty', lang) : '✏️ Neuer Chat (Du beginnst)';
  btnEmpty.innerHTML = `<span>${emptyTxt}</span>`;
  btnEmpty.addEventListener('click', () => {
    DOM.sessionsDropdownMenu.classList.remove('show');
    handleCreateNewChat(false);
  });
  DOM.sessionsDropdownMenu.appendChild(btnEmpty);

  const btnExport = document.createElement('button');
  btnExport.className = 'dropdown-item';
  btnExport.innerHTML = `<span>📥 Chat als Backup exportieren</span>`;
  btnExport.addEventListener('click', () => {
    DOM.sessionsDropdownMenu.classList.remove('show');
    handleExportChat();
  });
  DOM.sessionsDropdownMenu.appendChild(btnExport);
}

function handleExportChat() {
  if (!state.messages || state.messages.length === 0) {
    alert('Dieser Chat hat noch keine Nachrichten zum Exportieren.');
    return;
  }
  const charName = state.activeCharacter ? state.activeCharacter.name : 'Charakter';
  const lines = [`=== Chat-Backup mit ${charName} ===\nDatum: ${new Date().toLocaleString()}\n`];
  state.messages.forEach(m => {
    const sender = m.role === 'user' ? 'Du' : charName;
    lines.push(`[${sender}]:\n${m.content}\n`);
  });
  const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `Chat_${charName.replace(/[^a-zA-Z0-9_-]/g, '_')}_Backup.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

async function handleDeleteChat(chatId) {
  try {
    const res = await fetch(`/api/chats/${chatId}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error('Löschen fehlgeschlagen');

    state.chats = state.chats.filter(c => c.id !== chatId);

    if (state.activeChat && state.activeChat.id === chatId) {
      if (state.chats.length > 0) {
        state.activeChat = state.chats[0];
        DOM.currentChatTitle.textContent = state.activeChat.title || 'Chat';
        renderSessionsMenu();
        await loadMessages(state.activeChat.id);
      } else {
        await handleCreateNewChat(false);
        return;
      }
    } else {
      renderSessionsMenu();
    }
  } catch (err) {
    console.error('Fehler beim Löschen des Chats:', err);
    alert('Fehler beim Löschen des Chats: ' + err.message);
  }
}

async function handleCreateNewChat(includeGreeting = true) {
  if (!state.activeCharacter) return;
  try {
    const res = await fetch(`/api/characters/${state.activeCharacter.id}/chats`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ include_greeting: includeGreeting })
    });
    const newChat = await res.json();
    state.chats.unshift(newChat);
    state.activeChat = newChat;
    renderSessionsMenu();
    await loadMessages(newChat.id);
    DOM.chatTextarea.focus();
  } catch (err) {
    console.error('Fehler beim Erstellen eines neuen Chats:', err);
  }
}

// -------------------------------------------------------------
// Messages & Feed
// -------------------------------------------------------------
function saveMessagesLocally(chatId, messages) {
  if (!chatId || !Array.isArray(messages)) return;
  try {
    const valid = messages.filter(m => !m.id || !String(m.id).startsWith('temp-'));
    localStorage.setItem(`charai_backup_msgs_${chatId}`, JSON.stringify(valid));
    if (state.activeCharacter) {
      localStorage.setItem(`charai_char_msgs_${state.activeCharacter.id}`, JSON.stringify({
        chatId: chatId,
        messages: valid,
        updatedAt: Date.now()
      }));
    }
  } catch (e) {
    console.warn('LocalStorage save error:', e);
  }
}

async function loadMessages(chatId) {
  try {
    const res = await fetch(`/api/chats/${chatId}/messages`);
    const serverMessages = await res.json();

    // Auto-Recovery from client storage (protects against Render ephemeral container wipes)
    let localBackup = null;
    try {
      const raw = localStorage.getItem(`charai_backup_msgs_${chatId}`);
      if (raw) localBackup = JSON.parse(raw);
    } catch (_) {}

    if ((!localBackup || localBackup.length <= 1) && state.activeCharacter) {
      try {
        const charRaw = localStorage.getItem(`charai_char_msgs_${state.activeCharacter.id}`);
        if (charRaw) {
          const parsed = JSON.parse(charRaw);
          if (parsed && Array.isArray(parsed.messages) && parsed.messages.length > (localBackup ? localBackup.length : 1)) {
            localBackup = parsed.messages;
          }
        }
      } catch (_) {}
    }

    // Only restore if the server has ZERO messages but local storage has a valid chat history!
    if (serverMessages.length === 0 && localBackup && Array.isArray(localBackup) && localBackup.length > 0) {
      console.log(`[CharAI Auto-Recovery] Restoring ${localBackup.length} messages from local storage after server container wipe...`);
      try {
        await fetch(`/api/chats/${chatId}/sync`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages: localBackup })
        });
        const reRes = await fetch(`/api/chats/${chatId}/messages`);
        state.messages = await reRes.json();
      } catch (syncErr) {
        console.warn('Sync call failed, using local messages as view fallback:', syncErr);
        state.messages = localBackup;
      }
    } else {
      state.messages = serverMessages;
    }

    saveMessagesLocally(chatId, state.messages);
    renderMessages();
  } catch (err) {
    console.error('Fehler beim Laden der Nachrichten:', err);
    try {
      const raw = localStorage.getItem(`charai_backup_msgs_${chatId}`);
      if (raw) {
        state.messages = JSON.parse(raw);
        renderMessages();
      }
    } catch (_) {}
  }
}

function renderMessages() {
  DOM.messagesFeed.innerHTML = '';

  if (state.messages.length === 0) {
    const char = state.activeCharacter;
    const emptyEl = document.createElement('div');
    emptyEl.className = 'empty-chat-state';
    emptyEl.innerHTML = `
      <img src="${escapeHtml(char.avatar)}" class="empty-chat-avatar" onerror="this.src='/static/avatars/default.svg'">
      <h3>Du bist am Zug!</h3>
      <p>Eröffne das Gespräch mit <strong>${escapeHtml(char.name)}</strong>. Beschreibe die Szene oder stelle die erste Frage.</p>
    `;
    DOM.messagesFeed.appendChild(emptyEl);
  } else {
    state.messages.forEach(msg => {
      const msgEl = createMessageElement(msg);
      DOM.messagesFeed.appendChild(msgEl);
    });
  }
  scrollToBottom();
}

function createMessageElement(msg) {
  const isUser = msg.role === 'user';
  const row = document.createElement('div');
  row.className = `message-row ${isUser ? 'user' : 'assistant'}`;
  row.dataset.msgId = msg.id;

  const char = state.activeCharacter;
  const userAvatar = (state.user && state.user.avatar) ? state.user.avatar : '/static/avatars/default.svg';
  const userName = (state.user && (state.user.display_name || state.user.username)) ? (state.user.display_name || state.user.username) : (state.settings.user_name || 'Du');

  const avatarSrc = isUser ? userAvatar : (char ? char.avatar : '/static/avatars/default.svg');
  const senderName = isUser ? userName : (char ? char.name : 'Charakter');

  const alts = Array.isArray(msg.alternatives) && msg.alternatives.length > 0 ? msg.alternatives : [msg.content];
  const currIdx = msg.current_index !== undefined ? msg.current_index : alts.length - 1;
  const content = alts[currIdx] !== undefined ? alts[currIdx] : msg.content;
  const hasImage = Boolean(msg.image_url);

  row.innerHTML = `
    <img src="${escapeHtml(avatarSrc)}" class="message-avatar" alt="${escapeHtml(senderName)}" onerror="this.src='/static/avatars/default.svg'">
    <div class="message-bubble-wrap">
      <div class="message-sender-name">${escapeHtml(senderName)}</div>
      ${hasImage ? `
        <div class="message-attached-image" title="Klicken zum Vergrößern">
          <img src="${escapeHtml(msg.image_url)}" alt="Angehängtes Bild">
        </div>
      ` : ''}
      <div class="message-bubble">${formatRoleplayMarkdown(content)}</div>
      ${!isUser && alts.length > 1 ? `
        <div class="message-swipes">
          <button class="swipe-btn swipe-prev" ${currIdx <= 0 ? 'disabled' : ''} title="Vorherige Antwort (Swipe)">◀</button>
          <span>${currIdx + 1} / ${alts.length}</span>
          <button class="swipe-btn swipe-next" ${currIdx >= alts.length - 1 ? 'disabled' : ''} title="Nächste Antwort (Swipe)">▶</button>
        </div>
      ` : ''}
      <div class="message-actions">
        ${!isUser ? `
          <button class="action-icon-btn btn-regenerate" title="Neu generieren (Swipe)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
          </button>
        ` : ''}
        <button class="action-icon-btn btn-copy" title="Text kopieren">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        </button>
        <button class="action-icon-btn btn-edit" title="Bearbeiten">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
        </button>
        <button class="action-icon-btn btn-delete" title="Löschen">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
        </button>
      </div>
    </div>
  `;

  // Lightbox click on message image
  const imgEl = row.querySelector('.message-attached-image img');
  if (imgEl) {
    imgEl.addEventListener('click', () => openLightbox(msg.image_url));
  }

  const btnPrev = row.querySelector('.swipe-prev');
  const btnNext = row.querySelector('.swipe-next');
  if (btnPrev) btnPrev.addEventListener('click', () => handleSwipe(msg.id, currIdx - 1));
  if (btnNext) btnNext.addEventListener('click', () => handleSwipe(msg.id, currIdx + 1));

  const btnRegen = row.querySelector('.btn-regenerate');
  if (btnRegen) btnRegen.addEventListener('click', () => handleRegenerate());

  const btnCopy = row.querySelector('.btn-copy');
  if (btnCopy) {
    const handleCopy = async (e) => {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      const ok = await copyToClipboard(content);
      if (ok) {
        const origSvg = btnCopy.innerHTML;
        btnCopy.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`;
        btnCopy.style.color = '#10b981';
        btnCopy.classList.add('copied');
        setTimeout(() => {
          btnCopy.innerHTML = origSvg;
          btnCopy.style.color = '';
          btnCopy.classList.remove('copied');
        }, 1500);
      } else {
        btnCopy.style.color = '#ef4444';
        setTimeout(() => { btnCopy.style.color = ''; }, 1200);
      }
    };
    btnCopy.addEventListener('click', handleCopy);
    btnCopy.addEventListener('touchend', handleCopy);
  }

  const btnEdit = row.querySelector('.btn-edit');
  if (btnEdit) btnEdit.addEventListener('click', (e) => { e.stopPropagation(); enableMessageEdit(row, msg, content); });

  const btnDelete = row.querySelector('.btn-delete');
  if (btnDelete) btnDelete.addEventListener('click', (e) => { e.stopPropagation(); handleDeleteMessage(msg.id); });

  return row;
}

// -------------------------------------------------------------
// Message Sending & Streaming (SSE)
// -------------------------------------------------------------
async function handleSendMessage() {
  if (state.isStreaming || !state.activeChat) return;

  const content = DOM.chatTextarea.value.trim();
  const imageUrl = state.pendingChatImageUrl;

  if (!content && !imageUrl) return;

  DOM.chatTextarea.value = '';
  DOM.chatTextarea.style.height = 'auto';
  DOM.charCounter.textContent = '0 / 4000';
  removeChatAttachment();

  // Optimistic User Message
  const tempUserMsg = {
    id: 'temp-' + Date.now(),
    role: 'user',
    content: content,
    image_url: imageUrl,
    alternatives: [content],
    current_index: 0
  };
  state.messages.push(tempUserMsg);
  DOM.messagesFeed.appendChild(createMessageElement(tempUserMsg));
  scrollToBottom();

  // Assistant Bubble
  state.isStreaming = true;
  DOM.typingIndicator.style.display = 'flex';
  DOM.btnSendMessage.disabled = true;
  if (DOM.btnSkipContinue) DOM.btnSkipContinue.disabled = true;

  const char = state.activeCharacter;
  const assistantRow = document.createElement('div');
  assistantRow.className = 'message-row assistant streaming';
  assistantRow.innerHTML = `
    <img src="${escapeHtml(char.avatar)}" class="message-avatar" alt="${escapeHtml(char.name)}" onerror="this.src='/static/avatars/default.svg'">
    <div class="message-bubble-wrap">
      <div class="message-sender-name">${escapeHtml(char.name)}</div>
      <div class="message-bubble"><span class="stream-text"></span><span class="typing-dot" style="display:inline-block; margin-left:4px;"></span></div>
    </div>
  `;
  DOM.messagesFeed.appendChild(assistantRow);
  scrollToBottom();

  const bubbleTextSpan = assistantRow.querySelector('.stream-text');
  let accumulated = '';

  try {
    const response = await fetch(`/api/chats/${state.activeChat.id}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, image_url: imageUrl })
    });

    if (!response.ok) throw new Error(`Serverstatus: ${response.status}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let hasReceivedDone = false;

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'chunk') {
              accumulated += data.content;
              bubbleTextSpan.innerHTML = formatRoleplayMarkdown(accumulated);
              scrollToBottom();
            } else if (data.type === 'done') {
              hasReceivedDone = true;
              state.messages = state.messages.filter(m => m.id !== tempUserMsg.id);
              await loadMessages(state.activeChat.id);
            }
          } catch (e) {
            console.error('Error parsing SSE:', e);
          }
        }
      }
    }
  } catch (err) {
    console.error('Streaming error:', err);
    bubbleTextSpan.innerHTML = `<span style="color:#ef4444;">*(Fehler: ${err.message})*</span>`;
  } finally {
    state.isStreaming = false;
    DOM.typingIndicator.style.display = 'none';
    DOM.btnSendMessage.disabled = false;
    if (DOM.btnSkipContinue) DOM.btnSkipContinue.disabled = false;
    if (assistantRow.parentNode) {
      assistantRow.remove();
    }
    await loadMessages(state.activeChat.id);
  }
}

// -------------------------------------------------------------
// Skip / Continue (AI generates response without user message)
// -------------------------------------------------------------
async function handleSkipContinue() {
  if (state.isStreaming || !state.activeChat || !state.activeCharacter) return;

  state.isStreaming = true;
  DOM.typingIndicator.style.display = 'flex';
  DOM.btnSendMessage.disabled = true;
  if (DOM.btnSkipContinue) DOM.btnSkipContinue.disabled = true;

  const char = state.activeCharacter;
  const assistantRow = document.createElement('div');
  assistantRow.className = 'message-row assistant streaming';
  assistantRow.innerHTML = `
    <img src="${escapeHtml(char.avatar)}" class="message-avatar" alt="${escapeHtml(char.name)}" onerror="this.src='/static/avatars/default.svg'">
    <div class="message-bubble-wrap">
      <div class="message-sender-name">${escapeHtml(char.name)}</div>
      <div class="message-bubble"><span class="stream-text"></span><span class="typing-dot" style="display:inline-block; margin-left:4px;"></span></div>
    </div>
  `;
  DOM.messagesFeed.appendChild(assistantRow);
  scrollToBottom();

  const bubbleTextSpan = assistantRow.querySelector('.stream-text');
  let accumulated = '';

  try {
    const response = await fetch(`/api/chats/${state.activeChat.id}/continue`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) throw new Error(`Serverstatus: ${response.status}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'chunk') {
              accumulated += data.content;
              bubbleTextSpan.innerHTML = formatRoleplayMarkdown(accumulated);
              scrollToBottom();
            } else if (data.type === 'done') {
              await loadMessages(state.activeChat.id);
            }
          } catch (e) {
            console.error('Error parsing SSE:', e);
          }
        }
      }
    }
  } catch (err) {
    console.error('Continue streaming error:', err);
    bubbleTextSpan.innerHTML = `<span style="color:#ef4444;">*(Fehler: ${err.message})*</span>`;
  } finally {
    state.isStreaming = false;
    DOM.typingIndicator.style.display = 'none';
    DOM.btnSendMessage.disabled = false;
    if (DOM.btnSkipContinue) DOM.btnSkipContinue.disabled = false;
    if (assistantRow.parentNode) {
      assistantRow.remove();
    }
  }
}

// -------------------------------------------------------------
// Swipes & Regeneration
// -------------------------------------------------------------
async function handleRegenerate() {
  if (state.isStreaming || !state.activeChat) return;

  state.isStreaming = true;
  DOM.typingIndicator.style.display = 'flex';
  DOM.btnSendMessage.disabled = true;
  if (DOM.btnSkipContinue) DOM.btnSkipContinue.disabled = true;

  try {
    const response = await fetch(`/api/chats/${state.activeChat.id}/regenerate`, {
      method: 'POST'
    });

    if (!response.ok) throw new Error('Regeneration failed');

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'done') {
            await loadMessages(state.activeChat.id);
          }
        }
      }
    }
  } catch (err) {
    console.error('Error regenerating:', err);
  } finally {
    state.isStreaming = false;
    DOM.typingIndicator.style.display = 'none';
    DOM.btnSendMessage.disabled = false;
    if (DOM.btnSkipContinue) DOM.btnSkipContinue.disabled = false;
  }
}

async function handleSwipe(msgId, targetIndex) {
  try {
    const res = await fetch(`/api/messages/${msgId}/swipe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ index: targetIndex })
    });
    if (res.ok) {
      await loadMessages(state.activeChat.id);
    }
  } catch (err) {
    console.error('Swipe error:', err);
  }
}

// -------------------------------------------------------------
// Message Editing & Deletion
// -------------------------------------------------------------
function enableMessageEdit(row, msg, currentContent) {
  const bubble = row.querySelector('.message-bubble');
  const originalHtml = bubble.innerHTML;

  bubble.innerHTML = `
    <textarea class="input-field" style="width:100%; min-height:80px; margin-bottom:8px;">${escapeHtml(currentContent)}</textarea>
    <div style="display:flex; justify-content:flex-end; gap:8px;">
      <button class="btn btn-secondary btn-sm btn-cancel-edit">Abbrechen</button>
      <button class="btn btn-primary btn-sm btn-save-edit">Speichern</button>
    </div>
  `;

  const txtArea = bubble.querySelector('textarea');
  txtArea.focus();

  bubble.querySelector('.btn-cancel-edit').addEventListener('click', () => {
    bubble.innerHTML = originalHtml;
  });

  bubble.querySelector('.btn-save-edit').addEventListener('click', async () => {
    const newText = txtArea.value.trim();
    if (!newText) return;

    try {
      const res = await fetch(`/api/messages/${msg.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: newText })
      });
      if (res.ok) {
        await loadMessages(state.activeChat.id);
      }
    } catch (e) {
      console.error('Error editing message:', e);
    }
  });
}

async function handleDeleteMessage(msgId) {
  if (!confirm('Möchtest du diese Nachricht wirklich löschen?')) return;
  try {
    const chatId = state.activeChat ? state.activeChat.id : null;
    
    // 1. Immediately remove message from state.messages
    state.messages = state.messages.filter(m => String(m.id) !== String(msgId));
    
    // 2. Immediately update local storage backups so auto-recovery doesn't restore it
    if (chatId) {
      saveMessagesLocally(chatId, state.messages);
    }
    
    // 3. Immediately re-render feed so the message vanishes instantly
    renderMessages();
    
    // 4. Send DELETE request to server
    await fetch(`/api/messages/${msgId}`, { method: 'DELETE' });
  } catch (err) {
    console.error('Error deleting message:', err);
  }
}

// -------------------------------------------------------------
// Roleplay Markdown Formatter
// -------------------------------------------------------------
function formatRoleplayMarkdown(text) {
  if (!text) return '';

  // Strip accidental leading role prefixes like "assistant\n" or "assistant:"
  let cleanText = text
    .replace(/^(?:assistant|AI)\s*[:\n\-–—]*\s*/i, '')
    .replace(/^assistant\s+/i, '');

  if (state.activeCharacter && state.activeCharacter.name) {
    const escName = state.activeCharacter.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    cleanText = cleanText.replace(new RegExp(`^${escName}\\s*[:\\n\\-–—]*\\s*`, 'i'), '');
  }

  let escaped = escapeHtml(cleanText);

  escaped = escaped.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
  escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Roleplay formatting:
  // Beide Varianten: **Gedanken/Taten** und *Taten/Aktionen* werden kursiv im Roleplay-Stil hervorgehoben
  escaped = escaped.replace(/(\*{1,3})([^*\n]+?)\1/g, (match, stars, content) => {
    const cls = stars.length >= 2 ? 'action-text action-thought' : 'action-text';
    return `<span class="${cls}">${stars}${content}${stars}</span>`;
  });
  // Auch Unterstriche _Aktion_
  escaped = escaped.replace(/_([^_]+)_/g, '<span class="action-text">*$1*</span>');
  escaped = escaped.replace(/^&gt;\s*(.+)$/gm, '<blockquote>$1</blockquote>');

  const paragraphs = escaped.split(/\n\n+/);
  return paragraphs.map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Universal Clipboard Helper (supports HTTP LAN IP, HTTPS, Localhost, Mobile touch)
async function copyToClipboard(text) {
  if (!text) return false;

  // 1. Try modern navigator.clipboard if available and in secure context
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      console.warn('navigator.clipboard.writeText failed, using fallback:', err);
    }
  }

  // 2. Fallback using document.execCommand('copy') with hidden textarea
  try {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.width = '2em';
    textArea.style.height = '2em';
    textArea.style.padding = '0';
    textArea.style.border = 'none';
    textArea.style.outline = 'none';
    textArea.style.boxShadow = 'none';
    textArea.style.background = 'transparent';
    textArea.style.opacity = '0.01';
    textArea.style.zIndex = '-9999';
    textArea.setAttribute('readonly', '');
    document.body.appendChild(textArea);

    textArea.focus();
    textArea.select();
    textArea.setSelectionRange(0, 99999); // Mobile iOS / Android selection

    const successful = document.execCommand('copy');
    document.body.removeChild(textArea);
    return successful;
  } catch (err) {
    console.error('Fallback copy command failed:', err);
    return false;
  }
}

function scrollToBottom() {
  DOM.messagesFeed.scrollTop = DOM.messagesFeed.scrollHeight;
}

// -------------------------------------------------------------
// Quick Starters (Disabled / Removed per user request)
// -------------------------------------------------------------
function renderStarters() {
  if (DOM.startersBar) DOM.startersBar.innerHTML = '';
}

// -------------------------------------------------------------
// Speech Synthesis (Disabled)
// -------------------------------------------------------------
function speakMessage(text) {
  // Voice feature completely silenced per user request
  if ('speechSynthesis' in window) {
    try { window.speechSynthesis.cancel(); } catch (e) {}
  }
}

// -------------------------------------------------------------
// Character Creation & Editing Modals
// -------------------------------------------------------------
function openCharacterModal(char = null) {
  DOM.searchProfileStatus.style.display = 'none';
  DOM.searchProfileInput.value = '';
  const lang = (state.settings && state.settings.language) || 'auto';

  if (char) {
    DOM.modalCharTitle.textContent = typeof getTranslation === 'function' ? getTranslation('modal_char_edit_title', lang) : 'Charakter bearbeiten';
    DOM.charFormId.value = char.id;
    DOM.charName.value = char.name;
    DOM.charTitle.value = char.title || '';
    DOM.charTagline.value = char.tagline || '';
    DOM.charGreeting.value = char.greeting || '';
    DOM.charPersona.value = char.persona || '';
    DOM.charAvatarUrl.value = char.avatar || '';
    DOM.charAvatarPreview.src = char.avatar || '/static/avatars/default.svg';
    DOM.charIsNsfw.checked = Boolean(char.is_nsfw);
  } else {
    DOM.modalCharTitle.textContent = typeof getTranslation === 'function' ? getTranslation('modal_char_create_title', lang) : 'Neuen Charakter erstellen';
    DOM.formCharacter.reset();
    DOM.charFormId.value = '';
    DOM.charAvatarPreview.src = '/static/avatars/default.svg';
    DOM.charIsNsfw.checked = false;
  }
  DOM.modalCharacter.style.display = 'flex';
}

function openCharDetailsModal(char) {
  if (!char) return;
  const lang = (state.settings && state.settings.language) || 'auto';
  DOM.viewCharTitle.textContent = char.name;
  const greetingLabel = typeof getTranslation === 'function' ? getTranslation('label_char_greeting', lang) : 'Anfangstext (Start-Szene):';
  const personaLabel = typeof getTranslation === 'function' ? getTranslation('label_char_persona', lang) : 'Persönlichkeit & Prompt:';
  const exportTxt = typeof getTranslation === 'function' ? getTranslation('btn_export_char', lang) : '📁 Als JSON exportieren';
  const editTxt = typeof getTranslation === 'function' ? getTranslation('btn_edit_char', lang) : '✏️ Bearbeiten';
  const deleteTxt = typeof getTranslation === 'function' ? getTranslation('btn_delete_char', lang) : '🗑️ Löschen';

  DOM.viewCharBody.innerHTML = `
    <div style="display:flex; align-items:center; gap:16px; margin-bottom:16px;">
      <img src="${escapeHtml(char.avatar)}" style="width:70px; height:70px; border-radius:50%; object-fit:cover; border:2px solid var(--primary); cursor:pointer;" onclick="openLightbox('${escapeHtml(char.avatar)}')">
      <div>
        <div style="display:flex; align-items:center; gap:8px;">
          <h3 style="font-size:18px; margin-bottom:2px;">${escapeHtml(char.name)}</h3>
          ${char.is_nsfw ? '<span class="badge-nsfw">18+</span>' : ''}
        </div>
        <p style="color:var(--text-secondary); font-size:13px;">${escapeHtml(char.title || '')}</p>
        <p style="color:var(--text-muted); font-size:12px; font-style:italic; margin-top:2px;">"${escapeHtml(char.tagline || '')}"</p>
      </div>
    </div>
    <div class="form-group" style="margin-bottom:12px;">
      <label>${greetingLabel}</label>
      <div style="background:var(--bg-main); padding:10px 14px; border-radius:8px; font-size:13px; line-height:1.6; white-space:pre-wrap; border:1px solid var(--border-color);">${escapeHtml(char.greeting || '')}</div>
    </div>
    <div class="form-group">
      <label>${personaLabel}</label>
      <div style="background:var(--bg-main); padding:12px; border-radius:8px; font-size:13px; line-height:1.6; white-space:pre-wrap; max-height:200px; overflow-y:auto; border:1px solid var(--border-color);">${escapeHtml(char.persona)}</div>
    </div>
  `;

  DOM.viewCharFooter.innerHTML = `
    <button class="btn btn-secondary" id="btn-export-char-json">📁 ${exportTxt}</button>
    <button class="btn btn-secondary" id="btn-edit-current-char">✏️ ${editTxt}</button>
    <button class="btn btn-danger" style="background:#ef4444; color:white;" id="btn-delete-current-char">🗑️ ${deleteTxt}</button>
  `;

  document.getElementById('btn-export-char-json').addEventListener('click', () => {
    window.location.href = `/api/characters/${char.id}/export`;
  });

  document.getElementById('btn-edit-current-char').addEventListener('click', () => {
    DOM.modalCharView.style.display = 'none';
    openCharacterModal(char);
  });

  document.getElementById('btn-delete-current-char').addEventListener('click', async () => {
    const confirmDeleteMsg = typeof getTranslation === 'function' ? getTranslation('confirm_delete_char', lang) : `Bist du sicher, dass du "${char.name}" löschen möchtest?`;
    if (!confirm(confirmDeleteMsg)) return;
    try {
      const res = await fetch(`/api/characters/${char.id}`, { method: 'DELETE' });
      if (res.ok) {
        DOM.modalCharView.style.display = 'none';
        await loadCharacters();
      }
    } catch (e) {
      console.error(e);
    }
  });

  DOM.modalCharView.style.display = 'flex';
}

// -------------------------------------------------------------
// Event Listeners
// -------------------------------------------------------------
function setupEventListeners() {
  // Sidebar toggle with Mobile Backdrop
  const closeSidebar = () => {
    DOM.sidebar.classList.remove('open');
    if (DOM.sidebarBackdrop) DOM.sidebarBackdrop.classList.remove('active');
  };
  const openSidebar = () => {
    DOM.sidebar.classList.add('open');
    if (DOM.sidebarBackdrop) DOM.sidebarBackdrop.classList.add('active');
  };

  DOM.btnToggleSidebar.addEventListener('click', closeSidebar);
  DOM.btnShowSidebar.addEventListener('click', openSidebar);
  if (DOM.sidebarBackdrop) {
    DOM.sidebarBackdrop.addEventListener('click', closeSidebar);
    DOM.sidebarBackdrop.addEventListener('touchstart', closeSidebar, { passive: true });
  }

  // Character Search
  DOM.characterSearch.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    const filtered = state.characters.filter(c =>
      c.name.toLowerCase().includes(q) ||
      (c.tagline && c.tagline.toLowerCase().includes(q)) ||
      (c.title && c.title.toLowerCase().includes(q))
    );
    renderCharacterList(filtered);
  });

  // Create character button
  DOM.btnCreateChar.addEventListener('click', () => openCharacterModal());

  // Web Search in modal
  DOM.btnSearchProfile.addEventListener('click', () => handleSearchProfile());
  DOM.searchProfileInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSearchProfile();
    }
  });

  document.querySelectorAll('.quick-search-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      DOM.searchProfileInput.value = chip.textContent;
      handleSearchProfile(chip.textContent);
    });
  });

  // Avatar Upload from PC
  DOM.btnUploadAvatar.addEventListener('click', () => DOM.charAvatarFileInput.click());
  DOM.avatarDropzone.addEventListener('click', () => DOM.charAvatarFileInput.click());

  DOM.charAvatarFileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const uploadedUrl = await uploadImageFile(file, 'avatar');
      DOM.charAvatarUrl.value = uploadedUrl;
      DOM.charAvatarPreview.src = uploadedUrl;
      DOM.avatarDropzone.classList.add('highlight-pulse');
      setTimeout(() => DOM.avatarDropzone.classList.remove('highlight-pulse'), 800);
    } catch (err) {
      alert('Fehler beim Hochladen des Avatar-Bildes: ' + err.message);
    }
    DOM.charAvatarFileInput.value = '';
  });

  // Drag and drop avatar
  DOM.avatarDropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    DOM.avatarDropzone.style.borderColor = '#10b981';
  });
  DOM.avatarDropzone.addEventListener('dragleave', () => {
    DOM.avatarDropzone.style.borderColor = '';
  });
  DOM.avatarDropzone.addEventListener('drop', async (e) => {
    e.preventDefault();
    DOM.avatarDropzone.style.borderColor = '';
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      try {
        const uploadedUrl = await uploadImageFile(file, 'avatar');
        DOM.charAvatarUrl.value = uploadedUrl;
        DOM.charAvatarPreview.src = uploadedUrl;
      } catch (err) {
        alert('Fehler: ' + err.message);
      }
    }
  });

  // Chat Image Attachments
  DOM.btnAttachImage.addEventListener('click', () => DOM.chatFileInput.click());

  DOM.chatFileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const uploadedUrl = await uploadImageFile(file, 'chat');
      handleChatAttachment(uploadedUrl, file.name);
    } catch (err) {
      alert('Fehler beim Hochladen: ' + err.message);
    }
  });

  DOM.btnRemoveAttachment.addEventListener('click', () => removeChatAttachment());

  // Clipboard Paste Support (Ctrl+V with image anywhere in chat)
  window.addEventListener('paste', async (e) => {
    const items = (e.clipboardData || e.originalEvent.clipboardData).items;
    for (const item of items) {
      if (item.type.indexOf('image') !== -1) {
        e.preventDefault();
        const blob = item.getAsFile();
        try {
          const uploadedUrl = await uploadImageFile(blob, 'chat');
          handleChatAttachment(uploadedUrl, 'Screenshot aus Zwischenablage');
        } catch (err) {
          console.error('Clipboard upload error:', err);
        }
        break;
      }
    }
  });

  // Lightbox close
  DOM.btnCloseLightbox.addEventListener('click', () => {
    DOM.modalLightbox.style.display = 'none';
  });
  DOM.modalLightbox.addEventListener('click', (e) => {
    if (e.target === DOM.modalLightbox) {
      DOM.modalLightbox.style.display = 'none';
    }
  });

  // Import character button
  DOM.btnImportChar.addEventListener('click', () => DOM.fileImportInput.click());
  DOM.fileImportInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const text = await file.text();
      const json = JSON.parse(text);
      const res = await fetch('/api/characters/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(json)
      });
      if (res.ok) {
        const saved = await res.json();
        await loadCharacters();
        selectCharacter(saved);
      }
    } catch (err) {
      alert('Ungültige JSON-Charakterkarte!');
    }
    DOM.fileImportInput.value = '';
  });

  // Avatar presets
  document.querySelectorAll('.preset-avatar').forEach(img => {
    img.addEventListener('click', () => {
      const p = img.dataset.path;
      DOM.charAvatarUrl.value = p;
      DOM.charAvatarPreview.src = p;
      document.querySelectorAll('.preset-avatar').forEach(i => i.classList.remove('selected'));
      img.classList.add('selected');
    });
  });

  DOM.charAvatarUrl.addEventListener('input', (e) => {
    const v = e.target.value.trim() || '/static/avatars/default.svg';
    DOM.charAvatarPreview.src = v;
  });

  // Save Character Form
  DOM.formCharacter.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      id: DOM.charFormId.value || undefined,
      name: DOM.charName.value.trim(),
      title: DOM.charTitle.value.trim(),
      tagline: DOM.charTagline.value.trim(),
      greeting: DOM.charGreeting.value.trim(),
      persona: DOM.charPersona.value.trim(),
      example_dialogue: '',
      avatar: DOM.charAvatarUrl.value.trim() || '/static/avatars/default.svg',
      is_nsfw: DOM.charIsNsfw.checked ? 1 : 0
    };

    try {
      const res = await fetch('/api/characters', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const saved = await res.json();
        DOM.modalCharacter.style.display = 'none';
        await loadCharacters();
        selectCharacter(saved);
      }
    } catch (err) {
      console.error('Error saving character:', err);
    }
  });

  // Sessions Dropdown
  DOM.btnSessionsDropdown.addEventListener('click', (e) => {
    e.stopPropagation();
    DOM.sessionsDropdownMenu.classList.toggle('show');
  });
  window.addEventListener('click', () => {
    DOM.sessionsDropdownMenu.classList.remove('show');
  });

  // New Chat Dropdown
  DOM.btnNewChatDropdown.addEventListener('click', (e) => {
    e.stopPropagation();
    DOM.newChatDropdownMenu.classList.toggle('show');
  });

  DOM.btnCreateChatWithGreeting.addEventListener('click', () => {
    DOM.newChatDropdownMenu.classList.remove('show');
    handleCreateNewChat(true);
  });

  DOM.btnCreateChatEmpty.addEventListener('click', () => {
    DOM.newChatDropdownMenu.classList.remove('show');
    handleCreateNewChat(false);
  });

  window.addEventListener('click', () => {
    if (DOM.newChatDropdownMenu) {
      DOM.newChatDropdownMenu.classList.remove('show');
    }
  });

  // Character details button & Header tap
  if (DOM.btnCharDetails) {
    DOM.btnCharDetails.addEventListener('click', () => openCharDetailsModal(state.activeCharacter));
  }
  if (DOM.headerCharInfo) {
    DOM.headerCharInfo.addEventListener('click', () => openCharDetailsModal(state.activeCharacter));
  }

  // Sound toggle (if present)
  if (DOM.btnSoundToggle) {
    DOM.btnSoundToggle.addEventListener('click', () => {
      state.ttsEnabled = !state.ttsEnabled;
      DOM.btnSoundToggle.style.color = state.ttsEnabled ? '#6366f1' : 'var(--text-muted)';
    });
  }

  // Language Dropdown
  if (DOM.btnLanguageDropdown) {
    DOM.btnLanguageDropdown.addEventListener('click', (e) => {
      e.stopPropagation();
      DOM.languageDropdownMenu.classList.toggle('show');
    });
  }

  if (DOM.languageDropdownMenu) {
    DOM.languageDropdownMenu.querySelectorAll('.dropdown-item').forEach(btn => {
      btn.addEventListener('click', async () => {
        const selectedLang = btn.dataset.lang;
        DOM.languageDropdownMenu.classList.remove('show');
        state.settings.language = selectedLang;
        updateUIWithSettings();
        renderSessionsMenu();
        try {
          await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ settings: { ...state.settings, language: selectedLang } })
          });
        } catch (err) {
          console.error('Fehler beim Speichern der Sprache:', err);
        }
      });
    });
  }

  window.addEventListener('click', () => {
    if (DOM.languageDropdownMenu) {
      DOM.languageDropdownMenu.classList.remove('show');
    }
  });

  // Settings Modal
  DOM.btnOpenSettings.addEventListener('click', () => {
    DOM.modalSettings.style.display = 'flex';
  });

  // User Profile / Account Modal
  DOM.userProfileBtn.addEventListener('click', () => {
    if (state.user) {
      if (DOM.modalUserAccount) DOM.modalUserAccount.style.display = 'flex';
    } else {
      openAuthModal('login');
    }
  });

  if (DOM.btnAuthToggle) {
    DOM.btnAuthToggle.addEventListener('click', () => {
      if (state.user) {
        if (DOM.modalUserAccount) DOM.modalUserAccount.style.display = 'flex';
      } else {
        openAuthModal('login');
      }
    });
  }

  // Auth tabs & forms
  if (DOM.tabBtnLogin) {
    DOM.tabBtnLogin.addEventListener('click', () => switchAuthTab('login'));
  }
  if (DOM.tabBtnRegister) {
    DOM.tabBtnRegister.addEventListener('click', () => switchAuthTab('register'));
  }
  if (DOM.formAuthLogin) {
    DOM.formAuthLogin.addEventListener('submit', handleLogin);
  }
  if (DOM.formAuthRegister) {
    DOM.formAuthRegister.addEventListener('submit', handleRegister);
  }
  if (DOM.btnContinueAsGuest) {
    DOM.btnContinueAsGuest.addEventListener('click', () => {
      localStorage.setItem('guest_mode_dismissed', 'true');
      if (DOM.modalAuth) DOM.modalAuth.style.display = 'none';
    });
  }
  if (DOM.formUpdateProfile) {
    DOM.formUpdateProfile.addEventListener('submit', handleUpdateProfile);
  }
  if (DOM.btnAccountLogout) {
    DOM.btnAccountLogout.addEventListener('click', handleLogout);
  }

  // User Avatar file upload & preset selection
  const triggerAvatarUpload = () => {
    if (DOM.userAvatarFileInput) DOM.userAvatarFileInput.click();
  };
  if (DOM.btnTriggerUserAvatarUpload) {
    DOM.btnTriggerUserAvatarUpload.addEventListener('click', triggerAvatarUpload);
  }
  if (DOM.btnUserAvatarFileBtn) {
    DOM.btnUserAvatarFileBtn.addEventListener('click', triggerAvatarUpload);
  }

  if (DOM.userAvatarFileInput) {
    DOM.userAvatarFileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      try {
        const uploadedUrl = await uploadImageFile(file, 'avatar');
        if (DOM.accountAvatarImg) DOM.accountAvatarImg.src = uploadedUrl;
        if (DOM.profileInputAvatar) DOM.profileInputAvatar.value = uploadedUrl;
        document.querySelectorAll('.user-preset-avatar').forEach(el => el.classList.remove('selected'));
      } catch (err) {
        alert('Fehler beim Hochladen des Profilbildes: ' + err.message);
      }
      DOM.userAvatarFileInput.value = '';
    });
  }

  document.querySelectorAll('.user-preset-avatar').forEach(img => {
    img.addEventListener('click', () => {
      const p = img.dataset.path;
      if (DOM.accountAvatarImg) DOM.accountAvatarImg.src = p;
      if (DOM.profileInputAvatar) DOM.profileInputAvatar.value = p;
      document.querySelectorAll('.user-preset-avatar').forEach(el => el.classList.remove('selected'));
      img.classList.add('selected');
    });
  });

  // Provider radio change
  document.getElementsByName('provider').forEach(radio => {
    radio.addEventListener('change', (e) => {
      handleProviderFieldsVisibility(e.target.value);
    });
  });

  // Save Settings Form
  DOM.formSettings.addEventListener('submit', async (e) => {
    e.preventDefault();
    const settingsPayload = {
      provider: 'openai',
      openai_base_url: 'https://api.groq.com/openai/v1',
      openai_api_key: DEFAULT_GROQ_KEY,
      openai_model: 'qwen/qwen3.8-27b',
      gemini_api_key: '',
      gemini_model: 'gemini-1.5-flash',
      ollama_base_url: 'http://localhost:11434',
      ollama_model: 'llama3.2',
      nsfw_mode: DOM.setNsfwMode.checked ? 'true' : 'false',
      roleplay_tone: DOM.setRoleplayTone.value,
      language: DOM.setLanguage ? DOM.setLanguage.value : 'auto',
      user_name: DOM.setUserName.value.trim() || 'Reisender',
      user_persona: DOM.setUserPersona.value.trim()
    };

    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings: settingsPayload })
      });
      if (res.ok) {
        state.settings = settingsPayload;
        try {
          localStorage.setItem('charai_cached_settings', JSON.stringify(settingsPayload));
        } catch (_) {}
        updateUIWithSettings();
        renderSessionsMenu();
        DOM.modalSettings.style.display = 'none';
      }
    } catch (err) {
      console.error('Error saving settings:', err);
    }
  });

  // Close modals
  document.querySelectorAll('.btn-close-modal').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.dataset.target;
      if (targetId) {
        document.getElementById(targetId).style.display = 'none';
      }
    });
  });

  // Textarea input & keyboard shortcuts
  DOM.chatTextarea.addEventListener('input', () => {
    DOM.chatTextarea.style.height = 'auto';
    DOM.chatTextarea.style.height = Math.min(DOM.chatTextarea.scrollHeight, 180) + 'px';
    const len = DOM.chatTextarea.value.length;
    DOM.charCounter.textContent = `${len} / 4000`;
  });

  DOM.chatTextarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  DOM.btnSendMessage.addEventListener('click', () => handleSendMessage());
  if (DOM.btnSkipContinue) {
    DOM.btnSkipContinue.addEventListener('click', () => handleSkipContinue());
  }
}

window.addEventListener('DOMContentLoaded', init);
