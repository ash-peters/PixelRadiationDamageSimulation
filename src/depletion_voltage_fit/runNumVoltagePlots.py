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

#filter by section
if args.section:
    df = df[df["histogram"].str.contains(args.section, case=False, na=False)]
    if df.empty:
        raise ValueError(f"No entries found matching '{args.section}' in histogram column")

#plotting info
plt.figure(figsize=(10, 6))

if args.section:
    section_df = df.sort_values("run_number")
    x = np.asarray(section_df["run_number"].values, dtype=float)
    y = np.asarray(section_df["depletion_voltage"].values, dtype=float)
    plt.plot(x, y, marker="o", label=args.section)
else:
    for section, section_df in df.groupby("section"):
        section_df = section_df.sort_values("run_number")
        x = np.asarray(section_df["run_number"].values, dtype=float)
        y = np.asarray(section_df["depletion_voltage"].values, dtype=float)
        plt.plot(x, y, marker="o", label=section)


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
