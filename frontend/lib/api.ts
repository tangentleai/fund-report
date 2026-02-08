const API_BASE = "http://localhost:8000/api"

export type FundItem = {
  code: string
  name: string
  manager: string
  fund_type?: string
  podcast?: PodcastItem | null
}

export type PodcastItem = {
  id: number
  fund_code: string
  report_period: string
  title?: string
  audio_url?: string
  duration?: number
  transcript?: TranscriptItem[]
  status: string
  error_msg?: string
}

export type TranscriptItem = {
  time: number
  speaker: string
  text: string
}

export const api = {
  searchFunds: async (q: string) => {
    const res = await fetch(`${API_BASE}/funds/search?q=${encodeURIComponent(q)}`)
    return res.json()
  },
  addFund: async (deviceId: string, fundCode: string) => {
    const res = await fetch(`${API_BASE}/funds`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_id: deviceId, fund_code: fundCode })
    })
    return res.json()
  },
  getFunds: async (deviceId: string) => {
    const res = await fetch(`${API_BASE}/funds?device_id=${deviceId}`)
    return res.json()
  },
  deleteFund: async (deviceId: string, fundCode: string) => {
    const res = await fetch(
      `${API_BASE}/funds/${fundCode}?device_id=${deviceId}`,
      { method: "DELETE" }
    )
    return res.json()
  },
  generatePodcast: async (fundCode: string, deviceId: string) => {
    const res = await fetch(`${API_BASE}/podcasts/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fund_code: fundCode, device_id: deviceId })
    })
    return res.json()
  },
  getPodcast: async (id: number) => {
    const res = await fetch(`${API_BASE}/podcasts/${id}`)
    return res.json()
  },
  getPodcastStatus: async (id: number) => {
    const res = await fetch(`${API_BASE}/podcasts/${id}/status`)
    return res.json()
  }
}
