# 1. Modelo de Dominio y Contratos de Datos (DTOs / Schemas)

> **Entregable 1 — Metodología Spec-First**
> Define formalmente las entidades, objetos de valor, invariantes matemáticas tributarias (RUC Módulo 11, IGV, ISC Catálogo 08, ICBPER, Bonificaciones), el modelo de migración de datos históricos del almacén y los contratos de transferencia de datos (DTOs / JSON Schemas).

---

## 1.1 Diseño Estratégico del Dominio (Bounded Contexts)

Para evitar que el sistema herede el desorden del software básico anterior, el modelo de dominio se estructura en **dos subdominios principales** comunicados por identificadores inmutables:

1. **Subdominio de Facturación Electrónica (`Billing & UBL Core`)**:
   - Responsable de estructurar, validar y calcular Comprobantes de Pago Electrónicos (Facturas `01`, Boletas `03`, Notas de Crédito `07` y Notas de Débito `08`) bajo el estándar **OASIS UBL 2.1** y el **Anexo N.º 8 de la RS N.º 097-2012/SUNAT**.
2. **Subdominio de Inventario Permanente y Migración (`Inventory & Legacy Migration Core`)**:
   - Responsable de llevar el **Kardex Físico (Formato 12.1)** y **Kardex Valorizado (Formato 13.1)** bajo la **RS N.º 234-2006/SUNAT**, así como de ingerir, homologar y auditar las fichas históricas del sistema legado (`fecha`, `ingreso`, `salida`, `producto`, `nro_documento`).

---

## 1.2 Diagrama de Clases del Modelo de Dominio

