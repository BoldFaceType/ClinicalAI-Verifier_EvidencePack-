## DevOps Guide Exception: `mise` Installed But Not Callable

### Date
2026-06-26

### Scope
Windows user-space runtime management for repos that rely on [`mise.toml`](/C:/Dev/projects/Clinica%20AI%20Engineering/mise.toml).

### Exception
The DevOps Guide assumes `mise` is already callable from the active shell before any project-scoped runtime work begins. On this machine, that assumption was false even though `mise` was already installed and functional.

### Evidence
- A working standalone binary existed at `C:\Dev\_bin\mise\mise.exe`.
- Runtime installs and shims existed under `%LOCALAPPDATA%\mise`.
- PowerShell profile wiring was incomplete for Codex-hosted shells and similar sessions that do not reliably inherit the intended profile state.
- Symphony at `C:\Dev\symphony\elixir` built and launched successfully once the shell PATH explicitly included:
  - `C:\Dev\_bin\mise`
  - `C:\Users\jerem\AppData\Local\mise\shims`

### Root Cause Class
Shell discovery failure, not missing runtime manager.

This is the same class of problem as other Windows shell/path-resolution defects: the tool exists, but ambient shell assumptions make it appear absent.

### Required Gate
Before any `mise install`, run:

```powershell
mise --version
mise doctor
```

If either command fails, stop and repair discoverability before changing toolchains.

### Approved Remediation
1. Verify whether a user-space `mise` binary already exists.
2. Verify whether the shims directory already exists.
3. Repair user PATH first.
4. Prefer explicit user PATH entries over profile-only assumptions.
5. Reinstall only if the binary is absent or corrupt.

### Approved PATH Layout
For this machine, the stable Windows layout is:

```text
C:\Dev\_bin\mise
C:\Users\jerem\AppData\Local\mise\shims
```

Order matters. Put the standalone `mise` binary first so `mise` remains callable even if shim behavior changes.

### Shim Policy
`mise doctor` warns that `mise-shim.exe` is not present and `mise` is falling back to file shim mode.

That warning is not, by itself, a defect requiring repair.

If shim removal was intentional to avoid WSL or shell conflicts, file shim mode is acceptable as long as:
- `mise --version` works
- `mise doctor` can inspect the active toolset
- project commands succeed via `mise exec`

### Do Not
- Do not perform a global reinstall.
- Do not restore removed shim binaries blindly.
- Do not assume PowerShell profile loading is sufficient in Codex-hosted shells.
- Do not bypass `mise` with unrelated runtime managers when `mise.toml` is the repo contract.

### Vetting Decision
- KISS: repair discoverability before reinstalling.
- Rule of One: `mise` owns runtime selection, `uv` owns Python dependencies.
- VCR: PATH repair is lower cost and lower risk than reinstalling.
- No global installs: all remediation remains user-scope.
