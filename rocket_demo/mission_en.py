"""Explicațiile citite de vocea în engleză (`voice_language = "en"`).

Pagina web și LCD-ul rămân în română; doar vocea vorbește engleză. Fiecare text
traduce explicația cu aceeași cheie din `mission.voice_texts()`. Când schimbi un text
în `mission.py`, schimbă-l și aici, apoi rulează `python3 tools/make_voice_texts.py`.

Textele sunt scrise ca să fie citite: fără simboluri, cu unitățile în cuvinte.
"""

from __future__ import annotations

VOICE_EN: dict[str, str] = {
    "stare_idle": (
        "Ready for launch. Press Go to start the checks. Before every launch, each team "
        "in mission control has to say Go."
    ),
    "statie_meteo": (
        "Weather check. The weather team checks the wind, the clouds and lightning. "
        "Strong winds high up can push the rocket off course."
    ),
    "hold_meteo": (
        "Hold: weather. The winds high up are too strong! We wait for them to calm down. "
        "In real life, many launches are delayed because of the weather."
    ),
    "statie_propulsie": (
        "Propulsion check. The propulsion team checks the engines and the tanks. The "
        "rocket needs fuel, but also liquid oxygen to burn it."
    ),
    "hold_propulsie": (
        "Hold: propulsion. The pressure in one of the tanks is too low. The engineers fix "
        "it before we continue."
    ),
    "statie_ghidare": (
        "Guidance check. We check the onboard computers and the sensors that keep the "
        "rocket on the right path, with no pilot needed."
    ),
    "hold_ghidare": (
        "Hold: guidance. A sensor sent a strange reading. The computer is restarted and "
        "checked again."
    ),
    "statie_comunicatii": (
        "Communications check. The antennas on the ground must receive the rocket's "
        "signal all the way up, so the team knows what is happening every second."
    ),
    "hold_comunicatii": (
        "Hold: communications. The radio signal is too weak. The ground antennas are "
        "being adjusted."
    ),
    "statie_siguranta": (
        "Range safety check. The area around the launch pad and the path over the ocean "
        "must be clear: no ships and no planes where pieces of the rocket could fall."
    ),
    "hold_siguranta": (
        "Hold: range safety. A boat has entered the restricted area! The launch waits "
        "until it leaves. This has really happened many times!"
    ),
    "stare_ready": (
        "All teams are Go! The flight director gives the green light. Press Launch to "
        "start the countdown."
    ),
    "etapa_liftoff": (
        "Liftoff! The engines push harder than the rocket weighs, so it starts to climb. "
        "At launch, a rocket like Falcon 9 weighs almost 550 tonnes, about as much as 90 "
        "big elephants!"
    ),
    "etapa_pitch": (
        "Clear of the tower. The rocket has passed the launch tower and starts to tilt "
        "towards the east. To reach orbit, sideways speed matters more than height, and "
        "flying east, the Earth's rotation gives us a boost."
    ),
    "etapa_maxq": (
        "Max Q: maximum pressure. We are already flying faster than sound, but the air is "
        "still thick, so it pushes hardest on the rocket. The engines throttle down a "
        "little, so the rocket is not stressed too much."
    ),
    "etapa_meco": (
        "MECO: stage one shuts down. MECO stands for Main Engine Cut-Off. In just two and "
        "a half minutes, the engines burned almost 400 tonnes of fuel and oxygen! Only a "
        "few tens of tonnes are left, saved for the landing."
    ),
    "etapa_separation": (
        "Stage separation. Stage one, now almost empty, separates. Without its weight, "
        "the rest of the rocket speeds up much more easily. That's why rockets have "
        "several stages!"
    ),
    "etapa_stage2": (
        "Second stage ignition. The second stage engine lights up. It has a much bigger "
        "nozzle, built especially for the vacuum of space, where there is almost no air."
    ),
    "etapa_les": (
        "Escape tower jettison. On top of the capsule sits a small tower with rocket "
        "motors. If something goes wrong, it pulls the capsule with the astronauts away "
        "from the rocket. We are now high enough that the capsule could escape without "
        "it, so we drop it: it would only be extra weight. By the way, the Crew Dragon "
        "capsule has no tower: its escape engines are built right into its walls."
    ),
    "etapa_speed": (
        "Picking up speed. The rocket is barely climbing now; it is speeding up "
        "sideways. In orbit, a spacecraft is always falling towards the Earth, but it "
        "moves so fast that it keeps missing it. That takes almost twenty-eight thousand "
        "kilometres per hour!"
    ),
    "etapa_landing": (
        "Stage one has landed! Meanwhile, the first stage flew back and landed upright on "
        "a platform in the ocean. Some modern rockets reuse their stages, like an "
        "airplane, which makes launches cheaper."
    ),
    "stare_scrub": (
        "Launch scrubbed. The launch was stopped before liftoff. That is not a failure: "
        "it is better to try again another day than to take a risk. Press Go for a new "
        "attempt."
    ),
    "stare_abort": (
        "Abort! Saving the crew. The escape system pulled the capsule away from the "
        "rocket. The capsule comes down under parachutes, and the astronauts are safe. "
        "The crew's safety matters most! Press Go for a new mission."
    ),
    "stare_orbit": (
        "Mission accomplished! Congratulations, team! The capsule is in orbit, about 200 "
        "kilometres above the Earth, and goes all the way around it in about 90 minutes. "
        "Press Go for a new mission."
    ),
}
