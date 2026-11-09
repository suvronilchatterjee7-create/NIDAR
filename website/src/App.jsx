import { useEffect, useRef, useState } from "react"
import AnnotationViewer from "./components/AnnotationViewer.jsx"
import StatChart from "./components/StatChart.jsx"
import PhotoSpots from "./components/PhotoSpots.jsx"
import ScrollDrone from "./components/ScrollDrone.jsx"
import { MagButton, StatChip, CopyButton, SectionHead, ICONS } from "./components/ui.jsx"
import { useRevealAll, useParallax, useScrollProgress, useActiveSection, prefersReducedMotion, spotlight } from "./effects.js"
import { REPO, ZIP, NAV, STEPS, CHARTS, FACTS, SOURCES, CHECKS, REVIEW_STEPS, LICENCES, SNIPPET, COMMANDS, ROADMAP } from "./data.js"

function Nav() {
  const progress = useScrollProgress()
  const active = useActiveSection(NAV.map(([id]) => id))
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 12)
    on(); window.addEventListener("scroll", on, { passive: true })
    return () => window.removeEventListener("scroll", on)
  }, [])
  useEffect(() => {
    if (!open) return
    const esc = (e) => e.key === "Escape" && setOpen(false)
    window.addEventListener("keydown", esc)
    return () => window.removeEventListener("keydown", esc)
  }, [open])
  return (
    <nav className={"nav" + (scrolled ? " is-scrolled" : "") + (open ? " is-open" : "")} aria-label="Main">
      <div className="nav-inner">
        <a href="#top" className="logo" aria-label="RescueSwarm, back to top">
          <svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true"><rect x="1" y="1" width="24" height="24" fill="none" stroke="#B6FF3B" strokeWidth="1.5" /><circle cx="13" cy="8" r="2" fill="#B6FF3B" /><path d="M13 10v6M8 12l5 2 5-2M10 21l3-5 3 5" stroke="#B6FF3B" strokeWidth="1.5" fill="none" strokeLinecap="round" /></svg>
          <span className="logo-word">RescueSwarm</span>
          <span className="logo-ver">Pose v0.1</span>
        </a>
        <div className="nav-links" id="nav-links">
          {NAV.map(([id, label]) => (
            <a key={id} href={"#" + id} className={"nav-link" + (active === id ? " is-active" : "")} aria-current={active === id ? "true" : undefined} onClick={() => setOpen(false)}>{label}</a>
          ))}
          <MagButton href={REPO} variant="ghost-acc" newTab className="nav-gh">GitHub <span aria-hidden="true">↗</span></MagButton>
        </div>
        <button type="button" className="nav-burger" aria-expanded={open} aria-controls="nav-links" aria-label={open ? "Close menu" : "Open menu"} onClick={() => setOpen((o) => !o)}>
          <span /><span />
        </button>
      </div>
      <div className="nav-progress" style={{ transform: "scaleX(" + progress + ")" }} aria-hidden="true" />
    </nav>
  )
}

function Drone() {
  const ref = useRef(null)
  useEffect(() => {
    if (prefersReducedMotion()) return
    const el = ref.current
    let raf = 0, tx = 0, ty = 0, cx = 0, cy = 0
    const move = (e) => { tx = (e.clientX / window.innerWidth - 0.5) * 2; ty = (e.clientY / window.innerHeight - 0.5) * 2; if (!raf) raf = requestAnimationFrame(tick) }
    const tick = () => {
      cx += (tx - cx) * 0.08; cy += (ty - cy) * 0.08
      el.style.setProperty("--dx", (cx * 18).toFixed(2) + "px")
      el.style.setProperty("--dy", (cy * 10).toFixed(2) + "px")
      el.style.setProperty("--dr", (cx * 3).toFixed(2) + "deg")
      raf = Math.abs(tx - cx) + Math.abs(ty - cy) > 0.002 ? requestAnimationFrame(tick) : 0
    }
    window.addEventListener("pointermove", move)
    return () => { window.removeEventListener("pointermove", move); cancelAnimationFrame(raf) }
  }, [])
  return (
    <div className="drone-wrap" data-parallax="-0.18">
      <div className="drone" ref={ref}>
        <div className="drone-beam" aria-hidden="true" />
        <img className="drone-img" src="/images/drone.png" alt="Grey quadcopter with a gimbal camera and green LEDs" width="1400" height="309" />
      </div>
    </div>
  )
}

