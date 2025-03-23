import pandas as pd

# Load raw data
df = pd.read_csv("ebay_tech_deals.csv", dtype=str)

# Clean price and original_price columns
df["price"] = df["price"].astype(str).str.replace("US $", "").str.replace(",", "").str.strip()
df["original_price"] = df["original_price"].astype(str).str.replace("US $", "").str.replace(",", "").str.strip()

df["price"] = pd.to_numeric(df["price"], errors='coerce')
df["original_price"] = pd.to_numeric(df["original_price"], errors='coerce')

# Replace missing original_price with price
df["original_price"].fillna(df["price"], inplace=True)

# Clean shipping column
df.loc[df["shipping"].isna() | df["shipping"].str.strip().isin(["", "N/A"]), "shipping"] = "Shipping info unavailable"
df["shipping"] = df["shipping"].str.strip()

# Compute discount percentage
df["discount_percentage"] = ((df["original_price"] - df["price"]) / df["original_price"]) * 100
df["discount_percentage"] = df["discount_percentage"].round(2).fillna(0.0)

# Save cleaned data
df.to_csv("cleaned_ebay_deals.csv", index=False)

print("Data cleaning complete. Saved as cleaned_ebay_deals.csv.")