---
name: linear-ticket-manager
description: "Create, edit, or draft Linear tickets in short, clear B1 English. Use for ticket requests, rough task notes, and ticket text improvements. Do not use for general writing or to perform the work described in a ticket."
---

# Linear Ticket Manager

Turn the user's request into a short ticket that the assigned person can understand and act on.
Use CEFR B1 English: common words, short sentences, and direct statements.
Use the writing rules below without requiring another skill.

## Writing rules

- Start the title with an action, such as Fix, Add, Move, or Remove.
- Aim for a title of 5–12 words. Keep necessary names and scope even if the title is longer.
- Use 1–3 short sentences for a simple description. Use up to 3 bullets when separate steps are clearer.
- Keep each sentence near 15 words and usually below 20 words.
- Use active voice and one main idea per sentence.
- Keep technical names, branch names, IDs, links, and error text exact. Use backticks for code and branch names.
- Explain a technical term only if the reader needs the explanation.
- Avoid idioms, formal filler, vague words, and repeated details.
- Preserve facts, conditions, uncertainty, and the user's scope. Do not invent a cause, deadline, priority, or solution.
- Add completion checks only when the user provides them or the requested result makes them clear.
- Use extra detail when needed to preserve meaning. Do not force every ticket into a large template.

These rules use plain-language ideas from STE. B1 English is the target, not a claim of certified STE compliance.

## Ticket workflow

1. Identify whether the user wants a draft, a new ticket, or an update.
   A request to create or update a ticket permits that action. A request for a draft permits text output only.
2. Use the connected Linear tools for requested ticket changes.
   Read the current ticket before an update. Keep unrelated fields unchanged.
3. Resolve the team and any named assignee from Linear records or confirmed context.
   Do not guess a person's account from an email initial. Ask one short question if the match remains unclear.
4. Write the title and description using the rules above.
   Ask only for missing details that prevent a correct ticket. Leave optional fields unset unless the user or confirmed context provides them.
5. Create or update the ticket once the needed details are clear. Do not ask for the same permission again.
6. Check the tool result for the ticket ID, URL, and requested fields.
   If the save result is unclear, search for the ticket before retrying. Do not create a second ticket blindly.
7. Reply with the ticket link and title. Mention the assignee when requested.
   If Linear is unavailable, return the ready-to-use draft and state that it was not saved.

Creating a ticket does not permit code changes, branch deletion, or other work described in that ticket.
Do not change status, priority, project, labels, or dates unless the request or confirmed context supports those changes.

## Examples

Request: “Create a ticket to move Argo CD to main and remove the old Azure branches.”

**Title:** Move Argo CD to main and remove old Azure branches

**Description:** Move the Argo CD configuration to `main`. Remove the old Azure branches after preserving required changes.

Request: “Draft a bug ticket: the save button sometimes fails after editing the address.”

**Title:** Fix address changes that sometimes fail to save

**Description:** Saving sometimes fails after a user edits the address. Make sure the Save button stores the address changes.

For a draft, return only the title and description. Keep writing notes and rule checks out of the ticket.
