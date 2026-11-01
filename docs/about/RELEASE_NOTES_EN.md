# Release Notes

## V1.24 Combined Candidate Filters and Keyword Search

- Fixes the candidate report being squeezed by filters at the minimum Windows window size. Reserves readable report height and lets the minimum window adapt to native fonts and layout.
- Candidate details add overlap filters: any, has candidate overlap or no candidate overlap. Combine them with baseline availability to find candidates that are free against the baseline but overlap each other.
- Adds case-insensitive literal substring search over original input and normalized CIDRs, intersected with availability and overlap filters while retaining original indices, physical lines and duplicates.
- Search updates after typing stops; Enter applies immediately. Bottom navigation, original-index jumps and TXT/CSV/Excel range output follow the same matching records.
- Edits immediately clear old details and disable old output. Changing search or overlap conditions cancels pending old saves even if the original value is restored.
- One-click reset restores all statuses, any overlap and an empty search. Empty results recover when conditions change or reset.
- Updates both languages, actual interface screenshots and offline help. Current pages show V1.24 only; Earlier releases move to the Update History text link.

[Update History](HISTORY.md)
