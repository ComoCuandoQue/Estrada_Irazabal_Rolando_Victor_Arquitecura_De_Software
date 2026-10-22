# 4. Matriz de Trazabilidad Normativa (Cruces: Datos de Negocio / Legado $\leftrightarrow$ Normativa SUNAT $\leftrightarrow$ `UBL-Invoice-2.1.xsd`)

> **Entregable 4 — Metodología Spec-First**
> Establece el mapeo exacto y auditable entre:
> 1. Los **contratos de datos (DTOs y Entidades)** del nuevo sistema de ABC Software Corp,
> 2. La **normativa tributaria de la SUNAT** (**RS N.º 097-2012/SUNAT**, **RS N.º 234-2006/SUNAT**, **RS N.º 193-2020/SUNAT**, **Anexo N.º 8: Catálogo de Códigos** y especialmente el **Catálogo N.º 08**),
> 3. Los nodos XPath y atributos XML definidos en el esquema oficial **OASIS `UBL-Invoice-2.1.xsd`**, y
> 4. Las **fichas del software legado** (`fecha`, `ingreso`, `salida`, `producto`, `nro_documento`).

---

## 4.1 Matriz de Cruce Estructural: Cabecera, Partes, Condiciones de Pago y Totales (`UBL-Invoice-2.1.xsd`)

