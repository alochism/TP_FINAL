"""Evalua la interpretacion de lenguaje natural contra el backend real.

Uso (con el backend corriendo y el proveedor de IA configurado):
    python evaluacion/evaluar.py --url http://127.0.0.1:8000
    python evaluacion/evaluar.py --url https://finanzas-tpfinal-api.onrender.com

Crea un usuario nuevo con las cuentas de casos.json, envia cada frase a POST /chat
(sin historial, como primer mensaje) y compara lo que hizo el sistema con lo esperado.
El resultado se escribe en docs/evaluacion-nl.md.

Metrica principal: operaciones incorrectas ejecutadas sin solicitar aclaracion.
"""
import argparse
import datetime as dt
import json
import time
import unicodedata
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

ROOT = Path(__file__).resolve().parent
WRITE_TOOLS = {"create_expense", "create_income"}
TZ = ZoneInfo("America/Argentina/Buenos_Aires")


def norm(text):
    text = unicodedata.normalize("NFD", (text or "").strip().lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def setup_user(client):
    email = f"evaluacion.{int(time.time())}@correo.com"
    password = "Evaluacion1234"
    client.post("/auth/register", json={"email": email, "password": password}).raise_for_status()
    token = client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return email


def evaluate(case, result, client, names):
    """Devuelve (ok, error_critico, detalle)."""
    actions = result.get("actions", [])
    writes = [a for a in actions if a["tool"] in WRITE_TOOLS and a["status"] == "ok"]
    expected = case["esperado"]

    if expected != "registra":
        if writes:
            return False, True, "ejecuto una escritura que no correspondia"
        if expected == "consulta" and case["tool"] not in [a["tool"] for a in actions]:
            used = ", ".join(a["tool"] for a in actions) or "ninguna tool"
            return False, False, f"esperaba {case['tool']}, uso {used}"
        return True, False, "sin cambios" if expected != "consulta" else "consulta correcta"

    if not writes:
        codes = ", ".join(f"{a['tool']}:{a['status']}" for a in actions) or "pregunto sin llamar tools"
        return False, False, f"no registro ({codes})"

    tx = next((t for t in client.get("/transactions").json() if t["id"] == result["transaction_id"]), None)
    if tx is None:
        return False, True, "no se encontro el movimiento"

    problems = []
    if writes[0]["tool"] != case["tool"]:
        problems.append(f"tipo {writes[0]['tool']}")
    if abs(float(tx["amount"]) - case["monto"]) > 0.001:
        problems.append(f"monto {tx['amount']}")
    if norm(names["accounts"][tx["account_id"]]) != norm(case["cuenta"]):
        problems.append(f"cuenta {names['accounts'][tx['account_id']]}")
    if norm(names["categories"][tx["category_id"]]) != norm(case["categoria"]):
        problems.append(f"categoria {names['categories'][tx['category_id']]}")
    expected_date = (dt.datetime.now(TZ).date() + dt.timedelta(days=case["fecha"])).isoformat()
    if tx["date"] != expected_date:
        problems.append(f"fecha {tx['date']}")

    if problems:
        return False, True, "registro con datos incorrectos: " + ", ".join(problems)
    return True, False, "registro correcto"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--delay", type=float, default=7, help="segundos entre casos (limite del proveedor)")
    parser.add_argument("--salida", default=str(ROOT.parent.parent / "docs" / "evaluacion-nl.md"))
    args = parser.parse_args()

    data = json.loads((ROOT / "casos.json").read_text(encoding="utf-8"))
    client = httpx.Client(base_url=args.url.rstrip("/"), timeout=90)
    setup_user(client)

    for account in data["cuentas"]:
        client.post("/accounts", json=account).raise_for_status()
    names = {
        "accounts": {a["id"]: a["name"] for a in client.get("/accounts").json()},
        "categories": {c["id"]: c["name"] for c in client.get("/categories").json()},
    }

    rows = []
    for case in data["casos"]:
        response = client.post("/chat", json={"message": case["mensaje"], "history": []})
        result = response.json() if response.status_code == 200 else {"reply": f"HTTP {response.status_code}", "actions": []}
        ok, critical, detail = evaluate(case, result, client, names)
        rows.append((case, ok, critical, detail, result.get("reply", "")))
        print(f"{case['id']:>3} {'OK ' if ok else 'ERR'}{' (CRITICO)' if critical else ''} {case['mensaje']} -> {detail}")
        time.sleep(args.delay)

    total = len(rows)
    passed = sum(1 for r in rows if r[1])
    critical = sum(1 for r in rows if r[2])
    by_type = {}
    for case, ok, *_ in rows:
        stats = by_type.setdefault(case["esperado"], [0, 0])
        stats[0] += 1
        stats[1] += ok

    lines = [
        "# Evaluacion de la interpretacion de lenguaje natural",
        "",
        f"Fecha de ejecucion: {dt.datetime.now(TZ):%Y-%m-%d %H:%M} · Casos: {total} · "
        f"Script: `backend/evaluacion/evaluar.py` · Casos: `backend/evaluacion/casos.json`",
        "",
        "## Resultado",
        "",
        f"- Casos resueltos como se esperaba: **{passed} de {total} ({passed / total:.0%})**.",
        f"- **Operaciones incorrectas ejecutadas sin solicitar aclaracion: {critical}** (metrica principal).",
        "",
        "| Resultado esperado | Casos | Correctos |",
        "|---|---|---|",
    ]
    lines += [f"| {k} | {v[0]} | {v[1]} |" for k, v in by_type.items()]
    lines += [
        "",
        "Criterios: *registra* exige tipo, monto, cuenta, categoria y fecha correctos; *pregunta*, "
        "*rechaza* y *sin_accion* exigen que no se registre nada; *consulta* exige usar la tool de lectura esperada.",
        "",
        "## Detalle",
        "",
        "| # | Mensaje | Esperado | Resultado | Detalle | Respuesta del asistente |",
        "|---|---|---|---|---|---|",
    ]
    for case, ok, crit, detail, reply in rows:
        status = "OK" if ok else ("ERROR CRITICO" if crit else "Error")
        reply = reply.replace("|", "/").replace("\n", " ")[:160]
        lines.append(f"| {case['id']} | {case['mensaje']} | {case['esperado']} | {status} | {detail} | {reply} |")

    Path(args.salida).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n{passed}/{total} correctos · {critical} criticos · informe en {args.salida}")


if __name__ == "__main__":
    main()
