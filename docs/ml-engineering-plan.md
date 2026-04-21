# ML Engineering Plan for Ops Agent

## Current Documents Module Baseline

The Documents module does not require an ML training plan for identity-document extraction. Use [production-llm-document-extraction-backend-spec.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\production-llm-document-extraction-backend-spec.md) as the active implementation source. Extraction is inference-only using OpenAI GPT-4o or GPT-4o-mini Vision, LangGraph orchestration, Pillow preprocessing, strict Pydantic or JSON Schema validation, one retry, manual review, and approved-only persistence. Any ML engineering content in this document applies only to future optional capabilities outside the current Documents extraction workflow.

## Role

ML Engineer for a banking-grade Document Processing Agent.

## Objective

Design the machine learning and AI components needed for OCR support, document classification, parsing, extraction, confidence estimation, and anomaly support, with production readiness for banking operations.

## Assumptions

1. VietOCR is the mandated OCR engine and remains the only primary OCR model in production.
2. Deterministic rules remain the first control layer for validation, compliance, and decisioning.
3. Classical ML is preferred over LLMs for classification, scoring, ranking, and anomaly support.
4. LLMs are restricted to bounded ambiguity resolution after rules and classical ML are exhausted.
5. Training and monitoring must optimize for noisy operational documents, not only clean benchmark scans.

## Deliverables

- AI problem map
- Model stack
- Dataset requirements
- Training plan
- Inference design
- Evaluation metrics
- Retraining strategy

## Dependencies

1. [ai-architecture.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\ai-architecture.md)
2. [banking-document-rules.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\banking-document-rules.md)
3. [compliance-risk-controls.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\compliance-risk-controls.md)
4. [prompt-system.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\prompt-system.md)
5. labeled document datasets, rule packs, and model registry

## Risks

1. noisy production documents do not resemble curated development datasets
2. OCR quality dominates downstream model performance
3. field-level labels are expensive and inconsistent across annotators
4. class imbalance causes weak performance on rare but important document types
5. low-confidence behavior is under-designed and pushes too much hidden risk downstream

## MVP vs Scale notes

### MVP

1. focus on a narrow document set: passport, national ID, driver's license, utility bill, bank-issued address letter, payslip, employment letter, bank statement, loan application, consent form
2. use template-aware rules plus lightweight ML for classification and quality scoring
3. keep LLM use off the critical path by default
4. optimize for robust abstention and human escalation over marginal automation gains

### Scale

1. broaden template coverage and multilingual support
2. add stronger layout/table models and anomaly detectors
3. expand feedback-driven active learning loops
4. add shadow evaluation for every material model update

## 1. AI Problem Decomposition

## 1.1 Subproblem map

| Subproblem | Type | Primary technique | Output |
|---|---|---|---|
| document image quality estimation | CV / scoring | rule + classical ML | quality score, retry suggestion |
| OCR text extraction | OCR | VietOCR + OpenCV | text blocks, per-line confidence |
| page / region segmentation | CV / parsing | OpenCV + classical CV | regions, tables, key-value zones |
| document classification | multi-class classification | LightGBM / XGBoost + rules | document type probabilities |
| template similarity / issuer matching | retrieval / ranking | embeddings + similarity | top template candidates |
| field extraction | hybrid IE | rules + anchors + retrieval + bounded LLM fallback | field values with evidence |
| field confidence estimation | calibration / scoring | classical ML + heuristics | field confidence score |
| cross-document anomaly support | anomaly scoring | LightGBM / isolation-style scoring | mismatch / risk score |
| reviewer assistance summary | bounded generation | LLM | structured summary only |

## 1.2 Problem ownership by phase

### Must-have in MVP

1. image quality scoring
2. VietOCR inference pipeline
3. document classification
4. template-aware field extraction
5. field confidence estimation
6. basic anomaly support for mismatches and suspicious incompleteness

### Beta

1. stronger layout parsing
2. statement-specific table parsing enhancements
3. LLM reconciliation on ambiguous extraction
4. active learning prioritization

