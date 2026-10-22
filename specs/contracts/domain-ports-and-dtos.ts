/**
 * ============================================================================
 * ABC SOFTWARE CORP — ESPECIFICACIÓN DE CONTRATOS Y PUERTOS (SPEC-FIRST)
 * ============================================================================
 * Este archivo define los contratos formales de tipos, catálogos SUNAT (Anexo 8),
 * DTOs y Puertos de Entrada/Salida que desacoplan el patrón MVC Monolítico Limpio
 * para permitir una migración transparente hacia Arquitectura Hexagonal y Microservicios.
 * ============================================================================
 */

// ----------------------------------------------------------------------------
// 1. CATÁLOGOS OFICIALES DE LA SUNAT (ANEXO N.º 8 - RS N.º 097-2012/SUNAT)
// ----------------------------------------------------------------------------

/** Catálogo N.º 01: Código de Tipo de Documento */
export type SunatDocumentTypeCat01 =
  | '01' // Factura Electrónica
  | '03' // Boleta de Venta Electrónica
  | '07' // Nota de Crédito Electrónica
  | '08'; // Nota de Débito Electrónica

/** Catálogo N.º 02: Códigos de Tipo de Monedas (ISO 4217) */
export type SunatCurrencyCodeCat02 = 'PEN' | 'USD';

/** Catálogo N.º 03: Códigos de Tipo de Unidad de Medida Comercial (UN/ECE Rec 20) */
export type SunatUnitCodeCat03 =
  | 'NIU' // Unidad (Bienes)
  | 'BX'  // Caja
  | 'KGM' // Kilogramo
  | 'LTR' // Litro
  | 'BG'  // Bolsa / Saco
  | 'PK'  // Paquete
  | 'DZN'; // Docena

/** Catálogo N.º 05: Códigos de Tipos de Tributos */
export type SunatTaxSchemeIdCat05 =
  | '1000' // IGV - Impuesto General a las Ventas (VAT)
  | '2000' // ISC - Impuesto Selectivo al Consumo (EXC)
  | '7152' // ICBPER - Impuesto a la Bolsa Plástica (OTH)
  | '9995' // Exportación (FRE)
  | '9996' // Gratuito / Bonificaciones (FRE)
  | '9997' // Exonerado (VAT)
  | '9998'; // Inafecto (FRE)

/** Catálogo N.º 06: Códigos de Tipos de Documentos de Identidad */
export type SunatIdentityDocTypeCat06 =
  | '6' // Registro Único de Contribuyentes (RUC - Validación Módulo 11)
  | '1' // Documento Nacional de Identidad (DNI - 8 dígitos)
  | '4' // Carnet de Extranjería
  | '7' // Pasaporte
  | '0'; // Doc. Trib. No Domiciliado sin RUC (Clientes Varios <= S/ 700)

/** Catálogo N.º 07: Códigos de Tipo de Afectación del IGV */
export type SunatIgvAffectationCat07 =
  | '10' // Gravado - Operación Onerosa
  | '11' // Gravado - Retiro por premio
  | '12' // Gravado - Retiro por donación
  | '13' // Gravado - Retiro
  | '14' // Gravado - Retiro por publicidad
  | '15' // Gravado - Bonificaciones (Muy usado en abarrotes mayoristas)
  | '16' // Gravado - Retiro por entrega a trabajadores
  | '20' // Exonerado - Operación Onerosa
  | '21' // Exonerado - Transferencia Gratuita
  | '30' // Inafecto - Operación Onerosa
  | '31' // Inafecto - Retiro por Bonificación
  | '40'; // Exportación de Bienes o Servicios

/**
 * PUNTO CLAVE EXIGIDO: Catálogo N.º 08 de SUNAT
 * Códigos de Tipos de Sistema de Cálculo del ISC
 */
export type SunatIscSystemCat08 =
  | '01' // Sistema al Valor (Tasa porcentual sobre el Valor de Venta)
  | '02' // Aplicación del Monto Fijo (Soles específicos por unidad o litro)
  | '03'; // Sistema de Precios de Venta al Público (PVP sugerido)

