import { useRef, useState } from "react"
import { prefersReducedMotion, useCountUp } from "../effects.js"

/** Button/link with a magnetic pull toward the pointer and a click ripple. */
export function MagButton({ href, children, variant = "primary", newTab, onClick, className = "", ...rest }) {
  const ref = useRef(null)
  const [ripples, setRipples] = useState([])
  const move = (e) => {
    if (prefersReducedMotion() || e.pointerType === "touch") return
    const r = ref.current.getBoundingClientRect()
    const x = (e.clientX - r.left - r.width / 2) * 0.22
    const y = (e.clientY - r.top - r.height / 2) * 0.32
    ref.current.style.setProperty("--tx", x.toFixed(1) + "px")
    ref.current.style.setProperty("--ty", y.toFixed(1) + "px")
  }
  const leave = () => { ref.current.style.setProperty("--tx", "0px"); ref.current.style.setProperty("--ty", "0px") }
  const down = (e) => {
    const r = ref.current.getBoundingClientRect()
    const id = Date.now() + Math.random()
    setRipples((rs) => [...rs, { id, x: e.clientX - r.left, y: e.clientY - r.top }])
    setTimeout(() => setRipples((rs) => rs.filter((p) => p.id !== id)), 650)
  }
  const Tag = href ? "a" : "button"
  return (
    <Tag ref={ref} href={href} className={"btn btn-" + variant + " " + className} onPointerMove={move} onPointerLeave={leave} onPointerDown={down}
      onClick={onClick} {...(newTab ? { target: "_blank", rel: "noopener noreferrer" } : {})} {...(href ? {} : { type: "button" })} {...rest}>
      <span className="btn-inner">{children}</span>
      {ripples.map((p) => <span key={p.id} className="ripple" style={{ left: p.x, top: p.y }} aria-hidden="true" />)}
    </Tag>
  )
}

export function StatChip({ value, label }) {
  const [ref, v] = useCountUp(value)
  return (
    <div className="stat-chip" ref={ref}>
      <span className="stat-num" aria-hidden="true">{v}</span>
      <span className="sr-only">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  )
}

export function CopyButton({ text, label = "Copy" }) {
  const [done, setDone] = useState(false)
  const copy = async () => {
    try { await navigator.clipboard.writeText(text); setDone(true); setTimeout(() => setDone(false), 1600) } catch { /* clipboard blocked */ }
  }
  return (
    <button type="button" className={"copy-btn" + (done ? " is-done" : "")} onClick={copy} aria-label={done ? "Copied" : label + " to clipboard"}>
      {done ? "Copied ✓" : label}
    </button>
  )
}

export function SectionHead({ num, label, title, intro, children }) {
  return (
    <header className="sec-head">
      {children}
      <div className="eyebrow" data-reveal><span className="eb-num">{num}</span><span className="eb-rule" aria-hidden="true" /><span>{label}</span></div>
      <h2 className="h2" data-reveal data-drone-target style={{ "--d": "80ms" }}>{title}</h2>
      {intro && <p className="intro" data-reveal style={{ "--d": "160ms" }}>{intro}</p>}
    </header>
  )
}

export const ICONS = {
  detect: (
    <svg viewBox="0 0 56 56" aria-hidden="true"><path d="M4 16V4h12M40 4h12v12M52 40v12H40M16 52H4V40" fill="none" stroke="#B6FF3B" strokeWidth="2" /><circle cx="28" cy="18" r="4" fill="none" stroke="#E8EEF5" strokeWidth="2" /><path d="M28 22v14M20 28l8-3 8 3M22 44l6-8 6 8" fill="none" stroke="#E8EEF5" strokeWidth="2" strokeLinecap="round" /></svg>
  ),
  kp: (
    <svg viewBox="0 0 56 56" aria-hidden="true"><g stroke="#B6FF3B" strokeWidth="2" fill="none" strokeLinecap="round"><path d="M28 12v18M18 18h20M18 18l-4 10M38 18l4 10M22 30h12M22 30l-2 10-1 10M34 30l2 10 1 10" /></g><g fill="#06080B" stroke="#B6FF3B" strokeWidth="2"><circle cx="28" cy="8" r="3" /><circle cx="18" cy="18" r="2.5" /><circle cx="38" cy="18" r="2.5" /><circle cx="14" cy="28" r="2.5" /><circle cx="42" cy="28" r="2.5" /><circle cx="22" cy="30" r="2.5" /><circle cx="34" cy="30" r="2.5" /><circle cx="20" cy="40" r="2.5" /><circle cx="36" cy="40" r="2.5" /><circle cx="19" cy="50" r="2.5" /><circle cx="37" cy="50" r="2.5" /></g></svg>
  ),
  outline: (
    <svg viewBox="0 0 56 56" aria-hidden="true"><path d="M28 3c4 0 6 3 6 6s-1 4-2 5c5 1 9 3 10 8l3 9c1 3-2 5-4 3l-4-6 0 9 2 14c0 3-4 4-5 1l-3-12h-2l-3 12c-1 3-5 2-5-1l2-14 0-9-4 6c-2 2-5 0-4-3l3-9c1-5 5-7 10-8-1-1-2-2-2-5s2-6 6-6z" fill="rgba(182,255,59,0.14)" stroke="#B6FF3B" strokeWidth="2" strokeLinejoin="round" /></svg>
  ),
  posture: (
    <svg viewBox="0 0 56 56" aria-hidden="true"><rect x="3" y="6" width="34" height="12" fill="none" stroke="#FF3B5C" strokeWidth="2" /><path d="M8 12h24" stroke="#FF3B5C" strokeWidth="2" /><circle cx="10" cy="38" r="4" fill="none" stroke="#FF3B5C" strokeWidth="2" /><path d="M14 38h14l8-4 8 4h8M28 38l6 8M36 34l-4-6" fill="none" stroke="#FF3B5C" strokeWidth="2" strokeLinecap="round" /></svg>
  ),
}
