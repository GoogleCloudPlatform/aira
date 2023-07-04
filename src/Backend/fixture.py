"""
Fixtures for the database.
"""
import asyncio
import datetime

from api import create_container, errors, models, ports
from api.helpers import time_now


async def insert_models(uow: ports.UnitOfWork):
    """
    Inserting all models.
    """
    role = await uow.role_repository.get(name="admin")
    role_user = await uow.role_repository.get(name="user")
    role_semi = await uow.role_repository.get(name="professor")

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
        grade=models.Grades.FIRST_FUND,
        shift="morning",
    )
    group2 = models.Group(
        customer_id=None,
        name="teste2",
        organization_id=org2.id,
        grade=models.Grades.FIRST_FUND,
        shift="evening",
    )
    test_user1 = models.User(
        external_id=None,
        customer_id=None,
        type=models.UserType.PASSWORD,
        name="Teste Admin",
        email_address="admin@radhark.tech",
        role_id=role.id,
        groups=[],
        organizations=[],
    )
    test_user1.password = "$2b$12$Vz6ThPIN30KSOl6Q6fOFIeh58fbx1D4YF6Pt9YJQLt3n6JRJv0NNO"
    test_user2 = models.User(
        external_id="8Esm3VnAFhXUAhspjb54SE0qvsC3",
        customer_id=None,
        type=models.UserType.FIREBASE,
        name="Rodrigo Werneck",
        email_address="werneck@radhark.tech",
        role_id=role.id,
        groups=[],
        organizations=[],
    )
    test_user3 = models.User(
        external_id=None,
        customer_id=None,
        type=models.UserType.PASSWORD,
        name="Teste Aluno",
        email_address="aluno@radhark.tech",
        role_id=role_user.id,
        groups=[group],
        organizations=[org1],
    )
    test_user3.password = "$2b$12$Vz6ThPIN30KSOl6Q6fOFIeh58fbx1D4YF6Pt9YJQLt3n6JRJv0NNO"
    test_user4 = models.User(
        external_id=None,
        customer_id=None,
        type=models.UserType.PASSWORD,
        name="Teste Professor",
        email_address="professor@radhark.tech",
        role_id=role_semi.id,
        groups=[group],
        organizations=[org1],
    )
    test_user4.password = "$2b$12$Vz6ThPIN30KSOl6Q6fOFIeh58fbx1D4YF6Pt9YJQLt3n6JRJv0NNO"
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
            ),
            models.Question(
                name="Leitura de frases",
                type=models.QuestionType.PHRASES,
                phrase_id="f0440ba0-7cbb-4100-b5f3-1a1f6d152dad",
                data="Eu tinha uma galinha. Ela se chamava Marilu.",
            ),
        ],
        start_date=time_now(),
        end_date=time_now() + datetime.timedelta(days=30),
        grade=group.grade,
    )

    await uow.organization_repository.create(org1)
    await uow.organization_repository.create(org2)
    await uow.group_repository.create(group)
    await uow.group_repository.create(group2)
    await uow.user_repository.create(test_user1)
    await uow.user_repository.create(test_user2)
    await uow.user_repository.create(test_user3)
    await uow.user_repository.create(test_user4)
    await uow.user_repository.create(exam)


async def main():
    """
    Startup of db fixtures.
    """
    container = create_container()
    uow_builder = container.get(ports.UnitOfWorkBuilder)
    async with uow_builder() as uow:
        try:
            await insert_models(uow)

            await uow.commit()
        except errors.AlreadyExists:
            pass


if __name__ == "__main__":
    asyncio.run(main())
