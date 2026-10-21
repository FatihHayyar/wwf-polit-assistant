# Erkenntnisse aus der Entwicklung

Diese technischen Erkenntnisse stützen sich auf beobachtete Projektfälle. Sie ersetzen keine persönliche Reflexion oder vollständige empirische Studie.

1. **Ein erfolgreicher Cursorlauf beweist keine Vollständigkeit, ein Vollvergleich jeden Tag ist aber zu teuer.** Nachträglich publizierte Dokumente können ältere Zeitstempel tragen, und die Quelle ändert Daten teils ohne neues Änderungsdatum. Die tragfähige Lösung kombiniert Änderungen, neue und fehlende IDs täglich mit vollständigen Vergleichen in Intervallen. Vorher die Quell-API genau prüfen: Nullwerte standen bei absteigender Sortierung vorne und verhinderten, dass Cursor vorrückten.
2. **Quell-ID und lokale Zeile sind nicht immer gleich.** Mehrfachzuordnungen von Dokumenten müssen beim Zählen und bei Watches getrennt betrachtet werden.
3. **Persistenz und politische Relevanz sind verschiedene Aufgaben.** Technische Korrekturen dürfen gespeichert werden, ohne Nutzer unnötig zu benachrichtigen.
4. **Wiederaufnahme muss vor einem grossen Livejob geprüft werden.** Batches, abgeschlossene Stufen und lokale Jobdateien bilden gemeinsam den Fortschritt.
5. **Die Zahl von Klassifikationen ist kein Gütebeleg.** Provisorische Taxonomie und Regeln benötigen fachliche Beispiele und eine unabhängige Bewertung.
6. **Ein Entwicklungsset misst nicht die Qualität.** 50/50 auf den Beispielen, an denen die Regeln verbessert wurden, stand ein Recall von 0.325 auf einem blinden Prüfset gegenüber. Sobald ein Prüfset zur Verbesserung genutzt wurde, braucht die nächste Messung ein neues; die Erstmessung wird eingefroren, auch wenn danach noch ein Fehler behoben wird.
7. **Sicherheit betrifft auch einfache Formulare.** Unterschiedliche Fehlermeldungen verraten bestehende Konten, unbegrenzte Anmeldeformulare ermöglichen E-Mail-Flut, und per GET eingelöste Links können von Mailscannern verbraucht werden.
8. **Containerisierung ist noch kein Betriebskonzept.** Secrets, SMTP, Jobpersistenz, Restore und Organisationszugriff müssen konkret validiert werden.
9. **Zusatzfunktionen vergrössern den Abnahmeumfang.** Kernaufgaben und tatsächliche WWF-Prüfung vor weiteren Komfortfunktionen priorisieren.
10. **Auftrag und Rückmeldungen regelmässig Zeile für Zeile abgleichen.** Mehrere Abonnements, Geschäftstyp und Dialogabfrage standen in Aufgabenstellung und E-Mail, wurden aber erst bei einem systematischen Abgleich als Lücke sichtbar.
11. **Eine regelbasierte Dialogabfrage ist ein ehrlicher erster Schritt.** Sie zeigt an, was sie verstanden hat, und kann nichts erfinden; ein Sprachmodell lässt sich später hinter derselben Schnittstelle vergleichen.

Die KI-Unterstützung von Code und Dokumentation ist offenzulegen und fachlich zu kontrollieren. Eigene Arbeitsstunden, persönliche Lernerfahrung und private Reflexion werden in den Kursunterlagen ergänzt und nicht aus Commit- oder Tool-Laufzeiten abgeleitet.
