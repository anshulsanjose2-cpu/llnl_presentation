# LLNL Panel — Talk Track & Delivery Guide
**Role:** AI Solutions Engineer · **Goal:** demonstrate SES.4 (Principal/Lead Architect) mastery
**Total target:** 15–18 min talking + buffer for questions

> **The level tell:** An S3 explains *how RAG works*. A principal explains *why most deployments fail, what they'd decide differently, and how they de-risk it organizationally.* Talk about **decisions, tradeoffs, failure modes, and org leverage** — not implementation steps. **Never claim the level — demonstrate it and let the panel conclude it.**

---

## Time budget
| Slide | Topic | Time |
|---|---|---|
| Title | Open | 0:15 |
| 1 | Introduction | 1:30 |
| 2a | Naive RAG + failure modes (setup) | 1:30 |
| 2b | Three-plane architecture (ANCHOR) | 2:30 |
| 3 | Retrieval + Evaluation depth | 2:30 |
| 4a | Case study — architecture | 2:00 |
| 4b | Case study — impact + leadership | 2:00 |
| 5 | Tooling ecosystem | 2:30 |
| 6 | Close | 1:00 |
| — | **Q&A** | remaining |

---

## TITLE (15s)
"Thank you for the time. I'm going to walk you through how I think about building LLM systems an organization can actually depend on — covering the four areas you asked about. I'll leave plenty of room for questions."

## SLIDE 1 — Introduction (90s)
"I'm Anshul Sharma. I have a master's in software engineering and thirteen years building production systems — starting in distributed systems, then large-scale productivity applications, then agentic systems, and now RAG and GenAI architecture. Quick credential anchor: I wrote *RAG in Production*, and I'm the inventor of the ILEI Architecture, which is patent-pending with the USPTO. I mention those not as trophies but because they're the same thread — a body of work on making LLM systems dependable.

Take away from this slide a trajectory, not a job list. I came to AI from distributed systems — so I don't see a model, I see a *distributed system with a probabilistic component in the critical path*. That framing changes every architectural decision.

My operating principle: I treat the language model as the **least reliable component in the system**, and I architect everything around containing and measuring that uncertainty.

At this stage of my career I lead less by writing the most code and more by setting architecture, defining what 'good' means in measurable terms, and getting data owners, security, and domain experts aligned *before* we build. In an environment where a confidently wrong answer has real cost, that discipline is the whole game."

## SLIDE 2a — The naive RAG (setup, ~1.5 min)
*Be generous about it — you respect it as a starting point, which makes the teardown credible.*
"If you ask most people what a RAG implementation is, this is it: chunk your documents, embed them, drop them in a vector database, retrieve top-k, hand it to the model. And honestly, this is a perfectly fine way to prove the concept in an afternoon — I've built this, it demos beautifully.

But the moment it meets real data, real users, and real consequences, it breaks in specific, predictable ways." [Walk 2–3 red failures — pick the Lab-relevant ones: no access control means it retrieves chunks the user isn't cleared to see; no evaluation means hallucinations ship silently.] "Every one of these is a production requirement the demo quietly ignored. So let me show you how I actually build it."

## SLIDE 2b — Three planes, not one pipeline (ANCHOR, 2.5 min)
"**The most important architectural decision I make: I split it into three planes.** An offline **Knowledge Plane** — governed, versioned, reproducible — an online **Serving Plane** that's about latency and validation, and a **Control Plane** that spans both. The first two fail differently, scale differently, and are owned by different people. Conflating them is the root cause of most production RAG problems.

Notice governance isn't a step at the end. Access-control identity, PII tags, and lineage travel *with* each chunk, and **ACLs are enforced at retrieval time** — by the time you're at the LLM, a leak has already happened.

And a third layer cuts across both — I call it the **Control Plane**: an evaluation harness that gates deployment, end-to-end tracing, access and governance with full audit, and caching and cost controls. Knowledge Plane, Serving Plane, Control Plane — that's the whole system in three words."

## SLIDE 3 — Retrieval is the system (2.5 min)
"The biggest lever on quality is not which model — it's whether the right context is in front of it.

That means **hybrid retrieval**: dense vectors plus sparse BM25, because pure semantic search quietly fails on exact terms — part numbers, acronyms — the precise tokens that matter in technical and scientific domains. Then **re-ranking** to fix ordering, and **structure-aware chunking** so we don't sever a table or split a claim from its caveat. I've repeatedly seen better chunking and re-ranking beat a more expensive model. So when a system hallucinates, my first question is never 'upgrade the model' — it's 'show me the retrieved context.'

On evaluation: I measure retrieval and generation **separately**. Context precision and recall on retrieval. **Faithfulness** and answer relevance on generation — faithfulness is the one I obsess over. I build the eval set *with domain experts*, run it on every change, and gate deployments on it like a test suite. If we can't measure it, we don't ship it.

[Land slowly:] A fluent, confident, unsupported answer is the most dangerous output a RAG system can produce. I'd rather it say 'I don't have enough information' than guess — refusal is a feature, not a failure."