/** Catálogo N.º 16: Códigos de Tipo de Precio de Venta Unitario */
export type SunatPriceTypeCat16 =
  | '01' // Precio unitario (incluye el IGV, ISC e ICBPER)
  | '02'; // Valor referencial unitario en operaciones no onerosas (Gratuitas)

/** Catálogo N.º 51: Código de Tipo de Operación */
export type SunatOperationTypeCat51 = '0101' | '0102' | '0200' | '1001';

/** Tablas SUNAT RS N.º 234-2006 para Kardex Formato 12.1 y 13.1 */
export type SunatKardexDocTypeTabla10 = '00' | '01' | '03' | '07' | '08' | '09';
export type SunatKardexOperationTabla12 =
  | '01' // Venta
  | '02' // Compra
  | '05' // Devolución recibida
  | '16' // Saldo Inicial (Usado en apertura de migración legada)
  | '99'; // Otros (Movimientos históricos internos del software legado)

// ----------------------------------------------------------------------------
// 2. CONTRATOS DE TRANSFERENCIA DE DATOS (DTOs)
// ----------------------------------------------------------------------------

export interface IscConfigurationDto {
  readonly systemCodeCat08: SunatIscSystemCat08;
  readonly rateOrFixedAmount: number;
  readonly suggestedRetailPrice?: number | null;
}

export interface IssueCpeItemDto {
  readonly sku: string;
  readonly unspscCode?: string | null;
  readonly description: string;
  readonly unitCode: SunatUnitCodeCat03;
  readonly quantity: number;
  readonly unitValue: number;
  readonly referenceUnitValue?: number | null;
  readonly discountAmount?: number;
  readonly igvAffectationCode: SunatIgvAffectationCat07;
  readonly iscConfiguration?: IscConfigurationDto | null;
  readonly appliesIcbper?: boolean;
}

export interface IssueCpeCommandDto {
  readonly idempotencyKey: string;
  readonly documentTypeCode: SunatDocumentTypeCat01;
  readonly operationTypeCode: SunatOperationTypeCat51;
  readonly series: string;
  readonly correlative: number;
  readonly issueDate: string;
  readonly issueTime: string;
  readonly dueDate?: string | null;
  readonly currencyCode: SunatCurrencyCodeCat02;
  readonly establishmentCode?: string;
  readonly customer: {
    readonly identityDocType: SunatIdentityDocTypeCat06;
    readonly identityDocNumber: string;
    readonly legalName: string;
    readonly ubigeo?: string | null;
    readonly address?: string | null;
    readonly email?: string | null;
  };
  readonly paymentTerms: {
    readonly condition: 'Contado' | 'Credito';
    readonly netPendingAmount?: number | null;
    readonly installments?: ReadonlyArray<{
      readonly installmentId: string;
      readonly amount: number;
      readonly dueDate: string;
    }>;
  };
  readonly billingReference?: {
    readonly refDocType: '01' | '03';
    readonly refSeriesCorrelative: string;
    readonly refIssueDate?: string;
    readonly reasonCode: string;
    readonly reasonDescription: string;
  } | null;
  readonly items: ReadonlyArray<IssueCpeItemDto>;
}

export interface CpeEmissionResponseDto {
  readonly documentId: string;
  readonly fullDocumentNumber: string;
  readonly status: 'ACCEPTED' | 'OBSERVED' | 'REJECTED' | 'QUEUED_OFFLINE';
  readonly xmlFileName: string;
  readonly digestValueHash: string;
  readonly qrCodeString: string;
  readonly sunatCdr?: {
    readonly responseCode: string;
    readonly description: string;
    readonly notes: ReadonlyArray<string>;
  } | null;
  readonly taxSummary: {
    readonly gravadoTotal: number;
    readonly exoneradoTotal: number;
    readonly inafectoTotal: number;
    readonly gratuitoTotal: number;
    readonly iscTotal: number;
    readonly igvTotal: number;
    readonly icbperTotal: number;
    readonly payableAmount: number;
  };
  readonly kardexMovementIds: ReadonlyArray<string>;
}

