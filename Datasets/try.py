import pandas as pd

# Load the CSV file
df = pd.read_csv("D:\\College_work\\DSP_\\DSP_Tasks\\Datasets\\emg_healthy.csv")

# Drop the first column
df = df.iloc[:, 1:]

# Save the modified DataFrame to a new CSV file
df.to_csv("D:\College_work\DSP_\DSP_Tasks\Datasets\emg_healthy_one_col.csv", index=False)