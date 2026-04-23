"""
VEILLE STRATEGIQUE - Version finale definitive
3 appels HTML assembles : Maroc + International + Analyse
Zero JSON, zero parsing, zero erreur
"""

import os
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
log = logging.getLogger(__name__)


def appeler_claude(client, prompt):
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generer_maroc(client, date):
    prompt = f"""Tu es un analyste expert en veille strategique bancaire au Maroc. Date : {date}

Genere UNIQUEMENT des blocs HTML pour ces 8 domaines marocains, 2 actualites chacun.
Reponds avec le HTML brut uniquement, sans texte avant ou apres.

Pour chaque domaine, utilise exactement ce format HTML (remplace les crochets par le vrai contenu) :

<div style="margin-bottom:14px;background:white;box-shadow:0 1px 4px rgba(0,0,0,0.07);">
  <div style="background:COULEUR;padding:10px 16px;">
    <span style="font-family:Georgia,serif;font-size:14px;font-weight:700;color:white;">ID - LABEL</span>
  </div>
  <div style="padding:14px 16px;">
    <div style="margin-bottom:14px;">
      <strong style="font-size:13px;color:#1a1a1a;">TITRE 1</strong>
      <span style="font-size:10px;color:#888;margin-left:8px;">SOURCE</span>
      <p style="font-size:12px;color:#555;margin:6px 0;">RESUME EN 2 PHRASES</p>
      <p style="font-size:12px;color:#333;margin:0 0 6px;"><strong style="color:COULEUR;">Analyse : </strong>ANALYSE EN 1 PHRASE</p>
      <div style="padding:6px 10px;border-left:3px solid COULEUR;font-size:11px;color:#444;">IMPLICATION CONCRETE</div>
    </div>
    <div style="border-top:1px solid #ede8e0;padding-top:14px;">
      <strong style="font-size:13px;color:#1a1a1a;">TITRE 2</strong>
      <span style="font-size:10px;color:#888;margin-left:8px;">SOURCE</span>
      <p style="font-size:12px;color:#555;margin:6px 0;">RESUME EN 2 PHRASES</p>
      <p style="font-size:12px;color:#333;margin:0 0 6px;"><strong style="color:COULEUR;">Analyse : </strong>ANALYSE EN 1 PHRASE</p>
      <div style="padding:6px 10px;border-left:3px solid COULEUR;font-size:11px;color:#444;">IMPLICATION CONCRETE</div>
    </div>
  </div>
</div>

Domaines et couleurs :
M1 Formation Bancaire Maroc = #1a3a5c
M2 Reglementation BAM et ACAPS = #8b1a2f
M3 Fintech et Startups Maroc = #c04a00
M4 Transformation Digitale Banques = #0e5c8b
M5 Politiques Formation et Emploi = #2d6a4f
M6 IA et Tech Banques Marocaines = #5c1a8b
M7 RSE et Finance Durable Maroc = #1a6b4a
M8 Competences du Futur Maroc = #4a7a1a"""

    return appeler_claude(client, prompt)


