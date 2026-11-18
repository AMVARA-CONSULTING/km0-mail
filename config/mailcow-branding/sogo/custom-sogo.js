// KM0 Mail — SOGo custom JS (Mailcow SSO bridge + dark contrast safety net).
// Source of truth: config/mailcow-branding/sogo/custom-sogo.js → apply script.
// Do not remove login redirect.

(function injectKm0SogoContrastCss() {
  if (document.getElementById('km0-sogo-contrast')) {
    return;
  }
  var css = [
    '/* KM0 SOGo coherent dark — belt-and-suspenders over Material tokens */',
    'md-sidenav.md-sidenav-left,',
    'md-sidenav.md-sidenav-left md-content {',
    '  background-color: #0B1220 !important;',
    '  color: #E6E9ED !important;',
    '}',
    'md-sidenav .sg-mailbox-list-item,',
    'md-sidenav md-list-item,',
    'md-sidenav .sg-item-name,',
    'md-sidenav .sg-no-wrap,',
    'md-sidenav .md-caption,',
    'md-sidenav .sg-md-title,',
    'md-sidenav .sg-md-caption,',
    'md-sidenav p {',
    '  color: #E6E9ED !important;',
    '}',
    'md-sidenav .sg-mailbox-list-item.sg-selected,',
    'md-sidenav md-list-item.sg-selected {',
    '  background-color: rgba(45, 212, 191, 0.18) !important;',
    '}',
    'md-sidenav .sg-counter-badge,',
    'md-sidenav .md-accent {',
    '  color: #2DD4BF !important;',
    '}',
    '#messagesList,',
    '.view-list,',
    '.view-list md-content {',
    '  background-color: #141B28 !important;',
    '  color: #E6E9ED !important;',
    '}',
    '.view-list .sg-tile-subject,',
    '.view-list .sg-tile-content,',
    '.view-list .msg-date,',
    '.view-list md-list-item {',
    '  color: #E6E9ED !important;',
    '}',
    'md-content .sg-md-title {',
    '  color: #E6E9ED !important;',
    '}',
    /* Empty preview / no-mailbox panes use background-200 + title */
    'md-content[md-colors] .sg-md-title,',
    'section md-content .sg-md-title {',
    '  color: #E6E9ED !important;',
    '}',
    'md-toolbar.md-hue-2 .sg-md-title,',
    'md-toolbar.md-hue-2 .md-caption,',
    'md-toolbar.md-hue-2 p {',
    '  color: #E6E9ED !important;',
    '}'
  ].join('\n');
  var style = document.createElement('style');
  style.id = 'km0-sogo-contrast';
  style.type = 'text/css';
  style.appendChild(document.createTextNode(css));
  (document.head || document.documentElement).appendChild(style);
})();

// Redirect SOGo's own login form to Mailcow user login (preserves /sogo-auth SSO).
document.addEventListener('DOMContentLoaded', function () {
  var loginForm = document.forms.namedItem('loginForm');
  if (loginForm) {
    window.location.href = '/user';
  }
});

// Logout back through Mailcow session
function mc_logout() {
  fetch('/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: 'logout=1'
  }).then(function () {
    window.location.href = '/';
  });
}

// Compose editor readability
CKEDITOR.addCss('body {font-size: 16px !important; font-family: "IBM Plex Sans", system-ui, sans-serif !important}');