```mermaid
classDiagram
    class ElectronicDocument {
        +UUID id
        +String ublVersionId "Constante: 2.1"
        +String customizationId "Constante: 2.0"
        +DocumentTypeCat01 documentType "01 | 03 | 07 | 08"
        +OperationTypeCat51 operationType "0101 Venta Interna"
        +DocumentSeries series "F001 | B001 | FC01 | BC01"
        +Int correlative "1..99999999"
        +LocalDate issueDate
        +LocalTime issueTime
        +LocalDate dueDate
        +CurrencyCodeCat02 currencyCode "PEN | USD"
        +PaymentTerms paymentTerms
        +BillingReference billingReference "Solo NC (07) / ND (08)"
        +DocumentStatus status
        +String xmlDigestHash
        +String qrCodePayload
        +validateDomainRules()
        +recalculateTotals()
    }

    class Party {
        +IdentityDocTypeCat06 identityDocType "6=RUC | 1=DNI | 0=Varios"
        +String identityDocNumber
        +String legalName
        +String tradeName
        +String ubigeoCat13 "6 dígitos"
        +String establishmentCode "0000 domicilio fiscal"
        +String addressLine
        +String email
    }

    class DocumentLine {
        +Int lineNumber
        +UUID productId
        +String sku
        +String unspscCodeCat25 "8 dígitos"
        +String description
        +UnitCodeCat03 unitCode "NIU | BX | KGM | BG | PK | LTR"
        +Decimal quantity "Hasta 10 decimales"
        +Decimal unitValue "Valor unitario sin IGV (10 dec)"
        +Decimal unitPriceWithTax "Precio unitario con IGV (Cat. 16 = 01)"
        +Decimal referenceUnitValue "Valor referencial gratuito (Cat. 16 = 02)"
        +Decimal lineDiscountAmount "Cat. 53 = 00"
        +IgvAffectationCat07 igvAffectation "10 | 11..16 | 20 | 30"
        +IscSystemCat08 iscSystem "01 | 02 | 03 (Nullable)"
        +Decimal iscRateOrFixedAmount
        +Boolean appliesIcbper
        +Decimal lineExtensionAmount "Valor de venta línea (2 dec)"
    }

    class TaxTotal {
        +Decimal totalTaxAmount "IGV + ISC + ICBPER"
        +List~TaxSubtotal~ subtotals
    }

    class TaxSubtotal {
        +Decimal taxableAmount "Base imponible"
        +Decimal taxAmount "Monto del tributo"
        +String taxCategoryId "S | E | O | Z"
        +TaxSchemeCat05 taxScheme "1000 | 2000 | 7152 | 9996 | 9997 | 9998"
        +Decimal percent "18.00 o tasa ISC"
        +String tierRangeCat08 "01 | 02 | 03 (Solo para ISC 2000)"
        +Int icbperBagQuantity "Solo para 7152"
        +Decimal icbperPerUnitAmount "Tarifa vigente por bolsa"
    }

    class LegalMonetaryTotal {
        +Decimal lineExtensionAmount "Total Valor de Venta"
        +Decimal taxInclusiveAmount "Total Precio de Venta"
        +Decimal allowanceTotalAmount "Total Descuentos Globales"
        +Decimal chargeTotalAmount "Total Otros Cargos"
        +Decimal prepaidAmount "Total Anticipos"
        +Decimal payableAmount "Importe Total a Pagar"
    }

    class Product {
        +UUID id
        +String sku
        +String formalName
        +String unspscCodeCat25
        +UnitCodeCat03 unitCode
        +String existenceTypeTabla02 "01 Mercadería"
        +IgvAffectationCat07 defaultIgvAffectation
        +IscSystemCat08 defaultIscSystem
        +Boolean isPlasticBagIcbper
        +Decimal currentStock
        +Decimal currentWeightedAvgCost
    }

    class InventoryLedgerEntry {
        +UUID id
        +String period "YYYYMM"
        +DateTime movementDate
        +UUID productId
        +String establishmentCode "0000"
        +String sunatTabla10DocType "01 | 03 | 07 | 08 | 09 | 00 (Migración)"
        +String documentSeries
        +String documentCorrelative
        +String sunatTabla12Operation "01 Venta | 02 Compra | 05 Devolución | 16 Saldo Inicial | 99 Otros"
        +Decimal quantityIn
        +Decimal unitCostIn
        +Decimal totalCostIn
        +Decimal quantityOut
        +Decimal unitCostOut
        +Decimal totalCostOut
        +Decimal balanceQuantity
        +Decimal balanceUnitCost
        +Decimal balanceTotalCost
        +UUID sourceCpeId "Nullable si proviene de migración"
        +UUID legacyRecordId "Trazabilidad inmutable al sistema antiguo"
    }

    class LegacyMovementRecord {
        +UUID id
        +String rawLegacyId
        +String fechaOriginal
        +Decimal ingresoOriginal
        +Decimal salidaOriginal
        +String productoOriginal
        +String nroDocumentoOriginal
        +String sha256IntegrityHash
        +DateTime migratedAt
    }

    ElectronicDocument "1" *-- "1" Party : Emisor (Supplier)
    ElectronicDocument "1" *-- "1" Party : Cliente (Customer)
    ElectronicDocument "1" *-- "1..*" DocumentLine : Líneas (InvoiceLine)
    ElectronicDocument "1" *-- "1" TaxTotal : Impuestos Globales
    TaxTotal "1" *-- "1..*" TaxSubtotal : Subtotales por Tributo
    ElectronicDocument "1" *-- "1" LegalMonetaryTotal : Totales Monetarios
    DocumentLine "*" --> "1" Product : Referencia Producto
    ElectronicDocument "0..1" --> "1..*" InventoryLedgerEntry : Genera Movimiento Kardex
    LegacyMovementRecord "1" --> "1" InventoryLedgerEntry : Audita y Trazabiliza
```

---

## 1.3 Modelo Entidad-Relación (Persistencia Relacional y Trazabilidad de Migración)

El esquema relacional está diseñado para funcionar idénticamente sobre **SQLite** (en modo local/offline para Windows `.msi` y Android `.apk`) y sobre **PostgreSQL** (en el despliegue centralizado/microservicios).

