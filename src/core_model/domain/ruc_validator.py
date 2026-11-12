"""
Validador de RUC (Algoritmo Módulo 11 SUNAT) y Reglas del Catálogo N.º 06.
"""

from decimal import Decimal
from typing import Tuple


class SunatRucValidator:
    """Implementa la validación matemática oficial del RUC peruano (11 dígitos, Módulo 11)."""

    VALID_PREFIXES = ("10", "15", "16", "17", "20")
    WEIGHTS = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    BOLETA_DNI_THRESHOLD_PEN = Decimal("700.00")

    @classmethod
    def validate_ruc_mod11(cls, ruc: str) -> Tuple[bool, str]:
        """
        Verifica si un número de RUC cumple con:
        1. Longitud exacta de 11 dígitos numéricos.
        2. Prefijo válido (10, 15, 16, 17, 20).
        3. Dígito verificador exacto según el Algoritmo Módulo 11.
        """
        if not ruc or len(ruc) != 11 or not ruc.isdigit():
            return False, f"El RUC '{ruc}' debe contener exactamente 11 dígitos numéricos."

        if not ruc.startswith(cls.VALID_PREFIXES):
            return False, f"El RUC '{ruc}' tiene un prefijo inválido (debe iniciar con 10, 15, 16, 17 o 20)."

        total_sum = sum(int(ruc[i]) * cls.WEIGHTS[i] for i in range(10))
        remainder = 11 - (total_sum % 11)

        if remainder == 10:
            expected_check_digit = 0
        elif remainder == 11:
            expected_check_digit = 1
        else:
            expected_check_digit = remainder

        actual_check_digit = int(ruc[10])
        if actual_check_digit != expected_check_digit:
            return (
                False,
                f"El RUC '{ruc}' falló la validación Módulo 11: dígito verificador esperado={expected_check_digit}, recibido={actual_check_digit}.",
            )

        return True, "RUC válido conforme al Algoritmo Módulo 11 de SUNAT."

    @classmethod
    def validate_customer_for_document(
        cls,
        document_type_cat01: str,
        series: str,
        customer_doc_type_cat06: str,
        customer_doc_number: str,
        payable_amount: Decimal,
    ) -> Tuple[bool, str]:
        """Valida la coherencia entre Tipo de Comprobante (Cat. 01), Serie y Documento del Cliente (Cat. 06)."""
        if document_type_cat01 == "01":
            if not series.startswith("F") or len(series) != 4:
                return False, f"Una Factura (01) exige serie alfanumérica de 4 caracteres iniciada en 'F' (recibido: '{series}')."
            if customer_doc_type_cat06 != "6":
                return False, "Una Factura Electrónica (01) exige que el adquirente se identifique con RUC (Catálogo 06 = '6')."
            return cls.validate_ruc_mod11(customer_doc_number)

        if document_type_cat01 == "03":
            if not series.startswith("B") or len(series) != 4:
                return False, f"Una Boleta (03) exige serie alfanumérica de 4 caracteres iniciada en 'B' (recibido: '{series}')."
            if payable_amount > cls.BOLETA_DNI_THRESHOLD_PEN and customer_doc_type_cat06 == "0":
                return (
                    False,
                    f"Boleta con importe S/ {payable_amount} supera el tope de S/ 700.00: es obligatorio identificar al comprador con DNI (Catálogo 06 = '1').",
                )
            if customer_doc_type_cat06 == "1" and (len(customer_doc_number) != 8 or not customer_doc_number.isdigit()):
                return False, f"El DNI '{customer_doc_number}' debe contener exactamente 8 dígitos numéricos."
            return True, "Cliente válido para Boleta de Venta."

        return False, f"Tipo de documento '{document_type_cat01}' no soportado en este validador."
