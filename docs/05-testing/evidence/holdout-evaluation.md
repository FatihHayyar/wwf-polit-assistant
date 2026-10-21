# Klassifikation auf einem unabhängigen Prüfset

**Stand: 2026-10-21, Klassifikator `rule-based-v7`.** Erzeugt mit `python -m scripts.evaluate_holdout`.

## Vorgehen

- **Stichprobe:** 300 zufällige Geschäfte aus 326'499 Geschäften (reproduzierbare Zufallsreihenfolge über einen festen Seed)' ohne die 50 Entwicklungsbeispiele.
- **Annotation:** blind vor Einsicht in die Klassifikatorausgaben, anhand der Kategoriendefinitionen der Taxonomie. Annotiert hat ein KI-Assistent, nicht WWF-Fachpersonen; die Labels sind deshalb eine nachvollziehbare Referenz, aber keine fachliche Abnahme.
- **Mehrdeutige Datensätze** (z. B. allgemeine Raumplanung, öV-Angebot, Lärm) zählen in der Relevanzmessung nicht und gelten als korrekt, solange die Zuordnung vertretbar ist.
- Die Stichprobe ist natürlich verteilt: Nur ein kleiner Teil der Geschäfte betrifft WWF-Themen. Die Zahl der positiven Fälle ist deshalb klein, und die Konfidenzintervalle sind entsprechend breit.

## Ergebnisse

| Kennzahl | Aktuelle Regeln | Produktion (gespeichert) |
|---|---:|---:|
| Datensätze streng korrekt | 268/300 | 268/300 |
| WWF-Relevanz: Precision (95 %-KI) | 1.0 (0.772–1.0) | 1.0 (0.772–1.0) |
| WWF-Relevanz: Recall (95 %-KI) | 0.325 (0.201–0.48) | 0.325 (0.201–0.48) |
| WWF-Relevanz: F1 | 0.491 | 0.491 |
| WWF-Relevanz: Accuracy | 0.899 | 0.899 |
| Hauptthemen: Precision (micro) | 0.786 | 0.786 |
| Hauptthemen: Recall (micro) | 0.268 | 0.268 |

Relevanzmatrix (aktuelle Regeln, 267 eindeutige Datensätze): TP 13, FP 0, FN 27, TN 227. Mehrdeutige Datensätze: 33, davon 0 einem WWF-Thema zugeordnet.

| Hauptthema | TP | FP | FN | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| Biodiversität & Landschaft | 2 | 1 | 8 | 0.667 | 0.2 |
| Klima & Energie | 7 | 1 | 10 | 0.875 | 0.412 |
| Umwelt & Politik | 1 | 1 | 3 | 0.5 | 0.25 |
| Nachhaltige Wirtschaft & Konsum | 1 | 0 | 2 | 1.0 | 0.333 |

## Abweichungen

