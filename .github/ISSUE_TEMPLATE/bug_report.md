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

```python
# Minimal reproducible example
from jnpr.junos import Device

dev = Device(host='router.example.com', user='admin')
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

## Additional Context

Add any other context, logs, or screenshots about the problem here.
