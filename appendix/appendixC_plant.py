def run_fuzzy():
    soc = SOC0
    hist = dict(soc=[], P=[], T=[], served1=[], served2=[], served3=[],
                grid_kW=[], solar_used=[], tiers=[])
    for k in range(N):
        S = min(solar[k] / 1.5, 1.0)
        G = grid[k]
        Ld = (tier1[k] + tier2[k] + tier3[k]) / L_MAX
        P, T = fuzzy_controller(S, soc, G, min(Ld, 1.0))
        # crisp tier gate
        if T >= 2.0:   allowed = 3
        elif T >= 1.0: allowed = 2
        else:          allowed = 1
        d1, d2, d3 = tier1[k], tier2[k], tier3[k]
        demand = d1 + (d2 if allowed >= 2 else 0) + (d3 if allowed >= 3 else 0)

        sol_used = min(solar[k], demand)
        deficit = demand - sol_used
        g_kW = 0.0; batt_out = 0.0
        grid_ok = G >= 0.4
        if P >= 0.5:
            can = min(DIS_MAX, max(0.0, (soc - SOC_FLOOR) * CAP / DT))
            batt_out = min(deficit, can)
            deficit -= batt_out
            if deficit > 0 and grid_ok:
                g_kW = deficit; deficit = 0.0
        else:
            if grid_ok:
                g_kW = deficit; deficit = 0.0
            else:
                can = min(DIS_MAX, max(0.0, (soc - SOC_FLOOR) * CAP / DT))
                batt_out = min(deficit, can)
                deficit -= batt_out
        unserved = deficit
        # charging
        surplus = max(0.0, solar[k] - sol_used)
        ch = min(surplus, CH_MAX, (1.0 - soc) * CAP / DT)
        grid_ch = 0.0
        if P < 0.55 and soc < 0.8 and G >= 0.9:
            grid_ch = min(0.4, CH_MAX - ch, (1.0 - soc) * CAP / DT - ch)
            grid_ch = max(0.0, grid_ch)
        soc = soc + (ch + grid_ch) * EFF * DT / CAP - batt_out * DT / (EFF * CAP)
        soc = float(np.clip(soc, 0, 1))
        g_kW += grid_ch

        # record served per tier (proportional shortfall to lowest priority served set)
        s3 = d3 if (allowed >= 3 and unserved <= 1e-9) else (max(0.0, d3 - unserved) if allowed >= 3 else 0.0)
        rem_unserved = max(0.0, unserved - (d3 if allowed >= 3 else 0.0) + s3) if allowed >= 3 else unserved
        s2 = d2 if (allowed >= 2 and rem_unserved <= 1e-9) else (max(0.0, d2 - rem_unserved) if allowed >= 2 else 0.0)
        rem2 = max(0.0, rem_unserved - (d2 if allowed >= 2 else 0.0) + s2) if allowed >= 2 else rem_unserved
        s1 = max(0.0, d1 - rem2)

        hist['soc'].append(soc); hist['P'].append(P); hist['T'].append(T)
        hist['served1'].append(s1); hist['served2'].append(s2); hist['served3'].append(s3)
        hist['grid_kW'].append(g_kW); hist['solar_used'].append(sol_used + ch)
        hist['tiers'].append(allowed)
    return {k: np.array(v) for k, v in hist.items()}

def run_baseline():
    """Conventional ATS: grid serves everything when present; on outage inverter serves ALL
       tiers from battery+solar until SOC<0.20 cutoff -> total blackout. Solar only charges battery."""
    soc = SOC0
    hist = dict(soc=[], served1=[], served2=[], served3=[], grid_kW=[], solar_used=[], on_grid=[])
    inverter_lock = False
    for k in range(N):
        d1, d2, d3 = tier1[k], tier2[k], tier3[k]
        demand = d1 + d2 + d3
        grid_ok = grid[k] >= 0.4
        g_kW = 0.0; sol_used = 0.0; s1 = s2 = s3 = 0.0
        if grid_ok:
            inverter_lock = False
            g_kW = demand; s1, s2, s3 = d1, d2, d3
            ch = min(solar[k], CH_MAX, (1.0 - soc) * CAP / DT)
            soc = float(np.clip(soc + ch * EFF * DT / CAP, 0, 1))
            sol_used = ch
        else:
            if soc <= 0.20: inverter_lock = True
            if not inverter_lock:
                sol_direct = min(solar[k], demand)
                deficit = demand - sol_direct
                can = min(DIS_MAX, max(0.0, (soc - SOC_FLOOR) * CAP / DT))
                batt_out = min(deficit, can)
                served = sol_direct + batt_out
                frac = served / demand if demand > 0 else 1.0
                s1, s2, s3 = d1 * frac, d2 * frac, d3 * frac
                surplus = max(0.0, solar[k] - sol_direct)
                ch = min(surplus, CH_MAX, (1.0 - soc) * CAP / DT)
                soc = float(np.clip(soc + ch * EFF * DT / CAP - batt_out * DT / (EFF * CAP), 0, 1))
                sol_used = sol_direct + ch
            else:
                ch = min(solar[k], CH_MAX, (1.0 - soc) * CAP / DT)
                soc = float(np.clip(soc + ch * EFF * DT / CAP, 0, 1))
                sol_used = ch
        hist['soc'].append(soc); hist['served1'].append(s1); hist['served2'].append(s2)
        hist['served3'].append(s3); hist['grid_kW'].append(g_kW)
        hist['solar_used'].append(sol_used); hist['on_grid'].append(grid_ok)
    return {k: np.array(v) for k, v in hist.items()}
