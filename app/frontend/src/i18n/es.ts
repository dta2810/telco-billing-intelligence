// Spanish dictionary. Keys are shared with en.ts — keep them in sync.
export const es: Record<string, string> = {
  // Header / nav
  'nav.home': 'Inicio',
  'nav.exec': 'Ejecutivo',
  'nav.customer': 'Clientes',
  'brand.tagline': 'Billing Intelligence',
  'lang.toggle': 'Idioma',

  // Role selection (landing)
  'role.subtitle':
    'Asistente conversacional para resolver consultas de billing — descuentos, mora, contratos y mejoras de plan — con datos en tiempo real y acciones accionables.',
  'role.exec.title': 'Vista Ejecutiva',
  'role.exec.desc':
    'KPIs del portafolio, insights generados con IA, y dashboard analítico. Para CFO, CMO y COO.',
  'role.customer.title': 'Vista Cliente',
  'role.customer.desc':
    'Lista filtrable de clientes con señales de churn, mora y descuentos. Drill-down a un cliente para resolver consultas en lenguaje natural.',
  'role.connecting': 'Conectando…',
  'role.connectedTo': 'Conectado a',
  'role.arpuLast': 'ARPU último',
  'role.notConnected': 'No conectado a Databricks',

  // Common
  'common.loading': 'Cargando…',
  'common.loadingKpis': 'Cargando KPIs…',
  'common.error': 'Error',
  'common.noMatches': 'Sin coincidencias.',
  'common.loadFailed': 'No se pudo cargar la lista. Intenta de nuevo.',

  // Executive page
  'exec.title': 'Vista Ejecutiva',
  'exec.subtitle': 'KPIs operacionales del portafolio · Período {period}',

  // KPI tile
  'kpi.vsPrev': 'vs período anterior',

  // Operational alerts
  'alerts.title': 'Alertas operacionales',
  'alerts.subtitle': 'Avisos del turno · {n} activos',
  'alerts.seeLess': 'Ver menos',
  'alerts.seeAll': 'Ver todas',
  'alerts.since': 'desde {date}',
  'alertcat.promo': 'Promoción',
  'alertcat.disruption': 'Disrupción',
  'alertcat.policy': 'Procedimiento',
  'alertcat.catalog': 'Catálogo',
  'alertcat.daily': 'Aviso del día',

  // Months (short)
  'month.1': 'Ene',
  'month.2': 'Feb',
  'month.3': 'Mar',
  'month.4': 'Abr',
  'month.5': 'May',
  'month.6': 'Jun',
  'month.7': 'Jul',
  'month.8': 'Ago',
  'month.9': 'Sep',
  'month.10': 'Oct',
  'month.11': 'Nov',
  'month.12': 'Dic',

  // AI insights
  'ai.title': 'AI Insights — Brief Ejecutivo',
  'ai.generating': 'Generando análisis con IA…',
  'ai.none': 'No hay insights disponibles.',

  // Dunning chart
  'dunning.title': 'Distribución por etapa de mora',
  'dunning.stage.0': 'Al día',
  'dunning.stage.1': '1–30 días',
  'dunning.stage.2': '31–60 días',
  'dunning.stage.3': '61–90 días',
  'dunning.stage.4': '+90 días',
  'dunning.stagePrefix': 'Etapa {n}',
  'dunning.tooltip': '{pagos} pagos · {clientes} clientes',

  // ARPU chart
  'arpu.title': 'ARPU mensual — últimos 6 meses',

  // Usage chart
  'usage.title': 'Evolución de consumo — últimos 6 meses',
  'usage.data': 'Datos (GB)',
  'usage.overage': 'Excedente (GB)',
  'usage.roaming': 'Roaming (GB)',
  'usage.voice': 'Voz (min)',
  'usage.sms': 'SMS',
  'usage.totalInvoice': 'Total factura: {total}',
  'usage.noInvoice': 'Sin factura',

  // Invoice chart
  'invoice.title': 'Evolución de la factura — últimos 6 meses',
  'invoice.plan': 'Plan',
  'invoice.device': 'Equipo',
  'invoice.overage': 'Excedente',
  'invoice.discount': 'Descuento',
  'invoice.total': 'Total: {total}',

  // Trail tables
  'table.byMonth': 'Detalle por mes',
  'table.month': 'Mes',
  'invtbl.plan': 'Plan',
  'invtbl.device': 'Equipo',
  'invtbl.overage': 'Excedente',
  'invtbl.discount': 'Descuento',
  'invtbl.total': 'Total',
  'usgtbl.data': 'Datos',
  'usgtbl.overage': 'Excedente',
  'usgtbl.roaming': 'Roaming',
  'usgtbl.voice': 'Voz',
  'usgtbl.sms': 'SMS',

  // Cohort explorer
  'cohort.title': 'Análisis por cohorte',
  'cohort.subtitle': 'Filtra un grupo y explora con el asistente de IA',
  'cohort.inCohort': 'Clientes en cohorte',
  'cohort.activateFilter': 'Activa un filtro arriba para ver candidatos.',
  'cohort.contextCohort': 'cohorte: {label}',
  'cohort.contextPortfolio': 'datos del portafolio',
  'cohort.preset.mora_60':
    'Lista los clientes con mayor saldo en mora 60+ días, ordenados por monto descendente.',
  'cohort.preset.expired_discount':
    '¿Cuántos clientes perdieron su descuento el mes pasado y cuál es el aumento promedio en su factura?',
  'cohort.preset.contract_expiring':
    '¿Cuántos contratos vencen en los próximos 60 días, por segmento, y cuál es el ETF total expuesto?',
  'cohort.preset.overage':
    '¿Qué planes tienen mayor tasa de consumo excedente y cuántos clientes están afectados por plan?',
  'cohort.fallback.0':
    '¿Hay una caída sostenida del ARPU desde agosto 2025? Muestra el trend mes a mes y el delta vs período anterior.',
  'cohort.fallback.1': '¿Cuál es el ARPU por plan en el último período?',
  'cohort.fallback.2': '¿Cuántos clientes están en mora 60+ días por segmento?',
  'cohort.fallback.3': '¿Qué planes tienen mayor tasa de consumo excedente?',
  'cohort.fallback.4': 'Top 5 clientes con mayor saldo vencido',
  'cohort.fallback.5':
    '¿Cuántos contratos vencen en los próximos 60 días y cuál es su ETF total?',

  // Filters + segments (values stay stable; only labels translate)
  'filter.mora_60': 'Mora 60+',
  'filter.expired_discount': 'Descuento vencido',
  'filter.contract_expiring': 'Contrato por vencer',
  'filter.overage': 'Consumo excedente',
  'segment.todos': 'todos',
  'segment.consumer': 'consumer',
  'segment.smb': 'smb',
  'segment.enterprise': 'enterprise',

  // Genie chat
  'genie.assistant': 'AI Assistant',
  'genie.newQuery': 'Nueva consulta',
  'genie.askAbout': 'Haz una pregunta sobre {context}',
  'genie.viewData': 'Ver detalle de datos (SQL · resultados)',
  'genie.genieQuery': 'Consulta generada por Genie:',
  'genie.results': 'Resultados ({n}):',
  'genie.analyzing': 'Analizando con IA…',
  'genie.placeholder': 'Pregunta sobre los datos…',
  'genie.noAnswer': 'Sin respuesta.',
  'genie.unknownError': 'Error desconocido',

  // Customer page
  'cust.title': 'Asistente CX — Clientes',
  'cust.subtitle':
    'Busca el cliente con el que estás hablando y resuelve su consulta.',
  'cust.searchCustomer': 'Buscar cliente',
  'cust.searchHint':
    'Escribe el ID, el nombre o el número del cliente. Selecciona del listado para abrir su detalle.',
  'cust.close': '← Cerrar y buscar otro cliente',
  'cust.noneSelected': 'Todavía no seleccionas un cliente',
  'cust.emptyHintPre': 'Búscalo arriba por número, nombre o ID (',
  'cust.emptyHintPost':
    '), y selecciónalo de la lista. Verás su resumen, las acciones disponibles y un chat con memoria para resolver dudas al instante.',

  // Search box
  'search.placeholder': 'Escribe ID, nombre o número del cliente',
  'search.clear': 'Limpiar',
  'search.searching': 'Buscando…',
  'search.noMatchesFor': 'Sin coincidencias para "{q}"',
  'search.alert': '{n} alerta',
  'search.alerts': '{n} alertas',

  // List panel
  'list.placeholder': 'ID, nombre o número…',
  'list.count': '{n} clientes',
  'list.emptyHint':
    'Escribe el ID o nombre del cliente, o activa un filtro rápido para listar candidatos.',
  'list.noMatch': 'Sin clientes que coincidan.',

  // Customer detail
  'detail.tab.summary': 'Resumen',
  'detail.tab.actions': 'Acciones',
  'detail.tab.chat': 'Conversar',
  'detail.signup': 'alta {date}',
  'detail.activeLines': '{n} línea(s) activa(s)',
  'detail.loadingUsage': 'Cargando consumo…',
  'detail.loadingInvoices': 'Cargando facturas…',
  'detail.lastInvoice': 'Detalle de la última factura',
  'detail.invoiceMeta': '· {period} · total {amt}',
  'detail.col.concept': 'Concepto',
  'detail.col.description': 'Descripción',
  'detail.col.amount': 'Monto',
  'detail.activeContract': 'Contrato vigente',
  'detail.contractEnds': 'Termina el',
  'detail.daysRemaining': '{n} días restantes',
  'detail.autoRenew': ' · auto-renovación activa',
  'detail.chatContext': 'cliente {id}',
  'detail.chargeType.recurring': 'Plan',
  'detail.chargeType.device_subsidy': 'Cuota equipo',
  'detail.chargeType.usage_overage': 'Consumo excedente',
  'detail.chargeType.discount': 'Descuento',
  'detail.chargeType.one_time': 'Cargo único',
  'detail.chargeType.tax': 'Impuesto (IVA/ITBIS)',
  'detail.q.0': '¿Por qué subió mi factura este mes?',
  'detail.q.1': '¿Cuál es mi plan y por qué mi consumo es diferente cada mes?',
  'detail.q.2': 'Detalle extendido de facturación últimos 3 meses',
  'detail.q.3': '¿Cuál fue mi consumo de datos en los últimos 3 meses?',
  'detail.q.4': '¿Cuándo termina mi contrato?',
  'detail.q.5': '¿Tengo cargos por equipo en mi factura?',
  'detail.q.6': '¿Cuál fue mi descuento más reciente y cuándo terminó?',

  // Status chips — shared
  'chip.calc': '¿Cómo lo calculamos?',
  'chip.howToOffer': 'Cómo ofrecerlo',
  'chip.howCalculated': 'Cómo se calcula',
  // Discount
  'chip.disc.expired.title': 'Descuento vencido',
  'chip.disc.expired.body':
    '{promo} venció el {date} ({days} días). Tu factura subió este mes.',
  'chip.disc.expiring.title': 'Descuento por vencer',
  'chip.disc.expiring.body': '{promo} vence en {days} días.',
  'chip.disc.active.title': 'Descuento activo',
  'chip.disc.active.body': '{promo} aplica hasta {date}.',
  'chip.disc.noActive.title': 'Sin descuento activo',
  'chip.disc.noActive.body':
    '{promo} finalizó hace {days} días. El aumento de la factura actual viene de otra causa.',
  'chip.disc.none.title': 'Sin descuento',
  'chip.disc.none.body': 'No tiene descuento aplicado actualmente.',
  // Payment
  'chip.pay.current.title': 'Al día',
  'chip.pay.current.body': 'Sin saldo pendiente.',
  'chip.pay.critical.title': 'Mora crítica',
  'chip.pay.critical.body': 'Saldo {balance}, {days} días en mora. {action}',
  'chip.pay.pending.title': 'Saldo pendiente',
  'chip.pay.pending.body': '{balance} · {days} días en mora. {action}',
  // NBO
  'chip.nbo.reasoning':
    'Analizamos el patrón histórico de uso del cliente y lo comparamos con los planes disponibles para identificar el mejor calce de servicio. La recomendación prioriza la experiencia y el calce al consumo real, no la reducción del ticket.',
  'chip.nbo.overage.title': 'Oportunidad NBO',
  'chip.nbo.overage.body': 'Sugerir {plan} — más capacidad, evita excedentes.',
  'chip.nbo.overage.s0':
    'Comunica al cliente que viene pagando consumo excedente y que {plan} le entrega más capacidad para evitar esos cargos extra.',
  'chip.nbo.overage.s1':
    'Frase: "vemos que cada mes te pasas del paquete; este plan te calza mejor y no pagas excedentes".',
  'chip.nbo.overage.s2':
    'Si tiene contrato vigente, simula el cambio antes de ofrecer (verifica ETF).',
  'chip.nbo.underuse.title': 'Subutiliza su plan',
  'chip.nbo.underuse.body': 'Si pide ajustar costo: {plan}.',
  'chip.nbo.underuse.s0':
    'Cliente subutiliza su plan, pero NO ofrezcas downgrade proactivamente.',
  'chip.nbo.underuse.s1':
    'Si el cliente pregunta "¿hay un plan más barato?" o pide reducir su factura, ahí sí presenta la opción.',
  'chip.nbo.underuse.s2':
    'Si solo está consultando uso, refuerza el valor del plan actual sin sugerir cambio.',
  'chip.nbo.match.title': 'Plan ajustado',
  'chip.nbo.match.body': 'Plan actual calza con el consumo. No proponer cambio.',
  'chip.nbo.match.s0':
    'Plan actual está bien dimensionado — no propongas cambio.',
  'chip.nbo.match.s1':
    'Aprovecha para ofrecer add-ons (roaming, datos adicionales) o upgrade de equipo si aplica.',
  'chip.nbo.match.s2': 'Refuerza fidelidad: "tu plan está hecho a tu medida, te cuidamos".',
  'chip.nbo.fit.title': 'Recomendación',
  'chip.nbo.fit.body': 'Si quiere optimizar: {plan}.',
  'chip.nbo.fit.s0':
    'Si el cliente quiere optimizar su servicio, presenta {plan} como mejor calce al consumo.',
  'chip.nbo.fit.s1': 'Si el cliente está satisfecho, no fuerces el cambio.',

  // Plan simulator
  'sim.title': 'Simular cambio de plan',
  'sim.selectPlan': 'Selecciona un plan…',
  'sim.simulate': 'Simular',
  'sim.currentPlan': 'Plan actual',
  'sim.proposedPlan': 'Plan propuesto',
  'sim.data': 'Datos',
  'sim.voice': 'Voz',
  'sim.sms': 'SMS',
  'sim.unlimited': 'ilimitados',
  'sim.unlimitedF': 'ilimitada',
  'sim.perMonth': '/mes',
  'sim.cost': 'Costo',
  'sim.noChange': 'sin cambio',
  'sim.annualSaving': 'ahorro anual: {v}',
  'sim.annualExtra': 'extra anual: {v}',
  'sim.min': 'min',
};
