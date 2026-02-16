from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime, timedelta
import qrcode
import random
from faker import Faker


class DocumentFactory:
    TIPI = ["verbale", "satellite", "planimetria", "permesso", "ordinanza", "comunicazione"]
    SCENARI = ["conforme", "violazione_leggera", "violazione_grave", "ricorso"]

    def __init__(self):
        self.faker = Faker("it_IT")

    def create(self, tipo: str, scenario: str, building_address: str, building_id: str, custom_data: dict = None) -> bytes:
        """Crea un documento PDF realistico in base a tipo e scenario."""
        if tipo not in self.TIPI:
            tipo = "verbale"
        if scenario not in self.SCENARI:
            scenario = "conforme"

        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
        story = []

        # Intestazione Comune
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=16,
            textColor=colors.HexColor("#003399"),
            spaceAfter=10,
            alignment=1,  # CENTER
        )

        story.append(Paragraph("COMUNE - UFFICIO PIANIFICAZIONE", title_style))
        story.append(Paragraph("Provincia di Cagliari", styles["Normal"]))
        story.append(Spacer(1, 0.5*cm))

        # Tipo documento
        story.append(Paragraph(f"<b>{tipo.upper()}</b>", styles["Heading2"]))
        story.append(Spacer(1, 0.3*cm))

        # Dati documento
        now = datetime.now()
        if tipo == "permesso":
            data_doc = now - timedelta(days=random.randint(30, 1000))
            scadenza = data_doc + timedelta(days=1825)
        elif tipo == "verbale":
            data_doc = now - timedelta(days=random.randint(0, 60))
        else:
            data_doc = now - timedelta(days=random.randint(0, 180))

        num_protocollo = f"{tipo.upper()}-{now.year}-{random.randint(1000, 9999)}"
        
        info_table = [
            ["Protocollo:", num_protocollo],
            ["Data:", data_doc.strftime("%d/%m/%Y")],
            ["Edificio:", building_address],
        ]
        
        info_style = TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e6f0ff")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ])
        
        info_tbl = Table(info_table, colWidths=[3*cm, 10*cm])
        info_tbl.setStyle(info_style)
        story.append(info_tbl)
        story.append(Spacer(1, 0.5*cm))

        # Contenuto specifico per tipo
        if tipo == "verbale":
            story.extend(self._verbale_content(scenario, building_address))
        elif tipo == "satellite":
            story.extend(self._satellite_content(scenario, data_doc))
        elif tipo == "planimetria":
            story.extend(self._planimetria_content(scenario, building_id))
        elif tipo == "permesso":
            story.extend(self._permesso_content(scenario, num_protocollo, data_doc, scadenza))
        elif tipo == "ordinanza":
            story.extend(self._ordinanza_content(scenario, building_address))
        elif tipo == "comunicazione":
            story.extend(self._comunicazione_content(scenario, building_address))

        story.append(Spacer(1, 0.5*cm))

        # QR code finto
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(f"insightpa://doc/{num_protocollo}")
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Converti QR a formato PNG
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        from reportlab.platypus import Image as RLImage
        qr_rl = RLImage(qr_buffer, width=2*cm, height=2*cm)
        story.append(qr_rl)

        # Firma digitale finta
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f"Sottoscritto digitalmente il {now.strftime('%d/%m/%Y %H:%M')} da sistema", styles["Normal"]))

        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    def _verbale_content(self, scenario: str, building_address: str):
        styles = getSampleStyleSheet()
        content = []
        
        content.append(Paragraph("<b>Oggetto:</b>", styles["Normal"]))
        if scenario == "conforme":
            content.append(Paragraph("Verifica conformità edificio - Esito CONFORME", styles["Normal"]))
            content.append(Spacer(1, 0.2*cm))
            content.append(Paragraph(f"In data odierna è stato effettuato sopralluogo presso {building_address}. "
                                     "L'edificio risulta conforme alle norme edilizie vigenti. "
                                     "Non sono state riscontrate anomalie o abusi.", styles["Normal"]))
        elif scenario == "violazione_leggera":
            content.append(Paragraph("Verifica conformità edificio - Esito CRITICITÀ MINORE", styles["Normal"]))
            content.append(Spacer(1, 0.2*cm))
            content.append(Paragraph(f"In data odierna è stato effettuato sopralluogo presso {building_address}. "
                                     "Sono state riscontrate piccole difformità: pergolato non autorizzato, "
                                     "piccola veranda in parziale contrasto con permesso originario.", styles["Normal"]))
        elif scenario == "violazione_grave":
            content.append(Paragraph("Verifica conformità edificio - Esito VIOLAZIONE", styles["Normal"]))
            content.append(Spacer(1, 0.2*cm))
            content.append(Paragraph(f"In data odierna è stato effettuato sopralluogo presso {building_address}. "
                                     "Sono state riscontrate gravi anomalie: piscina realizzata senza permesso, "
                                     "veranda in violazione vincolo costiero, ampliamento non autorizzato.", styles["Normal"]))
        else:  # ricorso
            content.append(Paragraph("Verbale di Ricorso - Richiesta Sanatoria", styles["Normal"]))
            content.append(Spacer(1, 0.2*cm))
            content.append(Paragraph(f"Ricorso relativo a verbale precedente per {building_address}. "
                                     "Richiedente ha prodotto documentazione integrativa. "
                                     "Verbale in corso di revisione.", styles["Normal"]))
        
        content.append(Spacer(1, 0.3*cm))
        return content

    def _satellite_content(self, scenario: str, data_doc: datetime):
        styles = getSampleStyleSheet()
        content = []
        
        content.append(Paragraph("<b>Analisi satellite - Change Detection</b>", styles["Normal"]))
        content.append(Spacer(1, 0.2*cm))
        
        if scenario in ["violazione_leggera", "violazione_grave"]:
            change_pct = random.randint(22, 80) if scenario == "violazione_grave" else random.randint(15, 25)
            content.append(Paragraph(f"Confidenza rilevamento: {change_pct}%", styles["Normal"]))
            content.append(Paragraph(f"Data immagine precedente: {(data_doc - timedelta(days=60)).strftime('%d/%m/%Y')}", styles["Normal"]))
            content.append(Paragraph(f"Data immagine attuale: {data_doc.strftime('%d/%m/%Y')}", styles["Normal"]))
            content.append(Paragraph("Variazioni rilevate: SI", styles["Normal"]))
        else:
            content.append(Paragraph(f"Confidenza rilevamento: {random.randint(5, 15)}%", styles["Normal"]))
            content.append(Paragraph("Variazioni rilevate: NO", styles["Normal"]))
        
        content.append(Spacer(1, 0.2*cm))
        return content

    def _planimetria_content(self, scenario: str, building_id: str):
        styles = getSampleStyleSheet()
        content = []
        
        content.append(Paragraph("<b>Planimetria Catastale</b>", styles["Normal"]))
        foglio = random.randint(1, 150)
        particella = random.randint(1, 500)
        sup_catastale = random.randint(100, 300)
        sup_reale = sup_catastale + (random.randint(10, 80) if scenario != "conforme" else random.randint(-5, 5))
        
        content.append(Paragraph(f"Foglio: {foglio}", styles["Normal"]))
        content.append(Paragraph(f"Particella: {particella}", styles["Normal"]))
        content.append(Paragraph(f"Categoria catastale: A/3", styles["Normal"]))
        content.append(Paragraph(f"Superficie catastale: {sup_catastale}m²", styles["Normal"]))
        content.append(Paragraph(f"Superficie rilevata: {sup_reale}m²", styles["Normal"]))
        if sup_reale > sup_catastale:
            content.append(Paragraph(f"<b>Differenza: +{sup_reale - sup_catastale}m² (NON AUTORIZZATA)</b>", styles["Normal"]))
        
        content.append(Spacer(1, 0.2*cm))
        return content

    def _permesso_content(self, scenario: str, num_prot: str, data_doc: datetime, scadenza: datetime):
        styles = getSampleStyleSheet()
        content = []
        
        content.append(Paragraph("<b>Permesso di Costruire</b>", styles["Normal"]))
        content.append(Spacer(1, 0.2*cm))
        content.append(Paragraph(f"Numero pratica: {num_prot}", styles["Normal"]))
        content.append(Paragraph(f"Data rilascio: {data_doc.strftime('%d/%m/%Y')}", styles["Normal"]))
        content.append(Paragraph(f"Data scadenza: {scadenza.strftime('%d/%m/%Y')}", styles["Normal"]))
        content.append(Paragraph(f"Oggetto: Nuova costruzione / Ristrutturazione", styles["Normal"]))
        content.append(Spacer(1, 0.2*cm))
        return content

    def _ordinanza_content(self, scenario: str, building_address: str):
        styles = getSampleStyleSheet()
        content = []
        
        content.append(Paragraph("<b>Ordinanza di Demolizione</b>", styles["Normal"]))
        content.append(Spacer(1, 0.2*cm))
        content.append(Paragraph(f"Riferimento: Art. 31 DPR 380/2001", styles["Normal"]))
        content.append(Paragraph(f"Edificio: {building_address}", styles["Normal"]))
        content.append(Paragraph("Motivi: Abuso edilizio - Costruzione non autorizzata", styles["Normal"]))
        content.append(Spacer(1, 0.2*cm))
        return content

    def _comunicazione_content(self, scenario: str, building_address: str):
        styles = getSampleStyleSheet()
        content = []
        
        content.append(Paragraph("<b>Comunicazione Amministrativa</b>", styles["Normal"]))
        content.append(Spacer(1, 0.2*cm))
        if scenario == "ricorso":
            content.append(Paragraph("Oggetto: Istanza di Sanatoria Art. 36 DPR 380/2001", styles["Normal"]))
        else:
            content.append(Paragraph("Oggetto: Diffida - Allertamento per violazione abusivismo", styles["Normal"]))
        content.append(Paragraph(f"Destinatario: {building_address}", styles["Normal"]))
        content.append(Spacer(1, 0.2*cm))
        return content


document_factory = DocumentFactory()
