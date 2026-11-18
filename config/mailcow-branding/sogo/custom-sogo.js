// KM0 Mail — SOGo custom JS (Mailcow SSO bridge + dark contrast safety net).
// Source of truth: config/mailcow-branding/sogo/custom-sogo.js → apply script.
// Do not remove login redirect.

(function injectKm0SogoContrastCss() {
  if (document.getElementById('km0-sogo-contrast')) {
    return;
  }
  var css = [
    '/* KM0 SOGo coherent dark — force readable folder rows + icons */',
    'md-sidenav.md-sidenav-left,',
    'md-sidenav.md-sidenav-left md-content {',
    '  background-color: #0B1220 !important;',
    '  color: #E6E9ED !important;',
    '}',
    /* Folder rows: text AND Material Icons were left at rgba(0,0,0,.54) */
    'md-sidenav.md-sidenav-left md-list-item,',
    'md-sidenav.md-sidenav-left md-list-item .md-button,',
    'md-sidenav.md-sidenav-left md-list-item .md-list-item-inner,',
    'md-sidenav.md-sidenav-left md-list-item .sg-item-name,',
    'md-sidenav.md-sidenav-left md-list-item .sg-no-wrap,',
    'md-sidenav.md-sidenav-left md-list-item span,',
    'md-sidenav.md-sidenav-left md-list-item div,',
    'md-sidenav.md-sidenav-left md-list-item p,',
    'md-sidenav.md-sidenav-left md-list-item .md-caption,',
    'md-sidenav.md-sidenav-left .sg-mailbox-list-item,',
    'md-sidenav.md-sidenav-left .sg-md-title,',
    'md-sidenav.md-sidenav-left .sg-md-caption {',
    '  color: #E6E9ED !important;',
    '  opacity: 1 !important;',
    '}',
    'md-sidenav.md-sidenav-left md-icon,',
    'md-sidenav.md-sidenav-left .material-icons,',
    'md-sidenav.md-sidenav-left md-list-item md-icon,',
    'md-sidenav.md-sidenav-left md-list-item .material-icons {',
    '  color: #E6E9ED !important;',
    '  fill: #E6E9ED !important;',
    '  opacity: 1 !important;',
    '}',
    'md-sidenav.md-sidenav-left md-list-item.sg-selected,',
    'md-sidenav.md-sidenav-left md-list-item.sg-selected .md-button,',
    'md-sidenav.md-sidenav-left .sg-mailbox-list-item.sg-selected {',
    '  background-color: rgba(45, 212, 191, 0.18) !important;',
    '}',
    'md-sidenav.md-sidenav-left md-list-item.sg-selected,',
    'md-sidenav.md-sidenav-left md-list-item.sg-selected * {',
    '  color: #5EEAD4 !important;',
    '}',
    'md-sidenav.md-sidenav-left md-list-item.sg-selected md-icon,',
    'md-sidenav.md-sidenav-left md-list-item.sg-selected .material-icons {',
    '  color: #2DD4BF !important;',
    '  fill: #2DD4BF !important;',
    '}',
    'md-sidenav.md-sidenav-left .sg-counter-badge {',
    '  color: #2DD4BF !important;',
    '}',
    /* Profile / quota block */
    'md-sidenav.md-sidenav-left md-toolbar,',
    'md-sidenav.md-sidenav-left md-toolbar .sg-md-title,',
    'md-sidenav.md-sidenav-left md-toolbar .md-caption,',
    'md-sidenav.md-sidenav-left md-toolbar p {',
    '  color: #E6E9ED !important;',
    '}',
    /* Message list pane */
    '#messagesList,',
    '.view-list,',
    '.view-list md-content {',
    '  background-color: #141B28 !important;',
    '  color: #E6E9ED !important;',
    '}',
    '.view-list .sg-tile-subject,',
    '.view-list .sg-tile-content,',
    '.view-list .msg-date,',
    '.view-list md-list-item,',
    '.view-list md-list-item * {',
    '  color: #E6E9ED !important;',
    '}',
    /* Kill white list toolbar island */
    '#messagesList > md-toolbar,',
    '.view-list > md-toolbar,',
    'md-content.view-list > md-toolbar,',
    '.sg-mail-list md-toolbar {',
    '  background-color: #0F766E !important;',
    '  color: #E6E9ED !important;',
    '}',
    '#messagesList > md-toolbar *,',
    '.view-list > md-toolbar *,',
    '#messagesList > md-toolbar md-icon,',
    '.view-list > md-toolbar md-icon {',
    '  color: #E6E9ED !important;',
    '  fill: #E6E9ED !important;',
    '}',
    '#messagesList > md-toolbar input,',
    '.view-list > md-toolbar input {',
    '  background-color: #141B28 !important;',
    '  color: #E6E9ED !important;',
    '}',
    /* Empty preview */
    'md-content .sg-md-title,',
    'md-content[md-colors] .sg-md-title,',
    'section md-content .sg-md-title {',
    '  color: #E6E9ED !important;',
    '}'
  ].join('\n');
  var style = document.createElement('style');
  style.id = 'km0-sogo-contrast';
  style.type = 'text/css';
  style.appendChild(document.createTextNode(css));
  (document.head || document.documentElement).appendChild(style);
})();

document.addEventListener('DOMContentLoaded', function () {
  var loginForm = document.forms.namedItem('loginForm');
  if (loginForm) {
    window.location.href = '/user';
  }
});

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

CKEDITOR.addCss('body {font-size: 16px !important; font-family: "IBM Plex Sans", system-ui, sans-serif !important}');
