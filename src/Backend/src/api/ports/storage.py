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
Module containing storage abstract.
"""
import abc


class Storage(abc.ABC):
    """
    Storage abstract
    """

    @abc.abstractmethod
    async def upload_by_file(self, path: str, audio_path: str) -> str:
        """
        Method that uploads a file by name.
        """

    @abc.abstractmethod
    async def upload_by_text(self, path: str, text: bytes) -> str:
        """
        Method that uploads a file by bytes.
        """

    @abc.abstractmethod
    async def download(self, uri: str, file_name: str) -> str:
        """
        Method that downloads a file.
        """

    @abc.abstractmethod
    async def generate_signed_url(self, path: str, mimetype: str) -> str:
        """
        Method to generate a signed url
        """

    @abc.abstractmethod
    async def get_blob_content_type(self, path: str) -> str | None:
        """
        Method to get blob metadata.
        """
