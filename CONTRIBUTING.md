# Contributing to cf-cloner

Thanks for considering a contribution.

## Before opening a pull request

Please open an issue first for:

- New features
- Password manager support
- Changes to the security model
- Cloudflare API behavior changes
- Large refactors

Small documentation fixes can go directly to a pull request.

## Development setup

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/cf-cloner.git
cd cf-cloner
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest
```

Run tests:

```bash
pytest
```

## Code style

- Keep code simple and readable.
- Do not print secrets.
- Do not log secrets.
- Do not write tokens to disk.
- Prefer explicit error messages.
- Keep provider-specific code isolated where possible.

## Security-sensitive contributions

For any change that touches:

- Token handling
- 1Password secret reads
- Cloudflare API writes
- Logging
- Subprocess calls

Explain the security implications in the pull request.

## Pull request checklist

- [ ] The change is documented.
- [ ] Tests pass.
- [ ] No secrets are printed.
- [ ] No secrets are written to disk.
- [ ] README is updated if behavior changed.
