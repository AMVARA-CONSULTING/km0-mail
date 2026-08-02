/* KM0 Mail — self-service custom domains (Settings > My domains). */
(function () {
  'use strict';

  function t(key) {
    return rcmail.gettext(key, 'km0_domains');
  }

  function parse(res) {
    return res
      .json()
      .then(function (body) { return { status: res.status, body: body }; })
      .catch(function () { return { status: res.status, body: null }; });
  }

  function apiGet(action, params) {
    var q = new URLSearchParams(params || {});
    var qs = q.toString();
    return fetch('?_task=settings&_action=plugin.km0_domains.' + action + (qs ? '&' + qs : ''), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin'
    }).then(parse);
  }

  function apiPost(action, params) {
    var body = new URLSearchParams();
    body.append('_token', rcmail.env.request_token);
    Object.keys(params || {}).forEach(function (k) { body.append(k, params[k]); });
    return fetch('?_task=settings&_action=plugin.km0_domains.' + action, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest'
      },
      credentials: 'same-origin',
      body: body.toString()
    }).then(parse);
  }

  function errLabel(status, body) {
    var e = (body && body.error) || '';
    var map = {
      invalid_domain: 'errInvalidDomain',
      domain_taken: 'errDomainTaken',
      forbidden: 'errForbidden',
      domain_not_active: 'errDomainNotActive',
      conflict: 'errDuplicate',
      email_already_linked: 'errDuplicate',
      password_too_short: 'errPasswordShort',
      invalid_email: 'errInvalidEmail',
      invalid_local_part: 'errInvalidEmail',
      rate_limited: 'errRateLimit'
    };
    if (status === 429) return t('errRateLimit');
    return t(map[e] || 'errGeneric');
  }

  function showMsg(text, isError) {
    var el = document.getElementById('km0d-msg');
    if (!el) return;
    el.textContent = text;
    el.hidden = false;
    el.className = 'km0d-msg banner ' + (isError ? 'banner--error' : 'banner--success');
    if (!isError) {
      window.setTimeout(function () { el.hidden = true; }, 4000);
    }
  }

  function el(tag, attrs, text) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    if (text != null) n.textContent = text;
    return n;
  }

  function button(label, cls) {
    return el('button', { type: 'button', class: 'btn btn-sm ' + (cls || 'btn-secondary') }, label);
  }

  function renderDnsTable(dns, checks) {
    var wrap = el('div', { class: 'km0d-dns' });
    wrap.appendChild(el('p', null, t('dnsIntro')));
    var table = el('table');
    var thead = el('tr');
    [t('colType'), t('colHost'), t('colValue')].forEach(function (h) { thead.appendChild(el('th', null, h)); });
    table.appendChild(thead);
    var rows = [
      ['TXT', dns.txt.host, dns.txt.value, checks && checks.txt_verified],
      ['MX (10)', dns.mx.host, dns.mx.value, checks && checks.mx_verified],
      ['TXT (SPF)', dns.spf.host, dns.spf.value, checks && checks.spf_verified],
      ['TXT (DKIM)', dns.dkim.host, dns.dkim.value, checks && checks.dkim_verified]
    ];
    rows.forEach(function (r) {
      var tr = el('tr');
      tr.appendChild(el('td', null, r[0] + (r[3] ? ' \u2713' : '')));
      tr.appendChild(el('td', null, r[1]));
      var td = el('td');
      var code = el('code', null, r[2]);
      var copy = el('span', { class: 'km0d-copy', title: t('btnCopy') }, ' \u29C9');
      copy.addEventListener('click', function () {
        if (navigator.clipboard) navigator.clipboard.writeText(r[2]);
        showMsg(t('copied'), false);
      });
      td.appendChild(code);
      td.appendChild(copy);
      tr.appendChild(td);
      table.appendChild(tr);
    });
    wrap.appendChild(table);
    return wrap;
  }

  function openDns(domain, detail) {
    detail.innerHTML = '';
    detail.appendChild(el('p', null, t('checking')));
    apiGet('status', { domain: domain }).then(function (r) {
      detail.innerHTML = '';
      if (r.status !== 200 || !r.body || !r.body.dns) {
        showMsg(errLabel(r.status, r.body), true);
        return;
      }
      detail.appendChild(renderDnsTable(r.body.dns, r.body.checks));
      var verify = button(t('btnVerify'), 'btn-primary');
      verify.addEventListener('click', function () {
        verify.disabled = true;
        verify.textContent = t('verifying');
        apiPost('check', { domain: domain }).then(function (c) {
          verify.disabled = false;
          verify.textContent = t('btnVerify');
          if (c.status === 200 && c.body && c.body.active) {
            showMsg(t('msgVerified'), false);
            refreshDomains();
          } else if (c.status === 200) {
            showMsg(t('msgNotYet'), true);
            openDns(domain, detail);
          } else {
            showMsg(errLabel(c.status, c.body), true);
          }
        });
      });
      detail.appendChild(verify);
    });
  }

  function openAddresses(domain, detail) {
    detail.innerHTML = '';
    var box = el('div');
    var form = el('div', { class: 'km0d-row' });
    var user = el('input', { type: 'text', class: 'form-control', placeholder: t('address'), autocapitalize: 'off', autocomplete: 'off', style: 'max-width:160px' });
    var at = el('span', null, '@' + domain);
    var pass = el('input', { type: 'password', class: 'form-control', placeholder: t('password'), autocomplete: 'new-password', style: 'max-width:160px' });
    var add = button(t('add'), 'btn-primary');
    form.appendChild(user); form.appendChild(at); form.appendChild(pass); form.appendChild(add);
    box.appendChild(el('h4', null, t('addAddress')));
    box.appendChild(form);
    var list = el('ul', { class: 'km0d-list' });
    box.appendChild(list);
    detail.appendChild(box);

    function reload() {
      apiGet('addresses', {}).then(function (r) {
        list.innerHTML = '';
        var rows = (r.body && r.body.addresses ? r.body.addresses : []).filter(function (a) {
          return a.domain === domain;
        });
        if (!rows.length) { list.appendChild(el('li', null, t('noaddresses'))); return; }
        rows.forEach(function (a) {
          var li = el('li');
          li.appendChild(el('span', null, a.email));
          var del = button(t('btnDelete'), 'btn-danger');
          del.addEventListener('click', function () {
            if (!window.confirm(t('confirmDeleteAddress'))) return;
            apiPost('del_address', { email: a.email }).then(function (d) {
              if (d.status === 200 && d.body && d.body.ok) { showMsg(t('msgAddressDeleted'), false); reload(); }
              else showMsg(errLabel(d.status, d.body), true);
            });
          });
          li.appendChild(del);
          list.appendChild(li);
        });
      });
    }

    add.addEventListener('click', function () {
      var u = (user.value || '').trim().toLowerCase();
      var p = pass.value || '';
      if (!u) { showMsg(t('errInvalidEmail'), true); return; }
      if (p.length < 8) { showMsg(t('errPasswordShort'), true); return; }
      add.disabled = true;
      apiPost('add_address', { email: u + '@' + domain, password: p }).then(function (r) {
        add.disabled = false;
        if ((r.status === 201 || r.status === 200) && r.body && r.body.ok) {
          user.value = ''; pass.value = '';
          showMsg(t('msgAddressAdded'), false);
          reload();
        } else {
          showMsg(errLabel(r.status, r.body), true);
        }
      });
    });

    reload();
  }

  function renderDomains(domains) {
    var list = document.getElementById('km0d-domains-list');
    var empty = document.getElementById('km0d-domains-empty');
    if (!list) return;
    list.innerHTML = '';
    if (!domains || !domains.length) { if (empty) empty.classList.remove('km0d-hidden'); return; }
    if (empty) empty.classList.add('km0d-hidden');

    domains.forEach(function (d) {
      var li = el('li');
      var head = el('div', { class: 'km0d-row', style: 'flex:1;justify-content:space-between;width:100%' });
      var left = el('div', { class: 'km0d-row' });
      left.appendChild(el('strong', null, d.name));
      var active = !!d.active;
      left.appendChild(el('span', { class: 'km0d-badge ' + (active ? 'ok' : 'pending') }, active ? t('statusActive') : t('statusPending')));
      head.appendChild(left);

      var actions = el('div', { class: 'km0d-actions' });
      var detail = el('div', { class: 'km0d-dns', style: 'width:100%' });

      if (!active) {
        var dnsBtn = button(t('btnShowDns'), 'btn-secondary');
        dnsBtn.addEventListener('click', function () {
          if (detail.dataset.open === '1') { detail.innerHTML = ''; detail.dataset.open = ''; return; }
          detail.dataset.open = '1';
          openDns(d.name, detail);
        });
        actions.appendChild(dnsBtn);
      } else {
        var addrBtn = button(t('btnAddresses'), 'btn-secondary');
        addrBtn.addEventListener('click', function () {
          if (detail.dataset.open === '1') { detail.innerHTML = ''; detail.dataset.open = ''; return; }
          detail.dataset.open = '1';
          openAddresses(d.name, detail);
        });
        actions.appendChild(addrBtn);
      }

      var delBtn = button(t('btnDelete'), 'btn-danger');
      delBtn.addEventListener('click', function () {
        if (!window.confirm(t('confirmDeleteDomain'))) return;
        apiPost('del_domain', { domain: d.name }).then(function (r) {
          if (r.status === 200 && r.body && r.body.ok) { showMsg(t('msgDomainDeleted'), false); refreshDomains(); }
          else showMsg(errLabel(r.status, r.body), true);
        });
      });
      actions.appendChild(delBtn);
      head.appendChild(actions);

      li.appendChild(head);
      li.appendChild(detail);
      list.appendChild(li);
    });
  }

  function refreshDomains() {
    apiGet('domains', {}).then(function (r) {
      renderDomains(r.body && r.body.domains ? r.body.domains : []);
    });
  }

  function addDomain() {
    var input = document.getElementById('km0d-domain-input');
    var btn = document.getElementById('km0d-domain-add');
    var domain = (input.value || '').trim().toLowerCase();
    if (!domain) { showMsg(t('errInvalidDomain'), true); return; }
    btn.disabled = true;
    apiPost('add_domain', { domain: domain }).then(function (r) {
      btn.disabled = false;
      if (r.status === 201 && r.body && r.body.ok) {
        input.value = '';
        showMsg(t('msgDomainAdded'), false);
        refreshDomains();
      } else {
        showMsg(errLabel(r.status, r.body), true);
      }
    });
  }

  function init() {
    var btn = document.getElementById('km0d-domain-add');
    var input = document.getElementById('km0d-domain-input');
    if (btn) btn.addEventListener('click', addDomain);
    if (input) input.addEventListener('keydown', function (e) { if (e.key === 'Enter') addDomain(); });
    refreshDomains();
  }

  if (window.rcmail) {
    rcmail.addEventListener('init', init);
  } else {
    document.addEventListener('DOMContentLoaded', init);
  }
})();