| ID | Campo en Dominio / DTO | Base Legal y Catálogo SUNAT (Anexo N.º 8) | Nodo XPath Exacto en `UBL-Invoice-2.1.xsd` | Atributos XML Obligatorios (`@`) | Cardinalidad y Regla de Validación (Spec Constraint) |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **M-01** | `ublVersionId` | Estándar OASIS UBL 2.1 / Guía XML SUNAT | `/Invoice/cbc:UBLVersionID` | *(Ninguno)* | **`[1..1]`** Constante `"2.1"`. Si difiere, rechazo inmediato (`Error 2074`). |
| **M-02** | `customizationId` | Guía de Elaboración XML UBL 2.1 SUNAT | `/Invoice/cbc:CustomizationID` | `@schemeAgencyName="PE:SUNAT"` | **`[1..1]`** Constante `"2.0"`. |
| **M-03** | `series` + `correlative` | RS 097-2012 Art. 10 (Numeración de CPE) | `/Invoice/cbc:ID` | *(Ninguno)* | **`[1..1]`** Patrón `^[FB][A-Z0-9]{3}-[0-9]{1,8}$` (ej. `F001-145`). |
| **M-04** | `issueDate` | RS 097-2012 (Fecha de emisión) | `/Invoice/cbc:IssueDate` | *(Ninguno)* | **`[1..1]`** Formato ISO `YYYY-MM-DD`. Máximo 3 días calendario de antigüedad al enviar a OSE/SUNAT. |
| **M-05** | `issueTime` | Guía XML UBL 2.1 SUNAT | `/Invoice/cbc:IssueTime` | *(Ninguno)* | **`[0..1]`** Formato `HH:MM:SS` (`00:00:00` a `23:59:59`). |
| **M-06** | `dueDate` | Guía XML UBL 2.1 SUNAT | `/Invoice/cbc:DueDate` | *(Ninguno)* | **`[0..1]`** Formato `YYYY-MM-DD` ($\ge$ `IssueDate`). |
| **M-07** | `documentTypeCode` + `operationTypeCode` | **Catálogo N.º 01** (Tipo de Documento) + **Catálogo N.º 51** (Tipo de Operación) | `/Invoice/cbc:InvoiceTypeCode` | `@listAgencyName="PE:SUNAT"`<br>`@listName="Tipo de Documento"`<br>`@listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01"`<br>`@listID="{operationTypeCode}"` | **`[1..1]`** Valor del elemento: `01` (Factura) o `03` (Boleta). El atributo `@listID` lleva el código del **Catálogo 51** (ej. `"0101"` Venta Interna). |
| **M-08** | `amountInWordsLegend` | **Catálogo N.º 52** (Códigos de Leyendas: `1000` Monto en Letras, `1002` Transferencia Gratuita) | `/Invoice/cbc:Note` | `@languageLocaleID="1000"` | **`[1..n]`** Texto en mayúsculas con importe expresado en letras y centavos `/100`. |
| **M-09** | `currencyCode` | **Catálogo N.º 02** (Códigos de Tipo de Monedas ISO 4217) | `/Invoice/cbc:DocumentCurrencyCode` | `@listID="ISO 4217 Alpha"`<br>`@listName="Currency"`<br>`@listAgencyName="United Nations Economic Commission for Europe"` | **`[1..1]`** `"PEN"` (Sol) o `"USD"` (Dólar Americano). |
| **M-10** | `digitalSignature` | RS 097-2012 (Firma Digital XAdES-BES con Certificado X.509) | `/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/ds:Signature` | `@Id="SignABCSoftware"` | **`[1..1]`** Debe contener `ds:SignedInfo`, `ds:DigestValue` (Hash del CPE), `ds:SignatureValue` y `ds:KeyInfo/ds:X509Data`. |
| **M-11** | `supplier.ruc` | **Catálogo N.º 06** (`6` = Registro Único de Contribuyentes) | `/Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID` | `@schemeID="6"`<br>`@schemeName="Documento de Identidad"`<br>`@schemeAgencyName="PE:SUNAT"`<br>`@schemeURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06"` | **`[1..1]`** 11 dígitos numéricos validados con Módulo 11. Debe coincidir con el RUC del nombre del archivo ZIP (`{RUC}-{Tipo}-{Serie}-{Numero}.zip`). |
| **M-12** | `supplier.legalName` | Padrón RUC SUNAT | `/Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName` | *(Se recomienda envolver en `<![CDATA[...]]>`) * | **`[1..1]`** Razón social oficial de ABC Software Corp (`1..1500` caracteres). |
| **M-13** | `supplier.establishmentCode` | Padrón de Establecimientos Anexos SUNAT | `/Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cac:RegistrationAddress/cbc:AddressTypeCode` | `@listAgencyName="PE:SUNAT"`<br>`@listName="Establecimientos anexos"` | **`[1..1]`** `"0000"` para domicilio fiscal principal o código de 4 dígitos de sucursal. |
| **M-14** | `customer.identityDocNumber` | **Catálogo N.º 06** (`6`=RUC, `1`=DNI, `4`=CE, `7`=Pasaporte, `0`=Doc.Trib.No.Dom.sin.RUC) | `/Invoice/cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID` | `@schemeID="{customer.identityDocType}"`<br>`@schemeName="Documento de Identidad"`<br>`@schemeAgencyName="PE:SUNAT"`<br>`@schemeURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06"` | **`[1..1]`** Si `InvoiceTypeCode="01"` (Factura), `@schemeID` **debe ser `"6"`** (RUC válido). Si `InvoiceTypeCode="03"` (Boleta) y `PayableAmount > 700.00`, prohíbe `@schemeID="0"`. |
| **M-15** | `paymentTerms.condition` | RS N.º 193-2020/SUNAT (Forma de Pago Contado o Crédito) | `/Invoice/cac:PaymentTerms[cbc:ID='FormaPago']/cbc:PaymentMeansID` | `@currencyID="{currencyCode}"` en `/cbc:Amount` | **`[1..1]`** `"Contado"` o `"Credito"`. Si es `"Credito"`, exige nodos adicionales `cac:PaymentTerms` por cada cuota (`Cuota001..CuotaNNN`) con `cbc:PaymentDueDate`. |
| **M-16** | `taxTotal.totalTaxAmount` | Guía XML UBL 2.1 SUNAT | `/Invoice/cac:TaxTotal/cbc:TaxAmount` | `@currencyID="{currencyCode}"` | **`[1..1]`** Suma exacta de `IGV (1000) + ISC (2000) + ICBPER (7152)`. |
| **M-17** | `taxTotal.subtotals[]` | **Catálogo N.º 05** (Códigos de Tipos de Tributos) | `/Invoice/cac:TaxTotal/cac:TaxSubtotal` | `@currencyID` en `cbc:TaxableAmount` y `cbc:TaxAmount`; `@schemeID="UN/ECE 5153"` en `cac:TaxScheme/cbc:ID` | **`[1..n]`** Un bloque `cac:TaxSubtotal` por cada tipo de tributo presente en el comprobante (`1000`, `2000`, `7152`, `9996`, `9997`, `9998`). |
| **M-18** | `legalMonetaryTotal` | Guía XML UBL 2.1 SUNAT | `/Invoice/cac:LegalMonetaryTotal` | `@currencyID="{currencyCode}"` en todos sus sub-elementos | **`[1..1]`** Contiene `cbc:LineExtensionAmount` (Total Valor Venta), `cbc:TaxInclusiveAmount` (Total Precio Venta) y `cbc:PayableAmount` (Importe Total a Pagar). |

