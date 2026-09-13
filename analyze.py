# analyze.py
#
# Breakdown-risk analysis for Vossberg Mobility fleet (fleet_history.csv, 120 cars).
#
# Key findings:
#   km_since_service is by far the strongest predictor of breakdown (correlation 0.40).
#   Odometer total and age_years are nearly useless — their group means differ by less than 1%.
#   avg_daily_km and load_factor both add signal (0.25 and 0.22), so the risk score uses all three.
#
# What the obvious guess gets wrong:
#   Total mileage (odometer_km) looks like the natural answer — older cars wear out, right?
#   The numbers say no: cars that broke down averaged 53 448 km; cars that did not averaged 53 302 km.
#   The difference is 146 km across 120 cars — noise, not signal.
#   Age (age_years) is even flatter: both groups average almost exactly 5.9 years.
#   The real danger sign is how far past its last service the car is running right now.

import pandas as pd

df = pd.read_csv("fleet_history.csv")

# ── 1. Column-by-column separation ───────────────────────────────────────────
broke = df[df["broke_down"] == 1]
fine  = df[df["broke_down"] == 0]

print("=== Group means: broke down vs. did not ===")
features = ["odometer_km", "km_since_service", "avg_daily_km", "load_factor", "age_years"]
for col in features:
    b_mean = broke[col].mean()
    f_mean = fine[col].mean()
    diff   = b_mean - f_mean
    print(f"  {col:22s}  broke={b_mean:8.1f}  fine={f_mean:8.1f}  diff={diff:+8.1f}")

print()
corr = df[features + ["broke_down"]].corr()["broke_down"].drop("broke_down")
print("=== Correlation with broke_down ===")
for col, val in corr.sort_values(ascending=False).items():
    print(f"  {col:22s}  r={val:.3f}")

# ── 2. Predictive columns ────────────────────────────────────────────────────
# km_since_service, avg_daily_km, and load_factor have meaningful correlations.
# odometer_km and age_years are essentially uncorrelated (|r| < 0.01) — excluded.

# ── 3. Risk score (0–100) ────────────────────────────────────────────────────
# Normalise each predictive column to [0, 1] then take a weighted sum.
# Weights chosen proportional to their correlation coefficients.

def minmax(series: pd.Series) -> pd.Series:
    """Scale a series to the [0, 1] range."""
    lo, hi = series.min(), series.max()
    return (series - lo) / (hi - lo) if hi != lo else pd.Series([0.5] * len(series))

df["norm_km_since"] = minmax(df["km_since_service"])   # weight 0.40
df["norm_daily_km"] = minmax(df["avg_daily_km"])        # weight 0.25
df["norm_load"]     = minmax(df["load_factor"])         # weight 0.22

total_weight = 0.40 + 0.25 + 0.22
df["risk_score"] = (
    0.40 * df["norm_km_since"] +
    0.25 * df["norm_daily_km"] +
    0.22 * df["norm_load"]
) / total_weight * 100

# ── 4. Ranked output ─────────────────────────────────────────────────────────
ranked = (
    df[["car_id", "risk_score", "km_since_service", "avg_daily_km", "load_factor",
        "odometer_km", "age_years", "broke_down"]]
    .sort_values("risk_score", ascending=False)
    .reset_index(drop=True)
)

print()
print("=== Cars ranked by breakdown risk (highest first) ===")
print(f"{'#':>3}  {'car_id':<10}  {'risk':>5}  {'km_since':>9}  {'daily_km':>9}  {'load':>5}  {'broke':>5}")
print("-" * 62)
for i, row in ranked.iterrows():
    flag = " **BROKE**" if row["broke_down"] == 1 else ""
    print(
        f"{i+1:>3}  {row['car_id']:<10}  {row['risk_score']:>5.1f}"
        f"  {row['km_since_service']:>9.0f}  {row['avg_daily_km']:>9.0f}"
        f"  {row['load_factor']:>5.2f}  {int(row['broke_down']):>5}{flag}"
    )

# ── 5. Quick validation: do top-quartile cars break down more often? ─────────
top25  = ranked.head(30)
rest   = ranked.tail(90)
print()
print(f"Breakdown rate — top 25% by risk : {top25['broke_down'].mean():.0%}")
print(f"Breakdown rate — bottom 75%      : {rest['broke_down'].mean():.0%}")
