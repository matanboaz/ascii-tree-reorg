# Contributor guide

- Keep parser, safety, and conflict rules in Python, not TypeScript.
- Preserve safe defaults and validate every destination before mutation.
- Add regression tests for parser, safety, packaging, protocol, and UI-boundary changes.
- Keep sidecar stdout as newline-delimited JSON; diagnostics belong on stderr.
- Keep Node and filesystem access out of the renderer; use the preload API.
- Render and inspect affected representative states for visual changes.
