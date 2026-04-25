"""
VEILLE STRATEGIQUE - Basée sur flux RSS
Sources marocaines et internationales vérifiées
Filtre date strict : 24h / 7 jours / 30 jours
Zéro hallucination — uniquement vrais articles
"""

import os
import smtplib
import logging
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from anthropic import Anthropic
import requests
from email.utils import parsedate_to_datetime

ANTHROPIC_API_KEY   = os.environ["ANTHROPIC_API_KEY"]
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
# SOURCES RSS VERIFIEES
# ============================================================
SOURCES_RSS_MAROC = [
    "https://www.leconomiste.com/rss-leconomiste",
    "https://www.lavieeco.com/feed/",
    "https://lnt.ma/feed/",
    "https://aujourdhui.ma/feed",
    "https://www.hespress.com/feed",
    "https://www.libe.ma/xml/syndication.rss",
    "https://www.mapnews.ma/en/actualites/general/rss",
    "https://www.moroccoworldnews.com/feed/",
    "https://www.medias24.com/feed/",
    "https://financesnews.press.ma/feed/",
]

SOURCES_RSS_INTL = [
    "https://www.finextra.com/rss/headlines.aspx",
    "https://feeds.reuters.com/reuters/businessNews",
    "https://esgtoday.com/feed/",
    "https://elearningindustry.com/feed",
    "https://venturebeat.com/feed/",
    "https://thefintechtimes.com/feed/",
    "https://www.weforum.org/agenda/feed/",
    "https://feeds.ft.com/rss/companies-financials",
]

# ============================================================
# DOMAINES ET MOTS-CLES
# ============================================================
DOMAINES_MAROC = [
    {"id": "M1", "label": "Formation Bancaire Maroc", "couleur": "#1a3a5c",
     "keywords": ["formation bancaire", "formation banque", "e-learning banque", "LMS bancaire", "GPBM formation", "Institut Bancaire Marocain", "OFPPT banque", "competences bancaires"]},
    {"id": "M2", "label": "Reglementation BAM ACAPS", "couleur": "#8b1a2f",
     "keywords": ["Bank Al-Maghrib", "BAM circulaire", "ACAPS", "reglementation bancaire maroc", "supervision bancaire", "formation BAM", "formation Bank Al-Maghrib"]},
    {"id": "M3", "label": "Fintech Startups Maroc", "couleur": "#c04a00",
     "keywords": ["fintech maroc", "paiement mobile maroc", "neobanque maroc", "startup fintech maroc", "portefeuille electronique", "paiement digital maroc"]},
    {"id": "M4", "label": "Transformation Digitale Banques", "couleur": "#0e5c8b",
     "keywords": ["digitalisation banque", "banque digitale", "banque numerique", "application bancaire", "banque en ligne maroc", "formation en ligne", "e-learning"]},
    {"id": "M5", "label": "Politiques Formation Emploi", "couleur": "#2d6a4f",
     "keywords": ["formation professionnelle maroc", "OFPPT", "ANAPEC", "emploi banque maroc", "competences professionnelles maroc"]},
    {"id": "M6", "label": "IA Tech Banques Marocaines", "couleur": "#5c1a8b",
     "keywords": ["intelligence artificielle banque", "IA banque maroc", "machine learning finance", "chatbot bancaire", "intelligence artificielle maroc"]},
    {"id": "M7", "label": "RSE Finance Durable Maroc", "couleur": "#1a6b4a",
     "keywords": ["finance verte maroc", "green bonds maroc", "ESG maroc", "obligations vertes maroc", "RSE maroc", "green finance", "formation RSE", "formation finance verte", "formation green business"]},
    {"id": "M8", "label": "Competences du Futur Maroc", "couleur": "#4a7a1a",
     "keywords": ["Future Skills", "nouvelles competences", "new skills", "competences futur maroc", "metiers avenir maroc", "reskilling maroc", "upskilling maroc"]},
]

