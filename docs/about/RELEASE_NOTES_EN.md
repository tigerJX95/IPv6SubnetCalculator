# Release Notes

## V1.18 Batch Candidate Details and Interface Cleanup

- Batch Availability adds candidate details: select a number in input order to inspect baseline conflict source lines, exact free/occupied ranges, and copy or save CIDRs inside that candidate.
- Duplicate candidates and physical source line numbers are retained. Read-only details are computed on demand against the same baseline snapshot; they neither change the occupied list nor reserve space between candidates.
- Changing the selected candidate, editing batch input or closing inspection invalidates old details and rejects pending stale saves.
- Includes presentation revisions: explicit input/containing-network labels; separate user help and release notes, with only current V1.18 notes in About; centered main document titles with spacing before subheadings.
- Address-format and two-network results use context-menu copying instead of right-side copy icons, retaining continuous 128-bit binary and complete reports. Both languages, matching screenshots, i18n and security checks are updated.
- Retains attachment-aware EXE Release builds and main ancestry validation without fetching historical tags. This release does not change historical tags or repository settings.
