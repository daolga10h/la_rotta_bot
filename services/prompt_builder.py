from models.user_profile import UserProfileData


BASE_PROMPT = """Sei un assistente conversazionale personale.
Parli in prima persona, senza nome.
Tono: caldo e onesto come base. Autorevole quando nomini pattern o resistenze che l'utente sta evitando.
Mai entusiasmo falso. Mai moralizzare. Mai dire "dovresti" — usa domande invece.
Risposte brevi: massimo 3-4 righe. Una domanda alla volta.
Lingua: italiano."""


def build_system_prompt(
    profile: UserProfileData,
    flow_name: str,
    flow_instructions: str,
    weekly_summaries: list[dict] | None = None,
) -> str:
    sections = [BASE_PROMPT]

    # Profilo utente
    if profile.user_name:
        gender_str = {"M": "uomo", "F": "donna"}.get(profile.user_gender or "", "")
        gender_note = f" ({gender_str} — usa il genere corretto negli aggettivi)" if gender_str else ""
        sections.append(f"\n[NOME UTENTE]\n{profile.user_name}{gender_note}")

    obj_lines = []
    for obj in sorted(profile.objectives, key=lambda o: o.rank):
        hours = f" ({obj.weekly_hours_target}h/sett.)" if obj.weekly_hours_target else ""
        obj_lines.append(f"  {obj.rank}. {obj.title}{hours}")
    objectives_text = "\n".join(obj_lines) if obj_lines else "  (nessun obiettivo ancora)"

    sections.append(f"""
[PROFILO UTENTE]
Contesto: {profile.user_context or 'non ancora definito'}
Obiettivi:
{objectives_text}
Motivazione di fondo: {profile.motivation_anchor or 'non ancora definita'}
Streak strategico: {profile.streak_strategic} giorni
Onboarding completo: {profile.onboarding_complete}""")

    # Contatori pattern recognition
    c = profile.counters
    sections.append(f"""
[CONTATORI]
Giorni operativi consecutivi: {c.consecutive_operative_days}
Settimane consecutive sotto obiettivo: {c.consecutive_weeks_under_target}
Sessioni strategiche totali: {c.total_strategic_sessions}""")

    # Libreria sblocchi (solo in Scenario C)
    if flow_name.startswith("SCENARIO_C") and profile.unlock_library:
        entries = profile.unlock_library[-3:]  # ultimi 3
        lib_lines = [f"  - [{e.context}] {e.insight}" for e in entries]
        sections.append(f"""
[LIBRERIA SBLOCCHI PERSONALI]
{chr(10).join(lib_lines)}""")

    # Riassunti narrativi settimanali
    if weekly_summaries:
        summaries_text = "\n".join(
            f"  Settimana {s.get('week_start', '?')} ({s.get('tone', '?')}): {s.get('narrative', '')}"
            for s in weekly_summaries
        )
        sections.append(f"""
[ULTIME SETTIMANE]
{summaries_text}""")

    # Flusso corrente
    sections.append(f"""
[FLUSSO ATTUALE]
Flusso: {flow_name}
{flow_instructions}""")

    return "\n".join(sections)


def build_classification_prompt(
    message: str,
    objectives: list,
    recent_messages: list[dict],
) -> str:
    obj_text = "; ".join(f"{o.rank}. {o.title}" for o in objectives)
    context_text = ""
    if recent_messages:
        context_text = "\nUltimi messaggi:\n" + "\n".join(
            f"  {m['role']}: {m['content'][:100]}" for m in recent_messages[-3:]
        )

    return f"""Classifica questo messaggio in una categoria.

Obiettivi utente: {obj_text}
{context_text}

Messaggio da classificare: "{message}"

Categorie possibili:
- IDEA: nuova idea o opportunità da parcheggiare
- UPDATE: aggiornamento su lavoro in corso
- BLOCCO: richiesta di aiuto o sblocco emotivo
- DOMANDA: domanda diretta al bot
- FEEDBACK: commento su una risposta del bot
- AMBIGUO: non chiaramente classificabile

Rispondi SOLO con JSON valido, nessun testo aggiuntivo:
{{"category": "CATEGORIA", "confidence": 0.95, "alternative_category": "ALTRA_CATEGORIA_O_NULL"}}"""
