export default async function handler(req, res) {
  const backend = process.env.BACKEND_URL || 'http://localhost:8000'
  try {
    const r = await fetch(`${backend}/health`)
    const json = await r.json()
    res.status(200).json(json)
  } catch (err) {
    res.status(502).json({ error: String(err) })
  }
}
