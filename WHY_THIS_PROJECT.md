# Why This Project Is Needed

> Draft v1 for review. Written as an answer to the judges' question: *what problem are we solving, and why does it matter?*
> Every external claim has a source link. Items marked **[VERIFY]** were found in a single or secondary source and should be checked before presenting. Items marked **[NOT RESEARCHED]** are gaps.

---

## 1. The one-paragraph answer

Organisations (government departments, and startups that resell chatbots) increasingly build on third-party LLMs. Guardrails check each request in isolation, but nothing checks whether a model's **ethical behaviour is getting worse over time**. Hosted models change silently, guardrails can be bypassed, and the organisation that deploys the chatbot is the one held responsible when it gives a wrong or unfair answer. Regulators (EU AI Act, UK AI Playbook, OECD) are moving toward requiring **continuous, evidence-based monitoring**, not one-off checks. Our system provides that: it scores every LLM's outputs on ethical dimensions, tracks drift, and automatically blocks a model that crosses a threshold until it is fixed and re-qualified.

---

## 2. The real-world problems

### 2.1 Models change underneath you, and you are not told

- A Stanford/Berkeley study compared March and June 2023 versions of GPT-3.5 and GPT-4. GPT-4's accuracy on identifying prime numbers fell from 84% to 51%. It also followed instructions less well and became less willing to answer sensitive questions. Some tasks improved while others got worse. The authors conclude that the "same" LLM service can change substantially in a short time, which is why continuous monitoring is needed. ([Chen, Zaharia, Zou, 2023](https://arxiv.org/pdf/2307.09009.pdf))
- Researchers studying `gpt-3.5-turbo` found it was updated twice without visibility to downstream developers, and that an API update could cause a major performance downgrade. ([Ma, Yang & Kästner, CAIN 2024](https://conf.researchr.org/details/cain-2024/cain-2024-call-for-papers/10/-Why-Is-My-Prompt-Getting-Worse-Rethinking-Regression-Testing-for-Evolving-LLM-APIs))
- Industry write-ups report short deprecation notice periods and floating aliases (e.g. a model name without a date silently resolving to whatever is "latest"). **[VERIFY]**: these are practitioner blogs; check each provider's deprecation page before citing specific dates. ([example](https://tianpan.co/blog/2026/04/13/the-model-deprecation-cliff))

**Consequence:** A model that was safe at procurement time may not be safe six months later, and the deployer may not know.

> Caveat for the pitch: the Chen et al. study uses 2023 model versions. It proves the *phenomenon*, not that today's models drift by the same amount. If time allows, we can run our own drift evidence from the project's data (see section 6).

### 2.2 Guardrails are necessary but not sufficient

- A 2025 empirical study tested six guardrail/prompt-injection detection systems (including Azure Prompt Shield and Meta Prompt Guard) and reported evasion success of up to 100% in some cases using simple character-injection techniques. ([arXiv 2504.11168](https://arxiv.org/pdf/2504.11168))
- A systematisation-of-knowledge paper finds the guardrail field fragmented, with evaluations focusing on defence efficacy against specific benchmarks and often ignoring cost and false-positive rates. ([SoK, arXiv 2506.10597](https://arxiv.org/html/2506.10597v1))
- Guardrails also operate **per request**. They do not produce a time series, so they cannot answer "is this model getting less fair than last month?"

### 2.3 The deployer is held responsible, not the model vendor

- **Air Canada (Moffatt v. Air Canada, 2024):** A tribunal held the airline liable for wrong refund information given by its website chatbot, rejected the argument that the chatbot was a separate entity responsible for its own actions, and framed the duty as taking reasonable care that the chatbot is accurate. This is a small-claims decision in Canada, not binding elsewhere, but it shows how courts may reason. ([Forsters](https://www.forsters.co.uk/p/102j1zr/ai-provides-advice-that-is-plane-wrong-who-is-liable), [McMillan](https://mcmillan.ca/insights/a-word-of-caution-company-liable-for-misrepresentations-made-by-chatbot/))
- **NYC MyCity chatbot (government):** A 2024 investigation by The Markup found the city's business chatbot repeatedly gave inaccurate answers on housing, labour and consumer law, including telling users that landlords need not accept tenants on rental assistance, which conflicts with city law. The city kept it online with a "beta" label. In January 2026 the new mayor called it "functionally unusable" and announced plans to take it down; it reportedly cost about half a million dollars. ([The Markup, 2024](https://themarkup.org/news/2024/04/02/malfunctioning-nyc-ai-chatbot-still-active-despite-widespread-evidence-its-encouraging-illegal-behavior), [The Markup, 2026](https://themarkup.org/artificial-intelligence/2026/01/30/mamdani-to-kill-the-nyc-ai-chatbot-we-caught-telling-businesses-to-break-the-law)). Note: one secondary source describes a Section 8 example slightly differently; use The Markup's wording.

**Why NYC matters for our pitch:** the failure was not one bad answer. It was a *persistent pattern* that stayed live for roughly two years because there was no mechanism that said "this crossed a threshold, switch it off." That is exactly the gap our system fills.

### 2.4 The measurement problem the problem statement describes

Government AI systems expose only prompts, responses, retrieved documents and telemetry, not model internals. There is no standard, quantified way to say whether a response was fair, accurate, transparent or lawful. Departments currently rely on policy documents and manual audits, which do not scale and do not run continuously. (From the sponsor's problem statement.)

---

## 3. What the regulators expect

> **Read this first: timing.** The EU AI Act's high-risk obligations were originally due 2 August 2026. The official AI Act text pages now show **2 December 2027** for Annex III systems and **2 August 2028** for Annex I systems, which is consistent with the "Digital Omnibus" postponement reported by law firms ([Gibson Dunn](https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/)). One source says the Omnibus entered into force on 27 July 2026 as Regulation (EU) 2026/1744 **[VERIFY]**, since I found no second source. Say "obligations phasing in through 2027–2028" rather than quoting a single date unless verified.

### 3.1 EU AI Act: what applies and what it asks for

| Article | What it requires | How it connects to drift monitoring |
|---|---|---|
| **Art. 9, Risk management** | A risk management process that runs across the whole lifecycle, including evaluating residual risk after mitigation ([source](https://artificialintelligenceact.eu/article/9/)) | Drift scores are a continuous risk signal; a blocked-then-requalified model is a documented mitigation and residual-risk check |
| **Art. 10, Data governance** | Examine for biases that could harm rights or cause prohibited discrimination, and take measures to detect, prevent and mitigate them ([source](https://artificialintelligenceact.eu/article/10/)) | Fairness dimension measured on live outputs. Note Art. 10 is written for training data; for systems that don't train models it applies to testing data, so our probe set is the relevant artefact |
| **Art. 12, Record-keeping** | Automatic event logs over the system's lifetime, enabling identification of risk situations, post-market monitoring and operational monitoring ([source](https://artificialintelligenceact.eu/article/12/)) | Our response/metric logs are the audit trail |
| **Art. 14, Human oversight** | Systems designed so people can prevent or minimise risk; oversight documented; people trained (secondary summary: [Dataiku](https://blog.dataiku.com/eu-ai-act-high-risk-requirements)) | Human approval for re-admitting a blocked model |
| **Art. 15, Accuracy, robustness, cybersecurity** | Appropriate accuracy and robustness maintained over the lifecycle; accuracy metrics declared; resilience incl. fail-safe/backup plans; resistance to AI-specific attacks ([source](https://artificialintelligenceact.eu/article/15/)) | Accuracy and security dimensions; fail-over to another model is the "redundancy / fail-safe" |
| **Art. 26, Deployer obligations** | Deployers must monitor operation, keep logs for at least six months, report serious incidents, and, if they have reason to think use presents a risk, **inform the provider and authority and suspend use** ([source](https://artificialintelligenceact.eu/article/26/)) | The automatic block is a machine-enforced version of "suspend use" |
| **Art. 72, Post-market monitoring** | Providers must run a documented system that actively and systematically collects and analyses performance data over the system's lifetime, based on a monitoring plan in the technical documentation ([Commission service desk](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-72)) | This is the closest regulatory description of what the project does |
| **Art. 50, Transparency** | Users must be told they are interacting with AI; AI-generated text/content must be marked in some contexts. Applies from 2 Aug 2026 per the official page, though the Omnibus reportedly moved a labelling deadline to 2 Dec 2026 **[VERIFY]** ([source](https://artificialintelligenceact.eu/article/50/)) | Transparency dimension (disclosure checks) |
| **Art. 99, Penalties** | Up to €15M or 3% of worldwide turnover for most operator obligations; up to €35M or 7% for prohibited practices; for SMEs/start-ups the **lower** of the two amounts applies ([source](https://artificialintelligenceact.eu/article/99/)) | The cost of not having evidence |

**General-purpose AI models (Art. 53/55):** providers of GPAI models with systemic risk must do adversarial testing, assess and mitigate systemic risk, and report serious incidents ([source](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-55)). These obligations sit with the *model provider* (OpenAI, Meta, etc.), not with the government department or startup that deploys the model. Our system covers the deployer side of the gap: you cannot assume the provider's compliance covers your use case.

### 3.2 UK AI Playbook for Government

Ten principles for safe, responsible and effective use of AI in government. Relevant themes: understanding AI's limits (bias, no guarantee of accuracy), lawful and secure use, **meaningful human control**, managing the full lifecycle, and ongoing assurance, with review boards encouraged. ([Burges Salmon](https://www.burges-salmon.com/articles/102jzoi/artificial-intelligence-playbook-for-the-uk-government-published/), [DWF](https://dwfgroup.com/en-au/news-and-insights/insights/2025/3/uk-government-launches-new-ai-playbook)). **[VERIFY]**: this is from law-firm summaries; for the exact ten principles, fetch the gov.uk original before putting them on a slide.

### 3.3 OECD AI Principles

Five values-based principles: inclusive growth and well-being; human-centred values and fairness; transparency and explainability; **robustness, security and safety (systems must function reliably throughout their lifetime, with risks continually assessed and managed)**; and accountability. Adopted 2019 and revised in 2024. ([OECD legal instrument](https://legalinstruments.oecd.org/public/doc/648/648.en.pdf)). **[VERIFY]**: wording taken via secondary summaries; confirm against the OECD PDF.

### 3.4 RTI Act (India), GDPR

**[NOT RESEARCHED]**. The sponsor's problem statement asks for mapping to the RTI Act and GDPR. This needs its own research pass (e.g. RTI timelines and exemptions; GDPR Art. 22 on automated decisions and Art. 5 accuracy principle). I did not want to fill this in from memory.

---

## 4. The gap: what exists today vs. what regulators and deployers need

| Need | Guardrails | Manual audit | Our system |
|---|---|---|---|
| Block a clearly bad single request | Yes | No | Not our job |
| Notice a model getting worse over weeks | No | Occasionally, slowly | **Yes** |
| Quantified, comparable score per ethical dimension | No | Subjective | **Yes** |
| Compare several LLMs on the same footing | No | Rarely | **Yes** |
| Automatic suspension on threshold breach | No | No | **Yes** |
| Evidence trail for regulators / courts | Partial (blocked-request logs) | Point-in-time reports | **Yes** |
| Works without model internals | Yes | Yes | **Yes** |

---

## 5. Who needs this

1. **Government departments** running citizen-information chatbots (UK, EU, India). They have legal duties of accuracy, fairness and transparency, and public accountability. The NYC case shows the political and financial cost of a chatbot that keeps running while wrong.
2. **Multi-LLM chatbot providers/startups.** They route traffic across several models, are the accountable party (Air Canada logic), and have somewhere to fail over to, which makes automatic quarantine practical. As small firms they also face the lower-of-two fine cap under Art. 99(6), but evidence still matters for contracts and liability.
3. **Procurement and compliance teams** who need a number and an audit trail instead of a vendor's assurance.

---

## 6. How our system answers each problem

| Problem | Our answer |
|---|---|
| Silent model changes | Scheduled **probe set** (fixed prompts) run against every model, plus sampled live traffic, giving a time series per model |
| Guardrails don't show trends | Per-dimension scores with confidence intervals, tracked over rolling windows |
| Deployer is liable | Immutable logs of prompts, responses, scores and decisions; automatic suspension when a threshold is crossed |
| No standard metric for "ethical" | Metric library per dimension, normalised to a common scale, with weights configurable by jurisdiction/department |
| No model internals | All metrics computed from outputs, retrieved documents and telemetry only |
| Need for human control | Auto-block, but human approval to re-admit; the block/unblock history is the audit record |
| Fix and return | Remediate (prompt, retrieval, filter or model-version change), re-run the probe set, re-admit only after clearing the threshold with margin |

> **Please check this table against the actual codebase before presenting.** It is written from your description of the idea. I have not yet read the backend to confirm which of these (probe set, confidence intervals, auto-block, human approval) are implemented versus planned. The repo contains `fairness_data.csv`, `query_api_metrics.csv` and a graphs dashboard, so some of it exists.

---

## 7. Known limitations (say these before the judges do)

- **LLM-as-judge is biased.** Judge models show position bias, verbosity bias and self-preference, so scores must be calibrated against a human-labelled gold set, with answer-order swapping and ideally a judge from a different model family than the one being scored. ([position bias study](https://arxiv.org/html/2406.07791v1), [self-preference](https://arxiv.org/pdf/2410.21819), [survey](https://arxiv.org/pdf/2412.05579))
- **"Ethical" is partly subjective** and varies by jurisdiction; our weights and thresholds are configurable for that reason, but defaults still embed choices.
- **Hosted models can't be retrained** by the deployer. "Make it better" means changing prompts, retrieval, filters or the model version, then re-testing.
- **Monitoring does not transfer legal liability.** It produces evidence of reasonable care. The Air Canada ruling is the kind of standard (reasonable care) that evidence helps meet.
- **Drift evidence is dated.** The best-known drift study is from 2023.

---

## 8. Suggested 30-second answer for the judges

> "Governments and startups are deploying chatbots on LLMs they don't control. Those models change silently, guardrails can be bypassed, and when the chatbot is wrong, the deployer is the one held responsible. Air Canada lost in court over its chatbot, and New York's city chatbot gave businesses illegal advice for about two years. Regulators like the EU AI Act, the UK AI Playbook and the OECD now expect continuous monitoring and the ability to suspend a system that presents risk. Nothing standard does that for LLM ethics. We score every model on ethical dimensions over time, detect drift, and automatically block a model that crosses a threshold until it is fixed and re-qualified."

---

## 9. Open items for next pass

1. Research RTI Act and GDPR mapping (section 3.5).
2. Fetch primary text: gov.uk AI Playbook, OECD PDF, EU Annex III / Art. 6 / Art. 25.
3. Confirm Digital Omnibus status and exact dates from an official EU source.
4. Check the codebase and fill section 6 with what is actually implemented.
5. Optional: generate our own drift evidence from `backend/data/*.csv` so the pitch doesn't rely only on 2023 research.
6. Add a short India-specific incident or example if one exists. I did not search for one.

---

## Sources

- EU AI Act text: [Art. 9](https://artificialintelligenceact.eu/article/9/), [Art. 10](https://artificialintelligenceact.eu/article/10/), [Art. 12](https://artificialintelligenceact.eu/article/12/), [Art. 15](https://artificialintelligenceact.eu/article/15/), [Art. 26](https://artificialintelligenceact.eu/article/26/), [Art. 50](https://artificialintelligenceact.eu/article/50/), [Art. 99](https://artificialintelligenceact.eu/article/99/), [Art. 72 (Commission)](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-72), [Art. 55 (Commission)](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-55)
- [Gibson Dunn on Digital Omnibus](https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/)
- [Chen et al., How Is ChatGPT's Behavior Changing over Time?](https://arxiv.org/pdf/2307.09009.pdf)
- [Ma et al., (Why) Is My Prompt Getting Worse?](https://conf.researchr.org/details/cain-2024/cain-2024-call-for-papers/10/-Why-Is-My-Prompt-Getting-Worse-Rethinking-Regression-Testing-for-Evolving-LLM-APIs)
- [Bypassing LLM Guardrails](https://arxiv.org/pdf/2504.11168), [SoK: Evaluating Jailbreak Guardrails](https://arxiv.org/html/2506.10597v1)
- [Forsters on Air Canada](https://www.forsters.co.uk/p/102j1zr/ai-provides-advice-that-is-plane-wrong-who-is-liable), [McMillan on Air Canada](https://mcmillan.ca/insights/a-word-of-caution-company-liable-for-misrepresentations-made-by-chatbot/)
- [The Markup, NYC chatbot 2024](https://themarkup.org/news/2024/04/02/malfunctioning-nyc-ai-chatbot-still-active-despite-widespread-evidence-its-encouraging-illegal-behavior), [The Markup 2026](https://themarkup.org/artificial-intelligence/2026/01/30/mamdani-to-kill-the-nyc-ai-chatbot-we-caught-telling-businesses-to-break-the-law)
- [Burges Salmon on UK AI Playbook](https://www.burges-salmon.com/articles/102jzoi/artificial-intelligence-playbook-for-the-uk-government-published/), [DWF](https://dwfgroup.com/en-au/news-and-insights/insights/2025/3/uk-government-launches-new-ai-playbook)
- [OECD AI Recommendation](https://legalinstruments.oecd.org/public/doc/648/648.en.pdf)
- LLM-as-judge: [position bias](https://arxiv.org/html/2406.07791v1), [self-preference](https://arxiv.org/pdf/2410.21819), [survey](https://arxiv.org/pdf/2412.05579)
