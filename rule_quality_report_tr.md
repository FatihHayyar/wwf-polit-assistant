# Kural tabanlı sınıflandırma testi

Son push: 40/50; yeni kurallar: 50/50. Gerçek veritabanına yazılmadı; iki sürüm ayrı geçici SQLite veritabanlarında aynı 50 kaynak kaydıyla test edildi.

Beklentiler kaynak metinlerinden bağımsız belirlenmiştir. Bu geliştirme seti tek başına tüm verinin doğruluğunu kanıtlamaz.

| Kaynak | Başlık | Beklenen zorunlu kodlar | Yeni öneri | Sonuç |
|---|---|---|---|---|
| affairs:2160 | Photovoltaikanlage Schulanlage Spitz | renewable_electricity | renewable_electricity | Doğru |
| affairs:37526 | Stillstand bei der Windenergie-Nutzung im Kanton Bern? | renewable_electricity | renewable_electricity | Doğru |
| affairs:3895 | Mehr Transparenz bei der Energieeffizienz städtischer Liegenschaften | building_efficiency | building_efficiency | Doğru |
| affairs:8598 | Synergien nutzen bei der Bereitstellung von Ladeinfrastruktur für die E-Mobilität | sustainable_mobility | sustainable_mobility | Doğru |
| documents:68618 | Antrag Stadtrat - 2026.96W | renewable_heat | renewable_heat | Doğru |
| affairs:24891 | Betreffend Seglerschutz/Artenschutz | species_habitats | species_habitats | Doğru |
| affairs:1337 | Naturschutzgebiet Ruggeller Riet | protected_areas | protected_areas | Doğru |
| affairs:43542 | Waldreservate im Kanton Basel-Stadt | forest | forest | Doğru |
| affairs:271 | Gewässerschutz im Rhein - der Rendite der Pharmaindustrie geopfert | waters | waters | Doğru |
| affairs:36406 | Aargauer Landwirtschaft ohne chemisch-synthetische Pestizide | agriculture_biodiversity | agriculture_biodiversity | Doğru |
| affairs:2913 | Kreislaufwirtschaft | circular_economy | circular_economy | Doğru |
| affairs:58340 | Food Waste eindämmen | food_consumption | food_consumption | Doğru |
| affairs:79298 | Sustainable Finance bei der St.Galler Kantonalbank – noch viel Luft nach oben | sustainable_finance | sustainable_finance | Doğru |
| affairs:2135 | Nachhaltiger Konsum in der Stadt Luzern | food_consumption | food_consumption | Doğru |
| affairs:64337 | Schweizer Kreislaufwirtschaft stärken. Plattform für Schweizer Ressourceneffizienz | resources_raw_materials, circular_economy | circular_economy, resources_raw_materials | Doğru |
| affairs:28932 | Vernehmlassung zur Teilrevision des kantonalen Umweltgesetzes (KUG; RB 40.7011) | environmental_law | environmental_law | Doğru |
| affairs:1549 | Umweltbildung und -erziehung | environmental_research_education | environmental_research_education | Doğru |
| affairs:188 | Einen Klimafonds "New Green Deal für Basel" (NGDB) | environmental_funding | environmental_funding | Doğru |
| affairs:194 | Nachhaltige Beschaffung nach ökologischen Kriterien beim Kanton und seinen Betrieben | public_sector | public_sector | Doğru |
| affairs:45107 | Basel pro Klima: Pariser Klimaabkommen einhalten | international_environment | international_environment | Doğru |
| affairs:2 | Klassenbildungen und Schulraumbedarf | other | other | Doğru |
| affairs:3 | Statistisches Amt und seine perfekten Mitarbeiter | other | other | Doğru |
| affairs:4 | Staatspräsidenten in Basel | other | other | Doğru |
| affairs:5 | Bedürfnisse der Universität und der Forschung | other | other | Doğru |
| affairs:6 | Schutz der persönlichen Integrität im Grossen Rat | other | other | Doğru |
| affairs:7 | Schaffung von Wohnraum für Studierende und junge Leute in Ausbildung | other | other | Doğru |
| affairs:8 | Analyse zu den aktuellen Steuerabzügen im Kanton Basel-Stadt | other | other | Doğru |
| affairs:12 | Arbeitsbedingungen des Mittelbaus an der Universität Basel | other | other | Doğru |
| affairs:14 | Schulraumplanung | other | other | Doğru |
| affairs:15 | Videoüberwachung im öffentlichen Raum | other | other | Doğru |
| affairs:17 | Luzerner Theater | other | other | Doğru |
| affairs:22 | Wahl eines Mitglieds des Districtsrates (Nachfolge Jürg Stöcklin, GAB) | other | other | Doğru |
| affairs:26 | Zusätzliche Mittel für vollständige Transparenz in der «Affäre Rossier» | other | other | Doğru |
| affairs:29 | Keine EU-Flagge am Stadthaus | other | other | Doğru |
| affairs:34 | Ersatzwahl Wahlbüro,  Austritt von Urs Wagner | other | other | Doğru |
| affairs:37 | Einrichtung eines runden Tischs für LGBTI-Anliegen | other | other | Doğru |
| affairs:38 | Cannabis-Tests | other | other | Doğru |
| affairs:43 | Neue und innovative Lernräume | other | other | Doğru |
| affairs:45 | Spitex | other | other | Doğru |
| affairs:59 | Corona an der Schule Dietikon | other | other | Doğru |
| affairs:1428 | Ratschlag Gesamtkonzept Elektromobilität; Anpassung des kantonalen Umweltschutzgesetzes | sustainable_mobility, environmental_law | environmental_law, sustainable_mobility | Doğru |
| affairs:2091 | Kreislaufwirtschaft im Kampf gegen die Klimakrise nutzen | circular_economy, climate_energy_other | circular_economy, climate_energy_other | Doğru |
| affairs:12866 | Pestizideinsatz im Wald auf Stadtgebiet, Genehmigungskriterien für den Einsatz von Pestiziden sowie Möglichkeiten für den Schutz der Gewässer und deren Organismen | forest, waters | agriculture_biodiversity, forest, waters | Doğru |
| affairs:155107 | Schweizer Kreislaufwirtschaft stärken. Ressourceneffizienz im Umweltschutzgesetz aufnehmen | circular_economy, resources_raw_materials, environmental_law | circular_economy, environmental_law, resources_raw_materials | Doğru |
| affairs:160271 | Massnahmen zum Schutz von Klima und Biodiversität. Synergien stärken  | climate_energy_other; ayrıca uygun bir biyolojik çeşitlilik etiketi | biodiversity_landscape_other, climate_energy_other | Doğru |
| affairs:1 | TransRUN II | other | other | Doğru |
| affairs:9 | Geschäftsbericht 2008 | other | other | Doğru |
| affairs:20 | Budgetpostulat Mirjam Ballmer Dienststelle Nr. 614 / Stadtgärtnerei / BVD | other | other | Doğru |
| affairs:48 | Arch-Areal | other | other | Doğru |
| affairs:57 | Nachhaltige Lösung Winterdienst | other | other | Doğru |
