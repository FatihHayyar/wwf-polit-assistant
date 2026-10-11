import unittest
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

    def test_legacy_rules_use_field_names_without_inventing_old_values(self):
        self.assertFalse(eligible("events","updated","Changed fields: position, last, details_url"))
        self.assertFalse(eligible("agendas","updated","Changed fields: item_number, item_result"))


if __name__=="__main__":unittest.main()
