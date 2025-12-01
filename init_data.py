from db import init_db, load_csv_to_db, create_stock_summary_view

def main():
    print("Initializing database...")
    init_db()
    
    print("Loading data from CSV...")
    # Load main report data and review summaries
    load_csv_to_db("리포트_데이터_최종.csv", "pdf_summary_300files.csv")
    
    print("Creating stock summary view...")
    create_stock_summary_view()
    
    print("Data initialization complete.")

if __name__ == "__main__":
    main()
