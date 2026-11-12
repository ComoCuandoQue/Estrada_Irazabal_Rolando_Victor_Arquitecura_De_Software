"""
Caso de Uso de Aplicación: Emisión, Generación XML UBL 2.1 y Validación XSD.
Orquesta el dominio tributario e invoca los Puertos de Salida sin acoplarse a detalles técnicos.
"""

from typing import List, Optional
from ..domain.entities import (
    ElectronicInvoiceDocument,
    InvoiceLineInput,
    PartyInfo,
    PaymentTermsInfo,
)
from ..domain.ruc_validator import SunatRucValidator
from ..domain.tax_engine import SunatTaxCalculationEngine, round2
from .ports import (
    GeneratedUblXmlArtifact,
    IUblInvoiceXmlGeneratorPort,
    IXsdSchemaValidatorPort,
)


class IssueElectronicInvoiceUseCase:
    """Caso de Uso principal invocado por el Controlador MVC."""

    def __init__(
        self,
        xml_generator_port: IUblInvoiceXmlGeneratorPort,
        xsd_validator_port: IXsdSchemaValidatorPort,
    ) -> None:
        self._xml_generator = xml_generator_port
        self._xsd_validator = xsd_validator_port

    def execute(
        self,
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
        raw_items: List[InvoiceLineInput],
        due_date: Optional[str] = None,
    ) -> GeneratedUblXmlArtifact:
        # 1. Validar RUC del Emisor (ABC Software Corp)
        is_sup_ok, sup_msg = SunatRucValidator.validate_ruc_mod11(supplier.identity_doc_number)
        if not is_sup_ok:
            raise ValueError(f"[Error Normativo Emisor] {sup_msg}")

        if not raw_items:
            raise ValueError("[Error Dominio] El comprobante debe contener al menos un ítem.")

        # 2. Calcular líneas e impuestos multicapa (IGV, Catálogo 08 ISC, ICBPER, Gratuitas)
        calculated_lines = [
            SunatTaxCalculationEngine.calculate_line(idx + 1, item)
            for idx, item in enumerate(raw_items)
        ]

        # 3. Consolidar totales del documento
        (
            global_tax_total,
            global_subtotals,
            monetary_total,
            has_free_lines,
        ) = SunatTaxCalculationEngine.consolidate_document_totals(calculated_lines)

        # 4. Validar identificación del cliente según Catálogo 01 y tope S/ 700.00
        is_cust_ok, cust_msg = SunatRucValidator.validate_customer_for_document(
            document_type_cat01=document_type_cat01,
            series=series,
            customer_doc_type_cat06=customer.identity_doc_type_cat06,
            customer_doc_number=customer.identity_doc_number,
            payable_amount=monetary_total.payable_amount,
        )
        if not is_cust_ok:
            raise ValueError(f"[Error Normativo Cliente] {cust_msg}")

        # 5. Validar cuotas si es al Crédito (RS 193-2020/SUNAT)
        if payment_terms.condition == "Credito":
            if not payment_terms.installments:
                raise ValueError("[Error RS 193-2020] Factura al Crédito requiere al menos una cuota.")
            installments_sum = round2(sum(inst.amount for inst in payment_terms.installments))
            if installments_sum != monetary_total.payable_amount:
                raise ValueError(
                    f"[Error RS 193-2020] La suma de cuotas ({installments_sum}) no coincide con el importe total a pagar ({monetary_total.payable_amount})."
                )

        # 6. Construir la Entidad Raíz del Dominio
        document = ElectronicInvoiceDocument(
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
            lines=calculated_lines,
            global_tax_total_amount=global_tax_total,
            global_tax_subtotals=global_subtotals,
            legal_monetary_total=monetary_total,
            amount_in_words_legend=SunatTaxCalculationEngine.amount_to_words_pen(
                monetary_total.payable_amount
            ),
            has_free_transfer_legend=has_free_lines,
        )

        # 7. Invocar el Puerto Generador de XML UBL 2.1
        xml_content, digest_hash, qr_string = self._xml_generator.generate_invoice_xml(document)

        # 8. Invocar el Puerto Validador contra el esquema oficial UBL-Invoice-2.1.xsd
        is_valid_xsd, xsd_errors = self._xsd_validator.validate_against_ubl_invoice_xsd(xml_content)
        validation_msg = (
            "CONFORME: El documento XML cumple al 100% con el esquema OASIS UBL-Invoice-2.1.xsd"
            if is_valid_xsd
            else "ERRORES XSD: " + "; ".join(xsd_errors)
        )

        return GeneratedUblXmlArtifact(
            xml_filename=document.standard_xml_filename,
            xml_content=xml_content,
            digest_value_hash=digest_hash,
            qr_code_string=qr_string,
            is_xsd_valid=is_valid_xsd,
            xsd_validation_message=validation_msg,
            document=document,
        )
