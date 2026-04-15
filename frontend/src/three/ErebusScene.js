/**
 * ErebusScene.js v3 — MAX VISUAL IMPACT
 * Key upgrades over v2:
 *  - toneMappingExposure 1.1 → 1.5  (brighter overall)
 *  - camera starts at z=50 (was 60) — objects 20% larger on screen
 *  - ALL materials use AdditiveBlending → proper light stacking, not muddy
 *  - additive glow halos on every hero/system node
 *  - ghost shapes 2–3% → 6–10% opacity (actually visible)
 *  - wireframe lines 45% → 65% opacity
 *  - scan beam: animated horizontal plane sweeping through scene
 *  - horizon ring: pulsing gold torus at scene floor
 *  - 1 400 total dust particles (5 layers, full -160 to +160 x spread)
 *  - blinking amplitude 0.18 → 0.35 (dramatically more noticeable)
 *  - node sizes +25% across the board
 *  - violet accent PointLight for sci-fi purple undertone
 */

import * as THREE from 'three'

const GOLD   = 0xC9A84C
const GOLDD  = 0xDFC06A
const BLUE   = 0x4A8FE7
const GREEN  = 0x2ECC8A
const RED    = 0xD95555
const AMBER  = 0xE09A25
const VIOLET = 0x8844CC

export class ErebusScene {
  constructor(canvas) {
    this.canvas   = canvas
    this.width    = window.innerWidth
    this.height   = window.innerHeight
    this.time     = 0
    this.mouse    = { x: 0, y: 0 }
    this.smooth   = { x: 0, y: 0 }
    this.scrollP  = 0
    this.disposed = false

    this._nodes       = []
    this._pulsars     = []
    this._curvePulse  = []
    this._cards       = []
    this._ambShapes   = []
    this._starGroups  = []
    this._ghostMeshes = []

    this._init()
  }

  _init() {
    this._setupRenderer()
    this._setupCamera()
    this._setupScene()
    this._setupLights()

    // Build scene in depth order (back → front)
    this._createSpaceGrid()
    this._createGhostLayer()
    this._createDust()
    this._createBlinkingStars()
    this._createScanBeam()
    this._createAmbientShapes()
    this._createAmbientLines()
    this._createHeroNodes()
    this._createSystemNodes()
    this._createConnections()
    this._createPipelineCurve()
    this._createCardPlanes()

    // Bind and start
    this._tick     = this._tick.bind(this)
    this._onResize = this._onResize.bind(this)
    this._onMouse  = this._onMouse.bind(this)
    window.addEventListener('resize',    this._onResize)
    window.addEventListener('mousemove', this._onMouse)
    this._raf = requestAnimationFrame(this._tick)
  }

  /* =====================  RENDERER / CAMERA / SCENE  ===================== */

