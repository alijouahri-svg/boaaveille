"""
VEILLE STRATEGIQUE - Version complete et definitive
- Veille quotidienne : articles des 24 dernieres heures avec liens verifies
- Synthese quinzaine : analyse des tendances des 15 derniers jours
- Tavily API : recherche web reelle
- 2 emails separes pour eviter le blocage Gmail
"""

import os
import smtplib
import logging
import json
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from anthropic import Anthropic
import requests

ANTHROPIC_API_KEY   = os.environ["ANTHROPIC_API_KEY"]
TAVILY_API_KEY      = os.environ["TAVILY_API_KEY"]
EMAIL_EXPEDITEUR    = os.environ["EMAIL_EXPEDITEUR"]
EMAIL_MOT_DE_PASSE  = os.environ["EMAIL_MOT_DE_PASSE"]
EMAIL_DESTINATAIRES = os.environ["EMAIL_DESTINATAIRES"].split(",")
MODE                = os.environ.get("MODE", "quotidien")  # quotidien ou quinzaine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
log = logging.getLogger(__name__)

# ============================================================
# 18 DOMAINES DE VEILLE
# ============================================================
DOMAINES = [
    {"id": "M1", "label": "Formation Bancaire Maroc",        "couleur": "#1a3a5c", "query": "formation bancaire Maroc LMS apprentissage banque"},
    {"id": "M2", "label": "Reglementation BAM ACAPS",        "couleur": "#8b1a2f", "query": "Bank Al-Maghrib BAM réglementation bancaire Maroc"},
    {"id": "M3", "label": "Fintech Startups Maroc",          "couleur": "#c04a00", "query": "fintech startup paiement mobile Maroc"},
    {"id": "M4", "label": "Transformation Digitale Banques", "couleur": "#0e5c8b", "query": "transformation digitale banque Maroc numérique"},
    {"id": "M5", "label": "Politiques Formation Emploi",     "couleur": "#2d6a4f", "query": "formation professionnelle emploi compétences Maroc"},
    {"id": "M6", "label": "IA Tech Banques Marocaines",      "couleur": "#5c1a8b", "query": "intelligence artificielle IA banque Maroc"},
    {"id": "M7", "label": "RSE Finance Durable Maroc",       "couleur": "#1a6b4a", "query": "finance verte ESG banque Maroc développement durable"},
    {"id": "M8", "label": "Competences du Futur Maroc",      "couleur": "#4a7a1a", "query": "compétences futur métiers reskilling Maroc 2030"},
    {"id": "I1",  "label": "Innovation Pedagogique Learning", "couleur": "#1a4a7a", "query": "innovation learning microlearning LXP elearning"},
    {"id": "I2",  "label": "IA dans la Formation",            "couleur": "#6b1a7a", "query": "artificial intelligence AI learning training corporate"},
    {"id": "I3",  "label": "Fintech Mondiale Open Banking",   "couleur": "#7a3d1a", "query": "fintech open banking embedded finance neobank"},
    {"id": "I4",  "label": "IA en Banque Cas Usage",          "couleur": "#1a6b6b", "query": "AI banking artificial intelligence fraud detection credit"},
    {"id": "I5",  "label": "Reglementation Financiere Intl",  "couleur": "#4a1a5c", "query": "banking regulation Basel DORA AML compliance"},
    {"id": "I6",  "label": "Certifications Standards",        "couleur": "#5c3d1a", "query": "banking certification CISI CFA ACAMS finance"},
    {"id": "I7",  "label": "Benchmarks Pedagogiques Banque",  "couleur": "#1a5c3d", "query": "bank training best practices learning financial services"},
    {"id": "I8",  "label": "IA Generale Tendances Mondiales", "couleur": "#3d1a5c", "query": "large language models AI GPT Claude Gemini news"},
    {"id": "I9",  "label": "RSE Finance Durable Mondiale",    "couleur": "#1a5c1a", "query": "ESG sustainable finance green banking CSRD"},
    {"id": "I10", "label": "Future Skills International",     "couleur": "#7a6b1a", "query": "future skills workforce reskilling WEF jobs 2030"},
]

# ============================================================
# RECHERCHE TAVILY
# ============================================================
def rechercher_articles(query, jours=1, max_results=3):
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
                "days": jours,
            },
            timeout=15
        )
        data = response.json()
        articles = []
        for r in data.get("results", []):
            source = r.get("url", "")
            source_clean = source.split("/")[2].replace("www.", "") if "/" in source else source
            articles.append({
                "titre": r.get("title", ""),
                "url": r.get("url", ""),
                "source": source_clean,
                "contenu": r.get("content", "")[:600],
                "date": r.get("published_date", "")
            })
        return articles
    except Exception as e:
        log.warning(f"Erreur Tavily pour '{query}': {e}")
        return []


