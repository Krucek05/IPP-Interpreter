# IPP projekt – interpret jazyka SOL26

V tomto repozitáři najdete šablony projektů pro interpret a testovací nástroj ve všech třech
jazycích, ve kterých můžete dle zadání projekt řešit. Dále je zde dostupný překladač SOL2XML
a různé ukázkové soubory.

Aktuální stav:
- Všechny šablony i překladač SOL2XML jsou zveřejněny a považovány za stabilní. 
  Přijímáme tipy k vylepšení a především reporty chyb (na fóru nebo na discordu).
  Doporučujeme repozitář sledovat, ale na případné důležité změny budeme upozorňovat i pomocí
  aktualit z předmětu.
- Ještě budou doplněny README soubory (zejména k šablonám interpretu).

Postupně budou doplňovány také příklady programů v jazyce SOL26 i v jeho SOL-XML reprezentaci 
a také ukázky Containerfile (Dockerfile) souborů, ze kterých můžete vycházet při kontejnerizaci.

Věnujte pozornost README souborům v jednotlivých adresářích, obsahují podrobné pokyny platné
pro jednotlivé jazyky.

## Podstatné změny

Podrobným záznamem o změnách v šablonách projektu je především [historie commitů](https://git.fit.vut.cz/IPP/ipp26-project-templates/commits/branch/main) v repozitáři. Do zpráv commitů se kromě standardní krátké zprávy snažíme psát také podrobnější vysvětlení změny (pokud nejde o úplně triviální/kosmetickou změnu), je tedy vhodné si commity rozkliknout a přečíst si celý popis.

Níže jsou uvedeny (v sestupném pořadí dle data) „zásadnější“ změny, které mohou ovlivnit chování šablon (v kontextu požadavků zadání):

| Datum    | Commit    | Popis
| -------- | --------- | -----
| 26-03-27 | `be87d45` | V Py šabloně testovacího nástroje povoleno ignorovat chybová hlášení související se spouštěním procesů.
| 26-03-27 | `1dc41a1` | V PHP šabloně testovacího nástroje odstraněna pravidla zamezující spouštění nových procesů.
| 26-03-08 | `64b94c1` | V Py šabloně interpretu opravena nesprávná deserializace XML (ve specifických a námi netestovaných případech).
| 26-03-06 | `c153e76` | Úprava implementace výstupního modelu testovacího nástroje (nemá žádný dopad na strukturu či použití).
| 26-03-06 | `67fd08c` | V Py šabloně interpretu odstraněny uvozovky kolem dopředných typových anotací (v Py 3.14 není vyžadováno).
| 26-03-04 | `71dc176` | Úprava nastavení pravidel pro kontrolu komplexity kódu (nyní konzistentní mezi TS a Py).
| 26-03-04 | `9307635` | Oprava špatné požadované verze Pythonu v `pyproject.toml` souborech (zadání vyžaduje 3.14).
