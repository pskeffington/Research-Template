# Scientific visualization standard

Choose the encoding to fit the variable and the scientific question, not aesthetics:

| Measurement | Encoding | Default | Required interpretation |
| --- | --- | --- | --- |
| Unordered categories | Color + text / shape | Okabe–Ito (up to 8 distinct groups) | Stable mapping, legend, per-group n |
| Continuous magnitude | Sequential scale | Viridis | Units and range on colorbar |
| Signed deviations | Diverging with meaningful zero | RdBu_r, midpoint 0 | State whether values are raw, differences or z-scores |
| Missingness | Explicit omission + count | Neutral legend/caption | Missing is never zero |
| Prediction performance | Confusion matrix / ROC / calibration | Defined denominators | Discrimination is not calibration or clinical utility |

Every shared figure must state title, cohort / observation unit, x/y labels and units (including `unitless`), sample sizes after exclusions, transformation scale, legend/colorbar, uncertainty display definition where relevant, source/analysis revision, and a caption that does not imply causal or clinical conclusions unsupported by design.

Figures are generated on request; no automatic external publishing. Favor SVG/PDF for vector artwork and 300-dpi PNG where raster required. Do not infer a confidence interval from boxplot whiskers. PCA separation is exploratory. Heatmap colors are not p-values. If more than eight categorical groups occur, use faceting or alternative encodings.

The Python helper returns a Matplotlib Figure so the operator can add publication-specific text and panels before calling `save_figure`. Follow an independent figure review for labels and numerical alignment.
