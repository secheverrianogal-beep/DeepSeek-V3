# Codex Windows triage notes — 19 October 2026

This is a status/evidence note for the open Codex Windows issues linked from the Linear queue. It is not a root-cause claim or a source-code patch. Re-check issue state before acting; observations and hypotheses are kept separate.

## 1. MXC read-grant checkout denial — [#55032](https://github.com/openai/codex/issues/55032)

**State:** open. [#55031](https://github.com/openai/codex/issues/55031) has the same title and effectively identical report and is closed as a duplicate of #55032. Treat #55032 as the canonical issue; do not open another duplicate.

**Evidence in the report:** Codex 0.162.0 on Windows with MXC launched Git using `git -C <checkout> rev-parse --verify HEAD`; Git returned 128 with “cannot change to ... Permission denied” despite the requested explicit checkout read grant being present in the compared configuration. The actual Git OS working directory, security token and rejecting native rule were not captured. The raw resolved policy was not retained, and the reported minimal reproduction was not independently executed.

**Do not infer:** that ancestor traversal, policy translation, child enforcement, or a host filesystem rule is the cause. The source references and unit test mentioned in the issue do not establish which layer rejected this process.

**Useful next evidence:** preserve a sanitized complete resolved policy and native diagnostics for the child process, record the effective OS identity/token and actual cwd, and run the exact read-only reproduction against the pinned binary/source pair. Compare a permitted checkout with a protected-path negative control. Do not broaden root/parent permissions or relax containment as a diagnostic shortcut.

## 2. MSYS2/mintty newline shortcuts — [#55034](https://github.com/openai/codex/issues/55034)

**State:** open; the latest thread describes a local workaround and a proposed normalization path, but no PR/diff link was included in the comment inspected.

**Evidence in the thread:** a local workaround maps exactly `Enter + CONTROL` to `Enter + SHIFT` only on Windows when `MSYSTEM` and `TERM_PROGRAM=mintty` are present. Two normalization tests and the release build are reported as passing locally; the unpatched interactive reproduction on 0.163.0 and the full Rust test build remain unverified in the report.

**Main risk:** the mapping may steal an intentional Ctrl+Enter binding. The existing tests exercise normalization, not the complete Win32/mintty keyboard event pipeline.

**Next step:** publish the actual diff and exact test commands/results; inspect where Win32 input records are converted into TUI events; capture the relevant event sequence on affected and unaffected terminals. Keep the workaround environment-gated unless an underlying fix is demonstrated. Preserve Ctrl+Shift+Enter and all non-target combinations.

## 3. Unexpected camera permission in the Windows in-app browser — [#55072](https://github.com/openai/codex/issues/55072)

**State:** open. The primary report and a follow-up observation describe camera permission prompts and Windows Media Foundation camera initialization around ordinary in-app browsing.

**Evidence:** the reports describe OS permission prompts and FrameServer/DeviceMFT initialization/configuration events. A follow-up says the article still opened with camera permission denied and did not trigger a prompt in Microsoft Edge. The initiating process/origin/API and whether frames were acquired or transmitted remain unestablished.

**Do not allege:** recording, exfiltration, malicious behavior, or that a specific page/Cloudflare initiated the request. Initialization events alone do not prove frame capture or transmission.

**Next step:** identify the initiating first-party process/component and requesting origin/API using supported diagnostics, then determine whether device enumeration can trigger the prompt. Reproduce with permission denied and compare the in-app browser with Edge without collecting camera data or private browsing logs. Treat as a privacy-sensitive investigation, not a confirmed vulnerability until the request path is attributed.

## Acceptance discipline

- Keep issue state separate from reproduction status and from CI status.
- Record the exact binary/source revision and environment for every test.
- Do not claim a fix based on a workaround, static inspection, or author-reported tests alone.
- Prefer one focused regression test for the identified boundary and a negative control; avoid duplicate comments or broad permission changes.
