"""
VEILLE STRATÉGIQUE — Script Python pour GitHub Actions (version corrigée)
2 appels API séparés : Maroc + International pour éviter la coupure JSON
"""

import os
import json
import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from anthropic import Anthropic

ANTHROPIC_API_KEY   = os.environ["ANTHROPIC_API_KEY"]
EMAIL_EXPEDITEUR    = os.environ["EMAIL_EXPEDITEUR"]
EMAIL_MOT_DE_PASSE  = os.environ["EMAIL_MOT_DE_PASSE"]
EMAIL_DESTINATAIRES = os.environ["EMAIL_DESTINATAIRES"].split(",")
MODELE              = "claude-haiku-4-5-20251001"

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(message)s")
log = logging.getLogger(__name__)

DOMAINES_MAROC = [
    {"id": "M1", "label": "Formation Bancaire Maroc",        "keywords": ["GPBM formation", "Institut Bancaire Marocain", "OFPPT banque"]},
    {"id": "M2", "label": "Réglementation BAM & ACAPS",      "keywords": ["Bank Al-Maghrib circulaire", "ACAPS réglementation", "conformité bancaire Maroc"]},
    {"id": "M3", "label": "Fintech & Startups Maroc",        "keywords": ["fintech Maroc", "startup financière Maroc", "mobile payment Maroc"]},
    {"id": "M4", "label": "Transformation Digitale Banques", "keywords": ["Attijariwafa digital", "CIH Bank innovation", "néobanque Maroc"]},
    {"id": "M5", "label": "Politiques Formation & Emploi",   "keywords": ["OFPPT Maroc", "formation continue Maroc", "Anapec emploi"]},
    {"id": "M6", "label": "IA & Tech Banques Marocaines",    "keywords": ["intelligence artificielle banque Maroc", "chatbot banque Maroc"]},
    {"id": "M7", "label": "RSE & Finance Durable Maroc",     "keywords": ["finance verte Maroc", "ESG banque Maroc", "green bonds Maroc"]},
    {"id": "M8", "label": "Compétences du Futur Maroc",      "keywords": ["future skills Maroc", "compétences 2030 Maroc", "reskilling Maroc"]},
]

DOMAINES_INTL = [
    {"id": "I1",  "label": "Innovation Pédagogique & Learning", "keywords": ["microlearning corporate", "adaptive learning LXP"]},
    {"id": "I2",  "label": "IA dans la Formation",              "keywords": ["AI in learning", "generative AI training"]},
    {"id": "I3",  "label": "Fintech Mondiale & Open Banking",   "keywords": ["open banking international", "embedded finance"]},
    {"id": "I4",  "label": "IA en Banque — Cas d'Usage",        "keywords": ["AI banking use cases", "fraud detection AI"]},
    {"id": "I5",  "label": "Réglementation Financière Intl",    "keywords": ["Bâle IV", "DORA digital resilience", "AML compliance"]},
    {"id": "I6",  "label": "Certifications & Standards",        "keywords": ["CISI certification", "CFA banking", "ACAMS"]},
    {"id": "I7",  "label": "Benchmarks Pédagogiques Banque",    "keywords": ["bank training best practices", "learning ROI"]},
    {"id": "I8",  "label": "IA Générale — Tendances Mondiales", "keywords": ["large language models", "AI Act Europe", "AGI"]},
    {"id": "I9",  "label": "RSE & Finance Durable Mondiale",    "keywords": ["ESG investing", "sustainable banking", "CSRD"]},
    {"id": "I10", "label": "Future Skills — International",     "keywords": ["future of work WEF", "skills 2030", "reskilling global"]},
]

COULEURS = {
    "M1":"#1a3a5c","M2":"#8b1a2f","M3":"#c04a00","M4":"#0e5c8b",
    "M5":"#2d6a4f","M6":"#5c1a8b","M7":"#1a6b4a","M8":"#4a7a1a",
    "I1":"#1a4a7a","I2":"#6b1a7a","I3":"#7a3d1a","I4":"#1a6b6b",
    "I5":"#4a1a5c","I6":"#5c3d1a","I7":"#1a5c3d","I8":"#3d1a5c",
    "I9":"#1a5c1a","I10":"#7a6b1a",
}

