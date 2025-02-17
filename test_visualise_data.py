import pandas as pd
import matplotlib.pyplot as plt

# Load CSV file
#df = pd.read_csv("data/hallway/walk/exportfile1.csv").iloc[:, :6]#.iloc[1750:4000, :6]#.iloc[:, :6]
df = pd.read_csv("data/hallway/walk/pyshoe.csv").iloc[1750:4000, :6]#.iloc[:, :6]

# Plot subplots
fig, axes = plt.subplots(6, 1, figsize=(10, 12))
columns = df.columns

for i, col in enumerate(columns):
    axes[i].plot(df.index, df[col], label=col, color='b')
    axes[i].set_title(col)
    axes[i].set_xlabel("Index")
    axes[i].set_ylabel("Value")
    axes[i].grid()

plt.tight_layout()

# Save the figure to a directory
output_path = "test_visualise/plot_pyshoe_walk.png"
#output_path = "test_visualise/plot_exportfile1.png"
plt.savefig(output_path)
