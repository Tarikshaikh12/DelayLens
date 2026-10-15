# Data contract

Current research: `src/delaylens/data.py`, `review_features.py`, `review.py` and
`experiments/REVIEW_PROTOCOL.md` are authoritative. Input eligibility is based on
valid approval-time OrderInput fields and exactly one seller. Final status and
outcome availability do not select the prediction cohort. Raw and eligible counts
and every exclusion reason are generated in `reports/review/cohort_audit.json`.

A valid recorded delivery timestamp on or after approval supplies the target:
delivery calendar date after the promise is late; the same promised day is on time.
Missing or impossible delivery timestamps remain unknown. Conflicting final
status is audited without dropping the order. Development evaluation masks
outcomes unavailable at its fixed selection clock without removing their rows.
Training requires an observed outcome strictly before the training cutoff.

History updates only when a valid delivery event is strictly earlier than the
current approval. Final status does not update history. Geographical centroids
and order/catalogue fields come from the final snapshot; historical availability
and revisions are not observable and remain explicit limitations.

The original API contract is intentionally narrower: it exposes the old frozen
model and its original features through OrderInput. It does not pretend to serve
the newly preferred method. `/research/evaluation` describes the new research;
`/evaluation` preserves the original model's matched legacy evidence.

Cache provenance verifies all pinned raw hashes, preparation code, and the cache
file checksum before use. Do not load unknown pickle/joblib files from outside
this trusted project: these formats can execute code. User-facing uploads accept
order JSON, never executable model artifacts.