### Scale

1. richer anomaly models
2. multilingual support
3. issuer-generalized document understanding
4. advanced statement transaction parsing

## 2. Model Stack Recommendations

## 2.1 Model stack by function

| Function | Recommended model stack | Rationale |
|---|---|---|
| OCR | VietOCR + OpenCV preprocessing | required stack; best fit for text extraction pipeline control |
| image quality scoring | LightGBM on image features + OCR stats | fast and explainable scoring for retry / review routing |
| document classification | LightGBM or XGBoost on OCR tokens, layout features, template similarity | low latency, easy calibration, robust on tabular features |
| template retrieval | SentenceTransformers / BGE / E5 embeddings in Weaviate | supports nearest-template lookup without forcing LLM use |
| field extraction | rules + regex + layout anchors + nearest-template guidance | most auditable and cheapest for structured banking docs |
| extraction fallback | local LLM or OpenAI only in bounded JSON mode | only for unresolved ambiguity |
| field confidence estimator | calibrated LightGBM on evidence features | better than raw heuristic thresholds alone |
| anomaly support | LightGBM or XGBoost binary models | suited for suspicious mismatch / incomplete-pack scoring |

## 2.2 Recommended concrete models

### OCR

1. VietOCR production model variant tuned for banking documents
2. PyTorch inference with GPU queue and CPU fallback

### Embeddings

1. `bge-small` or `e5-base` for template retrieval in MVP
2. move to larger embedding models only if retrieval quality limits extraction support

### Classification

1. LightGBM as the default
2. XGBoost as benchmark comparator

### Confidence / anomaly scorers

1. LightGBM for field confidence calibration
2. LightGBM for suspicious mismatch risk scoring

### LLM fallback

1. local Mistral/Llama-class model as default bounded fallback
2. OpenAI optional only when approved by data-handling policy

## 2.3 Trade-offs

| Choice | Latency | Cost | Accuracy | Auditability | Notes |
|---|---:|---:|---:|---:|---|
| rules only | low | low | medium on noisy docs | high | best default path |
| rules + LightGBM | low | low | high for routing/classification | high | preferred for MVP |
| rules + LLM | medium/high | medium/high | higher on ambiguous cases | lower | only bounded fallback |
| larger embedding models | medium | medium | moderate gain | medium | use only if retrieval quality is blocking |

## 3. Dataset and Labeling Requirements

## 3.1 Dataset structure

Each sample should include:

1. raw document file
2. derived page images
3. workflow type
4. source channel
5. document type label
6. document quality label
7. page- and block-level OCR ground truth where available
8. field labels with evidence boxes
9. validation truth labels
10. reviewer correction outcomes

## 3.2 Required labeled datasets

| Dataset | Purpose | Minimum need for MVP |
|---|---|---|
| OCR text benchmark | evaluate VietOCR on banking docs | 2k to 5k pages with line-level ground truth |
| document classification set | classify supported doc types | 500 to 2k docs per major class if possible |
| field extraction truth set | supervise extraction and confidence calibration | 300 to 1k docs per in-scope type with field annotations |
| quality / readability set | learn retry / review routing | 1k+ pages labeled clean / usable / poor / unreadable |
| anomaly support set | mismatch and suspicious-case support | curated positive and negative cases from reviewer history |

## 3.3 Labeling policy

1. Label from source document evidence, not inferred truth from external systems.
2. For every field label, capture:
   - field name
   - canonical value
   - original source text
   - page number
   - bounding box
   - annotation confidence
3. Mark ambiguous labels explicitly instead of forcing a single truth value.
4. Keep separate labels for:
   - document missing field
   - field present but unreadable
   - OCR extracted incorrectly

## 3.4 Hard dataset requirements for banking realism

Training data must include:

1. low-resolution scans
2. skewed camera captures
3. photocopies and reprints
4. partially cropped uploads
5. mixed-language tokens where present
6. varied issuers and templates
7. poor lighting and background noise

Without this, benchmark scores will overstate production performance.

