"""
Fixtures for the database.
"""
import asyncio
import datetime
import os
from pathlib import Path
import textwrap

import chromadb
from chromadb.utils import embedding_functions

import sqlalchemy as sa
from api import create_container, errors, models, ports
from api.helpers import time_now


async def insert_models(uow: ports.UnitOfWork) -> None:
    """
    Inserting all models.
    """
    role = await uow.role_repository.get(name="admin")
    role_user = await uow.role_repository.get(name="user")
    role_semi = await uow.role_repository.get(name="professor")

    # Fetch series dynamically
    res_series = await uow._session.execute(sa.text("SELECT id, name FROM series"))
    series_map = {row.name: row.id for row in res_series.all()}

    # Fetch shifts dynamically
    res_shifts = await uow._session.execute(sa.text("SELECT id, name FROM work_shifts"))
    shifts_map = {row.name: row.id for row in res_shifts.all()}

    def get_series_id(grade_enum):
        val = grade_enum.value
        if val in series_map:
            return series_map[val]
        if "3ª Série" in val or "3ª" in val:
            return series_map.get("3º Ano") or list(series_map.values())[0]
        return list(series_map.values())[0]

    def get_shift_id(shift_str):
        mapping = {
            "morning": "Manhã",
            "evening": "Noite",
            "afternoon": "Tarde",
            "allday": "Integral"
        }
        name = mapping.get(shift_str, "Manhã")
        return shifts_map.get(name) or list(shifts_map.values())[0]
    
    senai = models.Organization(
        customer_id=None,
        region="DF",
        name="Escola Senai",
        city="DF",
        state="DF",
    )
    senai_group = models.Group(
        customer_id=None,
        name="Senai 3EM",
        organization_id=senai.id,
        series_id=get_series_id(models.Grades.THIRD_HS),
        shift_id=get_shift_id("morning"),
    )

    org1 = models.Organization(
        customer_id=None,
        region="teste",
        name="teste",
        city="teste",
        state="RJ",
    )
    org2 = models.Organization(
        customer_id=None,
        region="teste",
        name="teste2",
        city="teste",
        state="RJ",
    )
    group = models.Group(
        customer_id=None,
        name="teste",
        organization_id=org1.id,
        series_id=get_series_id(models.Grades.FIRST_FUND),
        shift_id=get_shift_id("morning"),
    )
    group2 = models.Group(
        customer_id=None,
        name="teste2",
        organization_id=org2.id,
        series_id=get_series_id(models.Grades.SECOND_FUND),
        shift_id=get_shift_id("evening"),
    )
    test_user1 = models.User(
        external_id=None,
        customer_id=None,
        type=models.UserType.PASSWORD,
        name="Teste Admin",
        email_address="gustavo@radhark.tech",
        role_id=role.id,
        region=None,
        state=None,
    )
    test_user1._password = "$2b$12$Kp735KKvJawJxkpAcmb2xO/3dTWi8LLUt1IOR3SWl2x6eThukKmvy"
    test_user2 = models.User(
        external_id=None,
        customer_id=None,
        type=models.UserType.FIREBASE,
        name="Rodrigo Werneck",
        email_address="werneck@radhark.tech",
        role_id=role.id,
        region=None,
        state=None,
    )
    test_user3 = models.User(
        external_id=None,
        customer_id=None,
        type=models.UserType.PASSWORD,
        name="Teste Aluno",
        email_address="aluno@radhark.tech",
        role_id=role_user.id,
        region=None,
        state=None,
    )
    test_user3.groups.append(senai_group)
    test_user3.organizations.append(senai)
    test_user3._password = "$2b$12$Kp735KKvJawJxkpAcmb2xO/3dTWi8LLUt1IOR3SWl2x6eThukKmvy"
    test_user4 = models.User(
        external_id=None,
        customer_id=None,
        type=models.UserType.PASSWORD,
        name="Teste Professor",
        email_address="professor@radhark.tech",
        role_id=role_semi.id,
        region=None,
        state=None,
    )
    test_user4.groups.append(senai_group)
    test_user4.organizations.append(senai)
    test_user4._password = "$2b$12$Kp735KKvJawJxkpAcmb2xO/3dTWi8LLUt1IOR3SWl2x6eThukKmvy"
    exam = models.Exam(
        name="Test Exam",
        questions=[
            models.Question(
                name="Leitura de palavras",
                phrase_id="49c68868-324e-45a7-98f0-bfcc6588e2ec",
                type=models.QuestionType.WORDS,
                data=(
                    "AVENIDA LONA FERRÃO CABELO RIO BOLADA DELEGADO ROUXINOL "
                    "FOGUEIRA PETECA ESPADA NEVE VIOLA MOÇO BARRIGA VELHO TOMADA "
                    "REI AMOSTRA FAIXA FILHOTE BANHEIRO PALITO SECA PLUMA PÉ FIGURA "
                    "NOVELA NINHO SAPATO UVA TOUCA EXEMPLO FIVELA MARIDO BONÉ CABIDE "
                    "LEI ABELHA BELICHE MIL VÉU FOLIA DOMINÓ COMETA CUBO ÚLTIMO TOMATE "
                    "CHÃO FAROFA COLMEIA XÍCARA REDE CARAVELA ALVO FADA MEL PLATEIA "
                    "BIGODE GIRAFA OURO BERRO PEQUENO COLEIRA CÉU VICE REINO IGUAL "
                    "PAU DÚVIDA PILHA OUVIDO MANHÃ MEIO FAROL SALADA MARRECO BICO "
                    "PORTA SESSENTA"
                ),
                formatted_data=(
                    "AVENIDA LONA FERRÃO CABELO RIO BOLADA DELEGADO ROUXINOL "
                    "FOGUEIRA PETECA ESPADA NEVE VIOLA MOÇO BARRIGA VELHO TOMADA "
                    "REI AMOSTRA FAIXA FILHOTE BANHEIRO PALITO SECA PLUMA PÉ FIGURA "
                    "NOVELA NINHO SAPATO UVA TOUCA EXEMPLO FIVELA MARIDO BONÉ CABIDE "
                    "LEI ABELHA BELICHE MIL VÉU FOLIA DOMINÓ COMETA CUBO ÚLTIMO TOMATE "
                    "CHÃO FAROFA COLMEIA XÍCARA REDE CARAVELA ALVO FADA MEL PLATEIA "
                    "BIGODE GIRAFA OURO BERRO PEQUENO COLEIRA CÉU VICE REINO IGUAL "
                    "PAU DÚVIDA PILHA OUVIDO MANHÃ MEIO FAROL SALADA MARRECO BICO "
                    "PORTA SESSENTA"
                ),
                order=1,
                answers=[],
                theme=None,
            ),
            models.Question(
                name="Leitura de frases",
                type=models.QuestionType.PHRASES,
                phrase_id="f0440ba0-7cbb-4100-b5f3-1a1f6d152dad",
                data="Eu tinha uma galinha. Ela se chamava Marilu.",
                formatted_data="Eu tinha uma galinha. Ela se chamava Marilu.",
                order=2,
                answers=[],
                theme=None,
            ),
        ],
        start_date=time_now(),
        end_date=time_now() + datetime.timedelta(days=30),
        grade=models.Grades.FIRST_FUND,
    )
    exam_two = models.Exam(
        name="Test Exam 2",
        questions=[
            models.Question(
                name="Leitura de palavras",
                phrase_id="49c68868-324e-45a7-98f0-bfcc6588e2ec",
                type=models.QuestionType.WORDS,
                data=(
                    "AVENIDA LONA FERRÃO CABELO RIO BOLADA DELEGADO ROUXINOL "
                    "FOGUEIRA PETECA ESPADA NEVE VIOLA MOÇO BARRIGA VELHO TOMADA "
                    "REI AMOSTRA FAIXA FILHOTE BANHEIRO PALITO SECA PLUMA PÉ FIGURA "
                    "NOVELA NINHO SAPATO UVA TOUCA EXEMPLO FIVELA MARIDO BONÉ CABIDE "
                    "LEI ABELHA BELICHE MIL VÉU FOLIA DOMINÓ COMETA CUBO ÚLTIMO TOMATE "
                    "CHÃO FAROFA COLMEIA XÍCARA REDE CARAVELA ALVO FADA MEL PLATEIA "
                    "BIGODE GIRAFA OURO BERRO PEQUENO COLEIRA CÉU VICE REINO IGUAL "
                    "PAU DÚVIDA PILHA OUVIDO MANHÃ MEIO FAROL SALADA MARRECO BICO "
                    "PORTA SESSENTA"
                ),
                order=1,
                formatted_data=(
                    "AVENIDA LONA FERRÃO CABELO RIO BOLADA DELEGADO ROUXINOL "
                    "FOGUEIRA PETECA ESPADA NEVE VIOLA MOÇO BARRIGA VELHO TOMADA "
                    "REI AMOSTRA FAIXA FILHOTE BANHEIRO PALITO SECA PLUMA PÉ FIGURA "
                    "NOVELA NINHO SAPATO UVA TOUCA EXEMPLO FIVELA MARIDO BONÉ CABIDE "
                    "LEI ABELHA BELICHE MIL VÉU FOLIA DOMINÓ COMETA CUBO ÚLTIMO TOMATE "
                    "CHÃO FAROFA COLMEIA XÍCARA REDE CARAVELA ALVO FADA MEL PLATEIA "
                    "BIGODE GIRAFA OURO BERRO PEQUENO COLEIRA CÉU VICE REINO IGUAL "
                    "PAU DÚVIDA PILHA OUVIDO MANHÃ MEIO FAROL SALADA MARRECO BICO "
                    "PORTA SESSENTA"
                ),
                answers=[],
                theme=None,
            ),
            models.Question(
                name="Leitura de frases",
                type=models.QuestionType.PHRASES,
                phrase_id="f0440ba0-7cbb-4100-b5f3-1a1f6d152dad",
                data="Eu tinha uma galinha. Ela se chamava Marilu.",
                formatted_data="Eu tinha uma galinha. Ela se chamava Marilu.",
                order=2,
                answers=[],
                theme=None,
            ),
        ],
        start_date=time_now(),
        end_date=time_now() + datetime.timedelta(days=4),
        grade=models.Grades.FIRST_FUND,
    )
    exam_three = models.Exam(
        name="Prova completa",
        questions=[
            models.Question(
                name="Palavras simples",
                phrase_id="49c68868-324e-45a7-98f0-bfcc6588e2ec",
                type=models.QuestionType.WORDS,
                data=(
                    "AVENIDA LONA FERRÃO CABELO RIO BOLADA DELEGADO ROUXINOL "
                    "FOGUEIRA PETECA ESPADA NEVE VIOLA MOÇO BARRIGA VELHO TOMADA "
                    "REI AMOSTRA FAIXA FILHOTE BANHEIRO PALITO SECA PLUMA PÉ FIGURA "
                    "NOVELA NINHO SAPATO UVA TOUCA EXEMPLO FIVELA MARIDO BONÉ CABIDE "
                    "LEI ABELHA BELICHE MIL VÉU FOLIA DOMINÓ COMETA CUBO ÚLTIMO TOMATE "
                    "CHÃO FAROFA COLMEIA XÍCARA REDE CARAVELA ALVO FADA MEL PLATEIA "
                    "BIGODE GIRAFA OURO BERRO PEQUENO COLEIRA CÉU VICE REINO IGUAL "
                    "PAU DÚVIDA PILHA OUVIDO MANHÃ MEIO FAROL SALADA MARRECO BICO "
                    "PORTA SESSENTA"
                ),
                order=1,
                formatted_data=(
                    "AVENIDA LONA FERRÃO CABELO RIO BOLADA DELEGADO ROUXINOL "
                    "FOGUEIRA PETECA ESPADA NEVE VIOLA MOÇO BARRIGA VELHO TOMADA "
                    "REI AMOSTRA FAIXA FILHOTE BANHEIRO PALITO SECA PLUMA PÉ FIGURA "
                    "NOVELA NINHO SAPATO UVA TOUCA EXEMPLO FIVELA MARIDO BONÉ CABIDE "
                    "LEI ABELHA BELICHE MIL VÉU FOLIA DOMINÓ COMETA CUBO ÚLTIMO TOMATE "
                    "CHÃO FAROFA COLMEIA XÍCARA REDE CARAVELA ALVO FADA MEL PLATEIA "
                    "BIGODE GIRAFA OURO BERRO PEQUENO COLEIRA CÉU VICE REINO IGUAL "
                    "PAU DÚVIDA PILHA OUVIDO MANHÃ MEIO FAROL SALADA MARRECO BICO "
                    "PORTA SESSENTA"
                ),
                answers=[],
                theme=None,
            ),
            models.Question(
                name="Palavras Complexas",
                type=models.QuestionType.COMPLEX_WORDS,
                phrase_id="f0440ba0-7cbb-4100-b5f3-1a1f6d152dad",
                data=(
                    "Paradoxo Efêmero Polissílabo Anacrônico Onomatopeia Metamorfose "
                    "Antropomorfismo Inexorável Inefável Perspicaz Desassossego "
                    "Perplexidade Incongruência Obsolescência Trivialidade Melancolia "
                    "Intrínseco Inóspito Obstinado Dicotomia Anátema Desvelar "
                    "Concomitante Incólume Escárnio Intransigente Parcimônia "
                    "Procrastinação Inusitado Inconteste Arbitrariedade Aviltante "
                    "Obsequioso Insólito Vicissitude Íntegro Perene Retrógrado Dissimulado "
                    "Peregrinação Condescendência Magnânimo Escrutínio Ludibriar Proeminente "
                    "Incisivo Labiríntico Inconspícuo Exacerbado Infausto Paradoxalidade "
                    "Austeridade Peremptório Vetusto Iniquidade Sublime Reticente "
                    "Conjetura Consoante Contundente"
                ),
                formatted_data=(
                    "Paradoxo Efêmero Polissílabo Anacrônico Onomatopeia Metamorfose "
                    "Antropomorfismo Inexorável Inefável Perspicaz Desassossego "
                    "Perplexidade Incongruência Obsolescência Trivialidade Melancolia "
                    "Intrínseco Inóspito Obstinado Dicotomia Anátema Desvelar "
                    "Concomitante Incólume Escárnio Intransigente Parcimônia "
                    "Procrastinação Inusitado Inconteste Arbitrariedade Aviltante "
                    "Obsequioso Insólito Vicissitude Íntegro Perene Retrógrado Dissimulado "
                    "Peregrinação Condescendência Magnânimo Escrutínio Ludibriar Proeminente "
                    "Incisivo Labiríntico Inconspícuo Exacerbado Infausto Paradoxalidade "
                    "Austeridade Peremptório Vetusto Iniquidade Sublime Reticente "
                    "Conjetura Consoante Contundente"
                ),
                order=2,
                answers=[],
                theme=None,
            ),
            models.Question(
                name="Texto Narrativo",
                type=models.QuestionType.PHRASES,
                phrase_id="f0440ba0-7cbb-4100-b5f3-1a1f6d152dad",
                data='''
                Era uma vez, uma menina que adorava explorar a floresta atrás de sua casa.
                Um dia, encontrou um cachorrinho perdido com pelo marrom e olhos brilhantes.
                Ela decidiu ajudar o cachorrinho a encontrar o caminho de volta para casa.
                Os dois caminharam juntos pela floresta, passando por árvores altas e riachos brilhantes.
                Enquanto procuravam, a menina e o cachorrinho brincaram de correr e pular sobre as pedras.
                A menina deu água ao cachorrinho e um pedaço de pão que tinha na mochila. Depois de algum tempo,
                ouviram um latido distante. Seguiram o som e encontraram a mãe do cachorrinho,
                que ficou muito feliz e lambeu a menina.
                A menina voltou para casa contente por ter feito dois novos amigos.
                ''',
                formatted_data='''
                Era uma vez, uma menina que adorava explorar a floresta atrás de sua casa.
                Um dia, encontrou um cachorrinho perdido com pelo marrom e olhos brilhantes.
                Ela decidiu ajudar o cachorrinho a encontrar o caminho de volta para casa.
                Os dois caminharam juntos pela floresta, passando por árvores altas e riachos brilhantes.
                Enquanto procuravam, a menina e o cachorrinho brincaram de correr e pular sobre as pedras.
                A menina deu água ao cachorrinho e um pedaço de pão que tinha na mochila. Depois de algum tempo,
                ouviram um latido distante. Seguiram o som e encontraram a mãe do cachorrinho,
                que ficou muito feliz e lambeu a menina.
                A menina voltou para casa contente por ter feito dois novos amigos.
                ''',
                order=3,
                answers=[],
                theme=None,
            ),
        ],
        start_date=time_now(),
        end_date=time_now() + datetime.timedelta(days=30),
        grade=models.Grades.THIRD_HS,
    )

    await uow.organization_repository.create(senai)
    await uow.group_repository.create(senai_group)
    
    await uow.organization_repository.create(org1)
    await uow.organization_repository.create(org2)
    await uow.group_repository.create(group)
    await uow.group_repository.create(group2)
    await uow.user_repository.create(test_user1)
    await uow.user_repository.create(test_user2)
    await uow.user_repository.create(test_user3)
    await uow.user_repository.create(test_user4)
    await uow.user_repository.create(exam)
    await uow.user_repository.create(exam_two)
    await uow.user_repository.create(exam_three)