---

## 4.2 Matriz de Cruce Estructural: Líneas de Detalle (`cac:InvoiceLine`) e Impuestos por Ítem

| ID | Campo en `DocumentLine` / DTO | Base Legal y Catálogo SUNAT (Anexo N.º 8) | Nodo XPath Exacto dentro de `/Invoice/cac:InvoiceLine` | Atributos XML Obligatorios (`@`) | Regla de Validación y Restricción Técnica |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **L-01** | `lineNumber` | Estándar UBL 2.1 | `./cbc:ID` | *(Ninguno)* | Entero secuencial iniciando en `1`. |
| **L-02** | `quantity` + `unitCode` | **Catálogo N.º 03** (Unidades de Medida Comerciales UN/ECE Rec 20) | `./cbc:InvoicedQuantity` | `@unitCode="{unitCode}"`<br>`@unitCodeListID="UN/ECE rec 20"`<br>`@unitCodeListAgencyName="United Nations Economic Commission for Europe"` | Mayor a `0` (hasta 10 decimales). En abarrotes: `NIU` (Unidad), `BX` (Caja), `BG` (Bolsa/Saco), `KGM` (Kilogramo), `PK` (Paquete), `LTR` (Litro). |
| **L-03** | `lineExtensionAmount` | Guía XML UBL 2.1 SUNAT | `./cbc:LineExtensionAmount` | `@currencyID="{currencyCode}"` | Valor de venta del ítem sin impuestos (`round(quantity * unitValue - discount, 2)`). |
| **L-04** | `unitPriceWithTax` o `referenceUnitValue` | **Catálogo N.º 16** (Códigos de Tipo de Precio de Venta Unitario) | `./cac:PricingReference/cac:AlternativeConditionPrice/cbc:PriceAmount` y `./cbc:PriceTypeCode` | `@currencyID="{currencyCode}"` en `PriceAmount`; `@listName="Tipo de Precio"`, `@listAgencyName="PE:SUNAT"`, `@listURI="...catalogo16"` en `PriceTypeCode` | **`01`** = Precio unitario (incluye IGV, ISC e ICBPER) para operaciones onerosas.<br>**`02`** = Valor referencial unitario para bonificaciones/operaciones no onerosas (gratuitas). |
| **L-05** | `lineDiscountAmount` | **Catálogo N.º 53** (Códigos de Cargos o Descuentos: `00` Descuento que afecta base IGV) | `./cac:AllowanceCharge[cbc:ChargeIndicator='false']/cbc:Amount` | `@currencyID="{currencyCode}"`; `cbc:AllowanceChargeReasonCode="00"` | Opcional (`0..n`). Se resta antes de calcular la base imponible del ISC y del IGV. |
| **L-06** | `igvAffectationCode` | **Catálogo N.º 07** (Códigos de Tipo de Afectación del IGV) | `./cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:TaxExemptionReasonCode` | `@listAgencyName="PE:SUNAT"`<br>`@listName="Afectacion del IGV"`<br>`@listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo07"` | Determina si el ítem es Gravado (`10`), Retiro/Bonificación (`11`..`16`), Exonerado (`20`), Inafecto (`30`) o Exportación (`40`). |
| **L-07** | **`iscConfiguration.systemCodeCat08`** | **Catálogo N.º 08 de SUNAT (Códigos de Tipos de Sistema de Cálculo del ISC)** | `./cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:TierRange` | En `./cac:TaxScheme`: `cbc:ID="2000"`, `cbc:Name="ISC"`, `cbc:TaxTypeCode="EXC"` | **Punto crítico exigido**: Acepta únicamente `"01"` (Al Valor), `"02"` (Monto Fijo) o `"03"` (Precios de Venta al Público). |
| **L-08** | `appliesIcbper` | Ley N.º 30884 / **Catálogo N.º 05** (`7152` = Impuesto a la Bolsa Plástica) | `./cac:TaxTotal/cac:TaxSubtotal[cac:TaxCategory/cac:TaxScheme/cbc:ID='7152']` | `@unitCode="NIU"` en `./cbc:BaseUnitMeasure`; `@currencyID="PEN"` en `./cac:TaxCategory/cbc:PerUnitAmount` | Obligatorio cuando se entregan bolsas plásticas. `TaxAmount = BaseUnitMeasure * PerUnitAmount`. |
| **L-09** | `description` | Guía XML UBL 2.1 SUNAT | `./cac:Item/cbc:Description` | *(Se recomienda envolver en `<![CDATA[...]]>`) * | Descripción comercial clara del producto (`1..500` caracteres). |
| **L-10** | `sku` | Código interno del producto en almacén | `./cac:Item/cac:SellersItemIdentification/cbc:ID` | *(Ninguno)* | Vincula el ítem de la factura directamente con el SKU del **Kardex Formal**. |
| **L-11** | `unspscCodeCat25` | **Catálogo N.º 25** (Código de Producto SUNAT - UNSPSC v14) | `./cac:Item/cac:CommodityClassification/cbc:ItemClassificationCode` | `@listID="UNSPSC"`<br>`@listAgencyName="GS1 US"`<br>`@listName="Item Classification"` | Código estándar de 8 dígitos (ej. `"50221101"` para Arroz, `"50202306"` para Gaseosas). |
| **L-12** | `unitValue` | Guía XML UBL 2.1 SUNAT | `./cac:Price/cbc:PriceAmount` | `@currencyID="{currencyCode}"` | Valor unitario **sin impuestos** (hasta 10 decimales). En operaciones gratuitas (`9996`), este nodo vale `"0.00"`. |

