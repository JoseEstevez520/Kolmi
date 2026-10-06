# Data and privacy

Kolmi is self-hosted: each class runs its own instance, with its own Supabase project and its own
server. Whoever deploys it decides what happens to the data and is the one who answers for it. This
page says what the app does with data so that person can tell their class. It is not legal advice.

## What the app keeps

All of it lives in the instance's Supabase project, in the region its owner picked.

- **Accounts:** the name and the email someone signs up with, their role (student or admin) and
  their status (active, pending while an admin lets them in, or blocked).
- **Notes:** what each student writes and the files they attach. Files go to a private Storage
  bucket and are served through short-lived links.
- **The shared pages:** the pages the AI writes from the notes, their earlier versions, and the
  log of what the AI did with each note.

## Who sees what

- A student sees their own notes. Until the pass has taken a note, only its author and the admins
  can see it.
- Admins see every note and the AI log, and the class's people: each one's name, email, role,
  status, when they joined and how many notes they left. An admin never sees anyone's chat with the
  hive: only its author does.
- Everyone in the class sees the shared pages.

## What leaves the instance

When the pass runs, the text of the pending notes and of the pages it updates is sent to the AI
provider the instance is configured with (`LLM_*` in `backend/.env`, any OpenAI-compatible
endpoint), and to a second one if `WEB_*` is set. The pass strips names and personal data from
what it writes, but it does not check what students put in their notes.

Where those providers process the data, and under what terms, depends on the provider chosen. If
the class is in the EU, check it before choosing, and sign the provider's data processing terms if it
has them.

## What a student can take

Anyone in the class can download a section's shared pages as Markdown files, from the
section's page. Those are the pages the pass wrote, without names; raw notes and attachments are not in
the export. What a student does with the files after that is theirs to decide: uploading them to
a service like NotebookLM sends them to that service, under its own terms.

## If you host an instance

- Tell your class what is above before they sign up: what is stored, who sees it and that notes go
  to an AI provider.
- Ask them not to write personal data or secrets in notes.
- Pick the AI provider with care, since it is the one place student text leaves your control.
- Keep the Supabase and provider keys in `.env`, never in git.
- Be ready to answer a request to see, correct or delete someone's data. Anyone changes their name
  and deletes their own account in Settings; an admin deletes someone's from the admin panel. A
  deleted account takes its notes, their files and its chat with it; what the pass already wrote
  into the shared pages stays, and so do the files on those pages, with no author.

## A notice to adapt

A starting point for a sign-up screen or a message to the class. Change it to match your instance.

> Kolmi is the class notebook. It keeps your name, your email, your notes and the files you attach.
> You and the admins see your notes until the AI turns them into shared pages, and the whole class
> sees those pages. When the AI runs, the text of the notes is sent to **[your AI provider]**. Don't
> write personal data or passwords in your notes. To see, correct or delete your data, write to
> **[contact]**.
