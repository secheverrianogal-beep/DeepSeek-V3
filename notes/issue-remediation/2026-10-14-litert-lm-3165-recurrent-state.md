# LiteRT-LM #3165 — cross-conversation recurrent-state contamination

**Review date:** 14 October 2026  
**Source issue:** https://github.com/google-ai-edge/LiteRT-LM/issues/3165  
**Existing candidate fix:** https://github.com/google-ai-edge/LiteRT-LM/pull/3945  
**Related but distinct rewind bug:** https://github.com/google-ai-edge/LiteRT-LM/issues/3947

## Finding and status

Issue #3165 describes recurrent/hybrid models (including Mamba2 and gated-delta/Qwen3.5-style models) returning corrupted answers when multiple conversations reuse one Engine. The failure is materially different from ordinary KV-cache prefix reuse: linear-attention/recurrent buffers represent accumulated state, so resetting only the step counter does not erase the prior conversation's state.

A maintainer has confirmed reproduction on shared-engine recurrent/hybrid models in the issue thread. PR #3945, opened by john-rocky, is currently **open, not draft, and unmerged**. On 2026-10-19 its live head is `b3934770f16b2f8d454fef41190abfe4404fcb70` (the historical head above is stale). The PR description reports successful macOS arm64 runs of state_test, llm_litert_compiled_model_executor_test, resource_manager_test, and llm_executor_processed_tokens_test, plus real-bundle Qwen3.5-2B and Qwen3.5-0.8B results changing from 0/9 to 9/9 expected "Beta" starts across a new conversation; those are author-reported local results, not independently rerun here. **Live GitHub Actions runs for the current head were checked on 2026-10-19: ML-CI-Linux-CMake, ML-CI-Win, ML-CI-Android-CMake, ML-CI-Build-Android, Google GitHub Admin: Actions Workflow Security Scan, CI-Mac, and ML-CI-Linux all completed successfully.** The status-check endpoint itself returned an empty list, so report the seven successful workflow runs specifically rather than saying CI is unconfirmed. PR remains open and unmerged. A later live metadata read on 2026-10-19 reported `mergeable=true`; this field can be transient, and no review or merge decision is implied.

## Candidate solution already present in upstream PR #3945

The proposed patch clears only state buffers identified as linear-attention state when a prefill starts at step 0, for both static and dynamic executors. The intent is:

- Clear accumulated recurrent state at a new sequence boundary (Reset or a new conversation restored at step 0).
- Keep KV-cache buffers unchanged because positions after the current step are masked.
- Leave models without declared linear-attention state unchanged.
- Leave prefills starting after step 0 unchanged.
- Exercise state clearing in in-place and ping-pong buffer configurations, including multiple decode heads.

The proposed approach is appropriately narrower than indiscriminately zeroing every cache buffer. Do not create a duplicate patch while this upstream candidate is active.

## Remaining review gates

1. Inspect the current PR diff against its current base and ensure the state-buffer predicate matches the executor metadata contract for all supported recurrent/hybrid bundle types.
2. Verify static and dynamic executor coverage and confirm that the step == 0 condition cannot clear state during an in-sequence prefill.
3. Review tests for both in-place and ping-pong allocations, models with no linear-attention state, multiple decode heads, Reset, and new-context restoration.
4. Obtain current CI results and rerun the exact test targets on a supported build environment; do not infer CI success from the PR description.
5. Keep the boundary explicit: the PR says rewind to a non-zero step is not addressed. Rewinding recurrent state requires a state snapshot/restore design, not just clearing buffers. The NPU executor is also a separate path and needs an explicit scope decision.
6. Validate candidate behavior against a published recurrent/hybrid model and a conventional attention-only control, using the same prompts and greedy decoding; compare shared-Engine/new-Conversation behavior against a fresh-Engine reference.

## Contribution boundary

This document is an independent review note in the personal DeepSeek-V3 fork, not a source-code fix to LiteRT-LM. The connected GitHub account has no write access to the LiteRT-LM upstream repository, and no writable LiteRT-LM fork is available. Use the existing upstream PR/issues for technical review; do not claim the bug is fixed until the candidate is accepted and validation evidence is available.


## Confirmed coverage gap in the prefix-reuse path

**Classification:** high-priority review finding confirmed by source-path inspection; the full end-to-end reproducer has not been run independently in this environment.

The reported failure path in issue #3165 involves token-prefix deduplication across conversations. In current `ResourceManager::Prefill()` (`runtime/framework/resource_management/resource_manager.cc`), the manager invokes `RemoveMatchingTokens(..., &current_step)` before the compiled-model executor receives the prefill:

- If a shared prefix matches but a suffix remains, `current_step` is advanced by the match length. In the branch that calls `SetCurrentStep(current_step)` before the executor prefill, the step is now non-zero; PR #3945's `ClearLinearAttentionStateIfFirstStep()` returns without clearing at that step.
- If all incoming tokens match, `ResourceManager::Prefill()` calls `SetCurrentStep(current_step)` and returns without calling the executor's `Prefill()` at all, so the PR's clearing hook is not reached by that call.
- The PR changes six state/executor files and its new tests do not modify or exercise the ResourceManager prefix-dedup path. Its direct non-zero-step test intentionally preserves state, which is valid for continuing a sequence but does not verify a new logical conversation reusing a prefix.

This path-level mismatch is supported by reproducible upstream reports with one shared Engine, growing prefixes, and fresh-Engine controls: [published-bundle repro](https://github.com/google-ai-edge/LiteRT-LM/issues/3165#issuecomment-5251336384), [v0.16.0 persistence report](https://github.com/google-ai-edge/LiteRT-LM/issues/3165#issuecomment-5260028474), and [v0.16.1 Qwen3.5 shared-Engine report](https://github.com/google-ai-edge/LiteRT-LM/issues/3165#issuecomment-5538743805). These reports are the original reporter's evidence; they were not rerun by this review.

**Required regression:** reproduce the growing-prefix case through the public Engine/Conversation → ResourceManager path. Use one shared Engine and a fresh-Engine baseline with the same model, prompt, greedy decoding, and conversation order. Capture the matched-prefix length, whether the input became empty, the effective runtime step, and whether executor `Prefill()` was called. Also include a same-conversation continuation control where preserving recurrent state is correct.

**Correction direction:** make prefix dedup aware of recurrent/running-state buffers for a new logical sequence (e.g. do not skip the prefix unless the recurrent state snapshot for that exact prefix is available), or restore the exact state snapshot corresponding to the reused prefix. Do not blindly clear recurrent state at a non-zero step while omitting prefix tokens, because then the recurrent state for those omitted prefix tokens is missing. This remains distinct from arbitrary rewind-to-nonzero-step support and the separate NPU executor path.
## Notification / publication status — 14 October 2026

A targeted top-level comment to upstream PR #3945 was attempted through the connected GitHub integration and rejected with HTTP 403 `Resource not accessible by integration`. Therefore no review comment was published upstream. The finding is recorded in the personal-fork PR discussion and Linear task SER-29 instead; it remains a review concern until an upstream-authorized reviewer can evaluate it.
