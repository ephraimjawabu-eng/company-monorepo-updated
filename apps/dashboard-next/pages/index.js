import useSWR from 'swr'
import { useState, useEffect } from 'react'

const fetcher = (url) => fetch(url).then(r => r.json())

export default function Home() {
  const [baseUrl, setBaseUrl] = useState(process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000')
    const { data: health, error: healthErr } = useSWR(() => `${baseUrl}/health`, fetcher, { refreshInterval: 5000 })
  const [apiKey, setApiKey] = useState('')
  const [brief, setBrief] = useState('Build a secure fintech web app with AI analytics, a native dashboard, and strong compliance. Must be scalable and deployment-ready.')
  const [plan, setPlan] = useState(null)
  const [status, setStatus] = useState('Awaiting API call')
  const [runId, setRunId] = useState(null)
  const [logs, setLogs] = useState([])

  useEffect(()=>{
    // poll logs if a run is active
    let t
    if (runId) {
      const poll = async ()=>{
        try{
                const r = await fetch(`${baseUrl.replace(/\/$/, '')}/gateway/runs/${runId}`)
          const j = await r.json()
          setStatus(`Run ${runId} status: ${j.status}`)
          setLogs(j.logs || [])
          if (j.status === 'queued' || j.status === 'running') t = setTimeout(poll, 1500)
        }catch(e){ console.warn('poll', e) }
      }
      poll()
    }
    return ()=>{ if (t) clearTimeout(t) }
  }, [runId])

  async function callHealth() {
    setStatus('Checking ' + baseUrl + '/health...')
    try{
      const response = await fetch(`${baseUrl.replace(/\/$/, '')}/health`)
      const data = await response.json()
      setStatus('Health OK')
    }catch(err){ setStatus('Health check failed: '+String(err)) }
  }

  async function generatePlan() {
    setStatus('Generating plan...')
    try{
      const r = await fetch(`${baseUrl.replace(/\/$/, '')}/plan`, { method: 'POST', headers: { 'Content-Type':'application/json', 'x-api-key': apiKey }, body: JSON.stringify({ name: 'Client Platform', domain: 'fintech', goals: brief, constraints: 'secure, scalable', stack: 'fullstack' }) })
      const j = await r.json()
      setPlan(j)
      setStatus(`Plan generated (${j.departments?.length||0} departments)`)
    }catch(e){ setStatus('Plan failed: '+String(e)) }
  }

  async function orchestrate() {
    if (!plan) { setStatus('Generate a plan first'); return }
    setStatus('Starting orchestration...')
    try{
      const body = { name: plan.project || 'project', domain: plan.domain||'general', brief }
      const r = await fetch(`${baseUrl.replace(/\/$/, '')}/gateway/orchestrate`, { method: 'POST', headers: { 'Content-Type':'application/json', 'x-api-key': apiKey }, body: JSON.stringify(body) })
      const j = await r.json()
      if (j.run_id) {
        setRunId(j.run_id)
        setStatus('Orchestration started: ' + j.run_id)
      } else {
        setStatus('Orchestration failed: '+JSON.stringify(j))
      }
    }catch(e){ setStatus('Orchestration error: '+String(e)) }
  }

  async function generateProduct() {
    setStatus('Generating product...')
    try{
      const r = await fetch(`${baseUrl.replace(/\/$/, '')}/gateway/generate`, { method:'POST', headers:{ 'Content-Type':'application/json', 'x-api-key': apiKey }, body: JSON.stringify({ name: 'dashboard-triggered' }) })
      const j = await r.json()
      setStatus('Generate result: ' + JSON.stringify(j))
    }catch(e){ setStatus('Generate failed: '+String(e)) }
  }

  return (
    <main style={{ padding: 24, fontFamily: 'Segoe UI, Roboto, system-ui' }}>
      <h1>Company Dashboard (Next.js)</h1>

      <header style={{ marginBottom: 12 }}>
        <label style={{ display:'block', marginBottom:6 }}>Backend URL
          <input aria-label="API base URL" value={baseUrl} onChange={(e)=>setBaseUrl(e.target.value)} style={{ width: '100%', padding:8, marginTop:6 }} />
        </label>
        <label style={{ display:'block', marginBottom:6 }}>Gateway API key
          <input aria-label="API key" type="password" value={apiKey} onChange={(e)=>setApiKey(e.target.value)} style={{ width: '100%', padding:8, marginTop:6 }} />
        </label>
        <div style={{ display:'flex', gap:8, marginTop:8 }}>
          <button onClick={callHealth}>Check health</button>
          <button onClick={generatePlan}>Generate plan</button>
          <button onClick={orchestrate} disabled={!plan}>Orchestrate</button>
          <button onClick={generateProduct} disabled={!plan}>Generate product</button>
        </div>
      </header>

      <section style={{ display:'grid', gridTemplateColumns: '1fr 1fr', gap:16 }}>
        <div>
          <h2>Project Brief</h2>
          <textarea rows={8} value={brief} onChange={(e)=>setBrief(e.target.value)} style={{ width:'100%', padding:8 }} />
        </div>
        <div>
          <h2>Active Departments</h2>
          <div id="statusBox">{status}</div>
          <ul aria-live="polite">
            {plan?.departments?.map((d, i)=> (<li key={i}><strong>{d.title}</strong> <small>{d.scope}</small></li>))}
          </ul>

          <h3>Recent Logs</h3>
          <div style={{ maxHeight:300, overflow:'auto', background:'#f8f8f8', padding:8 }}>
            {logs.length===0 ? <em>No logs</em> : logs.slice(-50).map((e, i)=>(<div key={i}><small>{new Date(e.ts*1000).toLocaleTimeString()}</small> <pre style={{ display:'inline' }}>{' '}{e.msg}</pre></div>))}
          </div>
        </div>
      </section>

      <footer style={{ marginTop:20 }}>
        <small>Health: {healthErr ? String(healthErr) : JSON.stringify(health)}</small>
      </footer>
    </main>
  )
}
