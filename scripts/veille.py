"""
VEILLE STRATEGIQUE - 3 modes avec filtre date strict
- Quotidien  : 24h uniquement
- Hebdo      : 7 jours uniquement
- Mensuel    : 30 jours uniquement
- Si aucun article dans la periode = case vide, rien invente
"""

import os
import smtplib
import logging
import json
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from anthropic import Anthropic
import requests

ANTHROPIC_API_KEY   = os.environ["ANTHROPIC_API_KEY"]
TAVILY_API_KEY      = os.environ["TAVILY_API_KEY"]
EMAIL_EXPEDITEUR    = os.environ["EMAIL_EXPEDITEUR"]
EMAIL_MOT_DE_PASSE  = os.environ["EMAIL_MOT_DE_PASSE"]
EMAIL_DESTINATAIRES = os.environ["EMAIL_DESTINATAIRES"].split(",")
MODE_DEMANDE        = os.environ.get("MODE", "auto")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
log = logging.getLogger(__name__)

AUJOURD_HUI = datetime.now()
DATE_LABEL  = AUJOURD_HUI.strftime("%A %d %B %Y")
ANNEE       = AUJOURD_HUI.strftime("%Y")

# ============================================================
# DETERMINATION DU MODE
# ============================================================
def determiner_mode():
    if MODE_DEMANDE in ["quotidien", "hebdomadaire", "mensuel"]:
        return MODE_DEMANDE
    # Mode auto : detecter selon le jour
    jour_semaine = AUJOURD_HUI.weekday()  # 0=lundi
    jour_mois    = AUJOURD_HUI.day
    if jour_mois == 1:
        return "mensuel"
    if jour_semaine == 0:
        return "hebdomadaire"
    return "quotidien"

# ============================================================
# CONFIG PAR MODE
# ============================================================
CONFIGS = {
    "quotidien": {
        "jours": 1,
        "label": "Rapport Quotidien",
        "periode": "Dernières 24 heures",
        "badge": "Articles publiés dans les dernières 24h uniquement",
        "max_results": 5,
    },
    "hebdomadaire": {
        "jours": 7,
        "label": "Rapport Hebdomadaire",
        "periode": "7 derniers jours",
        "badge": "Articles publiés dans les 7 derniers jours uniquement",
        "max_results": 7,
    },
    "mensuel": {
        "jours": 30,
        "label": "Rapport Mensuel",
        "periode": "30 derniers jours",
        "badge": "Articles publiés dans les 30 derniers jours uniquement",
        "max_results": 10,
    },
}

# ============================================================
# 18 DOMAINES
# ============================================================
# Sources prioritaires Maroc
SOURCES_MAROC = [
    "medias24.com", "leconomiste.com", "financesnews.press.ma",
    "ledesk.ma", "lavieeco.com", "lematin.ma", "lnt.ma",
    "aujourdhui.ma", "telquel.ma", "hespress.com",
    "bkam.ma", "attijariwafabank.com", "gbp.ma",
    "cihbank.ma", "bmcebank.ma", "sgmaroc.com",
    "acaps.ma", "casafinancecity.com", "gpbm.ma"
]

# Sources prioritaires International
SOURCES_INTL = [
    "finextra.com", "elearningindustry.com", "venturebeat.com",
    "reuters.com", "esgtoday.com", "ft.com",
    "thefintechtimes.com", "td.org", "weforum.org"
]