## 4. Training Pipeline Plan

## 4.1 Pipeline stages

1. ingest labeled artifacts into a curated training bucket
2. validate label schema and annotation completeness
3. split data by issuer/template/time to reduce leakage
4. build train / validation / test sets
5. compute baseline rule-only performance
6. train ML models
7. calibrate probabilities
8. evaluate on clean, noisy, and adversarial slices
9. register artifact versions
10. publish benchmark report

## 4.2 Data split rules

Use split policies that avoid unrealistic leakage:

1. separate train/test by document instance
2. where possible, separate by issuer/template family
3. maintain a temporal holdout for recent production patterns
4. keep a fixed golden holdout that never participates in tuning

## 4.3 Feature sets

### Classification features

1. OCR token TF/IDF or hashed n-grams
2. presence of anchor terms
3. page count
4. layout region counts
5. MRZ presence flag
6. issuer keyword matches
7. document dimensions and aspect ratios

### Field confidence features

1. OCR line confidence
2. anchor match score
3. regex / pattern pass flags
4. value normalization success
5. cross-field consistency flags
6. cross-document consistency flags
7. template similarity score

### Quality / anomaly features

1. blur / noise / skew metrics from OpenCV
2. OCR coverage ratio
3. missing critical region indicators
4. cross-document mismatch counts
5. duplicate / repeated template anomalies

## 4.4 Calibration

All probabilistic models must be calibrated before production. Use:

1. isotonic regression where data volume supports it
2. Platt scaling as fallback

Calibration quality must be reported, not assumed.

## 5. Inference Pipeline Plan

## 5.1 Inference order

1. preprocess document with OpenCV
2. run VietOCR
3. compute quality features and OCR confidence
4. run document classification
5. run template retrieval
6. apply deterministic extraction
7. run field confidence estimator
8. if medium confidence:
   - alternate preprocess profile
   - region-level re-OCR
   - alternate template extraction
   - optional bounded LLM reconcile
9. run validation and anomaly support scorers
10. hand off to compliance and decision layers

## 5.2 Inference contract

Every model output must contain:

1. model name
2. model version
3. input artifact refs
4. output payload
5. confidence score
6. status
7. latency
8. fallback path used

## 5.3 Low-confidence handling

Low confidence is a designed path, not an error.

### OCR low confidence

1. re-run with alternate preprocessing
2. region crop retry
3. if still low on critical regions, escalate to review

### Classification low confidence

1. compare top-k classes
2. consult template retrieval
3. if unresolved, `unknown_document_type` and review

### Extraction low confidence

1. keep only evidence-backed fields
2. mark unresolved mandatory fields explicitly
3. use bounded fallback only if policy allows
4. otherwise review

## 6. Evaluation Framework

## 6.1 Metrics by component

| Component | Primary metrics | Secondary metrics |
|---|---|---|
| OCR | CER, WER, line accuracy | page coverage, critical-field text recall |
| document classification | macro F1, per-class recall, calibration error | top-2 accuracy, confusion matrix |
| field extraction | exact match, normalized exact match, field recall on mandatory fields | evidence coverage rate |
| field confidence model | AUROC, AUPRC, Brier score, calibration error | threshold precision/recall |
| anomaly support | precision at review budget, recall on known positives | false alert rate |

## 6.2 Banking-specific evaluation slices

Always report results by:

1. document type
2. issuer / template family
3. source channel
4. image quality bucket
5. language bucket if applicable
6. workflow type

Average-only reporting is not acceptable for production readiness.

## 6.3 Threshold metrics for MVP readiness

Suggested initial targets:

1. OCR CER on in-scope clean pages: <= 5%
2. OCR CER on noisy pages: <= 12%
3. document classification macro F1 on MVP types: >= 0.93
4. mandatory field extraction exact/normalized match: >= 0.92
5. critical field evidence coverage: 100%
6. low-confidence recall on truly bad cases: high enough that false-safe automation remains near zero

These targets are starting points and must be validated against real pilot data.

