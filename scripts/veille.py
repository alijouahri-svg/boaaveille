"""
VEILLE STRATÉGIQUE — Script Python pour GitHub Actions
Formation Bancaire · IA · Fintech · RSE · Maroc & Monde
======================================================
INSTALLATION :
1. Créer un dépôt privé sur github.com
2. Placer ce fichier dans : scripts/veille.py
3. Placer le workflow dans : .github/workflows/veille.yml
4. Ajouter les secrets GitHub (voir README)
5. C'est parti — rapport chaque matin à 7h00 !
"""

import os
import json
import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from anthropic import Anthropic

# ============================================================
# CONFIGURATION — via variables d'environnement GitHub Secrets
# ============================================================
ANTHROPIC_API_KEY   = os.environ["ANTHROPIC_API_KEY"]
EMAIL_EXPEDITEUR    = os.environ["EMAIL_EXPEDITEUR"]      # votre-email@gmail.com
EMAIL_MOT_DE_PASSE  = os.environ["EMAIL_MOT_DE_PASSE"]    # Mot de passe app Gmail
EMAIL_DESTINATAIRES = os.environ["EMAIL_DESTINATAIRES"].split(",")  # email1,email2,email3
MODELE              = "claude-haiku-4-5-20251001"          # Gratuit ~0.05€/rapport

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(message)s")
log = logging.getLogger(__name__)

# ============================================================
# DOMAINES DE VEILLE — 18 DOMAINES
# ============================================================
DOMAINES_MAROC = [
    {"id": "M1",  "label": "Formation Bancaire Maroc",           "keywords": ["GPBM formation", "Institut Bancaire Marocain", "OFPPT banque", "formation professionnelle banque Maroc"]},
    {"id": "M2",  "label": "Réglementation BAM & ACAPS",         "keywords": ["Bank Al-Maghrib circulaire", "ACAPS réglementation", "conformité bancaire Maroc", "Bâle III Maroc"]},
    {"id": "M3",  "label": "Fintech & Startups Maroc",           "keywords": ["fintech Maroc", "startup financière Maroc", "CasaFinance City", "mobile payment Maroc"]},
    {"id": "M4",  "label": "Transformation Digitale Banques",    "keywords": ["Attijariwafa digital", "CIH Bank innovation", "néobanque Maroc", "transformation numérique banque"]},
    {"id": "M5",  "label": "Politiques Formation & Emploi",      "keywords": ["OFPPT Maroc", "formation continue Maroc", "Plan Maroc Compétences", "Anapec emploi"]},
    {"id": "M6",  "label": "IA & Tech Banques Marocaines",       "keywords": ["intelligence artificielle banque Maroc", "chatbot banque Maroc", "IA finance Maroc"]},
    {"id": "M7",  "label": "RSE & Finance Durable Maroc",        "keywords": ["finance verte Maroc", "green bonds Maroc", "ESG banque Maroc", "taxonomie verte BAM"]},
    {"id": "M8",  "label": "Compétences du Futur Maroc",         "keywords": ["future skills Maroc", "compétences 2030 Maroc", "métiers émergents banque", "reskilling Maroc"]},
]

DOMAINES_INTL = [
    {"id": "I1",  "label": "Innovation Pédagogique & Learning",  "keywords": ["microlearning corporate", "adaptive learning LXP", "learning experience platform"]},
    {"id": "I2",  "label": "IA dans la Formation",               "keywords": ["AI in learning", "generative AI training", "ChatGPT formation professionnelle"]},
    {"id": "I3",  "label": "Fintech Mondiale & Open Banking",    "keywords": ["open banking international", "embedded finance", "neobank global"]},
    {"id": "I4",  "label": "IA en Banque — Cas d'Usage",         "keywords": ["AI banking use cases", "fraud detection AI", "credit scoring machine learning"]},
    {"id": "I5",  "label": "Réglementation Financière Intl",     "keywords": ["Bâle IV", "DORA digital resilience", "MiCA crypto regulation", "AML compliance"]},
    {"id": "I6",  "label": "Certifications & Standards",         "keywords": ["CISI certification", "CFA banking", "ACAMS AML certification"]},
    {"id": "I7",  "label": "Benchmarks Pédagogiques Banque",     "keywords": ["bank training best practices", "financial services learning", "learning ROI"]},
    {"id": "I8",  "label": "IA Générale — Tendances Mondiales",  "keywords": ["large language models", "GPT Gemini Claude Mistral", "AI Act Europe", "AGI"]},
    {"id": "I9",  "label": "RSE & Finance Durable Mondiale",     "keywords": ["ESG investing", "green finance global", "sustainable banking", "CSRD"]},
    {"id": "I10", "label": "Future Skills — International",      "keywords": ["future of work WEF", "skills 2030", "workforce transformation", "reskilling global"]},
]

