# Internationalization Checks

[简体中文](INTERNATIONALIZATION_CI.md)

These checks adapt the goals of UnattendLocal V1.23 to this project's existing PyQt TS/QM architecture. They do not introduce its WPF or JSON localization runtime. This is a V1.15 maintenance update; existing functionality and screenshots remain unchanged.

## Coverage

Checks reject duplicate contexts/sources, missing or unfinished translations, untranslated Chinese, missing source messages, dynamic translation templates and incompatible placeholders/format specifiers. Native language names remain supported. TS and shipped QM must agree entry by entry. TS checkout newline conversion is normalized, while QM integrity remains byte-exact.

`assets/i18n/app_en.contracts.json` records the full active message set, source hashes and derived rules. Missing/extra/duplicate entries, stale hashes and weakened rules fail. Technical tokens such as encoding, shortcuts and URLs remain intact. Qt file filter patterns and order, resource paths and filename templates must not be translated. Structured messages preserve line count and per-line format fields. The source record is not automatic semantic approval of a translation.

Localized screenshot references retain their existing locale/hash checks. Chinese documents use Chinese screenshots and `_EN.md` documents use English screenshots. Metadata checks do not replace visual inspection.

## GitHub workflow

The standalone `i18n-check.yml` has a stable `i18n required gate`. PR detection uses the complete `base...head` diff and NUL-separated paths. Push/manual runs validate fully. Relevant resource/runtime/test/tool/document/dependency changes run catalog checks and Windows localization regressions. Unrelated PRs may intentionally skip both validation jobs. Failed/cancelled detection, failed/skipped relevant checks or unknown states cannot pass the final gate.

No EXE publishing or automatic PR comments are added. Existing full Windows/Linux regression jobs remain intact.

## Local maintenance

Install application and CI requirements, then run `python tools/check_i18n.py --report verification/i18n.json` and `python tools/check_doc_images.py`. After reviewing source changes, update contracts with `python tools/update_i18n_contracts.py`, complete translations and compile using `python tools/update_translations.py --lrelease PATH`. Do not refresh records blindly to bypass checks. Failed staged compilation preserves the shipped QM.

Local builds and verification execute these checks. Commit the TS, QM, generation record, source contracts and related source/tests together. No new screenshots are needed for this maintenance update.
