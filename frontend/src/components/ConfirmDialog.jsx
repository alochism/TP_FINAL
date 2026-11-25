
import { useEffect, useRef } from 'react'

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Confirmar',
  onConfirm,
  onCancel,
  busy = false,
}) {
  const dialogRef = useRef(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return

    if (open && !dialog.open) {
      dialog.showModal()
    } else if (!open && dialog.open) {
      dialog.close()
    }
  }, [open])

  function handleCancel(event) {
    event.preventDefault()
    if (!busy) onCancel()
  }

  return (
    <dialog
      ref={dialogRef}
      className="confirm-dialog"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-message"
      onCancel={handleCancel}
    >
      <h2 id="confirm-dialog-title">{title}</h2>
      <p id="confirm-dialog-message">{message}</p>

      <div className="confirm-dialog-actions">
        <button
          type="button"
          className="button-secondary"
          onClick={onCancel}
          disabled={busy}
          autoFocus
        >
          Cancelar
        </button>

        <button
          type="button"
          onClick={onConfirm}
          disabled={busy}
        >
          {busy ? 'Procesando...' : confirmLabel}
        </button>
      </div>
    </dialog>
  )
}
