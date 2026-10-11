# Cleaned data

This public folder includes the cleaned GenAI occupation lookup. The cleaned PLFS worker-level files are restricted respondent-level microdata and are **not included in this public repository**. They are available to authorized course users through the restricted course Drive folder.

## Public GenAI lookup

| File | Contents |
|---|---|
| `genai_scores_isco08_clean.csv` | One row per four-digit ISCO-08 occupation, with its occupation title, broad occupation group, mean potential GenAI exposure score, and number of task rows used to create that score. |

## Restricted cleaned PLFS worker files

The following files are created by `data-explore-stage1/explore_plfs.ipynb` after a user obtains the raw PLFS files. They retain people age 15 or older whose usual-principal activity status is an employment code (`11`, `12`, `21`, `31`, `41`, or `51`), have a valid one-digit occupation major group, and have a positive survey weight. The files retain only variables used in the analysis, standardize their names, and add readable group labels.

| File | Survey year | Occupation classification |
|---|---|---|
| `plfs_2018_19_workers_clean.csv.gz` | 2018-19 | NCO-2004 |
| `plfs_2021_22_workers_clean.csv.gz` | 2021-22 | NCO-2015 |
| `plfs_2023_24_workers_clean.csv.gz` | 2023-24 | NCO-2015 |

Each row in a PLFS worker file is a sampled employed person, not a population estimate. Use `survey_weight` for totals or percentages intended to represent India's population. The analysis script uses the separate Gmyrek source workbook to derive GenAI exposure scores; it does not add them to the restricted PLFS worker files. See the repository-level `data_dictionary.md` for all variable definitions.
