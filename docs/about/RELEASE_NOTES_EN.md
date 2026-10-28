# Release Notes

## V1.19 Batch Candidate Import and Runtime Update

- Revision: fixes unchanged Windows files being reported as modified during reading, restoring calculation-plan, planning-project and candidate imports.

- Batch Availability imports TXT/CIDR and planning-project JSON; JSON uses list text only, retaining comments, blank lines and duplicate candidates.
- Replacing candidates requires confirmation. Cancellation, file errors or dialog-time content changes preserve existing input/results; imported content is checked explicitly afterward.
- Improves ordinary-file reading and change messages; list tooltips display special characters literally.
- Updates PyQt6 and Qt runtime components to 6.12.0 from Riverbank's official pre-release index, retaining the existing PyQt interface and one-file build.
- Retains candidate details, internal CIDR output, address-tool context menus and About formatting; updates both languages and matching screenshots.
