# Cross-project issue remediation proposals

**Prepared:** 2026-10-14. Personal engineering notes, not an official statement from Google or DeepSeek.

## Scope and evidence

The connected GitHub account has write access to `secheverrianogal-beep/DeepSeek-V3` and `secheverrianogal-beep/Cv`; it does not currently expose writable personal forks of Google AI Edge Gallery or LiteRT-LM. This catalog is therefore a research record in the available DeepSeek-V3 fork, **not source code fixing those projects**. Apply each source change to the correct repository and test it before calling it fixed.

Evidence labels: **Source-observed** = code-path evidence in issue; **Reported** = reporter supplied logs or reproduction, not independently rerun here; **Hypothesis** = root cause needs debugging; **Unverified** = no passing regression in the affected source repository was confirmed here.

## A. Google AI Edge Gallery

### [#1324 — secret prefix logged; short secret may throw](https://github.com/google-ai-edge/gallery/issues/1324)
**Source-observed; runtime not independently reproduced.** Remove secret interpolation such as `secret.substring(0, 3)` from logs; log only a non-sensitive status. Validate any required minimum length before storing or running the skill, rather than using `substring` as validation. Tests: dummy values of lengths 0, 1, 2, 3 and normal length; controlled validation/no crash; assert neither full secret nor prefix appears in logs, errors or analytics.

### [#1325 — credentials may be included in Android backups](https://github.com/google-ai-edge/gallery/issues/1325)
**Potential risk; actual exposure unconfirmed.** Prefer separating skill secrets and access/refresh tokens from `user_data.pb` so excluding credentials does not remove chat history. Use a credential-specific store protected with Android Keystore-backed encryption, add active exclusions to legacy and Android 12+ cloud/device-transfer backup rules using the verified domain/path, and migrate transactionally. Test with dummy credentials by inspecting backup/restore, migration interruption, missing Keystore keys and non-sensitive history preservation. Check the merged manifest per build variant.

### [#1323 — iOS Agent Skills requires missing `skillName`](https://github.com/google-ai-edge/gallery/issues/1323)
**Reported.** Align the payload producer with the Swift `Decodable` schema. If supported legacy payloads omit `skillName`, implement explicit compatibility decoding only when a canonical fallback exists; do not default to an empty name or select another skill silently. Validate before execution and surface a recoverable error. Test current/legacy/malformed payloads and an end-to-end iOS skill call.

### [#1326 — Gemma 4 GPU bundle/runtime incompatibility](https://github.com/google-ai-edge/gallery/issues/1326)
**Reported on specific device/runtime combinations; not proof GPU is universally broken.** Add bundle compatibility metadata (required signatures/subgraphs, model revision and tested LiteRT-LM runtime range); validate prefill/decode plus vision/audio sections during packaging and before engine creation. On mismatch, report the missing section and compatible runtime rather than silently rewriting the bundle. Test CPU/GPU bundles, missing-signature fixtures and a runtime/device compatibility matrix.

### [#1317 — Qwen2.5 template string/sequence type error closes chat](https://github.com/google-ai-edge/gallery/issues/1317)
**Reported; exact expression must be verified against the bundled template.** Investigate the template `+` operation reported to receive a string and sequence. Fix the incompatible template/data boundary without blindly stringifying structured multimodal/tool content; normalize only documented text content. Catch template-render errors at the inference/UI boundary and show a recoverable error instead of terminating the app. Test plain text, list-of-parts, tool path where supported, CPU/GPU and malformed template.

### [#1297 — temporary system freeze during GPU loading](https://github.com/google-ai-edge/gallery/issues/1297)
**Insufficient diagnostics to assert a root cause.** Capture logcat/bug report and Perfetto trace across model load; record exact model, quantization, app/OS build, free memory and freeze duration. Instrument decompression/mmap, GPU delegate init, allocation, warm-up and UI frames; compare CPU/GPU and cold/warm load. If main-thread blocking is shown, move orchestration off-thread and provide progress/cancellation; if native delegate stalls, create a minimal runtime repro before changing priorities/timeouts. Verify with an on-device trace.

### [#1278 — web-fetch fails and no-skill fallback missing](https://github.com/google-ai-edge/gallery/issues/1278) and [#1307 — improve skill selection](https://github.com/google-ai-edge/gallery/issues/1307)
**Reported; network root cause partly hypothetical.** Treat “no applicable skill” as a valid router outcome: with zero skills or low routing confidence, pass the original request to normal model chat; do not force an irrelevant skill. For web-fetch, avoid broadly weakening WebView isolation. Prefer a narrow native HTTP(S) bridge that rejects `file:`, `content:`, `javascript:`, localhost/private/link-local targets and unsafe redirects, revalidates redirects/network destinations, caps response size/time and returns clear errors. Test zero/irrelevant/matching skills; public fetch, redirects, timeouts, invalid schemes, private destinations and offline mode. Measure direct-answer success, unnecessary tool calls, latency and memory.

## B. LiteRT-LM

### [#3947 — rewind boundary token lacks prefill embeddings](https://github.com/google-ai-edge/LiteRT-LM/issues/3947)
**Source-level; output regression not independently passing yet.** In `RollBackProcessedTokens()`, preserve the token-ID path. For embedding-input models, populate the reconstructed pending boundary token's normal embedding through the prefill lookup, and per-layer embedding when the signature requires it. Return failed-precondition if required lookup is unavailable. Test nonzero rewind followed by a different suffix, per-layer embeddings, missing lookup, token-ID model, zero-position rewind and multimodal control; compare against a clean run.

