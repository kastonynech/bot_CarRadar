"""One-off: check make/model slugs against OTOMOTO (1 polite request per 1.5s) and write miniapp/src/data/cars.json."""
import json, re, sys, time, httpx
CANDIDATES = {
 "audi": "a1 a3 a4 a5 a6 a7 a8 q2 q3 q5 q7 q8 tt",
 "bmw": "seria-1 seria-2 seria-3 seria-4 seria-5 seria-6 seria-7 x1 x2 x3 x4 x5 x6 z4 i3",
 "mercedes-benz": "klasa-a klasa-b klasa-c klasa-e klasa-s cla cls gla glb glc gle glk vito sprinter",
 "volkswagen": "golf passat polo tiguan touareg arteon caddy touran t-roc t-cross jetta up sharan",
 "skoda": "octavia fabia superb kodiaq karoq rapid scala yeti kamiq",
 "toyota": "yaris corolla auris avensis rav4 camry c-hr aygo prius land-cruiser",
 "ford": "focus fiesta mondeo kuga mustang puma s-max galaxy ecosport c-max",
 "opel": "astra corsa insignia zafira mokka vectra meriva crossland grandland",
 "renault": "clio megane captur kadjar scenic laguna talisman twingo",
 "peugeot": "206 207 208 307 308 3008 508 5008 2008 407",
 "citroen": "c3 c4 c5 berlingo c4-picasso c1 c3-aircross",
 "honda": "civic accord cr-v jazz hr-v",
 "hyundai": "i10 i20 i30 i40 tucson kona santa-fe ix35",
 "kia": "ceed sportage rio sorento picanto stonic niro",
 "mazda": "3 6 cx-5 cx-3 2 mx-5 cx-30",
 "nissan": "qashqai juke micra x-trail leaf note",
 "volvo": "v40 v50 v60 v70 v90 xc40 xc60 xc70 xc90 s60 s80 s90",
 "seat": "leon ibiza ateca arona alhambra toledo",
 "fiat": "500 panda punto tipo doblo bravo",
 "tesla": "model-3 model-s model-x model-y",
 "porsche": "911 cayenne macan panamera boxster cayman",
 "land-rover": "range-rover discovery freelander defender range-rover-sport range-rover-evoque",
 "mini": "cooper countryman clubman",
 "suzuki": "swift vitara sx4 jimny",
 "dacia": "duster sandero logan",
 "alfa-romeo": "giulietta giulia 159 147 stelvio",
 "jeep": "renegade compass cherokee wrangler grand-cherokee",
 "mitsubishi": "outlander asx lancer pajero colt",
 "subaru": "forester impreza outback xv",
 "chevrolet": "cruze aveo captiva spark",
 "lexus": "rx nx is ct",
 "jaguar": "xf xe f-pace xj",
 "infiniti": "", "cupra": "formentor leon", "ds-automobiles": "", "smart": "fortwo forfour",
}
H = {"User-Agent": "Mozilla/5.0 (compatible; CarRadar/0.1; personal listing monitor)", "Accept-Language": "pl"}
def total(c, path):
    r = c.get("https://www.otomoto.pl/osobowe" + path)
    m = re.search(r'totalCount\\?":(\d+)', r.text)
    return r.status_code, (int(m.group(1)) if m else 0), str(r.url)
out = {}
with httpx.Client(timeout=20, headers=H, follow_redirects=True) as c:
    for make, models in CANDIDATES.items():
        st, n, url = total(c, f"/{make}"); time.sleep(1.5)
        if st != 200 or n == 0 or not url.rstrip("/").endswith(f"/{make}"):
            print("BAD make", make, st, n, url); continue
        good = []
        for m in models.split():
            st, n2, url = total(c, f"/{make}/{m}"); time.sleep(1.5)
            if st == 200 and n2 > 0 and url.split("?")[0].rstrip("/").endswith(f"/{m}"): good.append(m)
            else: print("bad model", make, m, st, n2)
        out[make] = good
        print("ok", make, len(good), flush=True)
json.dump(out, open("scripts/cars.json", "w"), indent=1)