COULEURS = {
    "M1":"#1a3a5c","M2":"#8b1a2f","M3":"#c04a00","M4":"#0e5c8b",
    "M5":"#2d6a4f","M6":"#5c1a8b","M7":"#1a6b4a","M8":"#4a7a1a",
    "I1":"#1a4a7a","I2":"#6b1a7a","I3":"#7a3d1a","I4":"#1a6b6b",
    "I5":"#4a1a5c","I6":"#5c3d1a","I7":"#1a5c3d","I8":"#3d1a5c",
    "I9":"#1a5c1a","I10":"#7a6b1a",
}

# ============================================================
# PROMPT DE GÉNÉRATION
# ============================================================
def build_prompt(date: str) -> str:
    maroc_str = "\n".join(f"{d['id']} — {d['label']}: {', '.join(d['keywords'])}" for d in DOMAINES_MAROC)
    intl_str  = "\n".join(f"{d['id']} — {d['label']}: {', '.join(d['keywords'])}" for d in DOMAINES_INTL)

    return f"""Tu es un analyste senior en veille stratégique, expert en banque, formation professionnelle, fintech et IA. Tu travailles pour un Responsable Formation dans une banque marocaine. Ton analyse doit être analytique avec interprétation et implications concrètes.

Date : {date}

DOMAINES MAROC :
{maroc_str}

DOMAINES INTERNATIONAL :
{intl_str}

Pour chaque domaine, fournis 2 actualités récentes et significatives.

Réponds UNIQUEMENT en JSON valide strict, sans backticks, sans commentaires :
{{
  "date": "{date}",
  "resume_executif": "3-4 phrases analytiques",
  "signal_fort": "La tendance la plus importante en 1 phrase",
  "chiffre_cle": "Un chiffre marquant avec contexte",
  "a_surveiller": "Un risque ou opportunité émergente",
  "maroc": [
    {{
      "id": "M1",
      "label": "Formation Bancaire Maroc",
      "actualites": [
        {{"titre": "...", "source": "Source · Pays", "resume": "2-3 phrases", "analyse": "Interprétation", "implication": "Impact concret"}},
        {{"titre": "...", "source": "...", "resume": "...", "analyse": "...", "implication": "..."}}
      ]
    }}
  ],
  "international": [ ...même structure pour I1 à I10... ],
  "convergences": "Liens entre Maroc et International",
  "opportunites": ["Opportunité 1", "Opportunité 2"],
  "vigilance": ["Vigilance 1", "Vigilance 2"],
  "actions": ["Action 1", "Action 2", "Action 3"],
  "agenda": "Événements à venir"
}}"""


