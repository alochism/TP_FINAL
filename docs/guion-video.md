# Video script (English) — approx. 6 minutes

Split between the three team members. Lines in *italics* are what is shown on screen.

---

## 1. Introduction — 30 s (Alochis)

*Title slide: Conversational Personal Finance Platform — team and tutor names.*

"Hi, we are Aguilar, Alochis and Zupan. This is our final project for the Programming Technician degree at UTN: a web app where you record your expenses and income just by writing, as you would text a friend."

## 2. The problem — 45 s (Zupan)

*Survey charts from docs/images.*

"We surveyed 47 people. Three out of four try to keep track of their money, but only one in five does it regularly. More than half forget to record expenses, and 42 percent find it tedious. Ninety percent use more than one bank account or wallet. Filling in a form for every coffee is the friction we want to remove."

## 3. Architecture — 1 min (Aguilar)

*Architecture diagram from docs/arquitectura.md.*

"Our key principle is: the agent interprets, the backend decides.
The React frontend sends each message to our FastAPI backend, together with the user's login token. The backend forwards the message to the language model, through OpenClaw locally or Gemini in production, along with a fixed list of tools. The model only chooses a tool and proposes the data. The backend then validates everything: the amount, the category, and that the account belongs to the logged-in user. Only then does it write to PostgreSQL.
The model never sees or chooses the user, so it cannot touch someone else's data. And because we use the standard OpenAI chat format, we can switch providers by changing three environment variables."

## 4. Live demo — 2 min (Alochis)

*Deployed app at finanzas-tpfinal-web.onrender.com.*

1. *Register, create the accounts "Efectivo" and "Mercado Pago".*
   "First I create my accounts. These are records only: the app never moves real money."
2. *Type: "Pagué 20 lucas de luz".*
   "I paid twenty thousand pesos for electricity, but I didn't say which account. The system doesn't guess: it asks."
3. *Answer: "Mercado Pago".* *Show the "Registrado" badge.*
   "Now it has everything, so the backend validates and records it."
4. *Type: "¿Cuánto tengo?"*
   "Queries need no confirmation, but they still require authentication."
5. *Type: "Borrá el último gasto".*
   "Deleting is not part of our first version, so the assistant says so instead of improvising."
6. *Open Movimientos and Resumen.*
   "The classic screens show the same data, calculated by the backend."
7. *Mention the navigation.*
   "We used React Router so each screen has its own URL, like /chat or /cuentas, and protected routes send you back to the login if your session has expired. The real protection is still the backend's token check."

## 5. Validation rules and audit — 45 s (Zupan)

*Show the rules table from docs/informe-final.md and an audit_logs row.*

"We don't rely on a confidence number from the model. Deterministic rules decide: a missing amount or account means we ask; a negative amount or a future date is rejected; only one write per message; and if the model is down, nothing changes.
Every message is audited: the original text, what the model understood, what the backend decided, and the transaction created."

## 6. Testing — 45 s (Aguilar)

*Run pytest; open docs/evaluacion-nl.md.*

"We have 39 automated tests, including the chat with a simulated model. We also built a set of 60 real-life phrases with their expected results: complete, incomplete, invalid, queries and out-of-scope requests. Our main metric is how many wrong operations were executed without asking for clarification."

## 7. Deployment and closing — 30 s (Alochis)

*Render dashboard.*

"The database, the backend and the frontend run on Render, defined in a single file in the repository. Next steps are transfers, budgets and recurring payments.
Thank you!"
