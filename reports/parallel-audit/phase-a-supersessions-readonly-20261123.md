# Issue #26 — historická Fáze A a supersessions (READ-ONLY, 2026-11-23)

**Provozní záběr:** existující loucka_reconstruction,
lo-infra-db-mariadb01; pouze SELECT, bez změn produkčního nebo
pracovního archivu. Žádné nové SQL účty ani instance.

## Live SQL ověření tří historických aplikovaných dávek

Dávka rain-2009-2011-utc-midnight-reset-v1:
- 328 applied rain událostí, 328 new_value = 0.
- 328/328 současných hodnot rain odpovídá uloženému new_value.
- Historický odfiltrovaný příspěvek 175,14 mm.

Dávka rain-phaseA-june2010-corrected-20261030-v1:
- 30 applied rain událostí, všech 30 původně new_value = 0.
- Aktuálně 12/30 rain = 0.
- Zbylých 18/30 je **záměrně NULL po pozdější aplikované revizi**,
  nikoli chybějící/nezdokumentovaná nebo navrácená hodnota.
- Historický odfiltrovaný příspěvek 161,76 mm.

Dávka rain-phaseA-apply-20261030-v1:
- Dvě applied rain události, jedna rainRate událost.
- Ze dvou rain zůstává 1 původní nula; druhá je záměrně NULL
  po pozdější revizi. RainRate nadále 1/1 odpovídá původnímu
  aplikovanému new_value.
- Historický odfiltrovaný příspěvek rain: 61,22 mm.

Celkově původních 360 rain korekcí a jedna rainRate.
Z 360 rain má 341 současnou hodnotu rovnou původní nule;
**19** jich má zdokumentovanou pozdější změnu na NULL.

## Přesné vysvětlení všech 19 supersessions

Následná dávka
rain-2010-2011-phaseA-unknown-null-review-v1
má 19 applied událostí rain; vytvořeny 12.11.2026.

- 18 z původní červnové 2010 dávky, 1 z původní fáze
  rain-phaseA-apply-20261030-v1 (čas 1301295000, 2011).
- 19/19 předchozí new_value=0 odpovídá
  následnému old_value=0.
- 19/19 následné new_value je SQL NULL.
- 19/19 současná reconstruction.archive.rain je SQL NULL.
- 19/19 následné auditní state=applied.
- Důvod v auditu: odstraněný falešný srážkový příspěvek
  neprokazuje nulový skutečný lokální déšť; skutečný intervalový
  úhrn je neznámý, proto NULL.

**Nevracet těchto 19 hodnot na 0 bez nového nezávislého důkazu
a výslovně schváleného manifestu.** Nula a NULL jsou rozdílná
meteorologická i SQL tvrzení.

## Doplňkové ochranné testy

- Červenec 2021, dosavadní invariant:
  8928 archivních řádků, SUM(rain)*10 zaokrouhleno 42,567 mm
  v UTC intervalu [1625097600, 1627776000).
- Nové issue26 auditní tabulky obsahují 0 batch eventů a
  0 field eventů. Ve 2018 Q1 ani v chráněných polích rain/rainRate
  roku 2021 tedy **neexistuje žádný nový issue26 auditní zásah**.
- Není to důkaz úplné meteorologické pravdivosti všech historických
  údajů ani všech jiných zásahů mimo tento cílený výběr.

## Reprodukovatelná SQL kontrola (SELECT only)

    SELECT c.batch_key,c.variable,c.state,COUNT(*) AS events,
      SUM(c.new_value=0) AS old_batch_zero,
      SUM(CASE WHEN c.variable='rain'
            THEN (r.rain <=> c.new_value)
          WHEN c.variable='rainRate'
            THEN (r.rainRate <=> c.new_value)
          ELSE 0 END) AS currently_equal_original
    FROM loucka_reconstruction.reconstruction_changes c
    JOIN loucka_reconstruction.archive r ON r.dateTime=c.target_time
    WHERE c.batch_key IN (
      'rain-2009-2011-utc-midnight-reset-v1',
      'rain-phaseA-june2010-corrected-20261030-v1',
      'rain-phaseA-apply-20261030-v1'
    )
    GROUP BY c.batch_key,c.variable,c.state;

    SELECT a.batch_key AS previous_batch,b.batch_key AS superseding_batch,
      COUNT(*) AS supersessions,
      SUM(a.new_value <=> b.old_value) AS linked_values,
      SUM(b.new_value IS NULL) AS unknown_null,
      SUM(r.rain <=> b.new_value) AS current_matches_new
    FROM loucka_reconstruction.reconstruction_changes a
    JOIN loucka_reconstruction.reconstruction_changes b
      ON b.target_time=a.target_time AND b.variable='rain' AND b.id<>a.id
    JOIN loucka_reconstruction.archive r ON r.dateTime=a.target_time
    WHERE a.batch_key IN (
      'rain-phaseA-june2010-corrected-20261030-v1',
      'rain-phaseA-apply-20261030-v1'
    )
      AND a.variable='rain'
      AND NOT (r.rain <=> a.new_value)
    GROUP BY a.batch_key,b.batch_key;

    SELECT ROUND(SUM(COALESCE(rain,0))*10,3) AS july_mm
    FROM loucka_reconstruction.archive
    WHERE dateTime>=1625097600 AND dateTime<1627776000;

## Rozhodnutí

Historická fáze A i 19 pozdějších NULL supersessions jsou
ve sledovaných batchích konzistentní s aktuálním archive a
auditní historií. Nevytvářet žádný nový SQL UPDATE pro
již známé stavy. Zachovat explicitní per-batch owner approval
pro případné budoucí ověřené návrhy.

Denní extrémy/aggregates se neřeší ručně, přepočítá je
WeeWX po případném dokončení rekonstrukce.
Zálohy/PBS jsou mimo rozsah vlastníkovým rozhodnutím.
