import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tools.pedagogical_recommendations import query_pedagogical_recommendations

@pytest.mark.asyncio
async def test_query_recommendations_unauthenticated(mock_tool_context_unauthenticated):
    """Verifies that unauthenticated sessions are blocked."""
    result = await query_pedagogical_recommendations(
        pedagogical_approach="Consciência fonêmica",
        tool_context=mock_tool_context_unauthenticated
    )
    assert result["success"] is False
    assert "Access Denied" in result["error"]

@pytest.mark.asyncio
@patch("tools.pedagogical_recommendations.get_bq_client")
@patch("tools.pedagogical_recommendations.get_db_connection")
async def test_query_recommendations_teacher_scope(
    mock_db_connection,
    mock_bq_client,
    mock_tool_context_teacher
):
    """Verifies that teachers can only view students within their allowed organizations and groups."""
    # Mock BigQuery Client & Results
    mock_bq_instance = MagicMock()
    mock_bq_client.return_value = mock_bq_instance
    mock_query_job = MagicMock()
    mock_bq_instance.query.return_value = mock_query_job
    
    # Mock BigQuery returning one student
    mock_query_job.result.return_value = [
        MagicMock(items=lambda: [
            ("student_uuid", "student-111"),
            ("student_name", "João Silva"),
            ("class_grade", "2º Ano"),
            ("user_rating", "Pré-leitor 2"),
            ("response_amount_hits", 2),
            ("question_amount_words", 10),
            ("question_text", "casa bola pato"),
            ("response_text", "c-a-s-a b-o-l-a")
        ])
    ]

    # Mock DB Connection (PostgreSQL)
    mock_conn = AsyncMock()
    mock_db_connection.return_value = (mock_conn, None)
    
    # Mock SQL Query returning raw transcription
    file_id = "doc-uuid-999"
    mock_conn.fetch.return_value = [
        {
            "file_id": file_id,
            "filename": "guia_consciencia_fonemica.pdf",
            "description": "Atividades de fonemas",
            "transcription": "Texto completo do guia: Exercício 1: Repita o fonema /s/... Exercício 2: Soletrar..."
        }
    ]

    # Call tool
    result = await query_pedagogical_recommendations(
        pedagogical_approach="Consciência fonêmica",
        class_name="2º Ano A",
        tool_context=mock_tool_context_teacher
    )

    # Assertions
    assert result["success"] is True
    assert len(result["students"]) == 1
    assert result["students"][0]["student_name"] == "João Silva"
    
    # Verify BigQuery filters were populated correctly matching the teacher's allowed scope
    mock_bq_instance.query.assert_called_once()
    called_sql = mock_bq_instance.query.call_args[0][0]
    
    # Check that school_uuid and class_uuid parameters were passed
    assert "school_uuid IN UNNEST" in called_sql
    assert "class_uuid IN UNNEST" in called_sql

    # Verify DB Search was called
    mock_conn.fetch.assert_called_once()
    called_db_sql = mock_conn.fetch.call_args[0][0]
    called_db_params = mock_conn.fetch.call_args[0][1]
    
    assert "knowledge_base_files" in called_db_sql
    assert "filename ILIKE" in called_db_sql
    assert called_db_params == "%Consciência fonêmica%"

    # Verify final result contains the material and transcription
    assert len(result["materials"]) == 1
    assert result["materials"][0]["filename"] == "guia_consciencia_fonemica.pdf"
    assert "Exercício 1: Repita o fonema" in result["materials"][0]["transcription"]
    assert result["vector_chunks"] == []

@pytest.mark.asyncio
@patch("tools.pedagogical_recommendations.get_bq_client")
@patch("tools.pedagogical_recommendations.get_db_connection")
async def test_query_recommendations_admin_scope(
    mock_db_connection,
    mock_bq_client,
    mock_tool_context_admin
):
    """Verifies that administrators are unrestricted by allowed orgs/groups."""
    mock_bq_instance = MagicMock()
    mock_bq_client.return_value = mock_bq_instance
    mock_query_job = MagicMock()
    mock_bq_instance.query.return_value = mock_query_job
    mock_query_job.result.return_value = []

    mock_conn = AsyncMock()
    mock_db_connection.return_value = (mock_conn, None)
    mock_conn.fetch.return_value = []

    # Call tool
    result = await query_pedagogical_recommendations(
        pedagogical_approach="Consciência fonêmica",
        tool_context=mock_tool_context_admin
    )

    assert result["success"] is True
    # BigQuery was queried
    mock_bq_instance.query.assert_called_once()
    called_sql = mock_bq_instance.query.call_args[0][0]
    
    # Check that school_uuid/class_uuid UNNEST check is NOT in SQL for admin
    assert "school_uuid IN UNNEST" not in called_sql
    assert "class_uuid IN UNNEST" not in called_sql
