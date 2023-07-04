"""
Module for utility functions.
"""
import datetime
import json
import math
import typing
import uuid

import ffmpeg


def time_now() -> datetime.datetime:
    """
    Function to get current time with UTC timezone.
    """
    return datetime.datetime.now(tz=datetime.UTC)


def time_now_as_ts() -> int:
    """
    Function to get current time as timestamp.
    """
    return int(time_now().timestamp() * 1000)


def convert_audio(path: str, output_name: str, is_prod: bool) -> None:
    """
    Convert the type from one audio to another.
    """
    ffmpeg.input(path).output(output_name).run(overwrite_output=True, quiet=is_prod)


def get_file_metadata(path: str) -> dict[str, typing.Any]:
    """
    Function to get file metadata.
    """
    response = ffmpeg.probe(path)
    metadata: dict[str, typing.Any] = response.get("streams", [{}])[0]
    metadata["duration"] = int(
        math.ceil(float(response.get("format").get("duration", 61)))
    )
    return metadata


class CustomEncoder(json.JSONEncoder):
    """
    Class for uuid encoding when dumping
    """

    def default(self, o: typing.Any) -> typing.Any:
        """
        Method to correctly handle uuid.
        """
        if isinstance(o, uuid.UUID):
            return str(o)
        if isinstance(o, datetime.date):
            return o.strftime("%Y-%m-%d %H:%M:%S.%fZ")
        return json.JSONEncoder.default(self, o)


class UUIDEncoder(json.JSONEncoder):
    """
    Class for uuid encoding when dumping
    """

    def default(self, o: typing.Any) -> typing.Any:
        """
        Method to correctly handle uuid.
        """
        if isinstance(o, uuid.UUID):
            return str(o)
        if isinstance(o, list):
            return [self.default(item) for item in o]
        if isinstance(o, bytes):
            return o.decode("utf-8")
        return json.JSONEncoder.default(self, o)


def words_recursion(phrase: str) -> list[str]:
    """
    Recursion to split the phrases
    """
    phrase = phrase.strip()
    if len(phrase) < 100:
        return [phrase]
    phrase_calc = phrase[:100]
    if "," in phrase_calc:
        delimiter = ", " if ", " in phrase_calc else ","
    else:
        delimiter = " "
    phrase_1 = phrase_calc.rsplit(delimiter, 1)[0]
    phrase_list = [phrase_1, phrase[len(phrase_1) + len(delimiter) :]]
    result = []
    for phrase_new in phrase_list:
        result.extend(words_recursion(phrase_new))
    return result
