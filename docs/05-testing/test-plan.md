# Tests und Prüfung

## Rückverfolgbarkeit

Die [Akzeptanzkriterien](../02-requirements/acceptance-criteria.md) legen die fachlichen Erwartungen fest. Bekannte technische Ergebnisse stehen in [test-results.md](test-results.md). Zusätzlich zu Regressionen sind konkrete WWF-Aufgaben mit Beispieldaten, beobachtetem Verhalten, Abweichung und Entscheidung durchzuführen. Die Fach-/Betriebsabnahme ist derzeit offen.

Die regulären Backend-Tests verwenden isolierte Fixtures und Mocks. Für den folgenden Lauf sind kein PostgreSQL-Server und kein echter SMTP-Versand erforderlich. Im Projektordner mit installierter Anwendung ausführen; die Variablen gelten nur im aktuellen PowerShell-Prozess:

```powershell
$env:DATABASE_URL = 'sqlite://'
$env:JWT_SECRET_KEY = 'isolated-test-key-only'
python -B -m unittest discover -s tests -p 'test_*.py'
node tests/test_frontend.cjs
node --check app/web/app.js
node --check app/web/i18n.js
```

Node.js wird nur für die JavaScript-Prüfungen benötigt. Nach diesem Testlauf das Terminal schliessen oder die beiden Variablen entfernen, bevor dort die echte Anwendung gestartet wird:

```powershell
Remove-Item Env:DATABASE_URL
Remove-Item Env:JWT_SECRET_KEY
```

Die Suite prüft unter anderem Datenmapping, Beziehungen, Klassifikation, Änderungsrelevanz, Benachrichtigungen, Kontoeinstellungen und Sync-Fortschritt. `tests/test_frontend.cjs` prüft Übersetzungen und Darstellungslogik ohne Browser. Diese Prüfungen ersetzen keine Integration mit PostgreSQL, SMTP oder OpenParlData.

## Regelqualität und Ergebnisgruppen

`python -m scripts.rule_quality` vergleicht in isolierten SQLite-Datenbanken das 50-Beispiele-Entwicklungsset mit dem festgelegten früheren Commit und der aktuellen Taxonomie. PostgreSQL wird dabei nicht verändert. Dafür werden Git-Historie und die lokale Fixture benötigt. Das Ergebnis ist eine Regression auf Entwicklungsbeispielen, keine unabhängige Expertenmessung.

`python -m scripts.verify_rule_workers` benötigt dagegen die echte, aktuell geseedete PostgreSQL-Datenbank. Der Prozess arbeitet schreibgeschützt und vergleicht das Entwicklungsset plus 250 weitere Dokumente seriell und parallel. Die temporären SQLite-Testvariablen vorher entfernen. `python -m scripts.rule_backfill_status` überprüft ebenfalls schreibgeschützt die technische Abdeckung eines abgeschlossenen Backfills.

`tests/test_affair_result_groups.py` prüft die gruppierte Trefferzahl, Pagination, unterschiedliche Tage/Körperschaften, Nummernsuche und den Erhalt aller Quelldatensätze. Frontend-Checks prüfen **Hauptthema / Unterthema**, globales Sonstiges und lokalisierte Kategorienamen. Nachweise stehen in der [Prüfung vom 13. Oktober](review-2026-10-13.md).

## Browserprüfungen

Die Skripte `tests/browser_frontend.py`, `tests/browser_membership.py` und `tests/browser_search.py` benötigen zusätzlich Python Playwright und eine passende Browserumgebung. Die bestehenden Skripte sind auf Windows/Edge beziehungsweise ihre angegebenen lokalen URLs ausgelegt. Vor dem Ausführen die Zieladresse und Voraussetzungen im jeweiligen Skript prüfen.

```powershell
python -m pip install playwright
```

`tests/browser_ui_live.cjs` ist ein lokales Diagnosewerkzeug: es lädt derzeit Playwright aus einer global installierten Artillery-Abhängigkeit unter Windows. Es ist kein portabler Bestandteil der Standardinstallation. Browserprüfungen von Konten oder Abonnements nur gegen eine isolierte Test- oder Demo-Datenbank durchführen.

## Manuelle Abnahme

1. Alle neun Listen öffnen, Filter kombinieren und verknüpfte Details prüfen.
2. Auf schmalem und breitem Bildschirm lange Details scrollen und die Schliessen-Schaltfläche prüfen.
3. Registrierung, erneute Anmeldung und Abmelden über Mailpit testen; optional Google in einer eigenen Testkonfiguration prüfen.
4. Abonnements, Einzel-Watches und mehrere Empfänger speichern; Bestätigung und Adressverifikation prüfen.
5. Pause, vollständige Abmeldung von Abonnements und Kontolöschung prüfen.
6. Sync-Fehler und Wiederaufnahme in einer gesicherten Testumgebung prüfen; Quell-/DB-Stichproben vergleichen.

Fachliche Klassifikationsqualität muss zusätzlich anhand von WWF bewerteten Beispielen geprüft werden. Historische Testnachweise stehen im [Review](../daily-review-2026-10-11.md); sie gelten für den dort angegebenen Stand.
