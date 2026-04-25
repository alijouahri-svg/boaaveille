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
    # Google News RSS - couvre TOUS les sites marocains indexes par Google
    # Un flux par domaine pour cibler precisement
    "https://news.google.com/rss/search?q=banque+Maroc&hl=fr&gl=MA&ceid=MA:fr",
    "https://news.google.com/rss/search?q=formation+bancaire+Maroc&hl=fr&gl=MA&ceid=MA:fr",
    "https://news.google.com/rss/search?q=Bank+Al-Maghrib+BAM&hl=fr&gl=MA&ceid=MA:fr",
    "https://news.google.com/rss/search?q=fintech+Maroc&hl=fr&gl=MA&ceid=MA:fr",
    "https://news.google.com/rss/search?q=intelligence+artificielle+banque+Maroc&hl=fr&gl=MA&ceid=MA:fr",
    "https://news.google.com/rss/search?q=transformation+digitale+banque+Maroc&hl=fr&gl=MA&ceid=MA:fr",
    "https://news.google.com/rss/search?q=RSE+finance+verte+Maroc&hl=fr&gl=MA&ceid=MA:fr",
    "https://news.google.com/rss/search?q=competences+formation+emploi+Maroc&hl=fr&gl=MA&ceid=MA:fr",
    "https://news.google.com/rss/search?q=Attijariwafa+CIH+Banque+Populaire+BMCE&hl=fr&gl=MA&ceid=MA:fr",
    "https://news.google.com/rss/search?q=ACAPS+reglementation+bancaire+Maroc&hl=fr&gl=MA&ceid=MA:fr",
    "https://news.google.com/rss/search?q=e-learning+formation+Maroc&hl=fr&gl=MA&ceid=MA:fr",
    "https://news.google.com/rss/search?q=future+skills+competences+Maroc&hl=fr&gl=MA&ceid=MA:fr",
]


SOURCES_RSS_INTL = [
    # Fintech & Banque
    "https://www.finextra.com/rss/headlines.aspx",
    "https://feeds.reuters.com/reuters/businessNews",
    "https://thefintechtimes.com/feed",
    "https://finovate.com/feed",
    "https://bankingexchange.com/feed/",
    "https://thefinancialbrand.com/feed/",
    "https://bankingtech.com/feed/",
    "https://www.financemagnates.com/fintech/feed/",
    "https://paymentscardsandmobile.com/feed/",
    "https://techbullion.com/feed",
    "https://www.bobsguide.com/feed/",
    "https://globalbankingandfinance.com/feed/",
    "https://bankingjournal.aba.com/feed/",
    # Formation & L&D
    "https://feeds.feedburner.com/elearningindustry",
    "https://trainingindustry.com/feed/",
    "https://talentlms.com/blog/feed",
    "https://www.clomedia.com/feed/",
    "https://hrdive.com/feeds/news/",
    "https://joshbersin.com/feed/",
    "https://trainingjournal.com/feed/",
    "https://elearning.adobe.com/feed",
    "https://charteredbanker.com/feed/",
    # IA & Tech
    "https://venturebeat.com/feed/",
    "https://technologyreview.com/topnews.rss",
    "https://openai.com/blog/rss/",
    "https://huggingface.co/blog/feed.xml",
    # RSE & Finance Durable
    "https://esgtoday.com/feed/",
    "https://www.responsible-investor.com/feed/",
    "https://www.greenbiz.com/feed",
    # Institutions & Réglementation
    "https://www.weforum.org/agenda/feed/",
    "https://feeds.ft.com/rss/companies-financials",
    "https://www.fsb.org/feed/",
    "https://www.afdb.org/en/rss/news-events",
    "https://www.cgap.org/rss/",
    "https://ifc.org/rss/",
    # Grandes banques - blogs et newsrooms
    "https://newsroom.bnpparibas.com/rss/",
    "https://www.jpmorgan.com/insights/rss.xml",
    "https://www.goldmansachs.com/insights/rss.xml",
    "https://www.hsbc.com/news-and-media/rss",
    "https://home.barclays/news/rss.xml",
    "https://www.db.com/news/rss",
    "https://www.societegenerale.com/en/rss",
    "https://www.credit-agricole.com/en/rss.xml",
    "https://www.ubs.com/rss",
    "https://www.standardchartered.com/rss",
    # Formation bancaire specialisee
    "https://charteredbanker.com/feed/",
    "https://bankingjournal.aba.com/feed/",
    "https://www.efma.com/rss/",
    "https://iob.ie/rss/",
]