# ============================================================
# ANALYSE CLAUDE — QUOTIDIEN
# ============================================================
def analyser_quotidien(client, domaine, articles):
    if not articles:
        return {"id": domaine["id"], "label": domaine["label"], "couleur": domaine["couleur"], "actualites": []}

    articles_str = "\n\n".join([
        f"ARTICLE {i+1}:\nTitre: {a['titre']}\nSource: {a['source']}\nURL: {a['url']}\nDate: {a['date']}\nExtrait: {a['contenu']}"
        for i, a in enumerate(articles)
    ])

    prompt = f"""Tu es un analyste expert en veille strategique bancaire et formation.
Domaine : {domaine['label']}

Analyse UNIQUEMENT ces vrais articles. Ne fabrique rien.

{articles_str}

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
      "implication": "Implication concrete pour un responsable formation en banque"
    }}
  ]
}}

Maximum 2 actualites. Ignore les articles non pertinents pour ce domaine."""

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
            "actualites": result.get("actualites", [])[:2]
        }
    except Exception as e:
        log.warning(f"Erreur Claude pour {domaine['id']}: {e}")
        return {"id": domaine["id"], "label": domaine["label"], "couleur": domaine["couleur"], "actualites": []}


# ============================================================
# ANALYSE CLAUDE — QUINZAINE
# ============================================================
def analyser_quinzaine(client, domaine, articles):
    if not articles:
        return {"id": domaine["id"], "label": domaine["label"], "couleur": domaine["couleur"], "synthese": None}

    articles_str = "\n\n".join([
        f"ARTICLE {i+1}:\nTitre: {a['titre']}\nSource: {a['source']}\nURL: {a['url']}\nDate: {a['date']}\nExtrait: {a['contenu']}"
        for i, a in enumerate(articles)
    ])

    prompt = f"""Tu es un analyste expert en veille strategique bancaire et formation.
Domaine : {domaine['label']}
Periode : 15 derniers jours

Voici les articles trouves sur ce domaine ces 15 derniers jours :

{articles_str}

Fais une synthese analytique de quinzaine. Reponds UNIQUEMENT avec ce JSON brut sans backticks :
{{
  "tendance_principale": "La grande tendance qui se degage sur ce domaine ces 15 jours en 2 phrases",
  "faits_marquants": [
    {{
      "titre": "Fait marquant 1",
      "url": "URL source",
      "source": "Nom du site",
      "impact": "Impact et implications pour la formation bancaire"
    }},
    {{
      "titre": "Fait marquant 2",
      "url": "URL source",
      "source": "Nom du site",
      "impact": "Impact et implications"
    }}
  ],
  "evolution": "Comment ce domaine a evolue par rapport a la quinzaine precedente",
  "recommandation": "1 action concrete recommandee pour le responsable formation"
}}"""

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
            "synthese": result
        }
    except Exception as e:
        log.warning(f"Erreur Claude quinzaine pour {domaine['id']}: {e}")
        return {"id": domaine["id"], "label": domaine["label"], "couleur": domaine["couleur"], "synthese": None}


# ============================================================
# HTML — DOMAINE QUOTIDIEN
# ============================================================
def html_domaine_quotidien(d):
    color = d.get("couleur", "#1a3a5c")
    actualites = d.get("actualites", [])

    if not actualites:
        return f"""
        <div style="margin-bottom:12px;background:white;box-shadow:0 1px 4px rgba(0,0,0,0.07);">
          <div style="background:{color};padding:9px 15px;">
            <span style="font-family:Georgia,serif;font-size:14px;font-weight:700;color:white;">{d['id']} - {d['label']}</span>
          </div>
          <div style="padding:12px 16px;font-size:12px;color:#aaa;font-style:italic;">
            Aucun article publie dans les dernieres 24h pour ce domaine.
          </div>
        </div>"""

    actus_html = ""
    for i, a in enumerate(actualites):
        sep = "border-top:1px solid #ede8e0;padding-top:14px;margin-top:14px;" if i > 0 else ""
        url = a.get("url", "#")
        actus_html += f"""
        <div style="{sep}">
          <table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td style="font-family:Georgia,serif;font-size:13px;font-weight:700;color:#1a1a1a;line-height:1.4;">
              <a href="{url}" style="color:#1a1a1a;text-decoration:none;">{a.get('titre','')}</a>
            </td>
            <td width="120" align="right" valign="top">
              <span style="font-size:10px;background:#f0ece4;color:#888;padding:2px 6px;">{a.get('source','')}</span>
            </td>
          </tr></table>
          <div style="font-size:10px;color:#aaa;margin:3px 0;">{a.get('date','')}</div>
          <p style="font-size:12px;color:#555;line-height:1.65;margin:7px 0;">{a.get('resume','')}</p>
          <p style="font-size:12px;color:#333;line-height:1.6;margin:0 0 7px;">
            <strong style="color:{color};">Analyse : </strong>{a.get('analyse','')}
          </p>
          <div style="padding:6px 10px;border-left:3px solid {color};font-size:11px;color:#444;margin-bottom:8px;">
            → {a.get('implication','')}
          </div>
          <a href="{url}" style="font-size:11px;color:{color};font-weight:600;">
            🔗 Lire l'article source
          </a>
        </div>"""

    return f"""
    <div style="margin-bottom:12px;background:white;box-shadow:0 1px 4px rgba(0,0,0,0.07);">
      <div style="background:{color};padding:9px 15px;">
        <span style="font-family:Georgia,serif;font-size:14px;font-weight:700;color:white;">{d['id']} - {d['label']}</span>
      </div>
      <div style="padding:14px 16px;">{actus_html}</div>
    </div>"""


