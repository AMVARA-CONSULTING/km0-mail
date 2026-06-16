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

  function init() {
    var locale = getLocale();
    applyLocale(locale);
    updateLangSwitcher(locale);
    bindLangSwitcher();
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