DOMAINES = [
    {"id": "M1", "label": "Formation Bancaire Maroc",        "couleur": "#1a3a5c", "query": "formation bancaire banque Maroc",                    "sources": SOURCES_MAROC},
    {"id": "M2", "label": "Reglementation BAM ACAPS",        "couleur": "#8b1a2f", "query": "Bank Al-Maghrib reglementation bancaire Maroc",       "sources": SOURCES_MAROC},
    {"id": "M3", "label": "Fintech Startups Maroc",          "couleur": "#c04a00", "query": "fintech startup paiement digital Maroc",              "sources": SOURCES_MAROC},
    {"id": "M4", "label": "Transformation Digitale Banques", "couleur": "#0e5c8b", "query": "transformation digitale banque numerique Maroc",       "sources": SOURCES_MAROC},
    {"id": "M5", "label": "Politiques Formation Emploi",     "couleur": "#2d6a4f", "query": "formation professionnelle emploi competences Maroc",   "sources": SOURCES_MAROC},
    {"id": "M6", "label": "IA Tech Banques Marocaines",      "couleur": "#5c1a8b", "query": "intelligence artificielle IA banque Maroc",            "sources": SOURCES_MAROC},
    {"id": "M7", "label": "RSE Finance Durable Maroc",       "couleur": "#1a6b4a", "query": "finance verte ESG RSE developpement durable Maroc",   "sources": SOURCES_MAROC},
    {"id": "M8", "label": "Competences du Futur Maroc",      "couleur": "#4a7a1a", "query": "competences futur metiers reskilling emploi Maroc",   "sources": SOURCES_MAROC},
    {"id": "I1",  "label": "Innovation Pedagogique Learning", "couleur": "#1a4a7a", "query": "learning innovation microlearning LXP elearning",     "sources": SOURCES_INTL},
    {"id": "I2",  "label": "IA dans la Formation",            "couleur": "#6b1a7a", "query": "AI artificial intelligence corporate training",       "sources": SOURCES_INTL},
    {"id": "I3",  "label": "Fintech Mondiale Open Banking",   "couleur": "#7a3d1a", "query": "fintech open banking embedded finance neobank",       "sources": SOURCES_INTL},
    {"id": "I4",  "label": "IA en Banque Cas Usage",          "couleur": "#1a6b6b", "query": "artificial intelligence banking AI use cases",        "sources": SOURCES_INTL},
    {"id": "I5",  "label": "Reglementation Financiere Intl",  "couleur": "#4a1a5c", "query": "banking regulation compliance Basel AML DORA",        "sources": SOURCES_INTL},
    {"id": "I6",  "label": "Certifications Standards",        "couleur": "#5c3d1a", "query": "banking finance certification CISI CFA ACAMS",        "sources": SOURCES_INTL},
    {"id": "I7",  "label": "Benchmarks Pedagogiques Banque",  "couleur": "#1a5c3d", "query": "bank training best practices financial services",     "sources": SOURCES_INTL},
    {"id": "I8",  "label": "IA Generale Tendances Mondiales", "couleur": "#3d1a5c", "query": "AI artificial intelligence GPT LLM news",             "sources": SOURCES_INTL},
    {"id": "I9",  "label": "RSE Finance Durable Mondiale",    "couleur": "#1a5c1a", "query": "ESG sustainable finance green banking climate",       "sources": SOURCES_INTL},
    {"id": "I10", "label": "Future Skills International",     "couleur": "#7a6b1a", "query": "future of work skills workforce reskilling WEF",      "sources": SOURCES_INTL},
]

