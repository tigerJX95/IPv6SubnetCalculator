# Release Notes

## V1.37 Prefix demand planning and reverse DNS zones · 2026-11-22

- Size a parent prefix from subnet count, individual prefix and extra reserve. Compare the mathematical minimum with a nibble-aligned alternative, copy the result or save the planning report.
- Generate subnet reverse DNS zones. Non-nibble-aligned networks split into at most eight exact zones; copy the plain list or save TXT without querying DNS or creating records.
- Cite RFC 6052 explicitly in NAT64 deployment guidance and distinguish the current specification from its revision draft in Help. Extend equivalent-address and small-window checks.

[Update History](HISTORY_EN.md)
