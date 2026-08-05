<?php

/**
 * km0_theme — forces the Elastic dark base on every page, and soft-brands
 * a few Roundcube chrome details that aren't skin-overridable.
 *
 * - Adds `dark-mode` to <html> during head render (FOUC-free) so km0-app.css
 *   (which re-tints the Elastic dark layer) always applies. km0 is dark-only.
 * - Rewrites the page-title separator from Roundcube's hardcoded " :: " to
 *   " - " (e.g. "KM0 Mail - Compose") via the send_page hook, plus a tiny
 *   client patch for titles updated later by JS.
 *
 * @version 1.0.0
 * @license MIT
 * @author AMVARA CONSULTING S.L.
 */
class km0_theme extends rcube_plugin
{
    public function init()
    {
        $this->add_hook('render_page', [$this, 'force_dark']);
        $this->add_hook('send_page', [$this, 'fix_title_separator']);
    }

    public function force_dark(array $args): array
    {
        $rc = rcmail::get_instance();

        // FOUC-free dark base for the skin re-tint.
        $rc->output->add_header(
            '<script>try{document.documentElement.classList.add("dark-mode");}catch(e){}</script>'
        );

        // Keep document.title in sync when Roundcube updates it client-side
        // (unread counts, AJAX navigation). Initial <title> is fixed in send_page.
        $rc->output->add_footer(
            '<script>(function(){function f(t){return String(t||"").split(" :: ").join(" - ");}'
            . 'try{if(document.title)document.title=f(document.title);}'
            . 'catch(e){}'
            . 'function p(){if(!window.rcmail||typeof rcmail.set_pagetitle!=="function"||rcmail.__km0TitlePatched)return;'
            . 'rcmail.__km0TitlePatched=true;var o=rcmail.set_pagetitle.bind(rcmail);'
            . 'rcmail.set_pagetitle=function(t){return o(f(t));};}'
            . 'p();if(window.rcmail)rcmail.addEventListener("init",p);'
            . '})();</script>'
        );

        return $args;
    }

    /**
     * Roundcube hardcodes " :: " in get_pagetitle(); rewrite the final <title>.
     */
    public function fix_title_separator(array $args): array
    {
        if (!empty($args['content'])) {
            $args['content'] = preg_replace_callback(
                '/(<title[^>]*>)(.*?)(<\/title>)/is',
                static function (array $m): string {
                    return $m[1] . str_replace(' :: ', ' - ', $m[2]) . $m[3];
                },
                $args['content'],
                1
            );
        }

        return $args;
    }
}
