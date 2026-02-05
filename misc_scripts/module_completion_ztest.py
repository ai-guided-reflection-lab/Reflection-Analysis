"""
Two-Proportion Z-Test for Module Completion Rates
================================================

PURPOSE:
This script compares module completion rates between two independent groups:
- SET-SO (Software Engineering Techniques - Systems Optimization): n=100 students
- SET-IP (Software Engineering Techniques - Information Processing): n=74 students

RESEARCH QUESTION:
Are there statistically significant differences in support module completion rates 
between the two course sections?

STATISTICAL METHOD: Two-Proportion Z-Test
=========================================

WHY USE THIS TEST?
- We have two independent groups (different course sections)
- We're comparing proportions (completion rates) between groups
- Large enough sample sizes for normal approximation (n1=100, n2=74)
- Each observation is binary (completed vs. not completed)

ASSUMPTIONS:
1. Independence: Students in one section don't influence the other section
2. Random sampling: Students represent their respective populations
3. Large sample sizes: Both n1*p1, n1*(1-p1), n2*p2, n2*(1-p2) ≥ 5
4. Binary outcomes: Each student either completed the module or didn't

HOW THE TEST WORKS:
==================

STEP 1: Calculate sample proportions
- p1 = completed_SO / total_SO (completion rate in SET-SO)
- p2 = completed_IP / total_IP (completion rate in SET-IP)

STEP 2: Calculate pooled proportion
- p_pooled = (completed_SO + completed_IP) / (total_SO + total_IP)
- This estimates the overall completion rate if there's no difference between groups

STEP 3: Calculate standard error
- SE = sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
- This measures the expected variability in the difference between proportions

STEP 4: Calculate z-statistic
- z = (p1 - p2) / SE
- This standardizes the difference between proportions

STEP 5: Calculate p-value
- p = 2 * (1 - Φ(|z|)) for two-tailed test
- This gives the probability of observing at least this extreme a difference 
  if there's actually no difference between groups

INTERPRETATION:
===============
- z > 0: SET-SO has higher completion rate than SET-IP
- z < 0: SET-IP has higher completion rate than SET-SO
- |z| > 1.96: Statistically significant difference (p < 0.05)
- p < 0.05: Reject null hypothesis (groups differ significantly)
- p ≥ 0.05: Fail to reject null hypothesis (no significant difference)

PRACTICAL SIGNIFICANCE:
- Even if statistically significant, consider the magnitude of difference
- Small differences might not be educationally meaningful
- Large sample sizes can detect tiny differences that aren't practically important

NULL HYPOTHESIS (H0): p1 = p2 (no difference in completion rates)
ALTERNATIVE HYPOTHESIS (H1): p1 ≠ p2 (completion rates differ)
"""

import pandas as pd
from statsmodels.stats.proportion import proportions_ztest

print("="*60)
print("TWO-PROPORTION Z-TEST: MODULE COMPLETION ANALYSIS")
print("="*60)
print("Comparing completion rates between SET-SO and SET-IP sections")
print()

# Data for SET-SO and SET-IP
# These numbers represent actual completion counts from gradebook data
data = {
    "Module": [
        "Group Work",           # Required activity (for-credit)
        "Python",              # Optional extra credit module
        "Study Strategies",    # Optional extra credit module  
        "GitHub",              # Optional extra credit module
        "Time Management",     # Optional extra credit module
        "MySQL",               # Optional extra credit module
        "FastAPI"              # Optional extra credit module
    ],
    # Number of students who completed each module in SET-SO (n=100)
    "Completed_SO": [84, 59, 48, 42, 36, 33, 28],
    "Total_SO": [100] * 7,  # Total students in SET-SO section
    
    # Number of students who completed each module in SET-IP (n=74)  
    "Completed_IP": [54, 46, 29, 37, 28, 19, 19],
    "Total_IP": [74] * 7    # Total students in SET-IP section
}

