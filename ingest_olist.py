import requests
import pandas as pd
import os
import io

BASE_URL = "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets"

DATASETS = {
    "olist_customers": f"{BASE_URL}/olist_customers_dataset.csv",
    "olist_geolocation": f"{BASE_URL}/olist_geolocation_dataset.csv",
    "olist_order_items": f"{BASE_URL}/olist_order_items_dataset.csv",
    "olist_order_payments": f"{BASE_URL}/olist_order_payments_dataset.csv",
    "olist_order_reviews": f"{BASE_URL}/olist_order_reviews_dataset.csv",
    "olist_orders": f"{BASE_URL}/olist_orders_dataset.csv",
    "olist_products": f"{BASE_URL}/olist_products_dataset.csv",
    "olist_sellers": f"{BASE_URL}/olist_sellers_dataset.csv",
    "product_category_name_translation": f"{BASE_URL}/product_category_name_translation.csv"
}

def download_and_save_olist_datasets(output_dir="data/olist"):
    os.makedirs(output_dir, exist_ok=True)
    print(f"Ingesting Olist Brazilian E-Commerce datasets into Parquet format at '{output_dir}' ...")
    
    for name, url in DATASETS.items():
        print(f"Downloading {name} from {url} ...")
        try:
            # Download file into memory
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Read CSV directly from memory
            df = pd.read_csv(io.StringIO(response.text))
            
            # Save to Parquet
            parquet_path = os.path.join(output_dir, f"{name}.parquet")
            df.to_parquet(parquet_path, index=False)
            print(f"  -> Successfully saved {len(df)} records to {parquet_path}")
            
        except Exception as e:
            print(f"Error ingesting {name}: {e}")
            raise e

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ingest Olist E-Commerce CSV files into Parquet.")
    parser.add_argument("--output-dir", type=str, default="data/olist", help="Output directory for Parquet files.")
    args = parser.parse_args()
    
    download_and_save_olist_datasets(args.output_dir)
    print("Olist ingestion completed successfully!")

if __name__ == "__main__":
    main()
