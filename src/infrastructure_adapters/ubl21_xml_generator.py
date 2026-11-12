"""
Adaptador de Infraestructura: Generador de XML conforme a OASIS UBL-Invoice-2.1.xsd y Anexo N.º 8 SUNAT.
Implementa el puerto IUblInvoiceXmlGeneratorPort respetando estrictamente el <xs:sequence> de OASIS.
"""

import base64
import hashlib
from decimal import Decimal
from typing import Tuple
from lxml import etree

from ..core_model.application.ports import IUblInvoiceXmlGeneratorPort
from ..core_model.domain.entities import (
    CalculatedInvoiceLine,
    ElectronicInvoiceDocument,
    TaxSubtotalCalculated,
)

NS_INVOICE = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
NS_EXT = "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
NS_DS = "http://www.w3.org/2000/09/xmldsig#"

NSMAP = {
    None: NS_INVOICE,
    "cac": NS_CAC,
    "cbc": NS_CBC,
    "ds": NS_DS,
    "ext": NS_EXT,
}


def qn(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


class OasisUbl21XmlGeneratorAdapter(IUblInvoiceXmlGeneratorPort):
    """Construye el árbol XML UBL 2.1 cumpliendo cada XPath y atributo del Anexo N.º 8 de SUNAT."""

    def generate_invoice_xml(
        self, doc: ElectronicInvoiceDocument
    ) -> Tuple[str, str, str]:
        root = etree.Element(qn(NS_INVOICE, "Invoice"), nsmap=NSMAP)

        # Hash determinista SHA-256 sobre el identificador y totales del documento (simulación XAdES-BES)
        canonical_seed = (
            f"{doc.supplier.identity_doc_number}|{doc.document_type_cat01}|{doc.full_id}|"
            f"{doc.global_tax_total_amount:.2f}|{doc.legal_monetary_total.payable_amount:.2f}|"
            f"{doc.issue_date}|{doc.customer.identity_doc_type_cat06}|{doc.customer.identity_doc_number}"
        )
        digest_bytes = hashlib.sha256(canonical_seed.encode("utf-8")).digest()
        digest_b64 = base64.b64encode(digest_bytes).decode("ascii")
        sig_value_b64 = base64.b64encode(hashlib.sha512(digest_bytes).digest()).decode("ascii")

        # 1. ext:UBLExtensions (Contenedor obligatorio de Firma Digital XAdES-BES)
        ubl_exts = etree.SubElement(root, qn(NS_EXT, "UBLExtensions"))
        ubl_ext = etree.SubElement(ubl_exts, qn(NS_EXT, "UBLExtension"))
        ext_content = etree.SubElement(ubl_ext, qn(NS_EXT, "ExtensionContent"))
        ds_sig = etree.SubElement(ext_content, qn(NS_DS, "Signature"), Id="SignABCSoftware")
        signed_info = etree.SubElement(ds_sig, qn(NS_DS, "SignedInfo"))
        etree.SubElement(
            signed_info,
            qn(NS_DS, "CanonicalizationMethod"),
            Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
        )
        etree.SubElement(
            signed_info,
            qn(NS_DS, "SignatureMethod"),
            Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
        )
        ds_ref = etree.SubElement(signed_info, qn(NS_DS, "Reference"), URI="")
        transforms = etree.SubElement(ds_ref, qn(NS_DS, "Transforms"))
        etree.SubElement(
            transforms,
            qn(NS_DS, "Transform"),
            Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature",
        )
        etree.SubElement(
            ds_ref,
            qn(NS_DS, "DigestMethod"),
            Algorithm="http://www.w3.org/2001/04/xmlenc#sha256",
        )
        etree.SubElement(ds_ref, qn(NS_DS, "DigestValue")).text = digest_b64
        etree.SubElement(ds_sig, qn(NS_DS, "SignatureValue")).text = sig_value_b64

        # 2. cbc:UBLVersionID & 3. cbc:CustomizationID
        etree.SubElement(root, qn(NS_CBC, "UBLVersionID")).text = "2.1"
        etree.SubElement(
            root, qn(NS_CBC, "CustomizationID"), schemeAgencyName="PE:SUNAT"
        ).text = "2.0"

        # 4. cbc:ID, 5. cbc:IssueDate, 6. cbc:IssueTime, 7. cbc:DueDate
        etree.SubElement(root, qn(NS_CBC, "ID")).text = doc.full_id
        etree.SubElement(root, qn(NS_CBC, "IssueDate")).text = doc.issue_date
        etree.SubElement(root, qn(NS_CBC, "IssueTime")).text = doc.issue_time
        if doc.due_date:
            etree.SubElement(root, qn(NS_CBC, "DueDate")).text = doc.due_date

        # 8. cbc:InvoiceTypeCode (Catálogo 01 + @listID con Catálogo 51)
        etree.SubElement(
            root,
            qn(NS_CBC, "InvoiceTypeCode"),
            listAgencyName="PE:SUNAT",
            listName="Tipo de Documento",
            listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01",
            listID=doc.operation_type_cat51,
            name="Tipo de Operacion",
        ).text = doc.document_type_cat01

        # 9. cbc:Note (Catálogo 52: 1000=Monto en letras, 1002=Transferencia gratuita)
        note_words = etree.SubElement(root, qn(NS_CBC, "Note"), languageLocaleID="1000")
        note_words.text = etree.CDATA(doc.amount_in_words_legend)
        if doc.has_free_transfer_legend:
            note_free = etree.SubElement(root, qn(NS_CBC, "Note"), languageLocaleID="1002")
            note_free.text = etree.CDATA(
                "TRANSFERENCIA GRATUITA DE UN BIEN Y/O SERVICIO PRESTADO GRATUITAMENTE"
            )

        # 10. cbc:DocumentCurrencyCode (Catálogo 02)
        etree.SubElement(
            root,
            qn(NS_CBC, "DocumentCurrencyCode"),
            listID="ISO 4217 Alpha",
            listName="Currency",
            listAgencyName="United Nations Economic Commission for Europe",
        ).text = doc.currency_code_cat02

        # 11. cac:Signature
        cac_sig = etree.SubElement(root, qn(NS_CAC, "Signature"))
        etree.SubElement(cac_sig, qn(NS_CBC, "ID")).text = doc.supplier.identity_doc_number
        sig_party = etree.SubElement(cac_sig, qn(NS_CAC, "SignatoryParty"))
        sig_party_id = etree.SubElement(sig_party, qn(NS_CAC, "PartyIdentification"))
        etree.SubElement(sig_party_id, qn(NS_CBC, "ID")).text = doc.supplier.identity_doc_number
        sig_party_name = etree.SubElement(sig_party, qn(NS_CAC, "PartyName"))
        etree.SubElement(sig_party_name, qn(NS_CBC, "Name")).text = etree.CDATA(
            doc.supplier.legal_name
        )
        sig_attach = etree.SubElement(cac_sig, qn(NS_CAC, "DigitalSignatureAttachment"))
        ext_ref = etree.SubElement(sig_attach, qn(NS_CAC, "ExternalReference"))
        etree.SubElement(ext_ref, qn(NS_CBC, "URI")).text = "#SignABCSoftware"

        # 12. cac:AccountingSupplierParty (Emisor — ABC Software Corp)
        sup_container = etree.SubElement(root, qn(NS_CAC, "AccountingSupplierParty"))
        sup_party = etree.SubElement(sup_container, qn(NS_CAC, "Party"))
        sup_ident = etree.SubElement(sup_party, qn(NS_CAC, "PartyIdentification"))
        etree.SubElement(
            sup_ident,
            qn(NS_CBC, "ID"),
            schemeID=doc.supplier.identity_doc_type_cat06,
            schemeName="Documento de Identidad",
            schemeAgencyName="PE:SUNAT",
            schemeURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06",
        ).text = doc.supplier.identity_doc_number

        if doc.supplier.trade_name:
            sup_pname = etree.SubElement(sup_party, qn(NS_CAC, "PartyName"))
            etree.SubElement(sup_pname, qn(NS_CBC, "Name")).text = etree.CDATA(
                doc.supplier.trade_name
            )

        sup_legal = etree.SubElement(sup_party, qn(NS_CAC, "PartyLegalEntity"))
        etree.SubElement(sup_legal, qn(NS_CBC, "RegistrationName")).text = etree.CDATA(
            doc.supplier.legal_name
        )
        sup_addr = etree.SubElement(sup_legal, qn(NS_CAC, "RegistrationAddress"))
        etree.SubElement(
            sup_addr, qn(NS_CBC, "ID"), schemeName="Ubigeos", schemeAgencyName="PE:INEI"
        ).text = doc.supplier.ubigeo_cat13
        etree.SubElement(
            sup_addr,
            qn(NS_CBC, "AddressTypeCode"),
            listAgencyName="PE:SUNAT",
            listName="Establecimientos anexos",
        ).text = doc.supplier.establishment_code
        addr_line = etree.SubElement(sup_addr, qn(NS_CAC, "AddressLine"))
        etree.SubElement(addr_line, qn(NS_CBC, "Line")).text = etree.CDATA(
            doc.supplier.address_line
        )
        sup_country = etree.SubElement(sup_addr, qn(NS_CAC, "Country"))
        etree.SubElement(
            sup_country,
            qn(NS_CBC, "IdentificationCode"),
            listID="ISO 3166-1",
            listName="Country",
        ).text = doc.supplier.country_code

        # 13. cac:AccountingCustomerParty (Cliente Adquirente)
        cust_container = etree.SubElement(root, qn(NS_CAC, "AccountingCustomerParty"))
        cust_party = etree.SubElement(cust_container, qn(NS_CAC, "Party"))
        cust_ident = etree.SubElement(cust_party, qn(NS_CAC, "PartyIdentification"))
        etree.SubElement(
            cust_ident,
            qn(NS_CBC, "ID"),
            schemeID=doc.customer.identity_doc_type_cat06,
            schemeName="Documento de Identidad",
            schemeAgencyName="PE:SUNAT",
            schemeURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06",
        ).text = doc.customer.identity_doc_number
        cust_legal = etree.SubElement(cust_party, qn(NS_CAC, "PartyLegalEntity"))
        etree.SubElement(cust_legal, qn(NS_CBC, "RegistrationName")).text = etree.CDATA(
            doc.customer.legal_name
        )
        cust_addr = etree.SubElement(cust_legal, qn(NS_CAC, "RegistrationAddress"))
        etree.SubElement(
            cust_addr, qn(NS_CBC, "ID"), schemeName="Ubigeos", schemeAgencyName="PE:INEI"
        ).text = doc.customer.ubigeo_cat13
        cust_addr_line = etree.SubElement(cust_addr, qn(NS_CAC, "AddressLine"))
        etree.SubElement(cust_addr_line, qn(NS_CBC, "Line")).text = etree.CDATA(
            doc.customer.address_line
        )
        cust_country = etree.SubElement(cust_addr, qn(NS_CAC, "Country"))
        etree.SubElement(
            cust_country,
            qn(NS_CBC, "IdentificationCode"),
            listID="ISO 3166-1",
            listName="Country",
        ).text = doc.customer.country_code

        # 14. cac:PaymentTerms (RS N.º 193-2020/SUNAT — Contado o Crédito con Cuotas)
        pt_main = etree.SubElement(root, qn(NS_CAC, "PaymentTerms"))
        etree.SubElement(pt_main, qn(NS_CBC, "ID")).text = "FormaPago"
        etree.SubElement(pt_main, qn(NS_CBC, "PaymentMeansID")).text = (
            doc.payment_terms.condition
        )
        if doc.payment_terms.condition == "Credito":
            pending = doc.payment_terms.net_pending_amount or doc.legal_monetary_total.payable_amount
            etree.SubElement(
                pt_main, qn(NS_CBC, "Amount"), currencyID=doc.currency_code_cat02
            ).text = f"{pending:.2f}"
            for inst in doc.payment_terms.installments:
                pt_inst = etree.SubElement(root, qn(NS_CAC, "PaymentTerms"))
                etree.SubElement(pt_inst, qn(NS_CBC, "ID")).text = "FormaPago"
                etree.SubElement(pt_inst, qn(NS_CBC, "PaymentMeansID")).text = (
                    inst.installment_id
                )
                etree.SubElement(
                    pt_inst, qn(NS_CBC, "Amount"), currencyID=doc.currency_code_cat02
                ).text = f"{inst.amount:.2f}"
                etree.SubElement(pt_inst, qn(NS_CBC, "PaymentDueDate")).text = inst.due_date

        # 15. cac:TaxTotal Global
        tax_total_el = etree.SubElement(root, qn(NS_CAC, "TaxTotal"))
        etree.SubElement(
            tax_total_el, qn(NS_CBC, "TaxAmount"), currencyID=doc.currency_code_cat02
        ).text = f"{doc.global_tax_total_amount:.2f}"
        for sub in doc.global_tax_subtotals:
            self._append_tax_subtotal(
                tax_total_el, sub, doc.currency_code_cat02, is_line_level=False
            )

        # 16. cac:LegalMonetaryTotal
        lmt = etree.SubElement(root, qn(NS_CAC, "LegalMonetaryTotal"))
        etree.SubElement(
            lmt, qn(NS_CBC, "LineExtensionAmount"), currencyID=doc.currency_code_cat02
        ).text = f"{doc.legal_monetary_total.line_extension_amount:.2f}"
        etree.SubElement(
            lmt, qn(NS_CBC, "TaxInclusiveAmount"), currencyID=doc.currency_code_cat02
        ).text = f"{doc.legal_monetary_total.tax_inclusive_amount:.2f}"
        if doc.legal_monetary_total.allowance_total_amount > Decimal("0.00"):
            etree.SubElement(
                lmt, qn(NS_CBC, "AllowanceTotalAmount"), currencyID=doc.currency_code_cat02
            ).text = f"{doc.legal_monetary_total.allowance_total_amount:.2f}"
        etree.SubElement(
            lmt, qn(NS_CBC, "PayableAmount"), currencyID=doc.currency_code_cat02
        ).text = f"{doc.legal_monetary_total.payable_amount:.2f}"

        # 17. cac:InvoiceLine (1..n)
        for line in doc.lines:
            self._append_invoice_line(root, line, doc.currency_code_cat02)

        xml_bytes = etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8",
        )
        xml_str = xml_bytes.decode("utf-8")

        # Cadena oficial SUNAT para el Código QR
        igv_amount = next(
            (s.tax_amount for s in doc.global_tax_subtotals if s.tax_scheme_id_cat05 == "1000"),
            Decimal("0.00"),
        )
        qr_string = (
            f"{doc.supplier.identity_doc_number}|{doc.document_type_cat01}|"
            f"{doc.series}|{doc.correlative}|{igv_amount:.2f}|"
            f"{doc.legal_monetary_total.payable_amount:.2f}|{doc.issue_date}|"
            f"{doc.customer.identity_doc_type_cat06}|{doc.customer.identity_doc_number}|"
            f"{digest_b64}|"
        )
        return xml_str, digest_b64, qr_string

    def _append_tax_subtotal(
        self,
        parent_tax_total: etree._Element,
        sub: TaxSubtotalCalculated,
        currency_code: str,
        is_line_level: bool,
    ) -> None:
        """Agrega un nodo cac:TaxSubtotal respetando la secuencia de UBL-CommonAggregateComponents-2.1.xsd."""
        sub_el = etree.SubElement(parent_tax_total, qn(NS_CAC, "TaxSubtotal"))
        if sub.taxable_amount is not None:
            etree.SubElement(
                sub_el, qn(NS_CBC, "TaxableAmount"), currencyID=currency_code
            ).text = f"{sub.taxable_amount:.2f}"
        etree.SubElement(
            sub_el, qn(NS_CBC, "TaxAmount"), currencyID=currency_code
        ).text = f"{sub.tax_amount:.2f}"

        if is_line_level and sub.base_unit_measure_qty is not None:
            etree.SubElement(
                sub_el, qn(NS_CBC, "BaseUnitMeasure"), unitCode="NIU"
            ).text = str(sub.base_unit_measure_qty)

        cat_el = etree.SubElement(sub_el, qn(NS_CAC, "TaxCategory"))
        if sub.tax_scheme_id_cat05 != "7152":
            etree.SubElement(
                cat_el,
                qn(NS_CBC, "ID"),
                schemeID="UN/ECE 5305",
                schemeName="Tax Category Identifier",
            ).text = sub.tax_category_id

        if is_line_level:
            if sub.percent is not None:
                etree.SubElement(cat_el, qn(NS_CBC, "Percent")).text = f"{sub.percent:.2f}"
            if sub.per_unit_amount is not None:
                etree.SubElement(
                    cat_el, qn(NS_CBC, "PerUnitAmount"), currencyID=currency_code
                ).text = f"{sub.per_unit_amount:.2f}"
            if sub.tax_exemption_reason_cat07 is not None:
                etree.SubElement(
                    cat_el,
                    qn(NS_CBC, "TaxExemptionReasonCode"),
                    listAgencyName="PE:SUNAT",
                    listName="Afectacion del IGV",
                    listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo07",
                ).text = sub.tax_exemption_reason_cat07
            # PUNTO CLAVE: Catálogo 08 de SUNAT (Sistemas de Cálculo del ISC) en cbc:TierRange
            if sub.tier_range_cat08 is not None:
                etree.SubElement(cat_el, qn(NS_CBC, "TierRange")).text = sub.tier_range_cat08

        scheme_el = etree.SubElement(cat_el, qn(NS_CAC, "TaxScheme"))
        etree.SubElement(
            scheme_el, qn(NS_CBC, "ID"), schemeID="UN/ECE 5153", schemeAgencyID="6"
        ).text = sub.tax_scheme_id_cat05
        etree.SubElement(scheme_el, qn(NS_CBC, "Name")).text = sub.tax_scheme_name
        etree.SubElement(scheme_el, qn(NS_CBC, "TaxTypeCode")).text = sub.tax_type_code

    def _append_invoice_line(
        self,
        root: etree._Element,
        line: CalculatedInvoiceLine,
        currency_code: str,
    ) -> None:
        """Agrega un nodo cac:InvoiceLine respetando la secuencia exacta de UBL-Invoice-2.1.xsd."""
        line_el = etree.SubElement(root, qn(NS_CAC, "InvoiceLine"))
        etree.SubElement(line_el, qn(NS_CBC, "ID")).text = str(line.line_number)
        etree.SubElement(
            line_el,
            qn(NS_CBC, "InvoicedQuantity"),
            unitCode=line.unit_code_cat03,
            unitCodeListID="UN/ECE rec 20",
            unitCodeListAgencyName="United Nations Economic Commission for Europe",
        ).text = f"{line.quantity:.2f}"
        etree.SubElement(
            line_el, qn(NS_CBC, "LineExtensionAmount"), currencyID=currency_code
        ).text = f"{line.line_extension_amount:.2f}"

        # cac:PricingReference (Catálogo 16: '01'=Precio con IGV, '02'=Valor referencial gratuito)
        pricing_ref = etree.SubElement(line_el, qn(NS_CAC, "PricingReference"))
        alt_price = etree.SubElement(pricing_ref, qn(NS_CAC, "AlternativeConditionPrice"))
        etree.SubElement(
            alt_price, qn(NS_CBC, "PriceAmount"), currencyID=currency_code
        ).text = f"{line.alternative_condition_price:.2f}"
        etree.SubElement(
            alt_price,
            qn(NS_CBC, "PriceTypeCode"),
            listName="Tipo de Precio",
            listAgencyName="PE:SUNAT",
            listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16",
        ).text = line.price_type_code_cat16

        # cac:AllowanceCharge (Descuento de línea si existe)
        if line.discount_amount > Decimal("0.00"):
            ac_el = etree.SubElement(line_el, qn(NS_CAC, "AllowanceCharge"))
            etree.SubElement(ac_el, qn(NS_CBC, "ChargeIndicator")).text = "false"
            etree.SubElement(ac_el, qn(NS_CBC, "AllowanceChargeReasonCode")).text = "00"
            etree.SubElement(
                ac_el, qn(NS_CBC, "Amount"), currencyID=currency_code
            ).text = f"{line.discount_amount:.2f}"

        # cac:TaxTotal de la línea
        line_tax_el = etree.SubElement(line_el, qn(NS_CAC, "TaxTotal"))
        etree.SubElement(
            line_tax_el, qn(NS_CBC, "TaxAmount"), currencyID=currency_code
        ).text = f"{line.total_line_tax_amount:.2f}"
        for sub in line.tax_subtotals:
            self._append_tax_subtotal(line_tax_el, sub, currency_code, is_line_level=True)

        # cac:Item
        item_el = etree.SubElement(line_el, qn(NS_CAC, "Item"))
        etree.SubElement(item_el, qn(NS_CBC, "Description")).text = etree.CDATA(
            line.description
        )
        sellers_id = etree.SubElement(item_el, qn(NS_CAC, "SellersItemIdentification"))
        etree.SubElement(sellers_id, qn(NS_CBC, "ID")).text = line.sku
        comm_class = etree.SubElement(item_el, qn(NS_CAC, "CommodityClassification"))
        etree.SubElement(
            comm_class,
            qn(NS_CBC, "ItemClassificationCode"),
            listID="UNSPSC",
            listAgencyName="GS1 US",
            listName="Item Classification",
        ).text = line.unspsc_code_cat25

        # cac:Price (Valor unitario sin impuestos)
        price_el = etree.SubElement(line_el, qn(NS_CAC, "Price"))
        etree.SubElement(
            price_el, qn(NS_CBC, "PriceAmount"), currencyID=currency_code
        ).text = f"{line.unit_value:.2f}"
