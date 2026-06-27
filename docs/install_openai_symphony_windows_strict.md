## OpenAI Symphony on Windows: Strict Local-First Install Note

### Date
2026-06-26

### Installed Location
`C:\Dev\symphony\elixir`

### Verified State
The existing checkout is present and functional on this machine.

Verified successfully:
- `mise exec -- mix build`
- `mise exec -- escript bin/symphony --help`
- `mise exec -- escript bin/symphony .\WORKFLOW.md`
  - This reaches the expected guardrails acknowledgment screen

### Runtime Contract
This install is user-space and local-first.

- Runtime manager: `mise`
- Elixir/Erlang execution: `mise exec`
- No global install required

### Preflight
Before using Symphony, verify:

```powershell
mise --version
mise doctor
```

On this machine, the stable Windows PATH contract is:

```text
C:\Dev\_bin\mise
C:\Users\jerem\AppData\Local\mise\shims
```

### Working Install / Build Flow
From `C:\Dev\symphony\elixir`:

```powershell
mise trust
mise install
mise exec -- mix setup
mise exec -- mix build
```

### Working Verification Flow
```powershell
mise exec -- elixir --version
mise exec -- mix --version
mise exec -- escript bin/symphony --help
mise exec -- escript bin/symphony .\WORKFLOW.md
```

### Important Policy Correction
Do not describe `mise install` here as "installs Elixir/Erlang locally or globally."

For this environment and policy, the correct interpretation is:
- use `mise` as the project/runtime manager
- keep installs in user-space
- invoke project tooling through `mise exec`

### Known Windows Note
`mise doctor` reports file shim fallback because `mise-shim.exe` is not present. That is acceptable if command discovery and `mise exec` workflows are stable.

### If `mise` Appears Missing
Treat that as a shell discoverability problem first, not a missing-install problem.

Check:
1. Is `C:\Dev\_bin\mise\mise.exe` present?
2. Is `%LOCALAPPDATA%\mise\shims` present?
3. Are both on the user PATH?

Repair PATH before considering reinstall.
