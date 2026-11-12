"""
Suite de Pruebas Automatizadas (Unitarias + Integración XSD):
Verifica las reglas tributarias SUNAT (RUC Módulo 11, IGV, Catálogo 08 ISC, ICBPER, Gratuitas)
y la validación estricta de los XML generados contra xsd/maindoc/UBL-Invoice-2.1.xsd.
"""

import unittest
from decimal import Decimal
from pathlib import Path

from src.core_model.application.use_cases import IssueElectronicInvoiceUseCase
from src.core_model.domain.entities import (
    InvoiceLineInput,
    IscConfiguration,
    PartyInfo,
    PaymentTermsInfo,
)
from src.core_model.domain.ruc_validator import SunatRucValidator
from src.infrastructure_adapters.ubl21_xml_generator import OasisUbl21XmlGeneratorAdapter
from src.infrastructure_adapters.xsd_schema_validator import OasisXsdSchemaValidatorAdapter


class TestUbl21InvoiceGenerationAndXsdValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.xml_generator = OasisUbl21XmlGeneratorAdapter()
        cls.xsd_validator = OasisXsdSchemaValidatorAdapter()
        cls.use_case = IssueElectronicInvoiceUseCase(
            xml_generator_port=cls.xml_generator,
            xsd_validator_port=cls.xsd_validator,
        )
        cls.supplier = PartyInfo(
            identity_doc_type_cat06="6",
            identity_doc_number="20555999110",
            legal_name="ABC SOFTWARE CORP S.A.C.",
        )

    def test_01_ruc_modulo11_validation(self) -> None:
        ok, _ = SunatRucValidator.validate_ruc_mod11("20555999110")
        self.assertTrue(ok)
        ok_bad, msg_bad = SunatRucValidator.validate_ruc_mod11("20555999119")
        self.assertFalse(ok_bad)
        self.assertIn("Módulo 11", msg_bad)

    def test_02_generate_invoice_with_isc_cat08_icbper_and_validate_xsd(self) -> None:
        customer = PartyInfo(
            identity_doc_type_cat06="6",
            identity_doc_number="20601234565",
            legal_name="BODEGA SAN MARTIN S.A.C.",
        )
        items = [
            InvoiceLineInput(
                sku="AB-ARR-50KG",
                description="SACO DE ARROZ EXTRA X 50 KG",
                unit_code_cat03="BG",
                quantity=Decimal("10"),
                unit_value=Decimal("140.00"),
                igv_affectation_cat07="10",
            ),
            InvoiceLineInput(
                sku="BEB-GAS-3L",
                description="PACK GASEOSA 3L X 6",
                unit_code_cat03="PK",
                quantity=Decimal("5"),
                unit_value=Decimal("30.00"),
                igv_affectation_cat07="10",
                isc_config=IscConfiguration(
                    system_code_cat08="01",
                    rate_or_fixed_amount=Decimal("25.00"),
                ),
            ),
            InvoiceLineInput(
                sku="BOL-PLAST",
                description="BOLSA PLASTICA",
                unit_code_cat03="NIU",
                quantity=Decimal("2"),
                unit_value=Decimal("0.10"),
                igv_affectation_cat07="10",
                applies_icbper=True,
            ),
        ]
        artifact = self.use_case.execute(
            document_type_cat01="01",
            operation_type_cat51="0101",
            series="F001",
            correlative=145,
            issue_date="2026-11-12",
            issue_time="10:30:00",
            currency_code_cat02="PEN",
            supplier=self.supplier,
            customer=customer,
            payment_terms=PaymentTermsInfo(condition="Contado"),
            raw_items=items,
        )
        self.assertTrue(artifact.is_xsd_valid, artifact.xsd_validation_message)
        self.assertEqual(artifact.document.legal_monetary_total.line_extension_amount, Decimal("1550.20"))
        self.assertEqual(artifact.document.global_tax_total_amount, Decimal("324.29"))
        self.assertEqual(artifact.document.legal_monetary_total.payable_amount, Decimal("1874.49"))

    def test_03_boleta_over_700_without_dni_is_rejected(self) -> None:
        anonymous_customer = PartyInfo(
            identity_doc_type_cat06="0",
            identity_doc_number="00000000",
            legal_name="CLIENTES VARIOS",
        )
        items = [
            InvoiceLineInput(
                sku="AB-ARR-50KG",
                description="SACO DE ARROZ EXTRA X 50 KG",
                unit_code_cat03="BG",
                quantity=Decimal("6"),
                unit_value=Decimal("120.00"),
                igv_affectation_cat07="10",
            )
        ]
        with self.assertRaises(ValueError) as ctx:
            self.use_case.execute(
                document_type_cat01="03",
                operation_type_cat51="0101",
                series="B001",
                correlative=1,
                issue_date="2026-11-12",
                issue_time="10:30:00",
                currency_code_cat02="PEN",
                supplier=self.supplier,
                customer=anonymous_customer,
                payment_terms=PaymentTermsInfo(condition="Contado"),
                raw_items=items,
            )
        self.assertIn("700.00", str(ctx.exception))

    def test_04_sample_ubl21_xml_in_specs_is_xsd_valid(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        sample_path = repo_root / "specs" / "ubl-examples" / "20555999113-01-F001-145-ubl21-sample.xml"
        xml_text = sample_path.read_text(encoding="utf-8")
        is_valid, errors = self.xsd_validator.validate_against_ubl_invoice_xsd(xml_text)
        self.assertTrue(is_valid, f"Errores XSD en sample: {errors}")


if __name__ == "__main__":
    unittest.main()
