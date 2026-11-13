"""
Demostración Ejecutable: Generación de XML a partir del Modelo de Dominio y Validación
contra el esquema oficial OASIS UBL-Invoice-2.1.xsd para ABC Software Corp.
"""

from decimal import Decimal
from pathlib import Path

from .controllers.invoice_controller import InvoiceMvcController
from .core_model.application.use_cases import IssueElectronicInvoiceUseCase
from .core_model.domain.entities import (
    InstallmentInfo,
    InvoiceLineInput,
    IscConfiguration,
    PartyInfo,
    PaymentTermsInfo,
)
from .infrastructure_adapters.ubl21_xml_generator import OasisUbl21XmlGeneratorAdapter
from .infrastructure_adapters.xsd_schema_validator import OasisXsdSchemaValidatorAdapter


def build_abc_supplier() -> PartyInfo:
    """Emisor oficial: ABC Software Corp S.A.C. (RUC 20555999110 válido en Módulo 11)."""
    return PartyInfo(
        identity_doc_type_cat06="6",
        identity_doc_number="20555999110",
        legal_name="ABC SOFTWARE CORP S.A.C.",
        trade_name="ABC DISTRIBUIDORA MAYORISTA Y MINORISTA DE ABARROTES",
        ubigeo_cat13="150101",
        establishment_code="0000",
        address_line="AV. NICOLAS AYLLON 2450 - LIMA",
        country_code="PE",
    )


