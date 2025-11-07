from datetime import date

import pandas as pd
import requests


class Mortgage:
    COLUMNS = {
        "companyName": "bank",
        "name": "product_name",
        "effectiveInterestRate": "rate_effective",
        "nominalInterestRate": "rate_nominal",
        "monthlyPayment": "monthly",
        "estimatedTotalPayment": "total_cost",
        "firstYearCost": "first_year_cost",
        "establishmentFee": "establishment_fee",
    }

    def __init__(self, params):
        self.params = params
        self.api_url = "https://finans-api.forbrukerradet.no/bankprodukt/boliglan"

    def _fetch_data(self):
        """Fetch mortgage data from API."""
        response = requests.get(
            self.api_url, headers={"Accept": "application/json"}, params=self.params, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def get_dataframe(self):
        """Get data and convert to DataFrame."""
        try:
            data = self._fetch_data()

            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)

            # Extract establishment fee from nested product
            df["establishmentFee"] = df["product"].apply(
                lambda x: x.get("establishmentFeeForLoan", 0) if isinstance(x, dict) else 0
            )

            # Compute first year cost
            df["firstYearCost"] = df["monthlyPayment"] * 12

            # Debug: show only the columns we'll keep
            debug_cols = [col for col in self.COLUMNS if col in df.columns]
            print(df[debug_cols])
            df[debug_cols].to_csv("df.csv", index=False)

            # Select and rename columns
            existing = [col for col in self.COLUMNS if col in df.columns]
            df = df[existing].rename(columns=self.COLUMNS)

            # Strip whitespace from product name
            df["product_name"] = df["product_name"].str.strip()

            df.insert(0, "date", pd.to_datetime(date.today()))

            return df

        except Exception as e:
            print(f"Error fetching mortgage data: {e}")
            return pd.DataFrame()
