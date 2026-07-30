# Engineering Theory & Mathematical Derivations

This document derives every equation used in the three projects, in the
same order the code applies them. It is meant to be read alongside the
source — every section names the module and function that implements it.

References used throughout:

- Cohen, Rogers & Saravanamuttoo, *Gas Turbine Theory*, 5th/6th ed. — the
  primary reference for Project 1's real-cycle relations.
- Mattingly, *Elements of Gas Turbine Propulsion* — cross-checked for the
  thrust/efficiency definitions.
- Walsh & Fletcher, *Gas Turbine Performance* — corrected-parameter
  conventions used in Project 2.
- Shigley's *Mechanical Engineering Design* — the pin/clevis bearing-stress
  check used in Project 3.

---

## Part 1 — Turbojet Performance Simulator

### 1.1 Station numbering

```
0 ---- 2 ---- 3 ---- 4 ---- 5 ---- 8
freestream  intake  compressor  combustor  turbine  nozzle
            exit    exit        exit       exit     exit
```

This matches the numbering convention used throughout Cohen, Rogers &
Saravanamuttoo and most gas-turbine textbooks (stations 1, 6, 7 are
reserved for components — fan, afterburner — this simulator does not
model).

### 1.2 International Standard Atmosphere — `jetx/cycle/atmosphere.py`

Troposphere (0–11 km), linear temperature lapse:

```
T(h) = T_sl - L*h
p(h) = p_sl * (T(h)/T_sl)^(g0 / (L*R))
```

Lower stratosphere (11–20 km), isothermal:

```
T(h) = T_11               (constant, 216.65 K)
p(h) = p_11 * exp(-g0*(h - 11000) / (R*T_11))
```

Both are the direct solution of the hydrostatic equation `dp/dh = -rho*g0`
combined with the ideal gas law `p = rho*R*T`, integrated with T(h) either
linear or constant.

Freestream stagnation conditions add the ram effect of forward flight
(steady-flow energy equation, adiabatic, no work):

```
T0 / T = 1 + (gamma-1)/2 * M^2
p0 / p = (T0/T)^(gamma/(gamma-1))            [isentropic]
```

### 1.3 Intake — `components.intake`

No work is done, so `T02 = T0` (stagnation temperature unchanged). A
pressure-recovery factor represents duct friction / spillage losses:

```
p02 = pressure_recovery * p0
```

### 1.4 Compressor — `components.compressor`

Ideal (isentropic) exit temperature for pressure ratio `rc = p03/p02`:

```
T03s / T02 = rc^((gamma_c - 1)/gamma_c)
```

Isentropic efficiency is defined as ideal work over actual work for the
*same pressure rise* — always < 1 because real compression is irreversible
(entropy-generating), so the real temperature rise always exceeds the
ideal one:

```
eta_c = (T03s - T02) / (T03 - T02)
  =>   T03 = T02 + (T03s - T02) / eta_c
```

Specific work absorbed:

```
w_c = cp_cold * (T03 - T02)
```

### 1.5 Combustor — `components.combustor`, `components.fuel_air_ratio`

**Fuel-air ratio**, from an energy balance across the combustor. Per unit
mass of air entering, the fuel's chemical energy (discounted by combustion
efficiency) plus the sensible heat of the incoming air must equal the
sensible heat of the (1+f) kg of combustion products leaving:

```
cp_c*T03 + f*eta_b*Q_R = (1+f)*cp_h*T04
```

Solving for `f = m_dot_fuel / m_dot_air`:

```
f = (cp_h*T04 - cp_c*T03) / (eta_b*Q_R - cp_h*T04)
```

This is the standard combustor energy balance (Cohen, Rogers &
Saravanamuttoo §2.4) — it correctly keeps the added fuel mass flowing
through every downstream station, unlike a naive `f = cp*(T04-T03)/Q_R`
that ignores the (1+f) mass multiplier.

**Pressure loss**, modelled as a fixed fraction of inlet pressure (typical
3–6% for a real combustor liner):

