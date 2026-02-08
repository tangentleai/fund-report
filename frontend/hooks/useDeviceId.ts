import { useEffect, useState } from "react"

const KEY = "device_id"

export const useDeviceId = () => {
  const [deviceId, setDeviceId] = useState<string | null>(null)

  useEffect(() => {
    if (typeof window === "undefined") return
    let id = localStorage.getItem(KEY)
    if (!id) {
      id = `user_${Math.random().toString(36).slice(2, 11)}`
      localStorage.setItem(KEY, id)
    }
    setDeviceId(id)
  }, [])

  return deviceId
}
