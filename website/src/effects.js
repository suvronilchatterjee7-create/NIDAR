import { useEffect, useRef, useState } from "react"

export const prefersReducedMotion = () =>
  typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches

/** Adds .is-visible to every [data-reveal] element as it scrolls into view. */
export function useRevealAll() {
  useEffect(() => {
    const els = Array.from(document.querySelectorAll("[data-reveal]"))
    if (prefersReducedMotion() || typeof IntersectionObserver === "undefined") {
      els.forEach((el) => el.classList.add("is-visible"))
      return
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("is-visible")
            io.unobserve(e.target)
          }
        })
      },
      { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
    )
    els.forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [])
}

/** Writes scroll-driven parallax offsets to every [data-parallax="speed"] element. */
export function useParallax() {
  useEffect(() => {
    if (prefersReducedMotion()) return
    const els = Array.from(document.querySelectorAll("[data-parallax]"))
    let raf = 0
    const update = () => {
      raf = 0
      const vh = window.innerHeight
      for (const el of els) {
        const speed = parseFloat(el.dataset.parallax) || 0
        const host = el.parentElement.getBoundingClientRect()
        if (host.bottom < -200 || host.top > vh + 200) continue
        const center = host.top + host.height / 2 - vh / 2
        el.style.setProperty("--py", (-center * speed).toFixed(1) + "px")
      }
    }
    const onScroll = () => { if (!raf) raf = requestAnimationFrame(update) }
    update()
    window.addEventListener("scroll", onScroll, { passive: true })
    window.addEventListener("resize", onScroll)
    return () => {
      window.removeEventListener("scroll", onScroll)
      window.removeEventListener("resize", onScroll)
      cancelAnimationFrame(raf)
    }
  }, [])
}

/** 0..1 page scroll progress. */
export function useScrollProgress() {
  const [p, setP] = useState(0)
  useEffect(() => {
    let raf = 0
    const update = () => {
      raf = 0
      const max = document.documentElement.scrollHeight - window.innerHeight
      setP(max > 0 ? window.scrollY / max : 0)
    }
    const onScroll = () => { if (!raf) raf = requestAnimationFrame(update) }
    update()
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => { window.removeEventListener("scroll", onScroll); cancelAnimationFrame(raf) }
  }, [])
  return p
}

/** Id of the section currently in the middle of the viewport. */
export function useActiveSection(ids) {
  const [active, setActive] = useState("")
  useEffect(() => {
    const els = ids.map((id) => document.getElementById(id)).filter(Boolean)
    const visible = new Set()
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => { if (e.isIntersecting) visible.add(e.target.id); else visible.delete(e.target.id) })
        setActive(ids.find((id) => visible.has(id)) || "")
      },
      { rootMargin: "-45% 0px -50% 0px" }
    )
    els.forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [ids.join(",")])
  return active
}

/** Counts from 0 to `to` once the element is visible. */
export function useCountUp(to, duration = 1400) {
  const ref = useRef(null)
  const [val, setVal] = useState(prefersReducedMotion() ? to : 0)
  useEffect(() => {
    if (prefersReducedMotion()) { setVal(to); return }
    const el = ref.current
    if (!el) return
    let raf = 0
    const io = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return
      io.disconnect()
      const t0 = performance.now()
      const tick = (t) => {
        const k = Math.min(1, (t - t0) / duration)
        const eased = 1 - Math.pow(1 - k, 4)
        setVal(Math.round(to * eased))
        if (k < 1) raf = requestAnimationFrame(tick)
      }
      raf = requestAnimationFrame(tick)
    }, { threshold: 0.4 })
    io.observe(el)
    return () => { io.disconnect(); cancelAnimationFrame(raf) }
  }, [to, duration])
  return [ref, val]
}

/** Is the element in view (once)? Used by charts. */
export function useInViewOnce(threshold = 0.3) {
  const ref = useRef(null)
  const [seen, setSeen] = useState(prefersReducedMotion())
  useEffect(() => {
    if (seen) return
    const el = ref.current
    if (!el || typeof IntersectionObserver === "undefined") { setSeen(true); return }
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setSeen(true); io.disconnect() } }, { threshold })
    io.observe(el)
    return () => io.disconnect()
  }, [seen, threshold])
  return [ref, seen]
}

/** Pointer-follow spotlight: sets --mx/--my on the element (used for card glow). */
export function spotlight(e) {
  const r = e.currentTarget.getBoundingClientRect()
  e.currentTarget.style.setProperty("--mx", e.clientX - r.left + "px")
  e.currentTarget.style.setProperty("--my", e.clientY - r.top + "px")
}