### [#3944 — JSON constraints fail with speculative/MTP decoding](https://github.com/google-ai-edge/LiteRT-LM/issues/3944)
**Controlled report; internal root cause remains a hypothesis.** Keep draft grammar state separate from the authoritative verifier/accepted-token state; commit only tokens valid under the current constraint and never accept tokens past the grammar stop state. Until supported, reject at setup or fall back to non-speculative constrained decoding for that request only. Test 60+ prompts, nested schema and `UNSUPPORTED` enum values; every successful output must parse and conform, with stop/cancel and CPU/GPU controls.

### [#3932 — C API greedy/Top-K samplers on CPU](https://github.com/google-ai-edge/LiteRT-LM/issues/3932)
**Source-observed/reported.** Publish backend-by-sampler capability. Implement CPU greedy/Top-K if supported; otherwise reject during config/session creation, not first send. Never silently substitute a requested sampler. Scope sampler instances to sessions or key reuse by full type/parameters so a Top-P session cannot contaminate a later greedy/Top-K session. Test Top-P→greedy→Top-K and reverse order in one engine, repeated sends, plus docs for every backend. Include the reported #2080 reuse interaction.

### [#3948 — C API setter for preface prefill on init](https://github.com/google-ai-edge/LiteRT-LM/issues/3948)
Add a false-by-default flag to `LiteRtLmConversationConfig` and a public setter `litert_lm_conversation_config_set_prefill_preface_on_init(LiteRtLmConversationConfig*, bool)`; forward it to the existing C++ builder. Document that computation moves to conversation creation rather than disappearing. Test default behavior, eager prefill without a dummy user turn/assistant reply, long prefaces and unchanged behavior in other APIs.

### [#3949 — conversation-level checkpoint and rollback](https://github.com/google-ai-edge/LiteRT-LM/issues/3949)
A checkpoint must snapshot native session position **and** conversation history, append state, processor/channel-filter state. Add save/restore/delete to C++ and C. Restore atomically; retain checkpoint for repeat rollback; invalidate later checkpoints only after successful restore; reject unsupported multimodal/NPU modes early. Test temporary third turn → rewind → alternative third turn, repeated restore, overwrite/delete, failure injection, disposal and unsupported backends. #3947 remains a distinct embedding-input regression that checkpoint tests should cover.

### [#3929 — EmbeddingGemma 2 task prefixes disagree with model card](https://github.com/google-ai-edge/LiteRT-LM/issues/3929)
Update docs from the pinned model revision and config, not intuition. The report gives these prefixes; verify exact strings against the targeted revision before merging: search query `task: search result | query: `; document `title: none | text: `; classification `task: classification | query: `; clustering `task: clustering | query: `; sentence similarity `task: sentence similarity | query: `. Add a query/document paired example and fixture/docs test to keep guide, demo and model card aligned.

### [#3927 — Qwen3.5 tool calls returned as plain text](https://github.com/google-ai-edge/LiteRT-LM/issues/3927)
**Detailed reported repro.** Add explicit Qwen3.5 metadata/data processor or parser for `<tool_call><function=NAME><parameter=KEY>VALUE</parameter></function></tool_call>`; do not route it through generic text parsing or assume Qwen3 syntax is identical. Register proper model type/template/thought channel. If unsupported, return a clear error instead of empty `tool_calls`. Test both 2B/0.8B variants, auto-call on/off, no-call text, multiple calls and malformed/escaped arguments.

### [#3959 — Gemma 4 template uses unsupported Jinja methods in minja](https://github.com/google-ai-edge/LiteRT-LM/issues/3959), [related minja #97](https://github.com/google/minja/issues/97)
**Detailed reported repro.** Prefer implementing Jinja `dict.get(key, default)` semantics and `is mapping` in minja with tests for absent keys/null/defaults, then update dependency and render canonical Gemma 4 template. If impossible, ship a compatibility-tested template; do not trim image/audio branches without explicit bundle metadata/docs. Test history/tool turns and the multimodal paths the bundle claims to support.

### [#3961 — Gemma 4 E4B GPU output corrupted](https://github.com/google-ai-edge/LiteRT-LM/issues/3961)
**Reported deterministic 30-turn `Foo`/`Bar` repro; root cause unknown.** Preserve the program as a regression. Compare CPU/GPU, short/8192 context, cold/reused conversation and repeats; capture first divergent token/logits/cache position. Inspect GPU KV-cache offsets, rotary/position handling, precision conversions, verifier path if enabled and context-length patching as hypotheses. Fix only the isolated layer; do not change model weights or add broad CPU fallback as a substitute for debugging. Reject known-unsafe combinations rather than returning corrupted text as success.

## C. DeepSeek-V3 — existing FP8 proposal

Existing [PR #1706](https://github.com/deepseek-ai/DeepSeek-V3/pull/1706), related [issue #1703](https://github.com/deepseek-ai/DeepSeek-V3/issues/1703), personal branch `fix/atomic-fp8-output-publication`. The proposal stages converted shards/index in a temporary sibling directory, validates references, publishes only after success, preserves an existing destination on conversion/rename failure, cleans staging files, restores PyTorch default dtype and adds failures/replacement regressions.

**Recorded validation:** `py_compile` and `git diff --check` reported passed. Targeted pytest was **not run** because pytest, PyTorch, safetensors and tqdm were unavailable. Do not call it merged or fully tested. Next gates: run pytest in supported CI; verify destination preservation/staging cleanup for every failure, bad index entries, dtype restoration after exceptions and a small inference smoke test. Do not duplicate this implementation in the research branch.

## Rules

A proposal is not an upstream patch. Mark fixed only when the change exists in the correct repository and the targeted regression passes. Note unavailable hardware/toolchains explicitly. Security tests must use dummy credentials only.