```
p04 = p03 * (1 - pressure_loss_fraction)
```

### 1.6 Turbine — `components.turbine`

**Work balance.** In a single-spool turbojet with no bleed or power
off-take, the turbine's *entire* job is to supply the compressor's power
demand, after mechanical losses:

```
(1+f) * cp_h * (T04 - T05) * eta_mech = w_c
  =>  T04 - T05 = w_c / (eta_mech * (1+f) * cp_h)
```

**Pressure drop**, from the turbine's isentropic efficiency (opposite
convention to the compressor's — actual work over ideal work for the same
temperature drop, since expansion delivers *less* real work than ideal for
a given pressure ratio):

```
eta_t = (T04 - T05) / (T04 - T05s)
  =>  T05s = T04 - (T04 - T05)/eta_t
p05/p04 = (T05s/T04)^(gamma_h/(gamma_h - 1))          [isentropic]
```

### 1.7 Nozzle — `components.nozzle`

**Choking check.** The critical (choking) stagnation-to-static pressure
ratio for a real (non-ideal) convergent nozzle:

```
(p0/p*) = [1 - (1/eta_n)*(gamma-1)/(gamma+1)]^(-gamma/(gamma-1))
```

which reduces to the classic ideal-nozzle result `((gamma+1)/2)^(gamma/(gamma-1))`
at `eta_n = 1`.

**Unchoked** (`p05/pa` below critical): the jet fully expands to ambient
static pressure.

```
T8s = T05 * (pa/p05)^((gamma_h-1)/gamma_h)
T8  = T05 - eta_n*(T05 - T8s)
V8  = sqrt(2*cp_h*(T05 - T8))                          [energy equation]
```

**Choked** (`p05/pa` at or above critical): the throat sits at Mach 1 and
cannot expand further regardless of how low `pa` is.

```
T8 = 2*T05 / (gamma_h + 1)
p8 = p05 / (p0/p*)_critical
V8 = sqrt(gamma_h * R_h * T8)                          [sonic velocity]
```

Choked flow leaves `p8 > pa`, which is why the thrust equation below needs
an explicit pressure-thrust term for this case. See
`docs/assumptions_and_limitations.md` for the consequence this has on
computed thermal efficiency at high pressure ratio / high TIT.

### 1.8 Overall performance — `performance.py`

**Net thrust** (momentum change + pressure thrust):

```
F = m_dot_a * [(1+f)*V8 - V0] + A8*(p8 - pa)
```

**Specific thrust:** `F_s = F / m_dot_a` (thrust per unit air mass flow;
independent of engine size, so it is the natural way to compare cycle
*designs* rather than specific *engines*).

**Thrust-specific fuel consumption:** `TSFC = m_dot_f / F = f / F_s`.

**Thermal efficiency** (fraction of fuel chemical energy converted to
kinetic energy of the working fluid):

```
eta_th = [(1+f)*V8^2 - V0^2] / (2*f*Q_R)
```

**Propulsive (Froude) efficiency** (fraction of that kinetic-energy
*change* converted into useful thrust power):

```
eta_p = 2*V0*[(1+f)*V8 - V0] / [(1+f)*V8^2 - V0^2]
```

At `V0 = 0` (static test-bed condition) this is identically zero — no
thrust *power* is done on a stationary vehicle, by definition, no matter
how much thrust *force* is produced.

**Overall efficiency:** `eta_o = eta_th * eta_p` (equivalently, thrust
power delivered / fuel chemical power supplied).

---

## Part 2 — Test-Bed Data Reduction

### 2.1 Sensor calibration models — `jetx/daq/sensors.py`

| Sensor | Raw signal | Calibration equation |
|---|---|---|
| Load cell | ADC counts | `F = slope*(raw - zero_offset)` |
| Thermocouple (Type K) | millivolts | `T[degC] = mV/Seebeck + T_cold_junction` |
| Pressure transducer | 4–20 mA loop current | `p = p_min + (I-4)/(20-4) * (p_max - p_min)` |
| RPM / speed pickup | pulse count over a window | `RPM = (pulses / pulses_per_rev) / window_s * 60` |

