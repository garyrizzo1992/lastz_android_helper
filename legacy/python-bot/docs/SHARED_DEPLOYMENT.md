# Public role / private production configuration

The reusable macOS deployment implementation is published in lastz_pub under
deployment/ansible/roles/automation. This repository retains real host configuration,
credentials, bot entry point and state migrations. No production values are
stored in the public role.

ansible/playbook.shared.yaml is the opt-in consumer. Its first play fetches a
reviewed public commit on the Ansible controller, into the ignored
ansible/.public-deployment directory. The second play applies that role to
macmini using the existing private vars.yaml.

Run from Linux/WSL or macOS:

```bash
ansible-galaxy collection install -r ansible/requirements.yaml
ansible-playbook -i ansible/inventory.ini ansible/playbook.shared.yaml
```

Supply the existing Vault options when updating credentials. The shared role
uses worker.env; it copies bot.env there first if worker.env does not exist.
Existing external action/truck state remains in place. New launcher output uses
logs/worker.stdout.log and logs/worker.stderr.log. The bot's own logs are unchanged.

This mode runs main_scrcpy.py directly through an external managed launcher.
It does NOT invoke the old self-updating run_bot.sh: startup uses the revision
Ansible installed, preserving the CI validation boundary. Future updates require
rerunning Ansible (manually or through private CI). Set lastz_branch to a reviewed
application SHA for immutable deployment; the public role has a separate SHA pin.

The existing playbook.yaml remains available for the existing startup-pull mode.
Do not alternate the two playbooks during normal operations: they manage the
same worker label but different launch commands and log filenames.

No production deployment was performed as part of publishing the role. Validate
this opt-in path on the Mac before making it the normal deployment entry point.
Review and update the public-role SHA in playbook.shared.yaml deliberately.
For the self-hosted Mac runner path, see CI_DEPLOYMENT.md; it uses the separate
local inventory rather than SSHing to the Mac's LAN address.