# ============================================================
# HTML — DOMAINE QUINZAINE
# ============================================================
def html_domaine_quinzaine(d):
    color = d.get("couleur", "#1a3a5c")
    synthese = d.get("synthese")

    if not synthese:
        return f"""
        <div style="margin-bottom:12px;background:white;box-shadow:0 1px 4px rgba(0,0,0,0.07);">
          <div style="background:{color};padding:9px 15px;">
            <span style="font-family:Georgia,serif;font-size:14px;font-weight:700;color:white;">{d['id']} - {d['label']}</span>
          </div>
          <div style="padding:12px 16px;font-size:12px;color:#aaa;font-style:italic;">
            Pas suffisamment d'articles sur ce domaine cette quinzaine.
          </div>
        </div>"""

    faits_html = ""
    for f in synthese.get("faits_marquants", []):
        url = f.get("url", "#")
        faits_html += f"""
        <div style="border-top:1px solid #ede8e0;padding-top:12px;margin-top:12px;">
          <a href="{url}" style="font-family:Georgia,serif;font-size:13px;font-weight:700;color:#1a1a1a;text-decoration:none;">{f.get('titre','')}</a>
          <span style="font-size:10px;background:#f0ece4;color:#888;padding:2px 6px;margin-left:8px;">{f.get('source','')}</span>
          <p style="font-size:12px;color:#444;margin:6px 0;">{f.get('impact','')}</p>
          <a href="{url}" style="font-size:11px;color:{color};font-weight:600;">🔗 Source</a>
        </div>"""

    return f"""
    <div style="margin-bottom:12px;background:white;box-shadow:0 1px 4px rgba(0,0,0,0.07);">
      <div style="background:{color};padding:9px 15px;">
        <span style="font-family:Georgia,serif;font-size:14px;font-weight:700;color:white;">{d['id']} - {d['label']}</span>
      </div>
      <div style="padding:14px 16px;">
        <div style="padding:10px 14px;background:{color}12;border-left:3px solid {color};margin-bottom:12px;">
          <div style="font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:{color};font-weight:700;margin-bottom:5px;">Tendance principale</div>
          <p style="font-size:13px;color:#333;line-height:1.6;margin:0;font-style:italic;">{synthese.get('tendance_principale','')}</p>
        </div>
        <div style="font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:#aaa;margin-bottom:8px;">Faits marquants</div>
        {faits_html}
        <div style="margin-top:14px;padding:8px 12px;background:#f0f7ff;border-left:3px solid #1a3a5c;">
          <span style="font-size:11px;color:#1a3a5c;font-weight:700;">Evolution : </span>
          <span style="font-size:12px;color:#444;">{synthese.get('evolution','')}</span>
        </div>
        <div style="margin-top:8px;padding:8px 12px;background:#fff8f0;border-left:3px solid #c8a96e;">
          <span style="font-size:11px;color:#c8a96e;font-weight:700;">Recommandation : </span>
          <span style="font-size:12px;color:#444;">{synthese.get('recommandation','')}</span>
        </div>
      </div>
    </div>"""


# ============================================================
# EMAIL BUILDER
# ============================================================
def construire_email(date, titre, sous_titre, badge, contenu):
    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f7f4ef;font-family:Arial,sans-serif;">
