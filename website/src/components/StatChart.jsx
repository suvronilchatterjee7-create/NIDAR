import { useState } from "react"
import { BARS, STACKS } from "../data.js"
import { useInViewOnce } from "../effects.js"

const SEG = ["var(--acc)", "#6B7D95", "#3A4757"]

export default function StatChart({ kind }) {
  const [ref, seen] = useInViewOnce(0.3)
  const [hot, setHot] = useState(null)

  if (BARS[kind]) {
    const d = BARS[kind]
    const max = Math.max(...d.rows.map((r) => r.pct))
    const summary = d.rows.map((r) => r.label + " " + r.value + " " + d.unit + " (" + r.pct + "%)").join(", ")
    return (
      <div ref={ref} className="chart" role="img" aria-label={summary}>
        {d.rows.map((r, i) => (
          <div key={r.label} className={"bar-row" + (hot === i ? " is-hot" : "") + (hot !== null && hot !== i ? " is-dim" : "")}
            onMouseEnter={() => setHot(i)} onMouseLeave={() => setHot(null)}>
            <div className="bar-label">
              <span className={r.warn ? "is-warn" : ""}>{r.label}</span>
              <span className="bar-val"><b className={r.warn ? "is-warn" : ""}>{r.pct.toFixed(1)}%</b> {r.value}</span>
            </div>
            <div className="bar-track">
              <div className="bar-fill" style={{
                width: (seen ? (r.pct / max) * 100 : 0) + "%",
                background: r.warn ? "var(--warn)" : i === 0 ? "var(--acc)" : "#6B7D95",
                transitionDelay: i * 90 + "ms",
              }} />
            </div>
          </div>
        ))}
        <span className="chart-note">{d.note}</span>
      </div>
    )
  }

  const d = STACKS[kind]
  const summary = d.stacks.map((s) => s.label + ": " + s.segs.map((g) => g.label + " " + g.value).join(", ")).join("; ")
  return (
    <div ref={ref} className="chart" role="img" aria-label={summary}>
      {d.stacks.map((s) => {
        const total = s.segs.reduce((a, g) => a + g.value, 0)
        return (
          <div key={s.label} className="stack">
            <div className="bar-label"><span>{s.label}</span><span className="bar-val">{total} {s.unit}</span></div>
            <div className="stack-track">
              {s.segs.map((g, i) => {
                const pct = (g.value / total) * 100
                return (
                  <div key={g.label} className={"stack-seg" + (hot === s.label + i ? " is-hot" : "")} title={g.label + ": " + g.value + " (" + pct.toFixed(1) + "%)"}
                    onMouseEnter={() => setHot(s.label + i)} onMouseLeave={() => setHot(null)}
                    style={{ width: (seen ? pct : 0) + "%", background: SEG[i], transitionDelay: i * 120 + "ms" }}>
                    {pct >= 20 && <span style={{ color: i === 0 ? "#05070A" : "#E8EEF5" }}>{pct.toFixed(1)}%</span>}
                  </div>
                )
              })}
            </div>
            <div className="stack-legend">
              {s.segs.map((g, i) => (
                <span key={g.label}><i style={{ background: SEG[i] }} aria-hidden="true" /><b>{g.label}</b>{g.value}</span>
              ))}
            </div>
          </div>
        )
      })}
      <span className="chart-note">{d.note}</span>
    </div>
  )
}
