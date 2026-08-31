# Evidence — Part 3 (foundation): UC functions

Four Unity Catalog SQL functions on `acmetel_gold` — the agent's deterministic tools (also
callable by Genie). Ported to English, parametrized to the real catalog/schema.

## Functions created — SUCCESS

```
check_discount_status   get_next_best_offer   get_payment_status   simulate_plan_change
```

## Live tests (real seeded customers)

`check_discount_status('CUS-000011')`:
```
active | Prepay 12% OFF | days_to_expire=43 | "...still active until 2026-10-13."
```

`get_payment_status('CUS-000002')` (delinquent):
```
outstanding_balance=92.61  days_overdue=11  dunning_stage=3
next_action="Formal delinquency notice. Suspension risk."
```

`simulate_plan_change('CUS-000002', 'PLAN-001')` (downgrade):
```
current=AcmeTel Family 60GB  new=AcmeTel Lite 5GB
monthly_delta=-50.00  annual_delta=-600.00
warning="Active contract until 2028-02-25; switching may apply a penalty of $256.48.
         Careful: the new plan has 5GB vs your current 60GB. Overage risk."
```

_Last updated: 2026-08-31_
