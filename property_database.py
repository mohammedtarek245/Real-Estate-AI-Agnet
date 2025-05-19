import pandas as pd

class RealEstateListings:
    def __init__(self, csv_path: str):
        try:
            self.df = pd.read_csv(csv_path)
        except FileNotFoundError:
            self.df = pd.DataFrame()
            print(f"⚠️ CSV file not found at: {csv_path}. Using empty DataFrame.")
        except Exception as e:
            self.df = pd.DataFrame()
            print(f"⚠️ Error loading listings CSV: {e}")

    def search(self, filters: dict) -> list:
        results = self.df.copy()

        if self.df.empty:
            return []

        if 'location' in filters:
            results = results[results['location'].str.contains(filters['location'], case=False, na=False)]

        if 'property_type' in filters:
            results = results[results['type'].str.contains(filters['property_type'], case=False, na=False)]

        if 'budget' in filters:
            try:
                # Handle both string or list formats for budget
                budget_value = (
                    filters['budget'][0]
                    if isinstance(filters['budget'], list)
                    else filters['budget']
                )
                budget = int(str(budget_value).replace(",", "").strip())
                results = results[pd.to_numeric(results['price'], errors='coerce') <= budget]
            except Exception as e:
                print(f"⚠️ Could not parse budget: {filters.get('budget')} → {e}")

        if 'bedrooms' in filters:
            try:
                results = results[results['bedrooms'] == int(filters['bedrooms'])]
            except Exception:
                pass

        # Return top 3 matching rows as dictionaries
        return results.head(3).to_dict(orient="records")
