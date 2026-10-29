---
name: Bug Report
about: Report a bug or unexpected behavior in py-junos-eznc
title: "[BUG] "
labels: bug
assignees: ''
---

## Description

A clear and concise description of the bug.

## Steps to Reproduce

> **Security reminder:** Before pasting any code, logs, or output below, replace all
> real hostnames, IP addresses, usernames, and passwords with safe placeholders
> (e.g. `host='<DEVICE-IP>'`, `user='<USERNAME>'`, `passwd='<REDACTED>'`).

```python
# Minimal reproducible example — credentials/hostnames already replaced
from jnpr.junos import Device

dev = Device(host='<DEVICE-IP>', user='<USERNAME>')
dev.open()
# ...
```

1. Step 1
2. Step 2
3. Step 3

## Expected Behavior

What you expected to happen.

## Actual Behavior

What actually happened. Include the full traceback if applicable.

> **Security reminder:** Ensure the traceback/log output below does not contain real
> hostnames, IP addresses, usernames, or passwords. Replace them with `<REDACTED>` before posting.

```
Traceback (most recent call last):
  ...
```

## Environment

| Item | Version |
|------|---------|
| py-junos-eznc version | <!-- e.g. 2.7.0 --> |
| Python version | <!-- e.g. 3.10.4 --> |
| OS | <!-- e.g. Ubuntu 22.04 --> |
| Junos version | <!-- e.g. 22.1R1 --> |
| Junos platform | <!-- e.g. MX480, vMX, QFX5100 --> |
| Transport | <!-- NETCONF/SSH, Console, Outbound SSH --> |

## Junos RPC / XML (if applicable)

If this is related to a specific RPC call or XML, include the relevant details:

```xml
<!-- RPC request/response if applicable -->
```

## Credential Scrubbing Checklist

Before submitting, confirm you have removed sensitive data from this report:

- [ ] No real hostnames or IP addresses
- [ ] No real usernames
- [ ] No real passwords or SSH key material
- [ ] No real device serial numbers or other PII

## Additional Context

Add any other context, logs, or screenshots about the problem here.
