# Codex durable-host 403 and CLOSE_WAIT — triage note (19 October 2026)

Source: [openai/codex #54696](https://github.com/openai/codex/issues/54696), with related reports #53667, #38981, #31376 and #38925.

## Confirmed report evidence (reporter-supplied, not independently reproduced)

The original report records a Windows Desktop app-server accumulating TCP sockets to `chatgpt.com` in `CLOSE_WAIT` during multi-hour sessions. The follow-up on build 26.1013.4894.0 / bundled CLI 0.163.0-alpha.10.2 reports a second, potentially related signal:

- A `durable` app-server host retry occurs every ~20 seconds and receives HTTP/WebSocket response `403`.
- The reporter counted 457 attempts over ~2.5 hours and thousands of corresponding log lines.
- In that session the process also accumulated hundreds of threads, thousands of handles and high RSS; the UI became laggy. Restart temporarily reduced the observed socket count.
- With the same credentials, the reporter says the backend discovery endpoint returned `200` and a WebSocket URL, while the hard-coded `codex-cloud-backend.chatgpt.com` endpoint returned `101` in a separate test and `403` in the failing connection context.

These observations raise a useful hypothesis: the durable-host URL selection/refresh path and the socket lifecycle may be two distinct defects, or a retry path may amplify a transport leak. They do **not** prove the server URL is being ignored, nor that every failed durable retry causes one leaked socket. The issue needs sanitized per-attempt correlation to establish that.

## Investigation should separate two questions

### A. Why does the durable connection receive 403?

Trace the durable-host connection setup from the discovery response through URL selection, host identity, authentication/authorization headers, websocket handshake and reconnect logic. Log only safe metadata: selected host category, whether the URL came from discovery/default, HTTP status, attempt number, and a correlation ID. Do not log tokens, full verification URLs, cookies or credential-bearing query parameters.

Compare:
1. the URL returned by the discovery endpoint;
2. the URL actually passed to the WebSocket client;
3. whether the same authentication/session context is used for both;
4. behavior after discovery refresh and after app-server restart.

A `403` is an observed status, not proof of a credential failure or of a hard-coded fallback. Keep both explanations open until the selected URL and handshake context are captured.

### B. Why do sockets remain in CLOSE_WAIT?

Audit response-body and WebSocket stream ownership independently from the 403 path. On EOF, non-success handshake, cancellation, timeout, retry replacement and shutdown, ensure the relevant stream/socket is closed and removed from the pool according to the transport library's contract.

Use a controlled local server/proxy that can return a 403, close a connection after a successful response, interrupt a stream and accept a reconnect. For each case, count sockets and open handles before and after repeated attempts. Verify that failed retries do not grow `CLOSE_WAIT` monotonically and that normal connection reuse still works.

## Regression criteria

- Repeated durable-host 403 responses do not cause unbounded socket, thread or handle growth.
- A discovered URL is either used or rejected with an explicit, safe diagnostic; default fallback behavior is covered by a test.
- Discovery refresh, 101 handshake, 403 handshake, peer EOF, cancellation and process shutdown each release owned resources.
- Long-running Windows soak test shows bounded `CLOSE_WAIT` counts and stable memory/handle growth.
- Existing healthy streaming and legitimate connection reuse remain intact.

## Duplicate/related issue discipline

#54696 references #53667, #38981, #31376 and #38925. Compare code paths and consolidate around a common transport/resource-lifecycle fix only if evidence supports it. Keep the latest Windows build and the `durable`-host 403 as new reproduction context even if an older issue becomes the canonical tracker.

## Status

This is a testable investigation plan based on the issue and its follow-up. No independent reproduction, source-level root cause, code fix or CI pass is claimed here. Restarting the app is a temporary workaround, not a fix.
