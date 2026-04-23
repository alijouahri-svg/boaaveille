"""
VEILLE STRATEGIQUE — Script Python pour GitHub Actions (v4 - definitive)
3 appels API : Maroc (8) + International partie 1 (5) + partie 2 (5)
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
MODELE              = "claude-sonnet-4-6"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
log = logging.getLogger(__name__)

COULEURS = {
    "M1":"#1a3a5c","M2":"#8b1a2f","M3":"#c04a00","M4":"#0e5c8b",
    "M5":"#2d6a4f","M6":"#5c1a8b","M7":"#1a6b4a","M8":"#4a7a1a",
    "I1":"#1a4a7a","I2":"#6b1a7a","I3":"#7a3d1a","I4":"#1a6b6b",
    "I5":"#4a1a5c","I6":"#5c3d1a","I7":"#1a5c3d","I8":"#3d1a5c",
    "I9":"#1a5c1a","I10":"#7a6b1a",
}

# ============================================================
# APPEL API
# ============================================================
def appeler_claude(client, prompt):
    message = client.messages.create(
        model=MODELE,
        max_tokens=5000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    debut = raw.find("{")
    fin = raw.rfind("}")
    if debut >= 0 and fin >= 0:
        raw = raw[debut:fin+1]
    return json.loads(raw)

# ============================================================
# PROMPT MAROC
# ============================================================
def prompt_maroc(date):
    return f"""Tu es un analyste en veille strategique bancaire au Maroc. Date : {date}

Genere un rapport JSON sur ces 8 domaines. Pour chaque domaine : 2 actualites.
Reponds UNIQUEMENT avec le JSON brut, sans backticks ni texte autour.

{{
  "resume": "Resume executif Maroc en 2 phrases",
  "signal": "Tendance principale en 1 phrase",
  "chiffre": "Un chiffre cle avec contexte",
  "vigilance": "Un risque a surveiller",
  "domaines": [
    {{
      "id": "M1", "label": "Formation Bancaire Maroc",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }},
    {{
      "id": "M2", "label": "Reglementation BAM et ACAPS",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }},
    {{
      "id": "M3", "label": "Fintech et Startups Maroc",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }},
    {{
      "id": "M4", "label": "Transformation Digitale Banques",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }},
    {{
      "id": "M5", "label": "Politiques Formation et Emploi",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }},
    {{
      "id": "M6", "label": "IA et Tech Banques Marocaines",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }},
    {{
      "id": "M7", "label": "RSE et Finance Durable Maroc",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }},
    {{
      "id": "M8", "label": "Competences du Futur Maroc",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }}
  ]
}}

Remplace chaque valeur entre guillemets par le vrai contenu. Garde exactement cette structure JSON."""

# ============================================================
# PROMPT INTERNATIONAL PARTIE 1 (I1 a I5)
# ============================================================
def prompt_intl1(date):
    return f"""Tu es un analyste en veille strategique internationale, expert en banque, formation et IA. Date : {date}

Genere un rapport JSON sur ces 5 domaines internationaux. Pour chaque domaine : 2 actualites.
Reponds UNIQUEMENT avec le JSON brut, sans backticks ni texte autour.

{{
  "domaines": [
    {{
      "id": "I1", "label": "Innovation Pedagogique et Learning",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }},
    {{
      "id": "I2", "label": "IA dans la Formation",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }},
    {{
      "id": "I3", "label": "Fintech Mondiale et Open Banking",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }},
    {{
      "id": "I4", "label": "IA en Banque Cas Usage",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }},
    {{
      "id": "I5", "label": "Reglementation Financiere Internationale",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }}
  ]
}}

Remplace chaque valeur entre guillemets par le vrai contenu. Garde exactement cette structure JSON."""

# ============================================================
# PROMPT INTERNATIONAL PARTIE 2 (I6 a I10)
# ============================================================
def prompt_intl2(date):
    return f"""Tu es un analyste en veille strategique internationale, expert en banque, formation et IA. Date : {date}

Genere un rapport JSON sur ces 5 domaines internationaux. Pour chaque domaine : 2 actualites.
Inclus aussi les sections analyse et actions.
Reponds UNIQUEMENT avec le JSON brut, sans backticks ni texte autour.

{{
  "convergences": "2 phrases sur les liens entre tendances Maroc et International",
  "opportunites": ["Opportunite concrete 1 pour le responsable formation", "Opportunite concrete 2"],
  "actions": ["Action prioritaire a faire cette semaine", "Action 2", "Action 3"],
  "agenda": "Evenements ou publications importants a venir cette semaine",
  "domaines": [
    {{
      "id": "I6", "label": "Certifications et Standards Bancaires",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }},
    {{
      "id": "I7", "label": "Benchmarks Pedagogiques Banque",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }},
    {{
      "id": "I8", "label": "IA Generale Tendances Mondiales",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }},
    {{
      "id": "I9", "label": "RSE et Finance Durable Mondiale",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }},
    {{
      "id": "I10", "label": "Future Skills International",
      "actualites": [
        {{"titre": "titre1", "source": "source1", "resume": "resume1", "analyse": "analyse1", "implication": "implication1"}},
        {{"titre": "titre2", "source": "source2", "resume": "resume2", "analyse": "analyse2", "implication": "implication2"}}
      ]
    }}
  ]
}}

