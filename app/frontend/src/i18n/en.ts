// English dictionary. Keys are shared with es.ts — keep them in sync.
export const en: Record<string, string> = {
  // Header / nav
  'nav.home': 'Home',
  'nav.exec': 'Executive',
  'nav.customer': 'Customers',
  'brand.tagline': 'Billing Intelligence',
  'lang.toggle': 'Language',

  // Role selection (landing)
  'role.subtitle':
    'Conversational assistant to resolve billing inquiries — discounts, dunning, contracts and plan upgrades — with real-time data and actionable steps.',
  'role.exec.title': 'Executive View',
  'role.exec.desc':
    'Portfolio KPIs, AI-generated insights, and analytical dashboard. For CFO, CMO and COO.',
  'role.customer.title': 'Customer View',
  'role.customer.desc':
    'Filterable customer list with churn, dunning and discount signals. Drill down into a customer to resolve inquiries in natural language.',
  'role.connecting': 'Connecting…',
  'role.connectedTo': 'Connected to',
  'role.arpuLast': 'Latest ARPU',
  'role.notConnected': 'Not connected to Databricks',

  // Common
  'common.loading': 'Loading…',
  'common.loadingKpis': 'Loading KPIs…',
  'common.error': 'Error',
  'common.noMatches': 'No matches.',
  'common.loadFailed': 'Could not load the list. Try again.',

  // Executive page
  'exec.title': 'Executive View',
  'exec.subtitle': 'Portfolio operational KPIs · Period {period}',

  // KPI tile
  'kpi.vsPrev': 'vs prior period',

  // Operational alerts
  'alerts.title': 'Operational alerts',
  'alerts.subtitle': 'Shift notices · {n} active',
  'alerts.seeLess': 'See less',
  'alerts.seeAll': 'See all',
  'alerts.since': 'since {date}',
  'alertcat.promo': 'Promotion',
  'alertcat.disruption': 'Disruption',
  'alertcat.policy': 'Procedure',
  'alertcat.catalog': 'Catalog',
  'alertcat.daily': 'Daily notice',

  // Months (short)
  'month.1': 'Jan',
  'month.2': 'Feb',
  'month.3': 'Mar',
  'month.4': 'Apr',
  'month.5': 'May',
  'month.6': 'Jun',
  'month.7': 'Jul',
  'month.8': 'Aug',
  'month.9': 'Sep',
  'month.10': 'Oct',
  'month.11': 'Nov',
  'month.12': 'Dec',

  // AI insights
  'ai.title': 'AI Insights — Executive Brief',
  'ai.generating': 'Generating AI analysis…',
  'ai.none': 'No insights available.',

  // Dunning chart
  'dunning.title': 'Distribution by dunning stage',
  'dunning.stage.0': 'Current',
  'dunning.stage.1': '1–30 days',
  'dunning.stage.2': '31–60 days',
  'dunning.stage.3': '61–90 days',
  'dunning.stage.4': '+90 days',
  'dunning.stagePrefix': 'Stage {n}',
  'dunning.tooltip': '{pagos} payments · {clientes} customers',

  // ARPU chart
  'arpu.title': 'Monthly ARPU — last 6 months',

  // Usage chart
  'usage.title': 'Usage trend — last 6 months',
  'usage.data': 'Data (GB)',
  'usage.overage': 'Overage (GB)',
  'usage.roaming': 'Roaming (GB)',
  'usage.voice': 'Voice (min)',
  'usage.sms': 'SMS',
  'usage.totalInvoice': 'Invoice total: {total}',
  'usage.noInvoice': 'No invoice',

  // Invoice chart
  'invoice.title': 'Invoice trend — last 6 months',
  'invoice.plan': 'Plan',
  'invoice.device': 'Device',
  'invoice.overage': 'Overage',
  'invoice.discount': 'Discount',
  'invoice.total': 'Total: {total}',

  // Trail tables
  'table.byMonth': 'Detail by month',
  'table.month': 'Month',
  'invtbl.plan': 'Plan',
  'invtbl.device': 'Device',
  'invtbl.overage': 'Overage',
  'invtbl.discount': 'Discount',
  'invtbl.total': 'Total',
  'usgtbl.data': 'Data',
  'usgtbl.overage': 'Overage',
  'usgtbl.roaming': 'Roaming',
  'usgtbl.voice': 'Voice',
  'usgtbl.sms': 'SMS',

  // Cohort explorer
  'cohort.title': 'Cohort analysis',
  'cohort.subtitle': 'Filter a group and explore with the AI assistant',
  'cohort.inCohort': 'Customers in cohort',
  'cohort.activateFilter': 'Activate a filter above to see candidates.',
  'cohort.contextCohort': 'cohort: {label}',
  'cohort.contextPortfolio': 'portfolio data',
  'cohort.preset.mora_60':
    'List the customers with the highest 60+ day overdue balance, sorted by amount descending.',
  'cohort.preset.expired_discount':
    'How many customers lost their discount last month and what is the average increase in their bill?',
  'cohort.preset.contract_expiring':
    'How many contracts expire in the next 60 days, by segment, and what is the total ETF exposed?',
  'cohort.preset.overage':
    'Which plans have the highest overage rate and how many customers are affected per plan?',
  'cohort.fallback.0':
    'Is there a sustained ARPU decline since August 2025? Show the month-over-month trend and the delta vs the prior period.',
  'cohort.fallback.1': 'What is the ARPU by plan in the latest period?',
  'cohort.fallback.2': 'How many customers are 60+ days overdue by segment?',
  'cohort.fallback.3': 'Which plans have the highest overage rate?',
  'cohort.fallback.4': 'Top 5 customers with the highest overdue balance',
  'cohort.fallback.5':
    'How many contracts expire in the next 60 days and what is their total ETF?',

  // Filters + segments (values stay stable; only labels translate)
  'filter.mora_60': 'Dunning 60+',
  'filter.expired_discount': 'Expired discount',
  'filter.contract_expiring': 'Contract expiring',
  'filter.overage': 'Overage',
  'segment.todos': 'all',
  'segment.consumer': 'consumer',
  'segment.smb': 'smb',
  'segment.enterprise': 'enterprise',

  // Genie chat
  'genie.assistant': 'AI Assistant',
  'genie.newQuery': 'New query',
  'genie.askAbout': 'Ask a question about {context}',
  'genie.viewData': 'View data detail (SQL · results)',
  'genie.genieQuery': 'Query generated by Genie:',
  'genie.results': 'Results ({n}):',
  'genie.analyzing': 'Analyzing with AI…',
  'genie.placeholder': 'Ask about the data…',
  'genie.noAnswer': 'No answer.',
  'genie.unknownError': 'Unknown error',

  // Customer page
  'cust.title': 'CX Assistant — Customers',
  'cust.subtitle':
    "Find the customer you're speaking with and resolve their inquiry.",
  'cust.searchCustomer': 'Find customer',
  'cust.searchHint':
    'Type the customer ID, name, or phone number. Select from the list to open their detail.',
  'cust.close': '← Close and search another customer',
  'cust.noneSelected': 'No customer selected yet',
  'cust.emptyHintPre': 'Search above by phone, name, or ID (',
  'cust.emptyHintPost':
    '), then pick one from the list. You will see their summary, available actions, and a memory-aware chat to resolve questions on the spot.',

  // Search box
  'search.placeholder': 'Type customer ID, name, or phone number',
  'search.clear': 'Clear',
  'search.searching': 'Searching…',
  'search.noMatchesFor': 'No matches for "{q}"',
  'search.alert': '{n} alert',
  'search.alerts': '{n} alerts',

  // List panel
  'list.placeholder': 'ID, name, or phone…',
  'list.count': '{n} customers',
  'list.emptyHint':
    'Type the customer ID or name, or activate a quick filter to list candidates.',
  'list.noMatch': 'No matching customers.',

  // Customer detail
  'detail.tab.summary': 'Summary',
  'detail.tab.actions': 'Actions',
  'detail.tab.chat': 'Chat',
  'detail.signup': 'joined {date}',
  'detail.activeLines': '{n} active line(s)',
  'detail.loadingUsage': 'Loading usage…',
  'detail.loadingInvoices': 'Loading invoices…',
  'detail.lastInvoice': 'Latest invoice detail',
  'detail.invoiceMeta': '· {period} · total {amt}',
  'detail.col.concept': 'Item',
  'detail.col.description': 'Description',
  'detail.col.amount': 'Amount',
  'detail.activeContract': 'Active contract',
  'detail.contractEnds': 'Ends on',
  'detail.daysRemaining': '{n} days remaining',
  'detail.autoRenew': ' · auto-renewal on',
  'detail.chatContext': 'customer {id}',
  'detail.chargeType.recurring': 'Plan',
  'detail.chargeType.device_subsidy': 'Device fee',
  'detail.chargeType.usage_overage': 'Overage',
  'detail.chargeType.discount': 'Discount',
  'detail.chargeType.one_time': 'One-time charge',
  'detail.chargeType.tax': 'Tax (VAT)',
  'detail.q.0': 'Why did my bill go up this month?',
  'detail.q.1': 'What is my plan and why is my usage different each month?',
  'detail.q.2': 'Extended billing detail for the last 3 months',
  'detail.q.3': 'What was my data usage over the last 3 months?',
  'detail.q.4': 'When does my contract end?',
  'detail.q.5': 'Are there device charges on my bill?',
  'detail.q.6': 'What was my most recent discount and when did it end?',

  // Status chips — shared
  'chip.calc': 'How we calculate it',
  'chip.howToOffer': 'How to offer it',
  'chip.howCalculated': "How it's calculated",
  // Discount
  'chip.disc.expired.title': 'Expired discount',
  'chip.disc.expired.body':
    '{promo} expired on {date} ({days} days ago). Your bill went up this month.',
  'chip.disc.expiring.title': 'Discount expiring',
  'chip.disc.expiring.body': '{promo} expires in {days} days.',
  'chip.disc.active.title': 'Active discount',
  'chip.disc.active.body': '{promo} applies until {date}.',
  'chip.disc.noActive.title': 'No active discount',
  'chip.disc.noActive.body':
    '{promo} ended {days} days ago. The current bill increase comes from another cause.',
  'chip.disc.none.title': 'No discount',
  'chip.disc.none.body': 'No discount currently applied.',
  // Payment
  'chip.pay.current.title': 'Up to date',
  'chip.pay.current.body': 'No outstanding balance.',
  'chip.pay.critical.title': 'Critical dunning',
  'chip.pay.critical.body': 'Balance {balance}, {days} days overdue. {action}',
  'chip.pay.pending.title': 'Outstanding balance',
  'chip.pay.pending.body': '{balance} · {days} days overdue. {action}',
  // NBO
  'chip.nbo.reasoning':
    "We analyze the customer's historical usage pattern and compare it with the available plans to find the best service fit. The recommendation prioritizes experience and fit to real usage, not lowering the ticket.",
  'chip.nbo.overage.title': 'NBO opportunity',
  'chip.nbo.overage.body': 'Suggest {plan} — more capacity, avoids overage.',
  'chip.nbo.overage.s0':
    'Tell the customer they have been paying overage and that {plan} gives them more capacity to avoid those extra charges.',
  'chip.nbo.overage.s1':
    'Phrasing: "we see you go over your bundle every month; this plan fits you better and you avoid overage".',
  'chip.nbo.overage.s2':
    'If they have an active contract, simulate the change before offering (check the ETF).',
  'chip.nbo.underuse.title': 'Underusing their plan',
  'chip.nbo.underuse.body': 'If they ask to reduce cost: {plan}.',
  'chip.nbo.underuse.s0':
    'The customer is underusing their plan, but do NOT proactively offer a downgrade.',
  'chip.nbo.underuse.s1':
    'If the customer asks "is there a cheaper plan?" or wants to reduce their bill, then present the option.',
  'chip.nbo.underuse.s2':
    'If they are only checking usage, reinforce the value of the current plan without suggesting a change.',
  'chip.nbo.match.title': 'Well-sized plan',
  'chip.nbo.match.body': 'Current plan fits the usage. Do not propose a change.',
  'chip.nbo.match.s0': 'The current plan is well sized — do not propose a change.',
  'chip.nbo.match.s1':
    'Take the chance to offer add-ons (roaming, extra data) or a device upgrade if it applies.',
  'chip.nbo.match.s2':
    'Reinforce loyalty: "your plan is tailored to you, we\'ve got you covered".',
  'chip.nbo.fit.title': 'Recommendation',
  'chip.nbo.fit.body': 'If they want to optimize: {plan}.',
  'chip.nbo.fit.s0':
    'If the customer wants to optimize their service, present {plan} as the best fit to their usage.',
  'chip.nbo.fit.s1': 'If the customer is satisfied, do not force the change.',

  // Plan simulator
  'sim.title': 'Simulate plan change',
  'sim.selectPlan': 'Select a plan…',
  'sim.simulate': 'Simulate',
  'sim.currentPlan': 'Current plan',
  'sim.proposedPlan': 'Proposed plan',
  'sim.data': 'Data',
  'sim.voice': 'Voice',
  'sim.sms': 'SMS',
  'sim.unlimited': 'unlimited',
  'sim.unlimitedF': 'unlimited',
  'sim.perMonth': '/mo',
  'sim.cost': 'Cost',
  'sim.noChange': 'no change',
  'sim.annualSaving': 'annual saving: {v}',
  'sim.annualExtra': 'annual extra: {v}',
  'sim.min': 'min',
};