<div style="max-width:680px;margin:0 auto;">
  <div style="background:#0f2540;padding:22px 28px;">
    <div style="font-family:Georgia,serif;font-size:24px;font-weight:900;color:white;">VEILLE STRATEGIQUE</div>
    <div style="font-family:Georgia,serif;font-size:15px;font-weight:700;color:#c8a96e;">{titre}</div>
    <div style="font-size:11px;color:rgba(255,255,255,0.5);margin-top:4px;">{sous_titre}</div>
    <div style="font-size:12px;color:#c8a96e;margin-top:5px;font-weight:600;">{date}</div>
  </div>
  <div style="background:#1a6b4a;padding:8px 28px;">
    <span style="font-size:11px;color:white;">✅ {badge}</span>
  </div>
  <div style="padding:20px 28px;">
    {contenu}
    <div style="border-top:2px solid #0f2540;padding-top:12px;margin-top:16px;">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td style="font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:1.5px;">Veille Strategique · {date}</td>
        <td align="right" style="font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:1.5px;">Sources verifiees · Confidentiel</td>
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
# MODE QUOTIDIEN
# ============================================================
def run_quotidien(client, date):
    log.info("MODE : Veille Quotidienne")
    maroc, intl = [], []

    for domaine in DOMAINES:
        log.info(f"Traitement {domaine['id']}...")
        articles = rechercher_articles(domaine["query"], jours=1, max_results=3)
        log.info(f"  {len(articles)} articles trouves")
        resultat = analyser_quotidien(client, domaine, articles)
        if domaine["id"].startswith("M"):
            maroc.append(resultat)
        else:
            intl.append(resultat)
        time.sleep(1)

    total_maroc = sum(len(d.get("actualites", [])) for d in maroc)
    total_intl  = sum(len(d.get("actualites", [])) for d in intl)

    # Email 1 — Maroc
    contenu_maroc = "".join(html_domaine_quotidien(d) for d in maroc)
    html1 = construire_email(
        date,
        "Rapport Quotidien — Partie 1",
        "Veille Maroc · Articles des dernieres 24h",
        f"{total_maroc} articles verifies avec liens · 24h uniquement",
        contenu_maroc
    )
    envoyer(f"1/2 Veille Maroc - {date}", html1)
    time.sleep(3)

    # Email 2 — International
    contenu_intl = "".join(html_domaine_quotidien(d) for d in intl)
    html2 = construire_email(
        date,
        "Rapport Quotidien — Partie 2",
        "Veille Internationale · Articles des dernieres 24h",
        f"{total_intl} articles verifies avec liens · 24h uniquement",
        contenu_intl
    )
    envoyer(f"2/2 Veille Internationale - {date}", html2)


# ============================================================
# MODE QUINZAINE
# ============================================================
def run_quinzaine(client, date):
    log.info("MODE : Synthese Quinzaine")
    maroc, intl = [], []

    for domaine in DOMAINES:
        log.info(f"Synthese {domaine['id']}...")
        articles = rechercher_articles(domaine["query"], jours=15, max_results=5)
        log.info(f"  {len(articles)} articles trouves sur 15 jours")
        resultat = analyser_quinzaine(client, domaine, articles)
        if domaine["id"].startswith("M"):
            maroc.append(resultat)
        else:
            intl.append(resultat)
        time.sleep(1)

    # Email 1 — Synthese Maroc
    contenu_maroc = "".join(html_domaine_quinzaine(d) for d in maroc)
    html1 = construire_email(
        date,
        "Synthese de Quinzaine — Partie 1",
        "Veille Maroc · Bilan des 15 derniers jours",
        "Synthese analytique · Tendances · Faits marquants · Recommandations",
        contenu_maroc
    )
    envoyer(f"1/2 Synthese Quinzaine Maroc - {date}", html1)
    time.sleep(3)

    # Email 2 — Synthese International
    contenu_intl = "".join(html_domaine_quinzaine(d) for d in intl)
    html2 = construire_email(
        date,
        "Synthese de Quinzaine — Partie 2",
        "Veille Internationale · Bilan des 15 derniers jours",
        "Synthese analytique · Tendances · Faits marquants · Recommandations",
        contenu_intl
    )
    envoyer(f"2/2 Synthese Quinzaine Internationale - {date}", html2)


# ============================================================
# MAIN
# ============================================================
def main():
    date = datetime.now().strftime("%A %d %B %Y")
    log.info(f"Demarrage veille du {date} — Mode : {MODE}")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    # Determiner automatiquement le mode selon la date
    jour = datetime.now().day
    mode_effectif = MODE

    # Si lance automatiquement (pas manuellement), verifier si c'est le 1er ou le 15
    if MODE == "quotidien" and jour in [1, 15]:
        log.info(f"Jour {jour} du mois — lancement automatique de la synthese quinzaine")
        mode_effectif = "quinzaine"

    if mode_effectif == "quinzaine":
        run_quinzaine(client, date)
    else:
        run_quotidien(client, date)

    log.info("Veille terminee avec succes !")


if __name__ == "__main__":
    main()
