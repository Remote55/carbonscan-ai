# Independent PointNet Evidence Report

Verdict: `FAIL_METRICS`
Promote: `false`
Checkpoint SHA-256: `9a21f8ee167d7511a55e5b2c835fab5b6d3ac95b0027340900982eff68a675f1`

## Baseline

- External segmentation macro: `{"accuracy":0.4722710513680526,"leaf_iou":0.39384645177433714,"mean_iou":0.2948622237299912,"wood_iou":0.1958779956856453}`
- External segmentation pooled: `{"accuracy":0.465427110199006,"confusion":{"leaf_as_leaf":1705265,"leaf_as_wood":2461311,"wood_as_leaf":180769,"wood_as_wood":595068},"leaf_iou":0.3922543529441533,"mean_iou":0.28803956354860205,"wood_iou":0.18382477415305076}`
- Macro Wood IoU: `0.1958779956856453`
- DBH MAE (cm): `1.1339476465903928`
- Height MAE (m): `0.5433234000000015`
- Volume MAPE (%): `18.928262273343613`
- Measurable trees: `65`

## Candidate

- External segmentation macro: `{"accuracy":0.8018531951466719,"leaf_iou":0.788133971019304,"mean_iou":0.5127106180471609,"wood_iou":0.23728726507501768}`
- External segmentation pooled: `{"accuracy":0.8058357324650934,"confusion":{"leaf_as_leaf":3698498,"leaf_as_wood":468078,"wood_as_leaf":491562,"wood_as_wood":284275},"leaf_iou":0.7939863524867662,"mean_iou":0.5112594243391131,"wood_iou":0.22853249619146002}`
- Macro Wood IoU: `0.23728726507501768`
- DBH MAE (cm): `1.1591405814498605`
- Height MAE (m): `0.9508502244897976`
- Volume MAPE (%): `21.74924193798788`
- Measurable trees: `49`

## Paired uncertainty

- Paired deltas: `{"dbh_abs_error_delta":{"estimate":0.03413998317115112,"name":"DBH absolute-error candidate-minus-baseline","unit":"cm"},"height_abs_error_delta":{"estimate":0.4087914285714283,"name":"Height absolute-error candidate-minus-baseline","unit":"m"},"volume_ape_delta":{"estimate":3.4630320709342732,"name":"Volume APE candidate-minus-baseline","unit":"percent"},"wood_iou_delta":{"estimate":0.041409269389372436,"name":"Wood IoU candidate-minus-baseline","unit":"proportion"}}`
- Confidence intervals: `{"dbh_abs_error_delta":{"estimate":0.03413998317115112,"lower":-0.6826728936304942,"upper":0.5311570882957047},"height_abs_error_delta":{"estimate":0.4087914285714283,"lower":0.14933392857142722,"upper":0.7471825918367331},"volume_ape_delta":{"estimate":3.4630320709342732,"lower":-0.24560393615757425,"upper":6.7235818992751195},"wood_iou_delta":{"estimate":0.041409269389372436,"lower":-0.043984823986107494,"upper":0.12596225793244115}}`

- Wood IoU candidate-minus-baseline: estimate `0.041409269389372436`; 95% CI [`-0.043984823986107494`, `0.12596225793244115`] proportion
- DBH absolute-error candidate-minus-baseline: estimate `0.03413998317115112`; 95% CI [`-0.6826728936304942`, `0.5311570882957047`] cm
- Height absolute-error candidate-minus-baseline: estimate `0.4087914285714283`; 95% CI [`0.14933392857142722`, `0.7471825918367331`] m
- Volume APE candidate-minus-baseline: estimate `3.4630320709342732`; 95% CI [`-0.24560393615757425`, `6.7235818992751195`] percent

## Limitations

- Cohort A contains only 10 individual non-Thai TLS trees, so confidence intervals may be wide.
- Wan development data is not an independent final test.
- Demol is a locked reused benchmark, not a newly blind cohort.
- Downstream evidence validates only DBH, height, and taper-volume measurements.
- This evaluation does not validate species classification, allometric carbon, carbon credits, or deployment.
- This result does not automatically change the production default.
