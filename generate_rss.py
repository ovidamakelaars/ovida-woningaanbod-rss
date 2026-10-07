import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from xml.dom import minidom

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

# De JSON bevat de woningen in 'objects'
properties = data.get("objects", [])

for property in properties:
    object_code = str(property.get("object_code", ""))

    street = property.get("street_name", "")
    house_number = property.get("house_number", "")
    addition = property.get("house_number_addition", "")
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

    # Beschrijving
    price = property.get("rent_price") or property.get("buy_price") or ""
    rooms = property.get("amount_of_rooms") or ""
    area = property.get("usable_area_living_function") or ""

    description = (
        f"Adres: {address}, {place}\n"
        f"Prijs: {price}\n"
        f"Kamers: {rooms}\n"
        f"Oppervlakte: {area} m²\n"
        f"Objectcode: {object_code}"
    )

    ET.SubElement(item, "description").text = description

# XML netjes formatteren
xml_bytes = ET.tostring(rss, encoding="utf-8")
pretty_xml = minidom.parseString(xml_bytes).toprettyxml(
    indent="  ",
    encoding="utf-8"
)

Path(OUTPUT_FILE).write_bytes(pretty_xml)

print(f"RSS-feed gemaakt met {len(properties)} woningen.")
