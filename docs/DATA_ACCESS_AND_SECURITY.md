# Research Data Access, Restrictions, and Secure Handling

**Last reviewed:** October 13, 2026. **Audience:** all users of this public Research-Template.

> **This repository is public. Never commit, attach, upload, or paste identifiable,
> patient-level, controlled-access, confidential, licensed-restricted or other
> sensitive research data.** All included demonstration records are synthetic.
> Reading a published data dictionary does not authorize access to, reuse of,
> redistribution of, or publication from the underlying dataset.
> Git ignore rules are not encryption or access controls.

**Policy precedence:** The source owner's current access policy, approved
data-use agreement (DUA), consent restrictions, IRB or local human-research
review, and institutional security rules supersede this orientation guide.
Stop before importing any file whose access or handling authorization is unclear.

## Classify the source before using it

| Tier | Typical examples | Minimum action |
| --- | --- | --- |
| Public reference documentation | Codebooks, metadata schemas, publications | Cite the source; verify the actual data file's rights separately |
| Public-use research records | Published NHANES, BRFSS, GEO, and open GDC/TCIA collections | Check research-use terms, non-reidentification, attribution and sharing limitations |
| Registration / license | SEER Research Data and certain imaging collections | Complete individual registration and agreements before using data |
| Controlled/restricted research | GDC/dbGaP controlled genomics, SEER Research Plus, NCHS RDC restricted variables, selected TCIA collections, institution-held clinical data | Apply for purpose- and user-specific approval, use an authorized environment, obey disclosure rules |

Open access does **not** necessarily permit re-identification, republishing,
record linkage, or processing by external AI services.

## Official applications and instructions