# ============================================================
# RECHERCHE TAVILY AVEC FILTRE DATE STRICT
# ============================================================
def rechercher_articles(query, jours, max_results):
    """
    Recherche Tavily avec filtre date strict.
    Utilise les parametres officiels Tavily : topic, time_range, include_domains.
    Rejette tout article plus ancien que la periode demandee.
    """
    # Mapping jours -> time_range Tavily
    time_range = "day" if jours == 1 else ("week" if jours == 7 else "month")

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "topic": "news",
        "time_range": time_range,
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
    }

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json=payload,
            timeout=15
        )
        data = response.json()
        articles_valides = []
        date_limite = AUJOURD_HUI - timedelta(days=jours)

        for r in data.get("results", []):
            date_pub_str = r.get("published_date", "")

            # Si pas de date : on rejette — on ne prend pas de risque
            if not date_pub_str:
                log.info(f"  Rejete (pas de date): {r.get('title','')[:60]}")
                continue

            # Parser et verifier la date strictement
            try:
                date_pub = datetime.fromisoformat(
                    date_pub_str.replace("Z", "").replace("+00:00", "").split("T")[0]
                )
                if date_pub < date_limite:
                    log.info(f"  Rejete (trop ancien {date_pub.strftime('%d/%m/%Y')}): {r.get('title','')[:50]}")
                    continue
            except Exception:
                log.info(f"  Rejete (date illisible): {r.get('title','')[:50]}")
                continue

            source = r.get("url", "")
            source_clean = source.split("/")[2].replace("www.", "") if "/" in source else source

            articles_valides.append({
                "titre":   r.get("title", ""),
                "url":     r.get("url", ""),
                "source":  source_clean,
                "contenu": r.get("content", "")[:600],
                "date":    date_pub.strftime("%d/%m/%Y"),
            })

        log.info(f"  {len(articles_valides)} articles valides dans la periode")
        return articles_valides

    except Exception as e:
        log.warning(f"Erreur Tavily: {e}")
        return []


