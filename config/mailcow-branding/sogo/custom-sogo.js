// KM0 Mail — SOGo custom JS (Mailcow SSO bridge). Do not remove login redirect.
// Source of truth: config/mailcow-branding/sogo/custom-sogo.js → apply script.

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
