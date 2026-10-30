# User Guide

This guide explains current operations. Version changes are listed separately on the Release Notes tab.

## Planning project save and restore

- Open/save-as icons at the top of Subnet List remain accessible on the Allocation Suggestions tab.
- Separate JSON preserves the original list (comments and blank lines included), parent network, allocation prefix, requested count and result tab. Unfinished drafts are supported.
- Files are validated before replacement confirmation. Restoring clears derived results; run checks or planning again. This format is separate from calculation plans; Ctrl+S/Ctrl+O still operate calculation plans.
- Reuses save conflict protection and rejects stale actions when inputs or tasks change during dialogs. Changes to saved projects are marked as unsaved.
- Projects require manual saving. Before closing or opening another project, save, discard or cancel unsaved planning changes. Cancelled or failed saves preserve current work. Tab navigation alone does not trigger a reminder.


## Calculate a network

Enter an IPv6 CIDR such as **2026:1015:abcd::/48**, then a target prefix such as **64** without a slash. Source and target prefixes range from 0 to 128; the target must be at least the source prefix. Click Calculate or press Enter in either input. Uppercase hexadecimal is normalized to lowercase; host bits are normalized to the containing network.

The summary contains the network range, subnet count, addresses per subnet and additional subnet bits. IPv6 has no broadcast address; the last address is the maximum address in the range. Address capacity is a mathematical count, not an assignable-host guarantee. Review address-use guidance before deployment.

## Browse, select and locate

Results load one page at a time, with 25, 50, 100 or 200 records. Page indices and address counts retain integer precision even for the full IPv6 space. Use the navigation icons or enter a page number.

Choose a location mode: IPv6 address, subnet index, address range or index range. Ranges include both endpoints. Location selects the first matching row and preserves range highlighting across pages. Clear highlighting and Clear selection are separate actions. Ctrl+click and Shift+click select records; Ctrl+A selects the current page, Ctrl+C copies and Esc clears manual selection. Double-click or press Enter for subnet details.

## Copy and export

Copy selected subnets, the entire page, a bounded index range, exact statistics or the calculation summary using the relevant icons. Tooltips explain each action. Range copying is limited to 5,000 records per operation; export larger sets.

Export all subnets or an index range to TXT or Excel (XLSX). A worksheet supports 1,048,575 data rows plus its header; use TXT above this limit. Review size estimates and available space before very large exports. Cancelling removes incomplete temporary files and preserves an existing destination. Excel headers and the worksheet name use the interface language at export start. English output uses “No.”, “IPv6 Subnet” and the worksheet name “IPv6 Subnets”; Chinese output retains its original Chinese labels. Switching languages during export does not change that file. TXT contains one CIDR per line. Addresses, selected ranges and exact index values are unchanged.

## Calculation plans and drag-and-drop

Save the last successful calculation, name, notes, page size, current page, range, page selection and active calculation/tool tab as JSON. Use Ctrl+S, Ctrl+Shift+S for Save As or Ctrl+O to open. Recalculate edited parameters before saving.

Drop one local .json plan anywhere in the main window, including inputs and tables. Validation precedes any replacement. Save, Discard or Cancel protects unsaved work; otherwise confirm replacement. The file is checked again after confirmation. Invalid files and cancellation preserve current work. Source files are not modified by importing, and no extra calculation or export action is triggered beyond restoring the saved calculation/view.

Multiple files, folders, remote links and unsupported formats are rejected. TXT/CIDR lists use Subnet List's Import icon. Finish or cancel background work before dropping a plan. Windows may block Explorer drops into an elevated application; use Open Plan in that case.

## Address tools

Convert one IPv6 address without a prefix or zone identifier into canonical lowercase compression, full expansion and binary. Binary is displayed in 16-bit groups and copied as 128 consecutive bits. IPv4-mapped IPv6 notation is supported.

Two-network analysis identifies equality, containment in either direction, adjacency or separation, with exact overlapping and gap address counts. Adjacency alone does not imply the two CIDRs can merge into one. These tools do not change the calculator's parameters or result.

## Subnet lists

Paste or import a UTF-8 TXT/CIDR file (BOM allowed), one CIDR per line. Blank lines and whole-line # comments are ignored; inline comments, CSV and spreadsheets are unsupported. Limits apply independently: **5,000 validation entries**, **1,048,576 UTF-8 bytes (1 MiB)** and **20,000 physical lines**, including blank/comment lines. Byte size is not a line count.

