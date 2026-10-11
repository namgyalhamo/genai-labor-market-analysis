# India, work, and potential GenAI exposure

This repository accompanies the final insight report, **“India's workforce and potential exposure to generative AI.”** It examines occupational employment patterns in India using the 2018-19, 2021-22, and 2023-24 Periodic Labour Force Survey (PLFS), then links the two most recent waves to an occupation-level potential GenAI-exposure proxy based on Gmyrek et al. (2025).

The research question is descriptive:

> Which parts of India's employed workforce are concentrated in occupations with greater potential exposure to generative AI, and how does this differ by sex, rural or urban sector, and education?

Potential exposure is not a measure of AI adoption, job displacement, or a causal estimate of employment effects.

## Data access and reproducibility

This public repository includes the raw and cleaned GenAI score data used in the analysis:

- `data/raw/Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx` is the original task-level ISCO-08 score workbook from Gmyrek et al. (2025).
- `data/cleaned/genai_scores_isco08_clean.csv` is the cleaned occupation-level lookup created from that workbook.

Respondent-level PLFS microdata are not included in this public GitHub repository because MoSPI provides them through registered access and its data-access agreement does not allow public redistribution. For course review, the raw and cleaned PLFS files are available in a restricted [institutional Google Drive folder](https://drive.google.com/drive/folders/1Ao_-s7wpro-9DcoEiedIZseTnOEV7Xxb?usp=drive_link). Access requires signing in with a CMU institutional account. 

Other users can reproduce the PLFS portion of the project by obtaining the three corresponding PLFS first-visit person files from the [MoSPI Microdata Catalogue](https://microdata.gov.in/NADA/index.php/catalog/PLFS); saving them as `plfs_2018_19_person.csv.gz`, `plfs_2021_22_person.csv.gz`, and `plfs_2023_24_person.csv.gz` in `data/raw/`; opening `data-explore-stage1/explore_plfs.ipynb` in VS Code; selecting a Python kernel with the required packages; and clicking **Run All**. The notebook creates the three cleaned worker-level files in `data/cleaned/`.

## Reproduce the analysis

1. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

2. Obtain the three authorized PLFS first-visit person files and place them in `data/raw/` using the exact filenames described above.

3. Open `data-explore-stage1/explore_plfs.ipynb` in VS Code and click **Run All**. This creates the cleaned PLFS worker files.

4. Run the analysis script from the repository root:

   ```bash
   python scripts/run_analysis.py
   ```

The script creates cleaned GenAI occupation scores, processed aggregate tables, and PNG figures.

## Occupation matching method

The three-year employment trend uses nine broad one-digit occupation groups because 2018-19 uses NCO-2004 while later PLFS waves use NCO-2015. The detailed GenAI analysis uses three-digit NCO-2015 occupation groups for 2021-22 and 2023-24.

NCO-2015 is aligned with ISCO-08 at the first four digits. Because PLFS provides three-digit occupation codes, each three-digit PLFS group receives the unweighted mean of compatible four-digit ISCO-08 occupation scores. This is a transparent occupation-level proxy, not an individual worker score.

## Repository guide

- `data/raw/` - raw Gmyrek et al. GenAI score workbook and the local input location for authorized PLFS files.
- `data/cleaned/` - cleaned GenAI occupation-score lookup; PLFS worker-level files are created locally by the notebook.
- `data/processed/` - reproducible aggregate tables used in the report; these contain no respondent-level PLFS records.
- `data-explore-stage1/explore_plfs.ipynb` - PLFS data cleaning, code-label mapping, and creation of cleaned PLFS worker files.
- `scripts/run_analysis.py` - GenAI score cleaning, weighted aggregation, correlation analysis, and figure generation.
- `figures/` - report-ready PNG charts.
- `data_dictionary.md` - explanation of cleaned and processed variables.

## Sources

- Ministry of Statistics and Programme Implementation, Government of India. *Periodic Labour Force Survey*, 2018-19, 2021-22, and 2023-24 first-visit person files. MoSPI Microdata Catalogue.
- Gmyrek, P., et al. (2025). *Generative AI and jobs: A refined global index of occupational exposure*. ILO Working Paper 140. [Source score repository](https://github.com/pgmyrek/2025_GenAI_scores_ISCO08).
- International Labour Organization. (2012). *International Standard Classification of Occupations: ISCO-08*.
