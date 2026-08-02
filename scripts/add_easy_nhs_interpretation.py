from pathlib import Path

path = Path("README.md")
text = path.read_text(encoding="utf-8")
needle = """The selected `lag_1` baseline marginally outperformed the trailing three-month baseline on the validation period. Provider-level WAPE was available for 289 providers with positive holdout activity: median 13.0128%, 68.5% at or below 20%, and 90.0% at or below 50%. Provider-level results are more volatile for low-volume organisations, so the national aggregate WAPE is the primary headline measure.\n"""
replacement = needle + """
#### Easy interpretation of these results

In simple terms, the benchmark asked: **if next month's MRI activity is estimated mainly from the previous month's activity, how close is that estimate to the actual NHS activity?** Across the national holdout period, the model predicted **821,577 MRI activities** against an actual **840,480**, a difference of **18,903 activities**. This corresponds to a national error of **2.2491%**, or roughly **2 missed activities for every 100 actually delivered**.

The results suggest five practical conclusions:

- **Strong national-level accuracy:** a 2.2491% holdout WAPE means the simple baseline followed overall NHS MRI demand closely during the unseen test period.
- **Recent demand is highly informative:** the previous month's activity (`lag_1`) performed slightly better than averaging the previous three months, indicating that the latest observed month was the most useful short-term signal in this dataset.
- **Useful for planning, not exact scheduling:** the result supports short-term aggregate demand and capacity planning, but it should not be interpreted as an exact forecast for every provider, day or patient pathway.
- **Provider performance varies:** the median provider-level WAPE was 13.0128%. Around 68.5% of scored providers were within 20% error, while low-volume providers showed greater percentage volatility.
- **External evidence strengthens credibility:** the benchmark used official public NHS data across 463 providers rather than only synthetic simulation inputs, showing that the repository can ingest, validate and benchmark against real operational evidence.

**Practical meaning for decision-makers:** at national or large-network level, this baseline can provide a credible near-term reference for MRI demand. Hospitals and local systems should still recalibrate it using their own operational data, capacity constraints, seasonal patterns and service changes before using it for staffing, scanner investment or scheduling decisions.
"""
if needle not in text:
    raise SystemExit("Target benchmark interpretation paragraph not found")
path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")
