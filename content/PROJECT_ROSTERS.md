# Complete project rosters

`project-rosters.json` is the final explicit membership registry. Include every confirmed participant as a member, with their role; never replace a member card with an "also participates" footnote. The historical `team-directory.json` and earlier build stages remain preserved snapshots; their partial rosters and note fields are superseded by this final registry.

`python scripts/complete_project_rosters.py` runs after the historical site checks and before all assistant corpus builders. It uses existing person cards and profiles without inventing ranks, institutions or responsibilities. The same member list produces the directory, proposal-detail cards and profile study links. Shared members can belong to multiple teams, but no person can occur twice within one team. Each project retains its existing status and review date. The principal investigator remains in the existing leadership and proposal-lead fields rather than being repeated in a footnote.

The AÜB roster includes Ahmet Sami Konca, Kibar Gül, Naciye Somuncu Demir and Yeşim Taktat Ateş. The separate 3501 roster retains seven members. Konca's unrelated published-research collaboration stays in the collaborators section and is not converted into a 3501 role.

`python tests/project_rosters_browser.py` runs on the final output, after the assistant builders. It checks complete rosters in both languages, unique membership, correct links and affiliations, note removal, preservation of application statuses, mobile/desktop layout, search and assistant-fact parity. The optional `--offline --before-assistant` flags are only for local preview checks; production runs use neither flag. Do not update academic, CV or proposal-review dates for a roster presentation change.