## 7. Error Analysis Framework

## 7.1 Error taxonomy

Classify every failure into one primary bucket:

1. source image quality issue
2. OCR recognition issue
3. layout segmentation issue
4. document misclassification
5. extraction anchor failure
6. normalization/parsing failure
7. confidence miscalibration
8. anomaly false positive / false negative
9. fallback path failure
10. labeling ambiguity

## 7.2 Review workflow

For each model release:

1. inspect top false accepts
2. inspect top false rejects
3. inspect all critical-field failures
4. inspect all cases where human reviewers overrode high-confidence outputs
5. inspect all production DLQ cases touching AI services

## 7.3 Root-cause outputs

Error analysis reports should answer:

1. what failed
2. why it failed
3. whether the issue is data, model, prompt, rule, or orchestration related
4. whether the failure should be solved by:
   - more labels
   - better preprocessing
   - better features
   - stricter thresholding
   - fallback routing

## 8. Retraining Strategy

## 8.1 Feedback sources

Use these feedback signals:

1. reviewer field corrections
2. reviewer class corrections
3. escalation outcomes
4. low-confidence review outcomes
5. DLQ and processing-failure cases
6. periodic QA sample reviews

## 8.2 Retraining cadence

### MVP

1. monthly data refresh for classification and confidence models
2. quarterly OCR evaluation review unless drift or incident forces earlier review

### Scale

1. continuous labeling intake
2. biweekly or monthly candidate retrains depending document volume
3. shadow deployment before promotion

## 8.3 Retraining gates

A new model version should not be promoted unless:

1. it beats or matches production on golden holdout
2. it does not worsen critical-field recall
3. it does not increase unsafe false-pass behavior
4. calibration quality remains acceptable
5. regression slices remain stable on noisy documents

## 8.4 Active learning

Prioritize labeling for:

1. low-confidence cases
2. reviewer-overridden high-confidence cases
3. newly seen templates
4. repeated escalation clusters
5. rare document types with poor recall

## 9. Production Monitoring

## 9.1 Online metrics

Track per model:

1. input volume
2. latency
3. confidence distribution
4. abstention / review rate
5. downstream correction rate
6. drift indicators on OCR tokens and features
7. template novelty rate

## 9.2 Alert conditions

Alert when:

1. OCR confidence distribution shifts materially
2. document class mix changes sharply
3. reviewer correction rate rises above baseline
4. high-confidence outputs are increasingly overridden
5. anomaly review queue spikes

## 10. Major Risks and Expected Failure Modes

## 10.1 Expected failure modes

| Failure mode | Likely cause | Safe handling |
|---|---|---|
| unreadable OCR on critical fields | poor scan quality | re-OCR then human review |
| wrong document class on rare template | class imbalance / unseen issuer | unknown class + review |
| extracted wrong but plausible value | OCR text confusion or anchor drift | confidence penalty, cross-document validation, human review |
| overconfident bad prediction | miscalibration | conservative thresholding and override monitoring |
| weak anomaly recall | sparse positive labels | rules + analyst feedback + incremental retraining |
| model drift | new templates / channels | drift monitoring, shadow evaluation, retraining |

## 10.2 Engineering risks

1. over-investing in complex models before data quality is mature
2. under-investing in annotation quality and evidence structure
3. using clean benchmark data that hides production failure modes
4. treating low confidence as noise instead of a routing signal

## 11. Recommended ML Build Sequence

1. dataset schema and annotation tooling
2. VietOCR preprocessing and evaluation harness
3. document classification baseline
4. deterministic extraction + field confidence baseline
5. confidence calibration layer
6. anomaly support baseline
7. reviewer feedback capture loop
8. bounded LLM fallback only after the above are stable

## 12. Recommended ML Stance

For Ops Agent, the right ML strategy is:

1. OCR as the foundation,
2. small, well-calibrated models for classification and scoring,
3. rules for validation,
4. conservative abstention,
5. human review for unresolved ambiguity.

That is more valuable for real banking documents than chasing model novelty.
