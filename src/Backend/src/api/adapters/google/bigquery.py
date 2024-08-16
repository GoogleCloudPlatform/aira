"""
Module with the implementation of bigquery
"""

import asyncio
import dataclasses
import functools
import json
import typing
from datetime import datetime

from google.cloud import bigquery
from google.oauth2 import service_account

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

    async def save(self, result: Result) -> typing.Sequence[dict[str, typing.Any]]:
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
        return response

    async def get_student_results(
        self,
        school_region: str | None = None,
        school_city: str | None = None,
        exam_name: str | None = None,
        school_name: str | None = None,
        class_name: str | None = None,
        exam_start_date: datetime | None = None,
        exam_end_date: datetime | None = None,
        organizations: list[str] | None = None,
        groups: list[str] | None = None,
    ) -> typing.Sequence[dict[str, typing.Any]]:
        """
        Get student results from database.
        """
        fields = []
        # ruff: noqa: E501
        query_parameters: list[
            bigquery.ScalarQueryParameter | bigquery.ArrayQueryParameter
        ] = []
        if school_region:
            fields.append("school_region=@school_region_param")
            query_parameters.append(
                bigquery.ScalarQueryParameter(
                    "school_region_param", "STRING", school_region
                )
            )
        if school_city:
            fields.append("school_city=@school_city_param")
            query_parameters.append(
                bigquery.ScalarQueryParameter(
                    "school_city_param", "STRING", school_city
                )
            )
        if exam_name:
            fields.append("exam_name=@exam_name_param")
            query_parameters.append(
                bigquery.ScalarQueryParameter("exam_name_param", "STRING", exam_name)
            )
        if school_name:
            fields.append("school_name=@school_name_param")
            query_parameters.append(
                bigquery.ScalarQueryParameter(
                    "school_name_param", "STRING", school_name
                )
            )
        if class_name:
            fields.append("class_name=@class_name_param")
            query_parameters.append(
                bigquery.ScalarQueryParameter("class_name_param", "STRING", class_name)
            )
        if exam_start_date:
            fields.append("exam_start_date>=@exam_start_date_param")
            query_parameters.append(
                bigquery.ScalarQueryParameter(
                    "exam_start_date_param", "TIMESTAMP", exam_start_date
                )
            )
        if exam_end_date:
            fields.append("exam_end_date<=@exam_end_date_param")
            query_parameters.append(
                bigquery.ScalarQueryParameter(
                    "exam_end_date_param", "TIMESTAMP", exam_end_date
                )
            )
        if organizations:
            fields.append("school_uuid IN UNNEST(@organizations_param)")
            query_parameters.append(
                bigquery.ArrayQueryParameter(
                    "organizations_param", "STRING", organizations
                )
            )
        if groups:
            fields.append("class_uuid IN UNNEST(@groups_param)")
            query_parameters.append(
                bigquery.ArrayQueryParameter("groups_param", "STRING", groups)
            )
        where_clause = ""
        if fields:
            where_clause = "WHERE " + " AND ".join(fields)

        job_config = bigquery.QueryJobConfig(query_parameters=query_parameters)
        query = (
            "SELECT * "
            "FROM `rad-stt-dev.dataset_lia.student_results` "
            f"{where_clause}"
            "LIMIT 1000"
        )

        query_job = await asyncio.to_thread(
            functools.partial(self.client.query, query, job_config=job_config)
        )
        results = await asyncio.to_thread(functools.partial(query_job.result))
        return list(map(dict, results))