  _setupRenderer() {
    this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true, alpha: false })
    this.renderer.setSize(this.width, this.height)
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    this.renderer.setClearColor(0x08080d, 1)
    this.renderer.toneMapping        = THREE.ACESFilmicToneMapping
    this.renderer.toneMappingExposure = 1.5
  }

  _setupCamera() {
    this.camera = new THREE.PerspectiveCamera(62, this.width / this.height, 0.05, 900)
    this.camera.position.set(0, 0, 50) // closer than before, objects feel larger
  }

  _setupScene() {
    this.scene = new THREE.Scene()
    this.scene.fog = new THREE.FogExp2(0x08080d, 0.0055)

    // 3 depth groups → different mouse-parallax speeds
    this._deepGroup  = new THREE.Group()  // z 45-80  → 0.8x mouse
    this._midGroup   = new THREE.Group()  // z 20-45  → 2.6x mouse
    this._closeGroup = new THREE.Group()  // z 0-20   → 5.5x mouse
    this.scene.add(this._deepGroup, this._midGroup, this._closeGroup)
  }

  _setupLights() {
    this.scene.add(new THREE.AmbientLight(0x1a1b25, 2.0)) // much brighter ambient

    this.goldLight = new THREE.PointLight(GOLD, 10, 120)
    this.goldLight.position.set(0, 14, 44)
    this.scene.add(this.goldLight)

    this.blueLight = new THREE.PointLight(BLUE, 6, 100)
    this.blueLight.position.set(-18, -6, 16)
    this.scene.add(this.blueLight)

    this.greenLight = new THREE.PointLight(GREEN, 4, 80)
    this.greenLight.position.set(14, 10, -10)
    this.scene.add(this.greenLight)

    // Left gold fill — fills empty left side
    const fillL = new THREE.PointLight(GOLD, 3.5, 90)
    fillL.position.set(-30, 2, 32)
    this.scene.add(fillL)

    // Right blue accent
    const fillR = new THREE.PointLight(BLUE, 2.5, 80)
    fillR.position.set(30, 6, 28)
    this.scene.add(fillR)

    // Violet depth light — sci-fi undertone
    const violet = new THREE.PointLight(VIOLET, 3, 110)
    violet.position.set(0, -5, 62)
    this.scene.add(violet)
  }

  /* ==========================  SPACE GRID  ========================== */

  _createSpaceGrid() {
    // Floor grid — gold, 3.8% opacity (clearly a grid now)
    const W = 240, step = 16, pts = []
    for (let x = -W / 2; x <= W / 2; x += step) {
      pts.push(new THREE.Vector3(x, -22, -80), new THREE.Vector3(x, -22, 80))
    }
    for (let z = -80; z <= 80; z += step) {
      pts.push(new THREE.Vector3(-W / 2, -22, z), new THREE.Vector3(W / 2, -22, z))
    }
    this._deepGroup.add(new THREE.LineSegments(
      new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({ color: GOLD, transparent: true, opacity: 0.038 })
    ))

    // Back wall grid — blue, 1.8%
    const wPts = []
    for (let x = -W / 2; x <= W / 2; x += step * 2) {
      wPts.push(new THREE.Vector3(x, -32, 78), new THREE.Vector3(x, 26, 78))
    }
    for (let y = -32; y <= 26; y += step) {
      wPts.push(new THREE.Vector3(-W / 2, y, 78), new THREE.Vector3(W / 2, y, 78))
    }
    this._deepGroup.add(new THREE.LineSegments(
      new THREE.BufferGeometry().setFromPoints(wPts),
      new THREE.LineBasicMaterial({ color: BLUE, transparent: true, opacity: 0.018 })
    ))

    // Horizon ring — gold torus at floor level, pulsing
    this._horizonRing = new THREE.Mesh(
      new THREE.TorusGeometry(56, 0.14, 4, 90),
      new THREE.MeshBasicMaterial({
        color: GOLD, transparent: true, opacity: 0.055,
        blending: THREE.AdditiveBlending, depthWrite: false,
      })
    )
    this._horizonRing.position.set(0, -20, 18)
    this._horizonRing.rotation.x = Math.PI / 2
    this._deepGroup.add(this._horizonRing)
  }

  /* ==========================  GHOST LAYER  ========================= */

  _createGhostLayer() {
    const ghost = (GeoClass, args, pos, color, opacity) => {
      const m = new THREE.Mesh(
        new GeoClass(...args),
        new THREE.MeshBasicMaterial({
          color, wireframe: true, transparent: true, opacity,
          blending: THREE.AdditiveBlending, depthWrite: false,
        })
      )
      m.position.set(...pos)
      this._deepGroup.add(m)
      this._ghostMeshes.push({ mesh: m, rx: 0.0005, ry: 0.0008, rz: 0.0003 })
    }

    // LEFT (fills empty left void) — much more visible than v2
    ghost(THREE.SphereGeometry,      [16, 24, 24],      [-26, 3, 40],  GOLD,   0.07)
    ghost(THREE.TorusGeometry,       [10, 0.5, 8, 40],  [-19, -8, 30], GOLD,   0.055)
    ghost(THREE.IcosahedronGeometry, [7, 1],             [-32, 9, 48],  BLUE,   0.06)

    // RIGHT counterweight (different shapes to avoid symmetry)
    ghost(THREE.OctahedronGeometry,  [11, 1],            [28, -4, 44],  BLUE,   0.055)
    ghost(THREE.TorusKnotGeometry,   [6, 1.8, 60, 6],    [24, 11, 52],  GOLD,   0.04)

    // Deep center — big ghosted spheres give sense of vast space
    ghost(THREE.SphereGeometry,      [30, 18, 18],       [0, 0, 76],    GOLD,   0.015)
    ghost(THREE.IcosahedronGeometry, [20, 2],             [5, -6, 70],   BLUE,   0.020)
  }

  /* ==========================  PARTICLES  =========================== */

  _createDust() {
    const mk = (n, color, size, op, rX, rY, rZ, zMid, group) => {
      const pos = new Float32Array(n * 3)
      for (let i = 0; i < n; i++) {
        pos[i * 3]     = (Math.random() - 0.5) * rX
        pos[i * 3 + 1] = (Math.random() - 0.5) * rY
        pos[i * 3 + 2] = (Math.random() - 0.5) * rZ + zMid
      }
      const g = new THREE.BufferGeometry()
      g.setAttribute('position', new THREE.BufferAttribute(pos, 3))
      const pts = new THREE.Points(g, new THREE.PointsMaterial({
        color, size, transparent: true, opacity: op,
        sizeAttenuation: true, depthWrite: false,
        blending: THREE.AdditiveBlending,
      }))
      group.add(pts)
      return pts
    }

    // 6 particle layers — total ~1420 particles, full ±160 width spread
    this._d1 = mk(500, GOLD,   0.11, 0.55, 360, 160, 360, 22, this._deepGroup)
    this._d2 = mk(200, BLUE,   0.18, 0.40, 280, 110, 260, 14, this._deepGroup)
    this._d3 = mk(160, VIOLET, 0.14, 0.28, 220,  90, 200, 26, this._deepGroup)
    this._d4 = mk(280, GOLD,   0.14, 0.45, 200,  90, 160, 18, this._midGroup)
    this._d5 = mk(120, BLUE,   0.22, 0.32, 100,  55,  90, -8, this._midGroup)
    this._d6 = mk(70,  GOLDD,  0.32, 0.68,  80,  50,  50, 12, this._closeGroup)
  }

  /* ========================  BLINKING STARS  ======================== */

  _createBlinkingStars() {
    for (let g = 0; g < 12; g++) {
      const cnt = 22
      const pos = new Float32Array(cnt * 3)
      for (let i = 0; i < cnt; i++) {
        pos[i * 3]     = (Math.random() - 0.5) * 320
        pos[i * 3 + 1] = (Math.random() - 0.5) * 150
        pos[i * 3 + 2] = (Math.random() - 0.5) * 230 + 28
      }
      const geo = new THREE.BufferGeometry()
      geo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
      const color = [GOLD, BLUE, 0xFFFFFF, VIOLET][g % 4]
      const pts = new THREE.Points(geo, new THREE.PointsMaterial({
        color, size: 0.07 + Math.random() * 0.16, transparent: true, opacity: 0.25,
        sizeAttenuation: true, depthWrite: false, blending: THREE.AdditiveBlending,
      }))
      this._deepGroup.add(pts)
      this._starGroups.push({ pts, phase: g * (Math.PI * 2 / 12), speed: 0.28 + Math.random() * 0.60 })
    }
  }

  /* ==========================  SCAN BEAM  =========================== */

  _createScanBeam() {
    // Thin translucent horizontal plane that sweeps vertically — very cinematic
    this._scanBeam = new THREE.Mesh(
      new THREE.PlaneGeometry(260, 0.5),
      new THREE.MeshBasicMaterial({
        color: GOLD, transparent: true, opacity: 0.06,
        blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
      })
    )
    this._scanBeam.position.set(0, 20, 30)
    this._scanBeam.rotation.y = 0.15
    this._deepGroup.add(this._scanBeam)
  }

  /* ========================  AMBIENT SHAPES  ======================== */

  _createAmbientShapes() {
    const geos = [
      new THREE.BoxGeometry(1, 1, 1),
      new THREE.OctahedronGeometry(0.8, 0),
      new THREE.TetrahedronGeometry(0.9, 0),
      new THREE.IcosahedronGeometry(0.65, 0),
    ]
    const colors = [GOLD, BLUE, GOLD, GREEN, GOLDD, AMBER]

    // Full-width distribution: left (-34) → right (+30), varied depths
    const positions = [
      [-24, 7,34],[-28,-4,28],[-20,12,40],[-32,-9,36],[-14,-14,30],[-36, 5,44],
      [-10, 9,30],[-5 ,-7,26],[-7 ,14,38],
      [ 2 ,-9,25],[ 0 ,15,42],[-2 ,-14,33],
      [ 9 , 7,32],[12 ,-5,27],[10 ,14,40],
      [18 , 6,32],[22 ,-5,27],[20 ,13,40],[26,-11,34],[30, 7,38],[16,-16,30],
      [-26, 0,58],[ 0 ,-6,61],[26 , 4,55],[-14, 9,63],[14,-9,59],
      [-17,-6,19],[-9 , 8,16],
    ]

    positions.forEach((pos, i) => {
      const geo  = geos[i % geos.length].clone()
      const col  = colors[i % colors.length]
      const opac = 0.09 + Math.random() * 0.15       // 9–24% visible (was 4-13%)
      const mat  = new THREE.MeshBasicMaterial({
        color: col, wireframe: true, transparent: true, opacity: opac,
        blending: THREE.AdditiveBlending, depthWrite: false,
      })
      const mesh = new THREE.Mesh(geo, mat)
      mesh.position.set(...pos)
      mesh.scale.setScalar(0.5 + Math.random() * 1.8)
      mesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI)

      const z = pos[2]
      const grp = z > 38 ? this._deepGroup : (z > 24 ? this._midGroup : this._closeGroup)
      grp.add(mesh)

      this._ambShapes.push({
        mesh,
        rx: (Math.random() - 0.5) * 0.007,
        ry: (Math.random() - 0.5) * 0.010,
        rz: (Math.random() - 0.5) * 0.005,
        phase:    Math.random() * Math.PI * 2,
        floatSpd: 0.4 + Math.random() * 0.7,
        floatAmp: 0.10 + Math.random() * 0.30,
        baseY:    pos[1],
      })
    })
  }

  /* ========================  AMBIENT LINES  ========================= */

  _createAmbientLines() {
    const pairs = [
      [[-24,7,34],[-16,-4,26]], [[24,-2,32],[16,9,40]],
      [[-7,11,30],[7,-7,25]],   [[-32,3,44],[-22,-8,36]],
      [[22,13,40],[30,-5,32]],  [[-16,-5,19],[-7,11,30]],
      [[2,-9,58],[18,4,55]],    [[-24,5,58],[-7,-6,61]],
      [[0,8,28],[12,-5,27]],    [[-9,0,22],[9,0,22]],
    ]
    pairs.forEach(([a, b], i) => {
      const geo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...a), new THREE.Vector3(...b)])
      const mat = new THREE.LineBasicMaterial({
        color: i % 2 === 0 ? BLUE : GOLD,
        transparent: true, opacity: 0.07 + Math.random() * 0.06,
      })
      const grp = a[2] > 42 ? this._deepGroup : this._midGroup
      grp.add(new THREE.Line(geo, mat))
    })
  }

  /* ==========================  HERO NODES  ========================== */

  _createHeroNodes() {
    const halo = (r, color, parent) => {
      parent.add(new THREE.Mesh(
        new THREE.SphereGeometry(r, 16, 16),
        new THREE.MeshBasicMaterial({
          color, transparent: true, opacity: 0.055,
          side: THREE.BackSide, blending: THREE.AdditiveBlending, depthWrite: false,
        })
      ))
    }

    const mk = (GeoClass, args, pos, solidC, wireC, rotS, floatA, floatSpd, phase, haloR) => {
      const geo   = new GeoClass(...args)
      const solid = new THREE.Mesh(geo, new THREE.MeshPhongMaterial({
        color: solidC, emissive: solidC, emissiveIntensity: 0.22,
        shininess: 160, transparent: true, opacity: 0.90,
      }))
      const wire  = new THREE.Mesh(geo.clone(), new THREE.MeshBasicMaterial({
        color: wireC, wireframe: true, transparent: true, opacity: 0.65,
        blending: THREE.AdditiveBlending, depthWrite: false,
      }))
      const g = new THREE.Group()
      g.add(solid, wire)
      halo(haloR, wireC, g)
      g.position.set(...pos)
      this._closeGroup.add(g)
      this._nodes.push({ mesh: g, rotSpeed: rotS, floatAmp: floatA, floatSpd, phase, baseY: pos[1] })
    }

    mk(THREE.IcosahedronGeometry, [3.5, 1],            [0,   0, 32], 0x1a1208, GOLD,  0.0022, 0.38, 0.70, 0,   7.5)
    mk(THREE.TorusGeometry,       [1.6, 0.55, 10, 24], [-10, 2, 25], 0x0a1020, BLUE,  0.006,  0.55, 1.10, 1.3, 5.2)
    mk(THREE.OctahedronGeometry,  [2.4, 0],             [12, -2, 22], 0x0a1a12, GREEN, 0.004,  0.42, 0.90, 2.6, 5.8)

    // Big transparent background sphere
    const bg = new THREE.Mesh(
      new THREE.SphereGeometry(20, 36, 36),
      new THREE.MeshBasicMaterial({ color: GOLD, wireframe: true, transparent: true, opacity: 0.030,
        blending: THREE.AdditiveBlending, depthWrite: false })
    )
    bg.position.set(0, 0, 38)
    this._deepGroup.add(bg)
    this._bgSphere = bg
  }

  /* ========================  SYSTEM NODES  ========================== */

  _createSystemNodes() {
    const MODS = [
      { GeoClass: THREE.TorusKnotGeometry,  args: [1.0, 0.32, 90, 9],  pos: [-6, 1.5,14], wireC: GOLD,  solidC: 0x15100a, rotS: 0.006 },
      { GeoClass: THREE.IcosahedronGeometry, args: [1.7, 1],            pos: [ 5,-0.5,17], wireC: BLUE,  solidC: 0x080f1a, rotS: 0.004 },
      { GeoClass: THREE.OctahedronGeometry,  args: [1.6, 0],            pos: [ 0,-3.5,20], wireC: GREEN, solidC: 0x081510, rotS: 0.007 },
      { GeoClass: THREE.BoxGeometry,         args: [2.2, 2.2, 2.2],     pos: [-7,-3,  22], wireC: AMBER, solidC: 0x12100a, rotS: 0.004 },
      { GeoClass: THREE.SphereGeometry,      args: [1.5, 14, 14],       pos: [ 8, 3.5,19], wireC: RED,   solidC: 0x15080a, rotS: 0.003 },
      { GeoClass: THREE.ConeGeometry,        args: [1.3, 2.6, 7],       pos: [ 2, 6,  15], wireC: GOLDD, solidC: 0x12100a, rotS: 0.005 },
    ]

    this._systemNodes = MODS.map((m, i) => {
      const geo   = new m.GeoClass(...m.args)
      const solid = new THREE.Mesh(geo, new THREE.MeshPhongMaterial({
        color: m.solidC, emissive: m.solidC, emissiveIntensity: 0.35,
        shininess: 160, transparent: true, opacity: 0.85,
      }))
      const wire  = new THREE.Mesh(geo.clone(), new THREE.MeshBasicMaterial({
        color: m.wireC, wireframe: true, transparent: true, opacity: 0.68,
        blending: THREE.AdditiveBlending, depthWrite: false,
      }))
      const g = new THREE.Group()
      g.add(solid, wire)
      // halo
      g.add(new THREE.Mesh(
        new THREE.SphereGeometry(3.4, 12, 12),
        new THREE.MeshBasicMaterial({ color: m.wireC, transparent: true, opacity: 0.045,
          side: THREE.BackSide, blending: THREE.AdditiveBlending, depthWrite: false })
      ))
      g.add(new THREE.PointLight(m.wireC, 1.4, 13))
      g.position.set(...m.pos)
      this._closeGroup.add(g)
      this._nodes.push({ mesh: g, rotSpeed: m.rotS, floatAmp: 0.22 + Math.random() * 0.28,
        floatSpd: 0.5 + Math.random() * 0.7, phase: i * 1.05, baseY: m.pos[1] })
      return { pos: new THREE.Vector3(...m.pos), wireC: m.wireC }
    })
  }

  /* ======================  CONNECTIONS + PULSARS  =================== */

  _createConnections() {
    this._connEdges = []
    const edges = [[0,1],[0,2],[1,3],[2,4],[3,5],[4,5],[1,5],[0,4]]
    edges.forEach(([a, b]) => {
      const sn = this._systemNodes
      if (!sn[a] || !sn[b]) return
      const pts = [sn[a].pos.clone(), sn[b].pos.clone()]
      this._closeGroup.add(new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(pts),
        new THREE.LineBasicMaterial({ color: GOLD, transparent: true, opacity: 0.22 })
      ))
      this._connEdges.push({ start: pts[0], end: pts[1] })

      const pMesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.09, 7, 7),
        new THREE.MeshBasicMaterial({ color: GOLDD, transparent: true, opacity: 0,
          blending: THREE.AdditiveBlending, depthWrite: false })
      )
      this._closeGroup.add(pMesh)
      this._pulsars.push({ mesh: pMesh, start: pts[0], end: pts[1],
        t: Math.random(), speed: 0.20 + Math.random() * 0.25 })
    })
  }

  /* ========================  PIPELINE CURVE  ======================== */

  _createPipelineCurve() {
    this._curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-24, 4,  5),
      new THREE.Vector3(-10,-4,  0),
      new THREE.Vector3(  0, 2, -6),
      new THREE.Vector3( 12,-3,-18),
      new THREE.Vector3( 24, 4,-28),
    ])

    this._midGroup.add(new THREE.Mesh(
      new THREE.TubeGeometry(this._curve, 80, 0.06, 7, false),
      new THREE.MeshBasicMaterial({ color: BLUE, transparent: true, opacity: 0.28,
        blending: THREE.AdditiveBlending })
    ))

    for (let i = 0; i < 12; i++) {
      const mesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.18, 7, 7),
        new THREE.MeshBasicMaterial({ color: BLUE, transparent: true, opacity: 0,
          blending: THREE.AdditiveBlending, depthWrite: false })
      )
      this._midGroup.add(mesh)
      this._curvePulse.push({ mesh, t: i / 12, speed: 0.12 + Math.random() * 0.09 })
    }

    ;[0.2, 0.4, 0.6, 0.8].forEach(t => {
      const pt = this._curve.getPoint(t)
      const m  = new THREE.Mesh(
        new THREE.OctahedronGeometry(0.38, 0),
        new THREE.MeshBasicMaterial({ color: BLUE, wireframe: true, transparent: true, opacity: 0.72,
          blending: THREE.AdditiveBlending })
      )
      m.position.copy(pt)
      this._midGroup.add(m)
      this._nodes.push({ mesh: m, rotSpeed: 0.014, floatAmp: 0.12, floatSpd: 1.6, phase: t * 6, baseY: pt.y })
    })
  }

  /* ==========================  CARD PLANES  ========================= */

  _createCardPlanes() {
    const DEFS = [
      { pos: [-14, 4,-30], rot: [ 0.08, 0.22,-0.06], accent: GOLD  },
      { pos: [ 10,-3,-40], rot: [-0.12,-0.28, 0.09], accent: BLUE  },
      { pos: [ -3, 7,-48], rot: [ 0.18, 0.06, 0.14], accent: GREEN },
      { pos: [-11,-6,-55], rot: [-0.10, 0.32,-0.08], accent: AMBER },
      { pos: [ 16, 2,-50], rot: [ 0.05,-0.18, 0.11], accent: GOLDD },
    ]
    DEFS.forEach(cd => {
      const pGeo = new THREE.PlaneGeometry(7.5, 5)
      const g    = new THREE.Group()
      g.add(new THREE.Mesh(pGeo,
        new THREE.MeshBasicMaterial({ color: 0x141826, transparent: true, opacity: 0.45, side: THREE.DoubleSide })))
      g.add(new THREE.LineSegments(
        new THREE.EdgesGeometry(pGeo),
        new THREE.LineBasicMaterial({ color: cd.accent, transparent: true, opacity: 0.65,
          blending: THREE.AdditiveBlending })
      ))
      g.position.set(...cd.pos)
      g.rotation.set(...cd.rot)
      this._midGroup.add(g)
      this._cards.push({ mesh: g, baseRot: { x: cd.rot[0], y: cd.rot[1], z: cd.rot[2] } })
    })
  }

  /* =======================  SCROLL → CAMERA  ======================== */

  updateScroll(progress) {
    this.scrollP = progress
    this.camera.position.z = 50 - progress * 105   // 50 → -55
    this.camera.position.y = Math.sin(progress * Math.PI * 1.6) * 3.5
    this.camera.position.x = Math.sin(progress * Math.PI * 2.8) * 2.5
    this.camera.rotation.y = Math.sin(progress * Math.PI * 1.8) * 0.055
    this.camera.rotation.z = Math.cos(progress * Math.PI * 2.4) * 0.016

    this.goldLight.intensity  = 10 * Math.max(0, 1 - progress * 2.2)
    this.blueLight.intensity  = 3  + progress * 9
    this.greenLight.intensity = progress * 5
  }

  /* ============================  TICK  ============================== */

  _tick() {
    if (this.disposed) return
    this._raf = requestAnimationFrame(this._tick)
    this.time += 0.008

    // Mouse lerp
    this.smooth.x += (this.mouse.x - this.smooth.x) * 0.022
    this.smooth.y += (this.mouse.y - this.smooth.y) * 0.022

    // ── Depth-based parallax ────────────────────────────────────
    this._deepGroup.position.x  =  this.smooth.x * 0.8
    this._deepGroup.position.y  = -this.smooth.y * 0.55
    this._midGroup.position.x   =  this.smooth.x * 2.6
    this._midGroup.position.y   = -this.smooth.y * 1.8
    this._closeGroup.position.x =  this.smooth.x * 5.5
    this._closeGroup.position.y = -this.smooth.y * 3.8

    // ── Slow scene drift (deep layer) ──────────────────────────
    this._deepGroup.rotation.y = this.time * 0.006
    if (this._bgSphere) this._bgSphere.rotation.y = this.time * 0.030

    // ── Scan beam sweep down then jump to top ──────────────────
    if (this._scanBeam) {
      this._scanBeam.position.y = 22 - ((this.time * 3.8) % 46)
      this._scanBeam.material.opacity = 0.03 + Math.abs(Math.sin(this.time * 0.45)) * 0.045
    }

    // ── Horizon ring pulse ─────────────────────────────────────
    if (this._horizonRing) {
      this._horizonRing.material.opacity = 0.04 + Math.sin(this.time * 0.7) * 0.025
    }

    // ── Ghost shapes rotate slowly ─────────────────────────────
    this._ghostMeshes.forEach(g => {
      g.mesh.rotation.x += g.rx
      g.mesh.rotation.y += g.ry
      g.mesh.rotation.z += g.rz
    })

    // ── Primary nodes float and spin ───────────────────────────
    this._nodes.forEach(n => {
      n.mesh.rotation.y += n.rotSpeed
      n.mesh.rotation.x += n.rotSpeed * 0.55
      n.mesh.position.y  = n.baseY + Math.sin(this.time * n.floatSpd + n.phase) * n.floatAmp
    })

    // ── Ambient shapes rotate + float ─────────────────────────
    this._ambShapes.forEach(a => {
      a.mesh.rotation.x += a.rx
      a.mesh.rotation.y += a.ry
      a.mesh.rotation.z += a.rz
      a.mesh.position.y  = a.baseY + Math.sin(this.time * a.floatSpd + a.phase) * a.floatAmp
    })

    // ── Blinking stars — amplitude 0.35 (very noticeable) ─────
    this._starGroups.forEach(g => {
      g.pts.material.opacity = Math.max(0.01, 0.08 + Math.sin(this.time * g.speed + g.phase) * 0.35)
    })

    // ── Connection pulsars ─────────────────────────────────────
    this._pulsars.forEach(p => {
      p.t = (p.t + p.speed * 0.008) % 1
      p.mesh.position.lerpVectors(p.start, p.end, p.t)
      p.mesh.material.opacity = Math.sin(p.t * Math.PI) * 0.95
    })

    // ── Pipeline curve pulsars ─────────────────────────────────
    this._curvePulse.forEach(p => {
      p.t = (p.t + p.speed * 0.007) % 1
      p.mesh.position.copy(this._curve.getPoint(p.t))
      p.mesh.material.opacity = 0.35 + Math.sin(p.t * Math.PI) * 0.70
    })

    // ── Card planes — cursor tilt ──────────────────────────────
    this._cards.forEach((c, i) => {
      c.mesh.rotation.y = c.baseRot.y + this.smooth.x * 0.09 + Math.sin(this.time * 0.25 + i) * 0.012
      c.mesh.rotation.x = c.baseRot.x + this.smooth.y * 0.05
    })

    this.renderer.render(this.scene, this.camera)
  }

  /* ===========================  EVENTS  ============================= */

  _onMouse(e) {
    this.mouse.x = (e.clientX / window.innerWidth  - 0.5) * 2
    this.mouse.y = (e.clientY / window.innerHeight - 0.5) * 2
  }

  _onResize() {
    this.width  = window.innerWidth
    this.height = window.innerHeight
    this.camera.aspect = this.width / this.height
    this.camera.updateProjectionMatrix()
    this.renderer.setSize(this.width, this.height)
  }

  dispose() {
    this.disposed = true
    cancelAnimationFrame(this._raf)
    window.removeEventListener('resize',    this._onResize)
    window.removeEventListener('mousemove', this._onMouse)
    this.scene.traverse(obj => {
      if (obj.geometry) obj.geometry.dispose()
      if (obj.material) {
        const ms = Array.isArray(obj.material) ? obj.material : [obj.material]
        ms.forEach(m => m.dispose())
      }
    })
    this.renderer.dispose()
  }
}
