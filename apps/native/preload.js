const { contextBridge, shell } = require('electron')

// Try to require keytar if available for secure storage; fall back gracefully
let keytar = null
try {
  keytar = require('keytar')
} catch (e) {
  keytar = null
}

// Expose a minimal, safe API to the renderer for launching external URLs and fetching local status
contextBridge.exposeInMainWorld('nativeAPI', {
  openExternal: (url) => {
    if (typeof url !== 'string') return
    // basic validation: only allow http(s) or file
    if (/^https?:\/\//.test(url) || /^file:\/\//.test(url)) {
      shell.openExternal(url)
    }
  },
  getBackendHealth: async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/health')
      return { ok: res.ok, status: res.status }
    } catch (e) {
      return { ok: false, error: String(e) }
    }
  },
  // Secure storage for API keys using OS keychain via keytar when available
  setApiKey: async (service, account, apiKey) => {
    if (!keytar) return { ok: false, error: 'keytar-not-available' }
    try {
      await keytar.setPassword(service, account, apiKey)
      return { ok: true }
    } catch (e) {
      return { ok: false, error: String(e) }
    }
  },
  getApiKey: async (service, account) => {
    if (!keytar) return { ok: false, error: 'keytar-not-available' }
    try {
      const v = await keytar.getPassword(service, account)
      return { ok: true, apiKey: v }
    } catch (e) {
      return { ok: false, error: String(e) }
    }
  }
})
