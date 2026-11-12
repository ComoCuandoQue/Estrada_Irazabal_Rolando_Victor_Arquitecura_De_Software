"""
Puertos Arquitectónicos (Interfaces) de la Capa de Aplicación (MVC Desacoplado -> Hexagonal).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple
from ..domain.entities import ElectronicInvoiceDocument


@dataclass(frozen=True)
class GeneratedUblXmlArtifact:
    """Resultado de la generación y validación del XML UBL 2.1."""
    xml_filename: str
    xml_content: str
    digest_value_hash: str
    qr_code_string: str
    is_xsd_valid: bool
    xsd_validation_message: str
    document: ElectronicInvoiceDocument


class IUblInvoiceXmlGeneratorPort(ABC):
    """Puerto de Salida: Construye el documento XML conforme a OASIS UBL-Invoice-2.1.xsd."""

    @abstractmethod
    def generate_invoice_xml(
        self, document: ElectronicInvoiceDocument
    ) -> Tuple[str, str, str]:
        """Retorna (xml_content, digest_value_hash, qr_code_string)."""
        raise NotImplementedError


class IXsdSchemaValidatorPort(ABC):
    """Puerto de Salida: Valida estructuralmente un XML contra el archivo oficial UBL-Invoice-2.1.xsd."""

    @abstractmethod
    def validate_against_ubl_invoice_xsd(self, xml_content: str) -> Tuple[bool, List[str]]:
        """Retorna (is_valid, error_messages)."""
        raise NotImplementedError
