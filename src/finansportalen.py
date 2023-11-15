import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import date
from io import StringIO
from urllib.parse import urlencode

import pandas as pd
import requests


class Mortgage:
    COLUMNS = {
        "leverandor_tekst": "bank",
        "navn": "product_name",
        "effektiv_rente": "rate_effective",
        "valgt_rente": "rate_nominal",
        "mndbelop": "monthly",
        "totalkostnad": "total_cost",
        "kostnad1ar": "first_year_cost",
        "etableringsgebyr_for_lanet": "establishment_fee",
    }

    def __init__(self, params):
        self.params = params
        self.base_url = "https://www.finansportalen.no/feed/v3/bank/boliglan_toppN.atom"
        self.xmlns = "{http://www.w3.org/2005/Atom}"

    def _get_xml(self):
        params = urlencode(self.params)
        url = f"{self.base_url}?{params}"

        res = requests.get(
            url,
            auth=(os.getenv("FP_USERNAME"), os.getenv("FP_PASSWORD")),
        )

        if res.status_code == 200:
            return res.content
        else:
            return None

    def get_dataframe(self):
        xml = self._get_xml()

        if xml:
            tree = ET.fromstring(xml).findall(f"{self.xmlns}entry")

            listings = {}
            count = 0

            for entries in tree:
                count += 1
                listings.update(
                    {
                        count: {
                            re.sub("{[^>]+}", "", entry.tag): entry.text.strip()
                            for entry in entries
                            if entry.text
                        }
                    }
                )

            _json = json.dumps(listings, indent=2, separators=(",", ": "))

            df = pd.read_json(StringIO(_json), orient="index")
            df = df[self.COLUMNS.keys()].rename(columns=self.COLUMNS)
            df.insert(0, "date", pd.to_datetime(date.today()))

            return df
        else:
            return None
