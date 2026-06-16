(function (global) {
  'use strict';

  var OIDC_SCOPE = 'openid profile email';
  var DEX_AUTHORITY = 'https://cloud.km0digital.com/dex';
  var OAUTH_CLIENT_ID = 'km0-mail-web';
  var OAUTH_REDIRECT_URI = location.origin + '/index.php/login/oauth';

  function clearOidcBrowserState() {
    var pat = /^oidc\.|^oidc\.user:/i;
    try {
      Object.keys(sessionStorage).forEach(function (k) {
        if (pat.test(k)) sessionStorage.removeItem(k);
      });
    } catch (_) {}
    try {
      Object.keys(localStorage).forEach(function (k) {
        if (pat.test(k)) localStorage.removeItem(k);
      });
    } catch (_) {}
  }

  function base64url(buf) {
    return btoa(String.fromCharCode.apply(null, new Uint8Array(buf)))
      .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
  }

  function randomHex(bytes) {
    var a = new Uint8Array(bytes);
    crypto.getRandomValues(a);
    return Array.from(a, function (b) { return ('0' + b.toString(16)).slice(-2); }).join('');
  }

  function generatePKCE() {
    var arr = new Uint8Array(32);
    crypto.getRandomValues(arr);
    var verifier = base64url(arr.buffer);
    return crypto.subtle
      .digest('SHA-256', new TextEncoder().encode(verifier))
      .then(function (hash) { return { verifier: verifier, challenge: base64url(hash) }; });
  }

  function storeSigninState(state, authority, clientId, redirectUri, codeVerifier) {
    try {
      localStorage.setItem('oidc.' + state, JSON.stringify({
        id: state,
        created: Math.floor(Date.now() / 1000),
        request_type: 'si:r',
        code_verifier: codeVerifier,
        redirect_uri: redirectUri,
        authority: authority,
        client_id: clientId,
        scope: OIDC_SCOPE,
        extraTokenParams: {},
        skipUserInfo: false
      }));
    } catch (_) {}
  }

  function startDexLogin(connectorId) {
    clearOidcBrowserState();

    generatePKCE().then(function (pkce) {
      var state = randomHex(16);
      storeSigninState(state, DEX_AUTHORITY, OAUTH_CLIENT_ID, OAUTH_REDIRECT_URI, pkce.verifier);
      location.assign(DEX_AUTHORITY + '/auth?' + new URLSearchParams({
        client_id:             OAUTH_CLIENT_ID,
        redirect_uri:          OAUTH_REDIRECT_URI,
        response_type:         'code',
        scope:                 OIDC_SCOPE,
        connector_id:          connectorId,
        state:                 state,
        code_challenge:        pkce.challenge,
        code_challenge_method: 'S256'
      }).toString());
    });
  }

  var PENDING_LOGIN_KEY = 'km0_pending_login';
  var PENDING_LOGIN_TTL_MS = 120000;

  function storePendingLogin(login, password) {
    try {
      sessionStorage.setItem(PENDING_LOGIN_KEY, JSON.stringify({
        login: login,
        password: password,
        exp: Date.now() + PENDING_LOGIN_TTL_MS
      }));
    } catch (_) {}
  }

  global.KM0DexAuth = {
    startDexLogin: startDexLogin,
    clearOidcBrowserState: clearOidcBrowserState,
    storePendingLogin: storePendingLogin
  };
})(window);