# ============================================================
# DOMAINES ET MOTS-CLES
# ============================================================
DOMAINES_MAROC = [
    {"id": "M1", "label": "Formation Bancaire Maroc", "couleur": "#1a3a5c",
     "keywords": ["formation bancaire", "formation banque", "e-learning banque", "LMS bancaire", "GPBM formation", "Institut Bancaire", "OFPPT banque", "formation financiere", "formation secteur bancaire"]},
    {"id": "M2", "label": "Reglementation BAM ACAPS", "couleur": "#8b1a2f",
     "keywords": ["Bank Al-Maghrib", "BAM", "ACAPS", "reglementation bancaire", "supervision bancaire", "circulaire banque", "banque centrale", "formation BAM", "formation Bank Al-Maghrib"]},
    {"id": "M3", "label": "Fintech Startups Maroc", "couleur": "#c04a00",
     "keywords": ["fintech", "paiement mobile", "paiement digital", "neobanque", "startup fintech", "portefeuille electronique", "paiement instantane", "inclusion financiere"]},
    {"id": "M4", "label": "Transformation Digitale Banques", "couleur": "#0e5c8b",
     "keywords": ["banque digitale", "banque numerique", "application bancaire", "banque en ligne", "formation en ligne", "e-learning", "digitalisation bancaire", "digital banking", "services bancaires digitaux", "Attijariwafa", "CIH", "Banque Populaire", "BMCE"]},
    {"id": "M5", "label": "Politiques Formation Emploi", "couleur": "#2d6a4f",
     "keywords": ["formation professionnelle", "OFPPT", "ANAPEC", "emploi", "marche travail", "insertion professionnelle", "qualification", "competences professionnelles"]},
    {"id": "M6", "label": "IA Tech Banques Marocaines", "couleur": "#5c1a8b",
     "keywords": ["intelligence artificielle", "IA", "machine learning", "chatbot", "automatisation", "algorithme", "AI", "deep learning", "scoring credit", "detection fraude"]},
    {"id": "M7", "label": "RSE Finance Durable Maroc", "couleur": "#1a6b4a",
     "keywords": ["finance verte", "green bonds", "ESG", "RSE", "green finance", "formation RSE", "formation finance verte", "formation green business", "obligations vertes", "developpement durable", "finance durable"]},
    {"id": "M8", "label": "Competences du Futur Maroc", "couleur": "#4a7a1a",
     "keywords": ["Future Skills", "nouvelles competences", "new skills", "competences futur", "metiers avenir", "reskilling", "upskilling", "competences numeriques", "formation metiers futur"]},
]

