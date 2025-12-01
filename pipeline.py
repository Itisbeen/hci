import pandas as pd
import os
from get_pdf import download_pdfs
from get_review import generate_reviews

def main():
    # 1. Load Report Data
    csv_path = "리포트_데이터_최종.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    print(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    
    if '첨부파일' not in df.columns:
        print("Error: '첨부파일' column not found in CSV.")
        return

    # 2. Download PDFs
    print("Starting PDF download...")
    pdf_urls = df['첨부파일'].dropna().tolist()
    download_pdfs(pdf_urls)
    print("PDF download complete.")

    # 3. Generate Reviews
    print("Starting review generation...")
    generate_reviews()
    print("Review generation complete.")

if __name__ == "__main__":
    main()
