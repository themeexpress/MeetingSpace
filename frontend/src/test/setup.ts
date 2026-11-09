import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// We don't use Vitest's `globals: true`, so @testing-library/react's
// auto-cleanup detection doesn't kick in - register it explicitly.
afterEach(cleanup)

// jsdom doesn't implement HTMLDialogElement.showModal()/close() yet, even
// though every real browser we ship to does. Polyfill just enough of the
// native behaviour (toggle `open`, fire the `close` event) so component
// tests can exercise the real <dialog>-based Dialog component.
if (typeof HTMLDialogElement !== 'undefined' && !HTMLDialogElement.prototype.showModal) {
  HTMLDialogElement.prototype.showModal = function (this: HTMLDialogElement) {
    this.setAttribute('open', '')
  }
  HTMLDialogElement.prototype.close = function (this: HTMLDialogElement) {
    this.removeAttribute('open')
    this.dispatchEvent(new Event('close'))
  }
}
