from api import models
from api.domain.service import phonemes
from api.helpers import util


def get_right_count_user_result(
    words: list[str], tts_words: str, question_type: str | None
) -> tuple[int, list[str]]:
    transcripts = (
        tts_words.replace(".", " ")
        .replace(",", "")
        .replace("!", "")
        .replace("?", "")
        .strip()
        .split()
    )
    match question_type:
        case models.QuestionType.WORDS.value | models.QuestionType.COMPLEX_WORDS.value:
            data_words = phonemes.phonemize_data_list(words)
            data_transcript = phonemes.phonemize_data_list(transcripts)
            right_words, clean_transcripts = _compare_list_string(
                data_words, data_transcript, words, transcripts
            )
        case _:
            data_words = words.copy()
            data_transcript = transcripts.copy()
            right_words, clean_transcripts = _compare_list_string(
                data_words, data_transcript, words, transcripts
            )
            right_words = util.clear_spelling_words(right_words)
    return len(right_words), clean_transcripts


def _compare_list_string(
    data_words: list[str],
    data_transcripts: list[str],
    words: list[str],
    transcripts: list[str],
) -> tuple[list[str], list[str]]:
    right_words = []
    for i, data_word in enumerate(data_words):
        for k, data_transcript in enumerate(data_transcripts):
            if data_transcript.lower() == data_word.lower():
                right_words.append(words[i])
                transcripts[k] = words[i]
                data_transcripts[k] = ""
                break

    return right_words, transcripts