Validation retains source line numbers and original input. Invalid entries are excluded from relationship checks. Duplicate, containment and adjacent pairs are counted exactly; at most 1,000 detail pairs are retained. Copy normalized valid unique networks or the report. This deduplication does not remove contained networks or merge adjacent ranges. Background tasks can be cancelled without editing input or source files.

## Free space and aggregation

Free Space subtracts the union of occupied entries from the parent network. Every occupied entry must be valid and fully inside the parent; otherwise the entire operation is rejected. An empty list means the full parent is free. Counts are exact integers; overlapping or duplicate occupied entries are counted once.

Free CIDR details are capped at 5,000 while the exact CIDR total and every free interval remain available in the report. Copying a complete CIDR list is disabled if details are truncated. Exact address capacities are available in tooltips and reports.

Aggregation removes duplicate and covered networks and merges only precisely representable adjacent ranges. It preserves exact address coverage without rewriting input, but does not retain allocation hierarchy or business boundaries. Review those boundaries before deployment. Editing inputs invalidates old planning results; editing the parent clears only Free Space. Lists and planning results are not stored in calculation plans; copy input/reports to retain them.

## Language, themes and help

The upper-right icons are **Language → Theme → About**. The globe menu offers 简体中文 and English. Switching is immediate and preserves inputs, results, pages, selections, location highlighting and list/planning state. The language preference is saved for the next launch. User names, notes, paths, input text and original third-party licenses are not translated.

The moon/sun icon or Ctrl+Shift+T switches Light/Dark and remembers the theme. F1 opens the reusable non-modal About window with information, this guide, third-party licenses and legal information. Esc closes dialogs. No Internet connection is required for calculation, switching languages or reading bundled documents.

## Input feedback

Invalid input receives a red border, warning indicator and specific explanation; bottom errors are bold. Editing clears the corresponding field marker and the next action validates again. List errors retain physical line numbers. Copy/export range errors appear inside their dialogs. A plan-file error marks the file status rather than valid current parameters.


## English samples

The source examples include `SubnetList_EN.txt`, `PlanningNetworks_EN.txt` and `OfficeNetwork_EN.json`. Their CIDRs, calculation parameters and view state match the Chinese samples; comments, names and notes use English. Choose a file according to your reading preference. Switching interface languages preserves imported text.


## Address range to CIDR

In Address Tools, enter inclusive first and last IPv6 addresses, then use the conversion icon or press Enter. Supports one address through the complete IPv6 space. The last address must be at least the first; omit CIDR prefixes and zone identifiers. Results cover exactly the range using minimal CIDRs and show an exact address count. Editing either address invalidates old results.

Icons copy the CIDR list or full report, or send the results to Subnet List for automatic checking. Different existing input requires confirmation with No as the default. Busy list tasks block transfer. Calculator results and calculation plans are preserved.


## Save and reuse list/planning text

Use the save icon above Subnet List:
- Original Input saves current editor text, including comments, blank lines and errors, even before checking.
- Valid Deduplicated CIDRs saves valid normalized networks in first-occurrence order after a successful check. Error rows remain available in the report.
- Check Report saves error records, exact totals and bounded relationship details.

The Free Space and Aggregation save icons offer complete CIDRs or planning reports. CIDR TXT has one network per line and can be reimported; reports are for reading and archiving. Truncated free-space details disable complete CIDR saving and transfer, while reports retain all free address intervals and exact counts. A zero-free-space result still supports a report.

Reports use the interface language at actual save time; original input stays unchanged. Overwriting requires confirmation, and failed writes preserve the existing file. If input/results change while a dialog is open, start saving again.

The Send Back for Checking icon returns complete planning results to Subnet List. Different existing input requires confirmation with No as the default. Accepted transfer clears old analysis and starts a new check. Busy tasks block transfer.

## Subnet allocation suggestions

Calculate the parent and occupied list in Free Space, then open Allocation. Enter a target prefix (64 or /64) and a count from 1 to 5,000. Click the calculation icon or press Enter. The target prefix must be at least as long as the parent prefix. Capacity counts aligned CIDR blocks; candidates start at the lowest available address. Insufficient capacity produces an exact count without partial suggestions.

Suggestions are not reserved. Copy CIDRs or a report, or save TXT. Confirm the append icon to retain existing content and comments, append candidates as occupied networks and recalculate free space. Record, byte and physical-line limits reject the append without changing input. Changes to the list, parent or request parameters invalidate old suggestions. Calculation plans and network device configuration are unaffected.


