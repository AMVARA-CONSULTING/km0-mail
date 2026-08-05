<?php

/**
 * KM0 Mail — self-service custom domains (Phase 2).
 *
 * Adds a "My domains" section to Settings so an authenticated user can add a
 * custom domain, publish DNS, verify it, and create/manage addresses on it.
 *
 * All backend calls are server-to-server (Bearer token) against the internal
 * mail-provision-api and domain-verify-api. The owner is always the session
 * mailbox ($_SESSION['username']); it is never taken from the browser.
 *
 * @version 1.0.0
 * @license MIT
 * @author AMVARA CONSULTING S.L.
 */
class km0_domains extends rcube_plugin
{
    public $task = 'settings';

    private $rc;
    private $prov_url;
    private $verify_url;
    private $token;

    public function init()
    {
        $this->rc = rcmail::get_instance();
        $this->prov_url = rtrim((string) $this->rc->config->get('km0_provision_api_url', ''), '/');
        $this->verify_url = rtrim((string) $this->rc->config->get('km0_domain_verify_api_url', ''), '/');
        $this->token = (string) $this->rc->config->get('km0_provision_api_token', '');

        $this->add_texts('localization/', true);

        // Settings section entry + page.
        $this->add_hook('settings_actions', [$this, 'settings_actions']);
        $this->register_action('plugin.km0_domains', [$this, 'action_index']);

        // JSON endpoints consumed by km0_domains.js (same-origin, session-scoped).
        $this->register_action('plugin.km0_domains.domains', [$this, 'action_domains_list']);
        $this->register_action('plugin.km0_domains.add_domain', [$this, 'action_add_domain']);
        $this->register_action('plugin.km0_domains.del_domain', [$this, 'action_del_domain']);
        $this->register_action('plugin.km0_domains.status', [$this, 'action_domain_status']);
        $this->register_action('plugin.km0_domains.check', [$this, 'action_domain_check']);
        $this->register_action('plugin.km0_domains.addresses', [$this, 'action_addresses_list']);
        $this->register_action('plugin.km0_domains.add_address', [$this, 'action_add_address']);
        $this->register_action('plugin.km0_domains.del_address', [$this, 'action_del_address']);
    }

    public function settings_actions($args)
    {
        $args['actions'][] = [
            'action' => 'plugin.km0_domains',
            'class'  => 'km0domains',
            'label'  => 'domainstitle',
            'domain' => 'km0_domains',
            'title'  => 'domainstitle',
        ];
        return $args;
    }

    public function action_index()
    {
        $this->include_script('km0_domains.js');
        $this->rc->output->set_pagetitle($this->gettext('domainstitle'));
        $this->rc->output->send('km0_domains.domains');
    }

    // --- helpers ---------------------------------------------------------

    private function owner(): string
    {
        return strtolower(trim((string) ($_SESSION['username'] ?? '')));
    }

    private function json($data, int $code = 200): void
    {
        if (!headers_sent()) {
            header('Content-Type: application/json; charset=utf-8', true, $code);
        }
        echo json_encode($data);
        exit;
    }

    private function require_write(): void
    {
        if (!$this->rc->check_request()) {
            $this->json(['error' => 'invalid_request'], 403);
        }
    }

    /**
     * Server-to-server call to an internal API with the shared Bearer token.
     * Returns [http_code, decoded_body|null].
     */
    private function api(string $base, string $path, string $method = 'GET', $payload = null): array
    {
        if ($base === '' || $this->token === '') {
            return [0, null];
        }
        $ch = curl_init($base . $path);
        $headers = ['Authorization: Bearer ' . $this->token];
        $opts = [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 30,
            CURLOPT_CUSTOMREQUEST  => $method,
        ];
        if ($payload !== null) {
            $opts[CURLOPT_POSTFIELDS] = json_encode($payload);
            $headers[] = 'Content-Type: application/json';
        }
        $opts[CURLOPT_HTTPHEADER] = $headers;
        curl_setopt_array($ch, $opts);
        $resp = curl_exec($ch);
        $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        $data = ($resp !== false && $resp !== '') ? json_decode($resp, true) : null;
        return [$code, $data];
    }

