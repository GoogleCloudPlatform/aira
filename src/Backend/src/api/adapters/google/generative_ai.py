import json
import random
import sys
import textwrap
import typing
from pathlib import Path

__import__("pysqlite3")
sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import chromadb
import vertexai
from chromadb.utils import embedding_functions
from vertexai.generative_models import GenerativeModel

from api import errors, models, ports

CURRENT_DIR = Path(__file__).resolve().parent
THEMES_DICT = {
    models.QuestionTheme.MONICA_AGUA_BOA: "monica_agua_boa.txt",
    models.QuestionTheme.O_MENINO_MALUQUINHO: "o_menino_maluquinho.txt",
    models.QuestionTheme.O_PEQUENO_PRINCIPE: "o_pequeno_principe.txt",
}


class GenerativeAI(ports.GenAI):
    """
    Implementation of google's cloud storage.
    """

    def __init__(self, project_id: str, location: str = "us-central1", embedding_model="text-embedding-004"):
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-2.0-flash-exp")
        self.embedding_model = embedding_model
        self.project_id = project_id
        self.location = location
        self.chroma_client = chromadb.PersistentClient(
            path="./chroma_data"
        )
        # GoogleVertexEmbeddingFunction requires api_key but uses it as a placeholder
        # when running in GCP with service account, it will use default credentials
        import google.auth
        credentials, _ = google.auth.default()
        self.embedding_function = (
            embedding_functions.GoogleVertexEmbeddingFunction(
                api_key="",  # Empty string - will use default credentials
                project_id=project_id,
                region=location,
                model_name=self.embedding_model,
            )
        )
        self.collections = {}

    def generate_words(
        self,
        qty_words: str,
        question_type: models.QuestionType,
        block_words: list[str] | None = None,
    ) -> list[str]:
        """
        Method genarates x amount of words.
        """
        qty = qty_words + 100
        query = ""
        # ruff: noqa: E501
        if block_words:
            block_words_joined = " ".join(block_words)
            query += f"Não utilize as palavras {block_words_joined}. "
        match question_type:
            case models.QuestionType.COMPLEX_WORDS:
                query += f"Me gere EXATAMENTE {qty} palavras ÚNICAS e DIFERENTES, aleatórias, com pelo menos três sílabas, todas em minúsculas, separadas por espaço. IMPORTANTE: Não repita palavras, cada palavra deve ser única. Critérios: - Diferentes extensões (número de letras e sílabas), com estruturas silábicas canônicas (CV) e não canônicas (CVC, VC, CCV); - Inclua palavras com regularidades e irregularidades ortográficas, considerando grafemas e fonemas com relação direta e indireta; - Evite palavras correlacionadas entre si. Retorne APENAS as palavras separadas por espaço, sem numeração ou formatação."
            case models.QuestionType.WORDS:
                query += f"Me gere EXATAMENTE {qty} palavras ÚNICAS e DIFERENTES, aleatórias, todas em minúsculas, separadas por espaço. IMPORTANTE: Não repita palavras, cada palavra deve ser única. Critérios: - Diferentes extensões (número de letras e sílabas), com estruturas silábicas canônicas (CV) e não canônicas (CVC, VC, CCV); - Familiaridade acessível para alunos em fase inicial de leitura, evitando palavras muito complexas ou técnicas; - Inclua palavras com regularidades e irregularidades ortográficas, considerando grafemas e fonemas com relação direta e indireta; - Evite palavras correlacionadas entre si. Retorne APENAS as palavras separadas por espaço, sem numeração ou formatação."
        import time
        from google.api_core import exceptions as google_exceptions
        
        try:
            response = self.model.generate_content(query)
        except google_exceptions.ResourceExhausted:
            # Se atingir rate limit na primeira tentativa, aguardar e tentar novamente
            time.sleep(2)
            response = self.model.generate_content(query)
        if question_type == models.QuestionType.PHRASES:
            return response.text
        words_list = list(set(response.text.split()))
        
        # Se não tivermos palavras suficientes, gerar mais com backoff exponencial
        retry_count = 0
        while len(words_list) < qty_words and retry_count < 3:
            try:
                # Aguardar antes de fazer nova requisição (exponential backoff)
                wait_time = 2 ** retry_count  # 1s, 2s, 4s
                time.sleep(wait_time)
                
                additional_qty = qty_words - len(words_list) + 20
                additional_query = query.replace(f"{qty}", f"{additional_qty}")
                additional_response = self.model.generate_content(additional_query)
                words_list = list(set(words_list + additional_response.text.split()))
                retry_count += 1
            except google_exceptions.ResourceExhausted:
                # Se atingir rate limit durante retry, parar e retornar o que temos
                break
            except Exception:
                # Para qualquer outro erro, parar e retornar o que temos
                break
        
        # Garantir que não excedemos o tamanho disponível
        sample_size = min(qty_words, len(words_list))
        sub_list = random.sample(words_list, sample_size)

        return sub_list

    def generate_multiple_choice(
        self,
        qty: int,
        text: str | None,
        user_input: str | None,
        block_questions: list[str] | None = None,
    ) -> dict[str, typing.Any]:
        """
        Method genarates a multiple choice question.
        """
        choice_query = ""
        for _ in range(qty):
            choice_query += (
                '{"answer": "A alternativa da questão", "is_correct": boolean},\n'
            )

        # ruff: noqa: E501
        query = "Me gere uma questão de múltipla escolha em formato JSON. Me responda em apenas uma linha, sem formatações HTML ou markdowns. A questão deve ser para jovens em processo de alfabetização. "
        if text and not user_input:
            query = f'Utilize este texto como referência: "{text}". A resposta da questão precisa estar explicitamente no texto e a resposta precisa refletir exatamente o que está escrito no texto. A questão obrigatoriamente deve ser sobre interpretação de texto. '
        if user_input and not text:
            query = f'A questão deve estar relacionada com este input: "{user_input}". '
        if text and user_input:
            query += f"A questão deve ser de interpretação sobre este texto: {text}; E utilizar este input para gerar uma pergunta sobre: {user_input}. Não fuja do tema nem do texto e não crie contexto que não esteja no texto. "
        query += f"""Retorne *apenas* um JSON válido, sem texto antes ou depois, em uma linha apenas. O formato JSON deve ser *IGUAL* a este exemplo, os campos em inglês, o valor dos campos em português brasileiro:
            {{
            "question": "Texto da questão",
            "answers": [
                {choice_query}
            ]
            }}
            Descrição dos campos:
            question: str. Texto da pergunta sendo feita; answers: list[dict[str, typing.Any]]. Lista de dicionários que contém informações sobre a alternativa.
            answer: str. Texto da alternativa; is_correct: bool. Boolean que indica se a alternativa está correta. apenas uma alternativa correta por questão.
            A quantidade de alternativas deve ser exatamente {qty}.
            Separe o texto em partes, pode ser de acordo com pontuação ou quantidade de letras, e a pergunta deve ser encontrada na parte (ou próximo a esta), de acordo com essa seed: {random.randint(0, 100)}"""
        if block_questions:
            block_questions_joined = '", "'.join(block_questions)
            query += f'Não utilize as questões "{block_questions_joined}" ou questões que podem ser interpretadas como alguma dessas citadas.'
        response = self.model.generate_content(query)
        json_start = response.text.find("{")
        json_end = response.text.rfind("}")
        json_str = response.text[json_start : json_end + 1]
        question_data = json.loads(json_str)
        return question_data

    def generate_text(self, subject: str = "infantil") -> str:
        """
        Method genarates a readable text.
        """
        query = f'Crie um texto narrativo curto, com cerca de 140 palavras, destinado à avaliação de leitura para alunos em fase inicial. O tema do texto é: "{subject}". - O texto deve incluir um título atrativo relacionado ao tema. - Utilize vocabulário simples e acessível, priorizando palavras adequadas ao nível de leitura inicial. - Inclua palavras que apresentem diferentes estruturas silábicas (como CV, CVC, VC, CCV) e explore variações ortográficas regulares e irregulares de forma equilibrada. - Mantenha a narrativa envolvente e estruturada, com uma introdução, um breve desenvolvimento e um desfecho claro '
        response = self.model.generate_content(query)
        return response.text

    def generate_question(
        self,
        question_type: models.QuestionType,
        text_data: str | None,
        user_input: str | None,
        block_questions: list[str] | None,
        question_theme: models.QuestionTheme | None = None,
    ) -> str:
        relevant_chunks = []
        match question_type:
            case models.QuestionType.UNDERSTANDING_CHECK:
                query = self._get_understanding_check_query(text_data, user_input)
            case models.QuestionType.LOGICAL_SITUATIONS:
                query = self._get_logical_situations_query(user_input)
            case models.QuestionType.SHORT_EXPLANATIONS:
                query = self._get_short_explanation_query(user_input)
            case models.QuestionType.SPECIFIC_KNOWLEDGE:
                collection_name = THEMES_DICT[question_theme]
                relevant_chunks.extend(
                    self._process_collection(collection_name, user_input)
                )
                query = self._get_themed_short_explanation_query(user_input)
            case _:
                raise errors.NotFound(question_type)

        query += f"Retorne *apenas* a pergunta, sem texto antes ou depois, e em uma única linha. Gere sempre 200 perguntas e retorne apenas a pergunta de número {random.randint(0, 150)}. "

        if block_questions:
            block_questions_joined = '", "'.join(block_questions)
            query += f'Não utilize as perguntas "{block_questions_joined}" ou variações dessas perguntas.'

        if relevant_chunks:
            contents = relevant_chunks + [query]
            response = self.model.generate_content(contents=contents)
        else:
            response = self.model.generate_content(query)

        return response.text.strip()

    def evaluate_test(
        self,
        question_type: models.QuestionType,
        text_data: str,
        tts_data: str,
        retry_attempt: int = 0,
        question_theme: models.QuestionTheme | None = None,
    ) -> tuple[bool | None, str | None]:
        # ruff: noqa: E501
        # Verificando se o tts_data está vazio ou contém apenas espaços
        relevant_chunks = []
        if not tts_data.strip():
            tts_data = "Nenhuma resposta foi identificada no áudio. Neste caso, o aluno não soube responder ou teve um problema de gravação, forneça a resposta para o aluno no feedback"
        match question_type:
            case models.QuestionType.UNDERSTANDING_CHECK:
                query = self._evaluate_understanding_check()
            case models.QuestionType.LOGICAL_SITUATIONS:
                query = self._evaluate_logical_situations()
            case models.QuestionType.SHORT_EXPLANATIONS:
                query = self._evaluate_short_explanations()
            case models.QuestionType.SPECIFIC_KNOWLEDGE:
                collection_name = THEMES_DICT[question_theme]
                relevant_chunks.extend(self._process_collection(collection_name))
                query = self._evaluate_themed_short_explanations()
            case _:
                raise errors.NotFound(question_type)

        query += """
        Retorne um JSON válido, sem texto antes ou depois, no seguinte formato:  

{  
  "is_correct": True,  
  "feedback": "Mensagem pedagógica objetiva e motivadora"  
}  

Regras para o feedback:  
- Se a resposta estiver **correta**, elogie, reforce o aprendizado e retorne True em "is_correct".  
- Se a resposta estiver **incorreta**, explique brevemente o erro e forneça uma orientação para que o aluno compreenda melhor o conceito e retorne False em "is_correct".  

O feedback deve ser **claro, objetivo e motivador**, sem formatações HTML ou markdowns. 
"""

        query += f'Este é o texto da questão: "{text_data}". Esta é a resposta do aluno, entenda que ela foi retirada por um programa de Speech to Text: {tts_data}'

        if relevant_chunks:
            contents = relevant_chunks + [query]
            response = self.model.generate_content(contents=contents)
        else:
            response = self.model.generate_content(query)
        json_start = response.text.find("{")
        json_end = response.text.rfind("}")
        json_str = response.text[json_start : json_end + 1]

        try:
            question_data = json.loads(json_str)
        except Exception:
            if retry_attempt < 5:
                return self.evaluate_test(
                    question_type,
                    text_data,
                    tts_data,
                    retry_attempt + 1,
                    question_theme,
                )
            return (None, None)

        return (question_data["is_correct"], question_data["feedback"])

    def get_exam_feedback(self, questions: list[typing.Any]) -> str:
        # Inicializando variáveis
        words_result = "Sem Classificação"
        words_user_accuracy = 0
        complex_result = "Sem Classificação"
        complex_user_accuracy = 0
        phrases_result = "Sem Classificação"
        phrases_user_accuracy = 0
        text_comprehension_result = 0
        total_text_comprehension_questions = 0
        logical_situation_result = 0
        total_logical_situation_questions = 0
        feedback_list_short = []
        feedback_list_industry = []

        # Processamento das questões
        for question in questions:
            if question.get("response"):
                match models.QuestionType(question["type"]):
                    case models.QuestionType.WORDS:
                        words_result = question["response"]["user_accuracy"]
                        words_user_accuracy = question["response"]["total_accuracy"]
                    case models.QuestionType.COMPLEX_WORDS:
                        complex_result = question["response"]["user_accuracy"]
                        complex_user_accuracy = question["response"]["total_accuracy"]
                    case models.QuestionType.PHRASES:
                        phrases_result = question["response"]["user_accuracy"]
                        phrases_user_accuracy = question["response"]["total_accuracy"]
                    case (
                        models.QuestionType.MULTIPLE_CHOICE
                        | models.QuestionType.UNDERSTANDING_CHECK
                    ):
                        total_text_comprehension_questions += 1
                        if question["response"].get("ai_is_correct"):
                            text_comprehension_result += 1
                    case models.QuestionType.LOGICAL_SITUATIONS:
                        total_logical_situation_questions += 1
                        if question["response"].get("ai_is_correct"):
                            logical_situation_result += 1
                    case models.QuestionType.SHORT_EXPLANATIONS:
                        feedback_list_short.append(
                            question["response"].get("ai_feedback")
                        )
                    case models.QuestionType.SPECIFIC_KNOWLEDGE:
                        feedback_list_industry.append(
                            question["response"].get("ai_feedback")
                        )

        # Criando a base do prompt
        query = "Um estudante realizou uma prova abaixo seguem as questões que foram respondidas e os seus resultados"

        # Adicionando Proficiência de Leitura se houver questões desse tipo
        if (
            words_result != "Sem Classificação"
            or complex_result != "Sem Classificação"
            or phrases_result != "Sem Classificação"
        ):
            query += "Proficiência de leitura: "
            if words_result != "Sem Classificação":
                query += f"Na questão de palavras simples: O percentual de acerto se comparado ao total de palavras lidas foi de {words_result} o percentual de acerto se comparado ao total de palavras que estavam contidos na questão foi de {words_user_accuracy}. "
            if complex_result != "Sem Classificação":
                query += f"Na questão de palavras complexas: O percentual de acerto se comparado ao total de palavras lidas foi de {complex_result} o percentual de acerto se comparado ao total de palavras que estavam contidos na questão foi de  {complex_user_accuracy}. "
            if phrases_result != "Sem Classificação":
                query += f"Na questão de texto narrativo: O percentual de acerto se comparado ao total de palavras lidas foi de {phrases_result} o percentual de acerto se comparado ao total de palavras que estavam contidos na questão foi de {phrases_user_accuracy}. "

        # Adicionando Compreensão de Texto se houver questões desse tipo
        if total_text_comprehension_questions > 0:
            query += f"Compreensão de texto: De um total de {total_text_comprehension_questions} questões de compreensão de texto, o estudante acertou {text_comprehension_result}. "

        # Adicionando Pensamento Crítico e Lógico se houver questões desse tipo
        if total_logical_situation_questions > 0:
            query += f"Pensamento crítico e lógico: De um total de {total_logical_situation_questions} questões de pensamento crítico e lógico, o estudante acertou {logical_situation_result}. "

        # Adicionando os feedbacks separados por tipo
        if feedback_list_short:
            query += f"Comunicação e resolução de problemas: Nesta questão, o aluno recebeu os seguintes feedbacks: \"{', '.join(feedback_list_short)}\". "
        if feedback_list_industry:
            query += f"Nas questões específicas de Áreas da Indústria: O aluno recebeu os seguintes feedbacks: \"{', '.join(feedback_list_industry)}\". "

        # Baseando o feedback no que foi respondido
        query += "Baseado nestes dados, me gere um feedback motivacional para o estudante, pontuando o que ele foi bem e o que ele pode melhorar. O feedback final do aluno deve conter no máximo 900 caracteres."

        # Gerando o conteúdo com o modelo
        result = self.model.generate_content(query).text.strip()

        # Retornando o resultado
        return result

    #     def get_exam_feedback(self, questions: list[typing.Any]) -> str:
    #         words_result = "Sem Classificação"
    #         words_user_accuracy = 0
    #         complex_result = "Sem Classificação"
    #         complex_user_accuracy = 0
    #         phrases_result = "Sem Classificação"
    #         phrases_user_accuracy = 0
    #         text_comprehension_result = 0
    #         total_text_comprehension_questions = 0
    #         logical_situation_result = 0
    #         total_logical_situation_questions = 0
    #         feedback_list = []
    #         for question in questions:
    #             if question.get("response"):
    #                 match models.QuestionType(question["type"]):
    #                     case models.QuestionType.WORDS:
    #                         words_result = question["response"]["user_rating"]
    #                         words_user_accuracy = question["response"]["user_accuracy"]
    #                     case models.QuestionType.COMPLEX_WORDS:
    #                         complex_result = question["response"]["user_rating"]
    #                         complex_user_accuracy = question["response"]["user_accuracy"]
    #                     case models.QuestionType.PHRASES:
    #                         phrases_result = question["response"]["user_rating"]
    #                         phrases_user_accuracy = question["response"]["user_accuracy"]
    #                     case (
    #                         models.QuestionType.MULTIPLE_CHOICE
    #                         | models.QuestionType.UNDERSTANDING_CHECK
    #                     ):
    #                         total_text_comprehension_questions += 1
    #                         if question["response"].get("ai_is_correct"):
    #                             text_comprehension_result += 1
    #                     case models.QuestionType.LOGICAL_SITUATIONS:
    #                         total_logical_situation_questions += 1
    #                         if question["response"].get("ai_is_correct"):
    #                             logical_situation_result += 1
    #                     case models.QuestionType.SHORT_EXPLANATIONS:
    #                         feedback_list.append(question["response"].get("ai_feedback"))
    #         query = f"""
    # Um estudante realizou uma prova que avalia os seguintes temas Proficiência de leitura. Compreensão de texto, Pensamento crítico e lógico e Comunicação e resolução de problemas,
    # vou informar o resultado do estudante em cada um dos temas.
    # Proficiência de leitura:
    # Dentro de proficiencia de leitura o aluno pode ser "Pré-leitor 1", "Pré-leitor 2", "Pré-leitor 3", "Pré-leitor 4", "Leitor Iniciante", "Leitor Fluente",
    # sendo o "Pré-leitor 1" o pior e "Leitor Fluente" o melhor.
    # Resultados do aluno:
    # Questão de palavras simples: {words_result}
    # com uma acurácia de {words_user_accuracy}
    # Questão de palavras complex: {complex_result}
    # com uma acurácia de {complex_user_accuracy}
    # Questão de frases: {phrases_result}
    # com uma acurácia de {phrases_user_accuracy}
    # Caso esteja sem classificação foi por que o aluno não respondeu, ignore a questão neste caso. A acurácia indica quantas palavras ele conseguiu ler no tempo indicado para a questão fazendo uma relação de quantas leu por quantas acertou. A acurácia vai de 0.0 a 1.0.

    # Compreensão de texto:
    # De um total de {total_text_comprehension_questions} questões de compreensão de texto o estudante acertou {text_comprehension_result}.

    # Pensamento crítico e lógico:
    # De um total de {total_logical_situation_questions} questões de compreensão de texto o estudante acertou {logical_situation_result}.

    # Comunicação e resolução de problemas:
    # Nesta questão, o aluno recebeu os seguintes feedbacks:
    # "{'", "'.join(feedback_list)}"

    # Baseado nestes dados me gere um feedback motivacional para o estudante pontuando o que ele foi bem e o que ele pode melhorar,
    # o feedback final do aluno deve conter no máximo 900 caracteres.
    #         """
    #         result = self.model.generate_content(query).text.strip()
    #         return result

    @staticmethod
    def _get_understanding_check_query(
        text_data: str | None, user_input: str | None
    ) -> str:
        query = "Me gere uma única pergunta de interpretação de texto. Me responda em apenas uma linha, sem formatações HTML ou markdowns. A pergunta deve avaliar a compreensão do usuário sobre um texto previamente apresentado. "
        if text_data and not user_input:
            query += f'Utilize este texto como referência: "{text_data}". A pergunta deve ser formulada de forma que valide se o usuário compreendeu corretamente o conteúdo do texto. '
        elif user_input and not text_data:
            query += (
                f'A pergunta deve estar relacionada com este input: "{user_input}". '
            )
        else:
            query += f'A pergunta deve ser de interpretação sobre este texto: "{text_data}", utilizando este input para direcionar o tema da pergunta: "{user_input}". Não fuja do conteúdo apresentado e não crie contexto além do texto. '

        return query

    @staticmethod
    def _get_logical_situations_query(user_input: str | None) -> str:
        return f'Gere uma questão desafiadora de **raciocínio lógico**. A questão deve estar relacionada com este input: "{user_input}". A questão deve envolver situações do dia a dia que exijam **pensamento analítico** e **dedução lógica** E por exemplo: "Ontem eu tinha 2 maçãs. Hoje eu tenho 3 maçãs, mas comi uma. Quantas maçãs eu tenho agora?" Regras: - A questão deve ser objetiva e clara. - Evite ambiguidades ou múltiplas interpretações. - Não inclua a resposta na pergunta. - **Apenas retorne a pergunta**, sem formatações HTML ou markdowns. Responda com apenas uma linha de texto contendo a questão.'

    @staticmethod
    def _get_short_explanation_query(user_input: str | None) -> str:
        # ruff: noqa: W291
        return f"""Gere uma situação-problema desafiadora para o usuário resolver baseada no input "{user_input}".

        Requisitos:  
        - A situação deve ser curta, clara e objetiva.  
        - Deve exigir uma explicação concisa como resposta.  
        - Deve estimular o pensamento crítico 
        - Deve ser contextualizada para que o usuário consiga responder de maneira natural.  

        A resposta do usuário será em áudio ou texto, então a pergunta deve ser estruturada de forma que possa ser respondida verbalmente.  

        Retorne apenas a pergunta, sem formatações HTML ou markdowns."""

    @staticmethod
    def _get_themed_short_explanation_query(user_input: str | None) -> str:
        # ruff: noqa: W291
        return f"""Gere uma situação-problema desafiadora para o usuário resolver baseada no input "{user_input}" utilizando o conteúdo fornecido.

        Requisitos:  
        - A situação deve ser curta, clara e objetiva.  
        - Deve exigir uma explicação concisa como resposta.  
        - Deve estimular o pensamento crítico 
        - Deve ser contextualizada para que o usuário consiga responder de maneira natural.  

        A resposta do usuário será em áudio ou texto, então a pergunta deve ser estruturada de forma que possa ser respondida verbalmente.  

        Retorne apenas a pergunta, sem formatações HTML ou markdowns."""

    @staticmethod
    def _evaluate_understanding_check() -> str:
        return "Avalie se a resposta do usuário para a pergunta cadastrada no sistema está correta ou incorreta. O input do usuário pode ser texto ou áudio transcrito.  A resposta correta está definida no banco de dados. Compare a resposta do usuário com a resposta esperada, garantindo que o significado original seja preservado.  "

    @staticmethod
    def _evaluate_logical_situations() -> str:
        return "Avalie se a resposta do usuário para a questão lógica cadastrada no sistema está **correta** ou **incorreta**. A resposta correta já está definida no banco de dados. Compare a resposta do usuário com a resposta esperada, garantindo que **o raciocínio lógico esteja correto**. "

    @staticmethod
    def _evaluate_short_explanations() -> str:
        return "Avalie a resposta do usuário para a situação-problema proposta. "

    @staticmethod
    def _evaluate_themed_short_explanations() -> str:
        return "Avalie a resposta do usuário para a situação-problema proposta. A resposta da questão encontra-se no conteúdo fornecido."

    def _load_txt_to_chroma(self, collection_name, chunk_size=2000):
        try:
            collection = self.chroma_client.create_collection(
                name=collection_name,
            )

            with open(
                CURRENT_DIR / f"themes/{collection_name}", encoding="utf-8"
            ) as file:
                text = file.read().strip()

            chunks = textwrap.wrap(text, width=chunk_size, break_long_words=False)
            collection.add(
                documents=chunks,
                ids=[f"{collection_name}_{i}" for i in range(len(chunks))],
            )

            self.collections[collection_name] = collection
        except Exception:
            self.collections[collection_name] = self.chroma_client.get_collection(
                name=collection_name
            )

    def _process_collection(self, collection_name: str, user_input: str | None = None):
        self._load_txt_to_chroma(collection_name)
        if user_input:
            # Obter o número de documentos disponíveis
            collection_count = self.collections[collection_name].count()
            # Usar o mínimo entre 5 e o número disponível para evitar erro
            n_results = min(5, collection_count) if collection_count > 0 else 1
            results = self.collections[collection_name].query(
                query_texts=[user_input], n_results=n_results
            )
            return results["documents"][0]
        else:
            results = self.collections[collection_name].get(include=["documents"])
            return results["documents"]
