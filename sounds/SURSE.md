# Sursele sunetelor

Sunetele din acest director sunt înregistrări reale NASA, tăiate și aduse la același
volum pentru demo. NASA permite folosirea lor fără altă aprobare, cu condiția să nu
sugerăm că NASA susține proiectul și să nu folosim sigla NASA
([Media Usage Guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/)).

| Fișier | Ce se aude | Sursa |
|---|---|---|
| `all_go.mp3` | Artemis I, directorul de lansare: „At this time I give you a go to resume count and launch Artemis 1.” | [Artemis Audio](https://www.nasa.gov/artemisaudio), „Go for Launch” |
| `countdown.mp3` | Artemis I, de la T-10: „Hydrogen burn-off igniters initiate… seven, six, five, four, stage engine start, three, two, one, boosters ignition, and liftoff of Artemis One.” | [Artemis Audio](https://www.nasa.gov/artemisaudio), „Liftoff” (T-minus 10 seconds) |
| `pitch.mp3` | Artemis II, după turn: „Good roll pitch.” / „Roger, roll pitch.” (începe după 1,5 s de liniște, ca să nu se suprapună cu numărătoarea) | [Artemis Audio](https://www.nasa.gov/artemisaudio), „Liftoff!” (Artemis II) |
| `maxq.mp3` | Space Shuttle Discovery: „Discovery, go at throttle up.” (motoarele revin la putere maximă după Max-Q) | [Historical Sounds](https://www.nasa.gov/historical-sounds/), „Go at throttle up 2” |
| `meco.mp3` | Discovery: „Discovery, nominal MECO, OMS-1 not required.” | [Historical Sounds](https://www.nasa.gov/historical-sounds/), „MECO” |
| `orbit.mp3` | Discovery: „Roger, nice to be in orbit.” | [Historical Sounds](https://www.nasa.gov/historical-sounds/), „Nice to be in orbit” |
| `ignition.mp3` | vuietul real al lansării STS-131 (primele 4 s, fără voce) | [Historical Sounds](https://www.nasa.gov/historical-sounds/), „STS-131: Sound of Launch” |
| `liftoff.mp3` | vuietul real al lansării STS-131 (18 s, fără voce) | la fel |
| `engine_loop.mp3` | vuietul STS-131, buclă de 11 s fără cusătură (se repetă cât merg motoarele) | la fel |

Restul sunetelor (bip-uri, alarme, separare, aterizare, sirenă) sunt cele provizorii,
generate de `tools/make_placeholder_sounds.py`.

Clipurile sunt potrivite pentru demo-ul fără voce (ABORT scurt în ecranul de start):
`countdown` e aliniat cu numărătoarea de pe LCD doar la accelerarea implicită
(`time_scale = 4`).
