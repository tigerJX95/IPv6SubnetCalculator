# Release Notes

## V1.23 Address Utilities and Candidate Range Export

- Adds bidirectional conversion between IPv6 addresses and complete ip6.arpa names, accepting uppercase and a trailing root dot, with context-menu copying of names, addresses and reports. No DNS queries are made.
- Adds signed decimal IPv6 address offsets with carry/borrow across groups and an optional CIDR restriction. Results outside IPv6 space or the restricted network are rejected without wrapping.
- Adds Excel (XLSX) export using the same filtered records as CSV. Address counts are explicit text cells for exact large integers on direct opening, with frozen headers, column filters and readable widths.
- The candidate detail Report menu adds “Save current range as CSV” for every record matching the browsing filter.
- CSV retains original candidate numbers, physical lines, duplicates, input, normalized networks, availability, exact occupied/free counts, overlap counts across all candidates and host-bit normalization flags.
- Uses UTF-8 with BOM, standard CSV quoting and line endings. Headers and statuses follow the interface language at actual save time. Counts use full decimal digits; import count columns as Text in Excel.
- Empty ranges disable CSV output. Filter changes, candidate edits or closing the window cancel pending old output, with overwrite confirmation and save conflict protection.
- Both home pages keep top sections text-only and place screenshots in the middle software gallery. Document checks reject top images; earlier notes use the Update History text link.

[Update History](HISTORY.md)