    private function owns_domain(string $owner, string $domain): bool
    {
        [$code, $data] = $this->api($this->prov_url, '/my/domains?owner=' . rawurlencode($owner), 'GET');
        if ($code !== 200 || !is_array($data) || empty($data['domains'])) {
            return false;
        }
        foreach ($data['domains'] as $d) {
            if (isset($d['name']) && strtolower($d['name']) === strtolower($domain)) {
                return true;
            }
        }
        return false;
    }

    private function in(string $name, int $mode): string
    {
        return trim((string) rcube_utils::get_input_value($name, $mode));
    }

    // --- actions ---------------------------------------------------------

    public function action_domains_list(): void
    {
        $owner = $this->owner();
        [$code, $data] = $this->api($this->prov_url, '/my/domains?owner=' . rawurlencode($owner), 'GET');
        $this->json($data ?? ['error' => 'upstream'], $code ?: 502);
    }

    public function action_add_domain(): void
    {
        $this->require_write();
        $owner = $this->owner();
        $domain = strtolower($this->in('domain', rcube_utils::INPUT_POST));
        [$code, $data] = $this->api($this->prov_url, '/my/domains', 'POST', ['owner' => $owner, 'domain' => $domain]);
        $this->json($data ?? ['error' => 'upstream'], $code ?: 502);
    }

    public function action_del_domain(): void
    {
        $this->require_write();
        $owner = $this->owner();
        $domain = strtolower($this->in('domain', rcube_utils::INPUT_POST));
        [$code, $data] = $this->api($this->prov_url, '/my/domains/' . rawurlencode($domain) . '?owner=' . rawurlencode($owner), 'DELETE');
        $this->json($data ?? ['error' => 'upstream'], $code ?: 502);
    }

    public function action_domain_status(): void
    {
        $owner = $this->owner();
        $domain = strtolower($this->in('domain', rcube_utils::INPUT_GPC));
        if (!$this->owns_domain($owner, $domain)) {
            $this->json(['error' => 'forbidden'], 403);
        }
        [$code, $data] = $this->api($this->verify_url, '/domain/' . rawurlencode($domain) . '/status', 'GET');
        $this->json($data ?? ['error' => 'upstream'], $code ?: 502);
    }

    public function action_domain_check(): void
    {
        $this->require_write();
        $owner = $this->owner();
        $domain = strtolower($this->in('domain', rcube_utils::INPUT_POST));
        if (!$this->owns_domain($owner, $domain)) {
            $this->json(['error' => 'forbidden'], 403);
        }
        [$code, $data] = $this->api($this->verify_url, '/domain/' . rawurlencode($domain) . '/check', 'POST', []);
        $this->json($data ?? ['error' => 'upstream'], $code ?: 502);
    }

    public function action_addresses_list(): void
    {
        $owner = $this->owner();
        [$code, $data] = $this->api($this->prov_url, '/my/addresses?owner=' . rawurlencode($owner), 'GET');
        $this->json($data ?? ['error' => 'upstream'], $code ?: 502);
    }

    public function action_add_address(): void
    {
        $this->require_write();
        $owner = $this->owner();
        $email = strtolower($this->in('email', rcube_utils::INPUT_POST));
        $password = (string) rcube_utils::get_input_value('password', rcube_utils::INPUT_POST);
        [$code, $data] = $this->api($this->prov_url, '/my/addresses', 'POST', [
            'owner'    => $owner,
            'email'    => $email,
            'password' => $password,
        ]);
        $this->json($data ?? ['error' => 'upstream'], $code ?: 502);
    }

    public function action_del_address(): void
    {
        $this->require_write();
        $owner = $this->owner();
        $email = strtolower($this->in('email', rcube_utils::INPUT_POST));
        [$code, $data] = $this->api($this->prov_url, '/my/addresses/' . rawurlencode($email) . '?owner=' . rawurlencode($owner), 'DELETE');
        $this->json($data ?? ['error' => 'upstream'], $code ?: 502);
    }
}
