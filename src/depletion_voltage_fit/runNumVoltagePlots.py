import pandas as pd
import matplotlib.pyplot as plt
import argparse
import glob
import os
import numpy as np

#setup arguments
parser = argparse.ArgumentParser(
    description="Plot depletion voltage vs. run number for each tracker section."
)
parser.add_argument(
    "-i", "--input_pattern",
    default="csvOutputs/depletion_results_run*.csv",
    help="Glob pattern for input CSVs (default: depletion_results_run*.csv)"
)
parser.add_argument(
    "-s", "--section", required=False,
    help="Filter to plot only this tracker section (e.g. BPix, FPix, Layer1, etc.)"
)
parser.add_argument(
    "-o", "--output_file",
    default="depletion_voltage_vs_run.png",
    help="Output plot filename"
)
parser.add_argument(
    "--show", action="store_true",
    help="Show the plot interactively"
)
args = parser.parse_args()

#combine all csv files
files = sorted(glob.glob(args.input_pattern))
if not files:
    raise FileNotFoundError(f"No CSV files found matching pattern: {args.input_pattern}")

dfs = []
for f in files:
    df = pd.read_csv(f)
    dfs.append(df)

combined_df = pd.concat(dfs, ignore_index=True)
combined_df = combined_df[combined_df["depletion_voltage"] > 0]

#filter by section
if args.section:
    combined_df = combined_df[combined_df["histogram"].str.strip() == args.section.strip()]
    if combined_df.empty:
        raise ValueError(f"No entries found matching '{args.section}' in histogram column")

combined_df["layer"] = combined_df["histogram"].str.extract(r"(Lay\d)")
combined_df["measurement"] = combined_df["section"].apply(
    lambda x: "Charge" if "Charge" in x else ("Size" if "Size" in x else "Unknown")
)

#plotting info
plt.figure(figsize=(10, 6))

for (layer, measurement), group_df in combined_df.groupby(["layer", "measurement"]):
    group_df = group_df.sort_values("run_number")
    plt.plot(
        group_df["run_number"],
        group_df["depletion_voltage"],
        marker="o",
        label=f"{layer} ({measurement})"
    )

plt.xlabel("Run Number")
plt.ylabel("Depletion Voltage (V)")
plt.title("Depletion Voltage vs. Run Number by Tracker Section")
plt.legend(title="Section", bbox_to_anchor=(1.05, 1), loc="upper left")
plt.grid(True)
plt.tight_layout()

plt.savefig(args.output_file)
print(f"[INFO] Plot saved to {args.output_file}")

if args.show:
    plt.show()
