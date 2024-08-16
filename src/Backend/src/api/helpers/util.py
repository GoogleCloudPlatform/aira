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
    delimiter = (", " if ", " in phrase_calc else ",") if "," in phrase_calc else " "
    phrase_1 = phrase_calc.rsplit(delimiter, 1)[0]
    phrase_list = [phrase_1, phrase[len(phrase_1) + len(delimiter) :]]
    result = []
    for phrase_new in phrase_list:
        result.extend(words_recursion(phrase_new))
    return result


word_dict = {
    "pt-BR": {
        "0": "zero",
        "1": "um",
        "2": "dois",
        "3": "três",
        "4": "quatro",
        "5": "cinco",
        "6": "seis",
        "7": "sete",
        "8": "oito",
        "9": "nove",
    },
    "en-US": {
        "0": "zero",
        "1": "one",
        "2": "two",
        "3": "three",
        "4": "four",
        "5": "five",
        "6": "six",
        "7": "seven",
        "8": "eight",
        "9": "nine",
    },
    "es-ES": {
        "0": "cero",
        "1": "uno",
        "2": "dos",
        "3": "tres",
        "4": "cuatro",
        "5": "cinco",
        "6": "seis",
        "7": "siete",
        "8": "ocho",
        "9": "nueve",
    },
}


def convert_number_to_written_text(word: str, language: str = "pt-BR") -> list[str]:
    """
    Convert decimal numbers to written text.

    :param word: the word that is in decimal format.
    :param language: the language that should be used to convert.

    :returns: the word in written format.
    """
    return [word_dict[language][letter] for letter in word]


def check_spelling_or_syllables(sentence: list[str]) -> int:
    """
    Checks if the sentence is being spelled or if it is just syllables
    """
    qty_spelling = 0
    qty_syllables = 0
    for word in sentence:
        if len(word) == 1:
            qty_spelling += 1
        elif len(word) <= 4:
            qty_syllables += 1
    if len(sentence) == 0:
        return 0
    if qty_syllables / len(sentence) >= 0.7:
        return 1  # Silabou
    if qty_spelling / len(sentence) >= 0.7:
        return -1  # Soletrou
    return 0  # Normal


def clear_spelling_words(sentence: list[str]) -> list[str]:
    articles = {"os", "as"}
    match check_spelling_or_syllables(sentence):
        case -1:
            return [word for word in sentence if len(word) > 1 and word not in articles]
        case _:
            return sentence
