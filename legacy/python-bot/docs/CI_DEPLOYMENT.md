# Deploying from GitHub Actions

`.github/workflows/deploy-macos.yaml` runs on every push to private `main` and
can also be started manually. It runs only on the Mac self-hosted runner labelled
`automation-deploy`, under the same logged-in macOS user that owns the bot's
LaunchAgent.

Every commit pushed to private `main` is resolved to a full SHA, validated, and
then deployed through `ansible/playbook.shared.yaml`. For a rollback or a
specific reviewed branch, tag, or commit, open **Actions → Deploy LastZ to macOS
→ Run workflow** and enter that revision.

The workflow uses `ansible/inventory.runner.ini`, which deploys to `localhost`.
It must not use the LAN SSH inventory: the runner already runs on the target Mac.
It fetches the public deployment role at the SHA pinned in
`ansible/playbook.shared.yaml` and the private bot at the resolved application
SHA. These are deliberately independent pins.

The managed checkout is `~/Applications/lastz`, not `~/Documents`. macOS may
deny a background LaunchAgent Files & Folders access to Documents even when an
interactive SSH or Terminal session can read it. Persistent bot configuration,
logs, and state stay under `~/Library/Application Support/LastZ`. The former
Documents checkout is treated as a migration source and is not deleted.

Before the first run, confirm the runner is **Idle** in repository **Settings →
Actions → Runners**, has `self-hosted`, `macOS`, `ARM64`, and
`automation-deploy` labels, and is installed as a service for `garyrizzo`.

The workflow does not pass an Ansible Vault file. Existing external `worker.env`
is preserved when `lastz_secrets` is empty, as it is in `ansible/vars.yaml`.
If secrets must change, use a protected GitHub Environment/secret and provide a
controller-local Vault password mechanism; do not commit Vault passwords or
worker environment files.

Protect `main`: every commit on it can execute code on the self-hosted runner.
The workflow does not run for pull requests or other branches. Deployments are
serialized rather than cancelled, so a newer push cannot interrupt a deployment
that has already stopped the bot service.