# ============================================================
# PROMPT — Version courte pour éviter la coupure JSON
# ============================================================
def build_prompt_maroc(date):
    domaines_str = "\n".join(f"{d['id']} — {d['label']}: {', '.join(d['keywords'])}" for d in DOMAINES_MAROC)
    return f"""Tu es un analyste en veille stratégique bancaire au Maroc. Date : {date}

DOMAINES :
{domaines_str}

Pour chaque domaine, donne 2 actualités courtes et percutantes.
Réponds UNIQUEMENT en JSON valide strict sans backticks :
{{
  "resume": "2 phrases sur les tendances Maroc du jour",
  "signal": "1 phrase — tendance principale",
  "chiffre": "1 chiffre clé avec contexte",
  "vigilance": "1 risque à surveiller",
  "domaines": [
    {{
      "id": "M1",
      "label": "Formation Bancaire Maroc",
      "actualites": [
        {{"titre": "Titre court", "source": "Source", "resume": "2 phrases max", "analyse": "1 phrase analytique", "implication": "Impact concret"}},
        {{"titre": "Titre court", "source": "Source", "resume": "2 phrases max", "analyse": "1 phrase analytique", "implication": "Impact concret"}}
      ]
    }}
  ]
}}"""

def build_prompt_intl(date):
    domaines_str = "\n".join(f"{d['id']} — {d['label']}: {', '.join(d['keywords'])}" for d in DOMAINES_INTL)
    return f"""Tu es un analyste en veille stratégique internationale, expert en banque, formation et IA. Date : {date}

DOMAINES :
{domaines_str}

Pour chaque domaine, donne 2 actualités courtes et percutantes.
Réponds UNIQUEMENT en JSON valide strict sans backticks :
{{
  "convergences": "2 phrases sur les liens Maroc International",
  "opportunites": ["Opportunité 1", "Opportunité 2"],
  "actions": ["Action 1 cette semaine", "Action 2", "Action 3"],
  "agenda": "Événements à venir cette semaine",
  "domaines": [
    {{
      "id": "I1",
      "label": "Innovation Pédagogique",
      "actualites": [
        {{"titre": "Titre court", "source": "Source", "resume": "2 phrases max", "analyse": "1 phrase analytique", "implication": "Impact concret"}},
        {{"titre": "Titre court", "source": "Source", "resume": "2 phrases max", "analyse": "1 phrase analytique", "implication": "Impact concret"}}
      ]
    }}
  ]
}}"""

