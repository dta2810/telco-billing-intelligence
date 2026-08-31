"""Server-side localization for AcmeTel Billing Intelligence.

Holds the language-dependent strings that the API generates: KPI tile labels
and subtitles, the AI prompts (executive brief + supervisor agent), operational
alert content, and a few narrative fallbacks. The frontend owns its own chrome
strings; this module owns anything the server renders into the response.
"""
from typing import Any


def norm_lang(lang: Any) -> str:
    """Normalize an arbitrary lang value to 'en' or 'es' (default 'es')."""
    return "en" if str(lang or "").lower().startswith("en") else "es"


# ----------------------------------------------------------------------------
# Flat string table (labels, subtitles, fallbacks). Use tr().
# ----------------------------------------------------------------------------

_S: dict[str, dict[str, str]] = {
    "es": {
        # Executive KPI tiles
        "exec.arpu.label": "ARPU mensual",
        "exec.arpu.subtitle": "{n} clientes facturados",
        "exec.collection.label": "Tasa de cobranza",
        "exec.collection.subtitle": "{paid} de {total} pagadas",
        "exec.rar.label": "Revenue en riesgo (60+d)",
        "exec.rar.subtitle": "{n} clientes en mora crítica",
        "exec.disc.label": "Descuentos por vencer (30d)",
        "exec.disc.subtitle": "{n} líneas afectadas",
        "exec.contracts.label": "Contratos por vencer (60d)",
        "exec.contracts.subtitle": "ETF expuesto: ${etf}",
        "exec.overage.label": "% líneas con overage",
        "exec.overage.subtitle": "{n} líneas excedieron quota",
        # Customer KPI tiles
        "cust.total.label": "Clientes activos",
        "cust.total.subtitle": "del portafolio total",
        "cust.mora60.label": "Mora crítica (60+ días)",
        "cust.mora60.subtitle": "requieren acción inmediata",
        "cust.expdisc.label": "Descuento vencido (último mes)",
        "cust.expdisc.subtitle": "factura subió este mes",
        "cust.contract.label": "Contrato por vencer (60d)",
        "cust.contract.subtitle": "ventana de retención",
        "cust.overage.label": "Consumo excedente (3m)",
        "cust.overage.subtitle": "candidatos a upgrade",
        # Narrative fallbacks
        "narrative.unavailable": "AI insights no disponibles.",
        "narrative.unavailable_err": "AI insights no disponibles ({e}).",
        "supervisor.nosummary": "No se pudo generar resumen ejecutivo.",
        "supervisor.error": "Error generando resumen: {e}",
        "genie.noresponse": "Sin respuesta generada.",
    },
    "en": {
        # Executive KPI tiles
        "exec.arpu.label": "Monthly ARPU",
        "exec.arpu.subtitle": "{n} customers billed",
        "exec.collection.label": "Collection rate",
        "exec.collection.subtitle": "{paid} of {total} paid",
        "exec.rar.label": "Revenue at risk (60+d)",
        "exec.rar.subtitle": "{n} customers in critical dunning",
        "exec.disc.label": "Discounts expiring (30d)",
        "exec.disc.subtitle": "{n} lines affected",
        "exec.contracts.label": "Contracts expiring (60d)",
        "exec.contracts.subtitle": "ETF exposed: ${etf}",
        "exec.overage.label": "% lines with overage",
        "exec.overage.subtitle": "{n} lines exceeded quota",
        # Customer KPI tiles
        "cust.total.label": "Active customers",
        "cust.total.subtitle": "of the total portfolio",
        "cust.mora60.label": "Critical dunning (60+ days)",
        "cust.mora60.subtitle": "require immediate action",
        "cust.expdisc.label": "Expired discount (last month)",
        "cust.expdisc.subtitle": "bill went up this month",
        "cust.contract.label": "Contract expiring (60d)",
        "cust.contract.subtitle": "retention window",
        "cust.overage.label": "Overage (3m)",
        "cust.overage.subtitle": "upgrade candidates",
        # Narrative fallbacks
        "narrative.unavailable": "AI insights unavailable.",
        "narrative.unavailable_err": "AI insights unavailable ({e}).",
        "supervisor.nosummary": "Could not generate executive summary.",
        "supervisor.error": "Error generating summary: {e}",
        "genie.noresponse": "No response generated.",
    },
}