```mermaid
erDiagram
    PRODUCTS ||--o{ INVENTORY_LEDGER_KARDEX : "registra movimientos"
    PRODUCTS ||--o{ LEGACY_PRODUCT_HOMOLOGATION : "homologa texto legado"
    LEGACY_RAW_MOVEMENTS ||--|| INVENTORY_LEDGER_KARDEX : "trazabilidad 1:1"
    ELECTRONIC_DOCUMENTS ||--|{ ELECTRONIC_DOCUMENT_LINES : "contiene"
    ELECTRONIC_DOCUMENTS ||--|{ ELECTRONIC_DOCUMENT_TAXES : "desglosa"
    ELECTRONIC_DOCUMENTS ||--o{ ELECTRONIC_DOCUMENT_INSTALLMENTS : "cuotas crédito"
    ELECTRONIC_DOCUMENTS ||--o{ INVENTORY_LEDGER_KARDEX : "afecta stock"

    LEGACY_RAW_MOVEMENTS {
        uuid id PK
        string legacy_row_id UK "ID fila original"
        string raw_fecha "Campo original: fecha"
        decimal raw_ingreso "Campo original: ingreso"
        decimal raw_salida "Campo original: salida"
        string raw_producto "Campo original: producto"
        string raw_nro_documento "Campo original: nro_documento"
        string sha256_hash "Hash inmutable de auditoría"
        timestamp imported_at
    }

    LEGACY_PRODUCT_HOMOLOGATION {
        string raw_producto_name PK "Texto exacto en ficha antigua"
        uuid target_product_id FK "Producto formal homologado"
        decimal initial_unit_cost "Costo unitario de apertura"
        string homologated_by
    }

    PRODUCTS {
        uuid id PK
        string sku UK
        string formal_name
        string unspsc_code_cat25 "Catálogo 25 SUNAT (8 dígitos)"
        string unit_code_cat03 "Catálogo 03 (NIU, BX, KGM, BG)"
        string existence_type_tabla02 "Tabla 2 SUNAT (01 Mercadería)"
        string igv_affectation_cat07 "Catálogo 07 (10, 20, 30)"
        string isc_system_cat08 "Catálogo 08 (01, 02, 03 o NULL)"
        decimal isc_rate_or_fixed
        boolean applies_icbper
    }

    INVENTORY_LEDGER_KARDEX {
        uuid id PK
        string period_yyyymm "Formato 12.1 / 13.1"
        timestamp movement_date
        uuid product_id FK
        string establishment_code "Anexo SUNAT (0000)"
        string tabla10_doc_type "01, 03, 07, 08, 00 (Otros/Migración)"
        string doc_series "F001, B001, MIG01"
        string doc_correlative "Correlativo formal"
        string tabla12_operation_type "01 Venta, 02 Compra, 16 Saldo Inicial"
        decimal qty_in
        decimal unit_cost_in
        decimal total_cost_in
        decimal qty_out
        decimal unit_cost_out
        decimal total_cost_out
        decimal balance_qty
        decimal balance_unit_cost "Costo Promedio Ponderado"
        decimal balance_total_cost
        uuid source_cpe_id FK "NULL si es migrado"
        uuid legacy_raw_id FK "Puntero a LEGACY_RAW_MOVEMENTS"
        string legacy_doc_ref "Copia indexada de nro_documento"
    }

    ELECTRONIC_DOCUMENTS {
        uuid id PK
        string doc_type_cat01 "01, 03, 07, 08"
        string operation_type_cat51 "0101"
        string series "F001, B001..."
        int correlative
        date issue_date
        time issue_time
        string currency_cat02 "PEN, USD"
        string customer_doc_type_cat06 "6, 1, 0"
        string customer_doc_number
        string customer_legal_name
        decimal total_gravado
        decimal total_exonerado
        decimal total_inafecto
        decimal total_gratuito
        decimal total_isc
        decimal total_igv
        decimal total_icbper
        decimal payable_amount
        string xml_digest_hash "DigestValue de ds:Signature"
        string qr_payload
        string status "ACCEPTED, OBSERVED, REJECTED, QUEUED_OFFLINE"
        string sunat_cdr_code
        string sunat_cdr_description
    }
```

