# Contributor guide

- Keep parser, safety, and conflict rules in Python, not TypeScript.
- Preserve safe defaults and validate every destination before mutation.
- Add regression tests for parser, safety, packaging, protocol, and UI-boundary changes.
- Keep sidecar stdout as version 1 newline-delimited JSON; diagnostics belong on stderr.
- Keep Node and filesystem access out of the renderer; use the narrow preload API.
- Validate IPC sender identity and payload shape in Electron main.
- Do not add runtime web dependencies or weaken CSP/navigation/permission controls.
- Render and inspect representative UI states after visual changes.
- Build release artifacts on their native OS/architecture and never overclaim unsigned artifacts.
- Update README, functional scope, protocol docs, and troubleshooting when behavior changes.