def tr(lang: Any, key: str, **kw: Any) -> str:
    lg = norm_lang(lang)
    template = _S[lg].get(key) or _S["es"].get(key) or key
    return template.format(**kw) if kw else template


# ----------------------------------------------------------------------------
# Executive brief prompt (ai_query)
# ----------------------------------------------------------------------------

def build_insights_prompt(lang: Any, period: str, summary_text: str) -> str:
    if norm_lang(lang) == "en":
        return (
            "You are a billing analyst for a LATAM telecom operator. These are the KPIs and "
            f"signals for period {period}:\n\n"
            f"{summary_text}\n\n"
            "Write an executive brief in English, in markdown, with this exact structure "
            "(no extra text outside the bullets):\n\n"
            "**Key finding this month:** _one sentence with a concrete figure_.\n\n"
            "**Risk to watch:** _one sentence with a concrete figure and why it matters_.\n\n"
            "**Opportunity spotted:** _one actionable sentence with a number_.\n\n"
            "**Recommended action:** _a single specific action for the CX or collections "
            "team, with a time horizon (this week / this month)_.\n\n"
            "Use USD amounts with two decimals and thousands separators."
        )
    return (
        "Eres analista de billing de un operador telco LATAM. Estos son los KPIs y "
        f"señales del período {period}:\n\n"
        f"{summary_text}\n\n"
        "Escribe un brief ejecutivo en español neutro, formato markdown con esta estructura "
        "exacta (sin texto adicional fuera de los bullets):\n\n"
        "**Hallazgo principal del mes:** _una oración con dato concreto_.\n\n"
        "**Riesgo a vigilar:** _una oración con dato concreto y por qué importa_.\n\n"
        "**Oportunidad detectada:** _una oración accionable con un número_.\n\n"
        "**Acción recomendada:** _una sola acción específica para el equipo CX o cobranza, "
        "con horizonte de tiempo (esta semana / este mes)_.\n\n"
        "Usa montos en USD con dos decimales y comas para miles. No uses tecnicismos como "
        "'dunning', 'MSISDN' u 'overage' — reemplázalos por 'mora', 'línea' o "
        "'consumo excedente'."
    )


# ----------------------------------------------------------------------------
# Supervisor system prompt (agent chat)
# ----------------------------------------------------------------------------

