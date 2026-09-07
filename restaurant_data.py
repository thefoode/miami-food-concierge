from sheet_data import make_csv_fetcher

get_restaurant_data = make_csv_fetcher("SHEET_CSV_URL", "restaurant data", required=True)
