"""
Module with the implementation of bigquery
"""
import asyncio
import dataclasses
import functools
import json

import google.cloud.bigquery as bigquery
import google.oauth2.service_account as service_account

from api import helpers, ports
from api.helpers.schemas import AnalyticalResult as Result


class BigQuery(ports.AnalyticalResult):
    """
    Implementation of google's cloud bigquery.
    """

    def __init__(self, project_id: str, dataset: str, table_name: str, creds_path: str):
        credentials = None
        if creds_path:
            credentials = service_account.Credentials.from_service_account_file(
                creds_path
            )
        self.client = bigquery.Client(project=project_id, credentials=credentials)
        self.project_id = project_id
        self.dataset = dataset
        self.table_name = table_name

    async def save(self, result: Result) -> bool:
        """
        Save result data to analytical database.
        """
        row = [
            json.loads(
                json.dumps(dataclasses.asdict(result), cls=helpers.CustomEncoder)
            )
        ]
        table_ref = bigquery.Table(
            f"{self.project_id}.{self.dataset}.{self.table_name}"
        )
        table = self.client.get_table(table_ref)
        response = await asyncio.to_thread(
            functools.partial(self.client.insert_rows, table, row)
        )
        return not response