| Geschäft | Titel | Zuordnung | Fehlend | Zusätzlich |
|---|---|---|---|---|
| 153693 | Einheimische Pflanzen | other | species_habitats | other |
| 49840 | Strategische Rohölreserven im Ausland | soil_spatial_planning | fossil_energy | soil_spatial_planning |
| 282827 | Abschaffung Eigenmietwert - Abzüge für energiesparende und umweltschonende Massnahmen erhalten | environment_policy_other | building_efficiency | environment_policy_other |
| 27598 | "In periferia?!? ...c'è ENERGIA! Parco GeoTermico del nucleo di Sonvico." | other | renewable_heat | other |
| 126608 | Förderung der Biodiversität bei Verkehrsprojekten, Gebäudesanierungen und Areal-Entwicklungen | biodiversity_landscape_other, building_efficiency | – | building_efficiency |
| 161502 | Bekämpfung der Verkehrsüberlastung. Die für den (abgelehnten) Autobahnausbau vorgesehen Milliarden für Projekt | other | sustainable_mobility | other |
| 156704 | Ausführungsverordnung zum Jagdgesetz | other | species_habitats | other |
| 298366 | Zu Fuss zur Schule statt “Elterntaxi“ | other | sustainable_mobility | other |
| 14862 | Die Bekämpfung des Japankäfers und die Folgen für Riehen und die Region | other | agriculture_biodiversity/biodiversity_landscape_other/species_habitats | other |
| 210825 | Entwicklungszusammenarbeit und MSC-Zertifizierung. Unterstützung lokaler Fischer | other | companies_supply_chains/food_consumption/international_environment/sustainable_economy_consumption_other/waters | other |
| 267553 | Einzelinitiative Dr. Marianne Klug Arter, Zürich, betreffend Änderung des Gesetzes über die Finanzierung von M | other | biodiversity_landscape_other/environmental_funding/environmental_law/protected_areas | other |
| 142964 | Waldweiden | public_sector | forest | public_sector |
| 244702 | Compostage de déchets ménagers | other | circular_economy | other |
| 310094 | Waldentwicklungsplan WEP für das Waldareal der Gemeinden Basel, Bettingen und Riehen 2021-2035 | other | forest | other |
| 334039 | Energie aus Fluss- und Trinkwasser | other | climate_energy_other/renewable_electricity/renewable_heat | other |
| 215590 | Was genau sind besonders besorgniserregende Stoffe und wie viele davon sind in der Schweiz zugelassen? | other | environment_policy_other/environmental_law | other |
| 188205 | Un Eco-quartier à la Concorde: favorisons une expérience innovatrice de logements à haute qualité environnemen | other | building_efficiency/climate_energy_other | other |
| 247922 | Changement de système d'imposition de la propriété du logement : quelles conséquences pour la politique climat | other | climate_energy_other | other |
| 139104 | Persistente organische Schadstoffe (POPs-Konvention) | other | international_environment | other |
| 59926 | Minimaler Schutz der Wässermatten | other | agriculture_biodiversity/biodiversity_landscape_other/species_habitats/waters | other |
| 10592 | Umsetzung des Unterrichtsfachs «Mensch und Umwelt» an den Volksschulen | other | environmental_research_education | other |
| 247092 | Papier- und Kartonsammlung durch Horwer Vereine | other | circular_economy | other |
| 146725 | Infrastrukturen des öffentlichen Verkehrs auf Kantonsstrassen: Lange Umsetzungsfristen gefährden die Attraktiv | other | sustainable_mobility | other |
| 87327 | Ausserordentliche Lage – Wölfe bedrohen unsere Dörfer | other | species_habitats | other |
| 338679 | Bilaterale III und Artikel 84 BV: Schutz des Alpengebiets vor zunehmendem individuellem Transitverkehr | other | environment_policy_other/environmental_law/sustainable_mobility | other |
| 75927 | Nachjagd/Herbstjagd | other | species_habitats | other |
| 157227 | Wie wird das Konzept der planetaren Belastbarkeitsgrenzen in der Strategie Nachhaltige Entwicklung 2030 berück | climate_energy_other, resources_raw_materials | – | resources_raw_materials |
| 237397 | Ökologisierung der Verkehrssteuern | other | sustainable_mobility | other |
| 318154 | Galleria Mappo-Morettina; impatto ambientale ad un anno dalla sua apertura | other | environment_policy_other/environmental_law/sustainable_mobility | other |
| 8447 | Kommunale Volksinitiative «für ein gesundes Stadtklima (Gute-Luft-Initiative)» | other | climate_energy_other/environment_policy_other | other |
| 41551 | Voruntersuchungen belasteter Standorte | other | environment_policy_other/environmental_law/soil_spatial_planning | other |
| 117740 | "Lugano, eventi a basso impatto ambientale?" | other | circular_economy/environment_policy_other/sustainable_economy_consumption_other | other |

## Einordnung

Das Entwicklungsset (50/50) misst nur, ob die Regeln die Beispiele erfüllen, an denen sie verbessert wurden. Dieses Prüfset schätzt die Qualität auf ungesehenen Daten. Es darf nicht zum Anpassen der Regeln verwendet werden; nach Regeländerungen wird erneut gemessen und für weitere Optimierungen ein neues Prüfset gezogen. Eine Bewertung durch WWF-Fachpersonen bleibt notwendig.
