<?php

$config = [];

// Database (required when config.inc.php is bind-mounted over the image default)
$config['db_dsnw'] = sprintf(
    'pgsql://%s:%s@%s/%s',
    getenv('ROUNDCUBEMAIL_DB_USER') ?: 'roundcube',
    getenv('ROUNDCUBEMAIL_DB_PASSWORD') ?: '',
    getenv('ROUNDCUBEMAIL_DB_HOST') ?: 'postgres',
    getenv('ROUNDCUBEMAIL_DB_NAME') ?: 'roundcube'
);

// IMAP — internal Docker TLS (self-signed or LE-mounted)
$config['imap_host'] = 'ssl://dovecot:993';
$config['imap_conn_options'] = [
    'ssl' => [
        'verify_peer' => false,
        'verify_peer_name' => false,
    ],
];

// SMTP submission (password or XOAUTH2 when OAuth session active)
$config['smtp_host'] = 'tls://postfix:587';
$config['smtp_user'] = '%u';
$config['smtp_pass'] = '%p';
$config['smtp_conn_options'] = [
    'ssl' => [
        'verify_peer' => false,
        'verify_peer_name' => false,
    ],
];

$config['skin'] = 'km0';
$config['language'] = 'en_US';
$config['support_url'] = 'https://km0digital.com/';
$config['product_name'] = 'KM0 Mail';
$config['des_key'] = getenv('ROUNDCUBEMAIL_DES_KEY') ?: 'change-me';
$config['plugins'] = ['archive', 'zipdownload', 'km0_sso_provision', 'km0_verification_banner', 'km0_domains'];

// Session security behind Nginx HTTPS
$config['force_https'] = true;
$config['use_https'] = true;
$config['proxy_whitelist'] = ['127.0.0.1', '::1'];

// Single, Proton-style login: native email+password only. OAuth disabled so the
// "Login with KM0 Mail" button never appears (it caused a Dex redirect loop).
// The oauth_* settings below are kept inert for a possible future opt-in; leaving
// oauth_provider null means Roundcube renders no OAuth button and uses SQL passdb.
$config['oauth_provider'] = null;
$config['oauth_provider_name'] = 'KM0 Mail';
$config['oauth_client_id'] = getenv('ROUNDCUBE_OAUTH_CLIENT_ID') ?: 'km0-mail-web';
$config['oauth_client_secret'] = getenv('ROUNDCUBE_OAUTH_CLIENT_SECRET') ?: '';
$config['oauth_config_uri'] = getenv('DEX_OIDC_DISCOVERY_URL')
    ?: 'https://cloud.km0digital.com/dex/.well-known/openid-configuration';
$config['oauth_scope'] = 'openid profile email';
$config['oauth_identity_fields'] = ['email'];
$config['oauth_verify_peer'] = true;
$config['oauth_auth_uri'] = 'https://cloud.km0digital.com/dex/auth';
$config['oauth_token_uri'] = 'https://cloud.km0digital.com/dex/token';
$config['oauth_auth_parameters'] = ['connector_id' => 'ldap'];
$config['oauth_cache'] = 'db';
$config['oauth_login_redirect'] = false;

// Branded entry at /login.html; silent mailbox auto-provision via plugin
$config['km0_mail_domain'] = getenv('MAIL_DOMAIN') ?: 'km0digital.com';
$config['km0_provision_api_url'] = getenv('KM0_PROVISION_API_URL') ?: 'http://mail-provision-api:8092';
$config['km0_provision_api_token'] = getenv('MAIL_PROVISION_API_TOKEN') ?: '';
$config['km0_domain_verify_api_url'] = getenv('KM0_DOMAIN_VERIFY_API_URL') ?: 'http://domain-verify-api:8093';
