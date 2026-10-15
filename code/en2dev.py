#!/usr/bin/env python3
"""Task 3: rule-based English (Latin script) -> Devanagari, as an Indian speaker would say the word.

No models, no pronunciation dictionary: a word is cut into letter groups by ordered spelling rules
(digraphs, silent letters, magic-e, soft c/g, -tion, -ing, -er ...) which give a list of Hindi
sounds, and the sounds are then written in Devanagari. A short list of irregular words
(EXCEPTIONS) covers spellings no rule can predict (one, people, the, brand names ...).

Runs after the Task 2 normalizer and only touches Latin-script words:

    python code/en2dev.py --in predictions/t2_normalized.csv --out predictions/t3_idea_text.csv
"""
import argparse, csv, re
from pathlib import Path

NUKTA = "़"
CONS = {
    "k": "क", "kh": "ख", "g": "ग", "j": "ज", "ch": "च", "T": "ट", "D": "ड", "t": "त", "th": "थ", "dh": "द",
    "n": "न", "p": "प", "f": "फ", "b": "ब", "m": "म", "y": "य", "r": "र", "l": "ल", "v": "व",
    "sh": "श", "s": "स", "h": "ह", "z": "ज" + NUKTA,
}
VOW = {  # name: (independent letter, matra)
    "a": ("अ", ""), "aa": ("आ", "ा"), "i": ("इ", "ि"), "ii": ("ई", "ी"), "u": ("उ", "ु"), "uu": ("ऊ", "ू"),
    "e": ("ए", "े"), "ai": ("ऐ", "ै"), "o": ("ओ", "ो"), "au": ("औ", "ौ"), "O": ("ऑ", "ॉ"),
}
V, C = "[aeiouy]", "[bcdfghjklmnpqrstvwxz]"
END = r"(?:#|s#|d#|r#|rs#|ing#|ly#)"          # endings that keep a magic e (make, makes, maker, making)

# (left context, letters, right context, sounds, condition)   '@' = vowel letter, '%' = consonant letter,
# '#' = word edge. The first rule that matches at a position wins; 'poly' = word has 2+ syllables.
RULES = []


def r(left, text, right, out, cond=None):
    RULES.append((left, text, right, out, cond))


