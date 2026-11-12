"""
Adaptador de Infraestructura: Validador de XML contra el esquema oficial OASIS UBL-Invoice-2.1.xsd.
Implementa el puerto IXsdSchemaValidatorPort cargando localmente xsd/maindoc/UBL-Invoice-2.1.xsd.
"""

from pathlib import Path
from typing import List, Optional, Tuple
from lxml import etree

from ..core_model.application.ports import IXsdSchemaValidatorPort


class OasisXsdSchemaValidatorAdapter(IXsdSchemaValidatorPort):
    """Carga y compila el archivo oficial UBL-Invoice-2.1.xsd para validar documentos XML UBL 2.1."""

    def __init__(self, xsd_path: Optional[Path] = None) -> None:
        if xsd_path is None:
            repo_root = Path(__file__).resolve().parents[2]
            xsd_path = repo_root / "xsd" / "maindoc" / "UBL-Invoice-2.1.xsd"
        self._xsd_path = xsd_path
        if not self._xsd_path.exists():
            raise FileNotFoundError(
                f"No se encontró el esquema XSD oficial en: {self._xsd_path}"
            )
        xml_schema_doc = etree.parse(str(self._xsd_path))
        self._schema = etree.XMLSchema(xml_schema_doc)

    @property
    def xsd_path(self) -> Path:
        return self._xsd_path

    def validate_against_ubl_invoice_xsd(self, xml_content: str) -> Tuple[bool, List[str]]:
        """Valida la estructura, orden de secuencias (<xs:sequence>), tipos y atributos del XML."""
        try:
            xml_doc = etree.fromstring(xml_content.encode("utf-8"))
        except etree.XMLSyntaxError as exc:
            return False, [f"Error de sintaxis XML: {exc}"]

        is_valid = self._schema.validate(xml_doc)
        if is_valid:
            return True, []

        errors = [
            f"Línea {err.line}: {err.message}"
            for err in self._schema.error_log
        ]
        return False, errors
