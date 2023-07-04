# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
