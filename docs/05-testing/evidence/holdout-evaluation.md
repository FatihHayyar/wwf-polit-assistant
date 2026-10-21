# Klassifikation auf unabhängigen Prüfsets

**Klassifikator `rule-based-v8`.** Erzeugt mit `python -m scripts.evaluate_holdout`.

## Vorgehen

- **Stichproben:** je 300 zufällige Geschäfte in reproduzierbarer Zufallsreihenfolge (fester Seed), ohne Überschneidung mit dem Entwicklungsset und untereinander.
- **Annotation:** blind vor Einsicht in die Klassifikatorausgaben, anhand der Kategoriendefinitionen. Annotiert hat ein KI-Assistent, nicht WWF-Fachpersonen; die Labels sind eine nachvollziehbare Referenz, aber keine fachliche Abnahme.
- **Mehrdeutige Datensätze** (z. B. allgemeine Raumplanung, öV-Angebot, Lärm) zählen in der Relevanzmessung nicht und gelten als korrekt, solange die Zuordnung vertretbar ist.
- **Natürliche Verteilung:** Nur ein kleiner Teil der Geschäfte betrifft WWF-Themen; die Konfidenzintervalle (Wilson, 95 %) sind deshalb breit.
- **Reihenfolge:** Prüfset A wurde am 21. Oktober gezogen und hat `rule-based-v7` gemessen. Seine Fehlerliste floss in die Entwicklung von `rule-based-v8` ein; für v8 ist A deshalb **nicht mehr unabhängig**. Prüfset B wurde vor jeder Messung von v8 gezogen und annotiert und ist die massgebliche Messung für v8.

## Prüfset B (massgeblich für v8)

300 zufällige Geschäfte, gezogen am 2026-10-21 (ORDER BY md5(id || ':holdout-2026-10-22') (Seed-Zeichenkette), die ersten 300 Datensätze ohne Entwicklungsset und Prüfset A). Vor der Messung von v8 gezogen und annotiert.

| Kennzahl | Aktuelle Regeln (`rule-based-v8`) | Gespeichert beim Ziehen (`rule-based-v7`) |
|---|---:|---:|
| Datensätze streng korrekt | 282/300 | 271/300 |
| WWF-Relevanz: Precision (95 %-KI) | 1.0 (0.857–1.0) | 1.0 (0.772–1.0) |
| WWF-Relevanz: Recall (95 %-KI) | 0.639 (0.476–0.775) | 0.361 (0.225–0.524) |
| WWF-Relevanz: F1 | 0.78 | 0.53 |
| WWF-Relevanz: Accuracy | 0.95 | 0.911 |
| Hauptthemen: Precision (micro) | 0.885 | 0.75 |
| Hauptthemen: Recall (micro) | 0.605 | 0.316 |

Relevanzmatrix der aktuellen Regeln (259 eindeutige Datensätze): TP 23, FP 0, FN 13, TN 223. Mehrdeutige Datensätze: 41, davon 5 einem WWF-Thema zugeordnet.

| Hauptthema | TP | FP | FN | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| Biodiversität & Landschaft | 6 | 1 | 2 | 0.857 | 0.75 |
| Klima & Energie | 14 | 1 | 4 | 0.933 | 0.778 |
| Umwelt & Politik | 1 | 1 | 0 | 0.5 | 1.0 |
| Nachhaltige Wirtschaft & Konsum | 2 | 0 | 3 | 1.0 | 0.4 |

### Abweichungen der aktuellen Regeln in Prüfset B (massgeblich für v8)

