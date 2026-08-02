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
      loginIntro: 'Sign in with your mailbox email and password.',
      ldapButton: 'Sign in with OpenCloud / LDAP',
      passwordButton: 'Sign in with email and password',
      landingOtherWays: 'Other ways to sign in',
      registerLink: 'Create a free account',
      registerSuccessBanner: 'Account created. Sign in below, then open the verification email in your inbox and click the link. Sending is disabled until you verify.',
      registerTitle: 'Create account',
      registerIntro: 'Pick a username and password. We create your @km0digital.com address instantly.',
      modeKm0: '@km0digital.com',
      modeCustom: 'My domain',
      emailLabel: 'Email address',
      usernameLabel: 'Username',
      usernameSuffix: '@km0digital.com',
      passwordLabel: 'Password',
      passwordConfirmLabel: 'Confirm password',
      contactLabel: 'Contact email (optional)',
      submitRegister: 'Create account',
      signInLink: 'Already have an account?',
      ldapHint: 'Uses your OpenCloud / LDAP account (brief redirect to cloud.km0digital.com).',
      errorUsernameRequired: 'Username is required.',
      errorEmailRequired: 'Email address is required.',
      registerErrorPasswordMismatch: 'Passwords do not match.',
      registerErrorPasswordWeak: 'Password must be at least 8 characters and include a special character.',
      registerErrorEmailInvalid: 'Enter a valid email address.',
      registerErrorDuplicate: 'This address is already registered. Sign in instead.',
      registerErrorValidation: 'Could not validate your details. Check the fields and try again.',
      registerErrorServiceUnavailable: 'Registration is temporarily unavailable. Try again later.',
      registerErrorRateLimit: 'Too many attempts. Wait a minute and try again.',
      registerErrorGeneric: 'Could not create account. Please try again later.',
      registerErrorFreemailMailbox: 'KM0 Mail cannot use Gmail, Outlook, or other freemail domains as a mailbox. Use @km0digital.com or your own domain.',
      registerErrorInvalidDomain: 'Invalid domain for this registration mode.',
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
      loginIntro: 'Inicia sesión con el correo y la contraseña de tu buzón.',
      ldapButton: 'Iniciar sesión con OpenCloud / LDAP',
      passwordButton: 'Iniciar sesión con correo y contraseña',
      landingOtherWays: 'Otras formas de acceder',
      registerLink: 'Crear cuenta gratuita',
      registerSuccessBanner: 'Cuenta creada. Inicia sesión, abre el correo de verificación en tu bandeja y haz clic en el enlace. El envío está desactivado hasta que verifiques.',
      registerTitle: 'Crear cuenta',
      registerIntro: 'Elige un usuario y una contraseña. Creamos tu dirección @km0digital.com al instante.',
      modeKm0: '@km0digital.com',
      modeCustom: 'Mi dominio',
      emailLabel: 'Correo electrónico',
      usernameLabel: 'Usuario',
      usernameSuffix: '@km0digital.com',
      passwordLabel: 'Contraseña',
      passwordConfirmLabel: 'Confirmar contraseña',
      contactLabel: 'Correo de contacto (opcional)',
      submitRegister: 'Crear cuenta',
      signInLink: '¿Ya tienes cuenta?',
      ldapHint: 'Usa tu cuenta OpenCloud / LDAP (redirección breve a cloud.km0digital.com).',
      errorUsernameRequired: 'El usuario es obligatorio.',
      errorEmailRequired: 'El correo electrónico es obligatorio.',
      registerErrorPasswordMismatch: 'Las contraseñas no coinciden.',
      registerErrorPasswordWeak: 'La contraseña debe tener al menos 8 caracteres e incluir un carácter especial.',
      registerErrorEmailInvalid: 'Introduce un correo electrónico válido.',
      registerErrorDuplicate: 'Esta dirección ya está registrada. Inicia sesión.',
      registerErrorValidation: 'No se pudieron validar los datos. Comprueba los campos.',
      registerErrorServiceUnavailable: 'El registro no está disponible temporalmente. Inténtalo más tarde.',
      registerErrorRateLimit: 'Demasiados intentos. Espera un minuto e inténtalo de nuevo.',
      registerErrorGeneric: 'No se pudo crear la cuenta. Inténtalo de nuevo más tarde.',
      registerErrorFreemailMailbox: 'KM0 Mail no admite Gmail, Outlook u otros correos gratuitos como buzón. Usa @km0digital.com o tu dominio propio.',
      registerErrorInvalidDomain: 'Dominio no válido para este modo de registro.',
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
      loginIntro: 'Inicia sessió amb el correu i la contrasenya de la teva bústia.',
      ldapButton: 'Iniciar sessió amb OpenCloud / LDAP',
      passwordButton: 'Iniciar sessió amb correu i contrasenya',
      landingOtherWays: 'Altres formes d\'accedir',
      registerLink: 'Crear compte gratuït',
      registerSuccessBanner: 'Compte creat. Inicia sessió, obre el correu de verificació a la teva bústia i fes clic a l\'enllaç. L\'enviament està desactivat fins que verifiquis.',
      registerTitle: 'Crear compte',
      registerIntro: 'Tria un usuari i una contrasenya. Creem la teva adreça @km0digital.com a l\'instant.',
      modeKm0: '@km0digital.com',
      modeCustom: 'El meu domini',
      emailLabel: 'Adreça de correu',
      usernameLabel: 'Usuari',
      usernameSuffix: '@km0digital.com',
      passwordLabel: 'Contrasenya',
      passwordConfirmLabel: 'Confirmar contrasenya',
      contactLabel: 'Correu de contacte (opcional)',
      submitRegister: 'Crear compte',
      signInLink: 'Ja tens compte?',
      ldapHint: 'Fes servir el compte OpenCloud / LDAP (redirecció breu a cloud.km0digital.com).',
      errorUsernameRequired: 'L\'usuari és obligatori.',
      errorEmailRequired: 'El correu electrònic és obligatori.',
      registerErrorPasswordMismatch: 'Les contrasenyes no coincideixen.',
      registerErrorPasswordWeak: 'La contrasenya ha de tenir almenys 8 caràcters i incloure un caràcter especial.',
      registerErrorEmailInvalid: 'Introdueix un correu electrònic vàlid.',
      registerErrorDuplicate: 'Aquesta adreça ja està registrada. Inicia sessió.',
      registerErrorValidation: 'No s\'han pogut validar les dades. Comprova els camps.',
      registerErrorServiceUnavailable: 'El registre no està disponible temporalment. Torna-ho a provar més tard.',
      registerErrorRateLimit: 'Massa intents. Espera un minut i torna-ho a provar.',
      registerErrorGeneric: 'No s\'ha pogut crear el compte. Torna-ho a provar més tard.',
      registerErrorFreemailMailbox: 'KM0 Mail no admet Gmail, Outlook ni altres correus gratuïts com a bústia. Fes servir @km0digital.com o el teu domini.',
      registerErrorInvalidDomain: 'Domini no vàlid per a aquest mode de registre.',
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
      loginIntro: 'Melden Sie sich mit E-Mail und Passwort Ihres Postfachs an.',
      ldapButton: 'Mit OpenCloud / LDAP anmelden',
      passwordButton: 'Mit E-Mail und Passwort anmelden',
      landingOtherWays: 'Weitere Anmeldeoptionen',
      registerLink: 'Kostenloses Konto erstellen',
      registerSuccessBanner: 'Konto erstellt. Melden Sie sich an, öffnen Sie die Bestätigungs-E-Mail im Postfach und klicken Sie auf den Link. Der Versand ist bis zur Bestätigung deaktiviert.',
      registerTitle: 'Konto erstellen',
      registerIntro: 'Wählen Sie einen Benutzernamen und ein Passwort. Wir erstellen sofort Ihre @km0digital.com-Adresse.',
      modeKm0: '@km0digital.com',
      modeCustom: 'Eigene Domain',
      emailLabel: 'E-Mail-Adresse',
      usernameLabel: 'Benutzername',
      usernameSuffix: '@km0digital.com',
      passwordLabel: 'Passwort',
      passwordConfirmLabel: 'Passwort bestätigen',
      contactLabel: 'Kontakt-E-Mail (optional)',
      submitRegister: 'Konto erstellen',
      signInLink: 'Bereits ein Konto?',
      ldapHint: 'Nutzt Ihr OpenCloud- / LDAP-Konto (kurze Weiterleitung zu cloud.km0digital.com).',
      errorUsernameRequired: 'Benutzername ist erforderlich.',
      errorEmailRequired: 'E-Mail-Adresse ist erforderlich.',
      registerErrorPasswordMismatch: 'Passwörter stimmen nicht überein.',
      registerErrorPasswordWeak: 'Passwort muss mindestens 8 Zeichen und ein Sonderzeichen enthalten.',
      registerErrorEmailInvalid: 'Geben Sie eine gültige E-Mail-Adresse ein.',
      registerErrorDuplicate: 'Diese Adresse ist bereits registriert. Bitte anmelden.',
      registerErrorValidation: 'Daten konnten nicht validiert werden. Felder prüfen.',
      registerErrorServiceUnavailable: 'Registrierung vorübergehend nicht verfügbar. Später erneut versuchen.',
      registerErrorRateLimit: 'Zu viele Versuche. Eine Minute warten und erneut versuchen.',
      registerErrorGeneric: 'Konto konnte nicht erstellt werden. Bitte später erneut versuchen.',
      registerErrorFreemailMailbox: 'KM0 Mail unterstützt Gmail, Outlook und andere Freemail-Domains nicht als Postfach. Nutze @km0digital.com oder deine eigene Domain.',
      registerErrorInvalidDomain: 'Ungültige Domain für diesen Registrierungsmodus.',
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

  function detectBrowserLocale() {
    if (typeof navigator === 'undefined' || !navigator.language) return DEFAULT;
    var langs = navigator.languages || [navigator.language];
    for (var i = 0; i < langs.length; i++) {
      var loc = norm(langs[i]);
      if (loc) return loc;
    }
    return DEFAULT;
  }

  function getLocale() {
    try {
      var q = new URLSearchParams(location.search).get('lang');
      var fromQ = norm(q);
      if (fromQ) { localStorage.setItem(STORAGE_KEY, fromQ); return fromQ; }
      return norm(localStorage.getItem(STORAGE_KEY)) || detectBrowserLocale();
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