# ============================================================
# APPEL API — avec nettoyage JSON robuste
# ============================================================
def appeler_claude(client, prompt):
    message = client.messages.create(
        model=MODELE,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text
    raw = raw.replace("```json", "").replace("```", "").strip()
    idx = raw.find("{")
    if idx > 0:
        raw = raw[idx:]
    # Fermer le JSON si coupé
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Tentative de réparation basique
        raw = raw.rstrip(",\n ") + "]}}"
        try:
            return json.loads(raw)
        except:
            log.error("JSON non réparable")
            return {}

# ============================================================
# GÉNÉRATION HTML
# ============================================================
def domain_html(domaine):
    color = COULEURS.get(domaine.get("id", ""), "#1a3a5c")
    flag = "🇲🇦" if domaine.get("id", "").startswith("M") else "🌍"
    actus = ""
    for i, a in enumerate(domaine.get("actualites", [])):
        sep = "border-top:1px solid #ede8e0;padding-top:12px;margin-top:12px;" if i > 0 else ""
        actus += f"""
        <div style="{sep}">
          <table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td style="font-family:Georgia,serif;font-size:13px;font-weight:700;color:#1a1a1a;">{a.get('titre','')}</td>
            <td width="130" align="right"><span style="font-size:10px;background:#f0ece4;color:#888;padding:2px 6px;">{a.get('source','')}</span></td>
          </tr></table>
          <p style="font-size:12px;color:#555;line-height:1.6;margin:7px 0;">{a.get('resume','')}</p>
          <p style="font-size:12px;color:#333;margin:0 0 7px;"><span style="color:{color};font-weight:700;">Analyse · </span>{a.get('analyse','')}</p>
          <div style="padding:6px 10px;background:{color}18;border-left:3px solid {color};font-size:11px;color:#444;">→ {a.get('implication','')}</div>
        </div>"""
    return f"""
    <div style="margin-bottom:12px;background:white;box-shadow:0 1px 4px rgba(0,0,0,0.07);">
      <div style="background:{color};padding:9px 15px;">
        <span style="font-size:10px;color:rgba(255,255,255,0.65);letter-spacing:1.5px;text-transform:uppercase;">{domaine.get('id','')} </span>
        <span style="font-family:Georgia,serif;font-size:14px;font-weight:700;color:white;">{domaine.get('label','')}</span>
      </div>
      <div style="padding:14px 16px;">{actus}</div>
    </div>"""

def build_email_html(date, maroc, intl):
    maroc_html   = "".join(domain_html(d) for d in maroc.get("domaines", []))
    intl_html    = "".join(domain_html(d) for d in intl.get("domaines", []))
    opps         = "".join(f'<div style="font-size:12px;color:#333;margin-bottom:6px;"><span style="color:#c8a96e;font-weight:700;">→ </span>{o}</div>' for o in intl.get("opportunites", []))
    actions_html = "".join(f'<div style="font-size:12px;color:#333;margin-bottom:6px;">☐ {a}</div>' for a in intl.get("actions", []))

    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f7f4ef;font-family:Arial,sans-serif;">
<div style="max-width:680px;margin:0 auto;">

  <div style="background:#0f2540;padding:20px 26px;">
    <div style="font-family:Georgia,serif;font-size:24px;font-weight:900;color:white;">VEILLE STRATÉGIQUE</div>
    <div style="font-family:Georgia,serif;font-size:17px;color:#c8a96e;">Rapport Quotidien</div>
    <div style="font-size:10px;color:rgba(255,255,255,0.45);margin-top:5px;text-transform:uppercase;letter-spacing:2px;">Banque · Formation · IA · RSE · Maroc & Monde</div>
    <div style="font-size:11px;color:#c8a96e;margin-top:4px;font-weight:600;">{date}</div>
  </div>

  <div style="padding:18px 26px;">

    <div style="background:#0f2540;padding:16px 20px;margin-bottom:12px;">
      <div style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:#c8a96e;margin-bottom:7px;">Résumé Exécutif — Maroc</div>
      <p style="font-family:Georgia,serif;font-size:14px;line-height:1.7;color:rgba(255,255,255,0.9);margin:0;">{maroc.get('resume','')}</p>
    </div>

    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;"><tr>
      <td width="33%" style="padding-right:5px;vertical-align:top;"><div style="background:white;padding:11px 13px;border-top:3px solid #c8a96e;">
        <div style="font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:#aaa;margin-bottom:5px;">Signal Fort</div>
        <div style="font-family:Georgia,serif;font-size:11px;font-weight:700;color:#c8a96e;line-height:1.4;">{maroc.get('signal','')}</div>
      </div></td>
      <td width="33%" style="padding:0 3px;vertical-align:top;"><div style="background:white;padding:11px 13px;border-top:3px solid #1a3a5c;">
        <div style="font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:#aaa;margin-bottom:5px;">Chiffre Clé</div>
        <div style="font-family:Georgia,serif;font-size:11px;font-weight:700;color:#1a3a5c;line-height:1.4;">{maroc.get('chiffre','')}</div>
      </div></td>
      <td width="33%" style="padding-left:5px;vertical-align:top;"><div style="background:white;padding:11px 13px;border-top:3px solid #8b1a2f;">
        <div style="font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:#aaa;margin-bottom:5px;">À Surveiller</div>
        <div style="font-family:Georgia,serif;font-size:11px;font-weight:700;color:#8b1a2f;line-height:1.4;">{maroc.get('vigilance','')}</div>
      </div></td>
    </tr></table>

    <div style="text-align:center;padding:8px 0 12px;"><span style="font-family:Georgia,serif;font-size:16px;font-weight:900;color:#0f2540;">🇲🇦 VEILLE MAROC</span></div>
    {maroc_html}

    <div style="text-align:center;padding:8px 0 12px;margin-top:6px;"><span style="font-family:Georgia,serif;font-size:16px;font-weight:900;color:#0f2540;">🌍 VEILLE INTERNATIONALE</span></div>
    {intl_html}

    <div style="text-align:center;padding:8px 0 12px;margin-top:6px;"><span style="font-family:Georgia,serif;font-size:16px;font-weight:900;color:#c8a96e;">ANALYSE & ACTIONS</span></div>

    <div style="background:white;padding:14px 16px;margin-bottom:10px;border-top:3px solid #0f2540;">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:2px;color:#aaa;margin-bottom:7px;">Convergences Maroc × International</div>
      <p style="font-family:Georgia,serif;font-size:12px;line-height:1.7;color:#333;font-style:italic;margin:0;">{intl.get('convergences','')}</p>
    </div>

    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:10px;"><tr>
      <td width="49%" style="padding-right:5px;vertical-align:top;">
        <div style="background:white;padding:13px 15px;border-top:3px solid #c8a96e;">
          <div style="font-size:9px;text-transform:uppercase;letter-spacing:2px;color:#aaa;margin-bottom:7px;">Opportunités</div>
          {opps}
        </div>
      </td>
      <td width="49%" style="padding-left:5px;vertical-align:top;">
        <div style="background:#f0f7ff;padding:13px 15px;border-left:4px solid #1a3a5c;">
          <div style="font-size:9px;text-transform:uppercase;letter-spacing:2px;color:#1a3a5c;margin-bottom:7px;">☐ Actions Cette Semaine</div>
          {actions_html}
        </div>
      </td>
    </tr></table>

    {f'<div style="background:#0f2540;color:white;padding:10px 15px;margin-bottom:12px;"><span style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#c8a96e;">📅 Agenda · </span><span style="font-size:11px;color:rgba(255,255,255,0.8);">{intl.get("agenda","")}</span></div>' if intl.get("agenda") else ""}

    <div style="border-top:2px solid #0f2540;padding-top:10px;">
      <table width="100%"><tr>
        <td style="font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:1px;">Veille Stratégique · {date}</td>
        <td align="right" style="font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:1px;">18 domaines · 36 actualités · Confidentiel</td>
      </tr></table>
    </div>

  </div>
</div>
</body></html>"""

# ============================================================
# ENVOI EMAIL
# ============================================================
def envoyer_email(date, maroc, intl):
    html = build_email_html(date, maroc, intl)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔍 Veille Stratégique — {date}"
    msg["From"]    = f"Veille Stratégique <{EMAIL_EXPEDITEUR}>"
    msg["To"]      = ", ".join(EMAIL_DESTINATAIRES)
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_EXPEDITEUR, EMAIL_MOT_DE_PASSE)
        server.sendmail(EMAIL_EXPEDITEUR, EMAIL_DESTINATAIRES, msg.as_string())
    log.info(f"✅ Email envoyé à {len(EMAIL_DESTINATAIRES)} destinataire(s)")

# ============================================================
# MAIN
# ============================================================
def main():
    date = datetime.now().strftime("%A %d %B %Y")
    log.info(f"🚀 Démarrage veille du {date}")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    log.info("🇲🇦 Appel API — Veille Maroc...")
    maroc = appeler_claude(client, build_prompt_maroc(date))
    log.info(f"✅ Maroc OK — {len(maroc.get('domaines', []))} domaines")

    log.info("🌍 Appel API — Veille Internationale...")
    intl = appeler_claude(client, build_prompt_intl(date))
    log.info(f"✅ International OK — {len(intl.get('domaines', []))} domaines")

    log.info("📧 Envoi email...")
    envoyer_email(date, maroc, intl)
    log.info("🎉 Veille terminée avec succès !")

if __name__ == "__main__":
    main()