function Hero() {
  return (
    <header className="hero" id="top">
      <div className="hero-bg" data-parallax="0.35" role="img" aria-label="Training exercise with a responder and a casualty lying on grass, with neon skeleton overlays drawn from the dataset annotations" />
      <div className="hero-grid" data-parallax="0.12" aria-hidden="true" />
      <div className="hero-shade" aria-hidden="true" />
      <div className="wrap hero-inner">
        <div className="hero-row">
          <div className="hero-copy">
            <p className="eyebrow-acc" data-reveal>NIDAR 2.0 · Track 1 · Drone Innovation</p>
            <h1 className="h1" data-reveal data-drone-target style={{ "--d": "80ms" }}>
              Teaching drones to see people from above, and to tell <span className="h1-warn">who needs help first.</span>
            </h1>
            <p className="hero-sub" data-reveal style={{ "--d": "160ms" }}>
              RescueSwarm Pose Dataset v0.1: 300 aerial and disaster-exercise images with 17-keypoint skeletons, body outlines and a posture label for every person.
            </p>
            <div className="chips" data-reveal style={{ "--d": "240ms" }}>
              <StatChip value={300} label="images" />
              <StatChip value={519} label="people" />
              <StatChip value={17} label="keypoints" />
            </div>
            <div className="btns" data-reveal style={{ "--d": "320ms" }}>
              <MagButton href="#viewer">Explore the data <span className="btn-arrow down" aria-hidden="true">↓</span></MagButton>
              <MagButton href={REPO} variant="ghost" newTab>GitHub <span className="btn-arrow" aria-hidden="true">↗</span></MagButton>
            </div>
          </div>
          <Drone />
        </div>
        <div className="strip" data-reveal style={{ "--d": "400ms" }}>
          <span><i className="blink" aria-hidden="true" />frame rs_000002.jpg</span>
          <span>source: real · public domain</span>
          <span>2 people · 17 keypoints each</span>
          <span className="is-warn">1 lying → priority</span>
        </div>
      </div>
      <a href="#pipeline" className="scroll-cue" aria-label="Scroll to the pipeline section"><span /></a>
    </header>
  )
}

