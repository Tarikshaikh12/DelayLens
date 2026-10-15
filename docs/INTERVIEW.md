# Interview questions and short answers

**1. What problem does DelayLens solve?**

It studies which orders to review within a fixed daily limit, not whether an intervention saves money.

**2. When is a prediction made?**

At approval. Historical statistics use only deliveries completed strictly earlier. Snapshot field availability remains an assumption.

**3. Why not remove undelivered orders?**

That selects the evaluation population using a future outcome. Unknown outcomes must remain in the queue and use review capacity.

**4. How is the target defined?**

A valid delivery calendar date after the promised date is late. Same-day delivery is on time; absent or impossible delivery timestamps are unknown.

**5. How was the method selected?**

Using prespecified rolling months and mean paired confirmed late-hit differences at the primary budget, with consistency and uncertainty gates.

**6. Did the monotone model improve anything?**

It improved observed development hits, but did not pass the conservative missing-outcome promotion gate. Those are different claims.

**7. What does a monotone constraint mean?**

With other features fixed, a longer promise or more slack cannot increase predicted lateness. This is a modelling assumption, not a causal finding.

**8. Why is July–August not a clean test?**

Its results had already informed earlier discussions. It is retrospective stress evidence and never selects a method in this run.

**9. Can calibration improve the daily queue?**

A strictly increasing calibration transform preserves ranking, so it cannot change which orders are selected apart from implementation-level ties.

**10. What would you need before adoption?**

Prospective data, reliable unknown-outcome resolution, versioned inputs, an operational feature service and evidence that the review action improves outcomes.