---

## 4.3 Especificación Detallada del Catálogo N.º 08 de SUNAT (Sistemas de Cálculo del ISC) y Catálogo N.º 05 / 07

### A. Cruce del Catálogo N.º 08 (ISC en Bebidas, Licores y Productos Selectivos de Abarrotes)

| Código Catálogo 08 | Descripción Oficial SUNAT | Nodo `cbc:TierRange` | Nodo `cac:TaxScheme` (Catálogo 05) | Fórmula de Base Imponible (`cbc:TaxableAmount`) | Impacto en el IGV de la Línea (`1000`) |
| :---: | :--- | :---: | :---: | :--- | :--- |
| **`01`** | **Sistema al Valor** | `<cbc:TierRange>01</cbc:TierRange>` | `ID="2000"`<br>`Name="ISC"`<br>`TaxTypeCode="EXC"` | $\text{ValorVenta}_{\text{línea}} = Q \times V_u - D$ | $\text{Base}_{\text{IGV}} = \text{ValorVenta}_{\text{línea}} + \text{ISC}_{01}$ |
| **`02`** | **Aplicación del Monto Fijo** *(Soles por unidad o litro)* | `<cbc:TierRange>02</cbc:TierRange>` | `ID="2000"`<br>`Name="ISC"`<br>`TaxTypeCode="EXC"` | Cantidad de unidades o litros afectos ($Q$) | $\text{Base}_{\text{IGV}} = \text{ValorVenta}_{\text{línea}} + \text{ISC}_{02}$ |
| **`03`** | **Sistema de Precios de Venta al Público (PVP)** | `<cbc:TierRange>03</cbc:TierRange>` | `ID="2000"`<br>`Name="ISC"`<br>`TaxTypeCode="EXC"` | $Q \times \text{PrecioSugerido}_{\text{PVP}} \times 0.909$ | $\text{Base}_{\text{IGV}} = \text{ValorVenta}_{\text{línea}} + \text{ISC}_{03}$ |

### B. Tabla de Correspondencia: Catálogo 07 (Afectación IGV) $\leftrightarrow$ Catálogo 05 (Tributo) $\leftrightarrow$ UN/ECE 5153

| Código Catálogo 07 (`cbc:TaxExemptionReasonCode`) | Descripción de la Operación | Categoría (`cac:TaxCategory/cbc:ID`) | Código Tributo Catálogo 05 (`cac:TaxScheme/cbc:ID`) | Nombre (`cbc:Name`) | Código Internacional (`cbc:TaxTypeCode`) | Tasa (`cbc:Percent`) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **`10`** | Gravado — Operación Onerosa | `S` | `1000` | `IGV` | `VAT` | `18.00` |
| **`11` a `16`** | Gravado — Retiro / Bonificación / Premio / Donación (No Onerosa) | `Z` | `9996` | `GRA` | `FRE` | `18.00` *(Referencial)* |
| **`20`** | Exonerado — Operación Onerosa | `E` | `9997` | `EXO` | `VAT` | `0.00` |
| **`21`** | Exonerado — Transferencia Gratuita | `Z` | `9996` | `GRA` | `FRE` | `0.00` |
| **`30`** | Inafecto — Operación Onerosa | `O` | `9998` | `INA` | `FRE` | `0.00` |
| **`31` a `36`** | Inafecto — Retiro por Bonificación / Muestras Médicas / Convenio | `Z` | `9996` | `GRA` | `FRE` | `0.00` |
| **`40`** | Exportación de Bienes o Servicios | `G` | `9995` | `EXP` | `FRE` | `0.00` |