def run_demo() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / "output"

    # Inyección de Dependencias (Puertos -> Adaptadores) en el patrón MVC Desacoplado
    xml_generator_adapter = OasisUbl21XmlGeneratorAdapter()
    xsd_validator_adapter = OasisXsdSchemaValidatorAdapter()
    use_case = IssueElectronicInvoiceUseCase(
        xml_generator_port=xml_generator_adapter,
        xsd_validator_port=xsd_validator_adapter,
    )
    controller = InvoiceMvcController(use_case=use_case)
    supplier = build_abc_supplier()

    print("=" * 88)
    print(" ABC SOFTWARE CORP — MOTOR DE GENERACION Y VALIDACION XML OASIS UBL 2.1 (XSD OFICIAL)")
    print(f" Esquema XSD Cargado: {xsd_validator_adapter.xsd_path.relative_to(repo_root)}")
    print("=" * 88)

    # -------------------------------------------------------------------------
    # ESCENARIO 1: Factura Mayorista al Contado (IGV + ISC Cat. 08 = 01 + ICBPER + Bonificación)
    # -------------------------------------------------------------------------
    customer_1 = PartyInfo(
        identity_doc_type_cat06="6",
        identity_doc_number="20601234565",
        legal_name="BODEGA Y ABARROTES SAN MARTIN S.A.C.",
        ubigeo_cat13="150101",
        address_line="AV. GRAU 450, CERCADO DE LIMA",
    )
    items_1 = [
        InvoiceLineInput(
            sku="AB-ARR-50KG",
            unspsc_code_cat25="50221101",
            description="SACO DE ARROZ EXTRA X 50 KG",
            unit_code_cat03="BG",
            quantity=Decimal("10.00"),
            unit_value=Decimal("140.00"),
            igv_affectation_cat07="10",
        ),
        InvoiceLineInput(
            sku="BEB-GAS-3L",
            unspsc_code_cat25="50202306",
            description="PACK GASEOSA 3 LITROS X 6 UNIDADES",
            unit_code_cat03="PK",
            quantity=Decimal("5.00"),
            unit_value=Decimal("30.00"),
            igv_affectation_cat07="10",
            isc_config=IscConfiguration(
                system_code_cat08="01",
                rate_or_fixed_amount=Decimal("25.00"),
            ),
        ),
        InvoiceLineInput(
            sku="BOL-PLAST-GDE",
            unspsc_code_cat25="24111503",
            description="BOLSA PLASTICA GRANDE BIODEGRADABLE",
            unit_code_cat03="NIU",
            quantity=Decimal("2.00"),
            unit_value=Decimal("0.10"),
            igv_affectation_cat07="10",
            applies_icbper=True,
        ),
        InvoiceLineInput(
            sku="AB-ACE-1L",
            unspsc_code_cat25="50151513",
            description="BOTELLA ACEITE VEGETAL 1 LITRO - BONIFICACION MAYORISTA",
            unit_code_cat03="NIU",
            quantity=Decimal("1.00"),
            unit_value=Decimal("0.00"),
            reference_unit_value=Decimal("8.00"),
            igv_affectation_cat07="15",
        ),
    ]

    art_1 = controller.issue_and_export_xml(
        output_dir=output_dir,
        document_type_cat01="01",
        operation_type_cat51="0101",
        series="F001",
        correlative=145,
        issue_date="2026-11-12",
        issue_time="10:30:00",
        currency_code_cat02="PEN",
        supplier=supplier,
        customer=customer_1,
        payment_terms=PaymentTermsInfo(condition="Contado"),
        items=items_1,
    )

    # -------------------------------------------------------------------------
    # ESCENARIO 2: Factura Mayorista al Crédito en 2 Cuotas (ISC Cat. 08 = 02 y 03)
    # -------------------------------------------------------------------------
    items_2 = [
        InvoiceLineInput(
            sku="LIC-RON-750",
            unspsc_code_cat25="50202206",
            description="CAJA RON PREMIUM 750ML X 12 BOTELLAS (ISC MONTO FIJO CAT. 08 = 02)",
            unit_code_cat03="BX",
            quantity=Decimal("4.00"),
            unit_value=Decimal("250.00"),
            igv_affectation_cat07="10",
            isc_config=IscConfiguration(
                system_code_cat08="02",
                rate_or_fixed_amount=Decimal("15.00"),
            ),
        ),
        InvoiceLineInput(
            sku="CER-PILS-630",
            unspsc_code_cat25="50202201",
            description="CAJA CERVEZA 630ML X 12 UNID (ISC PVP CAT. 08 = 03)",
            unit_code_cat03="BX",
            quantity=Decimal("10.00"),
            unit_value=Decimal("55.00"),
            igv_affectation_cat07="10",
            isc_config=IscConfiguration(
                system_code_cat08="03",
                rate_or_fixed_amount=Decimal("30.00"),
                suggested_retail_price=Decimal("72.00"),
            ),
        ),
    ]

    art_2 = controller.issue_and_export_xml(
        output_dir=output_dir,
        document_type_cat01="01",
        operation_type_cat51="0101",
        series="F001",
        correlative=146,
        issue_date="2026-11-12",
        issue_time="11:15:00",
        due_date="2026-12-12",
        currency_code_cat02="PEN",
        supplier=supplier,
        customer=customer_1,
        payment_terms=PaymentTermsInfo(
            condition="Credito",
            net_pending_amount=Decimal("2131.48"),
            installments=[
                InstallmentInfo("Cuota001", Decimal("1100.00"), "2026-11-27"),
                InstallmentInfo("Cuota002", Decimal("1031.48"), "2026-12-12"),
            ],
        ),
        items=items_2,
    )

    # -------------------------------------------------------------------------
    # ESCENARIO 3: Boleta de Venta Minorista con DNI (Gravado + Exonerado Cat. 07 = 20)
    # -------------------------------------------------------------------------
    customer_3 = PartyInfo(
        identity_doc_type_cat06="1",
        identity_doc_number="45891234",
        legal_name="JUAN CARLOS PEREZ GOMEZ",
    )
    items_3 = [
        InvoiceLineInput(
            sku="AB-AZU-50KG",
            unspsc_code_cat25="50161509",
            description="SACO DE AZUCAR RUBIA DOMESTICA X 50 KG",
            unit_code_cat03="BG",
            quantity=Decimal("5.00"),
            unit_value=Decimal("130.00"),
            igv_affectation_cat07="10",
        ),
        InvoiceLineInput(
            sku="AGR-LEN-10KG",
            unspsc_code_cat25="50405600",
            description="SACO DE LENTEJA AGRICOLA NATURAL X 10 KG (EXONERADO IGV)",
            unit_code_cat03="BG",
            quantity=Decimal("2.00"),
            unit_value=Decimal("45.00"),
            igv_affectation_cat07="20",
        ),
    ]

    art_3 = controller.issue_and_export_xml(
        output_dir=output_dir,
        document_type_cat01="03",
        operation_type_cat51="0101",
        series="B001",
        correlative=890,
        issue_date="2026-11-12",
        issue_time="12:00:00",
        currency_code_cat02="PEN",
        supplier=supplier,
        customer=customer_3,
        payment_terms=PaymentTermsInfo(condition="Contado"),
        items=items_3,
    )

    # -------------------------------------------------------------------------
    # ESCENARIO 4: Factura con RUC Demo Nubefact (20600695771) Firmada Criptográficamente
    # -------------------------------------------------------------------------
    nubefact_supplier = PartyInfo(
        identity_doc_type_cat06="6",
        identity_doc_number="20600695771",
        legal_name="ABC SOFTWARE CORP S.A.C.",
        trade_name="ABC DISTRIBUIDORA MAYORISTA Y MINORISTA DE ABARROTES",
        ubigeo_cat13="150101",
        establishment_code="0000",
        address_line="AV. NICOLAS AYLLON 2450 - LIMA",
        country_code="PE",
    )
    real_customer = PartyInfo(
        identity_doc_type_cat06="6",
        identity_doc_number="20100070970",
        legal_name="SUPERMERCADOS PERUANOS SOCIEDAD ANONIMA",
        ubigeo_cat13="150130",
        address_line="CAL. MORELLI NRO. 181 SAN BORJA - LIMA",
    )
    art_4 = controller.issue_and_export_xml(
        output_dir=output_dir,
        document_type_cat01="01",
        operation_type_cat51="0101",
        series="F001",
        correlative=145,
        issue_date="2026-11-12",
        issue_time="10:30:00",
        currency_code_cat02="PEN",
        supplier=nubefact_supplier,
        customer=real_customer,
        payment_terms=PaymentTermsInfo(condition="Contado"),
        items=items_1,
    )

    for idx, art in enumerate([art_1, art_2, art_3, art_4], start=1):
        print(f"\n[Escenario {idx}] Archivo Generado : output/{art.xml_filename}")
        print(f"  - Comprobante / Cliente : {art.document.full_id} -> {art.document.customer.legal_name}")
        print(f"  - Valor Venta Total     : S/ {art.document.legal_monetary_total.line_extension_amount:.2f}")
        print(f"  - Total Tributos (Tax)  : S/ {art.document.global_tax_total_amount:.2f}")
        print(f"  - Importe Total a Pagar : S/ {art.document.legal_monetary_total.payable_amount:.2f}")
        print(f"  - Resumen Hash (Digest) : {art.digest_value_hash}")
        print(f"  - Cadena QR SUNAT       : {art.qr_code_string}")
        print(f"  - Validacion XSD OASIS  : {art.xsd_validation_message}")

    print("\n" + "=" * 88)


if __name__ == "__main__":
    run_demo()
