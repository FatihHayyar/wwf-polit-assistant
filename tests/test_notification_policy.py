import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from app.services.notification_policy import eligible


class NotificationPolicyTests(unittest.TestCase):
    def test_editorial_dates_and_hash_changes_are_not_notifications(self):
        for dataset, field in [('affairs', 'end_date'), ('affairs', 'title_de'),
                               ('agendas', 'meeting_id'), ('agendas', 'item_title'),
                               ('documents', 'hash'), ('documents', 'name'),
                               ('texts', 'text_date'), ('votings', 'title_de'),
                               ('events', 'actor_de'), ('groups', 'name_de')]:
            self.assertFalse(eligible(dataset, 'updated', changes={field: {'before': 'old', 'after': 'new'}}))

    def test_isolated_spelling_correction_is_suppressed(self):
        self.assertFalse(eligible('texts', 'updated', changes={'text_de': {
            'before': 'mit gleicher Wirkstoffszusammensetzung',
            'after': 'mit gleicher Wirkstoffzusammensetzung'}}))
        self.assertFalse(eligible('texts', 'updated', changes={'text_de': {'before': 'Antwort', 'after': 'ANTWORT'}}))

    def test_inline_html_and_typography_do_not_trigger_notifications(self):
        for before, after in [('<a><span>Das Wort</span></a>.', '<a>Das Wort</a>.'),
                              ('l’autocensure', "l'autocensure"),
                              ('<span>Wirk</span><span>stoff</span>', 'Wirkstoff')]:
            self.assertFalse(eligible('texts', 'updated', changes={'text_de': {'before': before, 'after': after}}))

    def test_small_but_substantive_changes_remain_eligible(self):
        for before, after in [('10 Millionen', '11 Millionen'), ('angenommen', 'nicht angenommen'), ('-5', '5')]:
            self.assertTrue(eligible('texts', 'updated', changes={'text_de': {'before': before, 'after': after}}))

    def test_each_dataset_has_meaningful_and_technical_change_rules(self):
        cases={"affairs":("state_name_de","external_id"),"agendas":("item_result","item_number"),
               "meetings":("location","number"),"votings":("results_yes","external_id"),
               "events":("date","last"),"documents":("text","url"),"texts":("text_de","text_format"),
               "groups":("active","type_harmonized"),"interests":("role_name_de","declaration_doc_url")}
        for dataset,(meaningful,technical) in cases.items():
            with self.subTest(dataset=dataset):
                self.assertTrue(eligible(dataset,"created"))
                self.assertTrue(eligible(dataset,"updated",changes={meaningful:{"before":"old","after":"new"}}))
                self.assertFalse(eligible(dataset,"updated",changes={technical:{"before":"old","after":"new"}}))
                self.assertFalse(eligible(dataset,"updated",changes={meaningful:{"before":"A & B","after":" A  &amp; B\n"}}))

    def test_timestamp_precision_and_added_time_of_day_are_not_news(self):
        for before, after in [("2015-05-05T17:59:42", "2015-05-05T17:59:42.540000"),
                              ("2024-12-20T00:00:00", "2024-12-20T08:26:21.158000")]:
            self.assertFalse(eligible("votings", "updated", changes={"date": {"before": before, "after": after}}))
        self.assertTrue(eligible("votings", "updated", changes={"date": {"before": "2024-12-20T08:26:21", "after": "2024-12-21T08:26:21"}}))
        self.assertTrue(eligible("events", "updated", changes={"date": {"before": "2024-12-20T08:00:00", "after": "2024-12-20T14:00:00"}}))

    def test_accents_and_sentence_punctuation_are_not_news(self):
        self.assertFalse(eligible("affairs", "updated", changes={"state_name_fr": {
            "before": "En commission du Conseil des Etats", "after": "En commission du Conseil des États"}}))
        self.assertFalse(eligible("texts", "updated", changes={"text_de": {
            "before": "Dublin-Fälle nach Italien: Warum hält der Stopp an?",
            "after": "Dublin-Fälle nach Italien. Warum hält der Stopp an?"}}))
        self.assertTrue(eligible("texts", "updated", changes={"text_de": {"before": "-5", "after": "5"}}))

    def test_translation_replacing_a_copy_of_another_language_is_not_news(self):
        record = SimpleNamespace(state_name_de="Erledigt", state_name_fr="Liquidé", state_name_it="Liquidato")
        self.assertFalse(eligible("affairs", "updated", changes={"state_name_it": {"before": "Liquidé", "after": "Liquidato"}},
                                  record=record))
        text = SimpleNamespace(text_de="Der Bundesrat wird beauftragt", text_fr="Le Conseil fédéral est prié",
                               text_it="Il Consiglio federale è incaricato", text_date=None)
        self.assertFalse(eligible("texts", "updated", record=text, changes={"text_it": {
            "before": "Le Conseil fédéral est prié", "after": "Il Consiglio federale è incaricato"}}))
        # A revised translation while the German state stays the same is not news.
        revised = SimpleNamespace(state_name_de="Stellungnahme zum Vorstoss liegt vor",
                                  state_name_fr="L'avis relatif à l'intervention est disponible",
                                  state_name_it="Il parere sull'intervento è disponibile")
        self.assertFalse(eligible("affairs", "updated", record=revised, changes={"state_name_it": {
            "before": "La dichiarazione sull'intervento è disponibile", "after": "Il parere sull'intervento è disponibile"}}))
        # A real state change in German, or in every language that exists, remains news.
        self.assertTrue(eligible("affairs", "updated", record=record, changes={"state_name_de": {
            "before": "In Bearbeitung", "after": "Erledigt"}}))
        self.assertTrue(eligible("affairs", "updated", record=record, changes={
            "state_name_de": {"before": "In Bearbeitung", "after": "Erledigt"},
            "state_name_fr": {"before": "En traitement", "after": "Liquidé"},
            "state_name_it": {"before": "In trattamento", "after": "Liquidato"}}))
        geneva = SimpleNamespace(state_name_de=None, state_name_fr="En attente de réponse", state_name_it=None)
        self.assertTrue(eligible("affairs", "updated", record=geneva, changes={"state_name_fr": {
            "before": "Inscrit CA", "after": "En attente de réponse"}}))

    def test_repaired_broken_characters_are_not_news(self):
        for before, after in [("SekretÃ¤r", "Sekretär"), ("Conseil fÃ©dÃ©ral", "Conseil fédéral"),
                              ("Sekretär", "SekretÃ¤r")]:
            self.assertFalse(eligible("interests", "updated", changes={"role_name_de": {"before": before, "after": after}}))
        # A real role change written with broken characters stays news.
        self.assertTrue(eligible("interests", "updated", changes={"role_name_de": {"before": "Mitglied", "after": "SekretÃ¤r"}}))
        # Ordinary text with these letters is left untouched.
        self.assertTrue(eligible("texts", "updated", changes={"text_fr": {"before": "Â propos", "after": "À propos de rien"}}))

    def test_unknown_becoming_no_is_not_news(self):
        self.assertFalse(eligible("interests", "updated", changes={"ex_officio": {"before": None, "after": False}}))
        self.assertTrue(eligible("interests", "updated", changes={"ex_officio": {"before": None, "after": True}}))

    def test_old_dated_records_are_backfills_not_news(self):
        detected = datetime(2026, 11, 14, 16, 0, tzinfo=timezone.utc)
        old_vote = SimpleNamespace(date=datetime(2015, 5, 5, 17, 59))
        recent_vote = SimpleNamespace(date=datetime(2026, 11, 10, 9, 0))
        change = {"results_abstention": {"before": 0, "after": 1}}
        self.assertFalse(eligible("votings", "created", record=old_vote, reference=detected))
        self.assertFalse(eligible("votings", "updated", changes=change, record=old_vote, reference=detected))
        self.assertTrue(eligible("votings", "created", record=recent_vote, reference=detected))
        self.assertTrue(eligible("votings", "updated", changes=change, record=recent_vote, reference=detected))
        # Upcoming sessions and records without a date stay eligible.
        self.assertTrue(eligible("meetings", "created", record=SimpleNamespace(begin_date=datetime(2026, 12, 1)), reference=detected))
        self.assertTrue(eligible("documents", "created", record=SimpleNamespace(date=None), reference=detected))
        # Affairs are never treated as stale: a new state of an old affair is news.
        old_affair = SimpleNamespace(begin_date=datetime(2019, 3, 1), state_name_de="Erledigt")
        self.assertTrue(eligible("affairs", "updated", record=old_affair, reference=detected,
                                 changes={"state_name_de": {"before": "In Bearbeitung", "after": "Erledigt"}}))

    def test_legacy_rules_use_field_names_without_inventing_old_values(self):
        self.assertFalse(eligible("events","updated","Changed fields: position, last, details_url"))
        self.assertFalse(eligible("agendas","updated","Changed fields: item_number, item_result"))


if __name__=="__main__":unittest.main()
