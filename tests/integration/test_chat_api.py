from uuid import uuid4

from httpx import AsyncClient


class TestChatEndpoints:
    async def test_perguntar_em_conversa_inexistente_retorna_404(
        self,
        client: AsyncClient,
    ):
        response = await client.post(
            "/api/v1/chat/perguntar",
            json={
                "conversa_id": str(uuid4()),
                "texto": "teste",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Conversa não encontrada."
