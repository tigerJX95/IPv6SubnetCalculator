# Release Notes

## V1.25 Candidate Address Queries and CIDR Output

- Candidate details add search modes: Text contains, Contains address and Network overlap. Address/CIDR modes use IPv6 relationships independent of compressed or expanded spelling; CIDR host bits are normalized.
- Queries intersect with baseline availability and candidate-overlap filters, retaining original indices and duplicates. Navigation and TXT/CSV/Excel output use the same matching records.
- The Report menu adds copy/save of filtered CIDRs: complete normalized candidate networks, deduplicated in first-input order, without merging contained or adjacent networks.
- Invalid addresses/CIDRs mark the query input and disable old output. Editing the query, mode or filters, including away and back, stops pending old saves. Reset restores Text contains mode.
- Retains readable minimum report height and font-adaptive Windows layout; updates both languages, actual screenshots and current-version documentation.
- Preserves the Issue template configuration; source packaging verifies `.github/ISSUE_TEMPLATE/config.yml` is included.

[Update History](HISTORY.md)
