# Study Packs: source-qualified, opt-in dataset dictionaries

A Study Pack connects **published source metadata** to the generic research
tools. It is a versioned JSON dictionary, **not** a package of observations,
a scientific model, a ready-made manuscript, or authorization to access data.

## First pilot: NHANES 2017–2018

The source-qualified pilot covers three CDC NCHS files: demographics
(DEMO_J), urine albumin and creatinine (ALB_CR_J), and the kidney
questionnaire (KIQ_U_J). All three use SEQN as their respondent identifier.

~~~bash
research-template pack list
research-template pack describe --id nhanes-2017-2018
research-template pack plan --id nhanes-2017-2018
research-template pack validate --id nhanes-2017-2018 \
  --table DEMO_J --csv /approved/local/path/DEMO_J.csv
~~~

Run the validator separately for ALB_CR_J.csv and KIQ_U_J.csv. It
intentionally accepts **CSV files only** for this initial pilot and checks
an exact cycle-specific filename. Obtain source data legally and convert
SAS XPT or other supplied formats to CSV in your approved local environment.
Do not silently recode columns, truncate identifiers, or erase original
value labels. The pack **does not download data**.

The validator streams the CSV without producing any derived participant
records. It checks header names, required fields, types, coded categories,
respondent-key uniqueness and missing values. It reports aggregate
missingness and special nonresponse codes (e.g. KIQ022 7=Refused and
9=Don't know) without displaying raw responses. Structural success is
reported as STRUCTURE_PASS_ANALYSIS_REVIEW_REQUIRED. It is **not**
scientific, demographic, privacy, or survey-design approval.

The pack ships with official documentation links:

- [NHANES 2017–2018 demographics, survey design and weights](https://wwwn.cdc.gov/nchs/data/nhanes/public/2017/datafiles/DEMO_J.htm)
- [Urine albumin/creatinine and detection limits](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/ALB_CR_J.htm)
- [Kidney conditions questionnaire, age eligibility and weighting](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/KIQ_U_J.htm)

The source pages identify which questionnaire portions use interview or
examination weights. **Do not perform unweighted population inference** or
blindly use a single weight for all variables. Review respondent eligibility,
sample subsampling, zero weights, masked variance units SDMVPSU/SDMVSTRA
and multi-cycle guidance. The pack provides a *plan* for left joins on SEQN
but does not merge any actual files, select an analytic sample or fit tests.

## Generic workflow for additional studies

Each additional Study Pack should provide its own JSON dictionary in
src/research_template/packs/ containing:

1. Stable dataset identifier, source cycle/version, authoritative source URL,
   access restrictions, documentation revision and intended study scope.
2. One or more tables with their original variable names, data types,
   units, categories, special missing/nonresponse codes and join-key rules.
3. Eligibility, missingness, measurement timing, survey or longitudinal
   structure, and explicit unit-of-analysis contracts.
4. Derived-variable formulas with documented source equations and independent
   tests; **none may be calculated merely by loading a pack**.
5. A machine-readable join and analysis plan listing assumptions, required
   review decisions, missing variables and any weighting or clustering rules.
6. Synthetic-only positive and negative tests for the dictionary and CLI.
   No private real records, credentials, or source-distribution rights.
7. Dated source provenance and human approval gates for any real analysis.

### Candidate collections

| Collection | Official metadata | Status |
| --- | --- | --- |
| NHANES 2017–2018 | CDC component dictionaries | **Working validation pilot** |
| BRFSS | CDC annual codebooks and complex sample design | Discovery only; no executable pack yet |
| OMOP Common Data Model | OHDSI CDM field and vocabulary specifications | Discovery only; site-specific ETL and vocabularies needed |
| NCI Genomic Data Commons | GDC entity dictionary and JSON schemas | Discovery only; data and access restrictions vary |

Sources for the discovery-only candidates:
[BRFSS data and codebooks](https://www.cdc.gov/brfss/annual_data/annual_2023.html),
[OMOP CDM v5.4](https://ohdsi.github.io/CommonDataModel/cdm54.html),
and [GDC Data Dictionary](https://gdc.cancer.gov/about-data/data-dictionary).
**No claim is made that these candidates are implemented or validated.**

A pack is just a source-based contract. For a researcher's custom study,
we should support a user-authored pack with the same schema rather than
forcing their variables into an unrelated published codebook.

## Planned gates

- **P1 (this PR):** source-based registry, NHANES dictionary, safe CSV validation,
  explicit plan, synthetic regression tests.
- **P2:** safe multi-file binding, cardinality checks and optional XPT import,
  with file fingerprints and no silent row filtering.
- **P3:** study-specific variable mapping wizard, unit conversion provenance,
  fully reviewed joins, missingness and censoring plans.
- **P4:** design-aware execution adapters (e.g. R survey), appropriate tests and
  figures with uncertainty and clear denominators.
- **P5:** signed human review, journal derivatives and reproducible submission
  evidence, separate from data access and file-import success.

The template remains public and study-agnostic. Data for actual
research projects belongs in approved storage; Git ignore rules are not
access controls.

## Cancer-sector research discovery catalog

The optional [Cancer Research Sector Catalog](CANCER_RESEARCH_SECTOR_CATALOG.md) lists 14 source-qualified deployment *candidates* grouped by four publicly documented Dartmouth Cancer Center research themes. View them with `research-template sectors list`, choose one with `sectors plan --id ...`, then obtain and validate the specific source dictionary in a separate approved project. All entries are metadata-only plans. They never download data, assume journal approval, or execute statistical models. The sector matrix is an independent public-source index, not a Dartmouth collaboration or study-specific dataset.
