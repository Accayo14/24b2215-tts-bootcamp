#!/usr/bin/env python3
"""Rule-based Hindi text frontend (Task 2). No models, no external data.

Rewrites numbers (Indian lakh/crore system), rupee amounts, dates, times, percentages,
units and all-caps abbreviations into spoken Hindi in Devanagari. English words written
in Latin script are left untouched (that is Task 3's problem).

    python code/normalize.py --items data/val_items.csv data/eval_items.csv \
        --out predictions/t2_normalized.csv
"""
import argparse, csv, re
from pathlib import Path

ONES = ("शून्य एक दो तीन चार पाँच छह सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस "
        "बीस इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस तीस इकतीस बत्तीस तैंतीस चौंतीस "
        "पैंतीस छत्तीस सैंतीस अड़तीस उनतालीस चालीस इकतालीस बयालीस तैंतालीस चौवालीस पैंतालीस छियालीस "
        "सैंतालीस अड़तालीस उनचास पचास इक्यावन बावन तिरपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ साठ "
        "इकसठ बासठ तिरसठ चौंसठ पैंसठ छियासठ सड़सठ अड़सठ उनहत्तर सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर "
        "पचहत्तर छिहत्तर सतहत्तर अठहत्तर उन्यासी अस्सी इक्यासी बयासी तिरासी चौरासी पचासी छियासी सत्तासी "
        "अट्ठासी नवासी नब्बे इक्यानवे बानवे तिरानवे चौरानवे पंचानवे छियानवे सत्तानवे अट्ठानवे निन्यानवे").split()
assert len(ONES) == 100

MONTHS = "जनवरी फ़रवरी मार्च अप्रैल मई जून जुलाई अगस्त सितंबर अक्टूबर नवंबर दिसंबर".split()
LETTERS = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                   "ए बी सी डी ई एफ जी एच आई जे के एल एम एन ओ पी क्यू आर एस टी यू वी डब्ल्यू एक्स वाई ज़ेड".split()))
# all-caps tokens that are spoken as words, not spelled out: left in Latin script
SPOKEN_ACRONYMS = {"PIN", "NASA", "ISRO", "SIM", "OK", "COVID", "UNESCO", "NATO", "ASAP"}

CURRENCY = {"₹": "रुपये", "Rs": "रुपये", "INR": "रुपये", "रु": "रुपये", "$": "डॉलर", "€": "यूरो", "£": "पाउंड"}
MAGNITUDE = {"लाख": "लाख", "lakh": "लाख", "lakhs": "लाख", "करोड़": "करोड़", "crore": "करोड़", "crores": "करोड़",
             "हज़ार": "हज़ार", "हजार": "हज़ार", "अरब": "अरब"}
UNITS = {"km/h": "किलोमीटर प्रति घंटा", "kmph": "किलोमीटर प्रति घंटा", "km": "किलोमीटर", "kms": "किलोमीटर",
         "kg": "किलोग्राम", "kgs": "किलोग्राम", "mg": "मिलीग्राम", "g": "ग्राम", "cm": "सेंटीमीटर",
         "mm": "मिलीमीटर", "m": "मीटर", "ml": "मिलीलीटर", "L": "लीटर", "l": "लीटर", "GB": "गीगाबाइट",
         "MB": "मेगाबाइट", "KB": "किलोबाइट", "TB": "टेराबाइट", "kW": "किलोवाट", "hrs": "घंटे", "hr": "घंटे",
         "min": "मिनट", "sec": "सेकंड", "°C": "डिग्री सेल्सियस", "°F": "डिग्री फ़ारेनहाइट", "°": "डिग्री",
         "%": "प्रतिशत", "st": "", "nd": "", "rd": "", "th": ""}
TITLES = {"Dr.": "डॉक्टर", "Mr.": "मिस्टर", "Mrs.": "मिसेज़", "Ms.": "मिस", "Prof.": "प्रोफ़ेसर",
          "etc.": "इत्यादि", "No.": "नंबर"}

DIGIT_WORDS = ONES[:10]


def digits_words(s):
    return " ".join(DIGIT_WORDS[int(c)] for c in s if c.isdigit())