# ============================================================
# ANALYSE CLAUDE
# ============================================================
def analyser(client, domaine, articles, mode, config):
    """
    Claude analyse uniquement les articles fournis.
    Si liste vide : retourne domaine vide sans inventer.
    """
    if not articles:
        return {
            "id": domaine["id"],
            "label": domaine["label"],
            "couleur": domaine["couleur"],
            "actualites": [],
            "vide": True
        }

    articles_str = "\n\n".join([
        f"ARTICLE {i+1}:\nTitre: {a['titre']}\nSource: {a['source']}\nURL: {a['url']}\nDate: {a['date']}\nExtrait: {a['contenu']}"
        for i, a in enumerate(articles)
    ])

    nb_max = 2 if mode == "quotidien" else (3 if mode == "hebdomadaire" else 4)

    if mode == "mensuel":
        prompt_analyse = f"""Fais une synthese analytique de ces articles sur 30 jours :
- tendance_principale : grande tendance du mois en 2 phrases
- evolution : comment le domaine a evolue ce mois
- recommandation : 1 action concrete pour le responsable formation
- actualites : les {nb_max} articles les plus importants avec resume et implication"""
    else:
        prompt_analyse = f"""Analyse ces articles et pour chacun fournis :
- resume : 2 phrases factuelles
- analyse : 1 phrase d'interpretation
- implication : impact concret pour le responsable formation en banque"""

    prompt = f"""Tu es un analyste expert en veille strategique bancaire et formation.
Domaine : {domaine['label']}
Periode : {config['periode']} — jusqu'au {DATE_LABEL}

ARTICLES TROUVES DANS CETTE PERIODE :
{articles_str}

INSTRUCTION ABSOLUE : Analyse UNIQUEMENT ces articles. Ne fabrique rien. Ne cherche pas ailleurs.

Reponds UNIQUEMENT avec ce JSON brut sans backticks :
{{
  "actualites": [
    {{
      "titre": "Titre exact de l'article",
      "source": "Nom du site",
      "url": "URL exacte",
      "date": "Date de publication",
      "resume": "Resume factuel en 2 phrases",
      "analyse": "Interpretation analytique en 1 phrase",
      "implication": "Implication concrete pour responsable formation en banque"
    }}
  ],
  "tendance": "{("Grande tendance du mois en 1 phrase" if mode == "mensuel" else "")}",
  "recommandation": "{("Action concrete recommandee" if mode == "mensuel" else "")}"
}}

Maximum {nb_max} actualites."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        debut = raw.find("{")
        fin = raw.rfind("}")
        if debut >= 0 and fin >= 0:
            raw = raw[debut:fin+1]
        result = json.loads(raw)
        return {
            "id": domaine["id"],
            "label": domaine["label"],
            "couleur": domaine["couleur"],
            "actualites": result.get("actualites", [])[:nb_max],
            "tendance": result.get("tendance", ""),
            "recommandation": result.get("recommandation", ""),
            "vide": False
        }
    except Exception as e:
        log.warning(f"Erreur Claude {domaine['id']}: {e}")
        return {"id": domaine["id"], "label": domaine["label"], "couleur": domaine["couleur"], "actualites": [], "vide": True}


# ============================================================
# HTML DOMAINE
# ============================================================
def html_domaine(d, mode, config):
    color = d.get("couleur", "#1a3a5c")

    # Case vide — aucune info dans la periode
    if d.get("vide") or not d.get("actualites"):
        return f"""
        <div style="margin-bottom:10px;background:white;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
          <div style="background:{color};padding:8px 15px;">
            <span style="font-family:Georgia,serif;font-size:13px;font-weight:700;color:white;">{d['id']} — {d['label']}</span>
          </div>
          <div style="padding:10px 16px;font-size:12px;color:#bbb;font-style:italic;">
            Aucune information publiée sur ce domaine durant la période : {config['periode']}.
          </div>
        </div>"""

    # Bloc tendance mensuelle
    tendance_html = ""
    if mode == "mensuel" and d.get("tendance"):
        tendance_html = f"""
        <div style="padding:10px 14px;background:{color}12;border-left:3px solid {color};margin-bottom:12px;">
          <div style="font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:{color};font-weight:700;margin-bottom:4px;">Tendance du mois</div>
          <p style="font-size:12px;color:#333;line-height:1.6;margin:0;font-style:italic;">{d['tendance']}</p>
        </div>"""

    # Articles
    actus_html = ""
    for i, a in enumerate(d.get("actualites", [])):
        sep = "border-top:1px solid #ede8e0;padding-top:12px;margin-top:12px;" if i > 0 else ""
        url = a.get("url", "#")
        actus_html += f"""
        <div style="{sep}">
          <table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td><a href="{url}" style="font-family:Georgia,serif;font-size:13px;font-weight:700;color:#1a1a1a;text-decoration:none;line-height:1.4;">{a.get('titre','')}</a></td>
            <td width="110" align="right" valign="top"><span style="font-size:10px;background:#f0ece4;color:#888;padding:2px 5px;">{a.get('source','')}</span></td>
          </tr></table>
          <div style="font-size:10px;color:#1a6b4a;font-weight:600;margin:4px 0;">📅 {a.get('date','')}</div>
          <p style="font-size:12px;color:#555;line-height:1.6;margin:6px 0;">{a.get('resume','')}</p>
          <p style="font-size:12px;color:#333;margin:0 0 6px;"><strong style="color:{color};">Analyse : </strong>{a.get('analyse','')}</p>
          <div style="padding:5px 10px;border-left:3px solid {color};font-size:11px;color:#444;margin-bottom:7px;">→ {a.get('implication','')}</div>
          <a href="{url}" style="font-size:11px;color:{color};font-weight:600;text-decoration:none;">🔗 Lire l'article source</a>
        </div>"""

    # Recommandation mensuelle
    reco_html = ""
    if mode == "mensuel" and d.get("recommandation"):
        reco_html = f"""
        <div style="margin-top:12px;padding:8px 12px;background:#fff8f0;border-left:3px solid #c8a96e;">
          <span style="font-size:11px;color:#c8a96e;font-weight:700;">Recommandation : </span>
          <span style="font-size:12px;color:#444;">{d['recommandation']}</span>
        </div>"""

    return f"""
    <div style="margin-bottom:10px;background:white;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
      <div style="background:{color};padding:8px 15px;">
        <span style="font-family:Georgia,serif;font-size:13px;font-weight:700;color:white;">{d['id']} — {d['label']}</span>
      </div>
      <div style="padding:14px 16px;">
        {tendance_html}
        {actus_html}
        {reco_html}
      </div>
    </div>"""


# ============================================================
# EMAIL BUILDER
# ============================================================
def construire_email(titre, sous_titre, badge, contenu, stats):
    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f7f4ef;font-family:Arial,sans-serif;">
<div style="max-width:680px;margin:0 auto;">

  <div style="background:#0f2540;padding:20px 26px;">
    <div style="font-family:Georgia,serif;font-size:24px;font-weight:900;color:white;">VEILLE STRATEGIQUE</div>
    <div style="font-family:Georgia,serif;font-size:15px;font-weight:700;color:#c8a96e;">{titre}</div>
    <div style="font-size:11px;color:rgba(255,255,255,0.5);margin-top:3px;">{sous_titre}</div>
    <div style="font-size:12px;color:#c8a96e;margin-top:5px;font-weight:600;">{DATE_LABEL}</div>
  </div>

  <div style="background:#1a6b4a;padding:8px 26px;">
    <span style="font-size:11px;color:white;">✅ {badge} — {stats}</span>
  </div>

  <div style="padding:18px 26px;">
    {contenu}
    <div style="border-top:2px solid #0f2540;padding-top:10px;margin-top:14px;">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td style="font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:1px;">Veille Strategique · {DATE_LABEL}</td>
        <td align="right" style="font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:1px;">Sources verifiees · Confidentiel</td>
      </tr></table>
    </div>
  </div>

</div>
</body>
</html>"""


