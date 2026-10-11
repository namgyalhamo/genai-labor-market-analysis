"""Create analysis tables and figures from notebook-cleaned PLFS files.

Run from the repository root with the bundled or a normal Python environment:
    python scripts/run_analysis.py

First run ``data-explore-stage1/explore_plfs.ipynb`` from top to bottom. It
creates the three worker-level files in ``data/cleaned``. This script reads
those cleaned inputs, constructs the GenAI exposure proxy, and writes the
analysis outputs.
"""
from __future__ import annotations

from pathlib import Path
from textwrap import fill

import matplotlib
# The analysis writes PNG files and never needs to open a chart window. Using
# the non-interactive backend makes the script run reliably on any computer.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# --- Project folders and input files ---
# The cleaning notebook creates the three files below. Analysis reads them but
# never edits them, keeping cleaning and analysis as separate stages.
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
CLN = ROOT / "data" / "cleaned"
FIG = ROOT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
CLN.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

CLEANED_FILES = {
    "2018-19": CLN / "plfs_2018_19_workers_clean.csv.gz",
    "2021-22": CLN / "plfs_2021_22_workers_clean.csv.gz",
    "2023-24": CLN / "plfs_2023_24_workers_clean.csv.gz",
}
# Broad occupation groups used for the trend chart. One-digit groups are used
# because 2018–19 uses NCO-2004 while later PLFS years use NCO-2015.
OCC_LABELS = {
    "1": "Managers", "2": "Professionals", "3": "Technicians",
    "4": "Clerical", "5": "Service & sales", "6": "Agriculture",
    "7": "Craft", "8": "Operators", "9": "Elementary",
}
# Distinct colors make the nine broad groups readable in the detailed
# three-digit occupation scatterplot.
OCC_COLORS = {
    "1": "#1b9e77", "2": "#d95f02", "3": "#7570b3",
    "4": "#e7298a", "5": "#66a61e", "6": "#e6ab02",
    "7": "#a6761d", "8": "#666666", "9": "#1f78b4",
}
# Official ISCO-08 minor-group titles for the ten selected groups displayed in
# the exposure chart. The code remains in the label for reproducibility.
ISCO_MINOR_LABELS = {
    "931": "Mining and construction labourers",
    "921": "Agricultural, forestry and fishery labourers",
    "711": "Building frame and related trades workers",
    "912": "Vehicle, window, laundry and other hand cleaning workers",
    "713": "Painters, building structure cleaners and related trades workers",
    "241": "Finance professionals",
    "412": "Secretaries (general)",
    "411": "General office clerks",
    "431": "Numerical and material recording clerks",
    "413": "Keyboard operators",
}


def education_group(series: pd.Series) -> pd.Series:
    """Combine detailed education codes into groups large enough to compare."""
    code = pd.to_numeric(series, errors="coerce")
    below_primary = code.le(5).fillna(False).to_numpy(dtype=bool)
    primary_or_middle = code.isin([6, 7]).fillna(False).to_numpy(dtype=bool)
    secondary_or_above = code.ge(8).fillna(False).to_numpy(dtype=bool)
    return pd.Series(np.select(
        [below_primary, primary_or_middle, secondary_or_above],
        ["Below primary", "Primary or middle", "Secondary or above"],
        default="Missing / not reported",
    ), index=series.index)