_SUPERVISOR_ES = """Eres asistente de billing para agentes de servicio al cliente de un operador telco LATAM (postpago).

Tu trabajo: ayudar al agente a RESOLVER la consulta del cliente con un detalle accionable e itemizado. NO resumas en prosa lo que es naturalmente una tabla.

ESTRUCTURA OBLIGATORIA del output (en este orden):

1) Encabezado: `## Detalle - Cliente CUS-XXXXXX` (usa el customer_id real cuando la consulta es de un cliente).
2) Una tabla markdown SIEMPRE que los datos contengan ≥2 filas detalladas (cargos por período, líneas de factura, planes comparados, clientes en una lista). NO RESUMAS LAS FILAS — vuélcalas tal cual a la tabla. La tabla va PRIMERO o INMEDIATAMENTE después del encabezado.
3) 1-3 oraciones de contexto explicando qué muestra la tabla y la causa raíz del patrón.
4) Cierre con UNA línea — escoge según el caso:
   - Si los datos resuelven la pregunta del cliente: `> Siguiente paso: <acción concreta para el agente o el cliente>`.
   - Si los datos están INCOMPLETOS (Genie no devolvió el detalle necesario): NO uses "Recomendación". En su lugar invita al usuario en primera persona plural: `> ¿Quieres que revisemos juntos <qué exactamente> para identificar <qué causa>?` Ejemplo: `> ¿Quieres que revisemos juntos el detalle línea por línea de 2026-03 y 2026-04 para identificar qué cargos cambiaron?`

REGLAS DE TABLA:
- Columnas claras y alineadas: `| col | col | col |` con `|---|---|---:|` separator (la última columna numérica alineada a la derecha con `---:`).
- Una fila por cada registro de los datos crudos. NO consolides ni promedies si los datos vienen detallados.
- Si los datos vienen agregados (ej. solo 1 fila resumen), aún así usa una mini-tabla de 2 columnas (Concepto / Valor).

REGLAS DE CONTENIDO:
- Usa exactamente los datos crudos que recibes; no inventes filas, conceptos ni montos.
- Formatea montos en USD con dos decimales y comas para miles ($1,234.56).
- Usa español neutro. Reemplaza tecnicismos: 'mora' (no dunning), 'línea' (no MSISDN), 'consumo excedente' (no overage), 'cuota equipo' (no device subsidy), 'descuento aplicado' (no discount line), 'plan' (no rate plan).
- Si los datos no contienen lo necesario, NO redactes "Recomendación: Consultar el detalle…". En su lugar usa el cierre invitacional descrito arriba (`> ¿Quieres que…?`).
- No saludes ni te despidas. Empieza con el `## ...` directamente.

EJEMPLO PERFECTO (datos completos):

## Detalle de Cargos - Cliente CUS-000112

| Período | Concepto | Monto |
|---------|----------|------:|
| 2026-04 | Plan Premium 100GB | $54.99 |
| 2026-04 | Cuota equipo | $10.17 |
| 2026-03 | Plan Premium 100GB | $54.99 |
| 2026-03 | Cuota equipo | $10.17 |
| 2026-03 | Descuento aplicado | -$9.90 |

El incremento de $9.90 (+17.9%) se debe exclusivamente a la expiración del descuento que estuvo activo en marzo y no continuó en abril. Los cargos base (plan y cuota de equipo) se mantuvieron constantes.

> Siguiente paso: Comunicar proactivamente al cliente que la promoción finalizó y evaluar si corresponde renovarla por antigüedad o LTV.

EJEMPLO (datos incompletos — invitar a profundizar):

## Detalle - Cliente CUS-000002

| Concepto | Valor |
|----------|------:|
| Factura período 2026-04 | $92.61 |
| Factura período anterior | $58.84 |
| Incremento absoluto | $33.77 |
| Incremento porcentual | 57.4% |

La factura subió $33.77 (+57.4%) entre marzo y abril, pero los datos disponibles solo muestran los totales — sin el desglose por concepto no podemos identificar la causa exacta del aumento.

> ¿Quieres que revisemos juntos el detalle línea por línea de 2026-03 y 2026-04 para identificar qué cargos nuevos, descuentos vencidos o consumos excedentes causaron el incremento?"""