# ---- a ----
r("", "ess", "age", "ai s")                                 # message
r("", "age", "#", "e j")                                  # message, village, page, stage
r("", "ation", "", "e sh a n")                            # station, education
r("#", "add", "r", "e D")                                 # address
r("", "are", "#", "e y a r")                              # care, share
r("", "air", "%", "e y a r a")                          # airport, airline
r("", "air", "", "e y a r")
r("", "ai", "", "e")                                      # train, wait
r("", "ay", "@", "e y")                                   # player, layer
r("", "ay", "", "e")                                      # play, stay
r("", "aw", "", "O")
r("", "au", "", "O")
r("", "all", "(?!@)", "O l")                              # call, hall
r("", "alk", "", "O k")                                   # walk, talk (silent l)
r("", "alf", "", "aa f")
r("", "alm", "", "aa m")
r("", "al", "#", "a l", "poly")                           # local, social, hospital
r("", "ass", "(?:#|%)", "aa s")                                 # class, pass, glass
r("", "ast", "", "aa s T")                                # fast, last, master
r("#", "a", "cc", "a")                                  # account
r("w", "a", "(?!%e#)", "O")                               # want, watch, water, war
r("", "a", "(?:nge|ble|ste|ture)#", "e")                  # change, table, taste, nature
r("", "a", "%e" + END, "e")                               # make, name, late
r("", "ar", "#", "aa r", "mono")                          # car, star
r("", "ar", "#", "a r", "poly")                           # calendar, similar
r("", "ar", "y#", "a r")                                # salary, library
r("", "ar", "@", "ai r")                                  # carry, parent
r("", "ar", "", "aa r")                                   # park, party, market
r("#", "a", "%@", "a")                                    # about, again, alone
r("", "a", "%y#", "e")                                  # baby, lady
r("", "a", "#", "aa")                                     # extra, camera
r("", "a", "", "ai")                                      # cancel, bank, flat
# ---- b ----
r("m", "b", "#", "")                                      # comb, climb (silent b)
r("", "bb", "", "b")
r("", "b", "", "b")
# ---- c ----
r("", "cc", "[ei]", "k s")                                # access, success
r("", "cc", "", "k")
r("", "ch", "", "ch")
r("", "ck", "", "k")
r("", "cial", "", "sh a l")                               # special
r("", "c", "[eiy]", "s")                                  # city, office, cancel
r("", "c", "", "k")
# ---- d ----
r("", "dge", "", "j")                                     # bridge, badge
r("", "dd", "", "D")
r("", "d", "", "D")
# ---- e ----
r("#", "ex", "@", "e g z")                                # exam, example
r("", "ention", "", "e M sh a n")                         # mention, attention
r("", "essa", "", "ai s a")                                # message, messenger
r("", "ee", "", "ii")                                     # sleep, week
r("", "ear", "(?:n|l|th|ch)", "a r")                      # learn, earth
r("", "ear", "t", "aa r")                                 # heart
r("", "ear", "", "i y a r")                               # near, clear, hear
r("", "ea", "ding", "ii")                                # reading, leading
r("", "ea", "(?:d|th|lth|sure|vy|ther)", "e")             # head, health, weather
r("", "ea", "", "ii")                                     # eat, team, speak
r("(?:[rlj]|ch|sh)", "ew", "", "uu")                      # crew, flew
r("", "ew", "", "y uu")                                   # new, few, view
r("", "eigh", "", "e")                                    # weight, eight
r("", "ei", "", "ii")
r("", "ey", "", "ii")                                     # key, money, keyboard
r("c", "el", "#", "i l")                                  # cancel
r("", "el", "#", "a l", "poly")                           # hotel, travel
r("", "en", "#", "a n", "poly")                           # open, listen
r("", "em", "#", "a m", "poly")                           # system, problem
r("", "er", "#", "a r")                                   # computer, water, paper
r("#%*", "er", "%@", "a r")                               # first syllable: service, person
r("", "er", "%@", "a r a")                                # internet, camera
r("", "er", "", "a r")
r("[td]", "ed", "#", "i D")                               # wanted, added
r("", "ed", "#", "D", "poly")                             # called, booked
r("(?:s|x|z|ch|sh|c|g)", "es", "#", "i z")                # boxes, changes
r("", "es", "#", "s", "poly")                             # notes, makes
r("@.*%", "e", "#", "")                                   # silent final e
r("", "e", "#", "ii")                                     # me, he, we, be
r("#(?:r|d)", "e", "%@", "i")                           # result, record, delete
r("", "e", "", "e")
# ---- f ----
r("", "ff", "", "f")
r("", "f", "", "f")
# ---- g ----
r("#", "gn", "", "n")
r("#", "gh", "", "g")
r("", "gh", "", "")                                       # light, night: silent gh
r("", "gg", "", "g")
r("", "g", "(?:et|ift|irl|ive|ear|eek|ib)", "g")          # get, gift, girl, give
r("", "g", "[eiy]", "j")                                  # page, magic, engine
r("", "g", "", "g")
# ---- h ----
r("#", "h", "(?:our|onest|onor|eir)", "")                 # hour, honest (silent h)
r("[r@]", "h", "#", "")                                   # oh, ah
r("r", "h", "", "")
r("", "h", "", "h")
# ---- i ----
r("", "igh", "", "aa i")                                  # high, light, flight
r("", "ition", "", "i sh a n")                            # condition
r("", "ice", "#", "i s", "poly")                          # office, service, notice
r("", "ice", "#", "aa i s", "mono")                       # ice, nice, price
r("", "ive", "#", "i v", "poly")                          # active, native
r("", "iew", "", "y uu")                                  # view, interview
r("", "ie", "#", "ii", "poly")                            # movie, cookie
r("", "ie", "#", "aa ii", "mono")                         # pie, tie
r("", "ie", "", "ii")                                     # field, believe
r("", "ing", "", "i M g")                                 # walking, shopping
r("", "ir", "%", "a r")                                   # shirt, first, girl
r("", "i", "%e" + END, "aa i")                            # line, time, online
r("%", "i", "#", "ii", "poly")                            # taxi, ski
r("", "i", "", "i")
# ---- j / k ----
r("", "j", "", "j")
r("#", "kn", "", "n")
r("", "kk", "", "k")
r("", "k", "", "k")
# ---- l ----
r("%", "le", "#", "a l")                                  # table, simple, people
r("", "ll", "", "l")
r("", "l", "", "l")
# ---- m ----
r("", "mm", "", "m")
r("", "m", "b#", "m")
r("", "m", "[bp]", "M")                                   # number, simple, camp
r("", "m", "", "m")
# ---- n ----
r("", "nn", "", "n")
r("", "n", "l", "n a")                                    # online
r("", "n", "(?:[kgcqxszjtdfv])", "M")                     # internet, weekend, think
r("", "n", "", "n")
# ---- o ----
r("", "otion", "", "o sh a n")
r("", "oor", "", "o r")
r("", "ook", "", "u k")
r("", "oo", "", "uu")                                     # school, movie, food
r("", "oa", "", "o")                                      # road, boat
r("", "oi", "", "O i")                                    # point, voice
r("", "oy", "", "O y")                                    # boy, enjoy
r("", "ou", "", "aa u")                                     # house, sound, about
r("(?:(?<!s)h|[nwc])", "ow", "", "aa u")                               # how, now, wow
r("(?:d|t|br|cr|cl|fr|g|dr)", "ow", "n", "aa u")            # down, town, brown
r("(?:[psftcv]|sh|fl)", "ow", "er", "aa u")                 # power, flower
r("", "ow", "", "o")                                      # slow, show, follow, window
r("", "orr", "", "O r")                                   # sorry
r("w", "or", "", "a r")                                   # work, world, word
r("", "ore", "#", "o r")                                  # more, store
r("", "on", "#", "a n", "poly")                           # season, reason, button
r("", "or", "#", "a r", "poly")                           # doctor, actor
r("", "or", "", "O r")                                    # order, form, north
r("", "oper", "", "O p a r")                              # proper, operator
r("", "ovie", "#", "uu v ii")
r("m", "ov", "ing", "uu v")                               # moving
r("(?:m|pr|impr|rem)", "ove", "#", "uu v")                # move, prove, improve
r("(?:c|s)", "ome", "#", "a m")                           # come, some, welcome
r("#pr", "o", "(?:j|gr|c|d|f|t)", "o")                    # project, program, process
r("", "o", "(?:d|p)y#", "O")                              # body, copy
r("", "o", "%e" + END, "o")                               # phone, home, note
r("", "o", "%@", "o")                                     # hotel, photo, local
r("", "o", "#", "o")                                      # go, hello
r("", "o", "", "O")                                       # shop, office, online
# ---- p / q ----
r("", "ph", "", "f")
r("", "pp", "", "p")
r("", "p", "", "p")
r("", "qu", "", "k v")
r("", "q", "", "k")
# ---- r ----
r("", "rr", "", "r")
r("", "r", "", "r")
# ---- s ----
r("", "sch", "e", "sh")                                 # schedule
r("", "sch", "", "s k")                                   # school
r("", "sh", "", "sh")
r("", "ssion", "", "sh a n")
r("(?:n|l)", "sion", "", "sh a n")                        # tension
r("", "sion", "", "z a n")                                # vision, decision
r("", "ss", "", "s")
r("", "sc", "[eiy]", "s")                                 # science, scene
r("(?:ew|ay|oy|ey|ee|ie|oe)", "s", "#", "z")              # news, days, movies
r("(?:%[iu]|oo|(?<![aeiou])o)", "s", "e#", "z")          # use, exercise, choose, close
r("", "s", "e#", "s")                                     # house, mouse, case
r("@", "s", "@", "z")                                     # easy, music, visit
r("", "s", "", "s")
# ---- t ----
r("", "tch", "", "ch")
r("s", "tion", "", "ch a n")                              # question
r("", "tion", "", "sh a n")                               # action, option
r("", "ture", "#", "ch a r")                              # picture, future
r("@", "th", "er", "dh")                                  # together, weather
r("", "th", "", "th")
r("", "tt", "", "T")
r("", "t", "", "T")
# ---- u ----
r("", "ution", "", "y uu sh a n")                           # solution
r("", "ui", "(?:ce|c|s|t)", "uu")                                    # fruit, suit
r("", "ui", "", "i")                                      # build
r("", "uy", "", "aa ii")
r("(?:[rlj]|ch|sh)", "ue", "#", "uu")                     # blue, true
r("", "ue", "#", "y uu")                                  # value, due
r("", "ur", "", "a r")                                    # turn, church
r("(?:[rlj]|ch|sh|s[tp]?)", "u", "%e" + END, "uu")              # rule, June
r("", "u", "%e" + END, "y uu")                            # use, cute, huge
r("(?:[rlj]|ch|sh|s[tp]?)", "u", "%@", "uu")             # student, super
r("", "u", "%@", "y uu")                                  # music, future
r("(?:[rlj]|ch|sh)", "u", "#", "uu")
r("", "u", "#", "y uu")                                   # menu
r("", "u", "", "a")                                       # cut, bus, number
# ---- v / w / x / y / z ----
r("", "v", "", "v")
r("#", "wr", "", "r")
r("#", "wh", "", "v")
r("", "w", "", "v")
r("", "x", "", "k s")
r("#", "y", "", "y")
r("%", "y", "#", "ii", "poly")                            # happy, city, party
r("%", "y", "#", "aa ii", "mono")                         # my, fly, try
r("", "y", "%e#", "aa i")                                 # type, style
r("", "y", "@", "y")
r("", "y", "", "i")                                       # system, gym
r("", "zz", "", "z")
r("", "z", "", "z")

