import { useEffect, useRef, useState } from "react"
import { prefersReducedMotion } from "../effects.js"

/*
  Scroll-driven search drone.
  The hero drone hands over to a fixed overlay copy that flies a zig-zag route,
  one waypoint per [data-drone-target] headline, and points its light at the
  headline in view. Only transform/opacity are animated; positions are cached
  and re-measured on resize, font load and layout changes.
*/

const RATIO = 309 / 1400 // drone.png height / width
const clamp = (v, a, b) => Math.max(a, Math.min(b, v))
const lerp = (a, b, t) => a + (b - a) * t
const ease = (t) => t * t * (3 - 2 * t)

function textRect(el) {
  const r = document.createRange()
  r.selectNodeContents(el)
  const b = r.getBoundingClientRect()
  return { left: b.left, right: b.right, top: b.top + scrollY, bottom: b.bottom + scrollY, cy: b.top + b.height / 2 + scrollY }
}

export default function ScrollDrone() {
  const [enabled] = useState(() => !prefersReducedMotion())
  const droneEl = useRef(null)
  const beamEl = useRef(null)

  useEffect(() => {
    if (!enabled) return
    const root = document.documentElement
    root.classList.add("drone-flying")

    let targets = [], way = [], anchors = [], baseW = 460, vw = innerWidth, vh = innerHeight
    let lit = -2
    const cur = { x: 0, y: 0, s: 1, hx: 0, hy: 0, r: 0 }
    let first = true

    const measure = () => {
      vw = innerWidth; vh = innerHeight
      targets = Array.from(document.querySelectorAll("[data-drone-target]"))
      const hero = document.querySelector(".hero .drone-img")
      if (!hero || !targets.length) return
      const hb = hero.getBoundingClientRect()
      baseW = hb.width
      if (droneEl.current) droneEl.current.style.width = baseW + "px"
      const phone = vw < 810, tablet = vw < 1200
      const flyW = phone ? 110 : tablet ? 170 : 220
      const s = flyW / baseW
      const flyH = flyW * RATIO
      const maxScroll = Math.max(0, root.scrollHeight - vh)

      way = [{ x: hb.left + hb.width / 2, y: hb.top + scrollY + hb.height / 2, s: 1, hero: true }]
      anchors = [0]
      targets.forEach((el, i) => {
        if (i === 0 && el.closest(".hero")) { el._rect = textRect(el); return }
        const t = textRect(el)
        el._rect = t
        const w = t.right - t.left
        let x
        if (phone) x = vw - 16 - flyW / 2
        else {
          const side = way.length % 2 === 1 ? 0.78 : 0.22 // alternate right / left over the headline
          x = clamp(t.left + w * side, t.left + flyW / 2, Math.min(t.right, vw - 24) - flyW / 2)
          if (w < flyW * 1.4) x = clamp(t.right + flyW * 0.2, flyW / 2 + 16, vw - flyW / 2 - 24)
        }
        const y = t.top - flyH / 2 - (phone ? 46 : 74)
        way.push({ x, y, s, el })
        const a = clamp(t.top - vh * 0.45, anchors[anchors.length - 1] + 1, maxScroll)
        anchors.push(a)
      })
      if (first) { cur.x = way[0].x; cur.y = way[0].y; cur.s = 1; cur.hx = way[0].x; cur.hy = way[0].y - scrollY + hb.height * 2.8; first = false }
    }

    const setLit = (idx) => {
      if (idx === lit) return
      lit = idx
      targets.forEach((el, i) => {
        // way index k maps to target: hero waypoint (0) lights the hero h1 if it is a target
        el.classList.toggle("is-lit", i === idx)
        el.classList.toggle("drone-dim", idx >= 0 && i > idx)
      })
    }

    let raf = 0
    const tick = () => {
      raf = requestAnimationFrame(tick)
      step()
    }
    const step = () => {
      if (!way.length) return
      const sc = scrollY
      // which segment are we in?
      let i = 0
      while (i < anchors.length - 1 && sc >= anchors[i + 1]) i++
      let k = 0
      if (i < anchors.length - 1) {
        const span = anchors[i + 1] - anchors[i]
        const t = span > 0 ? clamp((sc - anchors[i]) / span, 0, 1) : 1
        k = ease(clamp((t - 0.12) / 0.76, 0, 1)) // hold briefly at each headline
      }
      const A = way[i], B = way[Math.min(i + 1, way.length - 1)]
      const tx = lerp(A.x, B.x, k), ty = lerp(A.y, B.y, k), ts = lerp(A.s, B.s, k)

      const px = cur.x
      cur.x += (tx - cur.x) * 0.14
      cur.y += (ty - cur.y) * 0.14
      cur.s += (ts - cur.s) * 0.14
      cur.r += (clamp((cur.x - px) * 0.6, -12, 12) - cur.r) * 0.12

      let active = k < 0.5 ? i : Math.min(i + 1, way.length - 1)
      const w = baseW * cur.s, h = w * RATIO
      const vx = cur.x, vy = cur.y - sc
      const srcY = vy + h * 0.08
      // Light only ever points down: once a headline has scrolled up past the drone,
      // move on to the next headline below instead of aiming back at it.
      while (active < way.length - 1 && way[active].el && way[active].el._rect.cy - sc < srcY + 24) active++
      let W = way[active]
      const below = W.hero || (W.el && W.el._rect.cy - sc >= srcY + 24)
      let hx, hy
      if (!below || W.hero || !W.el) { hx = vx; hy = srcY + h * 2.7 }
      else { const r = W.el._rect; hx = clamp(vx, r.left + 24, r.right - 24); hy = r.cy - sc }
      if (!below) W = { hero: false, el: null }
      cur.hx += (hx - cur.hx) * 0.16
      cur.hy += (hy - cur.hy) * 0.16
      cur.hy = Math.max(cur.hy, srcY + 30) // never let the cone flip upward, even mid-swing
      const dx = cur.hx - vx, dy = cur.hy - srcY
      const len = Math.max(20, Math.hypot(dx, dy))
      const ang = Math.atan2(-dx, dy) * 180 / Math.PI

      droneEl.current.style.transform = "translate3d(" + (vx - baseW / 2).toFixed(1) + "px," + (vy - (baseW * RATIO) / 2).toFixed(1) + "px,0) scale(" + cur.s.toFixed(3) + ") rotate(" + cur.r.toFixed(2) + "deg)"
      beamEl.current.style.transform = "translate3d(" + vx.toFixed(1) + "px," + srcY.toFixed(1) + "px,0) rotate(" + ang.toFixed(2) + "deg)"
      beamEl.current.style.height = len.toFixed(0) + "px"
      beamEl.current.style.width = clamp(len * 0.5, 40, 260).toFixed(0) + "px"

      // headline light
      const ti = W.hero ? targets.findIndex((el) => el.closest(".hero")) : targets.indexOf(W.el)
      setLit(ti)
      if (ti >= 0) {
        const el = targets[ti], r = el._rect
        el.style.setProperty("--lx", (cur.hx - r.left).toFixed(0) + "px")
      }
    }

    measure()
    // dev-only hook so the flight can be stepped in a paused (background) tab during testing
    if (import.meta.env.DEV) window.__sdStep = (n) => { for (let j = 0; j < n; j++) step() }
    raf = requestAnimationFrame(tick)
    const remeasure = () => { clearTimeout(remeasure.t); remeasure.t = setTimeout(measure, 120) }
    addEventListener("resize", remeasure)
    addEventListener("load", remeasure)
    document.fonts && document.fonts.ready.then(remeasure)
    const ro = new ResizeObserver(remeasure)
    ro.observe(document.body)
    return () => {
      cancelAnimationFrame(raf)
      removeEventListener("resize", remeasure)
      removeEventListener("load", remeasure)
      ro.disconnect()
      root.classList.remove("drone-flying")
      document.querySelectorAll("[data-drone-target]").forEach((el) => el.classList.remove("is-lit", "drone-dim"))
    }
  }, [enabled])

  if (!enabled) return null
  return (
    <div className="sdrone" aria-hidden="true">
      <div className="sdrone-beam" ref={beamEl} />
      <div className="sdrone-body" ref={droneEl}>
        <img src="/images/drone.png" alt="" width="1400" height="309" />
      </div>
    </div>
  )
}
