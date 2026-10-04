def tri(x, a, b, c):
    x = np.asarray(x, dtype=float)
    left = (x - a) / (b - a) if b != a else np.ones_like(x)
    right = (c - x) / (c - b) if c != b else np.ones_like(x)
    return np.clip(np.minimum(left, right), 0, 1)

# Input MFs (all normalized 0..1)
def solar_low(x):  return tri(x, -0.4, 0.0, 0.4)
def solar_med(x):  return tri(x, 0.2, 0.5, 0.8)
def solar_high(x): return tri(x, 0.6, 1.0, 1.4)

def soc_low(x):  return tri(x, -0.4, 0.0, 0.45)
def soc_med(x):  return tri(x, 0.25, 0.5, 0.75)
def soc_high(x): return tri(x, 0.55, 1.0, 1.4)

def grid_absent(x):   return tri(x, -0.4, 0.0, 0.4)
def grid_unstable(x): return tri(x, 0.2, 0.5, 0.8)
def grid_stable(x):   return tri(x, 0.6, 1.0, 1.4)

def load_low(x):  return tri(x, -0.4, 0.0, 0.4)
def load_med(x):  return tri(x, 0.2, 0.5, 0.8)
def load_high(x): return tri(x, 0.6, 1.0, 1.4)

# Output universes
P_UNIV = np.linspace(0, 1, 201)      # source priority: 0=grid ... 1=solar/battery
T_UNIV = np.linspace(0, 3, 301)      # tier permission: ~0.5 T1only, ~1.5 T1+2, ~2.5 all

def p_grid(u):  return tri(u, -0.4, 0.0, 0.45)
def p_blend(u): return tri(u, 0.25, 0.5, 0.75)
def p_solar(u): return tri(u, 0.55, 1.0, 1.4)

def t_t1(u):  return tri(u, -0.6, 0.5, 1.2)
def t_t12(u): return tri(u, 0.8, 1.5, 2.2)
def t_all(u): return tri(u, 1.8, 2.5, 3.6)

def centroid(univ, agg):
    s = agg.sum()
    return float((univ * agg).sum() / s) if s > 1e-9 else float(univ.mean())

def fuzzy_controller(S, B, G, L):
    sL, sM, sH = solar_low(S), solar_med(S), solar_high(S)
    bL, bM, bH = soc_low(B), soc_med(B), soc_high(B)
    gA, gU, gS = grid_absent(G), grid_unstable(G), grid_stable(G)
    lL, lM, lH = load_low(L), load_med(L), load_high(L)

    # ---- Source-priority rules (antecedent strength, output MF) ----
    p_rules = [
        (min(sH, max(bM, bH)), p_solar),      # R1 high solar & decent battery -> solar
        (bH,                    p_solar),      # R2 battery high -> solar/battery
        (gA,                    p_solar),      # R3 grid absent -> forced solar/battery
        (min(bL, gS, sL),       p_grid),       # R4 low solar & low battery & stable grid -> grid
        (min(max(bL, bM), gS),  p_grid),       # R5 grid stable & battery not high -> conserve reserve, use grid
        (min(sM, bM),           p_blend),      # R6 medium solar & medium battery -> blend
        (min(gU, bM),           p_blend),      # R7 unstable grid & medium battery -> blend
        (min(sH, bL, gS),       p_blend),      # R8 high solar but low battery, stable grid -> blend
    ]
    agg_p = np.zeros_like(P_UNIV)
    for w, mf in p_rules:
        if w > 0:
            agg_p = np.maximum(agg_p, np.minimum(w, mf(P_UNIV)))
    P = centroid(P_UNIV, agg_p)

    # ---- Tier-permission rules ----
    t_rules = [
        (min(sH, bH),           t_all),        # R9 abundant solar+battery -> all tiers
        (min(sH, bM),           t_all),        # R10
        (bH,                    t_all),        # R11 battery high -> all tiers
        (min(gS, bM),           t_all),        # R12 stable grid & medium battery -> all
        (min(gS, bL),           t_t12),        # R13 stable grid but low battery -> defer tier 3
        (min(gU, bM),           t_t12),        # R14 unstable grid, medium battery -> tiers 1-2
        (min(gA, bM),           t_t12),        # R15 outage with medium battery -> tiers 1-2
        (min(gA, bL),           t_t1),         # R16 outage with low battery -> critical only
        (min(gU, bL),           t_t1),         # R17 unstable grid & low battery -> critical only
        (min(sL, bL, lH),       t_t1),         # R18 no solar, low battery, heavy demand -> critical only
    ]
    agg_t = np.zeros_like(T_UNIV)
    for w, mf in t_rules:
        if w > 0:
            agg_t = np.maximum(agg_t, np.minimum(w, mf(T_UNIV)))
    T = centroid(T_UNIV, agg_t)
    return P, T
