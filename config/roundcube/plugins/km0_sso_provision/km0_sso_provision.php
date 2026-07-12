<?php

/**
 * Silent mailbox auto-provision after Dex LDAP OAuth login.
 * Supports @km0digital.com and verified custom domains; blocks freemail OIDC emails.
 */
class km0_sso_provision extends rcube_plugin
{
    public $task = 'login';

    private static array $freemailDomains = [
        'gmail.com', 'googlemail.com', 'outlook.com', 'hotmail.com', 'live.com',
        'yahoo.com', 'icloud.com', 'proton.me', 'protonmail.com',
    ];

    public function init()
    {
        $this->add_hook('oauth_login', [$this, 'oauth_login']);
    }

    public function oauth_login(array $args): array
    {
        $rcmail = rcmail::get_instance();
        $km0Domain = $rcmail->config->get('km0_mail_domain', 'km0digital.com');
        $email = strtolower(trim($args['identity']['email'] ?? ''));

        if ($email === '') {
            $this->oauth_error('Missing email in OIDC identity.');
            return $args;
        }

        $domain = substr($email, strrpos($email, '@') + 1);
        if (in_array($domain, self::$freemailDomains, true)) {
            $this->oauth_error(
                'Freemail addresses cannot be used for KM0 Mail. Register with @' . $km0Domain . ' or your own domain.'
            );
            return $args;
        }

        if ($domain !== $km0Domain && !$this->is_verified_custom_domain($domain)) {
            $this->oauth_error(
                'Your OIDC email domain is not registered with KM0 Mail. Complete registration first.'
            );
            return $args;
        }

        $opencloud_uuid = $args['identity']['sub'] ?? null;
        $mail_mode = ($domain === $km0Domain) ? 'km0' : 'custom';

        if (!$this->provision_mailbox($email, $opencloud_uuid, $mail_mode)) {
            $this->oauth_error(
                'Could not provision your mailbox. Try again or contact postmaster@' . $km0Domain . '.'
            );
        }

        return $args;
    }

    private function is_verified_custom_domain(string $domain): bool
    {
        $rcmail = rcmail::get_instance();
        $url = rtrim($rcmail->config->get('km0_domain_verify_api_url', ''), '/');
        if ($url === '') {
            return false;
        }

        $ch = curl_init($url . '/domain/' . rawurlencode($domain) . '/status');
        if ($ch === false) {
            return false;
        }
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 10]);
        $body = curl_exec($ch);
        $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($status !== 200 || !$body) {
            return false;
        }
        $data = json_decode($body, true);
        return !empty($data['active']) && ($data['verification_status'] ?? '') === 'verified';
    }

    private function provision_mailbox(string $email, ?string $opencloud_uuid, string $mail_mode): bool
    {
        $rcmail = rcmail::get_instance();
        $url = rtrim($rcmail->config->get('km0_provision_api_url', ''), '/');
        $token = $rcmail->config->get('km0_provision_api_token', '');

        if ($url === '' || $token === '') {
            rcube::write_log('errors', 'km0_sso_provision: provision API not configured');
            return false;
        }

        $payload = json_encode([
            'email' => $email,
            'opencloud_uuid' => $opencloud_uuid,
            'mail_mode' => $mail_mode,
            'send_verification' => ($mail_mode === 'km0'),
        ]);

        $ch = curl_init($url . '/provision');
        if ($ch === false) {
            return false;
        }

        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $payload,
            CURLOPT_HTTPHEADER => [
                'Content-Type: application/json',
                'Authorization: Bearer ' . $token,
            ],
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 30,
        ]);

        $body = curl_exec($ch);
        $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($status === 200 || $status === 201) {
            return true;
        }

        rcube::write_log('errors', 'km0_sso_provision: API status=' . $status . ' body=' . $body);
        return false;
    }

    private function oauth_error(string $message): void
    {
        rcmail::raise_error([
            'code' => 403,
            'type' => 'oauth',
            'message' => $message,
        ], true, true);
    }
}
