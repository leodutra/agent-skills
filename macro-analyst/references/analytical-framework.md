# Analytical Framework Reference

## Table of Contents

1. [Macro Driver Hierarchy](#macro-driver-hierarchy)
2. [Central Bank Cheat Sheet](#central-bank-cheat-sheet)
3. [Key Data Releases Calendar](#key-data-releases)
4. [Historical Analogues](#historical-analogues)
5. [EM Currency Risk Checklist](#em-currency-risk-checklist)
6. [Cross-Asset Signal Map](#cross-asset-signal-map)
7. [Common Analytical Traps](#common-analytical-traps)

---

## Macro Driver Hierarchy

FX markets are driven by a hierarchy of forces. Analyze in this order — do not skip levels.

### Tier 1: Rate Differentials (Dominant Driver)

The single most important medium-term FX driver. Currency flows follow yield.

**What to measure:**
- Nominal policy rate spread (e.g., Fed Funds vs ECB Deposit Rate)
- Real rate differential: (Nominal rate - Core CPI) for each currency
- 2-year government bond yield spread — the market's implied rate path
- OIS curve: what is the market pricing for the next 6-12 months of rate moves?

**Key principle:** The *direction* of the differential matters more than the *level*. A widening spread in favor of currency A drives A higher even if the absolute spread is small.

**Historical calibration:**
- EUR/USD has ~0.80 correlation with 2-year US-German yield spread over rolling 6-month windows
- USD/JPY is highly sensitive to US 10-year yields due to Japan's yield curve control legacy
- EM currencies respond more to real rate differentials than nominal ones

### Tier 2: Central Bank Policy Stance

Policy guides rate expectations, which move markets before actual rate changes.

**What to assess:**
- Explicit forward guidance vs data-dependency
- Dot plot / Summary of Economic Projections (Fed-specific)
- Dissent in voting — are hawks or doves gaining ground?
- Balance sheet policy: QE (currency negative), QT (currency positive, all else equal)
- Emergency tools: is the central bank intervening in FX? (BOJ, PBOC, SNB historically)

**Tone classification:**
- **Ultra-hawkish:** "We will do whatever it takes to bring inflation to target" + actual hikes
- **Hawkish:** Higher-for-longer messaging, no discussion of cuts
- **Neutral:** Data-dependent, balanced risk assessment
- **Dovish:** Discussing cuts, emphasizing growth risks
- **Ultra-dovish:** Active easing, QE, emergency rate cuts, forward guidance for low rates
- **Confused/Inconsistent:** Mixed signals from different officials — this is a volatility catalyst

### Tier 3: Fiscal and Sovereign Risk

Fiscal policy affects long-term currency valuation and central bank credibility.

**Key metrics:**
- Primary fiscal balance (excluding interest payments) — direction matters most
- Debt-to-GDP ratio: above 100% is a yellow flag, above 120% with rising trajectory is red
- Current account balance: persistent deficits require capital inflows to sustain the currency
- Twin deficit (fiscal + current account): historically the strongest negative signal for a currency
- Bond market vigilantes: is the 10-year yield rising because of growth (good) or fiscal risk (bad)?

**Fiscal dominance test:** Is the central bank constrained by government debt levels? If yes, the central bank cannot credibly tighten, which is bearish for the currency even if inflation is high. (See: Turkey 2021-2023, UK mini-budget crisis 2022)

### Tier 4: Global Risk Environment

Risk appetite drives capital flows between safe havens and risk assets.

**Risk-on regime (favors EM FX, commodity FX, risk currencies):**
- VIX below 15, equities trending up
- Credit spreads tightening
- Commodity prices rising
- Capital flowing into EM bond/equity funds

**Risk-off regime (favors USD, JPY, CHF):**
- VIX above 25, equities falling
- Credit spreads widening
- Flight to US Treasuries
- Capital flight from EM

**Dollar smile theory (Stephen Jen):**
USD strengthens in two scenarios: (1) US economy much stronger than rest of world → capital inflows, or (2) Global crisis/risk-off → safe haven demand. USD weakens when: global growth is synchronized and positive → capital flows away from safe haven into higher-yielding assets.

### Tier 5: Positioning and Sentiment (Contrarian at Extremes)

Positioning data is not a directional signal — it's a crowding signal.

**CFTC Commitments of Traders (COT) data:**
- Net long/short positions of leveraged funds
- Extreme readings (>2 standard deviations from 3-year mean) signal overcrowding
- Overcrowded positions unwind violently on contrary data

**Consensus / Analyst Surveys:**
- When >80% of analysts agree on a direction, the trade is usually fully priced
- Consensus is most useful as a contrarian indicator at extremes

---

## Central Bank Cheat Sheet

| Central Bank | Currency | Key Rate | Meeting Frequency | Key Personality Trait |
|---|---|---|---|---|
| Federal Reserve (Fed) | USD | Fed Funds Rate | 8x/year (FOMC) | Data-dependent, dual mandate (inflation + employment) |
| European Central Bank (ECB) | EUR | Deposit Facility Rate | 8x/year | Inflation-focused, consensus-driven, slow to act |
| Bank of Japan (BOJ) | JPY | Policy Rate | 8x/year | Ultra-gradualist, yield curve management legacy |
| Bank of England (BOE) | GBP | Bank Rate | 8x/year | Split committee, often ahead of consensus |
| People's Bank of China (PBOC) | CNY | LPR (1yr/5yr) | Monthly (LPR) | Managed FX, liquidity-driven, politically directed |
| Swiss National Bank (SNB) | CHF | Policy Rate | 4x/year | FX interventionist, small open economy focus |
| Reserve Bank of Australia (RBA) | AUD | Cash Rate | 8x/year | Commodity-linked, housing-sensitive |
| Bank of Canada (BOC) | CAD | Overnight Rate | 8x/year | Oil-sensitive, housing-focused |
| Banco Central do Brasil (BCB) | BRL | Selic Rate | 8x/year (Copom) | High credibility, real rate maximizer, EM leader |
| Banxico | MXN | Overnight Rate | 8x/year | Conservative, inflation-targeting, Fed-follower |

---

## Key Data Releases

**Tier 1 releases (immediate FX impact, high volatility):**
- US Non-Farm Payrolls (NFP) — first Friday of the month
- US/EU/UK CPI — monthly
- FOMC/ECB/BOJ rate decisions + press conferences
- US GDP (advance estimate)
- China PMI (official + Caixin)

**Tier 2 releases (meaningful but lower volatility):**
- PMI surveys (ISM Manufacturing/Services, EU PMIs)
- Retail sales
- Trade balance
- Housing data (US, UK, AU, CA)
- Wage growth data

**Tier 3 releases (background noise, occasionally matters):**
- Consumer confidence surveys
- Industrial production
- PPI
- Job openings (JOLTS)

---

## Historical Analogues

Use these to calibrate expectations. Past is not prologue, but patterns rhyme.

**Fed tightening + ECB easing (divergence) — 2014-2015:**
EUR/USD fell from 1.38 to 1.05 in 14 months. Rate divergence was the dominant driver. The move accelerated after the ECB launched QE in March 2015.

**USD/JPY and yield curve control — 2022:**
As the Fed hiked aggressively while the BOJ held YCC, USD/JPY surged from 115 to 152. The BOJ's eventual YCC tweak in December 2022 caused a sharp reversal.

**EM carry trade blow-up — 2013 (Taper Tantrum):**
Bernanke's suggestion of tapering QE triggered massive EM FX selloff. BRL fell 20%, INR 25%, TRY 15% in months. Fragile Five (BRL, INR, IDR, TRY, ZAR) hit hardest — all had current account deficits and dependence on foreign capital.

**UK mini-budget crisis — September 2022:**
GBP/USD crashed to 1.035 after Truss/Kwarteng announced unfunded tax cuts. Bond market and FX market reacted simultaneously. Example of fiscal dominance risk in a developed market. BOE forced into emergency intervention.

**Dollar smile in action — 2008 GFC:**
USD strengthened during the initial crisis (safe haven) → weakened during coordinated global easing → strengthened again as US recovered first. Classic illustration of the dollar smile framework.

---

## EM Currency Risk Checklist

For any emerging market currency analysis, score these factors:

| Risk Factor | Low Risk | Medium Risk | High Risk |
|---|---|---|---|
| Real interest rate | > +3% | +1% to +3% | < +1% or negative |
| Current account | Surplus | Deficit < 3% GDP | Deficit > 3% GDP |
| FX reserves | > 6 months imports | 3-6 months | < 3 months |
| External debt / GDP | < 30% | 30-60% | > 60% |
| Central bank independence | Full legal + de facto | Legal but political pressure | Compromised |
| Inflation | < 4% and stable | 4-8% | > 8% or accelerating |
| Fiscal balance | Primary surplus | Small primary deficit | Large primary deficit |

**Three or more "High Risk" scores = structurally bearish for the currency.**

---

## Cross-Asset Signal Map

FX does not exist in isolation. These cross-asset relationships provide confirmation or divergence signals.

| Signal | Implication |
|---|---|
| US 10Y yield rising + USD rising | Classic: US exceptionalism, capital inflows |
| US 10Y yield rising + USD falling | Fiscal risk signal — markets worried about debt, not growth |
| Oil rising + CAD/NOK lagging | Bearish divergence — economy not benefiting from commodity |
| Gold rising + USD rising | Unusual — signals deep systemic fear (both safe havens bid) |
| VIX spike + JPY not strengthening | BOJ intervention risk or structural JPY regime change |
| EM local bonds selling off + EM FX stable | Carry trade still intact but fragile — watch closely |
| DXY breaking key technical level + fundamental divergence | Positioning unwind, not fundamental shift — likely mean-reverts |

---

## Common Analytical Traps

Avoid these:

1. **Recency bias:** The last data point is not the trend. One hot CPI print doesn't mean inflation is re-accelerating. Look at 3-month and 6-month annualized rates.

2. **Confusing levels with direction:** A country with 12% rates isn't automatically bullish for the currency. If rates are going from 14% to 12%, that's a cutting cycle — bearish signal.

3. **Ignoring the denominator:** EUR/USD analysis requires analyzing BOTH the eurozone AND the US. Many analysts only analyze one side.

4. **Narrative over data:** "China is reopening" or "Europe is in crisis" are narratives. Price them with data: actual PMI numbers, capital flow data, credit growth.

5. **Treating consensus as signal:** If everyone is long USD, the bar for positive USD surprises is very high and the bar for negative surprises is very low. Crowded trades have asymmetric risk.

6. **Forgetting the calendar:** Macro analysis without knowing what data is coming next week is incomplete. Always check the economic calendar.

7. **Mixing timeframes:** A structurally bullish view (12-month) can coexist with a tactically bearish setup (2-week). State your timeframe explicitly.