# Irregular spellings: no rule can predict these (function words, sound-alikes, brand names).
EXCEPTIONS = {
    "the": "द", "this": "दिस", "that": "दैट", "they": "दे", "them": "दैम", "then": "दैन", "than": "दैन",
    "there": "देयर", "these": "दीज़", "those": "दोज़", "of": "ऑफ", "to": "टू", "you": "यू", "your": "योर",
    "are": "आर", "was": "वॉज़", "is": "इज़", "his": "हिज़", "has": "हैज़", "as": "ऐज़", "do": "डू",
    "who": "हू", "what": "व्हाट", "one": "वन", "two": "टू", "from": "फ्रॉम", "have": "हैव", "said": "सैड",
    "give": "गिव", "love": "लव", "above": "अबव", "done": "डन", "gone": "गॉन", "none": "नन",
    "someone": "समवन", "anyone": "एनीवन", "everyone": "एवरीवन", "money": "मनी", "month": "मंथ",
    "monday": "मंडे", "mother": "मदर", "brother": "ब्रदर", "other": "अदर", "another": "अनदर",
    "friend": "फ्रेंड", "good": "गुड", "put": "पुट", "full": "फुल", "push": "पुश", "pull": "पुल",
    "would": "वुड", "could": "कुड", "should": "शुड", "people": "पीपल", "women": "विमेन", "video": "वीडियो",
    "radio": "रेडियो", "idea": "आइडिया", "item": "आइटम", "iron": "आयरन", "year": "ईयर", "years": "ईयर्स",
    "create": "क्रिएट", "computer": "कंप्यूटर", "camera": "कैमरा", "email": "ईमेल", "wifi": "वाईफ़ाई",
    "movie": "मूवी", "ticket": "टिकट", "pizza": "पिज़्ज़ा", "tour": "टूर", "group": "ग्रुप", "soup": "सूप",
    "route": "रूट", "bye": "बाय", "sugar": "शुगर", "sure": "शोर", "guitar": "गिटार", "four": "फोर",
    "course": "कोर्स", "young": "यंग", "eye": "आई", "device": "डिवाइस", "mobile": "मोबाइल", "i": "आई", "a": "ए",
    "whatsapp": "व्हाट्सऐप", "facebook": "फ़ेसबुक", "instagram": "इंस्टाग्राम", "youtube": "यूट्यूब",
    "google": "गूगल", "iphone": "आईफ़ोन", "android": "एंड्रॉयड", "amazon": "अमेज़न", "uber": "उबर",
    # all-caps words the Task 2 normalizer leaves in Latin script (spoken as words)
    "pin": "पिन", "nasa": "नासा", "isro": "इसरो", "sim": "सिम", "ok": "ओके", "covid": "कोविड",
    "unesco": "यूनेस्को", "nato": "नाटो", "asap": "ऐसैप",
}
CONTRACTIONS = {"don't": "डोंट", "can't": "कैंट", "won't": "वोंट", "it's": "इट्स", "i'm": "आई एम",
                "that's": "दैट्स", "what's": "व्हाट्स", "let's": "लेट्स"}

