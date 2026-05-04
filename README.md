# cf-cloner

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Package](https://img.shields.io/badge/package-PyPI-ready-green)

`cf-cloner` is a secure CLI tool for duplicating Cloudflare API tokens by mirroring the source token's policy/scopes and saving the new token into 1Password.

It is designed for agencies, SaaS admins, and platform teams that need to recreate complex Cloudflare tokens without manually selecting dozens of permissions.

## What it does

`cf-cloner`:

1. Lets you fuzzy-search 1Password API Credential items.
2. Reads the selected Cloudflare token using the 1Password CLI.
3. Verifies the token with Cloudflare.
4. Fetches the source token's exact policy array.
5. Creates a new Cloudflare token with the same policies.
6. Sets a default 1-year expiration.
7. Saves the newly created token back into a target 1Password vault.

## Security model

`cf-cloner` is designed to avoid accidental secret exposure.

- Token values are never printed.
- Token values are never intentionally written to disk.
- The source token is read from 1Password with `op read`.
- The new token is saved directly into 1Password.
- The tool avoids shell history exposure.
- Errors do not include token values.

Important: a token must exist in process memory briefly so it can be sent to the Cloudflare API. This is unavoidable for this workflow.

## Requirements

Install these tools first:

```bash
brew install 1password-cli fzf
```

You also need:

- Python 3.9+
- An authenticated 1Password CLI session
- A Cloudflare API token with permission to read and create API tokens

Check 1Password auth:

```bash
op account get
```

If needed, sign in:

```bash
op signin
```

## Installation from source

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/cf-cloner.git
cd cf-cloner
pip install .
```

For development:

```bash
pip install -e .
```

## Installation from PyPI

After this package is published:

```bash
pip install cf-cloner
```

## Usage

Run:

```bash
cf-clone
```

You will be prompted to:

1. Select the source Cloudflare token from 1Password.
2. Enter the new Cloudflare token name.
3. Enter the target 1Password vault.

Example:

```bash
cf-clone
```

Set a custom expiration period:

```bash
cf-clone --expiry-days 90
```

## Expiry customization

The default expiry is 365 days.

Recommended runtime option:

```bash
cf-clone --expiry-days 180
```

To change the package default, edit:

```python
DEFAULT_EXPIRY_DAYS = 365
```

in:

```
src/cf_cloner/cloner.py
```

## Required Cloudflare permissions

The selected source token must be able to:

- Verify itself
- Read token details
- Create API tokens

In Cloudflare terms, the source token should include:

```
API Tokens:Edit
```

If the source token can manage API tokens and contains the policies you want to clone, cf-cloner will mirror its policy array.

## 1Password setup

Store Cloudflare tokens as 1Password items with category:

```
API Credential
```

The token should be in a field labeled one of:

```
credential
token
api token
api_token
password
```

The tool also supports fields marked with password purpose.

## Attestation and linking

No special Cloudflare or 1Password attestation is required.

No manual linking is required between Cloudflare and 1Password.

The workflow relies on:

1. Your local authenticated `op` CLI session.
2. A valid Cloudflare token with token-management permissions.
3. HTTPS requests to the Cloudflare API.

## Password manager support

Native support currently targets:

```
1Password CLI: op
```

Other password managers such as Bitwarden, KeePass, Doppler, Vault, or AWS Secrets Manager are not implemented yet.

If you need another provider, open a Feature Request and include:

- Password manager name
- CLI command examples
- How to read a secret safely
- How to create or update a stored secret
- Any masking behavior or audit-log concerns

## Publishing to PyPI

Install build tools:

```bash
python -m pip install --upgrade build twine
```

Build:

```bash
python -m build
```

Upload manually:

```bash
python -m twine upload dist/*
```

## GitHub release publishing

This repo includes a GitHub Actions workflow for publishing to PyPI on release.

To enable it:

1. Create a PyPI account.
2. Create a PyPI API token.
3. In GitHub, go to Repository Settings → Secrets and variables → Actions.
4. Add:

```
PYPI_API_TOKEN
```

5. Create a GitHub Release.

The `publish.yml` workflow will build and upload the package.

## Troubleshooting

### `op` not found

Install 1Password CLI:

```bash
brew install 1password-cli
```

### `fzf` not found

Install fzf:

```bash
brew install fzf
```

### 1Password is not signed in

Run:

```bash
op signin
```

### Cloudflare 403 or permission error

Ensure the selected source token has:

```
API Tokens:Edit
```

### No credential field found

Make sure the 1Password item has a token stored in a field labeled:

```
credential
```

or:

```
token
```

## Issues

Use GitHub Issues for:

- Bugs
- Cloudflare API errors
- 1Password CLI compatibility problems
- Missing docs
- Packaging problems

## Discussions

Use GitHub Discussions for:

- Workflow ideas
- Password manager support
- Security model questions
- Agency/team onboarding use cases

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md).

## Sponsorship

If this saves your team time, consider sponsoring the project through GitHub Sponsors.

Replace this section with your sponsor URL when ready.

## License

MIT. See [LICENSE](LICENSE).
