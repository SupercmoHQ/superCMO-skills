---
description: Set up your SuperCMO bring-your-own API keys and verify what's working.
---

Help me get SuperCMO working on my own keys. Use the **supercmo-setup** skill:

1. Run `python3 scripts/doctor.py` and show me which keys are set vs missing and what each enables.
2. Recommend one key to start (default `FAL_KEY` — it covers image + video + tts), tell me where to
   put it for the host I'm on, and wait while I add it.
3. Re-run `python3 scripts/doctor.py --check` to confirm it's valid, then suggest a quick test generation.

Keep it to one key to start — don't ask me to configure all of them.
