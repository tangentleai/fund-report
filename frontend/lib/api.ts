const API_BASE = "http://localhost:8000/api"

export type FundItem = {
  code: string
  name: string
  full_name?: string
  manager: string
  fund_type?: string
  fund_company?: string
  establish_date?: string
  latest_scale?: string
  custodian_bank?: string
  benchmark?: string
  podcasts: PodcastItem[]
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

export type BatchImportResult = {
  success: Array<{ code: string; name?: string; reason?: string }>
  failed: Array<{ code: string; reason: string }>
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
  getAllFunds: async () => {
    const res = await fetch(`${API_BASE}/funds/all`)
    return res.json()
  },
  deleteFund: async (deviceId: string, fundCode: string) => {
    const res = await fetch(
      `${API_BASE}/funds/${fundCode}?device_id=${deviceId}`,
      { method: "DELETE" }
    )
    return res.json()
  },
  batchImportFunds: async (fundCodes: string[]) => {
    const res = await fetch(`${API_BASE}/funds/batch-import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fund_codes: fundCodes })
    })
    return res.json()
  },
  deleteFundFromDb: async (fundCode: string) => {
    const res = await fetch(`${API_BASE}/funds/manage/${fundCode}`, {
      method: "DELETE"
    })
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: "删除失败" }))
      throw errorData
    }
    return res.json()
  },
  generatePodcast: async (fundCode: string, deviceId: string, reportPeriod?: string) => {
    const res = await fetch(`${API_BASE}/podcasts/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fund_code: fundCode, device_id: deviceId, report_period: reportPeriod })
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
  },
  deletePodcast: async (id: number) => {
    const res = await fetch(`${API_BASE}/podcasts/${id}`, {
      method: "DELETE"
    })
    return res.json()
  },
  getReportViewpoint: async (fundCode: string, reportPeriod: string) => {
    const res = await fetch(`${API_BASE}/funds/${fundCode}/report/${reportPeriod}`)
    return res.json()
  }
}
