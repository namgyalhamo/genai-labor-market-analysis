# Data dictionary

`data/cleaned/` contains cleaned source-level files. The PLFS worker files have one row per sampled person; the GenAI file is an occupation lookup. `data/processed/` contains analysis-ready, weighted aggregates only, with no respondent-level PLFS records.

## Cleaned PLFS worker-level files

`data/cleaned/plfs_*_workers_clean.csv.gz` contains one row per sampled employed person aged 15 or older. The files are created by `data-explore-stage1/explore_plfs.ipynb`. They keep only usual-principal-status workers (codes `11`, `12`, `21`, `31`, `41`, and `51`) with a valid major occupation group and a positive survey weight. The files are held in the restricted course Drive folder, not the public repository.

| Variable | Meaning |
|---|---|
| `year` | PLFS survey wave: `2018-19`, `2021-22`, or `2023-24`. |
| `occupation_classification` | Occupation system used in that wave: NCO-2004 for 2018-19 and NCO-2015 for the later waves. This is why comparisons across all three years use only broad one-digit occupation groups. |
| `state_code`, `state_label` | Official PLFS state/Union Territory code and its readable name. |
| `sector_code`, `sector_label` | Residential sector: `1` / Rural or `2` / Urban. |
| `sex_code`, `sex_label` | PLFS sex code and readable label. The analysis uses the label for sex comparisons. |
| `age` | Respondent age in completed years. Only people aged 15 or older are retained. |
| `education_code`, `education_label` | Official PLFS general-education code and its readable category. The analysis later groups these into below primary (codes 1–5), primary or middle (6–7), and secondary or above (8+). |
| `usual_activity_status`, `activity_label` | Usual-principal activity-status code and label. The retained codes identify self-employed workers (`11`, `12`, `21`), regular salaried/wage workers (`31`), and casual wage workers (`41`, `51`). |
| `industry_nic_code` | NIC industry code for the worker's usual-principal activity. It is retained for possible future industry analysis but is not used in the current report's GenAI matching. |
| `occupation_nco_code` | Detailed NCO occupation code for the worker's usual-principal activity. It is used to create the broad occupation group and, for 2021-22 and 2023-24, to match the three-digit GenAI proxy. |
| `occupation_major_code`, `occupation_major_label` | First digit of the occupation code and its readable broad occupation-group label. |
| `survey_weight` | PLFS person survey weight (the sub-sample multiplier). Summing it estimates the number of people represented by sampled records; weighted totals and percentages use this variable. |

`data/cleaned/genai_scores_isco08_clean.csv` is the cleaned lookup table made from the raw Gmyrek et al. task-score workbook. It has one row per four-digit ISCO-08 occupation, not one row per PLFS respondent.

| File | Variable | Meaning |
|---|---|---|
| `genai_scores_isco08_clean.csv` | `isco_4digit` | Standardized four-digit ISCO-08 occupation code. |
|  | `occupation_title`, `occupation_major_label` | Human-readable occupation title and its one-digit broad group. |
|  | `genai_score` | Mean 2025 potential GenAI exposure score across task rows in that occupation. |
|  | `task_rows` | Number of source task rows averaged to form the occupation score. |

## Processed aggregate output files

| File | Variable | Meaning |
|---|---|---|
| `employment_shares_by_occupation_year.csv` | `year` | PLFS survey year. |
|  | `occupation_major`, `occupation_label` | One-digit broad occupation group. Labels are harmonized to ISCO-style major groups; 2018-19 uses NCO-2004 and later waves use NCO-2015, so this is a broad comparison only. |
|  | `weighted_workers` | Sum of PLFS person weights for employed people aged 15+. |
|  | `share_percent` | Group's percentage of all employed, coded workers in that survey year. |
| `genai_exposure_proxy_by_occupation_3digit.csv` | `occupation_3digit` | Three-digit NCO-2015 / ISCO-08 minor occupation group used for 2021-22 and 2023-24 matching. |
|  | `genai_score` | Mean 2025 score across compatible four-digit ISCO-08 occupations. Each four-digit occupation is first given its mean task score, then each is weighted equally in the three-digit average. This is a potential-exposure proxy on a 0-1 scale. |
|  | `score_sd` | Standard deviation of four-digit occupation scores within the three-digit group. |
|  | `detailed_occupations`, `source_task_rows` | Number of four-digit occupations and source task rows contributing to the proxy. |
|  | `exposure_tercile` | Tercile of the 127 three-digit proxy scores: Lower, Middle, or Higher. |
| `occupation_exposure_profile_2023_24.csv` | `occupation_3digit`, `occupation_major` | Detailed matched occupation group and its one-digit major group. |
|  | `weighted_workers`, `share_percent` | 2023-24 estimated worker total and share of all employed, coded workers. |
|  | `genai_score`, `score_sd`, `detailed_occupations`, `source_task_rows`, `exposure_tercile` | Merged three-digit exposure-proxy fields described above. |
| `exposure_distribution_by_demographic_2023_24.csv` | `group` | PLFS characteristic used for comparison: sex, sector, or education. |
|  | `category` | Label within that characteristic. Rural/urban comes from PLFS sector; education is harmonized as below primary (codes 1-5), primary or middle (6-7), and secondary or above (8+). |
|  | `exposure_tercile` | Occupation-based potential-exposure tercile. |
|  | `weight`, `share_percent` | Weighted worker total and within-category percentage. |
| `exposure_and_change_correlation.csv` | `share_change_pp_2021_23` | Percentage-point change in employment share from 2021-22 to 2023-24 for a three-digit group. |
|  | `occupation_3digit`, `occupation_major`, `genai_score` | Three-digit detailed occupation, its broad occupation group, and its potential GenAI exposure score; these are the x-axis inputs for the scatterplot. |
| `exposure_and_change_correlation_by_major.csv` | `occupation_major`, `occupation_label` | One-digit broad occupation group used to colour and fit the grouped scatterplot. |
|  | `n_occupation_groups`, `pearson_r` | Number of detailed three-digit groups in that broad group and its descriptive Pearson correlation between potential GenAI exposure and employment-share change. |
| `remaining_group_correlations.csv` | `occupation_major`, `occupation_label`, `n_occupation_groups`, `pearson_r` | The six broad groups not shown with individual fitted lines in the simplified scatterplot, with their descriptive correlations and sample sizes. |
| `summary_metrics.csv` | `metric`, `value`, `n_occupation_groups`, `interpretation` | Name, value, number of matched groups, and plain-language interpretation of the overall Pearson correlation across the 127 three-digit occupation groups. It is descriptive only, not a causal estimate. |
