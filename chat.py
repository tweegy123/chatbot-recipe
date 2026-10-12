#!C:/Users/Jelly/AppData/Local/Python/pythoncore-3.14-64/python.exe
import json
import os
import sys
import random
import re
from pathlib import Path

BASE = Path(os.path.abspath(__file__)).parent
RECIPES = json.loads((BASE / "database.json").read_text(encoding="utf-8"))
PANTRY = {"salt", "pepper", "oil", "water", "sugar"} 
HELP = ('Hi! Tell me what is in your kitchen, like "I have chicken, garlic and rice". '
        'You can also ask for a recipe by name, or try "quick vegetarian meals" or "surprise me". '
        'I assume you always have salt, pepper, oil, water and sugar.')


def norm(word):
    """Crude singularizer so 'eggs' matches 'egg' and 'tomatoes' matches 'tomato'."""
    if word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith("oes"):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


def tokens(text):
    return [norm(w) for w in re.findall(r"[a-z]+", text.lower())]


KEYNAME = {}
for r in RECIPES: 
    r["_name_words"] = set(tokens(r["name"]))
    for ing in r["ingredients"]:
        ing["_key"] = tokens(ing["name"])[0]  
        KEYNAME.setdefault(ing["_key"], ing["name"])
VOCAB = {i["_key"] for r in RECIPES for i in r["ingredients"]} - PANTRY


def card(r, have=None):
    data = {"name": r["name"], "time": r["time"], "servings": r["servings"], "tags": r["tags"],
            "ingredients": [f'{i["qty"]} {i["name"]}' for i in r["ingredients"]], "steps": r["steps"]}
    if have is not None:
        needed = [i for i in r["ingredients"] if i["_key"] not in PANTRY]
        data["have"] = [i["name"] for i in needed if i["_key"] in have]
        data["missing"] = [i["name"] for i in needed if i["_key"] not in have]
    return data


def find_by_ingredients(have, pool, limit=5):
    ready, close = [], []
    for r in pool:
        needed = [i for i in r["ingredients"] if i["_key"] not in PANTRY]
        hits = sum(i["_key"] in have for i in needed)
        if hits:
            missing = len(needed) - hits
            (ready if missing == 0 else close).append((-hits, missing, r["time"], r))
    ready.sort(key=lambda t: t[:3])  
    close.sort(key=lambda t: t[:3])
    ready = [t[3] for t in ready][:4]
    close = [t[3] for t in close][:limit - len(ready)]
    return ready, close


def reply_to(message):
    toks = tokens(message)
    words = set(toks)
    have = words & VOCAB
    cue = bool(words & {"recipe", "make", "cook", "how", "show"})

    if not toks or (words & {"hi", "hello", "hey", "help"} and not have):
        return {"reply": HELP}

    #1.Recipe by name
    for r in RECIPES:
        distinct = {w for w in r["_name_words"] if w not in VOCAB and len(w) > 3}
        full = r["_name_words"] <= words
        if (full and (distinct or cue or not (have - r["_name_words"]))) or (distinct & words and (cue or not have)):
            return {"reply": f"Here is how to make {r['name']}:", "recipes": [card(r)], "full": True}

    # 2.Filters sa mga Diet Meals for Good healths
    pool, filters = RECIPES, []
    for diet in ("vegan", "vegetarian"):
        if diet in words:
            pool = [r for r in pool if diet in r["tags"]]
            filters.append(diet)
            break
    m = re.search(r"(\d+)\s*(?:min|minute)", message.lower())
    limit = int(m.group(1)) if m else (30 if words & {"quick", "fast"} else None)
    if limit:
        pool = [r for r in pool if r["time"] <= limit]
        filters.append(f"under {limit} minutes")

    # 3.Surprise me 'randoms for walang maisip na maluto'
    if words & {"surprise", "random"} and pool:
        return {"reply": "How about this one?", "recipes": [card(random.choice(pool))], "full": True}

    # 4. Search Find the igredients 'finder'
    if have:
        ready, close = find_by_ingredients(have, pool)
        if ready or close:
            names = sorted(KEYNAME[k] for k in have)
            text = ", ".join(names[:-1]) + (" and " if len(names) > 1 else "") + names[-1]
            if ready and close:
                msg = f"With {text}, you can cook these right now, plus a few you are close to:"
            elif ready:
                msg = f"With {text}, you can cook these right now:"
            else:
                best = sum(i["_key"] in have for i in close[0]["ingredients"])
                msg = (f"Nothing is fully ready yet, but these use {text} and only need a few more ingredients:"
                       if best >= len(have) else f"No recipe uses all of those together, but these are the closest ({text}):")
            return {"reply": msg, "recipes": [card(r, have) for r in ready + close]}
        return {"reply": "None of my recipes match those yet. Try adding another ingredient."}

    # 5. Matching browse 'pang hanap hanap ba'
    if filters:
        if not pool:
            return {"reply": "No recipes match that. Try a longer time or a different diet."}
        picks = sorted(pool, key=lambda r: r["time"])[:4]
        return {"reply": f"Here are some {' and '.join(filters)} options:", "recipes": [card(r) for r in picks]}

    return {"reply": "I did not catch that. " + HELP}


def main():
    message = ""
    if os.environ.get("REQUEST_METHOD") == "POST":
        size = int(os.environ.get("CONTENT_LENGTH") or 0)
        try:
            message = json.loads(sys.stdin.buffer.read(size).decode("utf-8")).get("message", "").strip()
        except ValueError:
            message = ""
    body = json.dumps(reply_to(message[:300])).encode("utf-8")
    sys.stdout.buffer.write(b"Content-Type: application/json; charset=utf-8\r\n\r\n" + body)


if __name__ == "__main__":
    main()