def generer_international(client, date):
    prompt = f"""Tu es un analyste expert en veille strategique internationale, banque, formation et IA. Date : {date}

Genere UNIQUEMENT des blocs HTML pour ces 10 domaines internationaux, 2 actualites chacun.
Reponds avec le HTML brut uniquement, sans texte avant ou apres.

Pour chaque domaine, utilise exactement ce format HTML (remplace les crochets par le vrai contenu) :

<div style="margin-bottom:14px;background:white;box-shadow:0 1px 4px rgba(0,0,0,0.07);">
  <div style="background:COULEUR;padding:10px 16px;">
    <span style="font-family:Georgia,serif;font-size:14px;font-weight:700;color:white;">ID - LABEL</span>
  </div>
  <div style="padding:14px 16px;">
    <div style="margin-bottom:14px;">
      <strong style="font-size:13px;color:#1a1a1a;">TITRE 1</strong>
      <span style="font-size:10px;color:#888;margin-left:8px;">SOURCE</span>
      <p style="font-size:12px;color:#555;margin:6px 0;">RESUME EN 2 PHRASES</p>
      <p style="font-size:12px;color:#333;margin:0 0 6px;"><strong style="color:COULEUR;">Analyse : </strong>ANALYSE EN 1 PHRASE</p>
      <div style="padding:6px 10px;border-left:3px solid COULEUR;font-size:11px;color:#444;">IMPLICATION CONCRETE</div>
    </div>
    <div style="border-top:1px solid #ede8e0;padding-top:14px;">
      <strong style="font-size:13px;color:#1a1a1a;">TITRE 2</strong>
      <span style="font-size:10px;color:#888;margin-left:8px;">SOURCE</span>
      <p style="font-size:12px;color:#555;margin:6px 0;">RESUME EN 2 PHRASES</p>
      <p style="font-size:12px;color:#333;margin:0 0 6px;"><strong style="color:COULEUR;">Analyse : </strong>ANALYSE EN 1 PHRASE</p>
      <div style="padding:6px 10px;border-left:3px solid COULEUR;font-size:11px;color:#444;">IMPLICATION CONCRETE</div>
    </div>
  </div>
</div>

Domaines et couleurs :
I1 Innovation Pedagogique et Learning = #1a4a7a
I2 IA dans la Formation = #6b1a7a
I3 Fintech Mondiale et Open Banking = #7a3d1a
I4 IA en Banque Cas Usage = #1a6b6b
I5 Reglementation Financiere Internationale = #4a1a5c
I6 Certifications et Standards Bancaires = #5c3d1a
I7 Benchmarks Pedagogiques Banque = #1a5c3d
I8 IA Generale Tendances Mondiales = #3d1a5c
I9 RSE et Finance Durable Mondiale = #1a5c1a
I10 Future Skills International = #7a6b1a"""

    return appeler_claude(client, prompt)


def generer_analyse(client, date):
    prompt = f"""Tu es un analyste expert en veille strategique bancaire et formation. Date : {date}

Genere UNIQUEMENT ce bloc HTML avec de vrais contenus analytiques (remplace tous les crochets).
Reponds avec le HTML brut uniquement, sans texte avant ou apres.

<div style="background:white;padding:16px 18px;margin-bottom:12px;border-top:3px solid #0f2540;">
  <div style="font-size:9px;text-transform:uppercase;letter-spacing:2px;color:#aaa;margin-bottom:8px;">Convergences Maroc x International</div>
  <p style="font-family:Georgia,serif;font-size:13px;line-height:1.7;color:#333;font-style:italic;margin:0;">[2 phrases analytiques sur les liens entre tendances Maroc et International cette semaine]</p>
</div>
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;"><tr>
  <td width="49%" style="padding-right:6px;vertical-align:top;">
    <div style="background:white;padding:14px 16px;border-top:3px solid #c8a96e;">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:2px;color:#aaa;margin-bottom:8px;">Opportunites Detectees</div>
      <div style="font-size:12px;color:#333;margin-bottom:6px;"><span style="color:#c8a96e;font-weight:700;">-> </span>[Opportunite 1 concrete pour responsable formation]</div>
      <div style="font-size:12px;color:#333;"><span style="color:#c8a96e;font-weight:700;">-> </span>[Opportunite 2 concrete]</div>
    </div>
  </td>
  <td width="49%" style="padding-left:6px;vertical-align:top;">
    <div style="background:#f0f7ff;padding:14px 16px;border-left:4px solid #1a3a5c;">
      <div style="font-size:9px;text-transform:uppercase;letter-spacing:2px;color:#1a3a5c;margin-bottom:8px;">Actions Cette Semaine</div>
      <div style="font-size:12px;color:#333;margin-bottom:5px;">[] [Action prioritaire 1]</div>
      <div style="font-size:12px;color:#333;margin-bottom:5px;">[] [Action 2]</div>
      <div style="font-size:12px;color:#333;">[] [Action 3]</div>
    </div>
  </td>
</tr></table>
<div style="background:#0f2540;color:white;padding:10px 15px;">
  <span style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#c8a96e;font-weight:600;">Agenda : </span>
  <span style="font-size:11px;color:rgba(255,255,255,0.8);">[Evenements ou publications importants a venir cette semaine]</span>
</div>"""

    return appeler_claude(client, prompt)


