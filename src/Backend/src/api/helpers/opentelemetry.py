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
Opentelemetry helper stuff.
"""

import functools
import logging
import typing

from google.pubsub_v1.types import pubsub
from opentelemetry import propagate
from opentelemetry.propagators import textmap


class PubsubAttributeGetter(textmap.Getter[dict[str, typing.Any]]):
    """
    Class implementing getter for otel.
    """

    def get(self, carrier: dict[str, typing.Any], key: str) -> list[str] | None:
        """
        Getter implementation to retrieve an attribute value from a pubsub
        message received via push endpoint.

        Args:
            carrier: message dictionary
            key: attribute name
        Returns:
            A list with a single string with the attribute value if it exists,
                else None.
        """
        attributes = carrier.get("attributes") or {}
        if key not in attributes:
            return None
        return [attributes[key]]

    def keys(self, carrier: dict[str, typing.Any]) -> list[str]:
        """
        Method implementation for retrieving attributes.
        """
        return list((carrier.get("attributes") or {}).keys())


class PubsubAttributeSetter(textmap.Setter[pubsub.PubsubMessage]):
    """
    Class implementing setter for otel.
    """

    def set(self, carrier: pubsub.PubsubMessage, key: str, value: str) -> None:
        """
        Setter implementation to set a PubsubMessage attribute value.

        Args:
            carrier: PubsubMessage
            key: attribute name
            value: attribute value
        """
        if key in carrier.attributes:
            logging.warning("Attribute %s is already set for message, overriding", key)
        carrier.attributes[key] = value


inject_to_pubsub_message = functools.partial(
    propagate.inject, setter=PubsubAttributeSetter()
)
extract_from_pubsub_push_message = functools.partial(
    propagate.extract, getter=PubsubAttributeGetter()
)