# ============================================================
# GÉNÉRATION DU RAPPORT HTML
# ============================================================
def build_email_html(rapport: dict) -> str:

    def domain_section(domaine: dict) -> str:
        color = COULEURS.get(domaine.get("id", ""), "#1a3a5c")
        actus_html = ""
        for i, a in enumerate(domaine.get("actualites", [])):
            border = "border-top:1px solid #ede8e0;padding-top:14px;margin-top:14px;" if i > 0 else ""
            actus_html += f"""
            <div style="{border}">
              <table width="100%" cellpadding="0" cellspacing="0"><tr>
                <td style="font-family:Georgia,serif;font-size:13px;font-weight:700;color:#1a1a1a;line-height:1.4;">{a.get('titre','')}</td>
                <td width="140" style="text-align:right;vertical-align:top;">
                  <span style="font-size:10px;background:#f0ece4;color:#888;padding:2px 6px;">{a.get('source','')}</span>
                </td>
              </tr></table>
              <p style="font-size:12px;color:#555;line-height:1.65;margin:8px 0;">{a.get('resume','')}</p>
              <p style="font-size:12px;color:#333;line-height:1.6;margin:0 0 8px;"><span style="color:{color};font-weight:700;">Analyse · </span>{a.get('analyse','')}</p>
              <div style="padding:7px 10px;background:{color}18;border-left:3px solid {color};font-size:11px;color:#444;">
                <span style="color:{color};font-weight:700;">→ </span>{a.get('implication','')}
              </div>
            </div>"""
        flag = "🇲🇦" if domaine.get("id","").startswith("M") else "🌍"
        return f"""
        <div style="margin-bottom:14px;background:white;box-shadow:0 1px 4px rgba(0,0,0,0.08);">
          <div style="background:{color};padding:10px 16px;">
            <span style="font-size:10px;font-weight:600;color:rgba(255,255,255,0.7);letter-spacing:1.5px;text-transform:uppercase;">{domaine.get('id','')} &nbsp;</span>
            <span style="font-family:Georgia,serif;font-size:14px;font-weight:700;color:white;">{domaine.get('label','')}</span>
          </div>
          <div style="padding:14px 16px;">{actus_html}</div>
        </div>"""

    maroc_html = "".join(domain_section(d) for d in rapport.get("maroc", []))
    intl_html  = "".join(domain_section(d) for d in rapport.get("international", []))

    opportunites_html = "".join(f'<div style="display:flex;gap:8px;margin-bottom:7px;font-size:12px;color:#333;"><span style="color:#c8a96e;font-weight:700;">→</span><span>{o}</span></div>' for o in rapport.get("opportunites", []))
    vigilance_html    = "".join(f'<div style="font-size:12px;color:#444;padding:5px 8px;border-left:3px solid #e05c00;margin-bottom:5px;">{v}</div>' for v in rapport.get("vigilance", []))
    actions_html      = "".join(f'<div style="display:flex;gap:8px;font-size:12px;color:#333;margin-bottom:7px;"><span style="display:inline-block;width:14px;height:14px;border:1.5px solid #1a3a5c;flex-shrink:0;margin-top:2px;"></span><span>{a}</span></div>' for a in rapport.get("actions", []))

    agenda_html = f'<div style="background:#0f2540;color:white;padding:10px 16px;margin-bottom:14px;"><span style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#c8a96e;font-weight:600;">📅 Agenda · </span><span style="font-size:12px;color:rgba(255,255,255,0.8);">{rapport.get("agenda","")}</span></div>' if rapport.get("agenda") else ""

    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f7f4ef;font-family:Arial,sans-serif;">
