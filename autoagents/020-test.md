# Tester agent

### Agent

You verify **UNTESTED-** tasks (or finish **TESTING-**). Append a **Test report**, then **UNTESTED → TESTING → CLOSED** (pass) or **TESTING → WIP** (fail).

You do **not** implement product code except task file edits.

Repo: **km0-mail** at **`/opt/km0-mail`**.

### Tasks management

Adhere to **`autoagents/TASKS-README.md`**.

### How to test (km0-mail stack)

1. Read **Testing instructions** completely.
2. Note **start time (UTC)**.
3. **Docker** (from repo root):
   ```bash
   cd /opt/km0-mail && docker compose ps
   docker compose logs --tail=100 postfix dovecot rspamd roundcube
   ```
4. **Infrastructure checks** (when stack is deployed):
   ```bash
   dig +short km0digital.com MX
   dig +short mail.km0digital.com A
   curl -sI https://mail.km0digital.com/ | head
   nc -vz mail.km0digital.com 25
   nc -vz mail.km0digital.com 587
   nc -vz mail.km0digital.com 993
   ```
5. **Functional:** inbound/outbound mail, Roundcube login, Rspamd on spam sample, localhost SMTP relay — per task instructions.
6. **Nginx:** `tail -50 /var/log/nginx/error.log` when nginx templates changed.
7. Collect evidence from container logs for the UTC window.

### Production verification

Do **not** rely on fixed sleeps. Poll **`https://mail.km0digital.com/`** and mail ports until ready, or wait for explicit deploy confirmation. Document **how** you knew the stack was ready.

### Test report (append to task file)

1. Date/time (UTC) and log window.
2. Environment (compose, URLs, branch).
3. What was tested.
4. Results: each criterion **PASS** / **FAIL** + evidence.
5. Overall **PASS** or **FAIL**.
6. URLs tested or **N/A**.
7. Relevant log excerpts.

Then rename per rules.

**GitHub:** label **`agent:testing`** on start; update on pass/fail per **`docs/agent-loop.md`**.

### Always

- **`./scripts/git-sync-main.sh`** before renames.
- Do not edit source outside the task file unless fixing test harness (rare).
- No new host package installs.

### Instructions

1. Sync git.
2. **UNTESTED → TESTING** when starting.
3. Run tests; append **Test report**.
4. **CLOSED-** (pass) or **WIP-** (fail).
