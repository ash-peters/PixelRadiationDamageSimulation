import ROOT
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import chisquare
import argparse

#argparse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-p", "--input_file_path", help="Input the path to the root file", required=True)
parser.add_argument("-g", "--graph_name", help="Input the graph title as seen in the root file", required=True)
parser.add_argument("-c", "--chisquare", default=0.5, type=float, help="Input the chi square threshold to test against", required=False)


#defining chi square calculation
def compute_chisquare(x_vals, y_vals):
    if len(x_vals) < 2:
        return float('inf')  # can't fit line to 1 point

    # Fit a line
    slope, intercept = np.polyfit(x_vals, y_vals, 1)
    expected = slope * np.array(x_vals) + intercept

    # Calculate chi-square (manual definition)
    observed = np.array(y_vals)
    chi2 = np.sum((observed - expected) ** 2 / expected)

    return chi2

if __name__ == "__main__":
    args = parser.parse_args()
    file = ROOT.TFile(args.input_file_path)
    graph = file.Get(args.graph_name)

    best_voltage = 0
    threshold = args.chisquare #chi squared threshold to check against

x_values = []
y_values = []

#get x and y values from graph
for i in range(1, graph.GetNbinsX() + 1):
    x = graph.GetXaxis().GetBinCenter(i)
    y = graph.GetBinContent(i)
    x_values.append(x)
    y_values.append(y)

#filter out where y = 0
x_filtered = [x for x, y in zip(x_values, y_values) if y != 0]
y_filtered = [y for x, y in zip(x_values, y_values) if y != 0]

x_plotting = [x for x, y in zip(x_values, y_values) if y != 0]
y_plotting = [y for x, y in zip(x_values, y_values) if y != 0]

#print(f'original y values: {y_filtered}')

#determine initial left and right side values
left_xvalues = []
left_yvalues = []

for _ in range(3):
    left_xvalues.append(x_filtered.pop(0))
    left_yvalues.append(y_filtered.pop(0))

#print(f'left y values: {left_yvalues}')
#print(f'remaining y values: {y_filtered}')

right_xvalues = []
right_yvalues = []

for _ in range(3):
    right_xvalues.append(x_filtered.pop(-1))
    right_yvalues.append(y_filtered.pop(-1))

#test portion of x and y values until chi squared exceeds threshold
#starting from the left

while x_filtered:
    x = x_filtered[0]
    y = y_filtered[0]

    temp_x = left_xvalues + [x]
    temp_y = left_yvalues + [y]

    chi_square = compute_chisquare(temp_x, temp_y)

    if chi_square < threshold:
        left_xvalues.append(x_filtered.pop(0))
        left_yvalues.append(y_filtered.pop(0))
    else:
        break



#print(f'updated left y values: {left_yvalues}')


#starting from the right

while x_filtered:
    x = x_filtered[-1]
    y = y_filtered[-1]
    
    temp_x = [x] + right_xvalues
    temp_y = [y] + right_yvalues
    
    chi_square = compute_chisquare(temp_x, temp_y)
    
    if chi_square < threshold:
        right_xvalues.insert(0, x_filtered.pop(-1))
        right_yvalues.insert(0, y_filtered.pop(-1))
    else:
        break





#invert right values
right_xvalues.reverse()
right_yvalues.reverse()

print(f'right y values: {right_yvalues}')

#generate plot with best fit lines
#create left side fit
b_left, a_left = np.polyfit(left_xvalues, left_yvalues, deg=1)
xseq_left = np.linspace(min(left_xvalues), max(left_xvalues), num=100)

#print(f'left x and y values: {left_xvalues}, {left_yvalues}')
#print(f'right x and y values: {right_xvalues}, {right_yvalues}')
#print(f'initial x and y values: {x_plotting}, {y_plotting}')

#create right side fit
b_right, a_right = np.polyfit(right_xvalues, right_yvalues, deg=1)
xseq_right = np.linspace(min(right_xvalues), max(right_xvalues), num=100)


#calculate intersection
if b_left != b_right:
    intersection_x = (a_right - a_left) / (b_left - b_right)
    intersection_y = a_left + b_left * intersection_x

    print(f"Intersection at x = {intersection_x:.2f}, y = {intersection_y:.2f} (Depletion Voltage)")

    # Optional: plot the intersection point
    plt.plot(intersection_x, intersection_y, 'ko', label=f"Intersection ({intersection_x:.2f} V)")
    plt.legend()
else:
    print("Lines are parallel; no intersection.")



#generating the plots
plt.plot(x_plotting, y_plotting, 'o')
plt.title("Bias Voltage vs Avg Cluster Charge")
plt.xlabel("Bias Voltage (V)")
plt.ylabel("Avg Cluster Charge")


plt.plot(xseq_left, a_left + b_left * xseq_left, color='red')
plt.plot(xseq_right, a_right + b_right * xseq_right, color='green')


plt.show()



