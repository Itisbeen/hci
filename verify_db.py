from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///reports.db")

with engine.connect() as conn:
    # Check for a report that should have review data (e.g., from 644830.pdf)
    # We need to find the report with attachment_url containing '644830'
    result = conn.execute(text("SELECT id, title, summary, novice_content, expert_content FROM reports WHERE attachment_url LIKE '%644830%'"))
    row = result.fetchone()
    
    if row:
        print(f"Report ID: {row[0]}")
        print(f"Title: {row[1]}")
        print(f"Summary: {row[2]}")
        print(f"Novice Content: {row[3]}")
        print(f"Expert Content: {row[4]}")
        
        if row[2] and row[3] and row[4]:
            print("SUCCESS: Review data loaded.")
        else:
            print("FAILURE: Review data missing.")
    else:
        print("FAILURE: Report not found.")