DOMAINES_INTL = [
    {"id": "I1",  "label": "Innovation Pédagogique & Learning", "couleur": "#1a4a7a",
     "keywords": ["microlearning", "learning experience", "LXP", "adaptive learning", "elearning", "corporate training", "instructional design"]},
    {"id": "I2",  "label": "IA dans la Formation",              "couleur": "#6b1a7a",
     "keywords": ["AI learning", "artificial intelligence training", "generative AI education", "ChatGPT training", "AI tutor", "learning analytics"]},
    {"id": "I3",  "label": "Fintech Mondiale & Open Banking",   "couleur": "#7a3d1a",
     "keywords": ["fintech", "open banking", "embedded finance", "neobank", "digital banking", "BaaS", "BNPL"]},
    {"id": "I4",  "label": "IA en Banque — Cas d'Usage",        "couleur": "#1a6b6b",
     "keywords": ["AI banking", "artificial intelligence finance", "fraud detection", "credit scoring AI", "robo-advisor", "generative AI bank"]},
    {"id": "I5",  "label": "Réglementation Financière Intl",    "couleur": "#4a1a5c",
     "keywords": ["Basel", "DORA", "AML", "regulation banking", "MiCA", "compliance", "financial regulation"]},
    {"id": "I6",  "label": "Certifications & Standards",        "couleur": "#5c3d1a",
     "keywords": ["CISI", "CFA", "ACAMS", "banking certification", "finance qualification"]},
    {"id": "I7",  "label": "Benchmarks Pédagogiques Banque",    "couleur": "#1a5c3d",
     "keywords": ["bank training", "financial services learning", "L&D banking", "learning ROI", "upskilling finance"]},
    {"id": "I8",  "label": "IA Générale — Tendances Mondiales", "couleur": "#3d1a5c",
     "keywords": ["GPT", "Claude", "Gemini", "LLM", "large language model", "AI regulation", "artificial intelligence", "foundation model"]},
    {"id": "I9",  "label": "RSE & Finance Durable Mondiale",    "couleur": "#1a5c1a",
     "keywords": ["ESG", "sustainable finance", "green banking", "CSRD", "climate risk", "net zero", "sustainable investment"]},
    {"id": "I10", "label": "Future Skills — International",     "couleur": "#7a6b1a",
     "keywords": ["future of work", "future skills", "reskilling", "upskilling", "workforce", "WEF jobs", "skills gap"]},
]

# ============================================================
# DETERMINATION DU MODE
# ============================================================
CONFIGS = {
    "quotidien":     {"jours": 1,  "label": "Rapport Quotidien",     "periode": "24 dernières heures",   "nb_articles": 2},
    "hebdomadaire":  {"jours": 7,  "label": "Rapport Hebdomadaire",  "periode": "7 derniers jours",      "nb_articles": 3},
    "mensuel":       {"jours": 30, "label": "Rapport Mensuel",       "periode": "30 derniers jours",     "nb_articles": 4},
}

def determiner_mode():
    if MODE_DEMANDE in CONFIGS:
        return MODE_DEMANDE
    jour_semaine = AUJOURD_HUI.weekday()
    jour_mois    = AUJOURD_HUI.day
    if jour_mois == 1:
        return "mensuel"
    if jour_semaine == 0:
        return "hebdomadaire"
    return "quotidien"

# ============================================================
# LECTURE DES FLUX RSS
# ============================================================
def lire_flux_rss(url, jours):
    """Lit un flux RSS et retourne les articles dans la période demandée."""
    articles = []
    date_limite = AUJOURD_HUI - timedelta(days=jours)

    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; VeilleStrategique/1.0)"}
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code != 200:
            log.warning(f"  RSS non accessible ({response.status_code}): {url}")
            return []

        root = ET.fromstring(response.content)

        # Trouver tous les items (RSS 2.0 et Atom)
        items = root.findall(".//item")
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

        for item in items:
            # Titre
            titre_el = item.find("title")
            if titre_el is None:
                titre_el = item.find("{http://www.w3.org/2005/Atom}title")
            titre = titre_el.text if titre_el is not None else ""

            # URL
            lien_el = item.find("link")
            if lien_el is None:
                lien_el = item.find("{http://www.w3.org/2005/Atom}link")
            lien = lien_el.text if lien_el is not None else ""
            if not lien and lien_el is not None:
                lien = lien_el.get("href", "")

            # Description
            desc_el = item.find("description")
            if desc_el is None:
                desc_el = item.find("{http://www.w3.org/2005/Atom}summary")
            description = desc_el.text if desc_el is not None else ""
            if description:
                # Nettoyer les balises HTML basiques
                import re
                description = re.sub(r'<[^>]+>', ' ', description)
                description = re.sub(r'\s+', ' ', description).strip()[:400]

            # Date
            date_el = item.find("pubDate")
            if date_el is None:
                date_el = item.find("{http://www.w3.org/2005/Atom}published")
            if date_el is None:
                date_el = item.find("{http://www.w3.org/2005/Atom}updated")

            date_pub = None
            if date_el is not None and date_el.text:
                try:
                    # Format RSS standard
                    date_pub = parsedate_to_datetime(date_el.text).replace(tzinfo=None)
                except Exception:
                    try:
                        # Format ISO
                        date_str = date_el.text[:19]
                        date_pub = datetime.fromisoformat(date_str)
                    except Exception:
                        pass

            # Filtre date strict
            if date_pub is None:
                continue
            if date_pub < date_limite:
                continue

            # Source
            source = url.split("/")[2].replace("www.", "")

            articles.append({
                "titre": titre.strip() if titre else "",
                "url": lien.strip() if lien else "",
                "source": source,
                "description": description,
                "date": date_pub.strftime("%d/%m/%Y %H:%M"),
                "date_obj": date_pub,
            })

    except Exception as e:
        log.warning(f"  Erreur RSS {url}: {e}")

    return articles


