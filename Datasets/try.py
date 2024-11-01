import pandas as pd

# Load the CSV file
df = pd.read_csv("D:\\College_work\\DSP_\\DSP_Tasks\\Datasets\\normal_ecg.csv")

# Drop the first column
df = df.iloc[:, 1:]

# Save the modified DataFrame to a new CSV file
df.to_csv("D:\College_work\DSP_\DSP_Tasks\Datasets\\normal_ecg.csv_one_col.csv", index=False)