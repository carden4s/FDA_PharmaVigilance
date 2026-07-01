# Spanish localization for column headers and categorical values
# Co-authored with CoCo
"""Central Spanish label dictionary so gold columns stay English in the DB but display in Spanish."""

COLUMN_LABELS = {
    "DRUG_NAME": "Medicamento",
    "DRUG_1_NAME": "Medicamento 1",
    "DRUG_2_NAME": "Medicamento 2",
    "REACTION_NAME": "Reacción",
    "REACTION_COUNT": "Reportes",
    "REACTION_FREQUENCY_PCT": "Frecuencia (%)",
    "RANK_WITHIN_DRUG": "Ranking",
    "SERIOUS_REACTION_COUNT": "Graves",
    "FATAL_REACTION_COUNT": "Mortales",
    "LAST_OBSERVED_DATE": "Última fecha",
    "PATIENT_AGE_GROUP": "Grupo de edad",
    "PATIENT_SEX": "Sexo",
    "PATIENT_COUNT": "Pacientes",
    "EVENT_COUNT": "Eventos",
    "SERIOUS_EVENT_COUNT": "Eventos graves",
    "SERIOUS_RATE_PCT": "Tasa de gravedad (%)",
    "FATAL_EVENT_COUNT": "Eventos mortales",
    "FATAL_RATE_PCT": "Tasa de mortalidad (%)",
    "AVG_PATIENT_AGE": "Edad promedio",
    "CO_OCCURRENCE_COUNT": "Coocurrencias",
    "COMBINED_SERIOUS_RATE_PCT": "Tasa de gravedad (%)",
    "COMBINED_FATAL_RATE_PCT": "Tasa de mortalidad (%)",
    "REPORTS_WITH_BOTH": "Reportes con ambos",
    "N_DRUG": "Reportes del fármaco",
    "N_REACTION": "Reportes de la reacción",
    "PRR": "PRR",
    "ROR": "ROR",
    "ROR_LOWER_95": "ROR (IC95% inf.)",
    "CHI_SQUARED": "Chi²",
    "IS_SIGNAL": "Señal",
    "TOTAL_REPORTS": "Reportes totales",
    "A": "a (ambos)",
    "PRR_UPPER_95": "PRR (IC95% sup.)",
    "ROR_UPPER_95": "ROR (IC95% sup.)",
    "PRR_LOWER_95": "PRR (IC95% inf.)",
    "PRR_SIGNAL": "Criterio PRR",
    "ROR_SIGNAL": "Criterio ROR",
    "SIGNAL_FLAG": "Señal",
    "DETECTED": "Detectado",
    "EXPECTED_SIGNAL": "Esperado",
    "SOURCE": "Fuente",
    "VALIDATION_NOTE": "Nota de validación",
}

SEX_ES = {"Male": "Masculino", "Female": "Femenino", "Unknown": "Desconocido"}
AGE_GROUP_ES = {"Unknown": "Desconocido"}


def localize_df(df, value_maps=None):
    """Return a copy of df with Spanish column headers and (optionally) translated cell values."""
    if df is None:
        return df
    out = df.copy()
    if value_maps:
        for col, mapping in value_maps.items():
            if col in out.columns:
                out[col] = out[col].replace(mapping)
    return out.rename(columns={c: COLUMN_LABELS.get(c, c) for c in out.columns})