// ----------------------------------------------------------------------------
// 3. CONTRATO DE MIGRACIÓN DE DATOS LEGADOS (TRAZABILIDAD 100%)
// ----------------------------------------------------------------------------

/** Representa exactamente una ficha del software básico actual */
export interface LegacyWarehouseCardDto {
  readonly legacyRowId: string;
  readonly fecha: string;
  readonly ingreso: number;
  readonly salida: number;
  readonly producto: string;
  readonly nro_documento: string;
}

export interface LegacyMigrationCommandDto {
  readonly batchId: string;
  readonly executionMode: 'DRY_RUN' | 'COMMIT';
  readonly defaultEstablishmentCode: string;
  readonly records: ReadonlyArray<LegacyWarehouseCardDto>;
  readonly productHomologationMap: Readonly<
    Record<
      string,
      {
        readonly sku: string;
        readonly formalName: string;
        readonly sunatUnitCodeCat03: SunatUnitCodeCat03;
        readonly unspscCodeCat25?: string;
        readonly existenceTypeTabla02: string;
        readonly defaultIgvAffectationCat07: SunatIgvAffectationCat07;
        readonly defaultIscSystemCat08?: SunatIscSystemCat08 | null;
        readonly initialUnitCost: number;
      }
    >
  >;
}

export interface MigrationReportResponseDto {
  readonly batchId: string;
  readonly executionMode: 'DRY_RUN' | 'COMMIT';
  readonly totalRead: number;
  readonly totalMigrated: number;
  readonly unmappedProducts: ReadonlyArray<string>;
  readonly negativeStockAlerts: ReadonlyArray<string>;
  readonly auditTrail: ReadonlyArray<{
    readonly legacyRowId: string;
    readonly legacyDocNumber: string;
    readonly assignedKardexId: string;
    readonly assignedFormalNumber: string;
    readonly sha256Hash: string;
  }>;
}

// ----------------------------------------------------------------------------
// 4. PUERTOS ARQUITECTÓNICOS (MVC DESACOPLADO -> ARQUITECTURA HEXAGONAL)
// ----------------------------------------------------------------------------

export type Result<T, E> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

export interface DomainRuleError {
  readonly errorCode: string;
  readonly sunatEquivalentCode: string;
  readonly message: string;
  readonly normativeReference: string;
}

/** PUERTO DE ENTRADA: Invocado por CpeController (MVC) o API Gateway (Hexagonal) */
export interface IIssueCpeUseCasePort {
  execute(command: IssueCpeCommandDto): Promise<Result<CpeEmissionResponseDto, DomainRuleError>>;
}

/** PUERTO DE ENTRADA: Invocado por LegacyMigrationController (MVC) */
export interface IMigrateLegacyKardexUseCasePort {
  execute(command: LegacyMigrationCommandDto): Promise<Result<MigrationReportResponseDto, DomainRuleError>>;
}

/** PUERTO DE SALIDA: Construcción y validación local contra UBL-Invoice-2.1.xsd */
export interface IUbl21XmlBuilderPort {
  buildAndValidateInvoiceXml(command: IssueCpeCommandDto): Promise<Result<{ xmlFileName: string; unsignedXml: string }, DomainRuleError>>;
}

/** PUERTO DE SALIDA: Firma Digital XAdES-BES con Certificado X.509 (.pfx) */
export interface IXmlDigitalSignerPort {
  signUblXml(unsignedXml: string): Promise<Result<{ signedXml: string; digestValueHash: string }, DomainRuleError>>;
}

/** PUERTO DE SALIDA: Comunicación SOAP/REST con OSE (ej. Nubefact) o SUNAT SOL */
export interface ISunatOseGatewayPort {
  sendBill(zipFileName: string, zipBase64: string): Promise<
    Result<
      {
        responseCode: string;
        description: string;
        notes: ReadonlyArray<string>;
        cdrZipBase64: string;
      },
      { isNetworkOrTimeoutError: boolean; message: string }
    >
  >;
}
