# macOS deployment

Run Ansible from Linux, WSL, or macOS. The target must already have Homebrew,
Git/Xcode command-line tools, a Python interpreter usable by Ansible, and an SSH
key authorized to read the repository. Connect as the configured LastZ user.
Automatic login must have created that user's GUI session. No monitor is needed.

Adjust ansible/vars.yaml or supply overrides with -e. Python defaults to 3.13 on
Apple Silicon. If changing the Python minor version, also change lastz_python and
recreate the virtual environment during a maintenance window.

```bash
ansible-galaxy collection install -r ansible/requirements.yaml
ansible-playbook -i ansible/inventory.ini ansible/playbook.yaml --syntax-check
ansible-playbook -i ansible/inventory.ini ansible/playbook.yaml
```

Use inventory.example.ini as a starting point. Local inventory and vault.yaml
are ignored by Git. For secrets, copy vault.example.yaml to vault.yaml, replace
the placeholder, then encrypt and deploy:

```bash
ansible-vault encrypt ansible/vault.yaml
ansible-playbook -i ansible/inventory.ini ansible/playbook.yaml -e @ansible/vault.yaml --ask-vault-pass
```

The environment template shell-quotes values and installs bot.env with mode 0600.
An empty lastz_secrets preserves existing configuration. Keep this dictionary
for credentials only; deployment paths belong in lastz_environment.

The playbook takes an exclusive deployment-directory lock and unloads the bot
before updating code and packages. Each deployment intentionally restarts the
bot, even if no files changed. Parallel deployments fail at lock acquisition.
Startup refuses to run while that lock exists. Do not run standalone bot
processes or manually launch the script during deployment.

Action status and truck state are copied from the old checkout before Git runs,
only when the destination does not exist. Existing .env is similarly preserved
as bot.env. Old logs and screenshots remain in the checkout. New runtime data
goes to ~/Library/Application Support/LastZ. Review migrated bot.env for old
LASTZ_* path overrides before deployment.

Git updates fail on conflicting local changes in Ansible; they are not discarded.
The service launcher retains the explicitly requested force-sync behaviour at
startup. It fetches the selected branch and resets tracked files, then installs
requirements-runtime.txt when its checksum or Python version changes. Pip failure
prevents startup. requirements.txt includes the same pinned runtime dependencies;
removed standalone desktop/web-store tools are not installed.

Preflight runs under tasks, loads the same environment as the service, and skips
Git and pip updates. Failure is advisory (including a disconnected phone); the
exit code and diagnostic output appear in the play recap output. Registration
with launchd does not establish that the game loop is healthy.

Deployment failure releases its lock but leaves the bot stopped if it was
already unloaded, to avoid starting a partially installed environment. Correct
the error and rerun. An interrupted controller may leave deploy.lock behind:
verify no deployment is active before removing that empty directory with rmdir.

LaunchAgent stdout/stderr are checked hourly by a separate logrotate agent;
each rotates above 10 MB with seven compressed copies. copytruncate can lose
a small amount of output during rotation. The bot's own log already rotates.

After reboot, check over SSH as the bot user:

```bash
launchctl print gui/$(id -u)/com.garyrizzo.lastz
git -C ~/Documents/lastz rev-parse --short HEAD
adb devices -l
tail -n 50 "$HOME/Library/Application Support/LastZ/logs/lastz_bot.log"
```

CI checks Ansible syntax/lint and shell syntax, and installs/imports the bot on a
macOS runner. USB authorization, real phone interaction, and automatic-login
recovery still require validation on the actual Mac.
