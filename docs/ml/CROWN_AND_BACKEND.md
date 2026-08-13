# The crown, and whether PointNet++ should replace tlsep

Two questions that had been open, measured together because they turned out to
be the same experiment.

## Question 1: does a better wood/leaf split unlock crown tracing?

`skeleton.trace_crown` measures a synthetic cylinder correctly and is 1490% out
on real crowns, which is why crown volume ships as an equation — the taper total
minus the tracked stem — rather than as a measurement.

The standing hypothesis, written down when that negative result was recorded:
tlsep calls too much foliage wood (leaf IoU 0.31, against 0.83 for doing nothing
at all), and leaves glue neighbouring branches into a blob with no axis to
follow. The shipped PointNet++ checkpoint scores leaf IoU 0.85, so swapping the
backend tests the hypothesis without retraining anything.

**Answer: no.** 17 Demol trees, crown volume against the harvested truth
(total tree minus stem):

| predictor | MAPE | bias | corr with truth | mean pred | mean truth |
|---|---:|---:|---:|---:|---:|
| tlsep traced | 2350.6% | +2338.8% | 0.46 | 2.886 | 0.328 |
| tlsep equation | 99.3% | +49.8% | 0.56 | 0.409 | 0.328 |
| pointnet traced | 152.6% | +28.4% | 0.31 | 0.101 | 0.328 |
| **pointnet equation** | **70.5%** | +20.9% | **0.72** | 0.226 | 0.328 |
| *always answer zero* | *100.0%* | *−100.0%* | — | *0.000* | *0.328* |

Read the traced rows against the zero predictor, not against each other. A
predictor that answers nothing scores exactly 100%, and PointNet++ traced scores
152.6% — it is **worse than refusing to answer**. The first version of this
measurement compared the two backends alone and made the tracer look 22× better;
it was tracing almost nothing (traced fraction 0.20, wood share 37%).

So foliage was not what broke the tracer, and the retraining work queued behind
this hypothesis would not have fixed it either.

### What did turn up

The crown **estimate** improves a lot with the better backend — 99.3% to 70.5%
MAPE, correlation 0.56 to 0.72. That has nothing to do with the tracer. Crown is
the residual of the taper total minus the tracked stem, so a cleaner wood/leaf
split gives a better stem volume and therefore a better residual.

That is a real improvement to a number the product reports. It is not an
improvement to the carbon figure, which comes from Chave on DBH, height and
density; the crown volume feeds `co2eq_volume_route_kg`, the cross-check.

## Question 2: should PointNet++ be promoted?

The policy in `scripts/sync_truth.py` asks for five things:

> verified checkpoint and training provenance, a reproducible independent
> real-data evaluation, improved Wood IoU, non-regressing DBH/height/volume
> errors, and a candidate measurable-tree count at least as high as the baseline.

Wood IoU has been measured many times and PointNet++ wins it. Every case made
for this candidate has rested on that. The two criteria about the measurements
themselves had never been run.

33 Demol trees against taped DBH and felled height, through the production
fit-quality gate:

| backend | reported | DBH MAE | DBH bias | worst | height MAE | wood share |
|---|---:|---:|---:|---:|---:|---:|
| **tlsep** | 32/33 | **0.73 cm** | −0.63 cm | 2.2 cm | **0.42 m** | 79.9% |
| pointnet | 31/33 | 0.75 cm | −0.62 cm | 2.7 cm | 0.59 m | 41.9% |

**Answer: no**, and it fails two of the five criteria outright — height
regresses, and it reports one fewer tree.

Height is where the mechanism shows: the candidate calls about 42% of the cloud
wood against tlsep's 80%, and height is max-Z over the wood set, so a thinner
set sits lower.

### The finding worth keeping

PointNet++ wins wood IoU by 67% relative and leaf IoU by nearly 3×, and measures
DBH no better and height worse.

**The metric the model is selected on does not predict the measurement the
product makes.** That is worth more than either answer above: it means the
PointNet++ line of work has been optimising a proxy, and the IoU numbers that
have been quoted all along — including in this repository's own evidence — are
not evidence for promotion on their own.

The cost of getting this wrong is concrete. The deployed image was built
deliberately without torch; promoting the candidate puts roughly 530 MB of it
back, for a pipeline that would not measure any better.

`tests/test_backend_promotion_gate.py` pins all of this, and every assertion is
written to fail if the candidate ever *does* improve — the message on each one
says to re-open the question.

## What would actually move the crown

Not a better wood/leaf split, on this evidence. The tracer fails on real crowns
for reasons this experiment did not identify: at 20,000 points per tree, branch
surfaces are too sparse to fit a circle to, and `trace_crown`'s cover sets have
nothing to follow. Candidate next steps, none tested:

- Trace at full resolution instead of the 20,000-point cap, which is where the
  measurement above and the shipped pipeline both operate.
- Compare against TreeQSM proper on the same trees, to separate "this
  implementation is wrong" from "this data cannot support the method".
- Accept the equation and spend the effort on the density instead, which is
  linear in the carbon figure and currently unsourced — see
  `WOOD_DENSITY_PROVENANCE.md`.
