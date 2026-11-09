import { useCallback, useMemo, useState } from "react"
import DATA from "../viewer.json"

// Layers are redrawn from RescueSwarm_PoseSet_v0.1/annotations/coco/*.json
// (17 COCO keypoints, segmentation polygon, posture label per person).
const SK = [[16,14],[14,12],[17,15],[15,13],[12,13],[6,12],[7,13],[6,7],[6,8],[7,9],[8,10],[9,11],[2,3],[1,2],[1,3],[2,4],[3,5],[4,6],[5,7]]

const ALT = {
  "rs_000001.jpg": "Synthetic aerial render on rubble with two people: one lying, one upright",
  "rs_000002.jpg": "Mass-casualty exercise photo: a responder walks past a training casualty lying on grass",
  "rs_000011.jpg": "Synthetic aerial render on grass with two people: one crouching, one lying",
  "rs_000012.jpg": "Synthetic aerial render on asphalt with one seated person",
  "rs_000014.jpg": "Synthetic aerial render on dirt with one person lying",
  "rs_000015.jpg": "Field exercise photo: four people standing in front of a relief tent",
  "rs_000272.jpg": "Rescue exercise on a snow slope, seen from above",
  "rs_000274.jpg": "Close view of a responder crouching over a training casualty",
}

const pad = (n) => (n < 10 ? "0" + n : String(n))
const src = (f) => "/images/" + f