def collecter_articles_rss(sources_rss, jours):
    """Collecte tous les articles de toutes les sources RSS."""
    tous_articles = []
    for url in sources_rss:
        try:
            articles = lire_flux_rss(url, jours)
            log.info(f"  {url.split('/')[2]} : {len(articles)} articles")
            tous_articles.extend(articles)
        except Exception as e:
            log.warning(f"  Erreur {url}: {e}")

    # Trier par date décroissante
    tous_articles.sort(key=lambda x: x.get("date_obj", datetime.min), reverse=True)
    return tous_articles


def filtrer_par_keywords(articles, keywords):
    """Filtre les articles par mots-cles dans le TITRE uniquement - strict."""
    articles_pertinents = []
    for article in articles:
        titre = article.get("titre", "").lower()
        for kw in keywords:
            if kw.lower() in titre:
                articles_pertinents.append(article)
                break
    return articles_pertinents


# ============================================================
# ANALYSE CLAUDE
# ============================================================
def analyser_avec_claude(client, domaine, articles, nb_max):
    if not articles:
        return {"id": domaine["id"], "label": domaine["label"], "couleur": domaine["couleur"], "actualites": [], "vide": True}

    articles_str = "\n\n".join([
        f"ARTICLE {i+1}:\nTitre: {a['titre']}\nSource: {a['source']}\nURL: {a['url']}\nDate: {a['date']}\nExtrait: {a['description']}"
        for i, a in enumerate(articles[:nb_max * 2])  # On lui donne plus pour qu'il choisisse les meilleurs
    ])

    prompt = f"""Tu es un analyste expert en veille strategique bancaire et formation.
Domaine : {domaine['label']}
Date : {DATE_LABEL}

Voici des articles REELS trouves dans les flux RSS de presse. Analyse UNIQUEMENT ces articles.
Ne fabrique rien. Ne complete pas avec tes propres connaissances.

{articles_str}

Selectionne les {nb_max} articles les plus pertinents pour ce domaine.
Reponds UNIQUEMENT avec ce JSON brut sans backticks :
{{
  "actualites": [
    {{
      "titre": "Titre exact de l'article",
      "source": "Nom du journal/site",
      "url": "URL exacte",
      "date": "Date de publication",
      "resume": "Resume factuel en 2 phrases basees sur l'extrait fourni",
      "analyse": "Interpretation analytique en 1 phrase",
      "implication": "Implication concrete pour un responsable formation en banque"
    }}
  ]
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
            "actualites": result.get("actualites", [])[:nb_max],
            "vide": False
        }
    except Exception as e:
        log.warning(f"Erreur Claude {domaine['id']}: {e}")
        return {"id": domaine["id"], "label": domaine["label"], "couleur": domaine["couleur"], "actualites": [], "vide": True}


# ============================================================
# GENERATION HTML
# ============================================================
def html_domaine(d, config):
    color = d.get("couleur", "#1a3a5c")

    if d.get("vide") or not d.get("actualites"):
        return f"""
        <div style="margin-bottom:10px;background:white;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
          <div style="background:{color};padding:8px 15px;">
            <span style="font-family:Georgia,serif;font-size:13px;font-weight:700;color:white;">{d['id']} — {d['label']}</span>
          </div>
          <div style="padding:10px 16px;font-size:12px;color:#bbb;font-style:italic;">
            Aucun article publié sur ce domaine durant la période : {config['periode']}.
          </div>
        </div>"""

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

    return f"""
    <div style="margin-bottom:10px;background:white;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
      <div style="background:{color};padding:8px 15px;">
        <span style="font-family:Georgia,serif;font-size:13px;font-weight:700;color:white;">{d['id']} — {d['label']}</span>
      </div>
      <div style="padding:14px 16px;">{actus_html}</div>
    </div>"""


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
        <td align="right" style="font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:1px;">Sources RSS verifiees · Confidentiel</td>
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
    log.info(f"Mode : {mode} — Periode : {config['periode']}")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    # Collecte RSS Maroc
    log.info("Collecte flux RSS Maroc...")
    articles_maroc = collecter_articles_rss(SOURCES_RSS_MAROC, config["jours"])
    log.info(f"Total articles Maroc bruts : {len(articles_maroc)}")

    # Collecte RSS International
    log.info("Collecte flux RSS International...")
    articles_intl = collecter_articles_rss(SOURCES_RSS_INTL, config["jours"])
    log.info(f"Total articles International bruts : {len(articles_intl)}")

    # Traitement domaines Maroc
    resultats_maroc = []
    for domaine in DOMAINES_MAROC:
        log.info(f"Traitement {domaine['id']} - {domaine['label']}...")
        articles_filtres = filtrer_par_keywords(articles_maroc, domaine["keywords"])
        log.info(f"  {len(articles_filtres)} articles pertinents")
        if articles_filtres:
            resultat = analyser_avec_claude(client, domaine, articles_filtres, config["nb_articles"])
        else:
            resultat = {"id": domaine["id"], "label": domaine["label"], "couleur": domaine["couleur"], "actualites": [], "vide": True}
        resultats_maroc.append(resultat)
        time.sleep(0.5)

    # Traitement domaines International
    resultats_intl = []
    for domaine in DOMAINES_INTL:
        log.info(f"Traitement {domaine['id']} - {domaine['label']}...")
        articles_filtres = filtrer_par_keywords(articles_intl, domaine["keywords"])
        log.info(f"  {len(articles_filtres)} articles pertinents")
        if articles_filtres:
            resultat = analyser_avec_claude(client, domaine, articles_filtres, config["nb_articles"])
        else:
            resultat = {"id": domaine["id"], "label": domaine["label"], "couleur": domaine["couleur"], "actualites": [], "vide": True}
        resultats_intl.append(resultat)
        time.sleep(0.5)

    # Stats
    total_m = sum(len(d.get("actualites", [])) for d in resultats_maroc)
    total_i = sum(len(d.get("actualites", [])) for d in resultats_intl)
    vides_m = sum(1 for d in resultats_maroc if d.get("vide"))
    vides_i = sum(1 for d in resultats_intl if d.get("vide"))

    prefixe = {"quotidien": "Quotidien", "hebdomadaire": "Hebdo", "mensuel": "Mensuel"}[mode]

    # Email 1 — Maroc
    contenu_m = "".join(html_domaine(d, config) for d in resultats_maroc)
    envoyer(
        f"1/2 Veille {prefixe} Maroc — {DATE_LABEL}",
        construire_email(
            f"{config['label']} — Veille Maroc",
            f"Sources RSS : leconomiste.com · lavieeco.com · medias24.com · lematin.ma · lnt.ma et plus",
            f"Articles verifies directement depuis les flux RSS — {config['periode']} uniquement",
            contenu_m,
            f"{total_m} articles · {vides_m} domaine(s) sans info cette periode"
        )
    )
    log.info(f"Email Maroc envoye — {total_m} articles")
    time.sleep(3)

    # Email 2 — International
    contenu_i = "".join(html_domaine(d, config) for d in resultats_intl)
    envoyer(
        f"2/2 Veille {prefixe} Internationale — {DATE_LABEL}",
        construire_email(
            f"{config['label']} — Veille Internationale",
            f"Sources RSS : finextra.com · reuters.com · venturebeat.com · esgtoday.com · weforum.org et plus",
            f"Articles verifies directement depuis les flux RSS — {config['periode']} uniquement",
            contenu_i,
            f"{total_i} articles · {vides_i} domaine(s) sans info cette periode"
        )
    )
    log.info(f"Email International envoye — {total_i} articles")
    log.info("Veille terminee avec succes !")


if __name__ == "__main__":
    main()
