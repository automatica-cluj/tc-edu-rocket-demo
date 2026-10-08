# Textele pentru voce

Generat de `python3 tools/make_voice_texts.py` din `rocket_demo/mission.py`. Nu edita
de mână: schimbă textul în `mission.py` și rulează din nou scriptul.

Pentru fiecare text de mai jos generează o voce (text-to-speech) și salveaz-o în acest
director cu **numele din titlu**, de ex. `sounds/voce/etapa_liftoff.mp3`. Merg
`.mp3`, `.ogg` sau `.wav`. Fișierele tale au prioritate față de ciornele din
`sounds/voce/ciorna/` (citite de vocea Ioana din macOS). Dacă lipsește și ciorna,
explicația e sărită, fără erori.

Verifică pronunția termenilor englezești (Go, No-Go, Launch, Stage, Hold, Abort,
scrub, Max Q, MECO, Falcon, Crew Dragon). Dacă generatorul îi citește greșit, scrie-i
cum se pronunță doar în textul dat generatorului.

## `stare_idle`

Pregătiți pentru lansare. Apăsați Go ca să începeți verificările. Înainte de orice lansare, fiecare echipă din centrul de control trebuie să spună Go.

## `statie_meteo`

Verificare: Meteo. Meteorologii verifică vântul, norii și fulgerele. Un vânt puternic la înălțime poate împinge racheta de pe traseu.

## `hold_meteo`

Hold: Meteo. Vânt prea puternic la înălțime! Așteptăm să se calmeze. În realitate, multe lansări sunt amânate din cauza vremii.

## `statie_propulsie`

Verificare: Propulsie. Echipa de propulsie verifică motoarele și rezervoarele. Racheta are nevoie de combustibil, dar și de oxigen lichid ca să-l poată arde.

## `hold_propulsie`

Hold: Propulsie. Presiunea dintr-un rezervor este prea mică. Inginerii o corectează înainte să continuăm.

## `statie_ghidare`

Verificare: Ghidare. Se verifică calculatoarele de bord și senzorii care țin racheta pe traseul corect, fără ajutorul unui pilot.

## `hold_ghidare`

Hold: Ghidare. Un senzor a trimis o valoare ciudată. Calculatorul este repornit și verificat din nou.

## `statie_comunicatii`

Verificare: Comunicații. Antenele de pe sol trebuie să primească semnalul rachetei pe tot drumul, ca echipa să știe în fiecare secundă ce se întâmplă.

## `hold_comunicatii`

Hold: Comunicații. Semnalul radio este prea slab. Se reglează antenele de la sol.

## `statie_siguranta`

Verificare: Siguranța zonei. Zona din jurul rampei și traseul peste ocean trebuie să fie libere: nicio navă și niciun avion acolo unde ar putea cădea bucăți din rachetă.

## `hold_siguranta`

Hold: Siguranța zonei. O barcă a intrat în zona interzisă! Lansarea așteaptă până pleacă. Chiar s-a întâmplat de multe ori!

## `stare_ready`

Toate echipele: Go! Directorul de zbor dă undă verde. Apăsați Launch ca să porniți numărătoarea inversă.

## `etapa_liftoff`

Decolare! Motoarele împing mai tare decât cântărește racheta, așa că ea începe să urce. La start, o rachetă ca Falcon 9 cântărește aproape 550 de tone, cam cât 90 de elefanți mari!

## `etapa_pitch`

Turnul a rămas în urmă. Racheta a trecut de turnul de lansare și începe să se încline spre est. Pentru a ajunge pe orbită contează mai mult viteza în lateral decât înălțimea, iar spre est ne ajută și rotația Pământului.

## `etapa_maxq`

Max Q: presiunea maximă. Zburăm deja mai repede decât sunetul, dar aerul este încă dens, așa că apasă cel mai tare pe rachetă. Motoarele își reduc puțin puterea ca racheta să nu fie solicitată prea mult.

## `etapa_meco`

Meco: treapta întâi se oprește. Meco vine de la Main Engine Cut-Off, adică oprirea motoarelor principale. În doar două minute și jumătate au ars aproape 400 de tone de combustibil și oxigen! Au mai rămas doar câteva zeci de tone, păstrate pentru aterizare.

## `etapa_separation`

Separarea treptelor. Treapta întâi, acum aproape goală, se desprinde. Fără greutatea ei, restul rachetei accelerează mult mai ușor. De aceea rachetele au mai multe trepte!

## `etapa_stage2`

Pornește treapta a doua. Motorul treptei a doua se aprinde. Are o duză mult mai mare, construită special pentru vid, unde aproape nu mai există aer.

## `etapa_les`

Turnul de salvare se desprinde. Pe vârful capsulei e un mic turn cu motoare-rachetă. Dacă ceva nu merge bine, el trage capsula cu astronauții departe de rachetă. Acum suntem destul de sus ca, la nevoie, capsula să se desprindă și fără el, așa că îl aruncăm: ar fi doar greutate în plus. (Capsula Crew Dragon nu are turn: motoarele ei de salvare sunt chiar în pereții capsulei.)

## `etapa_speed`

Câștigăm viteză. Racheta aproape nu mai urcă, ci accelerează pe orizontală. Pe orbită, nava cade încontinuu spre Pământ, dar merge atât de repede încât îl ratează mereu. Pentru asta e nevoie de aproape douăzeci și opt de mii de kilometri pe oră!

## `etapa_landing`

Treapta întâi a aterizat! Între timp, prima treaptă s-a întors și a aterizat vertical pe o platformă din ocean. Unele rachete moderne își refolosesc treptele, ca un avion, iar lansările devin mai ieftine.

## `stare_scrub`

Lansare anulată (scrub). Lansarea a fost oprită înainte de decolare. Nu e un eșec: e mai bine să încerci altă dată decât să riști. Apăsați Go pentru o nouă încercare.

## `stare_abort`

Abort! Salvăm echipajul. Sistemul de salvare a desprins capsula de rachetă. Capsula coboară cu parașute, iar astronauții sunt în siguranță. Siguranța echipajului e cea mai importantă! Apăsați Go pentru o nouă misiune.

## `stare_orbit`

Misiune îndeplinită! Felicitări, echipă! Capsula este pe orbită la aproximativ 200 de kilometri deasupra Pământului și face un ocol complet în aproximativ 90 de minute. Apăsați Go pentru o nouă misiune.
