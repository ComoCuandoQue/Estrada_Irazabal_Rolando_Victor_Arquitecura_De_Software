"""
Entidades y Objetos de Valor del Núcleo de Dominio Tributario — ABC Software Corp.
Diseñado bajo el principio de Modelo Puro (cero dependencias de frameworks o librerías XML).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional


@dataclass(frozen=True)
class PartyInfo:
    """Representa al Emisor (AccountingSupplierParty) o al Adquirente (AccountingCustomerParty)."""
    identity_doc_type_cat06: str  # '6'=RUC, '1'=DNI, '4'=CE, '0'=Clientes Varios
    identity_doc_number: str
    legal_name: str
    trade_name: Optional[str] = None
    ubigeo_cat13: str = "150101"
    establishment_code: str = "0000"
    address_line: str = "LIMA - PERU"
    country_code: str = "PE"


@dataclass(frozen=True)
class InstallmentInfo:
    """Representa una cuota de pago al crédito (RS N.º 193-2020/SUNAT)."""
    installment_id: str  # Ej: 'Cuota001'
    amount: Decimal
    due_date: str  # YYYY-MM-DD


@dataclass(frozen=True)
class PaymentTermsInfo:
    """Condición de pago del comprobante (Contado o Crédito)."""
    condition: str  # 'Contado' | 'Credito'
    net_pending_amount: Optional[Decimal] = None
    installments: List[InstallmentInfo] = field(default_factory=list)


@dataclass(frozen=True)
class IscConfiguration:
    """
    Configuración del Impuesto Selectivo al Consumo según el Catálogo N.º 08 de SUNAT:
    - '01': Sistema al Valor (porcentaje sobre valor de venta)
    - '02': Aplicación del Monto Fijo (soles por unidad/litro)
    - '03': Sistema de Precios de Venta al Público (PVP sugerido)
    """
    system_code_cat08: str  # '01' | '02' | '03'
    rate_or_fixed_amount: Decimal
    suggested_retail_price: Optional[Decimal] = None


@dataclass(frozen=True)
class InvoiceLineInput:
    """Datos de entrada de una línea de producto de abarrotes."""
    sku: str
    description: str
    unit_code_cat03: str  # 'NIU', 'BX', 'BG', 'PK', 'KGM', 'LTR'
    quantity: Decimal
    unit_value: Decimal  # Valor unitario sin impuestos (0.00 si es bonificación gratuita)
    igv_affectation_cat07: str  # '10'=Gravado, '15'=Bonificación, '20'=Exonerado, '30'=Inafecto
    unspsc_code_cat25: str = "50221101"
    reference_unit_value: Optional[Decimal] = None  # Obligatorio en bonificaciones (Cat. 16 = '02')
    discount_amount: Decimal = Decimal("0.00")
    isc_config: Optional[IscConfiguration] = None
    applies_icbper: bool = False


@dataclass(frozen=True)
class TaxSubtotalCalculated:
    """Subtotal calculado por cada tributo (Catálogo N.º 05 de SUNAT)."""
    taxable_amount: Optional[Decimal]
    tax_amount: Decimal
    tax_category_id: str  # 'S', 'E', 'O', 'Z'
    tax_scheme_id_cat05: str  # '1000'=IGV, '2000'=ISC, '7152'=ICBPER, '9996'=GRA, '9997'=EXO, '9998'=INA
    tax_scheme_name: str  # 'IGV', 'ISC', 'ICBPER', 'GRA', 'EXO', 'INA'
    tax_type_code: str  # 'VAT', 'EXC', 'OTH', 'FRE'
    percent: Optional[Decimal] = None
    tax_exemption_reason_cat07: Optional[str] = None
    tier_range_cat08: Optional[str] = None  # '01', '02', '03' para ISC
    base_unit_measure_qty: Optional[int] = None  # Para ICBPER (7152)
    per_unit_amount: Optional[Decimal] = None  # Tarifa por bolsa ICBPER


@dataclass(frozen=True)
class CalculatedInvoiceLine:
    """Línea de comprobante con todos sus importes y tributos calculados exactamente."""
    line_number: int
    sku: str
    unspsc_code_cat25: str
    description: str
    unit_code_cat03: str
    quantity: Decimal
    unit_value: Decimal
    price_type_code_cat16: str  # '01'=Precio con IGV, '02'=Valor referencial gratuito
    alternative_condition_price: Decimal
    line_extension_amount: Decimal
    discount_amount: Decimal
    total_line_tax_amount: Decimal
    tax_subtotals: List[TaxSubtotalCalculated]
    is_free_operation: bool


@dataclass(frozen=True)
class LegalMonetaryTotalCalculated:
    """Totales monetarios globales del comprobante (cac:LegalMonetaryTotal)."""
    line_extension_amount: Decimal
    tax_inclusive_amount: Decimal
    allowance_total_amount: Decimal
    charge_total_amount: Decimal
    payable_amount: Decimal


@dataclass(frozen=True)
class ElectronicInvoiceDocument:
    """Entidad Raíz del Agregado de Factura/Boleta Electrónica UBL 2.1."""
    document_type_cat01: str  # '01'=Factura, '03'=Boleta
    operation_type_cat51: str  # '0101'=Venta Interna
    series: str
    correlative: int
    issue_date: str  # YYYY-MM-DD
    issue_time: str  # HH:MM:SS
    currency_code_cat02: str  # 'PEN' | 'USD'
    supplier: PartyInfo
    customer: PartyInfo
    payment_terms: PaymentTermsInfo
    lines: List[CalculatedInvoiceLine]
    global_tax_total_amount: Decimal
    global_tax_subtotals: List[TaxSubtotalCalculated]
    legal_monetary_total: LegalMonetaryTotalCalculated
    amount_in_words_legend: str
    has_free_transfer_legend: bool
    due_date: Optional[str] = None

    @property
    def full_id(self) -> str:
        return f"{self.series}-{self.correlative}"

    @property
    def standard_xml_filename(self) -> str:
        return f"{self.supplier.identity_doc_number}-{self.document_type_cat01}-{self.series}-{self.correlative}.xml"
