(function () {
  'use strict';

  var STORAGE_KEY = 'km0-mail-login-lang';
  var LOCALES = ['en', 'es', 'ca', 'de'];
  var DEFAULT_LOCALE = 'en';

  var ROUNDcube_LANG = {
    en: 'en_US',
    es: 'es_ES',
    ca: 'ca_ES',
    de: 'de_DE',
  };

  var strings = {
    en: {
      langAria: 'Language',
      loginEyebrow: 'Kilometer 0 Digital',
      loginTagline: 'Local origin · Digital impact',
      logoAlt: 'Kilometer 0 Digital',
      usernameLabel: 'Username',
      passwordLabel: 'Password',
      loginButton: 'Login',
      support: 'Support',
      registerLink: 'Create a free account',
      registeredBanner:
        'Account created — sign in below with your new address and password.',
      loginErrorCredentials:
        'Incorrect email or password. Check your details (and Caps Lock) and try again.',
      loginErrorServer:
        'The mail server is temporarily unavailable. Please try again in a moment.',
    },
    es: {
      langAria: 'Idioma',
      loginEyebrow: 'Kilómetro 0 Digital',
      loginTagline: 'Origen local · Impacto digital',
      logoAlt: 'Kilómetro 0 Digital',
      usernameLabel: 'Usuario',
      passwordLabel: 'Contraseña',
      loginButton: 'Iniciar sesión',
      support: 'Soporte',
      registerLink: 'Crear cuenta gratuita',
      registeredBanner:
        'Cuenta creada. Entra abajo con tu nueva dirección y contraseña.',
      loginErrorCredentials:
        'Email o contraseña incorrectos. Revisa los datos (y el Bloq Mayús) e inténtalo de nuevo.',
      loginErrorServer:
        'El servidor de correo no está disponible temporalmente. Inténtalo de nuevo en un momento.',
    },
    ca: {
      langAria: 'Idioma',
      loginEyebrow: 'Kilòmetre 0 Digital',
      loginTagline: 'Origen local · Impacte digital',
      logoAlt: 'Kilòmetre 0 Digital',
      usernameLabel: 'Usuari',
      passwordLabel: 'Contrasenya',
      loginButton: 'Iniciar sessió',
      support: 'Suport',
      registerLink: 'Crear compte gratuït',
      registeredBanner:
        'Compte creat. Entra a sota amb la teva nova adreça i contrasenya.',
      loginErrorCredentials:
        'Correu o contrasenya incorrectes. Revisa les dades (i el Bloq Maj) i torna-ho a provar.',
      loginErrorServer:
        'El servidor de correu no està disponible temporalment. Torna-ho a provar d\'aquí un moment.',
    },
    de: {
      langAria: 'Sprache',
      loginEyebrow: 'Kilometer 0 Digital',
      loginTagline: 'Lokaler Ursprung · Digitale Wirkung',
      logoAlt: 'Kilometer 0 Digital',
      usernameLabel: 'Benutzername',
      passwordLabel: 'Passwort',
      loginButton: 'Anmelden',
      support: 'Support',
      registerLink: 'Kostenloses Konto erstellen',
      registeredBanner:
        'Konto erstellt. Melden Sie sich unten mit Ihrer neuen Adresse und Ihrem Passwort an.',
      loginErrorCredentials:
        'E-Mail oder Passwort ist falsch. Bitte prüfen Sie Ihre Angaben (und die Feststelltaste) und versuchen Sie es erneut.',
      loginErrorServer:
        'Der Mailserver ist vorübergehend nicht verfügbar. Bitte versuchen Sie es gleich erneut.',
    },
  };

  function normalizeLocale(raw) {
    if (!raw) return null;
    var code = String(raw).toLowerCase().split('-')[0];
    return LOCALES.indexOf(code) >= 0 ? code : null;
  }

  function detectBrowserLocale() {
    if (typeof navigator === 'undefined' || !navigator.language) return DEFAULT_LOCALE;
    var langs = navigator.languages || [navigator.language];
    for (var i = 0; i < langs.length; i++) {
      var loc = normalizeLocale(langs[i]);
      if (loc) return loc;
    }
    return DEFAULT_LOCALE;
  }

  function getLocale() {
    try {
      var params = new URLSearchParams(window.location.search);
      var fromQuery = normalizeLocale(params.get('lang'));
      if (fromQuery) {
        localStorage.setItem(STORAGE_KEY, fromQuery);
        return fromQuery;
      }
      var stored = normalizeLocale(localStorage.getItem(STORAGE_KEY));
      if (stored) return stored;
    } catch (e) {
      /* private mode / blocked storage */
    }
    return detectBrowserLocale();
  }

  function t(locale, key) {
    var pack = strings[locale] || strings[DEFAULT_LOCALE];
    return pack[key] || strings[DEFAULT_LOCALE][key] || key;
  }

  function applyFormLabels(locale) {
    var userLabel = document.querySelector('label[for="rcmloginuser"]');
    var passLabel = document.querySelector('label[for="rcmloginpwd"]');
    var submitBtn = document.getElementById('rcmloginsubmit');
    var supportLink = document.querySelector('#login-footer .support-link');

    if (userLabel) userLabel.textContent = t(locale, 'usernameLabel');
    if (passLabel) passLabel.textContent = t(locale, 'passwordLabel');
    if (submitBtn) submitBtn.textContent = t(locale, 'loginButton');
    if (supportLink) supportLink.textContent = t(locale, 'support');
  }

  function applyLocale(locale) {
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      el.textContent = t(locale, el.getAttribute('data-i18n'));
    });

    var logo = document.getElementById('logo');
    if (logo) logo.setAttribute('alt', t(locale, 'logoAlt'));

    var langNav = document.querySelector('.km0-lang-switch');
    if (langNav) langNav.setAttribute('aria-label', t(locale, 'langAria'));

    applyFormLabels(locale);
    document.documentElement.lang = locale;
  }

  function updateLangSwitcher(locale) {
    document.querySelectorAll('.km0-lang-switch [data-lang]').forEach(function (btn) {
      var active = btn.getAttribute('data-lang') === locale;
      btn.classList.toggle('km0-lang-switch__btn--active', active);
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
  }

  function setLocale(locale) {
    try {
      localStorage.setItem(STORAGE_KEY, locale);
    } catch (e) {
      /* ignore */
    }
    applyLocale(locale);
    updateLangSwitcher(locale);
    showQueryBanners(locale);
  }

  function stripBootstrapFromLangButtons() {
    document.querySelectorAll('.km0-lang-switch button').forEach(function (btn) {
      btn.classList.remove('btn', 'btn-secondary', 'btn-primary', 'btn-link');
    });
  }

  function bindLangSwitcher() {
    document.querySelectorAll('.km0-lang-switch [data-lang]').forEach(function (btn) {
      btn.addEventListener('click', function (ev) {
        ev.preventDefault();
        var locale = normalizeLocale(btn.getAttribute('data-lang'));
        if (locale) setLocale(locale);
      });
    });
  }

  function showQueryBanners(locale) {
    try {
      var params = new URLSearchParams(window.location.search);
      var registered = document.getElementById('km0-registered-banner');
      if (registered && params.get('registered') === '1') {
        registered.textContent = t(locale, 'registeredBanner');
        registered.hidden = false;
      }
    } catch (e) {
      /* ignore */
    }
  }

  // Turn Roundcube's generic "Login failed." / "Server Error!" toast into a
  // clear, localized message so users know exactly what went wrong. Roundcube
  // queues the message (pending_message) before its own init flush; overriding
  // display_message synchronously here — while rcmail already exists but the
  // message container does not yet — lets us rewrite it before it is shown.
  function mapLoginMessage(locale, msg, type) {
    if (typeof msg !== 'string') return null;
    var m = msg.toLowerCase();
    if (m.indexOf('login failed') !== -1 || m.indexOf('authentication') !== -1) {
      return { msg: t(locale, 'loginErrorCredentials'), type: 'error', timeout: 0 };
    }
    if (
      m.indexOf('server error') !== -1 || m.indexOf('storage') !== -1 ||
      m.indexOf('imap') !== -1 || m.indexOf('connect') !== -1 ||
      m.indexOf('unavailable') !== -1
    ) {
      return { msg: t(locale, 'loginErrorServer'), type: 'error', timeout: 0 };
    }
    return null;
  }

  function patchLoginMessages(locale) {
    if (typeof window === 'undefined' || !window.rcmail || window.rcmail.__km0MsgPatched) {
      return;
    }
    var rc = window.rcmail;
    rc.__km0MsgPatched = true;
    var orig = typeof rc.display_message === 'function' ? rc.display_message : null;
    rc.display_message = function (msg, type, timeout, key) {
      var mapped = null;
      try {
        mapped = mapLoginMessage(locale, msg, type);
      } catch (e) {
        /* fall back to original message */
      }
      if (mapped) {
        msg = mapped.msg;
        type = mapped.type;
        timeout = mapped.timeout;
      }
      if (orig) return orig.call(rc, msg, type, timeout, key);
    };
  }

  // Run before DOMContentLoaded so we win the race with rcmail's init flush.
  patchLoginMessages(getLocale());

  function init() {
    var locale = getLocale();
    patchLoginMessages(locale);
    stripBootstrapFromLangButtons();
    applyLocale(locale);
    updateLangSwitcher(locale);
    bindLangSwitcher();
    showQueryBanners(locale);
    stripBootstrapFromLangButtons();
    window.setTimeout(stripBootstrapFromLangButtons, 0);
    window.setTimeout(stripBootstrapFromLangButtons, 100);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.KM0MailLoginI18n = {
    setLocale: setLocale,
    getLocale: getLocale,
    locales: LOCALES,
    roundcubeLang: ROUNDcube_LANG,
  };
})();