---

## 1.4 Especificación de Reglas e Invariantes Matemáticas

### A. Invariante 1: Validación de RUC con Algoritmo Módulo 11 (`Catálogo 06 = 6`)
El sistema rechaza en la frontera del dominio cualquier intento de emitir una Factura (`01`) cuyo cliente no posea un RUC válido:
1. Expresión regular: `^(10|15|16|17|20)\d{9}$` (exactamente 11 dígitos numéricos).
2. Cálculo del dígito verificador $d_{11}$ con pesos $W = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]$:
   $$S = \sum_{i=1}^{10} d_i \cdot W_i, \quad R = 11 - (S \bmod 11)$$
   $$d_{11}^{\text{calculado}} = \begin{cases} 0 & \text{si } R = 10 \\ 1 & \text{si } R = 11 \\ R & \text{si } R \in [1..9] \end{cases}$$
   Si $d_{11} \neq d_{11}^{\text{calculado}}$, se lanza `ERR_INVALID_RUC_MOD11`.

---

### B. Invariante 2: Reglas de Identificación en Boletas de Venta (`Catálogo 01 = 03`)
- Si $\text{PayableAmount} \le \text{S/ } 700.00$, se permite emitir a **Clientes Varios** con `Catálogo 06 = 0` y número `"00000000"`.
- Si $\text{PayableAmount} > \text{S/ } 700.00$, es **obligatorio** identificar al adquirente con DNI (`Catálogo 06 = 1`, 8 dígitos `^\d{8}$`), Carnet de Extranjería (`4`) o RUC (`6`). De lo contrario, se lanza `ERR_BOLETA_IDENTIFICATION_REQUIRED_OVER_700`.

---

### C. Invariante 3: Motor Matemático de Impuestos (IGV, Catálogo 08 ISC, ICBPER y Gratuitas)

Para cada línea $i$ del comprobante:

1. **Precisión Decimal (Prevención del Error SUNAT `2017` / `3205`)**:
   - Cantidad (`cbc:InvoicedQuantity`) y Valor Unitario sin impuestos (`cac:Price/cbc:PriceAmount`): **hasta 10 decimales**.
   - Importes totales de línea (`cbc:LineExtensionAmount`) y montos de tributos (`cbc:TaxAmount`): **redondeo comercial Half-Up a 2 decimales** (`ROUND_HALF_UP`).

2. **Cálculo del ISC según el Catálogo N.º 08 de SUNAT (`TierRange` / `TaxScheme = 2000`)**:
   En la comercialización de abarrotes al por mayor y menor (cervezas, licores, bebidas azucaradas, cigarrillos), el **Catálogo N.º 08** define tres fórmulas mutuamente excluyentes:
   - **Código `01` — Sistema al Valor**:
     $$\text{Base}_{\text{ISC},i} = VV_i = \text{round}(Q_i \times V_{u,i} - D_i, 2)$$
     $$\text{ISC}_i = \text{round}\left(\text{Base}_{\text{ISC},i} \times \frac{\text{Tasa}_{\text{ISC}}}{100}, 2\right)$$
   - **Código `02` — Aplicación del Monto Fijo (Específico en Soles por unidad/litro)**:
     $$\text{ISC}_i = \text{round}\left(Q_i \times \text{MontoFijo}_{\text{ISC}}, 2\right)$$
   - **Código `03` — Sistema de Precios de Venta al Público (PVP)**:
     $$\text{Base}_{\text{ISC},i} = \text{round}\left(Q_i \times P_{\text{PVP},i} \times 0.909, 2\right)$$
     $$\text{ISC}_i = \text{round}\left(\text{Base}_{\text{ISC},i} \times \frac{\text{Tasa}_{\text{ISC}}}{100}, 2\right)$$