| Dataset | How to request or verify access | Official entry |
| --- | --- | --- |
| **SEER Research Data** | Register for an account, select Research Data, acknowledge the data-use agreement, and use your issued SEER*Stat login. Individual team users request access separately. | [SEER how to request access](https://seer.cancer.gov/data/access.html) |
| **SEER Research Plus / NCCR / specialized files** | Research Plus generally requires eligible institution-linked eRA Commons or HHS credentials and additional application details; specialized collections require their own request. Do not reuse Research Data authorization for restricted products. | [SEER product distinctions and applications](https://seer.cancer.gov/data/access.html) |
| **NCI GDC controlled genomic data** | Identify the exact controlled dataset. The PI requests institution-linked NIH eRA Commons credentials and project-level authorization through dbGaP. Wait for approval, then use approved GDC access/download methods. Public GDC files do not require the same authorization. | [GDC open/controlled distinctions](https://gdc.cancer.gov/access-data/data-access-processes-and-tools) · [Controlled access steps](https://gdc.cancer.gov/access-data/obtaining-access-controlled-data) |
| **NHANES public-use** | Choose the precise cycle, confirm public-use status, obtain the official documentation/codebooks and apply its analysis/design rules. | [NHANES 2017–2018 data](https://wwwn.cdc.gov/Nchs/Nhanes/continuousnhanes/default.aspx?BeginYear=2017) |
| **NHANES/NCHS restricted-use** | Use the NCHS Research Data Center Standard Application Process. Submit a justified research question, exact variable dictionary, methods, required source files and proposed outputs; wait for approval and required disclosure review. | [NCHS RDC application process](https://www.cdc.gov/rdc/application-process/index.html) |
| **BRFSS** | Download the appropriate annual *public-use* files/codebooks. Verify year-specific survey weights, included jurisdictions and intended population. | [CDC BRFSS annual data](https://www.cdc.gov/brfss/annual_data/annual_2025.html) |
| **NCBI GEO** | Identify GSE/GSM/GPL accession and review series/sample metadata, supplemental file descriptions and source-specific conditions. Public series documentation does not grant controlled-subject access. | [GEO programmatic access](https://www.ncbi.nlm.nih.gov/geo/info/geo_paccess.html) |
| **TCIA imaging** | Review each imaging collection's **Access** and **Citations & Data Usage Policy** sections; some require an account or restricted license. Contact TCIA support with the collection name if access is limited. | [TCIA collections](https://www.cancerimagingarchive.net/collections/) · [usage policies](https://wiki.cancerimagingarchive.net/display/Public/Data+Usage+Policies+and+Restrictions) · [restricted-collection instructions](https://wiki.cancerimagingarchive.net/display/Public/Frequently+Asked+Questions) |

**NIH controlled-data security update:** NIH specifies required security
practices for users of controlled-access data. New or renewed agreements
from **February 25, 2026** follow the updated NIH user security standards.
Review [NIH current requirements](https://www.grants.nih.gov/policy-and-compliance/policy-topics/sharing-policies/accessing-data/requirements)
and the terms of your particular agreement with institutional research IT.

## Application checklist — before any real data enters a workflow

1. **Scope:** Choose the exact dataset release, project/accession, requested
   fields, inclusion criteria, analysis unit and expected outputs. Check if
   a less restricted public-use version answers the question.
2. **Reviewers:** Identify the PI, source custodian, institution's data-use
   contracts office, IRB/human-subjects team and information-security team
   as applicable. Ask for a determination; never presume that access
   approval and ethical research approval are the same.
3. **Request:** Prepare a concise protocol, exact variable list/data
   dictionary, justification, planned analysis and joins, team roster,
   permitted computation and file transfer locations, retention and
   intended tables/figures. Submit using the **source owner's** form.
4. **Approve:** Complete identity verification, any required training,
   signing-official confirmation, DUAs and dataset-specific permissions.
   **Wait for recorded approval before downloading or processing**.
5. **Provision:** Obtain approval for the computing location, credentials,
   storage, backups, encryption, access logs, outbound connections,
   incident response, retention and approved processors.
6. **Receive:** Import only the authorized subset using approved channels.
   Record source/release, acquisition date, local file checksums and
   restrictions in a **private** source register. No raw data, confidential
   logs, download tokens or subject-level paths belong in a public PR.
7. **Validate:** Check types, identifiers, measurement units, missingness,
   eligibility, design weights, duplicate keys and joins in that approved
   environment. Passing schema validation is *not* scientific approval.
8. **Review outputs:** Examine charts, tiny cells, images, free text,
   patient linkage, learned parameters and logs for disclosure risk. Apply
   required disclosure/manual reviews before distribution.

For RDC datasets, the process may include an RDC analyst's review of
analytic output **and manuscripts** before publication:
[CDC restricted-data workflow](https://www.cdc.gov/rdc/application-process/accessing-restricted-data.html).

## Security safeguards

- **Separate the public code from private records.** Run with synthetic
  fixtures publicly. Store actual protected data only on approved
  institution-managed systems and encrypted approved devices or cloud
  workspaces. A GitHub fork, Actions job, public issue or Vercel preview
  is not an automatically approved data environment.
- **Least privilege and MFA.** Grant access by named researcher, role
  and actual need; maintain an authorized user list, multifactor
  authentication as required, timely revocation and access logs.
- **Encrypt data in transit and at rest** with approved infrastructure;
  keep keys/secrets in approved secret management rather than Git,
  notebooks, plaintext configuration, screenshots or CI logs.
- **Record provenance privately:** Dataset version, acquisition record,
  transformations, file hashes, processing environment and generated
  analysis lineage can be documented without revealing sensitive
  subject identifiers in the public repository.
- **No unauthorized sharing:** Do not send controlled genomic files,
  DICOM images, row-level data, free-text clinical notes, trained model
  weights or identifying prompts to an external AI/LLM, hosted notebook,
  plotting site or commercial processor without explicit permission.
- **Review indirect disclosures:** Rare subgroups, small cells, detailed
  geography, linked dates, DICOM metadata and fine-grained plots may
  reveal identities even without direct identifiers.
- **Retention and incident handling:** Follow the data agreement's
  retention, permitted outputs and secure deletion rules. In the event
  of suspected disclosure, stop sharing and contact the organization's
  security/privacy/data-steward incident channel promptly; preserve
  required evidence. Deleting a file in a later commit does **not**
  remove it from earlier public Git history or external clones.

## This repository's intended separation

- **Public repo:** source code, sanitized protocols, generic codebooks,
  literature citations, reproducible synthetic tests and demonstrably
  approved summary artifacts only.
- **Approved secure study environment:** permitted raw and derived
  subject data, restricted source files, provider tokens, sensitive
  logs, regulated model weights and source-specific approvals.
- **Release boundary:** Scientific validity, privacy/disclosure
  clearance, rights to redistribute and any journal publication
  permission are separate human decisions.

The repository root [Git ignore rules](../.gitignore) help avoid accidental
staging of common data-file extensions, raw/derived directories and secrets,
but do **not** replace access controls, encryption or a DUA.

If an access tier or security decision cannot be verified, **use synthetic
data only** until it can.

## Official references

Reviewed October 13, 2026. Recheck current requirements before applying:

- [SEER requests and agreements](https://seer.cancer.gov/data/access.html)
- [GDC controlled-data applications](https://gdc.cancer.gov/access-data/obtaining-access-controlled-data)
- [NCHS RDC proposal process](https://www.cdc.gov/rdc/application-process/index.html)
- [NHANES public-cycle documentation](https://wwwn.cdc.gov/Nchs/Nhanes/continuousnhanes/default.aspx?BeginYear=2017)
- [BRFSS annual use files](https://www.cdc.gov/brfss/annual_data/annual_2025.html)
- [GEO reference access](https://www.ncbi.nlm.nih.gov/geo/info/geo_paccess.html)
- [TCIA licenses and restrictions](https://wiki.cancerimagingarchive.net/display/Public/Data+Usage+Policies+and+Restrictions)
- [NIH controlled-data security standards](https://www.grants.nih.gov/policy-and-compliance/policy-topics/sharing-policies/accessing-data/requirements)
