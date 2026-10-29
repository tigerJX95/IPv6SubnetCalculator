# Release Notes

## V1.22 Range Reports and Candidate Overlap Details

- Candidate details add a Report menu to copy or save a TXT report of every candidate matching the current browsing filter.
- Adds candidate overlap sources: other original candidate numbers and source lines, equality/containment relationships, intersection CIDRs and exact address counts.
- Overlap sources are computed on demand against all original candidates, including entries outside the browsing filter. Complete detail reports include them in copy/TXT output; free/occupied CIDRs still use the baseline list.
- Reports retain original candidate numbers, physical line numbers, duplicates, input and normalized networks, availability and exact address counts. Candidate overlap counts retain the statistics for all original candidates.
- Empty ranges disable report output. Filter changes, candidate edits or closing the window cancel pending old-report saves, including changing away and back to the same filter.
- Navigating within the same range keeps the complete range report valid. Reports use the interface language at actual save time, with overwrite confirmation and save conflict protection.
- Updates both languages, user instructions and actual interface screenshots. Home pages and About show only current notes; earlier releases use the Update History text link.

[Update History](HISTORY.md)
