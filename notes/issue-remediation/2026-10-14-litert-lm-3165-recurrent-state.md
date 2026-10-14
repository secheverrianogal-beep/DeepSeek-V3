# LiteRT-LM #3165 — cross-conversation recurrent-state contamination

**Review date:** 14 October 2026  
**Source issue:** https://github.com/google-ai-edge/LiteRT-LM/issues/3165  
**Existing candidate fix:** https://github.com/google-ai-edge/LiteRT-LM/pull/3945  
**Related but distinct rewind bug:** https://github.com/google-ai-edge/LiteRT-LM/issues/3947

## Finding and status

Issue #3165 describes recurrent/hybrid models (including Mamba2 and gated-delta/Qwen3.5-style models) returning corrupted answers when multiple conversations reuse one Engine. The failure is materially different from ordinary KV-cache prefix reuse: linear-attention/recurrent buffers represent accumulated state, so resetting only the step counter does not erase the prior conversation's state.

A maintainer has confirmed reproduction on shared-engine recurrent/hybrid models in the issue thread. PR #3945, opened by john-rocky, is an existing **draft** candidate fix. Its head at this review was 65d070f2e70d692ef6d95553333a789c32034832. The PR author's description reports successful macOS arm64 runs of state_test, llm_litert_compiled_model_executor_test, resource_manager_test, and llm_executor_processed_tokens_test, and real-bundle tests with Qwen3.5-2B and Qwen3.5-0.8B changing from 0/9 to 9/9 expected "Beta" starts across a new conversation. These are author-reported results, **not independently rerun here**. The connected GitHub status-check query returned no checks for this head, so upstream CI is not confirmed.

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
