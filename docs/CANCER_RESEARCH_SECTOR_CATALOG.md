# Cancer research sector catalog and pre-staged study deployments

**Version:** 2026-10-13 · **Author:** Paul Skeffington · Prepared with OpenAI  
**State:** Independent public-source research alignment; **not** Dartmouth-affiliated,
endorsed, institutional software, human-subjects clearance or a validated clinical
pipeline. This catalog distributes **reference metadata only**.

## Research-sector basis

Dartmouth Cancer Center currently identifies four major NCI-reviewed research
programs on its public website. We use their published scientific themes as
**optional organizational tags** in the generic Research-Template, not as a
requirement that researchers work for Dartmouth.

| Program | Official research areas | Planned packs |
| --- | --- | ---: |
| [Cancer Population Sciences](https://cancer.dartmouth.edu/scientists-researchers/cancer-population-sciences) (CPS) | Epidemiology, rural access, screening, prevention and delivery science | 4 |
| [Cancer Signaling, Genomes, and Networks](https://cancer.dartmouth.edu/scientists-researchers/cancer-signaling-genomes-networks) (SGN) | Molecular pathways, computational genomics, translational cancer biology | 3 |
| [Immunology & Cancer Immunotherapy](https://cancer.dartmouth.edu/scientists-researchers/immunology-cancer-immunotherapy) (ICI) | Immune regulation, tumor microenvironment, immunotherapy translation | 3 |
| [Translational Engineering in Cancer](https://cancer.dartmouth.edu/scientists-researchers/translational-engineering-cancer-tec) (TEC) | Image guidance, radiobiology, radiation monitoring and detection | 4 |

Cross-sector methods — Biomedical Data Science, biostatistics, precision AI, and
health care delivery research — may support any of the four rather than
constituting additional formally named Cancer Center programs. See also
[Dartmouth Biomedical Data Science resources](https://geiselmed.dartmouth.edu/bmds/resources/)
and [Dartmouth Cancer Center research programs](https://cancer.dartmouth.edu/scientists-researchers/research-programs).

## Pre-staged deployables

*Discovery status:* **14/14 PRESTAGED_METADATA_ONLY; 4/14 may now generate
pre-cooked, source-linked draft workspaces; 0/14 oncology adapters or
analyses approved for execution.** No cancer dataset or model has
been fetched, compiled or installed. The separate generic NHANES 2017–2018
component dictionary validator may be useful to investigate certain *risk
factor* questions, but it does not itself establish a cancer cohort or
appropriate population inference.

| ID | Research starting point | Authoritative dictionary | Key prerequisite |
| --- | --- | --- | --- |
| CPS-01 | Registry cancer incidence and rural survivorship | [SEER 2025-submission docs](https://seer.cancer.gov/data-software/documentation/seerstat/nov2025/) | SEER*Stat registration, denominator and rate design |
| CPS-02 | Screening utilization and equity | [BRFSS codebook](https://www.cdc.gov/brfss/annual_data/annual_2023.html) | Survey weights, annual question eligibility |
| CPS-03 | Environmental exposures | [NHANES](https://wwwn.cdc.gov/nchs/nhanes/default.aspx) | Component-cycle eligibility, sub-sample weights |
| CPS-04 | Care disparities and comparative effectiveness | [SEER variable definitions](https://seer.cancer.gov/data-software/documentation/seerstat/nov2025/) | Treatment limitations and confounding |
| SGN-01 | Mutations and biological networks | [GDC dictionary](https://gdc.cancer.gov/about-data/data-dictionary) | Case/sample/aliquot links and controlled-access audit |
| SGN-02 | Tumor transcriptomics and differential expression | [GEO SOFT](https://www.ncbi.nlm.nih.gov/geo/info/soft.html) | Verify raw counts vs normalized intensities |
| SGN-03 | Proteogenomics | [NCI PDC/CPTAC](https://proteomics.cancer.gov/data-portal) | Cross-assay specimen matching and batch effects |
| ICI-01 | Tumor immune expression | [GDC](https://gdc.cancer.gov/about-data/data-dictionary) | Cell composition and unobserved therapy outcomes |
| ICI-02 | Immune single-cell sample metadata | [NCBI GEO](https://www.ncbi.nlm.nih.gov/geo/info/soft.html) | Sample/cell nesting and pseudoreplication prevention |
| ICI-03 | Immunotherapy trial landscape | [ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/api) | Registry entries are **not** patient efficacy data |
| TEC-01 | Cancer CT/MRI imaging | [TCIA collections](https://www.cancerimagingarchive.net/browse-collections/) | DICOM study/series/patient linkage and licenses |
| TEC-02 | Imaging AI benchmarking | [TCIA analyses](https://www.cancerimagingarchive.net/browse-data/) | Patient-level splits and reference standard |
| TEC-03 | Radiotherapy dose/structure QA | [TCIA collection metadata](https://www.cancerimagingarchive.net/browse-collections/) | RTSTRUCT/RTDOSE availability must be checked |
| TEC-04 | Optical/molecular contrast | [Dartmouth TEC research themes](https://cancer.dartmouth.edu/scientists-researchers/translational-engineering-cancer-tec) | No dataset selected: synthetic calibration only |

The full [14-row literature/deployment matrix](../references/DARTMOUTH_CANCER_DEPLOYABLE_LITERATURE_MATRIX_2026-10-13.csv)
includes analysis units, candidate tests, plot families, access gates,
references, and deployment priority. The
[program authority matrix](../references/DARTMOUTH_CANCER_PROGRAM_MATRIX_2026-10-13.csv)
records official program themes. The
[methods bibliography](../references/DARTMOUTH_CANCER_METHODS_MATRIX_2026-10-13.csv)
links methodology and reporting guidance (STROBE, REMARK, DESeq2, limma,
TRIPOD+AI, CLAIM 2024, CONSORT-AI, and GEO metadata specifications).

These references are starting points, not claims that a given method is
appropriate for an arbitrarily selected dataset. For example, DESeq2
requires count data; limma requires its relevant expression preparation
model; CLAIM 2024 addresses AI imaging reporting; STROBE describes
observational study reporting rather than confounding control.

**New:** [Generate one of four cancer research sector starters](SECTOR_STARTER_RECIPES.md) using `research-template sectors recipes` and `research-template sectors scaffold --id ... --out ...`. These prepare blank variable mappings and method/figure review plans; all actual data access, inference and publication remain disabled.

## How a researcher uses the catalog

~~~bash
# From a version of Research-Template containing this catalog:
research-template sectors list
research-template sectors list --program SGN
research-template sectors plan --id SGN-02
research-template sectors plan --id TEC-01

# A *separate*, existing NHANES schema pilot:
research-template pack list
research-template pack plan --id nhanes-2017-2018
# Pack validation requires --confirm-authorized-local-use and approved local storage
~~~

- **Sectors** return reference plans and mandatory gate checklists only.
- **Pack** returns installed actual source-variable contracts. The first pack
  validates three NHANES 2017–2018 CSV file schemas if users provide files.
- **Neither** command chooses a research question, downloads cancer data,
  performs molecular/model fitting, labels a clinical outcome, or
  authorizes manuscript publication.

When a candidate advances from catalog to an executable adapter, pin a
**specific source-dictionary version**, define actual file columns and units,
build synthetic schema fixtures, validate sample-level and outcome-level
identifiers, and independently test the statistical design. Keep those
decisions inside a researcher's own project and retain raw source names.

## Source restrictions that change the analysis

- **SEER:** The Research and Research Plus data products have different
  access rules. SEER data are not simply unrestricted public CSVs.
  [Official access rules](https://seer.cancer.gov/data/access.html).
- **GDC:** Public and controlled genomic files differ; the dictionary is
  public, not a license to access protected molecular or clinical records.
  [GDC model](https://gdc.cancer.gov/about-data/data-dictionary).
- **PDC/CPTAC:** Public proteomics and separately controlled genomic
  components must not be treated as equivalent.
  [NCI proteomic portal](https://proteomics.cancer.gov/data-portal).
- **GEO:** Series/sample/platform metadata are publicly documented, but
  expression values vary by instrument, preprocessing, transformation and
  series. [NCBI SOFT schema](https://www.ncbi.nlm.nih.gov/geo/info/soft.html).
- **TCIA:** DICOM collections differ in modalities, annotations, metadata,
  licensing and protected data. No general-purpose imaging AI adapter
  should assume patient identity, segmentation labels or RTDOSE are present.
  [TCIA collection index](https://www.cancerimagingarchive.net/browse-collections/).
- **ClinicalTrials.gov:** A registered trial record is not evidence that
  treatment effectiveness was established. Review study status and outcomes
  before any inference. [API documentation](https://clinicaltrials.gov/data-api/api).

## Literature-to-code gate progression

| Gate | Requirement | Current |
| --- | --- | --- |
| C0 | Source-backed themes, dated policy/method matrix, permissions noted | **Available: 14 plans** |
| C1 | Pinned versioned dictionary, unit/coding schema and sample fixtures | **NHANES general pilot only** |
| C2 | Private user-data validation and read-only join/eligibility plan | Not yet built for cancer candidates |
| C3 | Statistically appropriate model and uncertainty checks with independent negatives | Not yet built |
| C4 | ggplot2/Plotly/ComplexHeatmap manuscripts with geometry, scale and provenance | Generic plotting library exists; not tested against candidates |
| C5 | Independent scientific, copyright, privacy, institutional and publication approvals | Not granted |

Prioritize **SGN-02, SGN-01, TEC-01, and CPS-01/CPS-03** for early
dictionary engineering because their source specifications and generic
validation requirements can be made explicit. Their order is a suggested
technical work plan, **not** a Dartmouth research priority ranking.

### Important distinction

“Aligned with a publicly described Dartmouth research program” does **not**
mean “Dartmouth-approved,” “clinical-grade,” “licensed to use Dartmouth
data,” “published results reproduced,” or “ready to perform inference.”
The public Research-Template remains usable in other institutions and
specialties: this oncology catalog is **one optional thematic overlay**.
