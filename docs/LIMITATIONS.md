# Limitations of the FDA PharmaVigilance Analysis

> Academic limitations section for the thesis. Every claim below is a property of
> the data source (openFDA / FDA FAERS) or of disproportionality methodology, and
> constrains how the results in this work may be interpreted.

## 1. Spontaneous-reporting bias (the data are not a sample)
FAERS is a **spontaneous reporting system**: reports are submitted voluntarily by
clinicians, manufacturers, and patients. The data are therefore a *convenience
collection of notifications*, not a random or representative sample of treated
patients. Reporting is influenced by media attention, litigation, drug novelty,
and clinical awareness. Consequently, counts reflect **what gets reported**, not
the true frequency of events in the population.

## 2. Under-reporting
Only a small and unknown fraction of real adverse events are ever reported
(under-reporting is well documented, often >90% for many events). The absence of
reports for a drug-reaction pair therefore **cannot** be interpreted as evidence
of safety.

## 3. No denominator → no incidence or risk
FAERS contains **no exposure denominator** (the number of patients who took each
drug is unknown). It is therefore impossible to compute true incidence, absolute
risk, or relative risk from these data. All measures used here (PRR, ROR) are
**disproportionality** measures: they compare the *reporting* of a reaction for a
drug against its reporting for all other drugs in the database. They quantify a
**reporting association**, nothing more.

## 4. Correlation is not causation
A disproportionality signal (high PRR/ROR) indicates that a reaction is reported
*more than expected* for a drug. It does **not** establish a causal relationship.
Signals are hypotheses that require confirmation through pharmacological plausibility,
clinical review, and controlled epidemiological studies. Confounding by indication,
co-medication, and disease severity is not controlled for in this design.

## 5. Duplicates and the Weber effect
Despite deduplication (here on a deterministic `event_id` over a rolling 3-year
window), residual duplicate or follow-up reports may persist and inflate counts.
The **Weber effect** (a peak in reporting in the first ~2 years after launch,
followed by decline) and notoriety/stimulated reporting can distort temporal and
cross-drug comparisons. The "top drugs by report volume" in the data-quality
report should be read with this notoriety bias in mind.

## 6. Comparator (background) limitation specific to this work
For practical and cost reasons, the database here was built from a curated cohort
of widely-used drugs (~100). The disproportionality **background** is therefore
these ingested reports, **not the entire FAERS database**. This can dilute a
class effect (e.g., a statin's rhabdomyolysis signal is attenuated because other
statins are present in the comparator) and should be stated explicitly when
reporting any PRR/ROR value.

## 7. Coding, age-unit, and free-text limitations
- Drug names in FAERS are free text (brand, generic, misspellings, dosage strings).
  Normalisation here is heuristic and incomplete; some variants remain unmerged.
- openFDA age fields use unit codes (years/months/days/...) that must be converted;
  out-of-range or ambiguous ages are dropped.
- Seriousness fields are coded (1 = yes, 2 = no), not 0/1 — a frequent source of
  error if summed naively.

## 8. openFDA is not the Mexican pharmacovigilance system
This work uses **US FDA FAERS** data because it is the only freely accessible
adverse-event API. It is **not** equivalent to Mexican national pharmacovigilance
data. In Mexico, pharmacovigilance is governed by **NOM-220-SSA1-2016** and
coordinated by the **Centro Nacional de Farmacovigilancia (CNFV)** under
**COFEPRIS**. Differences in population, prescribing patterns, regulatory reporting
obligations, and case intake mean that signals found in FAERS **may not transfer**
directly to the Mexican context. Findings here should be framed as
methodological/illustrative for the Mexican setting, not as conclusions about the
Mexican population.

## 9. Scope of validity
Given the above, the appropriate claims supported by this work are:
- The pipeline **correctly implements** standard disproportionality methods
  (verified by positive controls, see `val_positive_controls`).
- It can **generate hypotheses** (signals) for further investigation.
It does **not** support claims about causation, incidence, or population-level risk.
