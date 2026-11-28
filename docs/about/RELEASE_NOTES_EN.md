# Release Notes

## V1.39 Batch NAT64 conversion and ULA subnet lookup · 2026-11-28

- Convert batches in either NAT64 direction using all six RFC 6052 prefix lengths. Preserve input order, duplicates and original line numbers; any invalid address cancels the entire output. Copy address-only lists or save full TXT reports.
- Generate a ULA /48 within fd00::/8 using the system random source, or enter an existing prefix. Locate an exact /64 subnet and its address range using a hexadecimal Subnet ID from 0000 to ffff.
- Correct multicast IPv4 destination guidance in NAT64 reports. Add bilingual help, actual interface screenshots and protection against exporting results after inputs change.

[Update History](HISTORY_EN.md)
