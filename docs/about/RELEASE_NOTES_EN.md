# Release Notes

## V1.33 Two-network CIDR filter counts and export · 2026-11-15

- Two-network CIDR details show full coverage and the exact address count within the filter separately. For example, filtering for `::3` matches `::2/127`: the block covers 2 addresses, and 1 address matches the filter.
- Two-network CIDR details can save only the addresses shared by the filter and the current category as TXT. For example, filtering for `::3` in `::2/127` saves only `::3/128`. The existing save action still writes full visible CIDRs.

[Update History](HISTORY.md)