## List lookup and coverage comparison

- Added address membership lookup: list all containing networks and original line numbers, longest prefix first, including duplicates and containing entries.
- Added coverage comparison: compare the current list with pasted or imported TXT / planning project lists, with exact added, removed and common address counts and complete ranges. Equivalent CIDR splits do not create false changes.
- Open both tools from the lookup icon at the top of Subnet List. They use a snapshot from when the window opened and support copying and conflict-safe TXT report saving. Editing inputs clears old results.
- Each list retains the 5,000-record, 1 MiB and 20,000-line limits. Empty lists support all-added or all-removed comparisons. Correct invalid records before querying or comparing.


## Candidate Network Availability

- Added Network Availability in the list tools window opened from the third, target-shaped icon at the top of Subnet List. Enter a candidate IPv6 CIDR to determine whether it is entirely free, partially occupied or fully occupied relative to the occupied list.
- Reports preserve all original conflicting line numbers, including duplicates and containing entries. Occupancy counts the union within the candidate only; disjoint entries do not affect the result. Host bits are normalized.
- Copy or save minimal CIDRs for free or occupied coverage within the candidate. Empty results and outputs exceeding 5,000 CIDRs cannot produce empty or partial lists; complete range reports remain available. Nothing is appended or allocated automatically.
- Editing the candidate clears stale results. Saves retain overwrite confirmation and conflict protection. The window uses the list snapshot taken when opened; reopen to refresh it. Query parameters and results are not stored in planning project JSON.

## Free Capacity Overview

- Added a Free Capacity Overview tab in the Subnet List lookup window. Enter a parent network to count complete, aligned available subnets at every prefix from the parent prefix through /128.
- Shows free addresses, occupied union size, the largest available subnet and fragmented addresses that cannot form a complete subnet at each prefix. Equal-sized largest subnets use the lowest address.
- Uses complete free ranges even when the 5,000-CIDR preview is truncated. Counts are exact integers without enumerating IPv6 addresses. Rows partition the same free space differently and must not be added together.
- Copy bilingual reports or save TXT with overwrite confirmation and conflict protection. Editing the parent clears results. The list snapshot is taken when the window opens; original projects are unchanged. Reopen to use an updated list.
- All occupied records must be valid and contained within the parent; an empty list leaves the entire parent free. Overview inputs and results are not stored in planning project JSON; save the report to retain them.

## CIDR Output for Lookup and Coverage Results

- Copy or save matching CIDRs from address lookup: normalized, deduplicated and ordered by longest prefix, retaining containing networks. Reports still preserve original line numbers and duplicate records.
- Select added, removed or common coverage and produce its exact minimal CIDR list. Copy or save TXT for reimport into Subnet List.
- Show the selected CIDR count. Empty categories cannot produce empty files; results exceeding 5,000 CIDRs disable list output while complete range reports remain available.
- Editing inputs invalidates output. Changing category or recalculating during a save dialog aborts stale output; overwrite confirmation and save conflict protection still apply.



## Batch Network Availability

Open Subnet List → the target-shaped lookup icon in the top row → Batch Availability. Enter one candidate CIDR per line, up to 5,000 (1 MiB and 20,000 physical lines per list). The baseline snapshot allows an empty occupied list; candidates cannot be empty. Invalid records reject the whole batch.

Example: baseline `2001:db8::/127`; candidates `2001:db8::/126`, `2001:db8::4/126`, and `2001:db8::/127` give partially occupied (2 occupied/2 free), entirely free (0/4), and fully occupied (2/0). Copy/save a complete report or deduplicated entirely free candidate CIDRs. Edits clear results; save guards reject stale output.

Candidates are independent and do not reserve space for each other. Duplicates and containment count as overlapping candidates; adjacent candidates do not. Entirely free candidates may overlap and cannot be assumed allocatable together. Address counts must not be added across overlaps. Results do not change the original list and are not saved in planning project JSON.

## About and Project Website

Use the upper-right information icon or F1. Program Information provides clickable project home and release-download links, opened only on click in the system browser. The other tabs provide offline help, original component licenses and legal information. Close with the title-bar close button or Esc; select text to copy. Language/theme changes do not open a browser.


## Batch candidate status output

Select entirely free, partially occupied, fully occupied, conflicting or all candidates in Batch Availability. The adjacent copy/save buttons output whole normalized candidate CIDRs, not their free/occupied fragments. Results are deduplicated in first-input order and retain containment. The full report is unaffected. For baseline `::/127` and candidate `::/126`, partially occupied output is `::/126`, while its free fragment is `::2/127`; use the single-network availability tab to output fragments. Empty categories disable CIDR output; category changes during saving cancel stale output.

