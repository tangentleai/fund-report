import { useState } from "react"

type SearchBoxProps = {
  onSearch: (query: string) => void
}

export default function SearchBox({ onSearch }: SearchBoxProps) {
  const [value, setValue] = useState("")

  return (
    <div className="card">
      <div className="actions">
        <input
          className="input"
          value={value}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            setValue(event.target.value)
          }
          placeholder="输入基金代码或名称"
        />
        <button className="button" onClick={() => onSearch(value)}>
          搜索
        </button>
      </div>
    </div>
  )
}
