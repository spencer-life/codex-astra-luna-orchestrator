# Maintaining the personal setup

## One source for ChatGPT and Codex

Use **https://github.com/spencer-life/codex-astra-luna-orchestrator/tree/personal**.
Always specify the `personal` branch when asking either assistant to inspect or
change the setup. A GitHub connection does not imply that the default branch is
`personal`, nor that a cached view includes the latest commit. Give the assistant
the branch link and, for a review, the commit SHA.

The files to maintain are:

- `orchestrator/config.toml`: root model/effort and only the five owned `[agents]` settings.
- `orchestrator/agents/*.toml`: the seven named roles, including the unchanged research verifier.
- `orchestrator/skills/astra-orchestrator/SKILL.md`: the literal installed skill source.
- `scripts/orchestrator_sync.py`, `mise.toml`, and its tests: the guarded apply workflow.

Do not edit the installed copies as the normal update path. Do not regenerate the
skill from instructions. Do not copy the entire installed config into the repo.
Do not copy credentials, permissions, providers, MCP servers, apps/plugins,
project paths, sessions, or logs into this public fork. Backups and installation
receipts stay outside the checkout and are never committed.

## Defaults preserved by this import

The root and reviewer use Astra at Low. Explorer, worker, tester, and generic
subagent fallback use Luna at High. Researcher and Semble search use Luna at
Medium. The agent settings keep three concurrent subagents and `max_depth = 1`;
the skill also prohibits nested delegation unless explicitly authorized.
Research verifier remains Sol at High, read-only, with its original instructions.
Existing explicit session choices are respected; these files do not prove the
settings already loaded into a running session.

The initial source import was taken from the working installed configuration.
It changes no model, effort, sandbox, service tier, or delegation setting.
The skill adds the repository-first workflow and uses portable home paths.
The Semble role only replaces its absolute launcher path with `~/.local/bin/semble`.
Other role files, including the research verifier, are copied byte for byte.

## Review, commit, and apply

Prerequisites: Git, mise, and uv. Review this repository's mise configuration
before trusting it. In your local checkout of `personal`:

```sh
# Run once after reviewing mise.toml:
mise trust

# If approved changes were made on GitHub or another machine:
mise run orchestrator:sync

# Inspect the actual source changes, then validate and test:
mise run orchestrator:validate
mise run orchestrator:test
mise run orchestrator:plan

# When you made local edits, commit only the reviewed paths first:
# git add <reviewed paths>
# git commit -m "fix(orchestrator): describe the approved change"

# Apply only the clean, committed personal checkout:
mise run orchestrator:apply
mise run orchestrator:status

# Publish approved local commits (never force-push):
git push origin personal
```

The exact future apply command is **`mise run orchestrator:apply`** from the
`personal` checkout. `mise run orchestrator:sync` fast-forwards only from the fork’s `personal`
branch; syncing and applying are separate, explicit steps. Nothing fetches or
installs original-project updates automatically. A dirty checkout or
an unexpected change to an owned installed file blocks apply. Review and preserve
that work rather than resetting or forcing through it.

Initial adoption of an existing installation uses an explicitly prepared
private baseline of the existing installed files. It must match immediately before applying. This is a
one-time adoption step; routine updates use the recorded installation state.
The workflow does not offer a force-overwrite option. All nine destination
files must already exist; this is a maintenance workflow, not a blank-machine
installer.

## What apply owns

Apply copies the seven role files and the skill directly from `orchestrator/`.
It merges only the allowlisted config keys while preserving unrelated TOML
settings and comments. It does not replace the whole config or remove unrelated
roles/skills. In particular, existing `agents.interrupt_message`, permissions,
MCP/app configuration, and other machine settings remain local and unchanged.

Before writing, apply validates the source and checks the recorded owned-file
hashes and config values. Changes to unrelated config keys are allowed. It backs
up all affected installed files and the prior receipt, writes replacements, and
records the source commit and content hashes. Concurrent applies are locked out;
failures during writing trigger restoration from the captured pre-apply data.
Individual replacements are atomic; a process kill or machine failure across
multiple files can still require recovery from the backup.

Installation state is kept at `~/.local/state/astra-orchestrator/state.json`.
Backups live under `~/.local/state/astra-orchestrator/backups/`; the apply
output gives the exact directory. Its `manifest.json` maps each installed path
to a backup file and records its original mode. Treat backups as private:
the config backup includes unrelated settings that must not be uploaded.
Do not publish the receipt or private baseline merely to prove installation.

If drift blocks apply, compare the local file with its maintained source and the
last installed commit. Preserve the local copy. Bring approved edits into the
repository, then explicitly reconcile the installed copy with the last recorded
state before retrying. Do not simply delete the receipt to bypass drift checks.
For rollback, preserve any newer local changes first and restore the affected
files **and matching receipt** from the same pre-apply backup. Do not mix backups
from different applies. Plan/status will detect a mismatched state.

Start a new Codex session after an apply that changes configuration, role
instructions, or the skill so it can load the applied files. This workflow does
not restart Codex or override a model/effort explicitly selected in a session.

## Original-project updates

`origin` is the fork. `upstream` is
`https://github.com/donvito/codex-astra-luna-orchestrator.git`.
`main` is reserved for the original-project reference, not personal changes.
The personal branch starts from the fork's existing reference commit
`642b16074ba8973d4f920ad8cbfb542bde3b4682`. This migration does not advance `main`,
merge newer original-project changes, or adopt upstream PR #15.

For a separately requested upstream review, fetch upstream, inspect the changes
in an isolated checkout, and review individual fixes for applicability. Updating
`main` must preserve its original-project-only history and must never run apply.
Port only explicitly approved changes into `orchestrator/` on `personal`, test,
commit, and apply through the same workflow. Do not merge `personal` into `main`.
The inherited `profiles/`, old guides, and `setup.sh`/`setup.ps1` are historical
upstream reference material; do not run those installers for this personal setup.

The earlier interrupted customization checkout and its untracked files were
preserved separately. Its private machine-specific commits were not imported
into the published personal branch history.