function Pipeline() {
  return (
    <section id="pipeline" className="sec">
      <div className="wrap">
        <div className="pipe-intro">
          <SectionHead num="02" label="What the drone sees" title="Four steps from pixels to triage" intro="Each annotation in the dataset maps to one stage of the onboard vision stack. Point at the dots on the photo to see what was labelled." />
          <PhotoSpots />
        </div>
        <div className="pipe-grid">
          {STEPS.map((s, i) => (
            <article key={s.n} className={"card step" + (s.warn ? " is-warn" : "")} onPointerMove={spotlight} data-reveal style={{ "--d": i * 90 + "ms" }}>
              <div className="step-top"><span className="step-n">Step {s.n}</span><span className="step-arrow" aria-hidden="true">{s.warn ? "■" : "→"}</span></div>
              <div className="step-icon">{ICONS[s.icon]}</div>
              <h3 className="h3">{s.title}</h3>
              <p className="muted">{s.line}</p>
              <span className="step-out">→ {s.out}</span>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}

function Viewer() {
  return (
    <section id="viewer" className="sec">
      <div className="wrap">
        <SectionHead num="03" label="Annotation viewer" title="See the labels, layer by layer"
          intro="Eight frames from the dataset, four real and four synthetic. Every layer is drawn live from the COCO JSON, so you can switch each one on and off." />
        <div data-reveal><AnnotationViewer /></div>
        <p className="note" data-reveal>The overlays in qa/overlays are baked into the images, so this viewer redraws keypoints, outlines and labels from annotations/coco instead.</p>
      </div>
    </section>
  )
}

function Data() {
  return (
    <section id="data" className="sec">
      <div className="wrap">
        <SectionHead num="04" label="Dataset at a glance" title="300 images. 519 people." intro="Every number below comes from the repository's QA files and COCO annotations." />
        <div className="chart-grid">
          {CHARTS.map(([kind, title, sub], i) => (
            <div key={kind} className="card chart-card" onPointerMove={spotlight} data-reveal style={{ "--d": (i % 2) * 100 + "ms" }}>
              <div className="chart-head"><h3 className="h3 sm">{title}</h3><span className="mono-sub">{sub}</span></div>
              <StatChart kind={kind} />
            </div>
          ))}
        </div>
        <div className="facts">
          {FACTS.map(([k, v], i) => (
            <div key={k} className="fact" data-reveal style={{ "--d": i * 80 + "ms" }}><span className="mono-acc">{k}</span><span className="fact-v">{v}</span></div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Sources() {
  return (
    <section id="sources" className="sec">
      <div className="wrap">
        <SectionHead num="05" label="Real vs synthetic" title="Half real, half rendered" />
        <div className="two-grid">
          {SOURCES.map((s, i) => (
            <article key={s.key} className="card src-card" data-reveal style={{ "--d": i * 120 + "ms" }}>
              <div className="src-media">
                <img src={s.img} alt={s.alt} width={s.w} height={s.h} loading="lazy" decoding="async" data-parallax="0.08" />
                <span className={"src-badge" + (s.key === "synthetic" ? " is-acc" : "")}>{s.key}</span>
              </div>
              <div className="src-body">
                <div className="src-title"><h3 className="h3">{s.title}</h3><span className={"mono-sub strong" + (s.key === "synthetic" ? " is-acc" : "")}>{s.count}</span></div>
                <p>{s.l1}</p>
                <p className="muted">{s.l2}</p>
                <span className="credit">{s.credit}</span>
              </div>
            </article>
          ))}
        </div>
        <div className="why" data-reveal>
          <h3 className="h3 acc">Why both?</h3>
          <p>Aerial photos of real casualties are scarce and hard to license, and real labels here are unreviewed pre-labels. Synthetic renders fill the class that matters most, lying people, with perfect labels. The trade-off is a domain gap: the rendered backgrounds are procedural and won't match a live drone feed exactly. The real images keep the model grounded in what a camera actually sees.</p>
        </div>
      </div>
    </section>
  )
}

function Quality() {
  return (
    <section id="quality" className="sec">
      <div className="wrap">
        <SectionHead num="06" label="Quality and trust" title="Checked, logged, licensed" intro="The validation suite, a review workflow and a per-image licence ledger ship with the data." />
        <div className="two-grid top">
          <div className="card pad" data-reveal>
            <div className="card-head"><h3 className="h3 sm">Validation report</h3><span className="pass">Status: PASS</span></div>
            <ul className="checks">
              {CHECKS.map(([c, d], i) => (
                <li key={c} style={{ "--d": i * 70 + "ms" }}><span className="tick" aria-hidden="true">✓</span><div><span>{c}</span><span className="mono-sub">{d}</span></div></li>
              ))}
            </ul>
            <span className="src-ref">Source: qa/validation_report.md</span>
          </div>
          <div className="card pad" data-reveal style={{ "--d": "120ms" }}>
            <h3 className="h3 sm">Human review in CVAT</h3>
            <div className="review">
              <div><b className="acc">188</b><span>reviewed · 36.2%<br />synthetic, exact geometry</span></div>
              <div><b className="warn">331</b><span>unreviewed · 63.8%<br />real, YOLOv8 pre-labels</span></div>
            </div>
            <ol className="steps-list">
              {REVIEW_STEPS.map((t, i) => <li key={i}><span className="mono-acc">{i + 1}</span><span>{t}</span></li>)}
            </ol>
            <span className="src-ref">Source: HOW_TO_REVIEW.md</span>
          </div>
        </div>
        <div className="card lic" data-reveal>
          <div className="card-head pad-x"><h3 className="h3 sm">Licence ledger</h3><span className="mono-sub">LICENSE_LEDGER.csv · 300 rows</span></div>
          <table>
            <thead><tr><th scope="col">Licence</th><th scope="col">Images</th><th scope="col">Commercial</th><th scope="col">Condition</th></tr></thead>
            <tbody>
              {LICENCES.map(([l, s, n, c]) => (
                <tr key={l}>
                  <th scope="row">{l}<span>{s}</span></th>
                  <td><span className="lic-bar" style={{ "--w": (n / 150) * 100 + "%" }} aria-hidden="true" />{n}</td>
                  <td className="acc">Yes</td>
                  <td className={c === "None" ? "muted" : "warn"}>{c}</td>
                </tr>
              ))}
            </tbody>
            <tfoot><tr><th scope="row">Total</th><td>300</td><td /><td /></tr></tfoot>
          </table>
          <p className="lic-note">All 300 images allow commercial use. 7 CC BY-SA 2.0 images also require share-alike.</p>
        </div>
        <div className="credits" data-reveal>
          <span className="mono-acc">Images on this site</span>
          <p>rs_000002 (hero, viewer, comparison): U.S. Marine Corps photo by Lance Cpl. Ella Cadby, public domain; the hero version has skeletons redrawn from its COCO annotations. rs_000015: U.S. Army photo by Sgt. 1st Class Shane Klestinski, public domain. rs_000272: U.S. Marine Corps photo by Cpl. Samuel Qin, public domain. rs_000274: U.S. Marine Corps photo by Lance Cpl. Kindsey Calvert, public domain. rs_000001, rs_000011, rs_000012, rs_000014: RescueSwarm generative rig. Sourced via Wikimedia Commons as listed in LICENSE_LEDGER.csv.</p>
        </div>
      </div>
    </section>
  )
}

function Start() {
  return (
    <section id="start" className="sec">
      <div className="wrap">
        <SectionHead num="07" label="Get started" title="Load it in three lines" />
        <div className="two-grid top">
          <div className="start-left" data-reveal>
            <p className="lead">The full package is one zip: images, COCO and MPII annotations, tools and QA reports. A YOLOv8n-pose checkpoint sits next to it in the repo.</p>
            <MagButton href={ZIP} className="btn-lg" aria-label="Download RescueSwarm_PoseSet_v0.1.zip, 40.7 megabytes">
              <span className="btn-arrow down" aria-hidden="true">↓</span> Download zip <small>40.7 MB</small>
            </MagButton>
            <div className="cmds">
              <span className="mono-acc">From the repo root</span>
              {COMMANDS.map((c) => (
                <div key={c} className="cmd"><code>{c}</code><CopyButton text={c} /></div>
              ))}
            </div>
            <a className="text-link" href={REPO} target="_blank" rel="noopener noreferrer">Browse the code, tools and QA reports on GitHub ↗</a>
          </div>
          <div className="code-card" data-reveal style={{ "--d": "120ms" }}>
            <div className="code-head"><span>load_coco.py</span><span className="muted">Python · pycocotools</span><CopyButton text={SNIPPET} /></div>
            <pre><code>{SNIPPET.split("\n").map((l, i) => (
              <span key={i} className={"code-line" + (l.trim().startsWith("#") ? " is-comment" : "")}><i aria-hidden="true">{i + 1}</i>{l || " "}</span>
            ))}</code></pre>
          </div>
        </div>
      </div>
    </section>
  )
}

function Roadmap() {
  return (
    <section id="roadmap" className="sec">
      <div className="wrap">
        <SectionHead num="08" label="Roadmap and limits" title="v0.1 is a seed set" intro="It's built for fine-tuning and outline checks, not as a finished benchmark. Here's what's done, what's next and what isn't documented yet." />
        <div className="rm-grid">
          {ROADMAP.map((c, i) => (
            <div key={c.title} className={"card pad rm tone-" + c.tone} onPointerMove={spotlight} data-reveal style={{ "--d": i * 100 + "ms" }}>
              <h3 className="h3">{c.title}</h3>
              <ul>{c.items.map((t) => <li key={t}><span aria-hidden="true">{c.mark}</span>{t}</li>)}</ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="footer">
      <div className="wrap">
        <div className="foot-row">
          <div className="foot-team">
            <span className="foot-word" data-reveal data-drone-target>RescueSwarm</span>
            <p className="muted">Team RescueSwarm · NIDAR 2.0 (2026–27), Track 1: Drone Innovation. Organised by Drone Federation India with MeitY under the SwaYaan programme.</p>
          </div>
          <div className="foot-col">
            <span className="mono-acc">Contact</span>
            <a className="foot-link" href={REPO} target="_blank" rel="noopener noreferrer">GitHub repository ↗</a>
            <a className="foot-link" href={REPO + "/issues"} target="_blank" rel="noopener noreferrer">Open an issue ↗</a>
          </div>
          <div className="foot-col">
            <span className="mono-acc">Licence</span>
            <p className="muted">Each image carries its own licence in LICENSE_LEDGER.csv: 150 generated by the team, 123 public domain, 20 CC BY and 7 CC BY-SA. Keep the attribution and share-alike terms where they apply.</p>
          </div>
        </div>
        <div className="foot-base"><span>© 2026 RescueSwarm · Dataset v0.1</span><span>Built for search and rescue</span></div>
      </div>
    </footer>
  )
}

function BackToTop() {
  const [show, setShow] = useState(false)
  useEffect(() => {
    const on = () => setShow(window.scrollY > window.innerHeight * 1.2)
    on(); window.addEventListener("scroll", on, { passive: true })
    return () => window.removeEventListener("scroll", on)
  }, [])
  return (
    <a href="#top" className={"to-top" + (show ? " is-shown" : "")} aria-label="Back to top" tabIndex={show ? 0 : -1}>↑</a>
  )
}

export default function App() {
  useRevealAll()
  useParallax()
  return (
    <>
      <a href="#viewer" className="skip">Skip to the annotation viewer</a>
      <Nav />
      <main>
        <Hero />
        <Pipeline />
        <Viewer />
        <Data />
        <Sources />
        <Quality />
        <Start />
        <Roadmap />
      </main>
      <Footer />
      <ScrollDrone />
      <BackToTop />
    </>
  )
}