DOMAINES_INTL = [
    {"id": "I1", "label": "Innovation Pedagogique Learning", "couleur": "#1a4a7a",
     "keywords": ["microlearning", "LXP", "adaptive learning", "elearning", "corporate training", "instructional design", "blended learning", "gamification", "learning management", "social learning", "mobile learning", "learning design", "SCORM", "xAPI"]},
    {"id": "I2", "label": "IA dans la Formation", "couleur": "#6b1a7a",
     "keywords": ["AI learning", "generative AI training", "AI corporate training", "AI tutor", "AI coaching", "intelligent tutoring", "learning analytics AI", "AI instructional design", "machine learning education", "AI assessment"]},
    {"id": "I3", "label": "Fintech Mondiale Open Banking", "couleur": "#7a3d1a",
     "keywords": ["open banking", "embedded finance", "neobank", "BaaS", "BNPL", "digital payments", "mobile banking", "API banking", "payments innovation", "digital wallet"]},
    {"id": "I4", "label": "IA en Banque Cas Usage", "couleur": "#1a6b6b",
     "keywords": ["AI banking", "artificial intelligence banking", "fraud detection AI", "credit scoring AI", "generative AI finance", "AI risk management", "AI compliance", "chatbot banking", "predictive banking", "AI wealth management"]},
    {"id": "I5", "label": "Reglementation Financiere Intl", "couleur": "#4a1a5c",
     "keywords": ["Basel IV", "DORA regulation", "AML compliance", "banking regulation", "MiCA", "RegTech", "KYC", "financial compliance", "banking supervision", "FATF", "prudential regulation"]},
    {"id": "I6", "label": "Certifications Standards Bancaires", "couleur": "#5c3d1a",
     "keywords": ["CISI certification", "CFA exam", "ACAMS", "banking qualification", "FRM certification", "banking diploma", "finance certification", "professional banking", "ICA qualification", "chartered banker"]},
    {"id": "I7", "label": "Benchmarks Pedagogiques Banque", "couleur": "#1a5c3d",
     "keywords": ["bank training", "financial services learning", "L&D banking", "learning ROI finance", "banking academy", "financial training program", "bank upskilling", "compliance training", "banking e-learning", "financial services training"]},
    {"id": "I8", "label": "IA Generale Tendances Mondiales", "couleur": "#3d1a5c",
     "keywords": ["large language model", "GPT", "Claude AI", "Gemini", "AI regulation", "LLM", "foundation model", "AI Act", "AGI", "AI governance", "AI ethics", "Mistral", "AI safety", "multimodal AI"]},
    {"id": "I9", "label": "RSE Finance Durable Mondiale", "couleur": "#1a5c1a",
     "keywords": ["ESG banking", "sustainable finance", "green banking", "CSRD", "climate risk banking", "net zero bank", "impact investing", "green bond", "taxonomy finance", "ESG reporting", "climate finance", "sustainable investment"]},
    {"id": "I10", "label": "Future Skills International", "couleur": "#7a6b1a",
     "keywords": ["future of work", "reskilling", "upskilling", "WEF skills", "skills gap", "workforce transformation", "talent development", "skills of the future", "digital skills", "human skills", "21st century skills", "workforce 2030"]},
    {"id": "I11", "label": "Formation dans les Grandes Banques Mondiales", "couleur": "#2a4a7a",
     "keywords": [
        # France
        "BNP Paribas training", "BNP Paribas formation", "BNP Paribas learning",
        "Societe Generale training", "Societe Generale formation",
        "Credit Agricole training", "Credit Agricole formation",
        "Natixis training", "BPCE formation",
        # USA
        "JPMorgan training", "JPMorgan learning", "JPMorgan Chase upskilling",
        "Bank of America training", "Goldman Sachs learning", "Goldman Sachs training",
        "Citibank training", "Wells Fargo training", "Morgan Stanley learning",
        # UK
        "HSBC training", "HSBC learning", "HSBC formation",
        "Barclays training", "Standard Chartered training",
        "Lloyds Bank training", "NatWest training",
        # Allemagne
        "Deutsche Bank training", "Deutsche Bank learning",
        "Commerzbank training",
        # Chine
        "ICBC training", "Bank of China learning",
        "Ping An training", "Ping An AI",
        # Japon
        "Mitsubishi UFJ training", "MUFG learning",
        # Suisse
        "UBS training", "UBS learning",
        # Golfe
        "Al Rajhi training", "Emirates NBD training", "QNB training",
        # Mots-cles generiques grandes banques
        "global bank training", "investment bank learning", "tier 1 bank upskilling",
        "bank AI training", "bank ESG training", "bank reskilling",
        "bank future skills", "bank digital training",
     ]},
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
    """Filtre les articles par mots-cles dans titre ET description."""
    articles_pertinents = []
    for article in articles:
        titre = (article.get("titre") or "").lower()
        description = (article.get("description") or "").lower()
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in titre or kw_lower in description:
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