---

## 4.4 Matriz de Trazabilidad de Migración: Fichas del Software Básico $\leftrightarrow$ Kardex Formal SUNAT (RS N.º 234-2006)

Esta matriz garantiza el cumplimiento de la primera condición innegociable de la gerencia: **mapear limpiamente toda la información histórica (`fecha`, `ingreso`, `salida`, `producto`, `nro_documento`) sin perder trazabilidad**:

| Campo en Ficha del Software Básico (Legado) | Tipo de Dato Original | Entidad y Atributo en el Nuevo Sistema (`INVENTORY_LEDGER_KARDEX`) | Columna Homóloga en Formato 12.1 y 13.1 (RS N.º 234-2006/SUNAT) | Regla de Transformación, Homologación y Auditoría |
| :--- | :--- | :--- | :--- | :--- |
| **`fecha`** | Texto (`"DD/MM/YYYY"` o `"YYYY-MM-DD"`) | `movement_date` (`TIMESTAMP`) + `period_yyyymm` (`CHAR(6)`) | **Fecha de Emisión** del documento de traslado, comprobante de pago o documento interno. | Se convierte a fecha ISO 8601 y se ordena cronológicamente. Se conserva el valor textual original en `LEGACY_RAW_MOVEMENTS.raw_fecha`. |
| **`ingreso`** | Numérico (`>= 0`) | `qty_in`, `unit_cost_in`, `total_cost_in` | **Entradas** (Cantidad, Costo Unitario y Costo Total) + **Tipo de Operación (Tabla 12)**. | Si es el primer movimiento histórico del producto, se asigna **Tabla 12 = `16` (Saldo Inicial)**; para ingresos posteriores, se asigna **`02` (Compra)** o **`99` (Otros)**. |
| **`salida`** | Numérico (`>= 0`) | `qty_out`, `unit_cost_out`, `total_cost_out` | **Salidas** (Cantidad, Costo Unitario al Costo Promedio Ponderado vigente y Costo Total) + **Tipo de Operación (Tabla 12)**. | Se asigna **Tabla 12 = `01` (Venta)** o **`99` (Otros - Salida Histórica)**. El motor verifica en `DRY_RUN` que `balance_qty` nunca caiga por debajo de `0`. |
| **`producto`** | Texto libre (`"Arroz Extra 50kg"`, `"Aceite 1L"`) | `product_id` $\rightarrow$ `PRODUCTS` (`sku`, `formal_name`, `unit_code_cat03`, `existence_type_tabla02`, `unspsc_code_cat25`) | **Cabecera del Kardex**: Código de la Existencia, Tipo de Existencia (**Tabla 2** = `01` Mercadería), Descripción y Código de Unidad de Medida (**Tabla 6 / Catálogo 03**). | Se cruza obligatoriamente con el diccionario `productHomologationMap`. Unifica variantes tipográficas bajo un único SKU formal. |
| **`nro_documento`** | Texto informal (`"VALE-102"`, `"S/N"`, `"001-450"`) | `tabla10_doc_type`, `doc_series`, `doc_correlative`, `legacy_doc_ref` y `legacy_raw_id` | **Documento de Traslado, Comprobante de Pago, Documento Interno o Similar**: Tipo (**Tabla 10**), Serie y Número. | • Si cumple formato de comprobante físico/electrónico válido (`001-450` o `F001-120`), se mapea a **Tabla 10 = `01`/`03`**.<br>• Si es informal (`"VALE-102"`, `"S/N"`), se asigna **Tabla 10 = `00` (Otros)**, Serie `MIG01` y correlativo autogenerado, almacenando `"VALE-102"` en `legacy_doc_ref` con un hash `SHA-256` inmutable para auditoría. |
