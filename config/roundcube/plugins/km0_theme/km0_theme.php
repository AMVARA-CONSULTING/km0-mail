<?php

/**
 * km0_theme — forces the Elastic dark base on every page.
 *
 * km0-web is dark-only, and the km0 skin re-tints the Elastic *dark* layer
 * (skins/km0/styles/km0-app.css) to the km0 design tokens. Enabling dark mode
 * normally depends on a cookie or the visitor's OS preference; this plugin adds
 * the `dark-mode` class to <html> during head render (FOUC-free) so the re-tint
 * always applies. No styling lives here — the look belongs to the skin.
 */
class km0_theme extends rcube_plugin
{
    public function init()
    {
        $this->add_hook('render_page', [$this, 'force_dark']);
    }

    public function force_dark(array $args): array
    {
        rcmail::get_instance()->output->add_header(
            '<script>try{document.documentElement.classList.add("dark-mode");}catch(e){}</script>'
        );

        return $args;
    }
}
