const { contextBridge, shell } = require('electron')

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
  }
})
