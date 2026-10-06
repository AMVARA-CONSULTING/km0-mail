<?php

/**
 * Mail login after Keycloak.
 * Only domains this mail server accepts may open a mailbox. Any other
 * domain is sent to the cloud and is not given mail access.
 *
 * @version 1.0.0
 * @license MIT
 * @author AMVARA CONSULTING S.L.
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
        $km0Domain = strtolower($rcmail->config->get('km0_mail_domain', 'km0digital.com'));
        $email = strtolower(trim($args['identity']['email'] ?? ''));
        $domain = '';
        if ($email !== '' && str_contains($email, '@')) {
            $domain = substr($email, strrpos($email, '@') + 1);
        }

        $exists = ($email !== '') ? $this->mailbox_exists($email) : false;
        if ($exists === null) {
            $this->oauth_error('Could not check the mailbox. Try again in a moment.');
            return $args;
        }

        // Gmail, Outlook, and any domain this server does not accept go to
        // the cloud. An address that already has a mailbox stays on mail,
        // including a domain row that is still pending.
        $accepted = $domain !== '' && $this->domain_is_accepted($domain, $km0Domain);
        if ($exists !== true && !$accepted) {
            $this->send_to_cloud();
        }

        $roles = $args['identity']['realm_access']['roles'] ?? [];
        if (is_string($roles)) {
            $roles = [$roles];
        }
        if (!in_array('km0MailUser', $roles, true)) {
            $this->oauth_error('This account does not have mail access.');
            return $args;
        }

        // Existing mailbox: do not call /provision. That call generates a new
        // password hash and would also reject a Keycloak user id that differs
        // from the stored cloud id.
        if ($exists === true) {
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

    /**
     * @return bool|null true if the mailbox row exists, false if it does not, null if the check failed
     */
    private function mailbox_exists(string $email): ?bool
    {
        $rcmail = rcmail::get_instance();
        $url = rtrim($rcmail->config->get('km0_provision_api_url', ''), '/');
        if ($url === '') {
            return null;
        }

        $ch = curl_init($url . '/account/' . rawurlencode($email) . '/status');
        if ($ch === false) {
            return null;
        }
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 10]);
        curl_exec($ch);
        $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($status === 200) {
            return true;
        }
        if ($status === 404) {
            return false;
        }
        return null;
    }

    private function domain_is_accepted(string $domain, string $km0Domain): bool
    {
        if (in_array($domain, self::$freemailDomains, true)) {
            return false;
        }
        if ($domain === $km0Domain) {
            return true;
        }
        return $this->is_verified_custom_domain($domain);
    }

    private function send_to_cloud(): void
    {
        $rcmail = rcmail::get_instance();
        $url = $rcmail->config->get('km0_cloud_url', 'https://cloud.km0digital.com/');
        header('Location: ' . $url, true, 302);
        exit;
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
