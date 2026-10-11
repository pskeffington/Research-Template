# Reusable statistical workflow

Start with the **unit of analysis and design**. Describe counts and missingness first. Select a method only after checking assumptions, repeated observations, weighting and multiplicity.

| Question | R base function | Precondition |
| --- | --- | --- |
| Numeric summary | `summary(x)`, `mean(x, na.rm=TRUE)`, `sd(x, na.rm=TRUE)` | Numeric scale and meaningful missingness policy |
| Categorical counts | `table(group, useNA="ifany")` | Declared coding and reference levels |
| Numeric association | `cor.test(x, y, method="spearman")` | Complete pairs; independent units or justified method |
| Two independent groups | `wilcox.test(value ~ group, data=clean)` | Exactly two independent groups |
| Paired measurements | `wilcox.test(before, after, paired=TRUE)` | Pair by explicit ID, never row position |
| Multiple groups | `kruskal.test(value ~ group, data=clean)` | Independent groups and explicit multiplicity plan |
| Regression | `lm(outcome ~ predictor, data=clean)` | Appropriate design, residuals, confounding and uncertainty |

Call `p.adjust(p_values, method="BH")` when the defined family of hypotheses requires false-discovery control; report effect size, interval and n, not just p. A nonparametric p-value is not a clinically meaningful effect estimate. Complex surveys, multi-level studies, survival and count-based genomics require domain-specific designs rather than these one-line examples. For gene counts, do not substitute Wilcoxon comparisons for a planned negative-binomial differential expression analysis.

For independent synthetic examples and documented plot calls see [R companion](../R/README.md). Never present an exploratory example as a verified clinical result.