<div style="max-width:680px;margin:0 auto;">

  <div style="background:#0f2540;padding:22px 28px;">
    <div style="font-family:Georgia,serif;font-size:26px;font-weight:900;color:white;">VEILLE STRATÉGIQUE</div>
    <div style="font-family:Georgia,serif;font-size:18px;font-weight:700;color:#c8a96e;">Rapport Quotidien</div>
    <div style="font-size:10px;color:rgba(255,255,255,0.5);margin-top:6px;text-transform:uppercase;letter-spacing:2px;">Banque · Formation · IA · RSE · Maroc & Monde</div>
    <div style="font-size:11px;color:#c8a96e;margin-top:4px;font-weight:600;">{rapport.get('date','')}</div>
  </div>

  <div style="padding:20px 28px;">

    <div style="background:#0f2540;padding:18px 22px;margin-bottom:14px;">
      <div style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:#c8a96e;margin-bottom:8px;font-weight:600;">Résumé Exécutif</div>
      <p style="font-family:Georgia,serif;font-size:14px;line-height:1.75;color:rgba(255,255,255,0.9);margin:0;">{rapport.get('resume_executif','')}</p>
    </div>

    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:14px;"><tr>
      <td width="33%" style="padding-right:6px;"><div style="background:white;padding:12px 14px;border-top:3px solid #c8a96e;">
        <div style="font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:#aaa;margin-bottom:5px;">Signal Fort</div>
        <div style="font-family:Georgia,serif;font-size:11px;font-weight:700;color:#c8a96e;line-height:1.4;">{rapport.get('signal_fort','')}</div>
      </div></td>
      <td width="33%" style="padding:0 3px;"><div style="background:white;padding:12px 14px;border-top:3px solid #1a3a5c;">
        <div style="font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:#aaa;margin-bottom:5px;">Chiffre Clé</div>
        <div style="font-family:Georgia,serif;font-size:11px;font-weight:700;color:#1a3a5c;line-height:1.4;">{rapport.get('chiffre_cle','')}</div>
      </div></td>
      <td width="33%" style="padding-left:6px;"><div style="background:white;padding:12px 14px;border-top:3px solid #8b1a2f;">
        <div style="font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:#aaa;margin-bottom:5px;">À Surveiller</div>
        <div style="font-family:Georgia,serif;font-size:11px;font-weight:700;color:#8b1a2f;line-height:1.4;">{rapport.get('a_surveiller','')}</div>
      </div></td>
    </tr></table>

    <div style="text-align:center;padding:10px 0 14px;"><span style="font-family:Georgia,serif;font-size:17px;font-weight:900;color:#0f2540;">🇲🇦 VEILLE MAROC</span></div>
    {maroc_html}

    <div style="text-align:center;padding:10px 0 14px;margin-top:8px;"><span style="font-family:Georgia,serif;font-size:17px;font-weight:900;color:#0f2540;">🌍 VEILLE INTERNATIONALE</span></div>
    {intl_html}

    <div style="text-align:center;padding:10px 0 14px;margin-top:8px;"><span style="font-family:Georgia,serif;font-size:17px;font-weight:900;color:#c8a96e;">ANALYSE & ACTIONS</span></div>

    <div style="background:white;padding:16px 18px;margin-bottom:12px;border-top:3px solid #0f2540;">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:2px;color:#aaa;margin-bottom:8px;">Convergences Maroc × International</div>
      <p style="font-family:Georgia,serif;font-size:12px;line-height:1.7;color:#333;font-style:italic;margin:0;">{rapport.get('convergences','')}</p>
    </div>

    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;"><tr>
      <td width="49%" style="padding-right:6px;vertical-align:top;">
        <div style="background:white;padding:14px 16px;border-top:3px solid #c8a96e;">
          <div style="font-size:9px;text-transform:uppercase;letter-spacing:2px;color:#aaa;margin-bottom:8px;">Opportunités</div>
          {opportunites_html}
        </div>
      </td>
      <td width="49%" style="padding-left:6px;vertical-align:top;">
        <div style="background:#fff8f0;padding:14px 16px;border-left:4px solid #e05c00;">
          <div style="font-size:9px;text-transform:uppercase;letter-spacing:2px;color:#e05c00;margin-bottom:8px;">⚠ Vigilance</div>
          {vigilance_html}
        </div>
      </td>
    </tr></table>

    <div style="background:#f0f7ff;padding:14px 16px;border-left:4px solid #1a3a5c;margin-bottom:12px;">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:2px;color:#1a3a5c;margin-bottom:8px;">☐ Actions Cette Semaine</div>
      {actions_html}
    </div>

    {agenda_html}

    <div style="border-top:2px solid #0f2540;padding-top:10px;">
      <table width="100%"><tr>
        <td style="font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:1px;">Veille Stratégique · {rapport.get('date','')}</td>
        <td style="text-align:right;font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:1px;">18 domaines · 36 actualités · Confidentiel</td>
      </tr></table>
    </div>

  </div>
</div>
</body></html>"""


# ============================================================
# ENVOI EMAIL VIA GMAIL SMTP
# ============================================================
def envoyer_email(rapport: dict):
    html_corps = build_email_html(rapport)
    date_str   = rapport.get("date", datetime.now().strftime("%d/%m/%Y"))
    objet      = f"🔍 Veille Stratégique — {date_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = objet
    msg["From"]    = f"Veille Stratégique <{EMAIL_EXPEDITEUR}>"
    msg["To"]      = ", ".join(EMAIL_DESTINATAIRES)
    msg.attach(MIMEText(html_corps, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_EXPEDITEUR, EMAIL_MOT_DE_PASSE)
        server.sendmail(EMAIL_EXPEDITEUR, EMAIL_DESTINATAIRES, msg.as_string())

    log.info(f"✅ Email envoyé à {len(EMAIL_DESTINATAIRES)} destinataire(s)")


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================
def main():
    date = datetime.now().strftime("%A %d %B %Y")
    log.info(f"🚀 Démarrage veille du {date}")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    # Générer le rapport
    log.info("🤖 Appel API Claude...")
    message = client.messages.create(
        model=MODELE,
        max_tokens=8000,
        messages=[{"role": "user", "content": build_prompt(date)}],
    )

    raw_json = message.content[0].text
    raw_json = raw_json.replace("```json", "").replace("```", "").strip()
    first_brace = raw_json.index("{")
    if first_brace > 0:
        raw_json = raw_json[first_brace:]

    rapport = json.loads(raw_json)
    log.info(f"✅ Rapport généré — {len(rapport.get('maroc', []))} domaines Maroc, {len(rapport.get('international', []))} domaines International")

    # Envoyer l'email
    log.info("📧 Envoi email...")
    envoyer_email(rapport)
    log.info("🎉 Veille terminée avec succès !")


if __name__ == "__main__":
    main()