## Input and containing network

In Batch Availability, “Input” retains your text and “containing network” shows the normalized CIDR. These labels do not indicate sorting or a range. For example, `2026:1051:3000:311a::/61` belongs to `2026:1051:3000:3118::/61`: the last three host bits are cleared; the fourth group spans `3118` through `311f`. Candidate records remain in input order.

## Copy address tool results

Address conversion and network relationship results use right-click menus instead of copy icons. Select text and choose Copy selected text; right-click a format for Copy current format / Copy continuous 128 bits or Copy all address formats. Right-click relationship results for the complete report. Editing input clears stale results and disables the associated copy actions.

## Batch candidate details

After a successful batch check, choose a Candidate number (input order) above the report and click the adjacent locate icon. Numbers start at 1 and count valid candidates, excluding blank/comment lines; duplicate candidates remain separate. Details show the candidate number, original physical line number and containing network. The original input is read-only.

Details use the same baseline snapshot. Reports retain all intersecting baseline records and their original source lines, including duplicates and containment, plus exact free/occupied ranges. Choose Free CIDRs inside candidate or Occupied CIDRs inside candidate to copy/save internal fragments, unlike the batch page's whole candidate output. Empty or over-5,000 CIDR outputs are disabled; the complete range report remains available.

Example: baseline `::/127` and `::3/128`, candidate `::3/126`. Its containing network is `::/126`, three addresses are occupied and the free CIDR is `::2/128`. Occupied CIDRs are `::/127` and `::3/128`. Copying does not change the baseline.

Changing candidate number, editing batch input or closing inspection clears old details and rejects pending stale saves. Closing details or pressing Esc preserves batch results; reopen with the icon. Close and reopen inspection to refresh its baseline snapshot.

Use the Previous candidate details / Next candidate details icons in the fixed bottom navigation bar to browse in the same window and synchronize the batch-page index. The corresponding button is disabled at either boundary. Switching retains the free/occupied CIDR category, clears the old report and computes details for the current candidate. Duplicate candidates remain separate items, and switching during a save rejects the old output. For example, with `::3/126`, `::4/126`, `::3/126`, Next moves from item 1 to item 2 and then item 3, preserving the distinct physical lines of the duplicate entries.

## Import batch candidates

The folder icon below Batch Availability input imports UTF-8 TXT/CIDR (BOM allowed) or planning-project JSON. JSON imports list text only, without restoring the parent network, allocation parameters, result tab or baseline. Comments, blank lines and duplicates are retained. Click Check after import to generate results.

Limits remain 1 MiB of UTF-8 text, 20,000 physical lines and 5,000 candidates. Replacing existing input requires confirmation, defaulting to No. Cancellation, encoding/format/size errors, empty lists or input/result changes during dialogs preserve current candidates and results. Successfully importing different text clears old reports and details.

Example: import a TXT containing `# candidates`, `::3/126` and `::4/126`. The baseline remains the main-window snapshot. Against `::/127`, the two candidates are partially occupied and entirely free.

Only ordinary files are imported. Devices and pipes are rejected; retry after writing finishes if a file changes or is replaced during reading. Ordinary files on network shares may still be delayed by networking or filesystem behavior; this policy does not provide network access timeouts.

The planning JSON container is limited to 7 MiB to allow JSON escaping; its imported list still has the 1 MiB UTF-8 text limit.

The bottom bar uses the same icon style as Subnet Results. First/Last moves to either boundary. Enter an index from 1 through the candidate count, then press Enter or click Go. For example, `3` opens item 3; the total count appears on the right. Invalid or out-of-range input is marked without changing the report. The bar stays below the report and does not scroll with it.

## Browse candidate details by status

The Browse selector below the report controls detail navigation and range reports: all candidates, entirely free, partly occupied, fully occupied or any occupied overlap (partial or full). First/Previous/Next/Last moves between matching entries while preserving original candidate numbers and duplicates. Changing the filter keeps the current candidate when it still matches; otherwise it shows the first match. Matched/Total counts candidate records; the bottom count is the number matching this filter.

Example: baseline `::/127` and `::3/128`; candidates in order `::3/126`, `::4/126`, `::3/126`, `::/127`. Partly occupied matches original items 1 and 3: Next moves from 1 to 3. Any occupied overlap matches 1, 3 and 4.

