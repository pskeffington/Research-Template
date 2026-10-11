# Biomedical color, axis and reporting conventions

**Author: Paul Skeffington · Prepared with OpenAI**

Every default figure is designed to be interpretable without the function source: title, study context, observation unit, labeled axes/units, measured n / total n, exclusions, source, evidence limitation and explicit legend/colorbar. The schema rejects missing labels and inferred units.

## Encoding matrix

| Quantity | Default encoding | Guard |
| --- | --- | --- |
| Nominal categories | **Okabe–Ito** palette (blue, vermillion, green, purple, orange, sky blue, black, yellow) | Stable dictionary levels; no more than eight; text or shape redundancy; yellow is low contrast on white |
| Continuous magnitudes | Perceptually uniform **Viridis** | Units stated; monotone lightness, not rainbow |
| Signed deviations from a meaningful midpoint | **RdBu_r**, visually symmetric limits | Explicit numeric `center` mandatory; never automatically treat unscaled expression as z-scores |
| Pearson r | Fixed diverging **−1 to +1** | Pairwise complete n in every cell; undefined correlations colored gray |
| Missing cells | Neutral `#CED4DC` | NA is never zero; total missing count in subtitle/caption |
| Distributions | Histogram bins, sample median, measured n | Bin choice disclosed; boxes show quartiles not CI; violin densities are estimates |
| Group comparisons | Stable colors plus labels/markers and group n | Categories absent in subset keep original color index |
| Tabular descriptors | Mean, **sample SD (n−1)**, median, Q1/Q3, IQR, range | Explicit denominators and exclusion counts; SD null if n<2 |

Color alone is not accessibility. The categorical palette may lose distinctions in grayscale; always accompany categories with labels, positions or shapes. Use figure-type semantics rather than universal colors for every study.

## Full-call export contract

`FigureKit.save(fig, path_without_extension)` generates PNG+PDF by default and `*.figure.json` with SHA-256 of each exported image, plot kind, data labels, source, n and scientific release caveat. Exports are not human scientific approval. For vector work prefer PDF/SVG; the raster defaults to 300 dpi. The optional R `rt_save` exports a single user-chosen file.

The complete synthetic CLI prints nine graph formats and two descriptive statistical summaries:

~~~bash
research-template demo --out artifacts/full_gallery --plots --ml
~~~

See [function-call sheet](FUNCTION_CALL_SHEET.md) for all working calls.

## Methodology references

- [Matplotlib — Choosing colormaps](https://matplotlib.org/stable/users/explain/colors/colormaps.html): sequential vs diverging, perceptual lightness.
- [Seaborn — Choosing color palettes](https://seaborn.pydata.org/tutorial/color_palettes.html): use redundant markers and appropriate luminance.
- [Okabe–Ito — Color Universal Design](https://jfly.uni-koeln.de/color/): categorical color mapping.
- [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html): figures cannot rescue leaked machine-learning validation.
- [TRIPOD+AI reporting](https://doi.org/10.1136/bmj-2023-078378): reporting prediction evidence.

A scientifically polished figure still requires appropriate estimands, statistical models, multiplicity, cohort validation, data rights and review.