_SUPERVISOR_EN = """You are a billing assistant for customer-service agents of a LATAM telecom operator (postpaid).

Your job: help the agent RESOLVE the customer's inquiry with actionable, itemized detail. Do NOT summarize in prose what is naturally a table.

REQUIRED OUTPUT STRUCTURE (in this order):

1) Header: `## Detail - Customer CUS-XXXXXX` (use the real customer_id when the inquiry is about a customer).
2) A markdown table WHENEVER the data contains ≥2 detailed rows (charges per period, invoice lines, compared plans, customers in a list). DO NOT SUMMARIZE THE ROWS — dump them as-is into the table. The table goes FIRST or IMMEDIATELY after the header.
3) 1-3 sentences of context explaining what the table shows and the root cause of the pattern.
4) Close with ONE line — choose by case:
   - If the data resolves the customer's question: `> Next step: <concrete action for the agent or the customer>`.
   - If the data is INCOMPLETE (Genie did not return the needed detail): do NOT use "Recommendation". Instead invite the user in the first person plural: `> Would you like us to review together <what exactly> to identify <what cause>?` Example: `> Would you like us to review together the line-by-line detail of 2026-03 and 2026-04 to identify which charges changed?`

TABLE RULES:
- Clear, aligned columns: `| col | col | col |` with a `|---|---|---:|` separator (the last numeric column right-aligned with `---:`).
- One row per record in the raw data. Do NOT consolidate or average if the data comes detailed.
- If the data comes aggregated (e.g. a single summary row), still use a 2-column mini-table (Item / Value).

CONTENT RULES:
- Use exactly the raw data you receive; do not invent rows, items or amounts.
- Format amounts in USD with two decimals and thousands separators ($1,234.56).
- Write in English. Native billing terms are fine (dunning, MSISDN, overage, device fee, discount line, rate plan).
- If the data does not contain what is needed, do NOT write "Recommendation: Check the detail…". Instead use the invitational close described above (`> Would you like us to…?`).
- No greetings or sign-offs. Start directly with the `## ...`.

PERFECT EXAMPLE (complete data):

## Charge Detail - Customer CUS-000112

| Period | Item | Amount |
|--------|------|-------:|
| 2026-04 | Premium 100GB plan | $54.99 |
| 2026-04 | Device fee | $10.17 |
| 2026-03 | Premium 100GB plan | $54.99 |
| 2026-03 | Device fee | $10.17 |
| 2026-03 | Discount applied | -$9.90 |

The $9.90 increase (+17.9%) is due exclusively to the expiration of the discount that was active in March and did not continue in April. The base charges (plan and device fee) stayed constant.

> Next step: Proactively tell the customer the promotion ended and evaluate whether to renew it based on tenure or LTV.

EXAMPLE (incomplete data — invite to dig deeper):

## Detail - Customer CUS-000002

| Item | Value |
|------|------:|
| Invoice period 2026-04 | $92.61 |
| Prior period invoice | $58.84 |
| Absolute increase | $33.77 |
| Percentage increase | 57.4% |

The bill went up $33.77 (+57.4%) between March and April, but the available data only shows the totals — without the item-level breakdown we cannot identify the exact cause of the increase.

> Would you like us to review together the line-by-line detail of 2026-03 and 2026-04 to identify which new charges, expired discounts or overage caused the increase?"""


def supervisor_prompt(lang: Any) -> str:
    return _SUPERVISOR_EN if norm_lang(lang) == "en" else _SUPERVISOR_ES


def build_supervisor_prompt(lang: Any, question: str, genie_text: str, data_summary: str) -> str:
    if norm_lang(lang) == "en":
        return (
            f"{_SUPERVISOR_EN}\n\n"
            f"Executive question: {question}\n\n"
            f"Genie raw text:\n{genie_text}\n"
            f"{data_summary}\n\n"
            "Respond in light markdown. "
            "Start directly with the answer — no greetings or preambles."
        )
    return (
        f"{_SUPERVISOR_ES}\n\n"
        f"Pregunta del ejecutivo: {question}\n\n"
        f"Texto crudo de Genie:\n{genie_text}\n"
        f"{data_summary}\n\n"
        "Responde en formato markdown ligero. "
        "Empieza directamente con la respuesta — sin saludos ni preámbulos."
    )


def scope_question(lang: Any, customer_id: str, question: str) -> str:
    if norm_lang(lang) == "en":
        return f"For customer {customer_id}: {question}"
    return f"Para el cliente {customer_id}: {question}"


def data_summary_label(lang: Any, n_rows: int, extra: int) -> tuple[str, str]:
    """Returns (header, more_line_template). more_line_template has {n}."""
    if norm_lang(lang) == "en":
        return (f"\n\nResults ({n_rows} rows):\n", "... and {n} more rows\n")
    return (f"\n\nResultados ({n_rows} filas):\n", "... y {n} filas más\n")


# ----------------------------------------------------------------------------
# Operational alerts
# ----------------------------------------------------------------------------

