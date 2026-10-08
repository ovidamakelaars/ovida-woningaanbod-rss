import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from xml.dom import minidom
from html import escape

SOURCE_URL = "https://ovida.com/api./properties/available.json"
OUTPUT_FILE = "feed.xml"

# Ovida JSON ophalen
with urllib.request.urlopen(SOURCE_URL, timeout=30) as response:
    data = json.loads(response.read().decode("utf-8"))

# RSS opbouwen
rss = ET.Element("rss", {
    "version": "2.0",
    "xmlns:atom": "http://www.w3.org/2005/Atom"
})

channel = ET.SubElement(rss, "channel")

ET.SubElement(channel, "title").text = "Ovida Woningaanbod"
ET.SubElement(channel, "description").text = "Alle beschikbare woningen van Ovida"
ET.SubElement(channel, "link").text = "https://ovida.com/wonen/aanbod"

properties = data.get("objects", [])

for property in properties:
    object_code = str(property.get("object_code", ""))

    street = property.get("street_name", "")
    house_number = property.get("house_number", "")
    addition = property.get("house_number_addition") or ""
    place = property.get("place", "")
    
    address = f"{street} {house_number}{addition}".strip()
    title = f"{address} - {place}".strip(" -")

    item = ET.SubElement(channel, "item")

    ET.SubElement(item, "title").text = title

    property_url = property.get("url", "")
    ET.SubElement(item, "link").text = property_url

    # Unieke ID van de woning
    ET.SubElement(item, "guid", {
        "isPermaLink": "false"
    }).text = object_code

    # Publicatiedatum
    publish_date = property.get("publish_date") or property.get("created_at")

    if publish_date:
        try:
            dt = datetime.fromisoformat(publish_date)
            ET.SubElement(item, "pubDate").text = format_datetime(dt)
        except ValueError:
            pass

    # Prijs
    price = property.get("rent_price") or property.get("buy_price")

    if price:
        try:
            price_text = f"€ {float(price):,.0f}".replace(",", ".")
        except (ValueError, TypeError):
            price_text = str(price)
    else:
        price_text = "Op aanvraag"

    # Oppervlakte
    area = property.get("usable_area_living_function")

    if area:
        area_text = f"{area} m²"
    else:
        area_text = "Niet opgegeven"

    # Hoofdfoto
    main_images = property.get("realworks_main_images", [])
    image_url = ""

    if main_images:
        try:
            image_url = main_images[0]["sizes"][0]["imageUrl"]
        except (KeyError, IndexError, TypeError):
            image_url = ""

    if image_url:
        if image_url.startswith("/"):
            image_url = "https://ovida.com" + image_url

    # HTML-kaart voor de e-mail
    html = f"""
<table cellpadding="0" cellspacing="0" border="0"
       style="width:100%; max-width:760px; font-family:Arial,Helvetica,sans-serif;
              border:4px solid #162340; border-radius:8px; overflow:hidden;
              margin:0 0 20px 0;">
    <tr>
        <td style="width:42%; vertical-align:top;">
            <img src="{escape(image_url)}"
                 alt="{escape(title)}"
                 style="display:block; width:100%; height:190px; object-fit:cover;">
        </td>

        <td style="width:58%; vertical-align:top; padding:20px 22px;">
            <div style="font-size:20px; line-height:1.3; font-weight:bold;
                        color:#162340; margin-bottom:15px;">
                {escape(title)}
            </div>

            <div style="font-size:15px; line-height:1.7; color:#333333;">
                <strong>Prijs:</strong> {escape(price_text)}<br>
                <strong>Oppervlakte:</strong> {escape(area_text)}
            </div>

            <div style="margin-top:18px;">
                <a href="{escape(property_url)}"
                   style="display:inline-block; background:#f18700;
                          color:#ffffff; text-decoration:none;
                          font-weight:bold; font-size:14px;
                          padding:11px 18px; border-radius:5px;">
                    Bekijk woning
                </a>
            </div>
        </td>
    </tr>
</table>
"""

    ET.SubElement(item, "description").text = html

# XML netjes formatteren
xml_bytes = ET.tostring(rss, encoding="utf-8")

pretty_xml = minidom.parseString(xml_bytes).toprettyxml(
    indent="  ",
    encoding="utf-8"
)

Path(OUTPUT_FILE).write_bytes(pretty_xml)

print(f"RSS-feed gemaakt met {len(properties)} woningen.")
