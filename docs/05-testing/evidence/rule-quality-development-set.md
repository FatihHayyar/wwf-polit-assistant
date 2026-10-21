# Regelqualität auf dem Entwicklungsset

Frühere Regeln: 40/50; aktuelle Regeln: 50/50. Beide Versionen wurden mit denselben 50 Quelldatensätzen in getrennten temporären SQLite-Datenbanken geprüft; PostgreSQL wurde nicht verändert.

**Einschränkung:** Die Regeln wurden anhand dieser Beispiele verbessert. Das Ergebnis ist eine Regressionsprüfung und keine unverzerrte Qualitätsschätzung. Die Messung auf ungesehenen Daten steht in [holdout-evaluation.md](holdout-evaluation.md).

| Quelle | Titel | Erwartete Pflichtcodes | Aktuelle Zuordnung | Ergebnis |
|---|---|---|---|---|
| affairs:2160 | Photovoltaikanlage Schulanlage Spitz | renewable_electricity | renewable_electricity | korrekt |
| affairs:37526 | Stillstand bei der Windenergie-Nutzung im Kanton Bern? | renewable_electricity | renewable_electricity | korrekt |
| affairs:3895 | Mehr Transparenz bei der Energieeffizienz städtischer Liegenschaften | building_efficiency | building_efficiency | korrekt |
| affairs:8598 | Synergien nutzen bei der Bereitstellung von Ladeinfrastruktur für die E-Mobilität | sustainable_mobility | sustainable_mobility | korrekt |
| documents:68618 | Antrag Stadtrat - 2026.96W | renewable_heat | renewable_heat | korrekt |
| affairs:24891 | Betreffend Seglerschutz/Artenschutz | species_habitats | species_habitats | korrekt |
| affairs:1337 | Naturschutzgebiet Ruggeller Riet | protected_areas | protected_areas | korrekt |
| affairs:43542 | Waldreservate im Kanton Basel-Stadt | forest | forest | korrekt |
| affairs:271 | Gewässerschutz im Rhein - der Rendite der Pharmaindustrie geopfert | waters | waters | korrekt |
| affairs:36406 | Aargauer Landwirtschaft ohne chemisch-synthetische Pestizide | agriculture_biodiversity | agriculture_biodiversity | korrekt |
| affairs:2913 | Kreislaufwirtschaft | circular_economy | circular_economy | korrekt |
| affairs:58340 | Food Waste eindämmen | food_consumption | food_consumption | korrekt |
| affairs:79298 | Sustainable Finance bei der St.Galler Kantonalbank – noch viel Luft nach oben | sustainable_finance | sustainable_finance | korrekt |
| affairs:2135 | Nachhaltiger Konsum in der Stadt Luzern | food_consumption | food_consumption | korrekt |
| affairs:64337 | Schweizer Kreislaufwirtschaft stärken. Plattform für Schweizer Ressourceneffizienz | resources_raw_materials, circular_economy | circular_economy, resources_raw_materials | korrekt |
| affairs:28932 | Vernehmlassung zur Teilrevision des kantonalen Umweltgesetzes (KUG; RB 40.7011) | environmental_law | environmental_law | korrekt |
| affairs:1549 | Umweltbildung und -erziehung | environmental_research_education | environmental_research_education | korrekt |
| affairs:188 | Einen Klimafonds "New Green Deal für Basel" (NGDB) | environmental_funding | environmental_funding | korrekt |
| affairs:194 | Nachhaltige Beschaffung nach ökologischen Kriterien beim Kanton und seinen Betrieben | public_sector | public_sector | korrekt |
| affairs:45107 | Basel pro Klima: Pariser Klimaabkommen einhalten | international_environment | international_environment | korrekt |
| affairs:2 | Klassenbildungen und Schulraumbedarf | other | other | korrekt |
| affairs:3 | Statistisches Amt und seine perfekten Mitarbeiter | other | other | korrekt |
| affairs:4 | Staatspräsidenten in Basel | other | other | korrekt |
| affairs:5 | Bedürfnisse der Universität und der Forschung | other | other | korrekt |
| affairs:6 | Schutz der persönlichen Integrität im Grossen Rat | other | other | korrekt |
| affairs:7 | Schaffung von Wohnraum für Studierende und junge Leute in Ausbildung | other | other | korrekt |
| affairs:8 | Analyse zu den aktuellen Steuerabzügen im Kanton Basel-Stadt | other | other | korrekt |
| affairs:12 | Arbeitsbedingungen des Mittelbaus an der Universität Basel | other | other | korrekt |
| affairs:14 | Schulraumplanung | other | other | korrekt |
| affairs:15 | Videoüberwachung im öffentlichen Raum | other | other | korrekt |
| affairs:17 | Luzerner Theater | other | other | korrekt |
| affairs:22 | Wahl eines Mitglieds des Districtsrates (Nachfolge Jürg Stöcklin, GAB) | other | other | korrekt |
| affairs:26 | Zusätzliche Mittel für vollständige Transparenz in der «Affäre Rossier» | other | other | korrekt |
| affairs:29 | Keine EU-Flagge am Stadthaus | other | other | korrekt |
| affairs:34 | Ersatzwahl Wahlbüro,  Austritt von Urs Wagner | other | other | korrekt |
| affairs:37 | Einrichtung eines runden Tischs für LGBTI-Anliegen | other | other | korrekt |
| affairs:38 | Cannabis-Tests | other | other | korrekt |
| affairs:43 | Neue und innovative Lernräume | other | other | korrekt |
| affairs:45 | Spitex | other | other | korrekt |
| affairs:59 | Corona an der Schule Dietikon | other | other | korrekt |
| affairs:1428 | Ratschlag Gesamtkonzept Elektromobilität; Anpassung des kantonalen Umweltschutzgesetzes | sustainable_mobility, environmental_law | environmental_law, sustainable_mobility | korrekt |
| affairs:2091 | Kreislaufwirtschaft im Kampf gegen die Klimakrise nutzen | circular_economy, climate_energy_other | circular_economy, climate_energy_other | korrekt |
| affairs:12866 | Pestizideinsatz im Wald auf Stadtgebiet, Genehmigungskriterien für den Einsatz von Pestiziden sowie Möglichkeiten für den Schutz der Gewässer und deren Organismen | forest, waters | agriculture_biodiversity, forest, waters | korrekt |
| affairs:155107 | Schweizer Kreislaufwirtschaft stärken. Ressourceneffizienz im Umweltschutzgesetz aufnehmen | circular_economy, resources_raw_materials, environmental_law | circular_economy, environmental_law, resources_raw_materials | korrekt |
| affairs:160271 | Massnahmen zum Schutz von Klima und Biodiversität. Synergien stärken  | climate_energy_other; zusätzlich ein passendes Biodiversitätsthema | biodiversity_landscape_other, climate_energy_other | korrekt |
| affairs:1 | TransRUN II | other | other | korrekt |
| affairs:9 | Geschäftsbericht 2008 | other | other | korrekt |
| affairs:20 | Budgetpostulat Mirjam Ballmer Dienststelle Nr. 614 / Stadtgärtnerei / BVD | other | other | korrekt |
| affairs:48 | Arch-Areal | other | other | korrekt |
| affairs:57 | Nachhaltige Lösung Winterdienst | other | other | korrekt |
