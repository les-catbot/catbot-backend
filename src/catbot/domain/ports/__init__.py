from catbot.domain.ports.avaliacao_repository import AvaliacaoRepository
from catbot.domain.ports.conversa_repository import ConversaRepository
from catbot.domain.ports.documento_repository import DocumentoRepository
from catbot.domain.ports.llm_client import LLMClient
from catbot.domain.ports.nlp_processor import NLPProcessor, NLPResult
from catbot.domain.ports.usuario_repository import UsuarioRepository

__all__ = [
    "AvaliacaoRepository",
    "ConversaRepository",
    "DocumentoRepository",
    "LLMClient",
    "NLPProcessor",
    "NLPResult",
    "UsuarioRepository",
]
