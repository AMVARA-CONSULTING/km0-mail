(function (global) {
  'use strict';

  var STORAGE_KEY = 'km0-mail-auth-lang';
  var LOCALES = ['en', 'es', 'ca', 'de'];
  var DEFAULT = 'en';

  var strings = {
    en: {
      langAria: 'Language',
      loginEyebrow: 'Kilometer 0 Digital',
      landingTagline: 'Local origin · Digital impact',
      loginTitle: 'KM0 Mail',
      loginIntro: 'Sign in with your KM0 LDAP account or mailbox password.',
      ldapButton: 'Sign in with KM0 LDAP',
      passwordButton: 'Sign in with email and password',
      landingDividerOr: 'or',
      registerLink: 'Create a free account',
      registerSuccessBanner: 'Account created. Log in and confirm the verification email in your inbox.',
      registerTitle: 'Create account',
      registerIntro: 'Choose a @km0digital.com address or use your own domain.',
      modeKm0: '@km0digital.com',
      modeCustom: 'My domain',
      emailLabel: 'Email address',
      usernameLabel: 'Username',
      usernameSuffix: '@km0digital.com',
      passwordLabel: 'Password',
      contactLabel: 'Contact email (optional)',
      submitRegister: 'Create account',
      signInLink: 'Already have an account?',
      pricingNotice: 'KM0 Mail is free during the trial phase. Pricing may change; see km0digital.com for updates.',
      domainTitle: 'Verify your domain',
      domainIntro: 'Add these DNS records at your registrar, then click Check again.',
      checkDns: 'Check again',
      verifyTitle: 'Email verification',
      verifySuccess: 'Your account is verified. You can send mail now.',
      verifyError: 'Invalid or expired verification link.',
      footerHome: 'km0digital.com',
    },
    es: {
      langAria: 'Idioma',
      loginEyebrow: 'Kilómetro 0 Digital',
      landingTagline: 'Origen local · Impacto digital',
      loginTitle: 'KM0 Mail',
      loginIntro: 'Inicia sesión con LDAP de KM0 o con la contraseña del buzón.',
      ldapButton: 'Iniciar sesión con LDAP KM0',
      passwordButton: 'Iniciar sesión con correo y contraseña',
      landingDividerOr: 'o',
      registerLink: 'Crear cuenta gratuita',
      registerSuccessBanner: 'Cuenta creada. Inicia sesión y confirma el correo de verificación en tu bandeja.',
      registerTitle: 'Crear cuenta',
      registerIntro: 'Elige una dirección @km0digital.com o tu propio dominio.',
      modeKm0: '@km0digital.com',
      modeCustom: 'Mi dominio',
      emailLabel: 'Correo electrónico',
      usernameLabel: 'Usuario',
      usernameSuffix: '@km0digital.com',
      passwordLabel: 'Contraseña',
      contactLabel: 'Correo de contacto (opcional)',
      submitRegister: 'Crear cuenta',
      signInLink: '¿Ya tienes cuenta?',
      pricingNotice: 'KM0 Mail es gratuito en la fase de prueba. El precio puede cambiar; consulta km0digital.com.',
      domainTitle: 'Verifica tu dominio',
      domainIntro: 'Añade estos registros DNS en tu registrador y pulsa Comprobar de nuevo.',
      checkDns: 'Comprobar de nuevo',
      verifyTitle: 'Verificación de correo',
      verifySuccess: 'Cuenta verificada. Ya puedes enviar correo.',
      verifyError: 'Enlace de verificación inválido o caducado.',
      footerHome: 'km0digital.com',
    },
    ca: {
      langAria: 'Idioma',
      loginEyebrow: 'Kilòmetre 0 Digital',
      landingTagline: 'Origen local · Impacte digital',
      loginTitle: 'KM0 Mail',
      loginIntro: 'Inicia sessió amb LDAP KM0 o amb la contrasenya de la bústia.',
      ldapButton: 'Iniciar sessió amb LDAP KM0',
      passwordButton: 'Iniciar sessió amb correu i contrasenya',
      landingDividerOr: 'o',
      registerLink: 'Crear compte gratuït',
      registerSuccessBanner: 'Compte creat. Inicia sessió i confirma el correu de verificació.',
      registerTitle: 'Crear compte',
      registerIntro: 'Tria una adreça @km0digital.com o el teu propi domini.',
      modeKm0: '@km0digital.com',
      modeCustom: 'El meu domini',
      emailLabel: 'Adreça de correu',
      usernameLabel: 'Usuari',
      usernameSuffix: '@km0digital.com',
      passwordLabel: 'Contrasenya',
      contactLabel: 'Correu de contacte (opcional)',
      submitRegister: 'Crear compte',
      signInLink: 'Ja tens compte?',
      pricingNotice: 'KM0 Mail és gratuït en la fase de prova. Consulta km0digital.com.',
      domainTitle: 'Verifica el teu domini',
      domainIntro: 'Afegeix aquests registres DNS i prem Comprova de nou.',
      checkDns: 'Comprova de nou',
      verifyTitle: 'Verificació de correu',
      verifySuccess: 'Compte verificat. Ja pots enviar correu.',
      verifyError: 'Enllaç de verificació invàlid o caducat.',
      footerHome: 'km0digital.com',
    },
    de: {
      langAria: 'Sprache',
      loginEyebrow: 'Kilometer 0 Digital',
      landingTagline: 'Lokaler Ursprung · Digitale Wirkung',
      loginTitle: 'KM0 Mail',
      loginIntro: 'Melden Sie sich mit KM0 LDAP oder Ihrem Postfachpasswort an.',
      ldapButton: 'Mit KM0 LDAP anmelden',
      passwordButton: 'Mit E-Mail und Passwort anmelden',
      landingDividerOr: 'oder',
      registerLink: 'Kostenloses Konto erstellen',
      registerSuccessBanner: 'Konto erstellt. Bitte Bestätigungs-E-Mail im Postfach öffnen.',
      registerTitle: 'Konto erstellen',
      registerIntro: 'Wählen Sie @km0digital.com oder Ihre eigene Domain.',
      modeKm0: '@km0digital.com',
      modeCustom: 'Eigene Domain',
      emailLabel: 'E-Mail-Adresse',
      usernameLabel: 'Benutzername',
      usernameSuffix: '@km0digital.com',
      passwordLabel: 'Passwort',
      contactLabel: 'Kontakt-E-Mail (optional)',
      submitRegister: 'Konto erstellen',
      signInLink: 'Bereits ein Konto?',
      pricingNotice: 'KM0 Mail ist in der Testphase kostenlos. Siehe km0digital.com.',
      domainTitle: 'Domain verifizieren',
      domainIntro: 'DNS-Einträge beim Registrar setzen, dann erneut prüfen.',
      checkDns: 'Erneut prüfen',
      verifyTitle: 'E-Mail-Bestätigung',
      verifySuccess: 'Konto bestätigt. Sie können jetzt senden.',
      verifyError: 'Ungültiger oder abgelaufener Bestätigungslink.',
      footerHome: 'km0digital.com',
    },
  };

  function norm(raw) {
    if (!raw) return null;
    var c = String(raw).toLowerCase().split('-')[0];
    return LOCALES.indexOf(c) >= 0 ? c : null;
  }

  function getLocale() {
    try {
      var q = new URLSearchParams(location.search).get('lang');
      var fromQ = norm(q);
      if (fromQ) { localStorage.setItem(STORAGE_KEY, fromQ); return fromQ; }
      return norm(localStorage.getItem(STORAGE_KEY)) || DEFAULT;
    } catch (e) { return DEFAULT; }
  }

  function t(key) {
    var loc = getLocale();
    return (strings[loc] && strings[loc][key]) || strings[DEFAULT][key] || key;
  }

  function apply() {
    var loc = getLocale();
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      el.textContent = t(el.getAttribute('data-i18n'));
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
      el.placeholder = t(el.getAttribute('data-i18n-placeholder'));
    });
    document.documentElement.lang = loc;
    document.querySelectorAll('.km0-lang-switch [data-lang]').forEach(function (btn) {
      var active = btn.getAttribute('data-lang') === loc;
      btn.classList.toggle('km0-lang-switch__btn--active', active);
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
  }

  function bindLang() {
    document.querySelectorAll('.km0-lang-switch [data-lang]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var l = norm(btn.getAttribute('data-lang'));
        if (l) { try { localStorage.setItem(STORAGE_KEY, l); } catch (e) {} apply(); }
      });
    });
  }

  global.KM0AuthI18n = { t: t, apply: apply, getLocale: getLocale };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { bindLang(); apply(); });
  } else { bindLang(); apply(); }
})(window);
