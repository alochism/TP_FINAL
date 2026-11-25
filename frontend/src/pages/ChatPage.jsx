import { useEffect, useRef, useState } from 'react'
import { apiRequest } from '../api/client'

const WELCOME = {
  role: 'assistant',
  content: 'Hola. Contame un gasto o un ingreso, o preguntame tu saldo. Por ejemplo: "Gasté 18.500 en el súper con Mercado Pago".',
}

// Cantidad de mensajes anteriores que se envian como contexto
const HISTORY_LIMIT = 20

export function ChatPage() {
  const [messages, setMessages] = useState([WELCOME])
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSubmit(event) {
    event.preventDefault()
    const message = text.trim()

    if (!message || sending) return

    // El historial solo lleva texto: las operaciones las decide el backend en cada mensaje
    const history = messages
      .filter((item) => item !== WELCOME)
      .slice(-HISTORY_LIMIT)
      .map(({ role, content }) => ({ role, content }))

    setMessages((current) => [...current, { role: 'user', content: message }])
    setText('')
    setSending(true)

    try {
      const data = await apiRequest('/chat', {
        method: 'POST',
        body: { message, history },
      })

      setMessages((current) => [
        ...current,
        { role: 'assistant', content: data.reply, registered: data.transaction_id !== null },
      ])
    
    } catch (err) {
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content:
            'No pude confirmar el resultado de la operación. ' +
            'Revisá la sección Movimientos antes de intentar nuevamente, ' +
            'para evitar registros duplicados.',
          error: true,
        },
      ])
    } finally {
      setSending(false)
    }
  }

  return (
    <section className="chat">
      <h1>Asistente</h1>

      <div className="card chat-messages" aria-live="polite">
        {messages.map((item, index) => (
          <div
            key={index}
            className={`chat-bubble chat-${item.role}${item.error ? ' chat-error' : ''}`}
          >
            {item.content}
            {item.registered && <span className="chat-badge">Registrado</span>}
          </div>
        ))}

        {sending && <div className="chat-bubble chat-assistant chat-pending">Pensando…</div>}
        <div ref={endRef} />
      </div>

      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          aria-label="Mensaje"
          placeholder="Escribí un gasto, un ingreso o una consulta"
          maxLength={1000}
          value={text}
          onChange={(event) => setText(event.target.value)}
          disabled={sending}
        />
        <button type="submit" disabled={sending || !text.trim()}>
          Enviar
        </button>
      </form>
    </section>
  )
}