_GROUPS = {"@": V, "%": C}
_COMPILED = {}
for left, text, right, out, cond in RULES:
    _COMPILED.setdefault(text[0], []).append(
        (re.compile("(?:" + "".join(_GROUPS.get(ch, ch) for ch in left) + ")$"), text,
         re.compile("".join(_GROUPS.get(ch, ch) for ch in right)), out.split(), cond))


def syllables(w: str) -> int:
    n = len(re.findall(V + "+", w))
    if n > 1 and re.search(C + "e$", w):
        n -= 1                                           # silent final e
    return n


def sounds(word: str):
    w = "#" + word + "#"
    poly = syllables(word) >= 2
    i, out = 1, []
    while i < len(w) - 1:
        for left, text, right, snd, cond in _COMPILED.get(w[i], ()):
            if not w.startswith(text, i):
                continue
            if cond == "poly" and not poly or cond == "mono" and poly:
                continue
            if not left.search(w[:i]) or not right.match(w[i + len(text):]):
                continue
            out += snd
            i += len(text)
            break
        else:
            i += 1                                       # unknown symbol: skip it
    return out


# consonant pairs Hindi spells with the inherent a instead of a conjunct (laptop, update, website, network)
SCHWA_PAIRS = {("p", "T"), ("p", "D"), ("b", "s"), ("D", "l"), ("th", "D"), ("T", "v")}


def write(snd):
    out, prev = [], None                                  # prev: 'C' = consonant waiting for a vowel
    last = None
    for k, s in enumerate(snd):
        if s in CONS:
            if prev == "C" and not ((last, s) in SCHWA_PAIRS and k < len(snd) - 1):
                out.append("्")
            out.append(CONS[s])
            prev = "C"
        elif s == "M":
            out.append("ं")
            prev = "V"
        else:
            indep, matra = VOW[s]
            out.append(matra if prev == "C" else indep)
            prev = "V"
        last = s
    return "".join(out)


def convert_word(token: str) -> str:
    low = token.lower().replace("’", "'")
    if low in CONTRACTIONS:
        return CONTRACTIONS[low]
    if low in EXCEPTIONS:
        return EXCEPTIONS[low]
    if "'" in low:                                        # John's -> John + s
        return "".join(convert_word(p) for p in low.split("'") if p)
    return write(sounds(low))


_TOKEN = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)*")


def convert_text(text: str) -> str:
    return _TOKEN.sub(lambda m: convert_word(m[0]), text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="CSV with a normalized_text column (Task 2 output)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with open(a.inp, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["idea_text"] = convert_text(row["normalized_text"])
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {a.out}")


if __name__ == "__main__":
    main()
