# Academic conversation assistant — v3

The final stage `scripts/build_assistant_v3.py` replaces the small on-device model interface with a server-ready conversation controller. The previous Qwen/WebLLM worker is not loaded by the final page. The existing structured website guide remains available, explicitly labelled non-generative.

`assistant-service/api/chat.mjs` implements a source-grounded server conversation using the OpenAI Responses API. The model is configurable on the server (default `gpt-5.4`). It uses limited conversation history, a trusted published-site corpus, structured output, source-ID validation, consent and persistent request quotas. Secrets are never included in the public website. Source retrieval detects changed named subjects and keeps context for pronoun follow-ups.

`content/assistant-service.json` contains only the public service endpoint. Its empty default keeps cloud conversation inactive. No provider account, service deployment, billing arrangement or actual model-quality validation is implied by publishing this code.

Build order: existing editorial/site gates; original assistant and source-rule tests; final v3 build; server unit tests and final browser tests; internal-link/checksum checks; Pages publish; live-file verification. The final browser tests use mocked server transport and are not a model-quality score. `assistant-service/evaluate.mjs` provides opt-in real-provider conversation cases and a manual review rubric; it skips unless explicitly enabled.

See `assistant-service/README.md` for authorised deployment, environment variables, quota semantics, data policies and evaluation. Preserve all evidence-backed academic dates and project statuses. No new duties or affiliations are inferred. Only already-public content enters the knowledge bundle; the existing discovery exclusion remains in place.
