# Academic conversation assistant

## Architecture and honest mode labels

`scripts/build_assistant.py` creates EN/TR `assistant.html`, public-HTML source records and the opt-in WebLLM interface after the existing site gates. Its original UI/runtime tests run first. `scripts/build_assistant_quality.py` then builds structured facts from the final public HTML, adds `academic-answer-engine.js`, patches the deployed chat controller and runs the final factual-answer tests. Final link/checksum/live verification runs only after both stages.

The default response layer is deterministic, not an LLM. It answers supported questions about team members, affiliations, project stages, documented contributions, publications, research areas and public contact information using public website fields and predefined bilingual response rules. It recognises names without Turkish diacritics, asks for clarification on ambiguous names and retains limited topic context for follow-up questions. Unknown contributions are not inferred from institutions or job titles. Every substantive factual answer provides actual source-page links.

For unhandled questions the retrieval fallback ranks relevant sentences rather than quoting the start of a page. The opt-in small model remains Qwen3-0.6B-q4f16_1-MLC with WebLLM 0.2.88. It is explicitly labelled experimental; this change does not claim to improve or validate its general reasoning, Turkish fluency or generated-answer accuracy. Known factual routes take precedence even when generation is enabled. Never describe rule-composed answers or retrieved excerpts as model-generated output.

## Generation and privacy

Generation is performed on a compatible WebGPU device only after explicit consent. The initial program/model download is approximately 400 MB. There is no provider API key, remote prompt endpoint, automatic model download or chat database. Normal third-party download requests go to jsDelivr, Hugging Face and MLC-hosted model libraries; the conversation is not sent to them. Model files may remain in browser cache. Questions and short context stay in page memory. Clear resets the factual context and model history. User/model output is rendered as text, never injected as HTML.

The assistant is not Hüseyin Ateş and cannot deliver messages, confirm appointments, grant admissions, promise funding or express his personal approval. It uses public pages only. Preserve the exclusion of person-tugce-unsal.html from discovery. Keep review dates and submitted/funded/completed distinctions unchanged unless new supporting evidence is actually reviewed.

## Tests and limits

`tests/assistant_browser.py` tests the original UI with mocked generation and probes the pinned runtime/configuration separately; it is not an LLM quality benchmark. After the final factual-answer pass, `tests/assistant_quality_browser.py` exercises actual DOM responses with no mocked prose. It checks complete 3501 and AÜB rosters, Yeşim Taktat Ateş in both applications, unknown technical duties, named-person follow-ups, email answers, project dates, citations, ambiguity handling, HTML injection resistance, no automatic model download and three widths in both languages. A changed-input assertion verifies that a project stage is read from current data rather than fixed example output. The --offline option inlines local assets in restricted environments. Repeated viewport/language checks are not distinct questions and must not be reported as a general model-quality score.

A fluent, indownload-free cloud assistant requires a separately authorised hosting/backend connection and a provider account with usage controls. No such provider is connected by this release. Do not place provider credentials in the public repository or ask the user to paste secrets into chat. The present factual-answer improvement is an interim quality safeguard, not a claim of cloud-level conversation quality.
