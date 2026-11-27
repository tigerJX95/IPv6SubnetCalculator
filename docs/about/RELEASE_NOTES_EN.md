# Release Notes

## V1.38 Site prefix comparison and offline Pref64 identification · 2026-11-27

- Compare site prefix options from a parent network and site count. See capacity, /64 subnets per site and the first/last prefix in the requested contiguous range for /48, /52, /56, /60 and /64; distinguish insufficient capacity from an unsplittable parent.
- Identify Pref64 candidates offline from pasted ipv4only.arpa AAAA addresses using the six RFC 6052 layouts and RFC 7050 markers. Preserve multiple candidates, original line numbers and single/two-address evidence; exclude unresolved ambiguity.
- Copy or save both reports as TXT; input edits immediately disable stale output. Refresh bilingual help and actual interface screenshots, keeping current specifications distinct from revision drafts.

[Update History](HISTORY_EN.md)
