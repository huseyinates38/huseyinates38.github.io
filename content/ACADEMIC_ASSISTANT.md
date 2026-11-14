# Academic conversation assistant

The final additive build stage `scripts/build_assistant.py` runs after the existing site/browser gates and before the final link/checksum/publish stages. It creates EN/TR `assistant.html`, a public-HTML knowledge snapshot, entry links and scoped styles. Existing research statuses and review dates are unchanged.

## Real generation and fallback

Generation is opt-in and happens on the visitor's device using WebLLM 0.2.88 and Qwen3-0.6B-q4f16_1-MLC. Official references: https://webllm.mlc.ai/docs/user/basic_usage.html and https://huggingface.co/mlc-ai/Qwen3-0.6B-q4f16_1-MLC . No API key is used. The model is small and is not a substitute for a reliable cloud assistant or for the academic's personal judgement. A compatible WebGPU device with shader-f16 support is required. The initial model/runtime download is roughly 400 MB; mobile compatibility and speed vary.

Before opting in, and on unsupported devices, the conversation shows clearly labelled source excerpts. It must never describe this deterministic retrieval as an LLM-generated answer. Source links are generated from the public corpus, not from model-provided HTML. The source corpus preserves the existing exclusion of person-tugce-unsal.html from discovery.

The assistant is visibly labelled as AI, not Hüseyin Ateş himself. It cannot deliver messages, accept admissions, promise funding, make appointments or claim personal endorsement. The contact page remains available. General educational explanations must be distinguished from verified website facts. No unverified project status is promoted to funded.

## Privacy and controls

Questions/history remain in page memory, not localStorage or a remote API. There is no analytics, chat database or automatic model download. Explicit consent starts third-party program/model requests (jsDelivr, Hugging Face, MLC-hosted model libraries); their normal request metadata is outside this site's control. Downloaded weights may remain in the browser cache. Stop terminates the worker; Clear also clears the conversation. User/model strings are rendered as text, never HTML. Limits: 1,200 input characters, short bounded history/context, 450 generated tokens, loading and generation timeouts.

## Validation

`python tests/assistant_browser.py` covers EN/TR at 390/768/1440 px, source retrieval, dual 3501/AÜB records, no auto-download, explicit consent, identity disclosure, contact handling, unsupported GPU fallback, text/HTML injection safety, clear/stop and the worker protocol. Inference is mocked for deterministic UI tests; the report states this explicitly. Online CI also imports the real pinned runtime and checks the real model configuration. This is not a test of generated-answer quality or a claim that real GPU inference ran on the test machine. `--offline` runs the UI tests with inlined assets in restricted environments.

A universal no-download/cloud experience would require a separately authorised backend and provider account. Never put provider secrets in public assets or the GitHub Pages bundle.