export default function AnnotationViewer() {
  const [idx, setIdx] = useState(0)
  const [layers, setLayers] = useState({ kp: true, ol: true, lb: true })
  const [hover, setHover] = useState(-1)
  const fr = DATA[idx]
  const raw = !layers.kp && !layers.ol && !layers.lb

  const go = useCallback((d) => { setHover(-1); setIdx((i) => (i + d + DATA.length) % DATA.length) }, [])
  const toggle = (k) => setLayers((l) => ({ ...l, [k]: !l[k] }))
  const setRaw = () => setLayers(raw ? { kp: true, ol: true, lb: true } : { kp: false, ol: false, lb: false })

  const onKey = (e) => {
    if (e.target.tagName === "INPUT") return
    const k = e.key.toLowerCase()
    if (e.key === "ArrowRight") { e.preventDefault(); go(1) }
    else if (e.key === "ArrowLeft") { e.preventDefault(); go(-1) }
    else if (k === "k") toggle("kp")
    else if (k === "o") toggle("ol")
    else if (k === "p") toggle("lb")
    else if (k === "r") setRaw()
  }

  const people = fr.P
  const visibleKp = useMemo(() => people.map((p) => { let n = 0; for (let i = 0; i < 17; i++) if (p.k[i * 3 + 2] > 0) n++; return n }), [people])
  const r = Math.max(fr.w, fr.h) / 150
  const fs = Math.max(fr.w, fr.h) / 42
  const tone = (p) => (p.p === "lying" ? "var(--warn)" : "var(--acc)")
  const dim = (i) => (hover >= 0 && hover !== i ? 0.18 : 1)

  const Toggle = ({ on, onClick, label, hint, kbd }) => (
    <button type="button" className={"toggle" + (on ? " is-on" : "")} aria-pressed={on} onClick={onClick} title={hint}>
      <span className="toggle-dot" aria-hidden="true" />
      {label}
      <kbd aria-hidden="true">{kbd}</kbd>
    </button>
  )

  return (
    <div className="viewer" role="region" aria-label="Interactive annotation viewer" onKeyDown={onKey}>
      <div className="viewer-main">
        <div className="toggles" role="group" aria-label="Annotation layers">
          <Toggle on={raw} onClick={setRaw} label="Raw image" hint="Hide every annotation layer" kbd="R" />
          <Toggle on={layers.kp} onClick={() => toggle("kp")} label="Keypoints" hint="17 COCO keypoints and skeleton" kbd="K" />
          <Toggle on={layers.ol} onClick={() => toggle("ol")} label="Outline" hint="Body-outline polygon" kbd="O" />
          <Toggle on={layers.lb} onClick={() => toggle("lb")} label="Posture" hint="Posture label per person" kbd="P" />
        </div>

        <div className="stage" style={{ aspectRatio: fr.w + " / " + fr.h }}>
          <img key={fr.f} className="stage-img" src={src(fr.f)} alt={ALT[fr.f]} width={fr.w} height={fr.h} decoding="async" />
          <svg key={"s" + fr.f} className="stage-svg" viewBox={"0 0 " + fr.w + " " + fr.h} aria-hidden="true">
            {layers.ol && people.map((p, i) => {
              const pts = []
              for (let j = 0; j < p.s.length; j += 2) pts.push(p.s[j] + "," + p.s[j + 1])
              return <polygon key={"o" + i} className="layer-ol" points={pts.join(" ")} fill={tone(p)} stroke={tone(p)} style={{ opacity: dim(i) }} vectorEffect="non-scaling-stroke" />
            })}
            {layers.kp && people.map((p, i) => {
              const P = (n) => [p.k[(n - 1) * 3], p.k[(n - 1) * 3 + 1], p.k[(n - 1) * 3 + 2]]
              return (
                <g key={"k" + i} className="layer-kp" style={{ opacity: dim(i) }}>
                  {SK.map(([a, b], j) => {
                    const A = P(a), B = P(b)
                    if (A[2] <= 0 || B[2] <= 0) return null
                    return <line key={j} x1={A[0]} y1={A[1]} x2={B[0]} y2={B[1]} stroke={tone(p)} strokeWidth={2.5} vectorEffect="non-scaling-stroke" strokeLinecap="round" strokeDasharray={A[2] === 1 || B[2] === 1 ? "5 4" : undefined} />
                  })}
                  {Array.from({ length: 17 }, (_, j) => {
                    const v = p.k[j * 3 + 2]
                    if (v <= 0) return null
                    return <circle key={"j" + j} cx={p.k[j * 3]} cy={p.k[j * 3 + 1]} r={r} fill={v === 2 ? "#05070A" : "transparent"} stroke={tone(p)} strokeWidth={2} strokeOpacity={v === 2 ? 1 : 0.7} vectorEffect="non-scaling-stroke" />
                  })}
                </g>
              )
            })}
            {layers.lb && people.map((p, i) => {
              const text = p.p === "lying" ? "LYING / CASUALTY" : p.p.toUpperCase()
              const w = text.length * fs * 0.62 + fs * 0.9
              const x = Math.min(Math.max(p.b[0], 0), fr.w - w)
              const y = Math.max(p.b[1] - fs * 1.5, 0)
              return (
                <g key={"l" + i} className="layer-lb" style={{ opacity: dim(i) }}>
                  <rect x={x} y={y} width={w} height={fs * 1.45} fill="#05070A" fillOpacity={0.88} stroke={tone(p)} strokeWidth={1} vectorEffect="non-scaling-stroke" />
                  <text x={x + fs * 0.45} y={y + fs * 1.05} fill={tone(p)} fontSize={fs} fontFamily="JetBrains Mono, monospace" fontWeight={600}>{text}</text>
                </g>
              )
            })}
          </svg>
          <div className="stage-scan" aria-hidden="true" />
          <div className="stage-tag" aria-hidden="true">{fr.f + "  " + fr.w + "×" + fr.h}</div>
          <div className="stage-corners" aria-hidden="true"><i /><i /><i /><i /></div>
        </div>

        <div className="thumbs-row">
          <button type="button" className="nav-arrow" onClick={() => go(-1)} aria-label="Previous image">←</button>
          <ul className="thumbs" aria-label="Choose an image">
            {DATA.map((d, i) => (
              <li key={d.f}>
                <button type="button" className={"thumb" + (i === idx ? " is-active" : "")} onClick={() => { setHover(-1); setIdx(i) }}
                  aria-current={i === idx ? "true" : undefined} aria-label={"Image " + (i + 1) + " of " + DATA.length + ": " + d.f + ", " + d.src}>
                  <img src={src(d.f)} alt="" loading="lazy" decoding="async" />
                  <span className={"thumb-tag" + (d.src === "real" ? "" : " is-syn")} aria-hidden="true">{d.src === "real" ? "REAL" : "SYN"}</span>
                </button>
              </li>
            ))}
          </ul>
          <button type="button" className="nav-arrow" onClick={() => go(1)} aria-label="Next image">→</button>
        </div>
      </div>

      <aside className="viewer-side" aria-label="Annotation details">
        <div aria-live="polite" className="side-head">
          <span className="mono-label">{"Frame " + pad(idx + 1) + " / " + pad(DATA.length)}</span>
          <span className="side-file">{fr.f}</span>
        </div>
        <div className="chips-row">
          {[fr.sp, fr.src, fr.lic].map((t) => <span key={t} className={"chip" + (t === "synthetic" ? " is-acc" : "")}>{t}</span>)}
        </div>
        <p className="side-credit">Credit: {fr.au}</p>
        <div className="side-people">
          <span className="mono-label">{people.length + (people.length === 1 ? " person" : " people")} · hover to isolate</span>
          {people.map((p, i) => (
            <button type="button" key={i} className={"person" + (hover === i ? " is-hover" : "")}
              onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(-1)} onFocus={() => setHover(i)} onBlur={() => setHover(-1)}
              aria-label={"Person " + (i + 1) + ": " + p.p + ", " + p.v.replace("_", " ") + ", occlusion " + p.o + ", " + visibleKp[i] + " of 17 keypoints, " + p.r}>
              <span className="person-dot" style={{ background: tone(p) }} aria-hidden="true" />
              <span className={"person-name" + (p.p === "lying" ? " is-warn" : "")}>{"P" + (i + 1) + "  " + p.p}</span>
              <span />
              <span className="person-meta">{p.v.replace("_", " ") + " · occlusion " + p.o + " · " + visibleKp[i] + "/17 kp · " + p.r}</span>
            </button>
          ))}
        </div>
        <div className="legend">
          <span><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="5" fill="#05070A" stroke="var(--acc)" strokeWidth="2" /></svg>visible keypoint (v=2)</span>
          <span><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="5" fill="none" stroke="var(--acc)" strokeOpacity="0.7" strokeWidth="2" /></svg>occluded keypoint (v=1)</span>
          <span><i className="legend-warn" aria-hidden="true" />lying = casualty, triage first</span>
          <span className="legend-hint">← → browse · R K O P toggle layers</span>
        </div>
      </aside>
    </div>
  )
}
