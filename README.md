# Fuzzy Logic Based Hybrid Load Balancing for Solar–Grid Supply with Tiered Load Shedding

Simulation code for the paper *“Fuzzy Logic Based Hybrid Load Balancing for Solar–Grid Supply with Tiered Load Shedding: A Simulation Study”* (J. N. Wanzala and M. Byamukama, Mbarara University of Science and Technology).

The code implements a four-input, two-output Mamdani fuzzy controller that jointly selects the supply source (solar/battery or grid) and the permitted load tiers (critical, flexible, non-essential) for a premises-scale solar–battery–grid installation, and compares it with three benchmarks on a one-minute, 24-hour energy-balance model.

## Contents

| File | Purpose |
|---|---|
| `sim_core.py` | Membership functions, 18-rule Mamdani inference with centroid defuzzification, plant model, scenario generator, the four controllers (fuzzy, threshold ATS baseline, ATS with critical-load priority, crisp rule-based tiered controller) and the metrics (Tier-1 availability, solar utilisation, grid energy, CWUE, PRI, switching events) |
| `experiments.py` | Nominal scenario, seven stress cases and the 100-run Monte Carlo evaluation (fixed seed 2026) |
| `tables.py` | Writes the LaTeX bodies of Tables 5–7 to `results/` |
| `figs.py` | Figures 2 (membership functions), 4 (key metrics) and 5 (Monte Carlo distributions) |
| `run_all.py` | Runs the whole pipeline |
| `appendix/` | The controller and plant listings printed in Appendices B and C of the paper |

## Running

```bash
pip install -r requirements.txt
python run_all.py
```

Outputs are written to `results/` (JSON results and table bodies) and `figures/`.

## Scenario and parameters

24-hour horizon at 1-minute resolution; 1.5 kW peak solar with 5 % noise and a cloud dip to 30 % (13:00–14:30); grid outages 09:30–11:00 and 18:30–22:30 and a brownout 15:00–15:30; 4.8 kWh battery, η = 0.90 applied on charge and discharge, 0.6 kW charge and 1.2 kW discharge limits, 10 % SOC floor, 60 % initial SOC; baseline inverter cut-off at 20 % SOC; L_max = 2.0 kW. All scenario data are synthetic.

## Notes on reproducibility

The nominal-scenario run reproduces the paper's Tier-1 availability (100 % vs 91.9 %), the baseline blackout from 21:23 (67 min), the minimum SOC values (11.5 % and 19.9 %) and the switching counts (2 vs 4). Solar utilisation and grid energy agree with Table 4 to within 2.2 percentage points and 0.27 kWh. Switching events of the fuzzy controller are counted after applying the 0.45/0.55 relay hysteresis of Eq. (7) to the source-priority output.

## Licence

MIT — see `LICENSE`.
