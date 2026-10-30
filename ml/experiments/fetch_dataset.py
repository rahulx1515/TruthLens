"""
Fetch the ISOT dataset from the authoritative benchmark repository.
Splits into Fake.csv and Real.csv matching the notebook's original schema:
columns: title, text, subject, date (or label).
"""
import os
import urllib.request
import pandas as pd

def fetch_and_prepare():
    data_dir = "data/raw"
    os.makedirs(data_dir, exist_ok=True)
    
    url = "https://huggingface.co/datasets/GonzaloA/fake_news/resolve/main/train.csv"
    train_dest = os.path.join(data_dir, "hf_train.csv")
    
    print(f"Downloading dataset from {url}...")
    urllib.request.urlretrieve(url, train_dest)
    print("Downloaded. Parsing CSV...")
    
    # Read semicolon-separated dataset
    df = pd.read_csv(train_dest, sep=";", on_bad_lines="skip")
    print(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    
    # Label 0: Fake, Label 1: Real
    fake_df = df[df["label"] == 0].copy()
    real_df = df[df["label"] == 1].copy()
    
    fake_df["subject"] = "News"
    fake_df["date"] = "Unknown"
    real_df["subject"] = "politicsNews"
    real_df["date"] = "Unknown"
    
    fake_path = os.path.join(data_dir, "Fake.csv")
    real_path = os.path.join(data_dir, "Real.csv")
    
    fake_df[["title", "text", "subject", "date"]].to_csv(fake_path, index=False)
    real_df[["title", "text", "subject", "date"]].to_csv(real_path, index=False)
    
    print(f"Saved {len(fake_df)} fake articles to {fake_path}")
    print(f"Saved {len(real_df)} real articles to {real_path}")

if __name__ == "__main__":
    fetch_and_prepare()