def assembler_email(date, bloc_maroc, bloc_intl, bloc_analyse):
    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f7f4ef;font-family:Arial,sans-serif;">
<div style="max-width:680px;margin:0 auto;">

  <div style="background:#0f2540;padding:22px 28px;">
    <div style="font-family:Georgia,serif;font-size:26px;font-weight:900;color:white;">VEILLE STRATEGIQUE</div>
    <div style="font-family:Georgia,serif;font-size:18px;font-weight:700;color:#c8a96e;">Rapport Quotidien</div>
    <div style="font-size:10px;color:rgba(255,255,255,0.45);margin-top:6px;text-transform:uppercase;letter-spacing:2px;">Banque - Formation - IA - RSE - Maroc et Monde</div>
    <div style="font-size:12px;color:#c8a96e;margin-top:5px;font-weight:600;">{date}</div>
  </div>

  <div style="padding:20px 28px;">

    <div style="text-align:center;padding:8px 0 14px;border-bottom:2px solid #0f2540;margin-bottom:16px;">
      <span style="font-family:Georgia,serif;font-size:17px;font-weight:900;color:#0f2540;">VEILLE MAROC</span>
    </div>
    {bloc_maroc}

    <div style="text-align:center;padding:8px 0 14px;border-bottom:2px solid #0f2540;margin:16px 0;">
      <span style="font-family:Georgia,serif;font-size:17px;font-weight:900;color:#0f2540;">VEILLE INTERNATIONALE</span>
    </div>
    {bloc_intl}

    <div style="text-align:center;padding:8px 0 14px;border-bottom:2px solid #c8a96e;margin:16px 0;">
      <span style="font-family:Georgia,serif;font-size:17px;font-weight:900;color:#c8a96e;">ANALYSE ET ACTIONS</span>
    </div>
    {bloc_analyse}

    <div style="border-top:2px solid #0f2540;padding-top:12px;margin-top:16px;">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td style="font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:1.5px;">Veille Strategique - {date}</td>
        <td align="right" style="font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:1.5px;">18 domaines - 36 actualites - Confidentiel</td>
      </tr></table>
    </div>

  </div>
</div>
</body>
</html>"""


def envoyer_email(date, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Veille Strategique - {date}"
    msg["From"]    = f"Veille Strategique <{EMAIL_EXPEDITEUR}>"
    msg["To"]      = ", ".join(EMAIL_DESTINATAIRES)
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_EXPEDITEUR, EMAIL_MOT_DE_PASSE)
        server.sendmail(EMAIL_EXPEDITEUR, EMAIL_DESTINATAIRES, msg.as_string())
    log.info(f"Email envoye a {len(EMAIL_DESTINATAIRES)} destinataire(s)")


def main():
    date = datetime.now().strftime("%A %d %B %Y")
    log.info(f"Demarrage veille du {date}")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    log.info("Appel 1/3 - Veille Maroc...")
    bloc_maroc = generer_maroc(client, date)
    log.info("Maroc OK")

    log.info("Appel 2/3 - Veille Internationale...")
    bloc_intl = generer_international(client, date)
    log.info("International OK")

    log.info("Appel 3/3 - Analyse et Actions...")
    bloc_analyse = generer_analyse(client, date)
    log.info("Analyse OK")

    log.info("Assemblage et envoi...")
    html = assembler_email(date, bloc_maroc, bloc_intl, bloc_analyse)
    envoyer_email(date, html)
    log.info("Veille terminee avec succes !")


if __name__ == "__main__":
    main()
