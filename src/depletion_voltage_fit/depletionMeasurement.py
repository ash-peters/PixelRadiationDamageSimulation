import ROOT
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import chisquare
import argparse
import os
import re
import csv

#argparse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-p", "--input_file_path", nargs="+", help="Input the path to the root file", required=True)
parser.add_argument("-d", "--directory", help="Input the directory path to the graphs in the root file", required=False)
parser.add_argument("-c", "--chisquare", default=0.5, type=float, help="Input the chi square threshold to test against", required=False)

args = parser.parse_args()

#extract run number from input file path
for file_path in args.input_file_path:
    basename = os.path.basename(file_path)
    match = re.search(r'Ntuple_(\d+)_\d+\.root', basename)
    run_number = match.group(1)

#initialize csv file
output_dir = "csvOutputs"
output_file = os.path.join(output_dir, f"depletion_results_run{run_number}.csv")
with open(output_file, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["run_number", "section", "histogram", "depletion_voltage"])

#define compute chisquared
def compute_chisquare(x_vals, y_vals):
    if len(x_vals) < 3:
        return float('inf')
    x_vals = np.asarray(x_vals, dtype=float)
    y_vals = np.asarray(y_vals, dtype=float)
    slope, intercept = np.polyfit(x_vals, y_vals, 1)
    expected = slope * x_vals + intercept
    chi2 = np.sum((y_vals - expected) ** 2)
    dof = len(x_vals) - 2
    return float('inf') if dof <= 0 else chi2 / dof


threshold = args.chisquare
for file_path in args.input_file_path:
    #store each branch in root file
    directories = []
    file = ROOT.TFile(file_path)
    
    if args.directory:
        directories.append(file.Get(args.directory))
    else:
        #get all directories at top level
        for key in file.GetListOfKeys():
            obj = key.ReadObj()
            if obj.InheritsFrom("TDirectoryFile"):
                directories.append(obj)

    #start of calculation
    for directory in directories:
        section_name = directory.GetName()
        print(f"[INFO] Processing section: {section_name}")
    
        for key in directory.GetListOfKeys():
            hist = key.ReadObj()
            if not hist.InheritsFrom("TH1D"):
                continue

            hist_name = hist.GetName()
            prefixes = ["AvgCluCharge_vs_BiasVoltage_", "AvgCluSize_vs_BiasVoltage_"]
            for prefix in prefixes:
                if hist_name.startswith(prefix):
                    hist_name = hist_name[len(prefix):]
                    break
            short_hist_name = hist_name

    
            #extract x/y values
            x_values = np.array([hist.GetXaxis().GetBinCenter(i) for i in range(1, hist.GetNbinsX() + 1)], dtype=float)
            y_values = np.array([hist.GetBinContent(i) for i in range(1, hist.GetNbinsX() + 1)], dtype=float)
    
            #filter out zeros
            x_filtered = [x for x, y in zip(x_values, y_values) if y != 0]
            y_filtered = [y for x, y in zip(x_values, y_values) if y != 0]
    
            if len(x_filtered) < 3:
                print(f"[WARN] {hist.GetName()} has too few valid bins.")
                intersection_y = -1
            else:
                x_filtered = np.asarray(x_filtered, dtype=float)
                y_filtered = np.asarray(y_filtered, dtype=float)
                slope, intercept = np.polyfit(x_filtered, y_filtered, 1)
                y_fit = [slope * x + intercept for x in x_filtered]
                residuals = [abs(y - yf) for y, yf in zip(y_filtered, y_fit)]
                avg_residual = sum(residuals) / len(residuals)
    
                if avg_residual < 0.05 * max(y_filtered):
                    print(f"[INFO] {hist.GetName()} too linear: likely no plateau.")
                    intersection_y = -1
                else:
                    #find intersection
                    right_x, right_y = [x_filtered[-2], x_filtered[-1]], [y_filtered[-2], y_filtered[-1]]
                    left_x, left_y = [x_filtered[0], x_filtered[1]], [y_filtered[0], y_filtered[1]]
    
                    #extend right side until chi2 threshold fails
                    for i in range(len(x_filtered) - 3, -1, -1):
                        chi = compute_chisquare([x_filtered[i]] + right_x, [y_filtered[i]] + right_y)
                        if chi < threshold:
                            right_x.insert(0, x_filtered[i])
                            right_y.insert(0, y_filtered[i])
                        else:
                            break
    
                    #extend left side until chi2 threshold fails
                    for i in range(2, len(x_filtered)):
                        chi = compute_chisquare(left_x + [x_filtered[i]], left_y + [y_filtered[i]])
                        if chi < threshold:
                            left_x.append(x_filtered[i])
                            left_y.append(y_filtered[i])
                        else:
                            break
    
                    #fit both sides
                    left_x = np.asarray(left_x, dtype=float)
                    left_y = np.asarray(left_y, dtype=float)
                    right_x = np.asarray(right_x, dtype=float)
                    right_y = np.asarray(right_y, dtype=float)
    
                    b_left, a_left = np.polyfit(left_x, left_y, 1)
                    b_right, a_right = np.polyfit(right_x, right_y, 1)
    
                    if b_left != b_right:
                        intersection_x = (a_right - a_left) / (b_left - b_right)
                        intersection_y = a_left + b_left * intersection_x
                        print(f"[RESULT] {hist.GetName()}: intersection_y = {intersection_y:.2f} V")
                    else:
                        intersection_y = -1
    
            #write to CSV
            with open(output_file, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([run_number, section_name, short_hist_name, intersection_y])

print(f"[INFO] Results saved to {output_file}")
