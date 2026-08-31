## Problem

<!-- What observable behavior or risk does this change address? -->

## Decision

<!-- What changed, and why is this the smallest durable design? -->

## Verification

- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `bash -n scripts/launch-aquarium scripts/idle-integration`
- [ ] `omarchy plugin validate .`
- [ ] Actual control-room or screensaver surface exercised when UI changed
- [ ] Screenshot or recording attached when appearance changed

## Safety

- [ ] No privileged installation or packaged Omarchy files modified
- [ ] Idle and lock timing remains intact
- [ ] Multi-monitor audio still has a single leader
- [ ] Documentation reflects configuration or behavior changes