## SLIDE 4a — Case study: architecture (2 min) ⚠️ CONFIRM NUMBERS ON 4b
Project: a unified knowledge assistant over **Wiki + Slack (public channels) + Jira**. Point of this slide: one assistant, but each source forced a *different* engineering problem — that range is the senior signal.

"My most recent enterprise project was a knowledge assistant that unified three systems engineers were losing hours across — our docs wiki, public Slack channels, and Jira. The hardest part wasn't the LLM, it was that these three sources fail differently.

Wiki goes stale — so I added recency decay and canonical-URL dedup. Slack is conversational with no ground truth — so I reconstructed threads, resolved mentions and links, extracted Q&A pairs, and critically filtered to *public channels only*; that's access control enforced at ingestion. Jira is half structured fields, half freeform comments — so I parsed fields and weighted resolved, accepted answers.

They normalize into one unified, ACL-tagged index. And the assistant lives where engineers already are — in Slack — answering with deep links back to the source, so every claim is verifiable."

## SLIDE 4b — Case study: impact + leadership (2 min)
Lead with metrics, then decisions, then the leadership beat (the SES.4 signal).

"Impact: we cut search time by about eighty percent — which, across the engineering org, added up to over thirty thousand man-hours saved year over year. Faithfulness held above 0.9 on our eval set. And engineers went from searching three systems to asking one.

The decisions I owned map exactly to that architecture. The conscious tradeoff: I tuned for *precision over coverage* — refuse-over-guess — because in an early rollout, one confident wrong answer destroys trust faster than ten honest 'I don't knows.'

And the part I'm proudest of isn't the stack — I got security, data owners, and SMEs aligned on access policy before we wrote a line of code, and the evaluation gate moved the team from 'looks good to me' to *measured*."

> ⚠️ **Confirm the supporting numbers (0.92 faithfulness, 3→1) are defensible** — the headline figures (−80% search time, 30,000+ hrs/yr) are your real ones. Be ready to explain *how* 30K hours was estimated (e.g., users × queries/wk × minutes saved). A Lab panel may probe the math.

## SLIDE 5 — Tooling ecosystem (2.5 min)
"I'm opinionated, but loyal to capabilities, not vendors. I use frameworks like LangChain and LlamaIndex to move fast, but in production I keep a thin custom layer on the critical path so I can trace and test it.

On models I weigh capability-per-dollar and latency — and critically, whether it can run inside the security boundary, which matters enormously here; that's where open-weight models like Llama or Mistral earn their place alongside frontier models like Claude. On stores, pgvector through Milvus or Qdrant depending on scale and ACL filtering needs, with BM25 for the hybrid layer. Evaluation tooling — RAGAS-style metrics and custom harnesses — has to gate CI. Guardrails enforce citations and structured output.

The punchline: in a deterministic-outcomes environment, I won't hand reliability to a black box I can't trace or test."

## SLIDE 6 — Close (60s)
"To bring it back to what the Lab prioritizes: deterministic outcomes — evaluation as a gate, refuse-over-guess by design. Data governance — ACLs, lineage, PII handling that travel with the data, in-boundary by default. Rigorous evaluation, measured continuously. Robust architecture — two planes, an owned critical path, full observability. And it's multidisciplinary — I align security, data owners, and domain experts as part of the architecture.

What I bring isn't 'I can build a RAG pipeline.' It's 'I can make an LLM system the Lab can defend, audit, and trust at scale' — and bring the organization along to do it. Thank you. I'd love to dig into any of these."

---

## Likely panel questions — have crisp answers ready
- **"How do you actually measure faithfulness?"** → grounding check: decompose answer into claims, verify each against retrieved context (LLM-as-judge calibrated against a human-labeled set + holdout).
- **"How do you stop the LLM leaking restricted data?"** → enforce at retrieval (ACL filter on metadata) so restricted chunks never enter context; defense-in-depth with output filters; audit log every retrieval.
- **"Why not just use the biggest model / a managed API?"** → boundary/auditability/latency/cost control; the lever is retrieval quality, not model size; black boxes you can't trace fail the deterministic-outcomes bar.
- **"How do you handle the corpus changing / stale answers?"** → versioned knowledge plane, re-index pipelines, lineage so revoked/updated sources propagate deterministically.
- **"Where does this break / what keeps you up at night?"** → silent retrieval degradation (good-looking answers on wrong context) → why continuous eval + tracing exist; and chunking choices on heterogeneous docs.
- **"What would you do differently next time?"** → invest in the eval set and SME loop *earlier* — it's the highest-leverage and most-deferred piece.
- **"What is the ILEI Architecture?"** (they WILL ask) → [FILL IN: what ILEI stands for + the one problem it solves + why it's novel]. 30-second version: "It's the architecture pattern behind everything I just described — [one-line value prop]. It's filed as a USPTO provisional, 63/076,477." Then tie it to a Lab need.

## Delivery reminders
- Slow down on Slides 2–3. Silence after the "refuse is a feature" line.
- Pair every tool with a *decision criterion* — never name-drop bare.
- Use their words: deterministic, governance, faithfulness, context precision.
- Don't say "I'm above this band." Demonstrate altitude; let them reach the conclusion.
