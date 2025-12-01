import pandas as pd
import os
from get_pdf import download_pdfs
from get_review import generate_reviews

def main():
    # 1. Load Report URLs from DB
    from db import get_all_report_urls
    
    print("Fetching report URLs from DB...")
    pdf_urls = get_all_report_urls()
    
    if not pdf_urls:
        print("No report URLs found in DB.")
        return

    # 2. Download PDFs
    print(f"Starting PDF download for {len(pdf_urls)} files...")
    download_pdfs(pdf_urls)
    print("PDF download complete.")

    # 3. Generate Reviews
    print("Starting review generation...")
    generate_reviews()
    print("Review generation complete.")

if __name__ == "__main__":
    main()
