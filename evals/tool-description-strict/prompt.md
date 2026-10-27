---
tags: [strict]
max_turns: 6
allowed_tools: [Read, Skill, Bash]
---

Apply STE100 to this tool description:

This function is used to fetch the latest metrics from the monitoring backend, and if the request times out after 30 seconds, it will be retried up to 3 times before an error is returned to the caller, unless retries have been disabled in the config.
