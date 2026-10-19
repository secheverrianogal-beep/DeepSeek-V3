# Validation errata — 14 October 2026

This file explicitly supersedes the stale validation sentence in `2026-10-14-proposed-fixes.md` stating that the targeted pytest suite was not run due to missing dependencies. The newer evidence is the author's 13 October comment on [upstream PR #1706](https://github.com/deepseek-ai/DeepSeek-V3/pull/1706#issuecomment-6148902056), corroborated in the maintainer's reply [here](https://github.com/deepseek-ai/DeepSeek-V3/pull/1706#issuecomment-6150723437).

## Current evidence for DeepSeek-V3 PR #1706

- `python -m pytest -q inference/tests/test_fp8_atomic_output.py`: **9 passed locally**, according to the PR author's published report.
- `python -m py_compile inference/fp8_cast_bf16.py inference/tests/test_fp8_atomic_output.py`: **passed locally**, according to the same report.
- Reported environment: Python 3.13.5, PyTorch 2.10.0+cpu, safetensors 0.7.0, pytest 9.0.2 and tqdm 4.67.3.
- Scope limitation: the test fixture replaces `weight_dequant` with a deterministic CPU implementation. These results validate filesystem publication, index handling and failure cleanup; they do not establish numerical correctness of the production CUDA kernel.
- CI: no matching GitHub Actions run/checks were confirmed for head `04f9384c39faf76ea88dc6e2c483ad91ab0b1c4b`. Both connected repository status queries returned empty status arrays. This is **not evidence that tests failed**; CI simply remains unconfirmed.
- Stronger preservation test: **present in the inspected PR #1706 diff at head `04f9384c39faf76ea88dc6e2c483ad91ab0b1c4b`**. The test's `snapshot_tree()` compares directory structure, symlinks, and SHA-256 hashes for files, including nested/binary content; the failure-path test checks that the original destination remains unchanged and staging is cleaned up. This presence was verified by reading the live PR diff on 2026-10-19. The test has not been independently executed in this environment, and CI remains unconfirmed. Do not conflate a test being committed with that test passing on CI.
- The current change rejects an already existing output directory. This is a safety improvement and a compatibility change; document that callers must select a new destination. Replacement semantics should be a separate, explicit design.

## Validation for the remediation catalog PR #2

This PR contains documentation only; no Gallery or LiteRT-LM source code is changed. The GitHub connector confirms the catalog files exist in `research/issue-remediation-catalog-2026-10-14`. PR #2 is open and unmerged; the connector reports `mergeable: false` at last check, which may indicate GitHub's mergeability calculation was not available yet and must not be described as a merge conflict without inspecting the live PR UI.

## Next concrete steps

1. Keep #1706 open until the stronger preservation test already present in head `04f9384c39faf76ea88dc6e2c483ad91ab0b1c4b` is run against that exact test-file version and CI evidence is reviewed. Do not ask to commit the test again; the live diff already contains it.
2. Check GitHub Actions/status checks for the exact SHA again before claiming CI passed.
3. Continue to treat all Gallery/LiteRT-LM items in the catalog as proposed fixes, not implemented source patches, until a writable authorized fork is connected and source regressions are run there.
