import { useEffect, useRef, useState } from "react"

// rs_000002.jpg: positions are % of the photo; facts come from annotations/coco/person_keypoints_train.json
// and LICENSE_LEDGER.csv.
const SPOTS = [
  { x: 18, y: 30, head: "Upright · 17 keypoints", line: "The walking responder is labelled upright, oblique view, with all 17 keypoints visible." },
  { x: 54, y: 64, head: "Lying · casualty", line: "The training casualty is labelled lying, with 16 of 17 keypoints visible. Lying people are flagged first.", warn: true, up: true, left: true },
  { x: 80, y: 26, head: "Real photo · public domain", line: "One of 150 Wikimedia Commons photos. Its labels are YOLOv8n-pose pre-labels, not yet human-reviewed.", left: true },
]

export default function PhotoSpots() {
  const frame = useRef(null)
  const ring = useRef(null)
  const [pinned, setPinned] = useState(-1)
  const [hover, setHover] = useState(-1)
  const [ringOn, setRingOn] = useState(false)
  const leaveT = useRef(0)

  // click outside or Escape closes a pinned card
  useEffect(() => {
    if (pinned < 0) return
    const out = (e) => { if (!frame.current.contains(e.target)) setPinned(-1) }
    const esc = (e) => { if (e.key === "Escape") { setPinned(-1); setHover(-1) } }
    document.addEventListener("pointerdown", out)
    document.addEventListener("keydown", esc)
    return () => { document.removeEventListener("pointerdown", out); document.removeEventListener("keydown", esc) }
  }, [pinned])

  // "Explore" ring follows the mouse over the photo only
  const move = (e) => {
    if (e.pointerType !== "mouse") return
    const r = frame.current.getBoundingClientRect()
    ring.current.style.transform = "translate3d(" + (e.clientX - r.left) + "px," + (e.clientY - r.top) + "px,0)"
    if (!ringOn) setRingOn(true)
  }

  const enter = (i) => (e) => { if (e.pointerType !== "mouse") return; clearTimeout(leaveT.current); setHover(i) }
  const leave = (e) => { if (e.pointerType !== "mouse") return; leaveT.current = setTimeout(() => setHover(-1), 140) }

  return (
    <figure className="pspot" ref={frame} onPointerMove={move} onPointerLeave={() => setRingOn(false)} data-reveal style={{ "--d": "120ms" }}>
      <img src="/images/rs_000002.jpg" alt="Mass-casualty exercise photo: a responder walks past a training casualty lying on grass" width="960" height="640" loading="lazy" decoding="async" />
      <div className={"pspot-ring" + (ringOn && hover < 0 ? " is-on" : "") + (hover >= 0 ? " is-small" : "")} ref={ring} aria-hidden="true"><span>Explore</span></div>
      {SPOTS.map((s, i) => {
        const open = pinned === i || hover === i
        return (
          <div key={i} className={"pspot-spot" + (s.left ? " to-left" : "") + (s.up ? " to-up" : "") + (s.warn ? " is-warn" : "") + (open ? " is-open" : "")}
            style={{ "--x": s.x + "%", "--y": s.y + "%", "--xf": s.x / 100 }} onPointerEnter={enter(i)} onPointerLeave={leave}>
            <button type="button" className="pspot-dot" aria-expanded={open} aria-controls={"pspot-card-" + i}
              onClick={(e) => { e.stopPropagation(); setPinned(pinned === i ? -1 : i) }}
              onFocus={() => setHover(i)} onBlur={() => setHover(-1)}>
              <i aria-hidden="true" /><span className="sr-only">{"Note: " + s.head}</span>
            </button>
            <span className="pspot-link" aria-hidden="true" />
            <div className="pspot-card" id={"pspot-card-" + i} role="note">
              <span className="pspot-head">{s.head}</span>
              <span className="pspot-line">{s.line}</span>
            </div>
          </div>
        )
      })}
      <figcaption className="pspot-cap">rs_000002.jpg · U.S. Marine Corps photo by Lance Cpl. Ella Cadby · public domain</figcaption>
    </figure>
  )
}
