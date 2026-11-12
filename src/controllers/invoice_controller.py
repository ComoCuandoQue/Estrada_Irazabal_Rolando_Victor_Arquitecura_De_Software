"""
Controlador MVC: Recibe solicitudes de la Vista/CLI, traduce los datos a entidades de entrada
e invoca el Caso de Uso del Modelo sin conocer detalles de lxml ni de XSD.
"""

from pathlib import Path
from typing import List, Optional
from ..core_model.application.ports import GeneratedUblXmlArtifact
from ..core_model.application.use_cases import IssueElectronicInvoiceUseCase
from ..core_model.domain.entities import (
    InvoiceLineInput,
    PartyInfo,
    PaymentTermsInfo,
)


class InvoiceMvcController:
    """Controlador de la capa de Presentación/Orquestación en el patrón MVC Limpio."""

    def __init__(self, use_case: IssueElectronicInvoiceUseCase) -> None:
        self._use_case = use_case

    def issue_and_export_xml(
        self,
        output_dir: Path,
        document_type_cat01: str,
        operation_type_cat51: str,
        series: str,
        correlative: int,
        issue_date: str,
        issue_time: str,
        currency_code_cat02: str,
        supplier: PartyInfo,
        customer: PartyInfo,
        payment_terms: PaymentTermsInfo,
        items: List[InvoiceLineInput],
        due_date: Optional[str] = None,
    ) -> GeneratedUblXmlArtifact:
        artifact = self._use_case.execute(
            document_type_cat01=document_type_cat01,
            operation_type_cat51=operation_type_cat51,
            series=series,
            correlative=correlative,
            issue_date=issue_date,
            issue_time=issue_time,
            due_date=due_date,
            currency_code_cat02=currency_code_cat02,
            supplier=supplier,
            customer=customer,
            payment_terms=payment_terms,
            raw_items=items,
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        out_file = output_dir / artifact.xml_filename
        out_file.write_text(artifact.xml_content, encoding="utf-8")
        return artifact