The index field takes the original candidate number. Click Go or press Enter. In the partial filter, `3` opens item 3; `2` is rejected without changing the report. Select All candidates to reach a nonmatching entry. An empty filter clears old input/reports and disables navigation, jumps and report/CIDR output; another filter restores browsing. A filter change rejects pending saves of old details, even when the current candidate still matches.

Browsing filters do not alter the baseline, candidate input, full batch report, batch CIDR output category or internal free/occupied CIDR category. Inspection still uses the baseline snapshot from when the window opened. Reopening details defaults to All candidates.

## Copy and save the current range report

Choose Browse at the bottom of candidate details, then use Report → Copy current range report or Save current range report as TXT. The report contains all matching candidates, with original indices, physical source lines, duplicates, input, normalized networks, status, exact occupied/free address counts and overlap counts from all original candidates.

Example: baseline `::/127` and `::3/128`; candidates `::3/126`, `::4/126`, `::3/126`, `::/127`. Select Partially occupied and copy the range report. It contains original items 1 and 3, keeping both duplicate records, and shows two matches out of four original candidates. All candidates outputs all four. Comments and blank lines still count toward physical source line numbers.

The range report includes every match. The existing report copy/save controls above it still operate on the current single candidate. The full batch report and batch CIDR output category remain independent. Reports use the language at copy time or actual save time; original user input is preserved. Empty filters disable the menu and never create empty files.

Navigation within the same range does not invalidate saving the complete range report. Changing the filter, editing candidate input or closing details during file selection or overwrite confirmation cancels the old save. Changing away and back to the same filter also cancels it. Cancellation preserves current work; overwrite confirmation and save conflict protection apply.

## Inspect candidate overlap sources

Open candidate details and scroll down to Candidate Overlap Details. It lists other overlapping candidates with their original numbers, physical source lines, original input, normalized networks, equality/containment relationships, intersection CIDRs and exact address counts. The current record is excluded; other duplicate records remain separate. Adjacent disjoint networks are excluded.

Example candidates: `::3/126`, `::/127`, `::3/126`, `::4/126`. Item 1 normalizes to `::/126`: it contains item 2, with intersection `::/127` and two addresses; item 3 is equal, with intersection `::/126` and four addresses. Item 4 is adjacent and is not listed. Intersections may cover the same addresses and their counts must not be added directly.

Sources use all candidates from the batch, including entries outside the browsing filter. Candidate overlaps and baseline occupancy are shown separately: a candidate entirely free against the baseline can still overlap another candidate. Only the current item is analyzed on demand; no all-pairs detail matrix or candidate reservations are created.

The existing detail report copy/save controls include both baseline availability and candidate overlaps. Internal free/occupied CIDR controls still output fragments relative to the baseline. The Report menu outputs the selected range’s record summaries and original overlap counts. Navigation, empty filters, candidate edits and closure clear old overlap evidence and reject stale complete-report saves.

## Export the Current Range as CSV

After a batch candidate check in Subnet List → Query → Batch Candidates, open candidate details, choose Browse, then Report → Save current range as CSV. The default filename is `IPv6_BatchRange_<category>.csv`. A missing extension is completed with `.csv`; other extensions are rejected. Empty ranges disable output.

Each candidate becomes one data record. Columns are: candidate index, original line, original input, normalized network, availability, occupied addresses, free addresses, overlapping candidate records (all candidates), and host bits normalized. Indices start at 1; physical lines include comments and blank lines. Input order and duplicates are retained. Overlap counts still refer to all candidates, including those outside the filter. No summary row is added.

For example, use baseline `::/127` and `::3/128`, with candidates `::3/126`, `::4/126`, `::3/126`, `::/127`. Exporting the partly occupied range produces original candidates 1 and 3. Both have normalized network `::/126`, occupied count 3, free count 1, overlap-record count 2 and host normalization Yes. Comments or blank lines before them increase their original line numbers.

Files use UTF-8 with BOM, standard CSV quotes, comma separators and CRLF line endings. Headers, statuses and Yes/No use the language at actual save time; original input stays unchanged. Counts are full decimal digits. **CSV quoting does not force Excel to treat cells as text**: use Data → From Text/CSV and set occupied/free address-count columns to Text before loading. For example, `::/0` against an empty baseline has `340282366920938463463374607431768211456` free addresses. Double-clicking the CSV can let Excel round large numbers automatically. Candidate address counts may overlap and cannot be added as an allocatable total.

