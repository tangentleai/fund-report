import type { ReactNode } from "react"

import "./globals.css"

export const metadata = {
  title: "基金播客 MVP",
  description: "基金季报观点播客解读"
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="container">{children}</div>
      </body>
    </html>
  )
}