3. **Impacto del ISC sobre la Base Imponible del IGV (`TaxScheme = 1000`)**:
   Por mandato de la Ley del IGV e ISC (TUO D.S. 055-99-EF), el ISC forma parte de la base imponible del IGV:
   $$\text{Base}_{\text{IGV},i} = VV_i + \text{ISC}_i$$
   $$\text{IGV}_i = \text{round}\left(\text{Base}_{\text{IGV},i} \times 0.18, 2\right)$$

4. **Bonificaciones y Transferencias Gratuitas (`Catálogo 07` $\in \{11..16\}$, `TaxScheme = 9996`)**:
   Común en abarrotes mayoristas (ej. *"Por la compra de 10 sacos, 1 saco de bonificación"*):
   - `cbc:PriceAmount` en `cac:Price` = `0.00`.
   - `cbc:PriceTypeCode` en `cac:PricingReference` = `"02"` (Valor referencial unitario en operaciones no onerosas, **Catálogo 16**).
   - `cbc:LineExtensionAmount` = $\text{round}(Q_i \times V_{\text{ref},i}, 2)$, pero **NO se suma** al `LegalMonetaryTotal/PayableAmount`.

5. **Impuesto al Consumo de las Bolsas de Plástico — ICBPER (`TaxScheme = 7152`)**:
   $$\text{ICBPER}_i = N_{\text{bolsas},i} \times 0.50 \text{ PEN}$$

---

### D. Invariante 4: Valuación de Inventario por Costo Promedio Ponderado (Formato 13.1 SUNAT)
Cada movimiento de entrada actualiza el costo unitario promedio ponderado ($CPP_t$) del producto:
- **En un Ingreso (Compra `Tabla 12 = 02`, Devolución de cliente `05` o Saldo Inicial Migrado `16`)**:
  $$CPP_t = \frac{(Q_{\text{saldo}, t-1} \times CPP_{t-1}) + (Q_{\text{ingreso}, t} \times C_{\text{ingreso}, t})}{Q_{\text{saldo}, t-1} + Q_{\text{ingreso}, t}}$$
- **En una Salida (Venta por Factura/Boleta `Tabla 12 = 01`)**:
  El costo unitario de salida es $C_{\text{salida}, t} = CPP_{t-1}$, manteniendo invariante el $CPP$ hasta la siguiente entrada.

---

## 1.5 Contratos formales de Datos (JSON Schemas Ejecutables)

Los esquemas formales bajo el estándar **JSON Schema Draft 2020-12** se encuentran listos para validación automatizada en la carpeta [`specs/schemas/`](../specs/schemas/):

1. **[`specs/schemas/issue-cpe-command.schema.json`](../specs/schemas/issue-cpe-command.schema.json)**: Contrato de entrada para emisión de Facturas, Boletas, Notas de Crédito y Notas de Débito.
2. **[`specs/schemas/cpe-emission-response.schema.json`](../specs/schemas/cpe-emission-response.schema.json)**: Contrato de salida con resumen tributario, Hash `DigestValue`, cadena QR oficial SUNAT, respuesta CDR y referencias de movimiento Kardex.
3. **[`specs/schemas/legacy-migration-contract.schema.json`](../specs/schemas/legacy-migration-contract.schema.json)**: Contrato de migración masiva para transformar las fichas antiguas (`fecha`, `ingreso`, `salida`, `producto`, `nro_documento`) con homologación de catálogo y validación en seco (`DRY_RUN`).
4. **[`specs/schemas/kardex-formal-12-1-13-1.schema.json`](../specs/schemas/kardex-formal-12-1-13-1.schema.json)**: Contrato de representación de los Libros Electrónicos Formato 12.1 y Formato 13.1 de la RS N.º 234-2006/SUNAT.