def load_workers(year: str) -> pd.DataFrame:
    """Load one notebook-cleaned PLFS file and verify its worker definition.

    A failed validation means the problem belongs in the cleaning notebook,
    rather than being silently fixed during analysis.
    """
    path = CLEANED_FILES[year]
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run data-explore-stage1/explore_plfs.ipynb first."
        )
    raw_columns = {
        "sector_code": "sector", "sex_code": "sex", "education_code": "education",
        "usual_activity_status": "activity", "occupation_nco_code": "occupation",
        "survey_weight": "weight",
    }
    frame = pd.read_csv(
        path,
        dtype={key: "string" for key in raw_columns if key != "survey_weight"},
        low_memory=False,
    ).rename(columns=raw_columns)
    required = set(raw_columns.values()) | {"age"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{path.name} is missing required cleaned columns: {sorted(missing)}")
    frame["activity"] = frame["activity"].str.strip().str.zfill(2)
    frame["occupation"] = frame["occupation"].str.strip().str.zfill(3)
    frame["weight"] = pd.to_numeric(frame["weight"], errors="coerce")
    frame["age"] = pd.to_numeric(frame["age"], errors="coerce")
    expected_workers = (
        frame["activity"].isin(["11", "12", "21", "31", "41", "51"])
        & frame["occupation"].str[0].isin(OCC_LABELS)
        & frame["weight"].gt(0) & frame["age"].ge(15)
    )
    if not expected_workers.all():
        raise ValueError(
            f"{path.name} contains rows outside the documented cleaned-worker population. "
            "Rerun the cleaning notebook instead of filtering in this analysis script."
        )
    frame["year"] = year
    frame["occupation_major"] = frame["occupation"].str[0]
    frame["occupation_label"] = frame["occupation_major"].map(OCC_LABELS)
    frame["sex_label"] = frame["sex"].map({"1": "Men", "2": "Women"}).fillna("Other / missing")
    frame["sector_label"] = frame["sector"].map({"1": "Rural", "2": "Urban"}).fillna("Other / missing")
    frame["education_group"] = education_group(frame["education"])
    return frame


def weighted_shares(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Calculate survey-weighted worker totals and percentage shares."""
    totals = frame.groupby(group_cols, dropna=False, as_index=False)["weight"].sum()
    totals = totals.rename(columns={"weight": "weighted_workers"})
    denom_cols = [c for c in group_cols if c != "occupation_major" and c != "occupation_label"]
    if denom_cols:
        denominator = totals.groupby(denom_cols)["weighted_workers"].transform("sum")
    else:
        denominator = totals["weighted_workers"].sum()
    totals["share_percent"] = totals["weighted_workers"] / denominator * 100
    return totals


# --- Chart helpers using Matplotlib and Seaborn ---
def grouped_bar(data: pd.DataFrame, path: Path, title: str, groups: list[str], series: list[str], colors: list[str], value_col: str = "share_percent") -> None:
    """Create the three-year broad-occupation comparison chart."""
    sns.set_theme(style="whitegrid", context="notebook")
    plot_data = data.copy()
    order = [OCC_LABELS[group] for group in groups]
    plot_data["occupation_label"] = plot_data["occupation_major"].map(OCC_LABELS)
    fig, ax = plt.subplots(figsize=(13, 7))
    sns.barplot(
        data=plot_data,
        x="occupation_label",
        y=value_col,
        hue="year",
        order=order,
        hue_order=series,
        palette=colors,
        ax=ax,
    )
    ax.set_title(title, loc="left", weight="bold", pad=16)
    ax.set_xlabel("")
    ax.set_ylabel("Survey-weighted share of employed people aged 15+ (%)")
    ax.tick_params(axis="x", rotation=30)
    ax.legend(title="Survey year")
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f", padding=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def horizontal_bar(data: pd.DataFrame, path: Path, title: str, value_col: str, subtitle: str) -> None:
    """Create the selected occupation-group exposure comparison chart."""
    sns.set_theme(style="whitegrid", context="notebook")
    plot_data = data.sort_values(value_col).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(11, 7))
    sns.barplot(data=plot_data, y="occupation_label", x=value_col, color="#007c91", ax=ax)
    fig.suptitle(title, x=0.125, y=0.98, ha="left", weight="bold")
    fig.text(0.125, 0.91, fill(subtitle, width=95), ha="left", va="top", color="#536274", fontsize=9)
    ax.set_xlabel("Potential GenAI exposure score")
    ax.set_ylabel("")
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f", padding=3, fontsize=8)
    fig.tight_layout(rect=[0, 0, 1, 0.87])
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def exposure_change_scatter(
    data: pd.DataFrame, path: Path, overall_correlation: float, group_stats: pd.DataFrame
) -> None:
    """Plot the overall fit plus only the three strongest positive group fits.

    Each dot represents one three-digit NCO-2015 occupation group. To avoid a
    crowded chart, dots from groups outside the top three are grey. The black
    dashed line and its correlation use all 127 groups together. None of these
    descriptive fits establish causation.
    """
    sns.set_theme(style="whitegrid", context="notebook")
    # This size is chosen for use both as a standalone PNG and in the PDF:
    # the legend remains readable after the report scales the figure down.
    fig, ax = plt.subplots(figsize=(9, 7.5))

    # Put all detailed groups on the chart first. Groups without a displayed
    # fitted line remain visible in neutral grey.
    ax.scatter(
        data["genai_score"], data["share_change_pp_2021_23"],
        s=42, alpha=0.55, color="#a7b1b7", label="Other broad groups",
    )

    # Show only the three strongest positive within-group correlations. The
    # other six groups are reported in the companion table instead.
    top_groups = group_stats.nlargest(3, "pearson_r")
    for _, stats in top_groups.iterrows():
        major_code = stats["occupation_major"]
        subset = data.loc[data["occupation_major"].eq(major_code)]
        legend_label = f"{stats['occupation_label']} (r={stats['pearson_r']:.2f}, n={int(stats['n_occupation_groups'])})"
        sns.regplot(
            data=subset,
            x="genai_score",
            y="share_change_pp_2021_23",
            ci=None,
            scatter_kws={"s": 48, "alpha": 0.78, "color": OCC_COLORS[major_code]},
            line_kws={"color": OCC_COLORS[major_code], "linewidth": 1.8},
            label=legend_label,
            ax=ax,
        )

    # Add the fitted line for all 127 groups, without plotting a second set
    # of dots. This lets readers compare group-specific slopes with the
    # overall relationship.
    sns.regplot(
        data=data,
        x="genai_score",
        y="share_change_pp_2021_23",
        scatter=False,
        ci=None,
        line_kws={"color": "black", "linewidth": 2.8, "linestyle": "--"},
        label=f"Overall (r={overall_correlation:.2f}, n={len(data)})",
        ax=ax,
    )

    # The dashed zero line separates occupations that gained employment share
    # from those that lost employment share over the two survey years.
    ax.axhline(0, color="black", linewidth=1, linestyle="--")
    ax.set_title(
        "Potential GenAI exposure and employment-share change, by broad occupation",
        loc="left",
        weight="bold",
        pad=16,
    )
    ax.set_xlabel("Potential GenAI exposure score")
    ax.set_ylabel("Change in employment share, 2021–22 to 2023–24\n(percentage points)")

    # Report the same descriptive overall Pearson correlation saved in
    # summary_metrics.csv. The three displayed group correlations appear in
    # the legend; the remaining six are in a separate table.
    ax.text(
        0.02,
        0.98,
        f"Overall Pearson r: {overall_correlation:.2f}\nDetailed occupation groups: {len(data)}",
        transform=ax.transAxes,
        va="top",
        bbox={"facecolor": "white", "edgecolor": "#cccccc", "boxstyle": "round"},
    )
    ax.legend(
        title="Displayed fitted lines",
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=2,
        frameon=True,
        fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def clean_genai_scores() -> pd.DataFrame:
    """Create a four-digit, occupation-level lookup from the raw task workbook.

    The raw Gmyrek et al. workbook has multiple task rows for each four-digit
    ISCO-08 occupation. This function keeps the fields needed here, standardizes
    the code as four text digits, and averages task scores within occupations.
    """
    scores = pd.read_excel(RAW / "Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx")
    required = {"ISCO_08", "Title", "label1d", "score_2025"}
    missing = required - set(scores.columns)
    if missing:
        raise ValueError(f"The GenAI score workbook is missing columns: {sorted(missing)}")
    scores["isco_4digit"] = pd.to_numeric(scores["ISCO_08"], errors="coerce").astype("Int64")
    scores["genai_task_score"] = pd.to_numeric(scores["score_2025"], errors="coerce")
    if scores[["isco_4digit", "genai_task_score"]].isna().any().any():
        raise ValueError("The GenAI score workbook has missing or invalid ISCO codes or 2025 task scores.")
    scores["isco_4digit"] = scores["isco_4digit"].astype(str).str.zfill(4)
    return scores.groupby("isco_4digit", as_index=False).agg(
        occupation_title=("Title", "first"),
        occupation_major_label=("label1d", "first"),
        genai_score=("genai_task_score", "mean"),
        task_rows=("genai_task_score", "size"),
    )


def detailed_exposure_proxy(occupation_scores: pd.DataFrame) -> pd.DataFrame:
    """Map three-digit NCO-2015 groups to mean compatible ISCO-08 task scores.

    NCO-2015 is aligned with ISCO-08 at the first four digits. PLFS records
    only the first three digits, so the score for each PLFS group is the
    unweighted mean of the four-digit ISCO occupations sharing those digits.
    Each detailed occupation is given equal weight, rather than allowing
    occupations with more task rows in the source workbook to dominate.
    """
    occupation_scores["occupation_3digit"] = occupation_scores["isco_4digit"].str[:3]
    exposure = occupation_scores.groupby("occupation_3digit", as_index=False).agg(
        genai_score=("genai_score", "mean"),
        score_sd=("genai_score", "std"),
        detailed_occupations=("isco_4digit", "nunique"),
        source_task_rows=("task_rows", "sum"),
    )
    exposure["occupation_major"] = exposure["occupation_3digit"].str[0]
    exposure["exposure_tercile"] = pd.qcut(
        exposure["genai_score"], 3, labels=["Lower", "Middle", "Higher"]
    )
    return exposure


def main() -> None:
    # 1. Combine the three already-cleaned worker files and measure the
    # employment share of each broad occupation group in each survey year.
    workers = pd.concat([load_workers(year) for year in CLEANED_FILES], ignore_index=True)
    trend = weighted_shares(workers, ["year", "occupation_major", "occupation_label"])
    trend.to_csv(OUT / "employment_shares_by_occupation_year.csv", index=False)

    # 2. Create the occupation-level GenAI exposure proxy from the external
    # task-score workbook. This does not measure actual GenAI use by workers.
    occupation_scores = clean_genai_scores()
    occupation_scores.to_csv(CLN / "genai_scores_isco08_clean.csv", index=False)
    exposure = detailed_exposure_proxy(occupation_scores)
    exposure.to_csv(OUT / "genai_exposure_proxy_by_occupation_3digit.csv", index=False)

    # 3. Attach exposure scores to 2023–24 workers. This uses the detailed
    # three-digit NCO-2015 code, not the one-digit trend grouping.
    latest = workers.loc[workers.year.eq("2023-24")].merge(
        exposure[["occupation_3digit", "genai_score", "exposure_tercile"]],
        left_on="occupation", right_on="occupation_3digit", how="left", validate="many_to_one"
    )
    if latest["genai_score"].isna().any():
        raise ValueError("At least one PLFS occupation has no compatible ISCO-08 score.")
    # 4. Within each demographic category, calculate the weighted percentage
    # of workers in lower-, middle-, and higher-exposure occupation groups.
    comparisons = []
    for variable in ["sex_label", "sector_label", "education_group"]:
        temp = latest.groupby([variable, "exposure_tercile"], observed=False)["weight"].sum().reset_index()
        temp["share_percent"] = temp["weight"] / temp.groupby(variable)["weight"].transform("sum") * 100
        temp["group"] = variable.replace("_label", "").replace("_group", "")
        temp = temp.rename(columns={variable: "category"})
        comparisons.append(temp[["group", "category", "exposure_tercile", "weight", "share_percent"]])
    comparison = pd.concat(comparisons, ignore_index=True)
    comparison.to_csv(OUT / "exposure_distribution_by_demographic_2023_24.csv", index=False)

    # 5. Produce one profile row per three-digit occupation for the latest year.
    latest_occ = latest.groupby(["occupation", "occupation_major"], as_index=False)["weight"].sum()
    latest_occ = latest_occ.rename(columns={"occupation": "occupation_3digit", "weight": "weighted_workers"})
    latest_occ["share_percent"] = latest_occ["weighted_workers"] / latest_occ["weighted_workers"].sum() * 100
    latest_occ = latest_occ.merge(exposure, on=["occupation_3digit", "occupation_major"], how="left", validate="one_to_one")
    latest_occ.to_csv(OUT / "occupation_exposure_profile_2023_24.csv", index=False)

    # 6. Test a descriptive association only for the two NCO-2015 years.
    # Comparing detailed codes with 2018–19 would mix NCO-2004 and NCO-2015.
    detailed_change = workers.loc[workers.year.isin(["2021-22", "2023-24"])].groupby(
        ["year", "occupation"], as_index=False
    )["weight"].sum().rename(columns={"weight": "weighted_workers"})
    detailed_change["share_percent"] = detailed_change["weighted_workers"] / detailed_change.groupby("year")["weighted_workers"].transform("sum") * 100
    change = detailed_change.pivot(index="occupation", columns="year", values="share_percent").reset_index()
    change["share_change_pp_2021_23"] = change["2023-24"] - change["2021-22"]
    corr = change.merge(exposure, left_on="occupation", right_on="occupation_3digit", how="inner", validate="one_to_one")
    r = corr["genai_score"].corr(corr["share_change_pp_2021_23"])
    corr[["occupation_3digit", "occupation_major", "genai_score", "share_change_pp_2021_23"]].to_csv(OUT / "exposure_and_change_correlation.csv", index=False)
    # Calculate an additional descriptive correlation for each of the nine
    # major occupation groups. These are based on the detailed three-digit
    # groups inside each major group, so n differs by group.
    group_correlation = corr.groupby("occupation_major", as_index=False).agg(
        n_occupation_groups=("occupation_3digit", "size"),
    )
    group_correlation["pearson_r"] = group_correlation["occupation_major"].map(
        corr.groupby("occupation_major").apply(
            lambda group: group["genai_score"].corr(group["share_change_pp_2021_23"])
        )
    )
    group_correlation["occupation_label"] = group_correlation["occupation_major"].map(OCC_LABELS)
    group_correlation = group_correlation[[
        "occupation_major", "occupation_label", "n_occupation_groups", "pearson_r"
    ]]
    group_correlation.to_csv(
        OUT / "exposure_and_change_correlation_by_major.csv", index=False
    )
    # A compact companion table for the six groups whose fitted lines are not
    # shown in the simplified scatterplot.
    remaining_group_correlation = group_correlation.loc[
        ~group_correlation["occupation_major"].isin(
            group_correlation.nlargest(3, "pearson_r")["occupation_major"]
        )
    ].sort_values("pearson_r", ascending=False)
    remaining_group_correlation.to_csv(
        OUT / "remaining_group_correlations.csv", index=False
    )
    pd.DataFrame([{
        "metric": "Pearson correlation: GenAI exposure proxy vs. 2021-22 to 2023-24 employment-share change",
        "value": round(float(r), 3), "n_occupation_groups": len(corr),
        "interpretation": "Descriptive correlation across three-digit NCO-2015 occupation groups; not causal inference.",
    }]).to_csv(OUT / "summary_metrics.csv", index=False)

    # 7. Create the report-ready figures from the saved analysis tables.
    grouped_bar(trend, FIG / "occupation_trends.png", "India's employment structure changed only modestly across broad occupations", list(OCC_LABELS), list(CLEANED_FILES), ["#9ab7c5", "#466a85", "#173f5f"])
    chart_data = pd.concat([latest_occ.nsmallest(5, "genai_score"), latest_occ.nlargest(5, "genai_score")]).copy()
    # Use readable ISCO-08 group titles rather than bare codes. These labels
    # describe the compatible ISCO groups used to construct the score proxy.
    chart_data["occupation_label"] = chart_data["occupation_3digit"].map(ISCO_MINOR_LABELS)
    chart_data["occupation_label"] = (
        chart_data["occupation_label"].fillna("Other occupation group")
        + "\n(" + chart_data["occupation_3digit"] + ")"
    )
    horizontal_bar(chart_data, FIG / "genai_exposure_profile.png", "Potential GenAI exposure varies within broad occupation groups", "genai_score", "Mean score across compatible four-digit ISCO-08 occupations; selected lowest and highest three-digit groups")
    exposure_change_scatter(
        corr,
        FIG / "exposure_vs_employment_change.png",
        r,
        group_correlation,
    )
    print(f"Processed {len(workers):,} employed PLFS observations.")


if __name__ == "__main__":
    main()