ALERT_TEMPLATES: dict[str, dict[str, list[dict]]] = {
    "es": {
        "promo": [
            {
                "title": "Promo Loyalty 25% — clientes consumer +24 meses",
                "body": "Activa para fidelización. Aplicar a clientes consumer con +24 meses de antigüedad y al menos 1 línea activa. Vigente hasta 2026-05-31.",
                "valid_to": "2026-05-31",
                "action_label": "Ofrecer al cliente elegible",
                "severity": "good",
            },
            {
                "title": "Bundle Internet+Móvil 18% para SMB",
                "body": "Descuento mensual sobre paquete combinado. Sólo segmento SMB con contrato vigente. Hasta 2026-06-15.",
                "valid_to": "2026-06-15",
                "action_label": "Activar desde CRM",
                "severity": "good",
            },
            {
                "title": "Roaming Caribe Gratis (verano 2026)",
                "body": "Add-on sin cargo durante el período vacacional. Mencionar antes de cerrar la consulta si el cliente viaja.",
                "valid_to": "2026-08-31",
                "action_label": None,
                "severity": "good",
            },
        ],
        "disruption": [
            {
                "region": "Norte",
                "title": "Mantenimiento programado Región Norte",
                "body": "Ventana 2026-05-02 02:00–04:00 hrs. Servicio móvil intermitente. Verificar zona del cliente antes de escalar.",
                "valid_to": "2026-05-02",
                "severity": "warn",
            },
            {
                "region": "Centro",
                "title": "Cobertura intermitente Región Centro",
                "body": "Reportes esporádicos desde 2026-04-28 14:00. Red investigando. Usar disculpa estandarizada en CRM.",
                "valid_to": None,
                "severity": "warn",
            },
            {
                "region": "Caribe",
                "title": "Falla en sitio celular Región Caribe",
                "body": "Sitio fuera de servicio desde 2026-04-29 06:00, ETA reparación ~6 hrs. Clientes en Bayahibe y Punta Cana afectados.",
                "valid_to": None,
                "severity": "alert",
            },
            {
                "region": "Sur",
                "title": "Trabajos de fibra Región Sur",
                "body": "Corte planificado 2026-05-03 01:00–03:00. Internet fijo intermitente. No aplica a móvil.",
                "valid_to": "2026-05-03",
                "severity": "warn",
            },
            {
                "region": "Pacífico",
                "title": "Saturación celular Región Pacífico",
                "body": "Tráfico elevado por evento masivo en David. Velocidad reducida. Normalización esperada después de 2026-04-30 22:00.",
                "valid_to": "2026-05-01",
                "severity": "warn",
            },
        ],
        "policy": [
            {
                "title": "Plan de pago 3 cuotas sin interés (mora 1–30d)",
                "body": "Clientes en primera etapa de mora pueden tomar plan de 3 pagos sin interés. Aplica desde 2026-04-25.",
                "valid_to": None,
                "action_label": "Habilitado en CRM",
                "severity": "info",
            },
            {
                "title": "Nuevo flujo de retención por baja anticipada",
                "body": "Si el cliente solicita baja con contrato vigente, ofrecer primero downgrade gratuito a Lite por 3 meses antes de cobrar ETF.",
                "valid_to": None,
                "action_label": "Ver guion en CRM",
                "severity": "info",
            },
        ],
        "catalog": [
            {
                "title": "Plan Lite 5GB descontinuado",
                "body": "Desde 2026-05-01 no se ofrece a clientes nuevos. Clientes actuales mantienen sus condiciones; no forzar migración.",
                "valid_to": None,
                "severity": "info",
            },
            {
                "title": "Lanzamiento AcmeTel Pro 50GB",
                "body": "Nuevo plan disponible en catálogo desde 2026-04-15. Posicionado entre Pro 30GB y Premium 100GB.",
                "valid_to": None,
                "severity": "info",
            },
        ],
        "daily": [
            {
                "title": "Pico esperado por descuentos vencidos",
                "body": "51 clientes perdieron descuentos en la corrida de abril. Esperar consultas tipo \"¿por qué subió mi factura?\" entre 9:00 y 12:00. Usar el chat con detalle itemizado para resolver.",
                "valid_to": "2026-05-05",
                "severity": "alert",
            },
            {
                "title": "Día 5 del mes: corte por mora 90+",
                "body": "Hoy se ejecuta corte automático para clientes en stage 4. Esperar consultas de reactivación. Validar plan de pago antes de prometer reconexión.",
                "valid_to": "2026-04-30",
                "severity": "alert",
            },
        ],
    },
    "en": {
        "promo": [
            {
                "title": "Loyalty 25% promo — consumer customers 24+ months",
                "body": "Active for retention. Apply to consumer customers with 24+ months tenure and at least 1 active line. Valid through 2026-05-31.",
                "valid_to": "2026-05-31",
                "action_label": "Offer to eligible customer",
                "severity": "good",
            },
            {
                "title": "Internet+Mobile bundle 18% for SMB",
                "body": "Monthly discount on the combined bundle. SMB segment with an active contract only. Through 2026-06-15.",
                "valid_to": "2026-06-15",
                "action_label": "Activate from CRM",
                "severity": "good",
            },
            {
                "title": "Free Caribbean Roaming (summer 2026)",
                "body": "No-charge add-on during the holiday period. Mention it before closing the inquiry if the customer travels.",
                "valid_to": "2026-08-31",
                "action_label": None,
                "severity": "good",
            },
        ],
        "disruption": [
            {
                "region": "North",
                "title": "Scheduled maintenance North Region",
                "body": "Window 2026-05-02 02:00–04:00. Intermittent mobile service. Verify the customer's area before escalating.",
                "valid_to": "2026-05-02",
                "severity": "warn",
            },
            {
                "region": "Central",
                "title": "Intermittent coverage Central Region",
                "body": "Sporadic reports since 2026-04-28 14:00. Network investigating. Use the standardized apology in CRM.",
                "valid_to": None,
                "severity": "warn",
            },
            {
                "region": "Caribbean",
                "title": "Cell site outage Caribbean Region",
                "body": "Site down since 2026-04-29 06:00, repair ETA ~6 hrs. Customers in Bayahibe and Punta Cana affected.",
                "valid_to": None,
                "severity": "alert",
            },
            {
                "region": "South",
                "title": "Fiber works South Region",
                "body": "Planned outage 2026-05-03 01:00–03:00. Intermittent fixed internet. Does not affect mobile.",
                "valid_to": "2026-05-03",
                "severity": "warn",
            },
            {
                "region": "Pacific",
                "title": "Cell congestion Pacific Region",
                "body": "High traffic from a mass event in David. Reduced speed. Normalization expected after 2026-04-30 22:00.",
                "valid_to": "2026-05-01",
                "severity": "warn",
            },
        ],
        "policy": [
            {
                "title": "3-installment interest-free payment plan (dunning 1–30d)",
                "body": "Customers in the first dunning stage can take a 3-payment interest-free plan. In effect since 2026-04-25.",
                "valid_to": None,
                "action_label": "Enabled in CRM",
                "severity": "info",
            },
            {
                "title": "New early-cancellation retention flow",
                "body": "If the customer requests cancellation with an active contract, first offer a free downgrade to Lite for 3 months before charging the ETF.",
                "valid_to": None,
                "action_label": "See script in CRM",
                "severity": "info",
            },
        ],
        "catalog": [
            {
                "title": "Lite 5GB plan discontinued",
                "body": "As of 2026-05-01 not offered to new customers. Existing customers keep their terms; do not force migration.",
                "valid_to": None,
                "severity": "info",
            },
            {
                "title": "AcmeTel Pro 50GB launch",
                "body": "New plan available in the catalog since 2026-04-15. Positioned between Pro 30GB and Premium 100GB.",
                "valid_to": None,
                "severity": "info",
            },
        ],
        "daily": [
            {
                "title": "Spike expected from expired discounts",
                "body": "51 customers lost discounts in the April run. Expect \"why did my bill go up?\" inquiries between 9:00 and 12:00. Use the itemized-detail chat to resolve.",
                "valid_to": "2026-05-05",
                "severity": "alert",
            },
            {
                "title": "Day 5 of the month: 90+ dunning cutoff",
                "body": "Today the automatic cutoff runs for stage-4 customers. Expect reactivation inquiries. Validate a payment plan before promising reconnection.",
                "valid_to": "2026-04-30",
                "severity": "alert",
            },
        ],
    },
}


def alert_templates(lang: Any) -> dict[str, list[dict]]:
    return ALERT_TEMPLATES[norm_lang(lang)]
