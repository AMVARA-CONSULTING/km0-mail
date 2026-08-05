<?php

/**
 * Show verification banner for pending mailboxes (Model A).
 *
 * @version 1.0.0
 * @license MIT
 * @author AMVARA CONSULTING S.L.
 */
class km0_verification_banner extends rcube_plugin
{
    public $task = 'mail';

    public function init()
    {
        $this->add_hook('render_page', [$this, 'render_banner']);
    }

    public function render_banner(array $args): array
    {
        $rcmail = rcmail::get_instance();
        if ($rcmail->task !== 'mail' || empty($_SESSION['username'])) {
            return $args;
        }

        $email = $_SESSION['username'];
        $status = $this->fetch_status($email);
        if ($status !== 'pending') {
            return $args;
        }

        $msg = $rcmail->gettext('km0_verify_banner', 'km0_verification_banner');
        if ($msg === 'km0_verify_banner') {
            $msg = 'Confirm your account: check your inbox for the verification email. Outbound send is disabled until verified.';
        }

        $rcmail->output->add_footer(html::div(
            ['class' => 'km0-verify-banner', 'role' => 'alert'],
            rcube::Q($msg)
        ));

        return $args;
    }

    private function fetch_status(string $email): ?string
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
        $body = curl_exec($ch);
        $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($code !== 200 || !$body) {
            return null;
        }
        $data = json_decode($body, true);
        return $data['verification_status'] ?? null;
    }
}
