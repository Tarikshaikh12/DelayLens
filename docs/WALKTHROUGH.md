# Explain the reviewed project in simple English

## What decision does it study?

A team can inspect only a limited number of orders each day. We ask whether a
machine-learning score finds more late deliveries than simple rules within the
same review limit. Finding a late order does not prove that reviewing it helps.

## What is known when an order is approved?

We use the order's promised date, price and parcel details, location categories,
and history of deliveries already completed before that moment. The final
snapshot does not prove that catalogue fields or promises never changed later.
That remaining assumption is explicit; this is not fully versioned event data.

## Why keep unknown outcomes?

Removing orders just because they never show a delivery can make the queue look
better than it is. Every input-eligible order stays. If selected, an unresolved
order uses a review slot. We report confirmed late hits and the unknown count.
A lower bound assumes unknown outcomes do not add late hits; an upper bound
allows them to. Cancellation may be a competing outcome rather than late delivery.

## How is the model evaluated?

Each development month trains only on the preceding window and completed outcomes
available before the month starts. Monthly queues use the same orders, capacities
and tie rule. The calendar windows and configurations are in the committed
protocol. Model selection uses monthly paired capacity differences, not one
month's average precision. A small numerical lead is not a deployment decision.

## Why did we add a conservative promotion gate?

Unknown labels are not necessarily random. We consider the adverse case where
unknown orders uniquely selected by a rule turn out late and those uniquely
selected by ML do not. The model must still pass the preregistered uncertainty
and consistency requirements. This is a conservative policy choice, not proof
that those adverse outcomes actually occurred.

## What do the monotone constraints mean?

Keeping other inputs fixed, allowing more time should not increase predicted
lateness. We constrain promised days and both slack features in that direction.
We test each coordinate and the joint change. This is a model assumption; it does
not prove that changing a promise causes a particular operational outcome.

## What does calibration change?

A strictly increasing probability transform keeps the order ranking unchanged.
The original sigmoid calibration therefore cannot improve the top-ranked queue.
The new comparison evaluates ranking directly and does not fit a calibrator.

## How should I explain the outcome?

Read the generated `reports/review/SUMMARY.md`. Distinguish a lead on confirmed
outcomes from passing the missing-outcome robustness gate. The preferred method
was frozen using development data. July–August only measures a retrospective
stress scenario; it does not change that preference.

## What would be required before adoption?

A new prospectively observed cohort, reliable outcome collection, versioned
approval-time inputs, an implemented historical-feature service, and an actual
intervention study. None of those is supplied by a polished dashboard.