| Geschäft | Titel | Zuordnung | Fehlend | Zusätzlich |
|---|---|---|---|---|
| 326757 | Produits locaux dans la restauration collective : un vœu pieux ? | other | food_consumption | other |
| 66906 | Tierschutz im Indonesien-Abkommen | species_habitats | – | species_habitats |
| 301751 | Protégeons nos réserves naturelles | other | protected_areas | other |
| 189493 | Non à un doublement des charges de chauffage : pour une tarification en matière de raccordement et de fournitu | other | renewable_heat | other |
| 201757 | Reduktion des Energieverbrauchs und der Lichtverschmutzung im Bereich der Strassenbeleuchtungen | biodiversity_landscape_other, environment_policy_other, public_sector | – | environment_policy_other |
| 20623 | Tarifpolitik bei ewb: Wo bleibt der ökologische Anreiz zum Wassersparen? | other | resources_raw_materials/waters | other |
| 312282 | Aktion zur Förderung von Elektrotaxis in Basel-Stadt | other | sustainable_mobility | other |
| 57415 | Auswirkungen des Freihandelsabkommens zwischen der Schweiz und China auf das Ökosystem des Hochplateaus von Ti | climate_energy_other | biodiversity_landscape_other/international_environment/species_habitats | climate_energy_other |
| 129872 | Nachtabschaltung der Strassenbeleuchtung | other | biodiversity_landscape_other/building_efficiency/climate_energy_other/public_sector | other |
| 172564 | Gesetz betreffend die Änderung des Gesetzes über die Energienutzung | other | climate_energy_other | other |
| 46873 | Ein Schattendach mit Begrünung | other | biodiversity_landscape_other/climate_energy_other | other |
| 87096 | Fischtreppe in Evionnaz: Wie ist der Stand der Dinge? | other | waters | other |
| 100263 | Energierichtplan | other | climate_energy_other | other |
| 106419 | Vom 7. April 2025, Verordnung zum ökologischen Ausgleich bei Bauvorhaben | other | biodiversity_landscape_other/environmental_law/soil_spatial_planning/species_habitats | other |
| 160133 | Regenwasser. Eine nachhaltige Ressource | other | resources_raw_materials/waters | other |
| 32063 | Favorisons le développement circulaire du tissu associatif et économique en Ville de Genève | other | circular_economy | other |
| 256381 | Bau des Munitionsdepots Brugg im kantonalen Naturschutzgebiet und Schutz der letzten Laubfrosch-Population an  | protected_areas | species_habitats | – |
| 258460 | Rückzug aus Investitionen in fossile Energien | fossil_energy | sustainable_finance | – |

### Erstmessung auf Prüfset B

Die erste Messung von v8 auf B ist unverändert in `holdout_v8_first_measurement.json` gespeichert: TP 24, FP 0, FN 12, TN 223, Precision 1.0 (0.862–1.0), Recall 0.667 (0.503–0.798), F1 0.8. Danach wurde eine Fehlerursache korrigiert, die auch ausserhalb von B auftrat (öffentliche Akteure wurden aus Vorstosstexten gelesen und verdrängten das Klima-Auffangthema). Die Werte oben enthalten diese Korrektur; da sie B gesehen hat, ist die Erstmessung die unabhängige Schätzung.

## Prüfset A (für v8 nicht mehr unabhängig)

300 zufällige Geschäfte, gezogen am 2026-10-21 (ORDER BY md5(id || ':holdout-2026-10-21') (Seed-Zeichenkette), die ersten 300 Datensätze ohne die 50 Entwicklungsbeispiele). Unabhängige Messung von v7; für v8 nur noch Entwicklungsdaten.

| Kennzahl | Aktuelle Regeln (`rule-based-v8`) | Gespeichert beim Ziehen (`rule-based-v7`) |
|---|---:|---:|
| Datensätze streng korrekt | 280/300 | 268/300 |
| WWF-Relevanz: Precision (95 %-KI) | 0.9 (0.744–0.965) | 1.0 (0.772–1.0) |
| WWF-Relevanz: Recall (95 %-KI) | 0.675 (0.52–0.799) | 0.325 (0.201–0.48) |
| WWF-Relevanz: F1 | 0.771 | 0.491 |
| WWF-Relevanz: Accuracy | 0.94 | 0.899 |
| Hauptthemen: Precision (micro) | 0.806 | 0.786 |
| Hauptthemen: Recall (micro) | 0.625 | 0.268 |

Relevanzmatrix der aktuellen Regeln (267 eindeutige Datensätze): TP 27, FP 3, FN 13, TN 224. Mehrdeutige Datensätze: 33, davon 1 einem WWF-Thema zugeordnet.

