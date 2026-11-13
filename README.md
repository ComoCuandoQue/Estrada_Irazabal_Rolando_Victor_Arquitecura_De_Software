# 📦 ABC Software Corp — Arquitectura, Especificación Spec-First y Motor de Facturación Electrónica OASIS UBL 2.1 (SUNAT)

![Metodología](https://img.shields.io/badge/Metodolog%C3%ADa-Spec--First-0A66C2?style=for-the-badge)
![Estándar OASIS](https://img.shields.io/badge/OASIS-UBL--Invoice--2.1.xsd-2EA44F?style=for-the-badge)
![Normativa SUNAT](https://img.shields.io/badge/SUNAT-RS_097--2012_%7C_RS_234--2006_%7C_Anexo_8-D9381E?style=for-the-badge)
![Arquitectura](https://img.shields.io/badge/Arquitectura-MVC_Limpio_%E2%86%92_Hexagonal-7B2CBF?style=for-the-badge)
![Plataformas](https://img.shields.io/badge/Target-Windows_(.msi)_%7C_Android_(.apk)-F59E0B?style=for-the-badge)

> **Proyecto Integral de Arquitectura de Software** para la modernización tecnológica y cumplimiento normativo tributario de **ABC Software Corp** (comercializadora de abarrotes y mercadería al por mayor y menor).
>
> El repositorio está estructurado en **tres módulos de ingeniería complementarios**:
> 1. **Módulo I — Caso de Estudio y Análisis Normativo Integral**
> 2. **Módulo II — Especificaciones Técnicas y Contratos (Spec-First)**
> 3. **Módulo III — Motor de Generación y Validación Estricta de XML a partir de `UBL-Invoice-2.1.xsd`**

---

## 🧭 Índice General por Módulos de Ingeniería

### Módulo I — Caso de Estudio y Análisis Normativo Integral
| Documento | Contenido Principal |
| :--- | :--- |
| 📄 [`docs/00-descripcion-del-caso.md`](./docs/00-descripcion-del-caso.md) | Diagnóstico del software básico actual (`fecha`, `ingreso`, `salida`, `producto`, `nro_documento`), exigencias de la SUNAT (**RS N.º 097-2012**, **RS N.º 234-2006**, **Anexo N.º 8** y **Catálogo 08 de ISC**), restricciones arquitectónicas innegociables y descubrimiento de casos de uso con benchmarking frente a **Nubefact**. |

### Módulo II — Diseño Arquitectónico y Especificaciones Técnicas (Spec-First)
| # | Componente de Especificación | Documento Técnico | Contratos y Esquemas Formales |
| :-: | :--- | :--- | :--- |
| **01** | **Modelo de Dominio y Contratos (DTOs / Schemas)** | 📄 [`docs/01-modelo-dominio-y-contratos.md`](./docs/01-modelo-dominio-y-contratos.md) | • [`issue-cpe-command.schema.json`](./specs/schemas/issue-cpe-command.schema.json)<br>• [`cpe-emission-response.schema.json`](./specs/schemas/cpe-emission-response.schema.json)<br>• [`legacy-migration-contract.schema.json`](./specs/schemas/legacy-migration-contract.schema.json)<br>• [`kardex-formal-12-1-13-1.schema.json`](./specs/schemas/kardex-formal-12-1-13-1.schema.json) |
| **02** | **Arquitectura MVC Limpio con Visión a Hexagonal** | 📄 [`docs/02-arquitectura-mvc-a-hexagonal.md`](./docs/02-arquitectura-mvc-a-hexagonal.md) | • [`domain-ports-and-dtos.ts`](./specs/contracts/domain-ports-and-dtos.ts) *(Puertos de Entrada/Salida e Inversión de Dependencias)* |
| **03** | **Especificación de Endpoints / Servicios y Casos de Uso** | 📄 [`docs/03-especificacion-endpoints-y-casos-uso.md`](./docs/03-especificacion-endpoints-y-casos-uso.md) | • [`abc-facturacion-kardex-api.openapi.yaml`](./specs/openapi/abc-facturacion-kardex-api.openapi.yaml) *(OpenAPI 3.1.0)* |
| **04** | **Matriz de Trazabilidad Normativa (SUNAT $\leftrightarrow$ UBL 2.1)** | 📄 [`docs/04-matriz-trazabilidad-normativa-ubl.md`](./docs/04-matriz-trazabilidad-normativa-ubl.md) | • [`20555999113-01-F001-145-ubl21-sample.xml`](./specs/ubl-examples/20555999113-01-F001-145-ubl21-sample.xml) |

### Módulo III — Implementación del Motor Generador y Validador XML (`UBL-Invoice-2.1.xsd`)
| Componente | Ruta en el Repositorio | Descripción Técnica |
| :--- | :--- | :--- |
| **Documentación de Implementación** | 📄 [`docs/05-implementacion-generador-xml-ubl21-xsd.md`](./docs/05-implementacion-generador-xml-ubl21-xsd.md) | Anatomía de `<xs:sequence>` en `UBL-Invoice-2.1.xsd`, arquitectura del generador por puertos y guía de ejecución. |
| **Esquemas XSD Oficiales OASIS** | 📁 [`xsd/maindoc/UBL-Invoice-2.1.xsd`](./xsd/maindoc/UBL-Invoice-2.1.xsd)<br>📁 [`xsd/common/`](./xsd/common/) | Esquemas oficiales OASIS UBL 2.1 completos para validación estructural offline sin dependencias externas. |
| **Núcleo de Dominio Tributario (`M`)** | 🐍 [`src/core_model/domain/entities.py`](./src/core_model/domain/entities.py)<br>🐍 [`src/core_model/domain/ruc_validator.py`](./src/core_model/domain/ruc_validator.py)<br>🐍 [`src/core_model/domain/tax_engine.py`](./src/core_model/domain/tax_engine.py) | Algoritmo **Módulo 11** de RUC, motor matemático de **IGV (18%)**, **ISC Catálogo 08 (`01`, `02`, `03`)**, **ICBPER (`7152`)** y **Bonificaciones (`9996`)**. |
| **Puertos y Casos de Uso (`M`)** | 🐍 [`src/core_model/application/ports.py`](./src/core_model/application/ports.py)<br>🐍 [`src/core_model/application/use_cases.py`](./src/core_model/application/use_cases.py) | Contratos `IUblInvoiceXmlGeneratorPort` e `IXsdSchemaValidatorPort` orquestados por `IssueElectronicInvoiceUseCase`. |
| **Adaptadores UBL 2.1 y XSD** | 🐍 [`src/infrastructure_adapters/ubl21_xml_generator.py`](./src/infrastructure_adapters/ubl21_xml_generator.py)<br>🐍 [`src/infrastructure_adapters/xsd_schema_validator.py`](./src/infrastructure_adapters/xsd_schema_validator.py) | Construcción DOM/XML conforme a `UBL-Invoice-2.1.xsd` y validador XSD con `lxml.etree.XMLSchema`. |
| **Controlador MVC y Demo** | 🐍 [`src/controllers/invoice_controller.py`](./src/controllers/invoice_controller.py)<br>🐍 [`src/demo_generate_and_validate.py`](./src/demo_generate_and_validate.py) | Controlador MVC y demostración ejecutable que genera y valida 3 escenarios reales en [`output/`](./output/). |
| **Comprobantes XML Generados** | 📄 [`output/20555999110-01-F001-145.xml`](./output/20555999110-01-F001-145.xml)<br>📄 [`output/20555999110-01-F001-146.xml`](./output/20555999110-01-F001-146.xml)<br>📄 [`output/20555999110-03-B001-890.xml`](./output/20555999110-03-B001-890.xml)<br>📄 [`output/20600695771-01-F001-145.xml`](./output/20600695771-01-F001-145.xml) | Facturas y Boletas UBL 2.1 generadas por el motor, firmadas con XMLDSig y validadas al 100% contra `UBL-Invoice-2.1.xsd`. |
| **Evidencia CDR SUNAT / Nubefact (`ResponseCode = 0`)** | ✅ [`output/R-20600695771-01-F001-145-cdr-sunat.xml`](./output/R-20600695771-01-F001-145-cdr-sunat.xml) | Constancia de Recepción (`ApplicationResponse`) oficial obtenida en `probar-xml.nubefact.com` (*"La Factura numero F001-145, ha sido aceptada"*). |
| **Suite de Pruebas Automatizadas** | 🧪 [`tests/test_ubl21_invoice_generation.py`](./tests/test_ubl21_invoice_generation.py) | Pruebas unitarias de Módulo 11, Catálogo 08 ISC, tope de S/ 700 en Boletas y conformidad XSD. |

---

## 🏗️ Flujo de Arquitectura: Del Modelo MVC a la Validación `UBL-Invoice-2.1.xsd`

```mermaid
flowchart LR
    subgraph MVC_Layer["Controlador y Modelo (MVC Desacoplado)"]
        CTRL["InvoiceMvcController"]
        UC["IssueElectronicInvoiceUseCase"]
        DOM["Dominio Tributario\n• Validador RUC Mod 11\n• Motor IGV / ISC Cat. 08 / ICBPER"]
    end

    subgraph Ports["Puertos de Salida"]
        P_GEN["IUblInvoiceXmlGeneratorPort"]
        P_VAL["IXsdSchemaValidatorPort"]
    end

    subgraph Adapters["Adaptadores UBL 2.1 & XSD"]
        GEN["OasisUbl21XmlGeneratorAdapter"]
        VAL["OasisXsdSchemaValidatorAdapter"]
        XSD[("xsd/maindoc/\nUBL-Invoice-2.1.xsd")]
    end

    CTRL --> UC
    UC --> DOM
    UC --> P_GEN
    UC --> P_VAL
    GEN -. "implementa" .-> P_GEN
    VAL -. "implementa" .-> P_VAL
    VAL --> XSD
```

---

## 🚀 Guía Paso a Paso desde Cero: Cómo Ejecutar el Generador XML y Validador XSD

Cualquier persona puede reproducir la generación de comprobantes UBL 2.1 y su validación contra `UBL-Invoice-2.1.xsd` siguiendo estos pasos desde cero:

### Paso 0: Requisitos Previos (Programas Necesarios)
Necesitas tener instalado **Python 3.10 o superior** (incluye `pip`) y opcionalmente **Git**:
- **Verificar si ya tienes Python**: Abre **PowerShell** o **CMD** y ejecuta `python --version`.
- **Si no tienes Python instalado en Windows**:
  - Instálalo desde [python.org/downloads](https://www.python.org/downloads/) (marcando la casilla **"Add python.exe to PATH"** al instalar), o ejecuta en PowerShell:
    ```powershell
    winget install -e --id Python.Python.3.12
    ```
- **Si no tienes Git instalado en Windows** *(opcional)*:
  ```powershell
  winget install -e --id Git.Git
  ```

---

### Paso 1: Obtener el Proyecto (Clonar con Git o Descargar ZIP)

**Opción A — Clonando con Git (Recomendado):**
```bash
git clone https://github.com/ComoCuandoQue/Estrada_Irazabal_Rolando_Victor_Arquitecura_De_Software.git
cd Estrada_Irazabal_Rolando_Victor_Arquitecura_De_Software
```

**Opción B — Sin usar Git (Descarga directa):**
1. En la página de GitHub del repositorio, haz clic en el botón verde **`<> Code`** $\rightarrow$ **`Download ZIP`**.
2. Descomprime el archivo `.zip` en tu computadora.
3. Abre una terminal (**PowerShell** o **CMD**) dentro de la carpeta descomprimida.

---

### Paso 2: Crear Entorno Virtual (Opcional) e Instalar Librerías (`requirements.txt`)

El motor utiliza tres librerías de Python listadas en [`requirements.txt`](./requirements.txt):
- `lxml`: Construcción DOM/XML, canonización W3C C14N y motor validador `XMLSchema` contra `UBL-Invoice-2.1.xsd`.
- `cryptography`: Generación de llaves RSA-2048, certificados digitales X.509 y firma criptográfica `RSA-SHA256` (`ds:Signature`).
- `xmlschema`: Soporte complementario de inspección de esquemas XSD 1.0/1.1.

Ejecuta en tu terminal:

```powershell
# (Opcional) Crear y activar un entorno virtual limpio en Windows:
python -m venv .venv
.\.venv\Scripts\activate

# Instalar todas las dependencias necesarias:
pip install -r requirements.txt
```
*(O si prefieres instalarlas directamente en una sola línea: `pip install lxml cryptography xmlschema`)*

---

### Paso 3: Ejecutar el Generador de XML UBL 2.1 y Validador `UBL-Invoice-2.1.xsd`

Desde la carpeta raíz del proyecto, ejecuta:

```bash
python -m src.demo_generate_and_validate
```

**¿Qué hace este comando automáticamente?**
1. Carga el esquema oficial [`xsd/maindoc/UBL-Invoice-2.1.xsd`](./xsd/maindoc/UBL-Invoice-2.1.xsd) y sus 14 esquemas `xsd/common/*.xsd`.
2. Valida los RUCs mediante el **Algoritmo Módulo 11** de SUNAT.
3. Calcula los impuestos (**IGV 18%**, **Catálogo 08 de ISC** \[`01` Al Valor, `02` Monto Fijo, `03` PVP\], **ICBPER `7152`** y **Bonificaciones Gratuitas `9996`**).
4. Genera los archivos XML en la carpeta [`output/`](./output/), los firma digitalmente con `RSA-SHA256` + Certificado `X.509` y los valida contra `UBL-Invoice-2.1.xsd`, mostrando en consola:
   ```text
   [Escenario 1] Archivo Generado : output/20555999110-01-F001-145.xml
     - Validacion XSD OASIS  : CONFORME: El documento XML cumple al 100% con el esquema OASIS UBL-Invoice-2.1.xsd
   ```

---

### Paso 4: Ejecutar la Suite de Pruebas Unitarias y de Integración XSD

Para correr los 4 tests automatizados que verifican el motor tributario y la validación XSD:

```bash
python -m unittest discover -s tests -v
```
Verás al final: `Ran 4 tests ... OK`.

---

### Paso 5: Cómo Comprobar el XML en Vivo en `https://probar-xml.nubefact.com/`

1. Abre el archivo generado [`output/20600695771-01-F001-145.xml`](./output/20600695771-01-F001-145.xml) y copia todo su contenido.
2. Ingresa a **[https://probar-xml.nubefact.com/](https://probar-xml.nubefact.com/)** y pega el XML en el editor izquierdo (**"Pega o Arrastra tu xml"**).
3. **Para probar con `SUNAT`**:
   - En la lista desplegable central selecciona **`SUNAT`** y haz clic en **`Enviar`**.
   - En el panel derecho recibirás la Constancia de Recepción (`<ar:ApplicationResponse>`) con `<cbc:ResponseCode>0</cbc:ResponseCode>` y `<cbc:Description>La Factura numero F001-145, ha sido aceptada</cbc:Description>` (cuya copia está guardada en [`output/R-20600695771-01-F001-145-cdr-sunat.xml`](./output/R-20600695771-01-F001-145-cdr-sunat.xml)).
4. **Para probar con `OSE`**:
   - Como el correlativo `F001-145` ya fue registrado en nuestra prueba previa (lo que devuelve `Código 1033: El comprobante fue registrado previamente`), cambia únicamente la línea `<cbc:ID>F001-145</cbc:ID>` por un correlativo nuevo (ej. `<cbc:ID>F001-98765</cbc:ID>`), asegúrate de que `<cbc:IssueDate>` tenga la fecha del día actual, marca **`Firmar`** y haz clic en **`Enviar`**.
