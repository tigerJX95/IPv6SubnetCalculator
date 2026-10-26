# Security Code Checks

[简体中文](SECURITY_CHECKS.md)

This configuration adapts UnattendLocal V1.23 security checks to Python/PyQt. It does not establish that the application is secure or that pending Qt issues are fixed.

## Automated checks

- CodeQL analyzes Python and GitHub Actions with security-extended queries, without building an EXE.
- Bandit scans core, ui, services, application entry files and tools. Findings with both severity and confidence at least Medium fail the source check.
- PR-only Dependency review fails on newly introduced known vulnerabilities of Low severity or higher, without building PR code or posting comments.
- Existing pip-audit continues checking all locked application packages in requirements.txt. Vulnerabilities, source errors, timeouts and missing reports are failures. This does not claim a full transitive audit of every CI tool.

Jobs default to read-only access. Only CodeQL additionally receives security-events write and actions read access for analysis uploads. Actions are pinned to full commit SHAs. No pull_request_target execution or self-hosted runner is added. The separate V1.16 Release build job requests contents write access for adding a missing EXE attachment; it never runs on PRs or overwrites existing attachments. See RELEASE_BUILD_EN.md.

## Local checks

Install requirements.txt and requirements-ci.txt, then run `python tools/check_security.py`. Reports are stored in verification/security. build.cmd installs check tools and runs the full local scan/audit before packaging. verify.cmd performs i18n and security preflight. Network audit failures do not silently pass. The source-only option is for the independent source-scanning job and is not a full dependency audit.

Local Bandit/pip-audit success does not mean CodeQL or GitHub PR Dependency review has run. PyPI vulnerability database coverage does not replace Qt upstream advisory tracking; see DEPENDENCY_STATUS.md.

Specific B314 suppressions are limited to bundled TS parsing, self-generated XLSX XML in the application self-check, and developer-owned TS parsing in the contract maintenance tool. Each has a reviewed scope comment. No global XML skip, file exclusion or automatic baseline hides findings; these are not claimed as confirmed application vulnerabilities or vulnerability fixes.

## Repository protection after upload

Workflow files do not configure repository protection. Enable Dependency graph and use CodeQL Advanced setup, disabling Default setup if needed to avoid conflicts. Require approval for outside collaborators and inspect scripts/tests/workflows before approval. Do not give fork PRs write tokens or secrets.

After the first hosted run, require the actual i18n, Python security, existing quality/regression/audit and CodeQL python/actions checks as appropriate; Dependency review runs only on PRs. Also enable Require code scanning results for CodeQL with Medium-or-higher security alerts blocked. A green analysis job only means analysis completed.

CODEOWNERS assigns review to @tigerJX95, including policy and workflow files. Required PRs, Code Owner review and owner bypass are separate repository settings. Feature availability depends on repository visibility and GitHub plan. Do not ignore failed/unavailable scans to obtain a passing state. This maintenance update did not modify the hosted repository or its settings.