def _below_100000(n):
    out = []
    if n >= 1000:
        out.append(ONES[n // 1000] + " हज़ार")
        n %= 1000
    if n >= 100:
        out.append(ONES[n // 100] + " सौ")
        n %= 100
    if n:
        out.append(ONES[n])
    return " ".join(out)


def num_words(n):
    """Non-negative integer -> Hindi words, Indian grouping (hazaar, lakh, crore, arab)."""
    if n == 0:
        return ONES[0]
    if n >= 10 ** 11:
        return digits_words(str(n))
    out = []
    for size, name in ((10 ** 9, "अरब"), (10 ** 7, "करोड़"), (10 ** 5, "लाख")):
        q, n = divmod(n, size)
        if q:
            out.append(ONES[q] + " " + name)
    if n:
        out.append(_below_100000(n))
    return " ".join(out)


def number_text(raw):
    """A matched number string (commas/decimal point allowed) -> words."""
    s = raw.replace(",", "")
    if "." in s:
        whole, frac = s.split(".", 1)
        return f"{num_words(int(whole))} दशमलव {digits_words(frac)}"
    if (len(s) >= 8) or (len(s) > 1 and s.startswith("0")):   # phone-like / leading zero: digit by digit
        return digits_words(s)
    return num_words(int(s))


NUM = r"(?:\d{1,3}(?:,\d{2})*,\d{3}|\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
D = str.maketrans("०१२३४५६७८९", "0123456789")


def _date(m):
    d, mo, y = int(m[1]), int(m[2]), m[3]
    if not (1 <= d <= 31 and 1 <= mo <= 12):
        return m[0]
    y = int(y) + (2000 if len(y) == 2 else 0)
    return f"{num_words(d)} {MONTHS[mo - 1]} {num_words(y)}"


def _time(m):
    h, mi = int(m[1]), int(m[2])
    if h > 24 or mi > 59:
        return m[0]
    return f"{num_words(h)} बजे" if mi == 0 else f"{num_words(h)} बजकर {num_words(mi)} मिनट"


def _currency(m):
    sym = m["pre"] or m["post"]
    amount, unit = m["num"].replace(",", ""), MAGNITUDE.get((m["unit"] or "").strip(), "")
    word = CURRENCY[sym.strip()]
    paise = ""
    if "." in amount and not unit and word == "रुपये":
        whole, frac = amount.split(".", 1)
        amount = whole
        p = int((frac + "0")[:2])
        paise = f" {num_words(p)} पैसे" if p else ""
        body = num_words(int(whole))
    elif "." in amount:
        body = number_text(amount)
    else:
        body = num_words(int(amount)) if len(amount) < 12 else digits_words(amount)
    if unit:
        body += " " + unit
    if body == "एक" and word == "रुपये" and not paise:
        word = "रुपया"
    return f"{body} {word}{paise}"


_UNIT_RE = "|".join(re.escape(u) for u in sorted(UNITS, key=len, reverse=True))
_CUR_SYM = r"₹|Rs\.?|INR|रु\.?|\$|€|£"


def _number(m):
    base = number_text(m["num"])
    u = m["u"]
    return base + (" " + UNITS[u] if UNITS[u] else "") if u else base


def _abbr(m):
    w = m[0]
    if w in SPOKEN_ACRONYMS:
        return w
    return " ".join(LETTERS[c] for c in w)


def normalize(text: str) -> str:
    s = text.translate(D)
    s = re.sub(r"(?<!\d)(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4}|\d{2})(?!\d)", _date, s)
    s = re.sub(r"(?<![\d:])(\d{1,2}):(\d{2})(?![\d:])", _time, s)
    # currency: symbol before the amount (optionally followed by lakh/crore/...), or ₹/Rs after it
    mag = "|".join(sorted(map(re.escape, MAGNITUDE), key=len, reverse=True))
    s = re.sub(rf"(?P<pre>{_CUR_SYM})\s*(?P<num>{NUM})(?:\s*(?P<unit>{mag})(?![A-Za-z]))?(?P<post>)", _currency, s)
    s = re.sub(rf"(?P<num>{NUM})(?:\s*(?P<unit>{mag})(?![A-Za-z]))?\s*(?P<post>₹|Rs\b\.?)(?P<pre>)", _currency, s)
    for k, v in TITLES.items():
        s = re.sub(rf"(?<![A-Za-z]){re.escape(k)}", v, s)
    s = re.sub(r"(?<!\d)(\d{1,4})\s*[-–—]\s*(\d{1,4})(?!\d)",
               lambda m: f"{number_text(m[1])} से {number_text(m[2])}" if int(m[1]) < int(m[2]) else m[0], s)
    s = re.sub(rf"(?P<num>{NUM})\s*(?P<u>{_UNIT_RE})(?![A-Za-z])", _number, s)
    s = re.sub(rf"(?<![\d,.])(?P<num>{NUM})(?![\d])(?P<u>)", _number, s)
    s = re.sub(r"(?<![A-Za-z])[A-Z]{2,6}(?![A-Za-z])", _abbr, s)
    s = s.replace("+", " प्लस ").replace("&", " और ").replace("₹", " रुपये ").replace("%", " प्रतिशत ")
    s = re.sub(r"\d", lambda m: DIGIT_WORDS[int(m[0])] + " ", s)      # safety net: nothing numeric survives
    return re.sub(r"[ \t]+", " ", s).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = []
    for p in a.items:
        with open(p, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                split = "val" if r["id"].startswith("val_") else "eval"
                rows.append([r["id"], split, r["text"], normalize(r["text"])])
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "split", "text", "normalized_text"])
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {a.out}")


if __name__ == "__main__":
    main()
