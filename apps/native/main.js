const { app, BrowserWindow, shell, session } = require('electron')
const path = require('path')

function createWindow () {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    resizable: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  })

  // Enforce a strict Content-Security-Policy via header for loaded pages
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    const csp = "default-src 'self' http://localhost:8000; script-src 'self' 'unsafe-inline' http://localhost:8000; connect-src 'self' http://localhost:8000 ws://localhost:8000;";
    const headers = Object.assign({}, details.responseHeaders, {
      'Content-Security-Policy': [csp]
    })
    callback({ responseHeaders: headers })
  })

  // Load local web UI (fallback to packaged web/index.html)
  const localIndex = path.join(__dirname, '..', 'web', 'index.html')
  win.loadFile(localIndex)

  // open external links in default browser
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.whenReady().then(createWindow)