Overwrite confirmation and save conflict protection apply. Changing the filter, including away and back, editing candidates or closing details during file selection or confirmation stops pending output. Navigation inside the same range remains valid. TXT reports, CIDR output and list content remain separate.

## Export the Current Range as Excel (XLSX)

In candidate details, choose Browse, then Report → Save current range as Excel (XLSX). The default filename is `IPv6_BatchRange_<category>.xlsx`; a missing extension is completed with `.xlsx`, and other extensions are rejected. Empty ranges disable output.

Excel contains the same nine columns and all matching records as CSV, retaining input order, original candidate numbers, physical lines and duplicates. The worksheet name, headers, statuses and Yes/No follow the language at actual save time. The first row is frozen; headers have filters, with readable widths and wrapped text.

Occupied/free address-count columns are explicitly text cells. **Opening XLSX directly preserves complete integers without the text-import setup required for CSV.** Original indices, source lines and overlap-record counts are sortable numeric cells; IPv6 and original input are text. There are no address-count sum formulas: overlapping candidate counts cannot be added as an allocatable total.

For example, check `::/0` against an empty baseline and export All candidates. The free-count cell retains `340282366920938463463374607431768211456`. The earlier partly occupied example exports only original candidates 1 and 3, including both duplicates. As with CSV/TXT, cancellation, filter changes (including away and back), candidate edits or closing stop pending old output. Overwrite confirmation applies, and changes by another program preserve that program's content.

Scroll down in Address Tools to find IPv6 and Reverse DNS Conversion and IPv6 Address Offset. Tools work independently and do not modify calculation plans, lists, network settings or DNS records. Press Enter in any input or click its calculation icon.

## IPv6 and Reverse DNS Conversion

| Setting / action | Meaning | Example |
|---|---|---|
| IPv6 or reverse DNS name | One IPv6 address or a complete ip6.arpa name with 32 single hexadecimal labels | `2001:db8::1` |
| Calculate / Enter | Detect the conversion direction and show a normalized address and name | Paste the name to recover the address |
| Right-click → Copy reverse DNS name | Copy the normalized lowercase name without a trailing root dot | Check a PTR owner name |
| Right-click → Copy IPv6 address | Copy only the corresponding address | `2001:db8::1` |
| Right-click → Copy complete tool report | Copy the address, name and operating boundaries | Keep a planning record |

For example, `::1` produces `1.` followed by 31 instances of `0.` and then `ip6.arpa`. Pasting the complete name back restores `::1`. Uppercase labels and a single trailing root dot are accepted. Reverse zones, wildcards, URLs, IPv4 addresses and scoped addresses containing `%` are rejected. Mapped IPv6 addresses use all 128 bits. See [RFC 3596 §2.5](https://www.rfc-editor.org/rfc/rfc3596.html#section-2.5).

This converts addresses and names only. It does not look up hostnames, contact DNS, verify PTR existence or create records. Editing clears the previous report and disables result copying; correct invalid input and convert again.


## IPv6 Address Offset

| Setting / action | Meaning | Example |
|---|---|---|
| Starting address | A single IPv6 address without CIDR or a scope identifier | `2001:db8::10` |
| Offset | Decimal integer, optional `+` or `-`, at most 39 digits; no hexadecimal, fractions or exponent notation | `16`, `-1`, `0` |
| Restricted network (optional) | Blank allows all IPv6 space; a CIDR requires both input and output inside it. Host bits are normalized | `2001:db8::/64` |
| Calculate / Enter | Use exact 128-bit arithmetic; restricted results also show distances from the first and last network addresses | `::ffff + 1` → `::1:0` |
| Right-click → Copy result address | Copy only the resulting IPv6 address | `2001:db8::20` |
| Right-click → Copy complete tool report | Include input, decimal offset, result and optional network/distances | Keep the planning calculation |

The default `2001:db8::10` plus decimal `16` gives `2001:db8::20`. An offset of `-1` gives `2001:db8::f`; zero keeps the same address. Within `::/126`, `::1 + 1` gives `::2`, two addresses from the start and one from the end. `::3 + 1` is rejected as outside that network. `:: - 1` and the maximum IPv6 address plus 1 are rejected without wrapping.

Editing clears old results and disables copying until recalculation. Reports follow the interface language; switching language preserves input and results. Mathematical results do not prove allocation or deployment suitability. Both tools support light/dark themes and remain reachable by scrolling when the page exceeds the window.
