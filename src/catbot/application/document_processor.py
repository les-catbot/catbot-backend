import fitz  # PyMuPDF

class DocumentProcessor:
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Lê os bytes de um arquivo PDF e extrai todo o texto contido nele."""
        text = ""
        # Abre o PDF diretamente da memória (sem salvar no disco)
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text