def create_chroma_collections() -> None:
    api_key = os.getenv("_GEMINI_API_KEY")
    if not api_key:
        raise Exception("api key vazia")
    CURRENT_DIR = Path(__file__).resolve().parent
    chroma_client = chromadb.PersistentClient(path="./chroma_data")
    for collection_name in ["alimentos_e_bebidas.txt", "eletroeletronica.txt", "materiais_nao_metalicos.txt", "telecomunicacoes.txt", "ti_software.txt"]:
        try:
            collection = chroma_client.create_collection(
                name=collection_name,
            )
            with open(CURRENT_DIR / f"src/api/adapters/google/themes/{collection_name}", 'r', encoding='utf-8') as file:
                text = file.read().strip()
                
            chunks = textwrap.wrap(text, width=2000, break_long_words=False)
            collection.add(
                documents=chunks,
                ids=[f"{collection_name}_{i}" for i in range(len(chunks))]
            )
        except Exception:
            pass

async def main() -> None:
    """
    Startup of db fixtures.
    """
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k] = v.strip().strip('"').strip("'")

    container = create_container()
    uow_builder = container.get(ports.UnitOfWorkBuilder)
    async with uow_builder() as uow:
        try:
            await insert_models(uow)

            await uow.commit()
        except errors.AlreadyExists:
            pass
    
    create_chroma_collections()


if __name__ == "__main__":
    asyncio.run(main())