import pandas as pd

# Load the CSV file
csv_file_path = './bot-service/il-cities-old.csv'  # Update this path to where your CSV file is located

df = pd.read_csv(csv_file_path)

# Select only required columns
df_filtered = df[['city', 'lat', 'lng']]

# Sort by city name
df_sorted = df_filtered.sort_values(by='city')

# Save to a new CSV file
df_sorted.to_csv("./filtered_cities.csv", index=False)

print("Filtered and sorted CSV file saved as 'filtered_cities.csv'")