Remplace chaque valeur entre guillemets par le vrai contenu. Garde exactement cette structure JSON."""

# ============================================================
# GENERATION HTML
# ============================================================
def domain_html(domaine):
    color = COULEURS.get(domaine.get("id", ""), "#1a3a5c")
    actus = ""
    for i, a in enumerate(domaine.get("actualites", [])):
        sep = "border-top:1px solid #ede8e0;padding-top:12px;margin-top:12px;" if i > 0 else ""
        actus += f"""
        <div style="{sep}">
          <table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td style="font-family:Georgia,serif;font-size:13px;font-weight:700;color:#1a1a1a;line-height:1.4;">{a.get('titre','')}</td>
            <td width="120" align="right" valign="top"><span style="font-size:10px;background:#f0ece4;color:#888;padding:2px 6px;">{a.get('source','')}</span></td>
          </tr></table>
          <p style="font-size:12px;color:#555;line-height:1.65;margin:7px 0;">{a.get('resume','')}</p>
          <p style="font-size:12px;color:#333;line-height:1.6;margin:0 0 7px;"><span style="color:{color};font-weight:700;">Analyse : </span>{a.get('analyse','')}</p>
          <div style="padding:6px 10px;background:{color}18;border-left:3px solid {color};font-size:11px;color:#444;">-> {a.get('implication','')}</div>
        </div>"""
    return f"""
    <div style="margin-bottom:12px;background:white;box-shadow:0 1px 4px rgba(0,0,0,0.07);">
      <div style="background:{color};padding:9px 15px;">
        <span style="font-size:10px;color:rgba(255,255,255,0.65);letter-spacing:1.5px;text-transform:uppercase;">{domaine.get('id','')} </span>
        <span style="font-family:Georgia,serif;font-size:14px;font-weight:700;color:white;">{domaine.get('label','')}</span>
      </div>
      <div style="padding:14px 16px;">{actus}</div>
    </div>"""


def build_email_html(date, maroc, intl1, intl2):
    maroc_html  = "".join(domain_html(d) for d in maroc.get("domaines", []))
    intl1_html  = "".join(domain_html(d) for d in intl1.get("domaines", []))
    intl2_html  = "".join(domain_html(d) for d in intl2.get("domaines", []))
    opps        = "".join(f'<div style="font-size:12px;color:#333;margin-bottom:6px;"><span style="color:#c8a96e;font-weight:700;">-> </span>{o}</div>' for o in intl2.get("opportunites", []))
    actions     = "".join(f'<div style="font-size:12px;color:#333;margin-bottom:6px;">[] {a}</div>' for a in intl2.get("actions", []))
    agenda_html = f'<div style="background:#0f2540;color:white;padding:10px 15px;margin-bottom:12px;"><span style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#c8a96e;font-weight:600;">Agenda : </span><span style="font-size:11px;color:rgba(255,255,255,0.8);">{intl2.get("agenda","")}</span></div>' if intl2.get("agenda") else ""

    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f7f4ef;font-family:Arial,sans-serif;">
<div style="max-width:680px;margin:0 auto;">

  <div style="background:#0f2540;padding:22px 28px;">
    <div style="font-family:Georgia,serif;font-size:26px;font-weight:900;color:white;">VEILLE STRATEGIQUE</div>
    <div style="font-family:Georgia,serif;font-size:18px;font-weight:700;color:#c8a96e;">Rapport Quotidien</div>
    <div style="font-size:10px;color:rgba(255,255,255,0.45);margin-top:6px;text-transform:uppercase;letter-spacing:2px;">Banque · Formation · IA · RSE · Maroc et Monde</div>
    <div style="font-size:12px;color:#c8a96e;margin-top:5px;font-weight:600;">{date}</div>
  </div>

  <div style="padding:20px 28px;">

    <div style="background:#0f2540;padding:18px 22px;margin-bottom:14px;">
      <div style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:#c8a96e;margin-bottom:9px;font-weight:600;">Resume Executif Maroc</div>
      <p style="font-family:Georgia,serif;font-size:14px;line-height:1.75;color:rgba(255,255,255,0.92);margin:0;">{maroc.get("resume","")}</p>
    </div>

    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:14px;"><tr>
      <td width="33%" style="padding-right:5px;vertical-align:top;"><div style="background:white;padding:12px 14px;border-top:3px solid #c8a96e;">
        <div style="font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:#aaa;margin-bottom:5px;">Signal Fort</div>
        <div style="font-family:Georgia,serif;font-size:11px;font-weight:700;color:#c8a96e;line-height:1.4;">{maroc.get("signal","")}</div>
      </div></td>
      <td width="33%" style="padding:0 3px;vertical-align:top;"><div style="background:white;padding:12px 14px;border-top:3px solid #1a3a5c;">
        <div style="font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:#aaa;margin-bottom:5px;">Chiffre Cle</div>
        <div style="font-family:Georgia,serif;font-size:11px;font-weight:700;color:#1a3a5c;line-height:1.4;">{maroc.get("chiffre","")}</div>
      </div></td>
      <td width="33%" style="padding-left:5px;vertical-align:top;"><div style="background:white;padding:12px 14px;border-top:3px solid #8b1a2f;">
        <div style="font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:#aaa;margin-bottom:5px;">A Surveiller</div>
        <div style="font-family:Georgia,serif;font-size:11px;font-weight:700;color:#8b1a2f;line-height:1.4;">{maroc.get("vigilance","")}</div>
      </div></td>
    </tr></table>

    <div style="text-align:center;padding:8px 0 14px;border-bottom:2px solid #0f2540;margin-bottom:14px;">
      <span style="font-family:Georgia,serif;font-size:17px;font-weight:900;color:#0f2540;">VEILLE MAROC</span>
    </div>
    {maroc_html}

    <div style="text-align:center;padding:8px 0 14px;border-bottom:2px solid #0f2540;margin:14px 0;">
      <span style="font-family:Georgia,serif;font-size:17px;font-weight:900;color:#0f2540;">VEILLE INTERNATIONALE</span>
    </div>
    {intl1_html}
    {intl2_html}

    <div style="text-align:center;padding:8px 0 14px;border-bottom:2px solid #c8a96e;margin:14px 0;">
      <span style="font-family:Georgia,serif;font-size:17px;font-weight:900;color:#c8a96e;">ANALYSE ET ACTIONS</span>
    </div>

    <div style="background:white;padding:16px 18px;margin-bottom:12px;border-top:3px solid #0f2540;">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:2px;color:#aaa;margin-bottom:8px;">Convergences Maroc x International</div>
      <p style="font-family:Georgia,serif;font-size:12px;line-height:1.7;color:#333;font-style:italic;margin:0;">{intl2.get("convergences","")}</p>
    </div>

    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;"><tr>
      <td width="49%" style="padding-right:6px;vertical-align:top;">
        <div style="background:white;padding:14px 16px;border-top:3px solid #c8a96e;">
          <div style="font-size:9px;text-transform:uppercase;letter-spacing:2px;color:#aaa;margin-bottom:8px;">Opportunites Detectees</div>
          {opps}
        </div>
      </td>
      <td width="49%" style="padding-left:6px;vertical-align:top;">
        <div style="background:#f0f7ff;padding:14px 16px;border-left:4px solid #1a3a5c;">
          <div style="font-size:9px;text-transform:uppercase;letter-spacing:2px;color:#1a3a5c;margin-bottom:8px;">Actions Cette Semaine</div>
          {actions}
        </div>
      </td>
    </tr></table>

    {agenda_html}

    <div style="border-top:2px solid #0f2540;padding-top:12px;">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td style="font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:1.5px;">Veille Strategique · {date}</td>
        <td align="right" style="font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:1.5px;">18 domaines · 36 actualites · Confidentiel</td>
      </tr></table>
    </div>

  </div>
</div>
</body></html>"""


