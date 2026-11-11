# Release Notes

## V1.32 Save filtered CIDR lists · 2026-11-11

- Save the current two-network CIDR results as UTF-8 TXT, one CIDR per line, ready to import into Subnet List.
- The filter status shows how many addresses the visible CIDR blocks cover. It counts the whole blocks and preserves the exact total.
- Saving is disabled for invalid filters or empty results. Changing the filter while choosing a file or confirming an overwrite cancels the save.
- Fix target prefix truncation: four-digit prefixes entered or pasted into the field are rejected instead of calculating 1280 as 128.

[Update History](HISTORY.md)
