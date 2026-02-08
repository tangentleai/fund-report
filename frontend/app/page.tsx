"use client"

import { useCallback, useEffect, useRef, useState } from "react"

import FundCard from "@/components/FundCard"
import SearchBox from "@/components/SearchBox"
import { api, FundItem, PodcastItem } from "@/lib/api"
import { useDeviceId } from "@/hooks/useDeviceId"

export default function HomePage() {
  const deviceId = useDeviceId()
  const [funds, setFunds] = useState<FundItem[]>([])
  const [searchResults, setSearchResults] = useState<FundItem[]>([])
  const [loading, setLoading] = useState(false)
  const timers = useRef<Record<string, number>>({})

  const refreshFunds = useCallback(async () => {
    if (!deviceId) return
    setLoading(true)
    const res = await api.getFunds(deviceId)
    setFunds(res.data || [])
    setLoading(false)
  }, [deviceId])

  useEffect(() => {
    refreshFunds()
  }, [refreshFunds])

  const handleSearch = async (query: string) => {
    const res = await api.searchFunds(query)
    setSearchResults(res.data || [])
  }

  const handleAddFund = async (fundCode: string) => {
    if (!deviceId) return
    await api.addFund(deviceId, fundCode)
    await refreshFunds()
  }

  const handleDeleteFund = async (fundCode: string) => {
    if (!deviceId) return
    await api.deleteFund(deviceId, fundCode)
    await refreshFunds()
  }

  const updateFundPodcast = (fundCode: string, podcast: PodcastItem) => {
    setFunds((prev: FundItem[]) =>
      prev.map((fund: FundItem) =>
        fund.code === fundCode ? { ...fund, podcast } : fund
      )
    )
  }

  const pollPodcast = (fundCode: string, podcastId: number) => {
    if (timers.current[fundCode]) {
      clearInterval(timers.current[fundCode])
    }
    timers.current[fundCode] = window.setInterval(async () => {
      const res = await api.getPodcastStatus(podcastId)
      const data = res.data
      if (!data) return
      updateFundPodcast(fundCode, { id: podcastId, ...data })
      if (data.status === "completed" || data.status === "failed") {
        clearInterval(timers.current[fundCode])
      }
    }, 3000)
  }

  const handleGenerate = async (fundCode: string) => {
    if (!deviceId) return
    const res = await api.generatePodcast(fundCode, deviceId)
    const data = res.data
    if (!data) return
    updateFundPodcast(fundCode, data)
    if (data.status === "generating" && data.id) {
      pollPodcast(fundCode, data.id)
    }
  }

  return (
    <div>
      <div className="header">
        <div className="title">基金播客</div>
        <div className="muted">MVP 验证版</div>
      </div>
      <SearchBox onSearch={handleSearch} />
      {searchResults.length > 0 && (
        <div className="card">
          <div className="title">搜索结果</div>
          <div className="list">
            {searchResults.map((fund) => (
              <div key={fund.code} className="card">
                <div className="header">
                  <div>
                    <div className="title">{fund.name}</div>
                    <div className="muted">
                      {fund.manager} · {fund.fund_type || "基金"}
                    </div>
                  </div>
                  <button
                    className="button"
                    onClick={() => handleAddFund(fund.code)}
                  >
                    添加
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="title">我的基金</div>
      {loading && <div className="muted">加载中...</div>}
      {funds.length === 0 && !loading && (
        <div className="muted">暂未添加基金</div>
      )}
      <div className="list">
        {funds.map((fund) => (
          <FundCard
            key={fund.code}
            fund={fund}
            onGenerate={handleGenerate}
            onDelete={handleDeleteFund}
          />
        ))}
      </div>
    </div>
  )
}
