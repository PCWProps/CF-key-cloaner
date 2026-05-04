# Security Policy

## Reporting a vulnerability

Please do not open a public issue for security vulnerabilities.

Instead, report privately through GitHub Security Advisories if enabled, or contact the maintainer directly.

## Supported versions

| Version | Supported |
|---|---|
| 1.x | Yes |

## Secret handling guarantees

`cf-cloner` is designed to:

- Never print token values.
- Never intentionally write token values to disk.
- Save newly created tokens directly to 1Password.
- Avoid shell history exposure.

## Limitations

A token must exist briefly in process memory to make authenticated Cloudflare API requests.

Users are responsible for:

- Keeping 1Password secure.
- Keeping Cloudflare tokens scoped appropriately.
- Rotating tokens regularly.
- Reviewing generated token permissions.