| Hauptthema | TP | FP | FN | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| Biodiversität & Landschaft | 6 | 1 | 4 | 0.857 | 0.6 |
| Klima & Energie | 11 | 4 | 5 | 0.733 | 0.688 |
| Umwelt & Politik | 6 | 0 | 0 | 1.0 | 1.0 |
| Nachhaltige Wirtschaft & Konsum | 2 | 1 | 1 | 0.667 | 0.667 |

### Abweichungen der aktuellen Regeln in Prüfset A (für v8 nicht mehr unabhängig)

| Geschäft | Titel | Zuordnung | Fehlend | Zusätzlich |
|---|---|---|---|---|
| 153693 | Einheimische Pflanzen | other | species_habitats | other |
| 210213 | Menschenrechtsdialog mit dem Präsidenten Aserbeidschans | fossil_energy | other | fossil_energy |
| 282827 | Abschaffung Eigenmietwert - Abzüge für energiesparende und umweltschonende Massnahmen erhalten | climate_energy_other, environment_policy_other | building_efficiency | climate_energy_other, environment_policy_other |
| 126608 | Förderung der Biodiversität bei Verkehrsprojekten, Gebäudesanierungen und Areal-Entwicklungen | biodiversity_landscape_other, building_efficiency | – | building_efficiency |
| 161502 | Bekämpfung der Verkehrsüberlastung. Die für den (abgelehnten) Autobahnausbau vorgesehen Milliarden für Projekt | circular_economy | sustainable_mobility | circular_economy |
| 298366 | Zu Fuss zur Schule statt “Elterntaxi“ | other | sustainable_mobility | other |
| 14862 | Die Bekämpfung des Japankäfers und die Folgen für Riehen und die Region | other | agriculture_biodiversity/biodiversity_landscape_other/species_habitats | other |
| 210825 | Entwicklungszusammenarbeit und MSC-Zertifizierung. Unterstützung lokaler Fischer | other | companies_supply_chains/food_consumption/international_environment/sustainable_economy_consumption_other/waters | other |
| 267553 | Einzelinitiative Dr. Marianne Klug Arter, Zürich, betreffend Änderung des Gesetzes über die Finanzierung von M | other | biodiversity_landscape_other/environmental_funding/environmental_law/protected_areas | other |
| 52318 | Ersatzbeiträge für die Befreiung vom Bau von Schutzräumen | climate_energy_other | other | climate_energy_other |
| 334039 | Energie aus Fluss- und Trinkwasser | waters | climate_energy_other/renewable_electricity/renewable_heat | waters |
| 188205 | Un Eco-quartier à la Concorde: favorisons une expérience innovatrice de logements à haute qualité environnemen | other | building_efficiency/climate_energy_other | other |
| 59926 | Minimaler Schutz der Wässermatten | other | agriculture_biodiversity/biodiversity_landscape_other/species_habitats/waters | other |
| 247092 | Papier- und Kartonsammlung durch Horwer Vereine | other | circular_economy | other |
| 338679 | Bilaterale III und Artikel 84 BV: Schutz des Alpengebiets vor zunehmendem individuellem Transitverkehr | other | environment_policy_other/environmental_law/sustainable_mobility | other |
| 75927 | Nachjagd/Herbstjagd | other | species_habitats | other |
| 157217 | Gezielte Kontrollen im öffentlichen Verkehr von Sans-Papiers durch die Zollverwaltung | sustainable_mobility | other | sustainable_mobility |
| 237397 | Ökologisierung der Verkehrssteuern | other | sustainable_mobility | other |
| 8447 | Kommunale Volksinitiative «für ein gesundes Stadtklima (Gute-Luft-Initiative)» | other | climate_energy_other/environment_policy_other | other |
| 41551 | Voruntersuchungen belasteter Standorte | other | environment_policy_other/environmental_law/soil_spatial_planning | other |

## Einordnung

Das Entwicklungsset (50/50) misst nur, ob die Regeln die Beispiele erfüllen, an denen sie verbessert wurden. Prüfsets schätzen die Qualität auf ungesehenen Daten. Sie dürfen nicht zum Anpassen der Regeln verwendet werden; nach Regeländerungen wird ein neues Prüfset gezogen. Eine Bewertung durch WWF-Fachpersonen bleibt notwendig.
