# ai/summarizer.py  ── version Ollama (100% local, gratuit)
import ollama
import os
import json
import pandas as pd
from datetime import date
from dotenv import load_dotenv
from database.db_manager import DBManager

load_dotenv()

OLLAMA_HOST  = os.getenv("OLLAMA_HOST",  "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def build_context(db: DBManager) -> str:
    """Rassemble les dernières stats depuis la DB et les formate pour le prompt."""
    top_skills  = db.get_top_skills(20)
    top_sectors = db.get_top_sectors(10)
    salary_data = db.get_salary_summary()
    growth_data = db.get_monthly_growth(3)   # 3 derniers mois

    context = f"""
Date d'analyse : {date.today().isoformat()}

TOP 20 COMPÉTENCES DEMANDÉES:
{json.dumps(top_skills, ensure_ascii=False, indent=2)}

TOP 10 SECTEURS (nombre d'offres):
{json.dumps(top_sectors, ensure_ascii=False, indent=2)}

STATISTIQUES SALARIALES (TND/mois):
{json.dumps(salary_data, ensure_ascii=False, indent=2)}

ÉVOLUTION DES 3 DERNIERS MOIS:
{json.dumps(growth_data, ensure_ascii=False, indent=2)}
"""
    return context


def summarize_market() -> dict:
    db      = DBManager()
    context = build_context(db)

    system_prompt = (
        "Tu es un expert du marché de l'emploi tunisien. "
        "Analyse les données fournies et rédige un résumé "
        "professionnel en français (max 300 mots) couvrant : "
        "1) tendances clés des compétences, "
        "2) secteurs en croissance, "
        "3) fourchettes salariales, "
        "4) recommandations pour les candidats."
    )

    # ── Appel Ollama (client Python officiel) ──────────────────────────────
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system",  "content": system_prompt},
            {"role": "user",    "content": context},
        ],
        options={
            "temperature": 0.3,    # réponses factuelles, peu créatives
            "num_predict": 600,    # ~300 mots
        }
    )

    summary_text  = response["message"]["content"]
    tokens_used   = response.get("eval_count", 0)   # tokens générés

    result = {
        "summary"      : summary_text,
        "generated_at" : date.today().isoformat(),
        "model"        : OLLAMA_MODEL,
        "tokens_used"  : tokens_used,
    }

    db.save_ai_summary(result)

    # Export CSV pour Power BI
    export_dir = os.getenv("EXPORT_DIR", "exports")
    os.makedirs(export_dir, exist_ok=True)
    pd.DataFrame([result]).to_csv(f"{export_dir}/ai_summary.csv", index=False)

    return result


# ── Fallback HTTP brut (si le client Python n'est pas installé) ────────────
def summarize_market_http() -> dict:
    """Alternative via requests directement sur l'API REST d'Ollama."""
    import requests

    db      = DBManager()
    context = build_context(db)

    payload = {
        "model" : OLLAMA_MODEL,
        "prompt": (
            "Tu es un expert du marché de l'emploi tunisien. "
            "Analyse et résume en français (max 300 mots):\n\n"
            + context
        ),
        "stream"  : False,
        "options" : {"temperature": 0.3, "num_predict": 600},
    }

    resp = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json=payload,
        timeout=120
    )
    resp.raise_for_status()
    data = resp.json()

    result = {
        "summary"      : data["response"],
        "generated_at" : date.today().isoformat(),
        "model"        : OLLAMA_MODEL,
        "tokens_used"  : data.get("eval_count", 0),
    }

    db.save_ai_summary(result)
    export_dir = os.getenv("EXPORT_DIR", "exports")
    os.makedirs(export_dir, exist_ok=True)
    pd.DataFrame([result]).to_csv(f"{export_dir}/ai_summary.csv", index=False)

    return result