# ============================================================
# ENVOI EMAIL
# ============================================================
def envoyer(sujet, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = sujet
    msg["From"]    = f"Veille Strategique <{EMAIL_EXPEDITEUR}>"
    msg["To"]      = ", ".join(EMAIL_DESTINATAIRES)
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_EXPEDITEUR, EMAIL_MOT_DE_PASSE)
        server.sendmail(EMAIL_EXPEDITEUR, EMAIL_DESTINATAIRES, msg.as_string())
    log.info(f"Email envoye : {sujet}")


# ============================================================
# MAIN
# ============================================================
def main():
    mode = determiner_mode()
    config = CONFIGS[mode]
    log.info(f"Demarrage — Mode : {mode} — Periode : {config['periode']}")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    maroc, intl = [], []

    for domaine in DOMAINES:
        log.info(f"Traitement {domaine['id']} — {domaine['label']}...")
        articles = rechercher_articles(domaine["query"], config["jours"], config["max_results"])
        resultat = analyser(client, domaine, articles, mode, config)
        if domaine["id"].startswith("M"):
            maroc.append(resultat)
        else:
            intl.append(resultat)
        time.sleep(1)

    # Statistiques
    total_m = sum(len(d.get("actualites", [])) for d in maroc)
    total_i = sum(len(d.get("actualites", [])) for d in intl)
    vides_m = sum(1 for d in maroc if d.get("vide"))
    vides_i = sum(1 for d in intl if d.get("vide"))

    prefixe = {"quotidien": "Quotidien", "hebdomadaire": "Hebdo", "mensuel": "Mensuel"}[mode]

    # Email 1 — Maroc
    contenu_m = "".join(html_domaine(d, mode, config) for d in maroc)
    envoyer(
        f"1/2 Veille {prefixe} Maroc — {DATE_LABEL}",
        construire_email(
            f"{config['label']} — Veille Maroc",
            f"Periode stricte : {config['periode']}",
            config["badge"],
            contenu_m,
            f"{total_m} articles · {vides_m} domaine(s) sans info cette periode"
        )
    )
    log.info(f"Email Maroc envoye — {total_m} articles, {vides_m} domaines vides")
    time.sleep(3)

    # Email 2 — International
    contenu_i = "".join(html_domaine(d, mode, config) for d in intl)
    envoyer(
        f"2/2 Veille {prefixe} Internationale — {DATE_LABEL}",
        construire_email(
            f"{config['label']} — Veille Internationale",
            f"Periode stricte : {config['periode']}",
            config["badge"],
            contenu_i,
            f"{total_i} articles · {vides_i} domaine(s) sans info cette periode"
        )
    )
    log.info(f"Email International envoye — {total_i} articles, {vides_i} domaines vides")
    log.info("Veille terminee avec succes !")


if __name__ == "__main__":
    main()
