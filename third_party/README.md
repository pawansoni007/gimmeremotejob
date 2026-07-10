# third_party

Vendored third-party code we call directly.

## OpenHarness

`OpenHarness/` is a **plain in-repo copy** of [`HKUDS/OpenHarness`](https://github.com/HKUDS/OpenHarness)
(MIT) — a Python port of Claude Code. It's the agent "brain": we call its
`QueryEngine` in-process from `service/`.

**Not a submodule, not from PyPI** — a one-time copy, so hosting/deploying the
service elsewhere doesn't drag in submodule machinery. The service installs it
editable via a `uv` path source (see `service/pyproject.toml`).

- Upstream: https://github.com/HKUDS/OpenHarness
- Pinned commit: `9b2efd795c6aa09f88b0c257d269a9e518da6ae7` (branch `main`)

### Updating it later (manual, on purpose)

```bash
rm -rf third_party/OpenHarness
git clone --depth 1 https://github.com/HKUDS/OpenHarness.git third_party/OpenHarness
rm -rf third_party/OpenHarness/.git
# then re-run `uv sync` in service/ and re-test
```
