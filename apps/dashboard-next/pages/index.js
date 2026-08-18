import useSWR from 'swr'

const fetcher = (url) => fetch(url).then(r => r.json())

export default function Home() {
  const { data, error } = useSWR('/api/health', fetcher, { refreshInterval: 5000 })
  return (
    <main style={{ padding: 24, fontFamily: 'Segoe UI, Roboto, system-ui' }}>
      <h1>Company Dashboard (Next.js)</h1>
      <section>
        <h2>API Health</h2>
        <pre>{error ? String(error) : JSON.stringify(data, null, 2)}</pre>
      </section>
    </main>
  )
}
