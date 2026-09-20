# Semble reference

Read only the section needed. This is the preserved 0.6.0 integration reference,
not a claim about today's installed version. Confirm the version and live tool
schema before version-sensitive maintenance. Ordinary discovery does not require
loading the full reference or running installation/cache-maintenance commands.

## Search and MCP

Prefer Semble MCP for repeated searches: its process retains the embedding model and indexes in memory. Use the CLI for scripts, maintenance, or when MCP is unavailable or its loaded schema lacks a needed capability.

- search: query, repo, top_k (default 5), max_snippet_lines (default 10), content.
- find_related: file_path, line, repo, top_k, max_snippet_lines, content. Use the returned file_path and start_line, preserving the search's repository set and content selection.
- repo accepts a local directory or an explicit HTTP(S) Git URL; Semble 0.6.0 also accepts a list of these for multi-repository search. Consult the live tool schema before passing a list.
- Default to all content (code, docs, config). Narrow to code, docs, or config when the question is specific or mixed results obscure the answer. These selections have separate cached indexes.
- Choose content, result count, and snippet length for the question; these are tunable budgets, not restrictions. Five results and ten snippet lines are a reasonable starting point for locating code; use full chunks when the task needs implementation detail. Start with a focused behavior description or identifier. Use zero lines when only locations are needed. Answer from snippets when they provide sufficient evidence. Read focused sections at returned lines only when more context or verification is needed; avoid repeating searches for an already-located implementation. Refine a query when results do not answer the question.
- Scope to the relevant repository or subtree. For cross-repository questions, search the relevant repositories together rather than indexing a broad workspace. Multi-repo results include a repos map and prefixed file paths; use that map to resolve local files and preserve prefixes for find_related.
- find_related returns similarity matches and filters to the seed chunk's detected language in 0.6.0; use a descriptive search for cross-language analogues. It is not an exhaustive call graph. Confirm callers/references with rg or language-aware tools. For similar implementation code, scope find_related to the source subtree when test matches dominate; adjust file_path relative to that root. For tests/examples, search their subtree when other matches obscure them.

When discovering deferred tools, match the Semble namespace rather than dumping every tool whose description mentions search. When wrapping MCP calls programmatically, return one useful result representation (structuredContent or text content), not both copies of the same snippets.

## Complete CLI reference (Semble 0.6.0)

Place query and paths before --content, which accepts multiple values.

```bash
semble --version
semble --help
semble search "authentication flow" ./project --content all --top-k 5 --max-snippet-lines 10
semble search "invoice endpoint" ./service-a ./service-b --content all --max-snippet-lines 10
semble search "deployment guide" ./project --content docs --max-snippet-lines 10
semble search "database host port" ./project --content config --max-snippet-lines 10
semble search "save_pretrained" ./project --content code --max-snippet-lines 10
semble find-related src/auth.py 42 ./project --content all --max-snippet-lines 10
semble find-related service-a/src/auth.py 42 ./service-a ./service-b --content all --max-snippet-lines 10
semble savings
```

search and find-related accept --top-k/-k (default 5), --max-snippet-lines (0 = locations only; omit for full chunks), --format json|text (JSON default), and --content code|docs|config|all (CLI default is code, so pass all explicitly). CLI content can combine types, e.g. --content code docs. Paths default to the current directory; multiple local paths/explicit Git URLs are supported. --include-text-files is deprecated; use --content all. Use COMMAND --help to verify syntax.

Running semble without a subcommand starts the stdio MCP server; `semble --content all` is this machine's configured server mode, not an indexing command. There is no separate CLI index/watch command: searches build and refresh indexes on demand.

If semble is missing from PATH, this installation's launcher is ~/.local/bin/semble. The version-matched uvx fallback is `uvx --from 'semble[mcp]==0.6.0' semble`. Prefer the installed launcher to avoid another tool environment.

## Index coverage and freshness

all means supported categories, not every file. In 0.6.0 JSON/JSON5/CSV/TSV, plain .txt, extensionless files such as Dockerfile/Makefile, symlinks, ignored paths, and files over the default 1,000,000-byte limit can be absent. Check known files directly when search coverage is insufficient.

Semble reads .gitignore and .sembleignore from the search root downward and skips common dependency/build directories. It does not load Git core.excludesfile, .git/info/exclude, or ignore files above that root. When a task needs persistent search coverage, check relevant local rules; exclude generated artifacts (for example target/, coverage/, .claude/worktrees/, or Repomix packs) with .sembleignore and preserve useful source/docs/config. Keep Git exclusions for untracked build/cache artifacts in .gitignore; do not Git-ignore .sembleignore itself. A parent workspace rule does not apply when searching a nested repository directly. For a recurring repository need, .sembleignore can exclude generated noise or force-include specific extension-bearing files such as !package.json; avoid broadly including generated data. Do not assume a negative search proves absence. Do not add repository rules just to run a one-off lookup. Force-included extensions bypass content-category filtering, so those files can appear even in code-only or docs-only searches.

Local indexes refresh incrementally for file edits/additions/deletions. MCP delays freshness checks after a build by roughly three times that build duration; immediately after edits, read the file or use CLI if fresh search results are essential. Remote URL indexes are cached snapshots without automatic upstream freshness checks; prefer a current local checkout when freshness matters.

## Maintenance and configuration

All CLI maintenance commands remain available when the task calls for them:

- semble clear orphans: delete indexes whose local source directories no longer exist.
- semble clear index: delete all saved Semble indexes, not just the current repository.
- semble clear savings: reset usage statistics.
- semble clear all: delete saved indexes and statistics; it does not clear the Hugging Face model cache.
- semble install --agent codex --type mcp instructions subagent --yes: write selected Codex integrations. --type also accepts all; --agent accepts multiple agents. Omit flags for interactive setup.
- semble uninstall accepts the same flags and removes the selected integrations.

Use clearing for a diagnosed cache problem or requested cleanup, not before routine searches. install/uninstall change persistent integration files and may overwrite this custom guide, global guidance, or MCP settings; preserve those customizations when maintaining the installation. Ordinary search tasks do not require running either command.

Semble is uv-tool managed; Mise supplies uv. `uv tool upgrade semble` updates it. After an upgrade, check --help and the MCP schema, review upstream integration changes, update this version-specific guide if needed, and restart the MCP client. A blind `semble install` would replace custom settings; merge relevant upstream changes instead. The 0.5.6-to-0.6.0 line-number fix does not invalidate old caches automatically; that upgrade needs a one-time index rebuild (completed for this setup).

Indexes/stats live in ~/.cache/semble. SEMBLE_CACHE_LOCATION selects an absolute alternate directory; use the same location across CLI/MCP when cache sharing is intended. SEMBLE_MAX_FILE_BYTES controls the file-size cap. SEMBLE_MODEL_NAME selects a compatible Model2Vec model/path; keep the installed default unless a task needs another. Initial model download uses the Hugging Face cache; indexing/search run locally on CPU. No API key is required.

semble savings estimates snippet savings against reading matched files in full; it is not measured Codex billing or a full workflow benchmark.