# ============================================================
# ENVOI EMAIL
# ============================================================
def envoyer_email(date, maroc, intl1, intl2):
    html = build_email_html(date, maroc, intl1, intl2)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Veille Strategique - {date}"
    msg["From"]    = f"Veille Strategique <{EMAIL_EXPEDITEUR}>"
    msg["To"]      = ", ".join(EMAIL_DESTINATAIRES)
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_EXPEDITEUR, EMAIL_MOT_DE_PASSE)
        server.sendmail(EMAIL_EXPEDITEUR, EMAIL_DESTINATAIRES, msg.as_string())
    log.info(f"Email envoye a {len(EMAIL_DESTINATAIRES)} destinataire(s)")


# ============================================================
# MAIN
# ============================================================
def main():
    date = datetime.now().strftime("%A %d %B %Y")
    log.info(f"Demarrage veille du {date}")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    log.info("Appel 1/3 - Veille Maroc...")
    maroc = appeler_claude(client, prompt_maroc(date))
    log.info(f"Maroc OK - {len(maroc.get('domaines', []))} domaines")

    log.info("Appel 2/3 - Veille Internationale partie 1 (I1-I5)...")
    intl1 = appeler_claude(client, prompt_intl1(date))
    log.info(f"International 1 OK - {len(intl1.get('domaines', []))} domaines")

    log.info("Appel 3/3 - Veille Internationale partie 2 (I6-I10)...")
    intl2 = appeler_claude(client, prompt_intl2(date))
    log.info(f"International 2 OK - {len(intl2.get('domaines', []))} domaines")

    log.info("Envoi email...")
    envoyer_email(date, maroc, intl1, intl2)
    log.info("Veille terminee avec succes !")


if __name__ == "__main__":
    main()
