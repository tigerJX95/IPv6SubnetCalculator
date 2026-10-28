[简体中文](RELEASE_BUILD.md) | [Home](../README_EN.md) | [Download releases](https://github.com/tigerJX95/IPv6SubnetCalculator/releases)

# Build EXE Only When a Release Has No EXE

V1.16 adds `.github/workflows/build.yml`, named **Build missing Release EXE**. It follows the UnattendLocal attachment policy, adapted to this project's Python/PyQt Windows x64 single-file EXE. Ordinary pushes and PRs do not trigger builds.

| Action/attachment state | Behavior |
|---|---|
| Published Release with any complete `.exe` attachment | Skip automatic build/upload, regardless of filename or extension case |
| Published Release without an EXE | Build, verify and attach `IPv6SubnetCalculator_Vversion.exe` |
| Only ZIP, text or GitHub automatic source archives | Still build; these are not EXE attachments |
| Empty or incomplete EXE | Fail; complete/remove the problem attachment before retrying that Release run |
| Immutable Release without an EXE | Fail without bypassing the lock |
| Manual EXE added while compiling | Recheck before uploading; stop automatic upload when an EXE is found |
| Manual Actions run | Build and verify; retain the EXE in Actions without modifying a Release |

## Usage

1. Commit the complete update to `main`, including the workflow, `tools/release_assets.py` and tests. The existing official-action allowlist and full-SHA requirement are compatible. No new Secrets or repository-wide read/write default are required.
2. Tag a commit containing the workflow. Use lowercase `v1.19` for `APP_VERSION = '1.19'`; the tag must exactly match the version and its commit must already be in `main` history.
3. To distribute a manually built EXE, upload the complete file to the Release draft before publishing. To request cloud compilation, publish without an EXE attachment.
4. Check **Build missing Release EXE** in Actions. After successful build/verification, refresh the Release for its EXE. SHA-256 is recorded in the run summary.

Uploading the workflow does not backfill historical Releases. Editing a Release or adding/removing an attachment does not trigger it. Retry an original Release run with Re-run jobs to retain its Release context. **Run workflow creates an independent Actions build and does not attach files to a historical Release.**

## Build and validation boundaries

- GitHub-hosted Windows 2025, x64 Python 3.12, locked application dependencies and PyInstaller 6.22.3. Licenses and offline documents are embedded. The Release EXE is not wrapped in a ZIP.
- Read-only by default; only the build job receives `contents: write` for attachment upload. No PR trigger. Uploads use a fixed Release ID and additive POST, without overwrites, deletions or Release/tag creation/edits. Same-name races fail rather than replacing files.
- Actions stores the raw EXE with `archive: false` for 7 days. Separate verification artifacts also last 7 days and are not attached to the Release. Release EXEs are unaffected by the Actions retention period.
- First hosted Windows build and real attachment upload require validation after commit. Local tests mock the API; no real Release or attachment was created.


V1.19 fetches only main history without fetching tags. This avoids case-variant historic tag collisions on Windows while retaining exact version and main ancestry checks. Existing tags are preserved.
