# Raw data

This folder includes the public GenAI score workbook. The restricted PLFS respondent-level microdata files are **not included in this public repository**. Authorized course users can access them through the restricted course Drive folder or obtain them from the MoSPI PLFS catalogue, then save them locally using the filenames below.

| File | Contents | Original source |
|---|---|---|
| `plfs_2018_19_person.csv.gz` | First-visit person-level PLFS CSV, compressed without changing its contents | [MOSPI PLFS catalogue](https://microdata.gov.in/NADA/index.php/catalog/PLFS) |
| `plfs_2021_22_person.csv.gz` | First-visit person-level PLFS CSV, compressed without changing its contents | [MOSPI PLFS catalogue](https://microdata.gov.in/NADA/index.php/catalog/PLFS) |
| `plfs_2023_24_person.csv.gz` | First-visit person-level PLFS CSV, compressed without changing its contents | [MOSPI PLFS catalogue](https://microdata.gov.in/NADA/index.php/catalog/PLFS) |
| `Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx` | Task-level GenAI scores for ISCO-08 occupations | Gmyrek et al. (2025) |

The PLFS files are expected locally when running the cleaning notebook, but are excluded from GitHub because they are restricted respondent-level microdata. The public GenAI workbook is included in this folder. A `.csv.gz` file is a standard compressed CSV that pandas reads automatically.

To use PLFS files stored elsewhere, override the defaults:

```sh
PLFS_2018=/path/to/PerV1_2018-19.csv \
PLFS_2021=/path/to/perv1.csv \
PLFS_2023=/path/to/perv1.csv \
python scripts/run_analysis.py
```
