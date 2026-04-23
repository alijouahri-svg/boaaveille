"""
VEILLE STRATEGIQUE - Version finale definitive
Claude genere directement le HTML - zero JSON, zero erreur possible
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


def generer_rapport_html(date):
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Tu es un analyste expert en veille strategique bancaire, formation et IA.
Date : {date}

Genere le code HTML complet d un email de veille strategique pour un Responsable Formation en banque au Maroc.

DOMAINES A COUVRIR (2 actualites par domaine) :
Maroc : M1-Formation Bancaire, M2-Reglementation BAM, M3-Fintech Maroc, M4-Transformation Digitale, M5-Formation Emploi, M6-IA Banques, M7-RSE Finance Durable, M8-Competences Futur
International : I1-Innovation Pedagogique, I2-IA Formation, I3-Fintech Open Banking, I4-IA Banque, I5-Reglementation, I6-Certifications, I7-Benchmarks, I8-IA Generale, I9-RSE Mondiale, I10-Future Skills

STRUCTURE HTML A PRODUIRE :
- Header bleu fonce (#0f2540) avec titre VEILLE STRATEGIQUE en blanc et date en dore (#c8a96e)
- Bloc resume executif fond bleu fonce, texte blanc
- 3 cartes : Signal Fort, Chiffre Cle, A Surveiller
- Section VEILLE MAROC avec les 8 domaines
- Section VEILLE INTERNATIONALE avec les 10 domaines
- Section ANALYSE ET ACTIONS : convergences, opportunites, actions semaine
- Footer : Veille Strategique - {date} - 18 domaines - 36 actualites - Confidentiel

STYLE :
- Fond general : #f7f4ef
- Header et blocs importants : #0f2540
- Accents dores : #c8a96e
- Chaque domaine a sa couleur de barre gauche
- Police Arial, emails compatibles
- Max width 680px centre

Pour chaque actualite, inclure : titre en gras, source, resume 2 phrases, analyse 1 phrase, implication concrete.

Reponds UNIQUEMENT avec le code HTML, en commencant directement par <!DOCTYPE html> et finissant par </html>. Aucun texte avant ou apres."""

    log.info("Appel API Claude - generation HTML...")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    html = message.content[0].text.strip()

    # Extraire uniquement le HTML si Claude a ajoute du texte autour
    debut = html.find("<!DOCTYPE")
    if debut < 0:
        debut = html.find("<html")
    if debut > 0:
        html = html[debut:]

    fin = html.rfind("</html>")
    if fin >= 0:
        html = html[:fin + 7]

    log.info(f"HTML genere - {len(html)} caracteres")
    return html


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

    html = generer_rapport_html(date)
    envoyer_email(date, html)

    log.info("Veille terminee avec succes !")


if __name__ == "__main__":
    main()
