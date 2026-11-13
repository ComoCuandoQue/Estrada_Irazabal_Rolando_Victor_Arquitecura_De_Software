"""
Motor Matemático Tributario SUNAT — ABC Software Corp.
Calcula IGV (Catálogo 07), ISC (Catálogo 08: Sistemas 01, 02, 03), ICBPER (7152) y Gratuitas (9996).
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple
from .entities import (
    CalculatedInvoiceLine,
    InvoiceLineInput,
    LegalMonetaryTotalCalculated,
    TaxSubtotalCalculated,
)

TWO_DECIMALS = Decimal("0.01")
IGV_RATE = Decimal("18.00")
ICBPER_TARIFF_PEN = Decimal("0.50")
PVP_ISC_FACTOR = Decimal("0.909")


def round2(value: Decimal) -> Decimal:
    """Redondeo comercial estándar SUNAT a 2 decimales (ROUND_HALF_UP)."""
    return value.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)


class SunatTaxCalculationEngine:
    """Motor puro de cálculo tributario por ítem y consolidado global."""

    FREE_AFFECTATION_CODES = {"11", "12", "13", "14", "15", "16", "21", "31", "32", "33", "34", "35", "36"}

    @classmethod
    def calculate_line(cls, line_number: int, item: InvoiceLineInput) -> CalculatedInvoiceLine:
        is_free = item.igv_affectation_cat07 in cls.FREE_AFFECTATION_CODES
        subtotals: List[TaxSubtotalCalculated] = []

        if is_free:
            ref_unit = item.reference_unit_value or Decimal("0.00")
            line_ext = round2(item.quantity * ref_unit)
            igv_rate = IGV_RATE if item.igv_affectation_cat07.startswith("1") else Decimal("0.00")
            free_tax = round2(line_ext * (igv_rate / Decimal("100")))
            subtotals.append(
                TaxSubtotalCalculated(
                    taxable_amount=line_ext,
                    tax_amount=free_tax,
                    tax_category_id="Z",
                    tax_scheme_id_cat05="9996",
                    tax_scheme_name="GRA",
                    tax_type_code="FRE",
                    percent=igv_rate,
                    tax_exemption_reason_cat07=item.igv_affectation_cat07,
                )
            )
            return CalculatedInvoiceLine(
                line_number=line_number,
                sku=item.sku,
                unspsc_code_cat25=item.unspsc_code_cat25,
                description=item.description,
                unit_code_cat03=item.unit_code_cat03,
                quantity=round2(item.quantity),
                unit_value=Decimal("0.00"),
                price_type_code_cat16="02",
                alternative_condition_price=round2(ref_unit),
                line_extension_amount=line_ext,
                discount_amount=Decimal("0.00"),
                total_line_tax_amount=Decimal("0.00"),
                tax_subtotals=subtotals,
                is_free_operation=True,
            )

        # Operación Onerosa (Gravada '10', Exonerada '20', Inafecta '30')
        line_ext = round2(item.quantity * item.unit_value - item.discount_amount)
        isc_amount = Decimal("0.00")

        # 1. Cálculo de ISC según el Catálogo N.º 08 de SUNAT (01=Al Valor, 02=Monto Fijo, 03=PVP)
        if item.isc_config is not None:
            sys_code = item.isc_config.system_code_cat08
            if sys_code == "01":
                isc_base = line_ext
                isc_amount = round2(isc_base * (item.isc_config.rate_or_fixed_amount / Decimal("100")))
                isc_percent = round2(item.isc_config.rate_or_fixed_amount)
            elif sys_code == "02":
                isc_base = round2(item.quantity)
                isc_amount = round2(item.quantity * item.isc_config.rate_or_fixed_amount)
                isc_percent = round2(item.isc_config.rate_or_fixed_amount)
            elif sys_code == "03":
                pvp = item.isc_config.suggested_retail_price or item.unit_value
                isc_base = round2(item.quantity * pvp * PVP_ISC_FACTOR)
                isc_amount = round2(isc_base * (item.isc_config.rate_or_fixed_amount / Decimal("100")))
                isc_percent = round2(item.isc_config.rate_or_fixed_amount)
            else:
                raise ValueError(f"Código Catálogo 08 de ISC inválido: '{sys_code}'. Use '01', '02' o '03'.")

            subtotals.append(
                TaxSubtotalCalculated(
                    taxable_amount=isc_base,
                    tax_amount=isc_amount,
                    tax_category_id="S",
                    tax_scheme_id_cat05="2000",
                    tax_scheme_name="ISC",
                    tax_type_code="EXC",
                    percent=isc_percent,
                    tier_range_cat08=sys_code,
                )
            )

        # 2. Cálculo de IGV / Exonerado / Inafecto (Catálogo 07 -> Catálogo 05)
        if item.igv_affectation_cat07 == "10":
            igv_base = round2(line_ext + isc_amount)
            igv_amount = round2(igv_base * (IGV_RATE / Decimal("100")))
            subtotals.append(
                TaxSubtotalCalculated(
                    taxable_amount=igv_base,
                    tax_amount=igv_amount,
                    tax_category_id="S",
                    tax_scheme_id_cat05="1000",
                    tax_scheme_name="IGV",
                    tax_type_code="VAT",
                    percent=IGV_RATE,
                    tax_exemption_reason_cat07="10",
                )
            )
        elif item.igv_affectation_cat07 == "20":
            igv_amount = Decimal("0.00")
            subtotals.append(
                TaxSubtotalCalculated(
                    taxable_amount=line_ext,
                    tax_amount=Decimal("0.00"),
                    tax_category_id="E",
                    tax_scheme_id_cat05="9997",
                    tax_scheme_name="EXO",
                    tax_type_code="VAT",
                    percent=Decimal("0.00"),
                    tax_exemption_reason_cat07="20",
                )
            )
        else:
            igv_amount = Decimal("0.00")
            subtotals.append(
                TaxSubtotalCalculated(
                    taxable_amount=line_ext,
                    tax_amount=Decimal("0.00"),
                    tax_category_id="O",
                    tax_scheme_id_cat05="9998",
                    tax_scheme_name="INA",
                    tax_type_code="FRE",
                    percent=Decimal("0.00"),
                    tax_exemption_reason_cat07=item.igv_affectation_cat07,
                )
            )

        # 3. Cálculo de ICBPER (Tributo 7152 - Bolsas Plásticas)
        icbper_amount = Decimal("0.00")
        if item.applies_icbper:
            bag_qty = int(item.quantity)
            icbper_amount = round2(Decimal(bag_qty) * ICBPER_TARIFF_PEN)
            subtotals.append(
                TaxSubtotalCalculated(
                    taxable_amount=None,
                    tax_amount=icbper_amount,
                    tax_category_id="S",
                    tax_scheme_id_cat05="7152",
                    tax_scheme_name="ICBPER",
                    tax_type_code="OTH",
                    base_unit_measure_qty=bag_qty,
                    per_unit_amount=ICBPER_TARIFF_PEN,
                )
            )

        total_line_tax = round2(isc_amount + igv_amount + icbper_amount)
        unit_price_with_tax = round2((line_ext + total_line_tax) / item.quantity)

        return CalculatedInvoiceLine(
            line_number=line_number,
            sku=item.sku,
            unspsc_code_cat25=item.unspsc_code_cat25,
            description=item.description,
            unit_code_cat03=item.unit_code_cat03,
            quantity=round2(item.quantity),
            unit_value=round2(item.unit_value),
            price_type_code_cat16="01",
            alternative_condition_price=unit_price_with_tax,
            line_extension_amount=line_ext,
            discount_amount=round2(item.discount_amount),
            total_line_tax_amount=total_line_tax,
            tax_subtotals=subtotals,
            is_free_operation=False,
        )

    @classmethod
    def consolidate_document_totals(
        cls, calculated_lines: List[CalculatedInvoiceLine]
    ) -> Tuple[Decimal, List[TaxSubtotalCalculated], LegalMonetaryTotalCalculated, bool]:
        """Consolida los subtotales globales por código de tributo (Catálogo 05) y el LegalMonetaryTotal."""
        grouped: Dict[str, Dict[str, Decimal]] = {}
        meta: Dict[str, Tuple[str, str, str]] = {}

        line_extension_total = Decimal("0.00")
        allowance_total = Decimal("0.00")
        has_free_lines = False

        for line in calculated_lines:
            if line.is_free_operation:
                has_free_lines = True
            else:
                line_extension_total = round2(line_extension_total + line.line_extension_amount)
                allowance_total = round2(allowance_total + line.discount_amount)

            for sub in line.tax_subtotals:
                scheme = sub.tax_scheme_id_cat05
                if scheme not in grouped:
                    grouped[scheme] = {"taxable": Decimal("0.00"), "tax": Decimal("0.00")}
                    meta[scheme] = (sub.tax_category_id, sub.tax_scheme_name, sub.tax_type_code)
                if sub.taxable_amount is not None:
                    # Regla SUNAT 3277: En el TaxSubtotal global de IGV (1000), TaxableAmount es la suma
                    # del Valor de Venta (LineExtensionAmount) de las líneas gravadas (sin sumar el ISC).
                    base_to_add = line.line_extension_amount if scheme == "1000" else sub.taxable_amount
                    grouped[scheme]["taxable"] = round2(grouped[scheme]["taxable"] + base_to_add)
                grouped[scheme]["tax"] = round2(grouped[scheme]["tax"] + sub.tax_amount)

        # El TaxAmount global de SUNAT suma únicamente tributos onerosos (1000 IGV + 2000 ISC + 7152 ICBPER)
        global_tax_amount = Decimal("0.00")
        global_subtotals: List[TaxSubtotalCalculated] = []

        order_priority = ["1000", "2000", "7152", "9997", "9998", "9996"]
        for scheme in order_priority:
            if scheme not in grouped:
                continue
            cat_id, name, t_type = meta[scheme]
            taxable_val = None if scheme == "7152" else grouped[scheme]["taxable"]
            tax_val = grouped[scheme]["tax"]
            if scheme in ("1000", "2000", "7152"):
                global_tax_amount = round2(global_tax_amount + tax_val)

            global_subtotals.append(
                TaxSubtotalCalculated(
                    taxable_amount=taxable_val,
                    tax_amount=tax_val,
                    tax_category_id=cat_id,
                    tax_scheme_id_cat05=scheme,
                    tax_scheme_name=name,
                    tax_type_code=t_type,
                )
            )

        tax_inclusive = round2(line_extension_total + global_tax_amount)
        monetary_total = LegalMonetaryTotalCalculated(
            line_extension_amount=line_extension_total,
            tax_inclusive_amount=tax_inclusive,
            allowance_total_amount=allowance_total,
            charge_total_amount=Decimal("0.00"),
            payable_amount=tax_inclusive,
        )
        return global_tax_amount, global_subtotals, monetary_total, has_free_lines

    @staticmethod
    def amount_to_words_pen(amount: Decimal) -> str:
        """Genera la leyenda del importe en letras (Catálogo 52 = '1000')."""
        integer_part = int(amount)
        cents = int((amount - Decimal(integer_part)) * 100)
        return f"SON {integer_part} Y {cents:02d}/100 SOLES"
