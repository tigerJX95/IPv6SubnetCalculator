# Release Notes

## V1.28 Union and symmetric difference for two networks

- Union covers all addresses in either network and counts overlaps only once.
- Symmetric difference keeps addresses that belong to exactly one network and excludes the intersection.
- Both results use the fewest CIDRs in ascending address order, leaving gaps uncovered. Copy them, send them to Subnet List or include them in the full relation report.

[Update History](HISTORY.md)
