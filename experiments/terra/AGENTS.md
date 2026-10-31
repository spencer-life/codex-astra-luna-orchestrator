# Terra experiment scope

This directory is the alternate session-only workflow, not the stable installation
source. Use `../../TERRA.md` for validation, local activation and evidence limits.
Use `terra-orchestrator` for substantive work in an explicitly selected experimental
session; do not combine its topology with the stable astra-orchestrator topology.
The original `orchestrator/`, installer guards and receipt identity stay unchanged.
Keep all private catalogs, session logs, receipts and machine paths outside Git.
Changes to routing require structural checks plus representative behavioral testing;
a regex or deterministic unit test cannot establish model behavior.
