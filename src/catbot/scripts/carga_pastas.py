import os
import asyncio
import httpx
from pathlib import Path

# Configurações
DIRETORIO_BASE = r"C:\Users\victo\Downloads\Documentos"
API_URL = "http://localhost:8000/documentos/"
MAX_CONCORRENTES = 3  # Número máximo de PDFs enviados ao mesmo tempo (aumente se sua máquina for forte)


async def enviar_documento(client, caminho_arquivo, nome_arquivo, categoria, semaforo):
    # O semáforo limita quantas funções rodam esta parte ao mesmo tempo
    async with semaforo:
        print(f"[{categoria}] Iniciando: {nome_arquivo}...")

        data = {
            "titulo": nome_arquivo.replace(".pdf", ""),
            "categoria": categoria,  # Pega o nome da pasta automaticamente!
            "fonte": "Carga em Lote (Script)"
        }

        with open(caminho_arquivo, "rb") as f:
            files = {"arquivo": (nome_arquivo, f, "application/pdf")}
            try:
                # Timeout alto (120s) porque processar PDF e vetorizar pode demorar
                response = await client.post(API_URL, data=data, files=files, timeout=120.0)

                if response.status_code == 201:
                    print(f"✅ Sucesso: {nome_arquivo} indexado na categoria '{categoria}'!")
                else:
                    print(f"❌ Erro ao enviar {nome_arquivo}: Status {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Falha de conexão ao enviar {nome_arquivo}: {str(e)}")


async def main():
    caminho_base = Path(DIRETORIO_BASE)

    if not caminho_base.exists() or not caminho_base.is_dir():
        print(f"Erro: A pasta {DIRETORIO_BASE} não existe.")
        return

    tarefas = []
    semaforo = asyncio.Semaphore(MAX_CONCORRENTES)

    # httpx.AsyncClient reaproveita conexões, deixando o processo muito mais rápido
    async with httpx.AsyncClient() as client:
        # Itera sobre todas as pastas dentro de DIRETORIO_BASE
        for pasta_categoria in caminho_base.iterdir():
            if pasta_categoria.is_dir():
                categoria_nome = pasta_categoria.name  # "rod", "resolucoes", "portarias"

                # Itera sobre os PDFs dentro daquela pasta
                for arquivo_pdf in pasta_categoria.glob("*.pdf"):
                    tarefas.append(
                        enviar_documento(
                            client=client,
                            caminho_arquivo=arquivo_pdf,
                            nome_arquivo=arquivo_pdf.name,
                            categoria=categoria_nome.capitalize(),  # Ex: "Portarias"
                            semaforo=semaforo
                        )
                    )

        total_arquivos = len(tarefas)
        if total_arquivos == 0:
            print("Nenhum arquivo PDF encontrado nas subpastas.")
            return

        print(f"Iniciando carga de {total_arquivos} documentos...")

        # Executa todas as tarefas (respeitando o limite do semáforo)
        await asyncio.gather(*tarefas)

    print("\n🚀 Carga de documentos finalizada com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())