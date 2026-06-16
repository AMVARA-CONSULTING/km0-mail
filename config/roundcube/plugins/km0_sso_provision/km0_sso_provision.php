<?php

/**
 * Silent mailbox auto-provision after Dex OAuth login (@km0digital.com only).
 */
class km0_sso_provision extends rcube_plugin
{
    public $task = 'login';

    public function init()
    {
        $this->add_hook('oauth_login', [$this, 'oauth_login']);
    }

    public function oauth_login(array $args): array
    {
        $rcmail = rcmail::get_instance();
        $domain = $rcmail->config->get('km0_mail_domain', 'km0digital.com');
        $email = strtolower(trim($args['identity']['email'] ?? ''));

        if ($email === '' || !preg_match('/@' . preg_quote($domain, '/') . '$/i', $email)) {
            rcmail::raise_error([
                'code' => 403,
                'type' => 'oauth',
                'message' => sprintf(
                    'Use an @%s address. Register at /register or sign in with the correct Google account.',
                    $domain
                ),
            ], true, true);
            return $args;
        }

        $opencloud_uuid = $args['identity']['sub'] ?? null;
        if (!$this->provision_mailbox($email, $opencloud_uuid)) {
            rcmail::raise_error([
                'code' => 503,
                'type' => 'oauth',
                'message' => 'Could not provision your mailbox. Try again or contact postmaster@km0digital.com.',
            ], true, true);
        }

        return $args;
    }

    private function provision_mailbox(string $email, ?string $opencloud_uuid): bool
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
}
