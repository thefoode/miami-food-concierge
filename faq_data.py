from sheet_data import make_csv_fetcher

get_faq_data = make_csv_fetcher("FAQ_CSV_URL", "FAQ data", required=False)
