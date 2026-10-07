"""WWF classification taxonomy.

Every concept is language-independent. Translations and synonyms of the same
semantic concept are grouped under one explicit concept code.

This is important for content classification: translations of the same concept
must count as ONE concept, not as multiple independent signals.
"""

TAXONOMY = [
    {
        "code": "climate_energy",
        "names": {
            "de": "Klima & Energie",
            "fr": "Climat & énergie",
            "it": "Clima & energia",
            "rm": "Clima & energia",
        },
        "sort_order": 10,
        "children": [
            {
                "code": "renewable_electricity",
                "names": {
                    "de": "Erneuerbarer Strom",
                    "fr": "Électricité renouvelable",
                    "it": "Elettricità rinnovabile",
                    "rm": "Electricitad regenerabla",
                },
                "concepts": [
                    {
                        "code": "photovoltaics",
                        "terms": {
                            "de": ["Photovoltaik"],
                            "fr": ["photovoltaïque"],
                            "it": ["fotovoltaico"],
                            "rm": ["fotovoltaica"],
                        },
                    },
                    {
                        "code": "solar_installation",
                        "terms": {
                            "de": ["Solaranlage"],
                            "fr": ["installation solaire"],
                            "it": ["impianto solare"],
                            "rm": ["implant solar"],
                        },
                    },
                    {
                        "code": "solar_electricity",
                        "terms": {
                            "de": ["Solarstrom"],
                            "fr": ["électricité solaire"],
                            "it": ["energia solare"],
                            "rm": ["energia solara"],
                        },
                    },
                    {
                        "code": "wind_energy",
                        "terms": {
                            "de": ["Windenergie", "Windkraft"],
                            "fr": ["énergie éolienne"],
                            "it": ["energia eolica"],
                            "rm": ["energia da vent"],
                        },
                    },
                    {
                        "code": "renewable_electricity",
                        "terms": {
                            "de": [
                                "erneuerbarer Strom",
                                "erneuerbare Elektrizität",
                            ],
                            "fr": ["électricité renouvelable"],
                            "it": ["elettricità rinnovabile"],
                            "rm": ["electricitad regenerabla"],
                        },
                    },
                ],
            },
            {
                "code": "renewable_heat",
                "names": {
                    "de": "Erneuerbare Wärme",
                    "fr": "Chaleur renouvelable",
                    "it": "Calore rinnovabile",
                    "rm": "Chalira regenerabla",
                },
                "concepts": [
                    {
                        "code": "heat_pump",
                        "terms": {
                            "de": ["Wärmepumpe"],
                            "fr": ["pompe à chaleur"],
                            "it": ["pompa di calore"],
                            "rm": ["pumpa da chalira"],
                        },
                    },
                    {
                        "code": "district_heating",
                        "terms": {
                            "de": ["Fernwärme"],
                            "fr": ["chauffage à distance"],
                            "it": ["teleriscaldamento"],
                            "rm": ["chalira a distanza"],
                        },
                    },
                    {
                        "code": "renewable_heat",
                        "terms": {
                            "de": ["erneuerbare Wärme"],
                            "fr": ["chaleur renouvelable"],
                            "it": ["calore rinnovabile"],
                            "rm": ["chalira regenerabla"],
                        },
                    },
                    {
                        "code": "solar_thermal",
                        "terms": {
                            "de": ["Solarthermie"],
                            "fr": ["solaire thermique"],
                            "it": ["solare termico"],
                        },
                    },
                    {
                        "code": "geothermal",
                        "terms": {
                            "de": ["Geothermie"],
                            "fr": ["géothermie"],
                            "it": ["geotermia"],
                            "rm": ["geotermia"],
                        },
                    },
                ],
            },
            {
                "code": "building_efficiency",
                "names": {
                    "de": "Gebäude & Energieeffizienz",
                    "fr": "Bâtiments & efficacité énergétique",
                    "it": "Edifici & efficienza energetica",
                    "rm": "Edifizis & effizienza energetica",
                },
                "concepts": [
                    {
                        "code": "building_renovation",
                        "terms": {
                            "de": [
                                "Gebäudesanierung",
                                "energetische Sanierung",
                            ],
                            "fr": [
                                "rénovation énergétique",
                                "assainissement énergétique",
                            ],
                            "it": [
                                "risanamento energetico",
                                "ristrutturazione energetica",
                            ],
                            "rm": ["sanaziun energetica"],
                        },
                    },
                    {
                        "code": "building_energy",
                        "terms": {
                            "de": ["Gebäudeenergie"],
                        },
                    },
                    {
                        "code": "energy_efficiency",
                        "terms": {
                            "de": ["Energieeffizienz"],
                            "fr": ["efficacité énergétique"],
                            "it": ["efficienza energetica"],
                            "rm": ["effizienza energetica"],
                        },
                    },
                    {
                        "code": "thermal_insulation",
                        "terms": {
                            "de": ["Wärmedämmung"],
                            "fr": ["isolation thermique"],
                            "it": ["isolamento termico"],
                            "rm": ["isolaziun termica"],
                        },
                    },
                ],
            },
            {
                "code": "sustainable_mobility",
                "names": {
                    "de": "Nachhaltige Mobilität & E-Mobilität",
                    "fr": "Mobilité durable & électromobilité",
                    "it": "Mobilità sostenibile & mobilità elettrica",
                    "rm": "Mobilitad persistenta & electromobilitad",
                },
                "concepts": [
                    {
                        "code": "electromobility",
                        "terms": {
                            "de": ["Elektromobilität"],
                            "fr": ["électromobilité"],
                            "it": ["elettromobilità"],
                            "rm": ["electromobilitad"],
                        },
                    },
                    {
                        "code": "electric_vehicle",
                        "terms": {
                            "de": ["Elektrofahrzeug"],
                            "fr": ["véhicule électrique"],
                            "it": ["veicolo elettrico"],
                            "rm": ["vehichel electric"],
                        },
                    },
                    {
                        "code": "charging_infrastructure",
                        "terms": {
                            "de": [
                                "Ladeinfrastruktur",
                                "Ladestation",
                            ],
                            "fr": [
                                "infrastructure de recharge",
                                "borne de recharge",
                            ],
                            "it": [
                                "infrastruttura di ricarica",
                                "stazione di ricarica",
                            ],
                            "rm": ["infrastructura da chargiar"],
                        },
                    },
                    {
                        "code": "slow_mobility",
                        "terms": {
                            "de": ["Langsamverkehr"],
                            "fr": ["mobilité douce"],
                            "it": ["mobilità lenta"],
                            "rm": ["mobilitad plauna"],
                        },
                    },
                    {
                        "code": "cycling",
                        "terms": {
                            "de": ["Veloverkehr"],
                            "fr": ["trafic cycliste"],
                            "it": ["traffico ciclistico"],
                        },
                    },
                ],
            },
            {
                "code": "grids_storage",
                "names": {
                    "de": "Netze & Speicher",
                    "fr": "Réseaux & stockage",
                    "it": "Reti & stoccaggio",
                    "rm": "Raits & accumulaziun",
                },
                "concepts": [
                    {
                        "code": "electricity_grid",
                        "terms": {
                            "de": ["Stromnetz"],
                            "fr": ["réseau électrique"],
                            "it": ["rete elettrica"],
                            "rm": ["rait electrica"],
                        },
                    },
                    {
                        "code": "grid_expansion",
                        "terms": {
                            "de": ["Netzausbau"],
                            "fr": ["extension du réseau"],
                            "it": ["potenziamento della rete"],
                            "rm": ["engrondiment da la rait"],
                        },
                    },
                    {
                        "code": "electricity_storage",
                        "terms": {
                            "de": ["Stromspeicher"],
                            "fr": ["stockage d'électricité"],
                            "it": ["accumulo elettrico"],
                        },
                    },
                    {
                        "code": "battery_storage",
                        "terms": {
                            "de": ["Batteriespeicher"],
                            "fr": ["stockage par batterie"],
                            "it": ["accumulo a batteria"],
                        },
                    },
                    {
                        "code": "energy_storage",
                        "terms": {
                            "de": ["Energiespeicher"],
                            "fr": ["stockage d'énergie"],
                            "it": ["stoccaggio di energia"],
                            "rm": ["accumulaziun d'energia"],
                        },
                    },
                ],
            },
            {
                "code": "fossil_energy",
                "names": {
                    "de": "Fossile Energien",
                    "fr": "Énergies fossiles",
                    "it": "Energie fossili",
                    "rm": "Energias fossilas",
                },
                "concepts": [
                    {
                        "code": "natural_gas",
                        "terms": {
                            "de": ["Erdgas"],
                            "fr": ["gaz naturel"],
                            "it": ["gas naturale"],
                            "rm": ["gas natiral"],
                        },
                    },
                    {
                        "code": "heating_oil",
                        "terms": {
                            "de": ["Heizöl"],
                            "fr": ["mazout"],
                            "it": ["olio combustibile"],
                        },
                    },
                    {
                        "code": "fossil_energy",
                        "terms": {
                            "de": ["fossile Energie"],
                            "fr": ["énergie fossile"],
                            "it": ["energia fossile"],
                            "rm": ["energia fossila"],
                        },
                    },
                    {
                        "code": "fossil_fuel",
                        "terms": {
                            "de": ["fossiler Brennstoff"],
                            "fr": ["combustible fossile"],
                            "it": ["combustibile fossile"],
                            "rm": ["combustibel fossil"],
                        },
                    },
                    {
                        "code": "gas_heating",
                        "terms": {
                            "de": ["Gasheizung"],
                            "fr": ["chauffage au gaz"],
                            "it": ["riscaldamento a gas"],
                        },
                    },
                    {
                        "code": "oil_heating",
                        "terms": {
                            "de": ["Ölheizung"],
                            "fr": ["chauffage au mazout"],
                        },
                    },
                ],
            },
            {
                "code": "large_consumers_datacenters",
                "names": {
                    "de": "Grossverbraucher & Rechenzentren",
                    "fr": "Grands consommateurs & centres de données",
                    "it": "Grandi consumatori & centri dati",
                    "rm": "Gronds consuments & centers da datas",
                },
                "concepts": [
                    {
                        "code": "large_consumer",
                        "terms": {
                            "de": [
                                "Grossverbraucher",
                                "Großverbraucher",
                            ],
                            "fr": [
                                "grand consommateur",
                                "grands consommateurs",
                            ],
                            "it": [
                                "grande consumatore",
                                "grandi consumatori",
                            ],
                            "rm": [
                                "grond consument",
                                "gronds consuments",
                            ],
                        },
                    },
                    {
                        "code": "data_center",
                        "terms": {
                            "de": [
                                "Rechenzentrum",
                                "Rechenzentren",
                                "Datacenter",
                            ],
                            "fr": [
                                "centre de données",
                                "centres de données",
                                "datacenter",
                            ],
                            "it": [
                                "centro dati",
                                "centri dati",
                                "datacenter",
                            ],
                            "rm": [
                                "center da datas",
                                "centers da datas",
                            ],
                        },
                    },
                ],
            },
        ],
    },
    {
        "code": "biodiversity_landscape",
        "names": {
            "de": "Biodiversität & Landschaft",
            "fr": "Biodiversité & paysage",
            "it": "Biodiversità & paesaggio",
            "rm": "Biodiversitad & cuntrada",
        },
        "sort_order": 20,
        "children": [
            {
                "code": "species_habitats",
                "names": {
                    "de": "Arten & Lebensräume",
                    "fr": "Espèces & habitats",
                    "it": "Specie & habitat",
                    "rm": "Spezias & spazis da viver",
                },
                "concepts": [
                    {
                        "code": "species_protection",
                        "terms": {
                            "de": ["Artenschutz"],
                            "fr": ["protection des espèces"],
                            "it": ["protezione delle specie"],
                            "rm": ["protecziun da las spezias"],
                        },
                    },
                    {
                        "code": "habitat",
                        "rule_type": "context",
                        "terms": {
                            "de": ["Lebensraum", "Lebensräume"],
                            "fr": [
                                "habitat naturel",
                                "habitats naturels",
                            ],
                            "it": [
                                "habitat naturale",
                                "habitat naturali",
                            ],
                            "rm": ["spazi da viver"],
                        },
                    },
                    {
                        "code": "biotope",
                        "terms": {
                            "de": ["Biotop"],
                            "fr": ["biotope"],
                            "it": ["biotopo"],
                            "rm": ["biotop"],
                        },
                    },
                    {
                        "code": "wildlife",
                        "terms": {
                            "de": ["Wildtier"],
                            "fr": ["faune sauvage"],
                            "it": ["fauna selvatica"],
                            "rm": ["animals selvadis"],
                        },
                    },
                    {
                        "code": "species_diversity",
                        "terms": {
                            "de": ["Artenvielfalt"],
                            "fr": ["diversité des espèces"],
                            "it": ["diversità delle specie"],
                        },
                    },
                ],
            },
            {
                "code": "protected_areas",
                "names": {
                    "de": "Schutzgebiete",
                    "fr": "Aires protégées",
                    "it": "Aree protette",
                    "rm": "Territoris protegids",
                },
                "concepts": [
                    {
                        "code": "nature_reserve",
                        "terms": {
                            "de": ["Naturschutzgebiet"],
                            "fr": ["réserve naturelle"],
                            "it": ["riserva naturale"],
                            "rm": ["reservat natiral"],
                        },
                    },
                    {
                        "code": "protected_area",
                        "terms": {
                            "de": ["Schutzgebiet"],
                            "fr": ["aire protégée"],
                            "it": ["area protetta"],
                            "rm": ["territori protegì"],
                        },
                    },
                    {
                        "code": "nature_park",
                        "terms": {
                            "de": ["Naturpark"],
                            "fr": ["parc naturel"],
                            "it": ["parco naturale"],
                            "rm": ["parc natiral"],
                        },
                    },
                    {
                        "code": "biosphere_reserve",
                        "terms": {
                            "de": ["Biosphärenreservat"],
                            "fr": ["réserve de biosphère"],
                            "it": ["riserva della biosfera"],
                        },
                    },
                ],
            },
            {
                "code": "forest",
                "names": {
                    "de": "Wald",
                    "fr": "Forêt",
                    "it": "Foresta",
                    "rm": "Guaud",
                },
                "concepts": [
                    {
                        "code": "forest_protection",
                        "terms": {
                            "de": ["Waldschutz"],
                            "fr": ["protection des forêts"],
                            "it": ["protezione delle foreste"],
                            "rm": ["protecziun dal guaud"],
                        },
                    },
                    {
                        "code": "forest_biodiversity",
                        "terms": {
                            "de": ["Waldbiodiversität"],
                            "fr": ["biodiversité forestière"],
                            "it": ["biodiversità forestale"],
                            "rm": ["biodiversitad dal guaud"],
                        },
                    },
                    {
                        "code": "protective_forest",
                        "terms": {
                            "de": ["Schutzwald"],
                            "fr": ["forêt protectrice"],
                            "it": ["bosco di protezione"],
                            "rm": ["guaud da protecziun"],
                        },
                    },
                    {
                        "code": "forest_reserve",
                        "terms": {
                            "de": ["Waldreservat"],
                            "fr": ["réserve forestière"],
                            "it": ["riserva forestale"],
                        },
                    },
                    {
                        "code": "forestry",
                        "terms": {
                            "de": ["Forstwirtschaft"],
                            "fr": ["sylviculture"],
                            "it": ["selvicoltura"],
                        },
                    },
                ],
            },
            {
                "code": "waters",
                "names": {
                    "de": "Gewässer & aquatische Ökosysteme",
                    "fr": "Eaux & écosystèmes aquatiques",
                    "it": "Acque & ecosistemi acquatici",
                    "rm": "Auas & ecosistems aquatics",
                },
                "concepts": [
                    {
                        "code": "water_protection",
                        "terms": {
                            "de": ["Gewässerschutz"],
                            "fr": ["protection des eaux"],
                            "it": ["protezione delle acque"],
                            "rm": ["protecziun da las auas"],
                        },
                    },
                    {
                        "code": "water_revitalization",
                        "terms": {
                            "de": ["Revitalisierung"],
                            "fr": ["revitalisation des cours d'eau"],
                            "it": ["rivitalizzazione dei corsi d'acqua"],
                            "rm": ["revitalisaziun"],
                        },
                    },
                    {
                        "code": "renaturation",
                        "terms": {
                            "de": ["Renaturierung"],
                            "fr": ["renaturation"],
                            "it": ["rinaturazione"],
                            "rm": ["renaturalisaziun"],
                        },
                    },
                    {
                        "code": "residual_flow",
                        "terms": {
                            "de": ["Restwasser"],
                            "fr": ["débit résiduel"],
                            "it": ["deflusso residuale"],
                            "rm": ["aua restanta"],
                        },
                    },
                    {
                        "code": "fish_passage",
                        "terms": {
                            "de": ["Fischgängigkeit"],
                            "fr": ["migration piscicole"],
                            "it": ["migrazione dei pesci"],
                        },
                    },
                    {
                        "code": "floodplain",
                        "terms": {
                            "de": ["Auenlandschaft"],
                        },
                    },
                ],
            },
            {
                "code": "soil_spatial_planning",
                "names": {
                    "de": "Boden & Raumplanung",
                    "fr": "Sols & aménagement du territoire",
                    "it": "Suolo & pianificazione territoriale",
                    "rm": "Terren & planisaziun dal territori",
                },
                "concepts": [
                    {
                        "code": "soil_protection",
                        "terms": {
                            "de": ["Bodenschutz"],
                            "fr": ["protection des sols"],
                            "it": ["protezione del suolo"],
                            "rm": ["protecziun dal terren"],
                        },
                    },
                    {
                        "code": "soil_sealing",
                        "terms": {
                            "de": ["Bodenversiegelung"],
                            "fr": ["imperméabilisation des sols"],
                            "it": ["impermeabilizzazione del suolo"],
                            "rm": ["impermeabilisaziun dal terren"],
                        },
                    },
                    {
                        "code": "urban_sprawl",
                        "terms": {
                            "de": ["Zersiedelung"],
                            "fr": ["mitage"],
                            "it": ["dispersione insediativa"],
                        },
                    },
                    {
                        "code": "spatial_planning",
                        "terms": {
                            "de": ["Raumplanung"],
                            "fr": ["aménagement du territoire"],
                            "it": ["pianificazione territoriale"],
                            "rm": ["planisaziun dal territori"],
                        },
                    },
                    {
                        "code": "crop_rotation_area",
                        "terms": {
                            "de": ["Fruchtfolgefläche"],
                            "fr": ["surface d'assolement"],
                            "it": [
                                "superficie per l'avvicendamento delle colture"
                            ],
                        },
                    },
                ],
            },
            {
                "code": "agriculture_biodiversity",
                "names": {
                    "de": "Landwirtschaft & Biodiversität",
                    "fr": "Agriculture & biodiversité",
                    "it": "Agricoltura & biodiversità",
                    "rm": "Agricultura & biodiversitad",
                },
                "concepts": [
                    {
                        "code": "biodiversity_promotion_area",
                        "terms": {
                            "de": ["Biodiversitätsförderfläche"],
                            "fr": [
                                "surface de promotion de la biodiversité"
                            ],
                            "it": [
                                "superficie per la promozione della biodiversità"
                            ],
                            "rm": [
                                "surfatscha da promoziun da la biodiversitad"
                            ],
                        },
                    },
                    {
                        "code": "ecological_performance",
                        "terms": {
                            "de": ["ökologischer Leistungsnachweis"],
                            "fr": ["prestations écologiques requises"],
                            "it": [
                                "prova che le esigenze ecologiche sono rispettate"
                            ],
                        },
                    },
                    {
                        "code": "pesticide",
                        "terms": {
                            "de": ["Pestizid"],
                            "fr": ["pesticide"],
                            "it": ["pesticida"],
                            "rm": ["pesticid"],
                        },
                    },
                    {
                        "code": "plant_protection_product",
                        "terms": {
                            "de": ["Pflanzenschutzmittel"],
                            "fr": ["produit phytosanitaire"],
                            "it": ["prodotto fitosanitario"],
                            "rm": ["med da protecziun da plantas"],
                        },
                    },
                    {
                        "code": "agricultural_biodiversity",
                        "terms": {
                            "de": ["Agrarbiodiversität"],
                            "fr": ["biodiversité agricole"],
                            "it": ["biodiversità agricola"],
                        },
                    },
                ],
            },
        ],
    },
    {
        "code": "sustainable_economy_consumption",
        "names": {
            "de": "Nachhaltige Wirtschaft & Konsum",
            "fr": "Économie durable & consommation",
            "it": "Economia sostenibile & consumo",
            "rm": "Economia persistenta & consum",
        },
        "sort_order": 30,
        "children": [
            {
                "code": "circular_economy",
                "names": {
                    "de": "Kreislaufwirtschaft & Recycling",
                    "fr": "Économie circulaire & recyclage",
                    "it": "Economia circolare & riciclaggio",
                    "rm": "Economia circulara & recicladi",
                },
                "concepts": [
                    {
                        "code": "circular_economy",
                        "terms": {
                            "de": ["Kreislaufwirtschaft"],
                            "fr": ["économie circulaire"],
                            "it": ["economia circolare"],
                            "rm": ["economia circulara"],
                        },
                    },
                    {
                        "code": "recycling",
                        "terms": {
                            "de": ["Recycling"],
                            "fr": ["recyclage"],
                            "it": ["riciclaggio"],
                            "rm": ["recicladi"],
                        },
                    },
                    {
                        "code": "reuse",
                        "terms": {
                            "de": ["Wiederverwendung"],
                            "fr": ["réutilisation", "réemploi"],
                            "it": ["riutilizzo", "riuso"],
                            "rm": ["reutilisaziun"],
                        },
                    },
                    {
                        "code": "reusable",
                        "terms": {
                            "de": ["Mehrweg"],
                            "fr": ["emballage réutilisable"],
                            "it": ["imballaggio riutilizzabile"],
                        },
                    },
                    {
                        "code": "resource_cycle",
                        "terms": {
                            "de": ["Ressourcenkreislauf"],
                        },
                    },
                ],
            },
            {
                "code": "resources_raw_materials",
                "names": {
                    "de": "Ressourcen & Rohstoffe",
                    "fr": "Ressources & matières premières",
                    "it": "Risorse & materie prime",
                    "rm": "Resursas & materias primas",
                },
                "concepts": [
                    {
                        "code": "raw_material_consumption",
                        "terms": {
                            "de": ["Rohstoffverbrauch"],
                            "fr": ["consommation de matières premières"],
                            "it": ["consumo di materie prime"],
                            "rm": ["consum da materias primas"],
                        },
                    },
                    {
                        "code": "resource_consumption",
                        "terms": {
                            "de": ["Ressourcenverbrauch"],
                            "fr": ["consommation de ressources"],
                            "it": ["consumo di risorse"],
                            "rm": ["consum da resursas"],
                        },
                    },
                    {
                        "code": "raw_material_extraction",
                        "terms": {
                            "de": ["Rohstoffabbau"],
                            "fr": ["extraction de matières premières"],
                            "it": ["estrazione di materie prime"],
                        },
                    },
                    {
                        "code": "resource_efficiency",
                        "terms": {
                            "de": ["Ressourceneffizienz"],
                            "fr": ["efficacité des ressources"],
                            "it": ["efficienza delle risorse"],
                            "rm": ["effizienza da resursas"],
                        },
                    },
                ],
            },
            {
                "code": "sustainable_finance",
                "names": {
                    "de": "Nachhaltige Finanzierung",
                    "fr": "Finance durable",
                    "it": "Finanza sostenibile",
                    "rm": "Finanzas persistentas",
                },
                "concepts": [
                    {
                        "code": "sustainable_finance",
                        "terms": {
                            "de": [
                                "nachhaltige Finanzierung",
                                "Sustainable Finance",
                            ],
                            "fr": ["finance durable"],
                            "it": ["finanza sostenibile"],
                            "rm": ["finanzas persistentas"],
                        },
                    },
                    {
                        "code": "green_bond",
                        "terms": {
                            "de": ["Green Bond"],
                            "fr": ["obligation verte"],
                            "it": ["obbligazione verde"],
                            "rm": ["obligaziun verda"],
                        },
                    },
                    {
                        "code": "climate_aligned_finance",
                        "terms": {
                            "de": ["klimaverträgliche Finanzflüsse"],
                            "fr": [
                                "flux financiers compatibles avec le climat"
                            ],
                            "it": [
                                "flussi finanziari compatibili con il clima"
                            ],
                        },
                    },
                ],
            },
            {
                "code": "companies_supply_chains",
                "names": {
                    "de": "Unternehmen & Lieferketten",
                    "fr": "Entreprises & chaînes d'approvisionnement",
                    "it": "Imprese & catene di approvvigionamento",
                    "rm": "Interpresas & chadainas da furniziun",
                },
                "concepts": [
                    {
                        "code": "supply_chain",
                        "terms": {
                            "de": ["Lieferkette", "Lieferketten"],
                            "fr": [
                                "chaîne d'approvisionnement",
                                "chaînes d'approvisionnement",
                            ],
                            "it": [
                                "catena di approvvigionamento",
                                "catene di approvvigionamento",
                            ],
                            "rm": ["chadaina da furniziun"],
                        },
                    },
                    {
                        "code": "due_diligence",
                        "terms": {
                            "de": ["Sorgfaltspflicht"],
                            "fr": ["devoir de diligence"],
                            "it": ["dovere di diligenza"],
                            "rm": ["obligaziun da diligenza"],
                        },
                    },
                    {
                        "code": "corporate_responsibility",
                        "terms": {
                            "de": ["Unternehmensverantwortung"],
                            "fr": ["responsabilité des entreprises"],
                            "it": ["responsabilità delle imprese"],
                            "rm": ["responsabladad d'interpresas"],
                        },
                    },
                    {
                        "code": "sustainability_reporting",
                        "terms": {
                            "de": ["Nachhaltigkeitsberichterstattung"],
                            "fr": ["rapport de durabilité"],
                            "it": ["rapporto di sostenibilità"],
                        },
                    },
                ],
            },
            {
                "code": "food_consumption",
                "names": {
                    "de": "Ernährung & Konsum",
                    "fr": "Alimentation & consommation",
                    "it": "Alimentazione & consumo",
                    "rm": "Nutriment & consum",
                },
                "concepts": [
                    {
                        "code": "food_waste",
                        "terms": {
                            "de": [
                                "Lebensmittelverschwendung",
                                "Food Waste",
                            ],
                            "fr": ["gaspillage alimentaire"],
                            "it": ["spreco alimentare"],
                            "rm": ["sfarlattim da victualias"],
                        },
                    },
                    {
                        "code": "sustainable_consumption",
                        "terms": {
                            "de": ["nachhaltiger Konsum"],
                            "fr": ["consommation durable"],
                            "it": ["consumo sostenibile"],
                            "rm": ["consum persistent"],
                        },
                    },
                    {
                        "code": "sustainable_diet",
                        "terms": {
                            "de": ["nachhaltige Ernährung"],
                            "fr": ["alimentation durable"],
                            "it": ["alimentazione sostenibile"],
                            "rm": ["nutriment persistent"],
                        },
                    },
                    {
                        "code": "meat_consumption",
                        "terms": {
                            "de": ["Fleischkonsum"],
                            "fr": ["consommation de viande"],
                            "it": ["consumo di carne"],
                        },
                    },
                ],
            },
        ],
    },
    {
        "code": "environment_policy",
        "names": {
            "de": "Umwelt & Politik",
            "fr": "Environnement & politique",
            "it": "Ambiente & politica",
            "rm": "Ambient & politica",
        },
        "sort_order": 40,
        "children": [
            {
                "code": "environmental_law",
                "names": {
                    "de": "Umweltrecht & Regulierung",
                    "fr": "Droit de l'environnement & réglementation",
                    "it": "Diritto ambientale & regolamentazione",
                    "rm": "Dretg d'ambient & regulaziun",
                },
                "concepts": [
                    {
                        "code": "environmental_law_act",
                        "terms": {
                            "de": [
                                "Umweltgesetz",
                                "Umweltschutzgesetz",
                            ],
                            "fr": [
                                "loi sur la protection de l'environnement"
                            ],
                            "it": [
                                "legge sulla protezione dell'ambiente"
                            ],
                            "rm": [
                                "lescha davart la protecziun da l'ambient"
                            ],
                        },
                    },
                    {
                        "code": "environmental_law",
                        "terms": {
                            "de": ["Umweltrecht"],
                            "fr": ["droit de l'environnement"],
                            "it": ["diritto ambientale"],
                            "rm": ["dretg d'ambient"],
                        },
                    },
                    {
                        "code": "environmental_impact_assessment",
                        "terms": {
                            "de": [
                                "Umweltverträglichkeitsprüfung",
                                "UVP",
                            ],
                            "fr": [
                                "étude d'impact sur l'environnement",
                                "EIE",
                            ],
                            "it": [
                                "esame dell'impatto sull'ambiente",
                                "EIA",
                            ],
                        },
                    },
                ],
            },
            {
                "code": "public_sector",
                "names": {
                    "de": "Öffentliche Hand",
                    "fr": "Pouvoirs publics",
                    "it": "Settore pubblico",
                    "rm": "Maun public",
                },
                "concepts": [
                    {
                        "code": "public_procurement",
                        "terms": {
                            "de": [
                                "öffentliche Beschaffung",
                                "öffentliches Beschaffungswesen",
                            ],
                            "fr": [
                                "marchés publics",
                                "achats publics",
                            ],
                            "it": [
                                "appalti pubblici",
                                "acquisti pubblici",
                            ],
                            "rm": ["acquisiziun publica"],
                        },
                    },
                    {
                        "code": "cantonal_administration",
                        "rule_type": "context",
                        "terms": {
                            "de": ["kantonale Verwaltung"],
                            "fr": ["administration cantonale"],
                            "it": ["amministrazione cantonale"],
                            "rm": ["administraziun chantunala"],
                        },
                    },
                    {
                        "code": "municipal_administration",
                        "rule_type": "context",
                        "terms": {
                            "de": ["Gemeindeverwaltung"],
                            "fr": ["administration communale"],
                            "it": ["amministrazione comunale"],
                            "rm": ["administraziun communala"],
                        },
                    },
                    {
                        "code": "exemplary_role",
                        "terms": {
                            "de": ["Vorbildfunktion"],
                            "fr": ["rôle exemplaire"],
                            "it": ["ruolo esemplare"],
                        },
                    },
                ],
            },
            {
                "code": "environmental_funding",
                "names": {
                    "de": "Umweltfinanzierung & Förderung",
                    "fr": "Financement environnemental & encouragement",
                    "it": "Finanziamento ambientale & promozione",
                    "rm": "Finanziaziun ambientala & promoziun",
                },
                "concepts": [
                    {
                        "code": "generic_funding_program",
                        "rule_type": "context",
                        "terms": {
                            "de": ["Förderprogramm"],
                            "fr": ["programme d'encouragement"],
                            "it": ["programma di incentivazione"],
                            "rm": ["program da promoziun"],
                        },
                    },
                    {
                        "code": "environmental_support",
                        "terms": {
                            "de": ["Umweltförderung"],
                        },
                    },
                    {
                        "code": "climate_fund",
                        "terms": {
                            "de": ["Klimafonds"],
                            "fr": ["fonds climatique"],
                            "it": ["fondo per il clima"],
                            "rm": ["fond climatic"],
                        },
                    },
                    {
                        "code": "energy_support",
                        "terms": {
                            "de": ["Energieförderung"],
                            "fr": ["promotion énergétique"],
                            "it": ["promozione energetica"],
                            "rm": ["promoziun energetica"],
                        },
                    },
                    {
                        "code": "funding_contribution",
                        "rule_type": "context",
                        "terms": {
                            "de": ["Förderbeitrag"],
                            "fr": ["contribution d'encouragement"],
                            "it": ["contributo di incentivazione"],
                        },
                    },
                ],
            },
            {
                "code": "international_environment",
                "names": {
                    "de": "Internationale Umweltpolitik",
                    "fr": "Politique environnementale internationale",
                    "it": "Politica ambientale internazionale",
                    "rm": "Politica ambientala internaziunala",
                },
                "concepts": [
                    {
                        "code": "climate_agreement",
                        "terms": {
                            "de": [
                                "Pariser Klimaabkommen",
                                "Klimaabkommen",
                            ],
                            "fr": [
                                "Accord de Paris",
                                "accord climatique",
                            ],
                            "it": [
                                "Accordo di Parigi",
                                "accordo sul clima",
                            ],
                            "rm": [
                                "Convenziun da Paris",
                                "cunvegna climatica",
                            ],
                        },
                    },
                    {
                        "code": "biodiversity_convention",
                        "terms": {
                            "de": ["Biodiversitätskonvention"],
                            "fr": [
                                "Convention sur la diversité biologique"
                            ],
                            "it": [
                                "Convenzione sulla diversità biologica"
                            ],
                            "rm": ["convenziun da biodiversitad"],
                        },
                    },
                    {
                        "code": "un_climate_conference",
                        "terms": {
                            "de": ["UNO-Klimakonferenz"],
                            "fr": [
                                "conférence des Nations Unies sur le climat"
                            ],
                            "it": ["conferenza ONU sul clima"],
                        },
                    },
                    {
                        "code": "cop",
                        "terms": {
                            "de": ["COP"],
                            "fr": ["COP"],
                            "it": ["COP"],
                            "rm": ["COP"],
                        },
                    },
                ],
            },
            {
                "code": "environmental_research_education",
                "names": {
                    "de": "Umweltbildung & Forschung",
                    "fr": "Éducation environnementale & recherche",
                    "it": "Educazione ambientale & ricerca",
                    "rm": "Furmaziun ambientala & perscrutaziun",
                },
                "concepts": [
                    {
                        "code": "environmental_education",
                        "terms": {
                            "de": ["Umweltbildung"],
                            "fr": ["éducation à l'environnement"],
                            "it": ["educazione ambientale"],
                            "rm": ["furmaziun ambientala"],
                        },
                    },
                    {
                        "code": "climate_education",
                        "terms": {
                            "de": ["Klimabildung"],
                            "fr": ["éducation climatique"],
                            "it": ["educazione climatica"],
                            "rm": ["furmaziun climatica"],
                        },
                    },
                    {
                        "code": "environmental_research",
                        "terms": {
                            "de": ["Umweltforschung"],
                            "fr": ["recherche environnementale"],
                            "it": ["ricerca ambientale"],
                            "rm": ["perscrutaziun ambientala"],
                        },
                    },
                    {
                        "code": "climate_research",
                        "terms": {
                            "de": ["Klimaforschung"],
                            "fr": ["recherche climatique"],
                            "it": ["ricerca climatica"],
                            "rm": ["perscrutaziun climatica"],
                        },
                    },
                    {
                        "code": "biodiversity_research",
                        "terms": {
                            "de": ["Biodiversitätsforschung"],
                            "fr": ["recherche sur la biodiversité"],
                            "it": ["ricerca sulla biodiversità"],
                        },
                    },
                ],
            },
        ],
    },
    {
        "code": "other",
        "names": {
            "de": "Sonstiges",
            "fr": "Autres",
            "it": "Altro",
            "rm": "Auter",
        },
        "sort_order": 999,
        "fallback": True,
        "children": [],
    },
]