The thermocouple model is a **linear approximation** of the true Type-K
EMF-temperature curve (an 8th/9th-order polynomial per NIST ITS-90); see
`docs/assumptions_and_limitations.md` for the accuracy trade-off this
makes.

### 2.2 Noise filtering — `jetx/daq/filtering.py`

**Moving average (boxcar):** a centred rolling mean over `window_samples`.
Cheap, but has a well-known trade-off: wider windows reduce noise more but
introduce more lag/smoothing of real transients.

**Butterworth low-pass + `filtfilt`:** the standard test-data-reduction
choice. The digital filter's cutoff is specified as a fraction of the
Nyquist frequency:

```
Wn = f_cutoff / (f_sample / 2)
```

`scipy.signal.filtfilt` applies the designed filter once forward and once
time-reversed, which cancels the filter's phase response exactly (a
"zero-phase" filter) — critical so a filtered channel stays aligned in
time with unfiltered event markers.

### 2.3 Corrected (referred) parameters — `jetx/daq/corrected_speed.py`

Gas-turbine performance parameters scale with inlet temperature and
pressure, so raw values from two different test days are not directly
comparable. The standard Buckingham-Pi non-dimensional groups, referenced
to sea-level ISA (`T_ref = 288.15 K`, `p_ref = 101325 Pa`):

```
theta = T_inlet / T_ref
delta = p_inlet / p_ref

N_corrected = N_actual / sqrt(theta)
W_corrected = W_actual * sqrt(theta) / delta
```

This is exactly what lets a test point from a 15 degC morning and a 35
degC afternoon be compared on equal terms.

### 2.4 QA flagging — `jetx/daq/qa.py`

Four independent flags per channel:

- **Dropout:** raw sample is `NaN`.
- **Stuck:** `N` or more consecutive exact-zero first differences
  (transducer/cabling fault holding a fixed reading).
- **Spike:** deviation from a rolling **median** exceeds `n_sigma` times a
  rolling **median absolute deviation** (MAD), scaled by the standard
  consistency constant `1.4826` so MAD approximates a normal-distribution
  standard deviation. The median/MAD pair is used instead of mean/std
  specifically because a single-sample spike inside a small window
  inflates the mean/std enough to mask itself — the classic failure mode
  of a naive rolling z-score.
- **Out of range:** value outside a configured physically-plausible
  envelope (sensor rated capacity, material temperature limit, overspeed
  limit).

---

## Part 3 — Test-Stand Fixture

### 3.1 Net area and mass — `jetx/fixture/geometry.py`

Net plate area subtracts the four corner-fillet cutouts and all through
holes from the gross rectangle:

```
A_fillet_loss = 4 * r^2 * (1 - pi/4)          [per corner, quarter-circle cut from a square]
A_net = L*W - A_fillet_loss - 4*(pi/4)*d_bolt^2 - (pi/4)*d_clevis^2
mass = A_net * t * rho
```

### 3.2 Clevis bearing stress — `geometry.BracketGeometry.bearing_stress_mpa`

First-pass **bearing (projected-area) stress** check at the clevis pin
interface — standard practice for sizing a pin/clevis joint before a full
FEA pass (Shigley's, ch. on pin joints):

```
sigma_bearing = F / (d_bore * t)
safety_factor = sigma_yield / sigma_bearing
```

This checks *bearing* stress only — it does not replace a shear-tearout,
fatigue, or stress-concentration (Kt at the fillet) check, all flagged in
`docs/future_work.md`.

### 3.3 DXF geometry — `jetx/fixture/dxf_export.py`

The rounded-rectangle outline is built from four `LINE` segments (the flat
edges, each stopped `r` short of its corner) and four `ARC` segments (90°
sweeps centred `r` in from each corner) — an exact vector representation
of the filleted rectangle, not an approximation.