# Create DataFrame for analysis
df = pd.DataFrame(data)

# Calculate completion rates for visualization
df["Rate_SO"] = (df["Completed_SO"] / df["Total_SO"] * 100).round(1)
df["Rate_IP"] = (df["Completed_IP"] / df["Total_IP"] * 100).round(1)
df["Rate_Difference"] = (df["Rate_SO"] - df["Rate_IP"]).round(1)

print("DESCRIPTIVE STATISTICS:")
print("=" * 40)
print(f"{'Module':<20} {'SET-SO Rate':<12} {'SET-IP Rate':<12} {'Difference':<12}")
print("-" * 56)
for _, row in df.iterrows():
    print(f"{row['Module']:<20} {row['Rate_SO']:>8.1f}% {row['Rate_IP']:>8.1f}% {row['Rate_Difference']:>+8.1f}%")

print("\nSTATISTICAL TESTING:")
print("=" * 40)

# Perform two-proportion z-test for each module
z_scores = []
p_values = []

for i in range(len(df)):
    # Extract data for this module
    module_name = df.loc[i, "Module"]
    completed_counts = [df.loc[i, "Completed_SO"], df.loc[i, "Completed_IP"]]
    total_students = [df.loc[i, "Total_SO"], df.loc[i, "Total_IP"]]
    
    # Perform two-proportion z-test
    # H0: p_SO = p_IP (no difference in completion rates)
    # H1: p_SO ≠ p_IP (completion rates differ)
    z_stat, p_val = proportions_ztest(completed_counts, total_students)
    
    z_scores.append(z_stat)
    p_values.append(p_val)
    
    # Interpret the result
    significance = "***SIGNIFICANT***" if p_val < 0.05 else "Not significant"
    direction = "SET-SO higher" if z_stat > 0 else "SET-IP higher"
    
    print(f"\n{module_name}:")
    print(f"  z-statistic: {z_stat:>8.3f}")
    print(f"  p-value:     {p_val:>8.6f}")
    print(f"  Result:      {significance}")
    if abs(z_stat) > 0.1:  # Only show direction if there's a meaningful difference
        print(f"  Direction:   {direction}")

# Add statistical results to the DataFrame
df["z_score"] = z_scores
df["p_value"] = p_values
df["Significant (p < 0.05)"] = df["p_value"] < 0.05

print("\nSUMMARY OF RESULTS:")
print("=" * 40)
significant_count = df["Significant (p < 0.05)"].sum()
total_tests = len(df)

print(f"Total modules tested: {total_tests}")
print(f"Statistically significant differences: {significant_count}")
print(f"Non-significant differences: {total_tests - significant_count}")

if significant_count == 0:
    print("\nCONCLUSION:")
    print("No statistically significant differences were found between SET-SO and SET-IP")
    print("completion rates for any of the support modules (all p-values > 0.05).")
    print("This suggests that course section does not significantly impact")
    print("student engagement with optional support materials.")
else:
    print(f"\nCONCLUSION:")
    print(f"Found {significant_count} significant difference(s) out of {total_tests} modules tested.")
    significant_modules = df[df["Significant (p < 0.05)"]]["Module"].tolist()
    print(f"Significant modules: {', '.join(significant_modules)}")

print("\nMETHODOLOGICAL NOTES:")
print("=" * 40)
print("• Two-tailed tests used (testing for any difference, not directional)")
print("• Alpha level: 0.05 (5% chance of Type I error)")
print("• No correction for multiple comparisons applied")
print("• Large sample sizes support normal approximation")
print("• Groups are independent (different course sections)")

# Export detailed results to CSV
output_file = "ssm_module_completion_ztest_results.csv"
df.to_csv(output_file, index=False)

print(f"\nDetailed results exported to: {output_file}")
print("\nFull DataFrame:")
print("=" * 40)
print(df.round(6))  # Show full precision for statistical values 