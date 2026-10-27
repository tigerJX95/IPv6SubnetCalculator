[简体中文](BATCH_AVAILABILITY.md) | [Home](../README_EN.md) | [Download releases](https://github.com/tigerJX95/IPv6SubnetCalculator/releases)

# Batch Network Availability

Open Subnet List → the third, target-shaped icon in the top row → Batch Availability. Scroll the tabs at small window sizes. The occupied baseline is a snapshot taken when this window opens; close, edit the original list and reopen to refresh it.

## V1.17 Output categories

The category selects CIDRs for its adjacent copy/save controls. Upper report controls still output every candidate. Output contains **whole candidate networks, not their free/occupied fragments**.

| Category | Condition | Baseline `::/127`, candidates `::/126`, `::4/126`, `::/127` |
|---|---|---|
| Entirely free | Zero occupied addresses | `::4/126` |
| Partially occupied | Both occupied and free addresses | `::/126` |
| Fully occupied | Zero free addresses | `::/127` |
| With occupied addresses | Partially or fully occupied | `::/126`, `::/127` |
| All candidates | No occupancy filter | `::/126`, `::4/126`, `::/127` |

Every category normalizes and deduplicates in first-input order, preserving candidate boundaries and containment without aggregation or allocation. Overlapping candidates are not necessarily allocatable together. Category changes preserve the result, input and full report. Category/result changes during saving cancel stale CIDR output. Empty categories disable CIDR output while complete reports remain available.

![English category selection](screenshots/batch_categories_en_US_light.png)

## Inputs and controls

| Item | Behavior and rules | Example |
|---|---|---|
| Occupied baseline | Uses the main window list; every record must be valid; empty is allowed | `2001:db8::/127` |
| Candidate input | One complete IPv6 CIDR per line; blank lines and # comments are ignored; physical line numbers are retained; host bits are normalized | `2001:db8::3/126` becomes `2001:db8::/126` |
| Check icon | Validates both lists before processing the whole batch; any invalid record rejects the batch | Click the check icon below the input |
| Upper copy/save icons | Output the complete per-candidate report, including state, capacity, overlapping candidate counts and normalization | Save `IPv6_BatchAvailability.txt` |
| Output category | Select candidate occupancy status; normalize and deduplicate in first-input order; containment retained, no aggregation | Both `::/125` and `::/126` are retained |
| Category copy/save icons | Output pure CIDRs for reimport into Subnet List; disabled when the selected category is empty | Save `IPv6_free_candidates_CIDRs.txt` |

Each list has independent limits of 5,000 records, 1 MiB of UTF-8 text and 20,000 physical lines. A CIDR may contain at most 200 characters. Candidates cannot be empty. IPv4, zone identifiers, invalid prefixes and missing prefixes are rejected.

## Example

Occupied baseline:

```text
2001:db8::/127
```

Candidate input:

```text
2001:db8::/126
2001:db8::4/126
2001:db8::/127
2001:db8::4/126
```

| Candidate line | State | Occupied/free addresses | Other overlapping candidate records |
|---|---|---|---|
| 1 | Partially occupied | 2/2 | 1 |
| 2 | Entirely free | 0/4 | 1 |
| 3 | Fully occupied | 2/0 | 1 |
| 4 | Entirely free | 0/4 | 1 |

The report retains duplicate lines 2 and 4. Entirely free candidate CIDR output contains just `2001:db8::4/126`.

![English batch availability](screenshots/batch_availability_en_US_light.png)

## Result boundaries

Each candidate is independently checked against the baseline; candidates do not occupy or reserve space for each other. Overlapping candidate record counts include duplicates and containment, exclude the candidate itself and exclude adjacent non-overlapping candidates. Entirely free candidates can overlap and are not necessarily allocatable together. Do not add overlapping address counts.

Calculations use exact integers and the occupied union without enumerating addresses. Disjoint occupied records have no effect. Editing candidates clears output immediately; input or result changes during saving cancel stale output. Saves retain overwrite confirmation and external-file conflict protection.

The baseline is unchanged. Nothing is allocated or appended automatically. Candidate inputs and results are not stored in planning project JSON; save them separately when needed. Free means uncovered by the supplied baseline, not verified network state, allocation rights or deployability.

## Candidate details

Select a candidate number after checking, then click the locate icon to inspect baseline conflicts and internal CIDRs. See [settings and example](BATCH_DETAILS_EN.md).
