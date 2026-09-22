// Physical AI and the magnet supply chain: the physics behind the supplier decisions.
// Build:  typst compile lesson.typ lesson.pdf   (figures: cd scripts && python -m lesson.figures)

#set document(title: "Physical AI and the magnet supply chain: the physics behind the supplier decisions", author: "AIInvestment research engine")
#set page(paper: "a4", margin: (x: 2.2cm, y: 2.4cm), numbering: "1", number-align: center,
  header: context { if counter(page).get().first() > 1 [ #text(size: 8pt, fill: gray)[Physical AI and the magnet supply chain — a physics lesson for an investor · 2026-09-22] ] })
#set text(font: "Libertinus Serif", size: 10.5pt, lang: "en")
#show math.equation: set text(font: "New Computer Modern Math")
#set math.equation(numbering: "(1)")
#set heading(numbering: "1.1")
#show heading.where(level: 1): it => { pagebreak(weak: true); v(6pt); text(size: 18pt, weight: 700)[#it]; v(8pt) }
#show heading.where(level: 2): it => { v(10pt); text(size: 12.5pt, weight: 700)[#it]; v(4pt) }
#set par(justify: true, leading: 0.62em)
#show figure.caption: set text(size: 9pt)
#show link: set text(fill: rgb("#1f4e79"))

#let investor(body) = block(fill: rgb("#eef4fa"), stroke: (left: 3pt + rgb("#1f4e79")), inset: (x: 10pt, y: 8pt), radius: 2pt, width: 100%)[
  #text(weight: 700, fill: rgb("#1f4e79"))[Investor consequence.] #body ]
#let worked(body) = block(fill: rgb("#f7f7f2"), stroke: 0.5pt + rgb("#bbb"), inset: 9pt, radius: 2pt, width: 100%)[
  #text(weight: 700)[Worked number.] #body ]
#let caveat(body) = block(fill: rgb("#fdf3ec"), stroke: (left: 3pt + rgb("#e67e22")), inset: (x: 10pt, y: 7pt), radius: 2pt, width: 100%)[
  #text(weight: 700, fill: rgb("#b9581a"))[Label.] #body ]

// ------------------------------------------------------------------------------------------
#align(center)[
  #v(3cm)
  #text(size: 24pt, weight: 700)[Physical AI and the magnet supply chain]
  #v(4pt)
  #text(size: 15pt)[The physics and the mathematics behind the supplier decisions]
  #v(14pt)
  #text(size: 11pt)[A lesson for an investor who reads papers · Compiled 22 September 2026]
  #v(6pt)
  #text(size: 10pt, fill: gray)[Companion to the explainer doc _Physical AI and the magnet supply chain — investor explainer_. Educational research only; not investment advice.]
]
#v(1.5cm)

#block(inset: (x: 1.2cm))[
  #text(weight: 700)[What this document does.] It derives, rather than asserts, the six results that decide who wins the race to put permanent magnets into humanoid robots: why Nd#sub[2]Fe#sub[14]B has no cheap rival, why motor heat forces dysprosium and terbium into the magnet, why coercivity is a defect property that grain-boundary diffusion can exploit, why the joint architecture of a robot is also its rare-earth bill, and why separating adjacent lanthanides costs so many stages that a 98% Chinese share in heavy separation is chemistry as much as policy. Each chapter ends with the consequence for a supplier decision.

  #text(weight: 700)[How the numbers were produced.] Every curve in the figures is computed by `scripts/lesson/magnetics.py`, which has a unit test per function (`scripts/tests/test_lesson_magnetics.py`). Every literature constant is cited to a paper or page opened on 22 September 2026; the bibliography lists only sources verified through the Crossref DOI registry, a publisher page, or the open-access text. Where a number is a modelling assumption rather than a measurement it is labelled as such in an orange _Label_ box.

  #text(weight: 700)[Notation.] SI units. $bold(B)$ is flux density (T), $bold(H)$ the magnetic field (A/m), $bold(M)$ the magnetisation (A/m) and $bold(J) = mu_0 bold(M)$ the polarisation (T); $mu_0 = 4 pi times 10^(-7)$ H/m. Fields quoted in tesla are $mu_0 H$. Coercivity: $H_(c J)$ is where $J$ crosses zero (intrinsic coercivity), $H_(c B)$ where $B$ does. 1 kOe = 79.58 kA/m; 1 MGOe = 7.958 kJ/m#super[3] @wiki-bhmax.
]

#pagebreak()
#outline(indent: 1.2em, depth: 2)

// ==========================================================================================
= From tokens to torque: why physical AI is a metallurgy problem

Digital AI is limited by compute, memory and electricity. Physical AI takes the same transformer models, feeds them cameras and language, and has them emit joint torques instead of tokens. The brain stays in silicon; the body is 20 to 50 electric motors, and every one of them is built around a sintered Nd–Fe–B permanent magnet @fai2026. A humanoid carries 2 to 4.5 kg of such magnet, the lower figure for high-gear-ratio joints and the higher for quasi-direct-drive joints, which works out to 0.57 to 1.3 kg of neodymium–praseodymium and 35 to 79 g of dysprosium per robot under the assumption of H- and SH-grade magnets with 50% dysprosium thrifting @fai2026.

Those four numbers (magnet mass, gear ratio, magnet grade, dysprosium thrifting) are not marketing choices. Each is fixed by a physical relation that this document derives:

#table(columns: (auto, 1fr, auto), stroke: 0.4pt + gray, inset: 6pt, align: (left, left, left),
  [*Decision*], [*Physics that fixes it*], [*Chapter*],
  [Which magnet material], [Energy product bound $(B H)_max <= B_r^2 slash 4 mu_0$ and the anisotropy field $H_A = 2 K_1 slash mu_0 M_s$], [2, 3],
  [Which grade (N, H, SH, UH)], [Load line versus the temperature-shifted knee of the $J(H)$ curve], [4],
  [How much Dy or Tb], [Coercivity is set by nucleation at grain surfaces: $H_c = alpha H_A - N_"eff" M_s$; diffusion depth $prop sqrt(D t)$], [5],
  [Joint architecture], [Air-gap shear stress: $tau = 2 pi r_g^2 l sigma$; magnet mass $prop tau slash N$], [6],
  [Who can refine the heavy elements], [Separation factor $beta$ near 1 and the Fenske stage count $N prop 1 slash ln beta$], [7],
)

#investor[The supply chain that matters is not "rare earths". It is a specific crystal (Nd#sub[2]Fe#sub[14]B), a specific defect-engineering process (grain-boundary diffusion of Dy or Tb), and a specific chemistry (hundreds of solvent-extraction stages). A company's position in the race is its position on those three, not on a mine.]

// ==========================================================================================
= Magnetostatics of a permanent magnet

== Fields, magnetisation and the demagnetising field

Inside matter the three field quantities are related by
$ bold(B) = mu_0 (bold(H) + bold(M)) = mu_0 bold(H) + bold(J). $ <eq:bhm>
Two of Maxwell's equations govern a magnet with no free current: $nabla dot bold(B) = 0$ and $nabla times bold(H) = 0$. The second means $bold(H)$ is conservative, so around any closed loop $integral.cont bold(H) dot d bold(l) = 0$. The first, applied to a uniformly magnetised body, forces $bold(H)$ inside the body to point _against_ $bold(M)$: the magnet is the source of a field that opposes its own magnetisation. For an ellipsoid this demagnetising field is uniform,
$ bold(H)_d = -N bold(M), $ <eq:demag>
with $N$ the demagnetising factor: $1 slash 3$ for a sphere, 1 for a thin plate magnetised through its thickness, and 0 for a long rod magnetised along its axis @wiki-demag @cullity2009. A thin magnet magnetised through its thickness, which is exactly the shape of a motor magnet, sits in the worst possible self-field. That geometric fact is the root of every thermal problem in Chapter 4.

== The magnetic circuit and the load line

Consider a magnet of length $l_m$ and cross-section $A_m$ driving flux across an air gap of length $l_g$ and area $A_g$ through an ideal iron yoke (infinite permeability, no leakage). Ampère's law around the circuit, with no current, gives
$ H_m l_m + H_g l_g = 0, $ <eq:ampere>
and flux continuity gives $B_m A_m = B_g A_g$ with $B_g = mu_0 H_g$ in the gap. Eliminating the gap quantities:
$ B_m = - mu_0 (l_m A_g) / (l_g A_m) H_m equiv - mu_0 P_c H_m. $ <eq:loadline>
Equation @eq:loadline is the _load line_: a straight line through the origin of the second quadrant of the $B$–$H$ plane whose slope, $-mu_0 P_c$, is fixed entirely by geometry. $P_c$ is the permeance coefficient. A long thin magnet in a short gap has a high $P_c$ and operates near $B_r$; a thin plate in a wide gap has a low $P_c$ and operates far down its curve, in a large reverse field. The operating point is the intersection of the load line with the magnet's own $B(H)$ curve @hendershot2010 @coey2010.

The "infinite permeability" yoke is the one idealisation an investor should not forget. Real electrical steel saturates: the flux density in a stator tooth cannot usefully exceed the saturation polarisation of iron, about 2 T @cullity2009, and a motor is normally designed with its teeth close to that limit. Once the steel is saturated, extra remanence from a better magnet grade buys nothing; the flux has nowhere to go. In a steel-limited design a grade upgrade is bought for coercivity, i.e. for temperature margin (Chapter 4), not for torque. Whether a given motor is magnet-limited or steel-limited is a question a supplier can answer in one sentence and a spec sheet cannot.

== Why the energy product is the figure of merit

The magnetostatic energy stored in the gap is $B_g^2 V_g slash 2 mu_0$, with $V_g = A_g l_g$. Work with twice that quantity (the factor $1 slash 2$ would appear on both sides and cancel). Using @eq:ampere and flux continuity,
$ B_g^2 V_g / mu_0 = (B_g A_g)(H_g l_g) = (B_m A_m)(-H_m l_m) = (-B_m H_m) V_m . $ <eq:energy>
So the magnet volume needed to hold a given field in a given gap is
$ V_m = (B_g^2 V_g) / (mu_0 (-B_m H_m)) . $ <eq:volume>
The magnet is smallest when the product $-B H$ at the operating point is largest. That product, maximised over the second quadrant, is the energy product $(B H)_max$ @wiki-bhmax. Everything a motor designer buys from a magnet maker is compressed into that one number and the temperature at which it survives.

== Anatomy of the loop

#figure(image("fig/f10_loop_anatomy.svg", width: 78%), caption: [The intrinsic loop $J(H)$ (solid) and the normal loop $B(H) = J + mu_0 H$ (dashed) of a hard magnet. $B_r$ is the remanence, $H_(c J)$ the field that reverses the polarisation, $H_(c B)$ the smaller field at which $B$ itself crosses zero. Computed from a smooth model loop; the shape, not the numbers, is the lesson.]) <fig:loop>

The intrinsic curve $J(H)$ is the material; the normal curve $B(H)$ is what the circuit sees. For a well-made magnet $J$ stays flat at $B_r$ deep into the second quadrant and then collapses at the _knee_, near $H_(c J)$. Along the flat part, with a small recoil permeability $mu_r$ close to 1,
$ B(H) = B_r + mu_0 mu_r H, quad H <= 0, $ <eq:linear>
so the energy product along the line is $-B H = -(B_r + mu_0 mu_r H) H$, maximised at $H = -B_r slash (2 mu_0 mu_r)$:
$ (B H)_max = B_r^2 / (4 mu_0 mu_r) <= B_r^2 / (4 mu_0) . $ <eq:bhmax>
The bound is reached only if the knee lies beyond the optimum point, i.e. if $mu_0 H_(c J) > B_r slash 2$ roughly. A magnet with a high remanence but a low coercivity never reaches its own bound: this is why alnico, whose remanence is comparable to Nd–Fe–B's but whose coercivity is small, never comes close to its own bound @cullity2009.

#worked[For Nd#sub[2]Fe#sub[14]B the room-temperature saturation polarisation is $J_s = 1.60$ T @hirosawa2017. Equation @eq:bhmax with $B_r = J_s$ and $mu_r = 1$ gives $(1.60)^2 slash (4 times 4 pi times 10^(-7)) = 509$ kJ/m#super[3], exactly the theoretical maximum listed by Hirosawa et al. @hirosawa2017. Commercial sintered grades reach 200 to 440 kJ/m#super[3] @wiki-ndfeb because real remanence is below $J_s$ (grain misalignment, non-magnetic grain-boundary phase, porosity) and because the knee truncates the curve at high temperature.]

#figure(image("fig/f01_energy_product.svg", width: 78%), caption: [The energy-product ceiling $B_r^2 slash 4 mu_0$ against remanence. The Nd#sub[2]Fe#sub[14]B point reproduces the 509 kJ/m#super[3] theoretical value; the band is the commercial sintered range @wiki-ndfeb.]) <fig:bh>

#investor[The magnet is a volume-per-torque device. A 10% loss of remanence (from heat, from cerium substitution, from a cheaper grade) is a 19% loss of energy product by @eq:bhmax, and by @eq:volume a 23% larger magnet to do the same job. Small changes in $B_r$ are large changes in the bill of materials.]

// ==========================================================================================
= Why Nd#sub[2]Fe#sub[14]B has no cheap rival

== Where the remanence comes from

The compound discovered in 1984 @sagawa1984 @croat1984 is tetragonal Nd#sub[2]Fe#sub[14]B: 14 iron atoms carry most of the moment, and the two neodymium atoms add to it because the light rare-earth 4f moment couples parallel to the iron moment. The result is a saturation polarisation of 1.60 T, a saturation magnetisation $M_s = 1.28$ MA/m, and a Curie temperature of 586 K @hirosawa2017 @susner2015; the single-crystal magnetisation and anisotropy of the whole R#sub[2]Fe#sub[14]B family were mapped in the two years after the discovery @hirosawa1986 @grossinger1986. The heavy rare earths (Gd onward) couple _antiparallel_ to the iron, which is why substituting them lowers the remanence, a point Chapter 4 returns to.

== Where the coercivity comes from: magnetocrystalline anisotropy

A ferromagnet's energy depends on the direction of $bold(M)$ relative to the crystal axes. For a uniaxial crystal with easy axis $c$ and angle $theta$ between $bold(M)$ and $c$,
$ E_a = K_1 sin^2 theta + K_2 sin^4 theta + dots, $ <eq:anis>
and for Nd#sub[2]Fe#sub[14]B at room temperature $K_1 = 4.3$ MJ/m#super[3] @hirosawa2017. The physical origin is the strongly aspherical 4f charge cloud of the Nd#super[3+] ion sitting in the crystal's electric field; spin–orbit coupling locks the Fe–Nd spin system to the orientation that cloud prefers @haskel2005 @herbst1991. Density-functional calculations overestimate $K_1$ (about 8 MJ/m#super[3] against the measured 4.3) because thermal disorder of the 4f moments already matters at 300 K @susner2015, which is a first hint that anisotropy, and hence coercivity, is the temperature-fragile property.

The field needed to rotate $bold(M)$ away from the easy axis against $K_1$ is the _anisotropy field_. Write the energy per unit volume with a field of magnitude $H$ applied _against_ $bold(M)$, so that the Zeeman term is $+ mu_0 M_s H cos theta$: $E = K_1 sin^2 theta + mu_0 M_s H cos theta$. The aligned state $theta = 0$ stops being a minimum when $partial^2 E slash partial theta^2 |_(theta = 0) = 2 K_1 - mu_0 M_s H = 0$, which gives
$ H_A = (2 K_1) / (mu_0 M_s) . $ <eq:ha>

#worked[With $K_1 = 4.3$ MJ/m#super[3] and $M_s = 1.28$ MA/m, @eq:ha gives $H_A = 5.35$ MA/m, i.e. $mu_0 H_A = 6.7$ T. Hirosawa et al. list 5.33 MA/m @hirosawa2017. The 1984 pulsed-field measurement gave a larger 12 MA/m for Nd#sub[2]Fe#sub[14]B and found the maximum anisotropy field of the whole R#sub[2]Fe#sub[14]B series in Tb#sub[2]Fe#sub[14]B at 28 MA/m @yamamoto1984; the absolute values depend on the extrapolation method, but the ratio Tb : Nd of about 2.3 by the same method is the number that matters for Chapter 5.]

== The Stoner–Wohlfarth limit

For a single-domain particle whose magnetisation rotates coherently, the energy is $E = K_u V sin^2(phi - theta) - mu_0 M_s V H cos phi$ @stoner1948 @wiki-sw. With the field antiparallel to the easy axis, the particle switches exactly at $H = H_A$; for a random assembly of such particles the coercivity is $0.48 H_A$ @wiki-sw. This is the ceiling: no magnet can have a coercivity above its anisotropy field, and a perfect aligned magnet would switch at $H_A$ itself. Real sintered Nd–Fe–B switches at a fifth of that (Chapter 5).

== The competition, in the same units

#table(columns: (auto, auto, auto, auto), stroke: 0.4pt + gray, inset: 6pt,
  [*Material*], [*Why it loses to Nd–Fe–B*], [*Where it still wins*], [*Source*],
  [Hard ferrite], [Energy product about 1/18 of sintered Nd–Fe–B by volume: the ferrite motor for the same torque is several times heavier], [Cost; positive $beta$ (coercivity _rises_ with temperature)], [@wiki-ndfeb @bunting],
  [Sm–Co (2:17)], [Lower $J_s$ so lower $(B H)_max$; cobalt and samarium cost; samarium export-licensed since April 2025], [Curie temperature 720 °C; small $alpha$ and $beta$; radiation and corrosion resistance], [@wiki-ndfeb @bunting @chinabriefing],
  [Alnico], [Coercivity of a few tens of kA/m: the knee truncates @eq:bhmax], [Temperature stability], [@bunting],
  [Ce-substituted Nd–Fe–B], [For $x = 0.38$ Ce on the Nd site, $H_A$ at 400 K falls from 5.5 to 4.7 T and $T_C$ from 586 to 543 K @susner2015], [Cerium is the cheap by-product of every Nd mine], [@susner2015],
  [Rare-earth-free motors], [Induction and reluctance machines exist @widmer2015 but carry a torque-density penalty that a 2 t car can hide and a 30 kg robot cannot], [Cost, supply security], [@widmer2015],
)

The wider landscape of hard, soft and energy-conversion magnetic materials is reviewed in @gutfleisch2011. Nanostructured exchange-spring magnets (hard phase plus soft high-moment phase) were predicted to exceed 1 MJ/m#super[3] @skomski1993 and remain a laboratory result thirty years later; the gap between ferrite and Nd–Fe–B, the "plugging the gap" problem @coey2012, is still open.

#investor[There is no substitution story at the top of the performance range: every alternative in the table above loses on remanence, on coercivity, or on both, and the energy-product bound @eq:bhmax is squared in remanence. The substitution stories that are real are _downward_: cerium for cost, ferrite where torque density does not matter. A robot joint is the application where torque density matters most, so it is the last place substitution arrives.]

// ==========================================================================================
= Heat: why the grade ladder exists and why it runs on dysprosium

== Reversible temperature coefficients

Between room temperature and the working temperature both remanence and coercivity fall approximately linearly:
$ B_r (T) = B_r (T_0) [1 + alpha (T - T_0)], quad H_(c J) (T) = H_(c J) (T_0) [1 + beta (T - T_0)] . $ <eq:tempco>
For sintered Nd–Fe–B, $alpha approx -0.12$ %/°C and $beta approx -0.55$ to $-0.65$ %/°C; for Sm–Co, $alpha approx -0.04$ and $beta approx -0.2$ to $-0.4$; ferrite has $alpha approx -0.20$ but a _positive_ $beta approx +0.27$ %/°C @bunting. Hirosawa et al. quote about $-0.5$ %/K for the coercivity of Nd–Dy–Fe–B @hirosawa2017. The asymmetry is the whole story: at 120 °C an Nd–Fe–B magnet has lost 12% of its remanence but 60% of its coercivity. Remanence loss costs torque; coercivity loss costs the magnet its life.

#figure(image("fig/f04_temp_coefficients.svg", width: 92%), caption: [Normalised remanence and coercivity against temperature from @eq:tempco with the coefficients in @bunting. Nd–Fe–B's coercivity collapses fastest; ferrite's rises.])

== The knee crossing

The operating point sits where the load line @eq:loadline crosses $B(H)$. As the magnet heats, $B_r$ falls a little and the knee marches toward the origin. When the knee reaches the load line, the polarisation at the operating point starts to collapse and the loss is _irreversible_: cooling the magnet does not restore it, because the reversed grains stay reversed. The design rule is therefore not "stay below the Curie temperature" (586 K) but "keep the operating field a safe margin inside the knee at the hottest point of the duty cycle".

#figure(image("fig/f02_demag_temperature.svg", width: 85%), caption: [Second-quadrant curves of an N-type magnet ($B_r$ 1.40 T, $H_(c J)$ 12 kOe at 20 °C, $alpha = -0.12$, $beta = -0.60$ %/°C) at four temperatures, with load lines for $P_c$ = 1, 2 and 5. By 120 °C the knee has crossed the $P_c$ = 1 and 2 lines. The knee shape is a smooth model; the coefficients are from @bunting and @radial.]) <fig:knee>

#caveat[The "highest safe temperature" curves below use a toy criterion: the operating field on the load line, times a 20% margin, must stay below $H_(c J)(T)$. Manufacturers rate grades more conservatively (they use the actual knee field, which lies below $H_(c J)$, and specific test geometries), so the absolute temperatures here run higher than nominal ratings. The _ordering_ and the _slope_ against $P_c$ are the physics; the absolute values are the model.]

#figure(image("fig/f03_safe_temperature.svg", width: 82%), caption: [Highest safe temperature against permeance coefficient for five grades, from `max_safe_temperature()` with the minimum coercivities of the class table @radial. Two levers move the ceiling: the grade (vertical spacing) and the circuit design (slope).]) <fig:safe>

#worked[At $P_c = 2$ the toy criterion gives 120 °C for N (12 kOe), 155 °C for H (17 kOe), 163 °C for SH (20 kOe) and 172 °C for UH (25 kOe). The nominal class ratings are 80, 120, 150 and 180 °C @radial. Each class step (N to M, M to H, H to SH, and so on) adds 3 to 5 kOe of coercivity and 20 to 30 °C of nominal rating @radial, and each step costs more dysprosium or terbium.]

== Why the fix is dysprosium

Coercivity is proportional to the anisotropy field, for reasons Chapter 5 derives (@eq:kronmuller). The heavy rare earths raise $H_A$: by the 1984 single-method comparison, Tb#sub[2]Fe#sub[14]B has about 2.3 times the anisotropy field of Nd#sub[2]Fe#sub[14]B @yamamoto1984, so substituting Dy or Tb for part of the Nd pushes the knee outward at every temperature; the proportionality of coercivity to anisotropy field in Dy-substituted sintered magnets was established directly in 1987 @sagawa1987, and the intrinsic properties of the (Nd,Dy)#sub[2]Fe#sub[14]B series are still being refined in high-field work @kostyuchenko2020. Per gram, terbium is the more effective of the two: about 2.5 g of dysprosium does the coercivity work of 1 g of terbium @fai2026, and terbium is the scarcer and dearer element.

The cost is remanence. The heavy rare-earth 4f moment couples antiparallel to the iron sublattice, so each Dy atom subtracts moment: in (Nd#sub[2−x]Dy#sub[x])Fe#sub[14]B the formula-unit moment falls from 25.50 $mu_B$ at $x = 0$ to 23.48 at $x = 0.25$ and 21.03 at $x = 0.5$, while coercivity roughly doubles @haider2021. Dy occupies the 4f rare-earth site specifically @haider2021. By @eq:bhmax the remanence penalty is squared in the energy product. This trade, coercivity up and energy product down, is the whole reason the industry moved from alloying Dy through the bulk to placing it only where it is needed.

#investor[A magnet grade is a dysprosium content, and the grade is chosen by the motor's hottest duty point on the load line. Two suppliers can move the bill: the magnet maker, by getting the same coercivity with less Dy (Chapter 5), and the motor maker, by raising $P_c$ or improving cooling so a lower grade survives (Chapter 6). Ask both which lever they own.]

// ==========================================================================================
= Coercivity is a defect property: Brown's paradox and grain-boundary diffusion

== Brown's paradox

The Stoner–Wohlfarth ceiling says a perfect aligned crystal reverses only at $H_A$: 5.3 MA/m for Nd#sub[2]Fe#sub[14]B. A commercial N-grade sintered magnet reverses at 12 kOe, i.e. 0.95 MA/m, less than a fifth of $H_A$. This shortfall, general to all hard magnets, was pointed out by Brown in 1945 @brown1945: reversal does not happen by coherent rotation of a whole grain but by _nucleation_ of a reversed domain at some defect where the local anisotropy is reduced or the local field is enhanced, followed by domain-wall propagation. Once one grain reverses, it seeds its neighbours unless something isolates them.

Kronmüller's analysis of nucleation in inhomogeneous ferromagnets @kronmuller1987, applied to Nd–Fe–B by Kronmüller, Durst and Sagawa @kronmuller1988, condenses the microstructure into two parameters:
$ H_c = alpha H_A - N_"eff" M_s . $ <eq:kronmuller>
The form follows from two superpositions. First, nucleation happens where it is easiest: in a surface layer whose anisotropy constant is reduced to $K_1' < K_1$ (disorder, oxidation, a few nanometres of off-stoichiometry), the Stoner–Wohlfarth switching field of that layer is $2 K_1' slash mu_0 M_s = alpha_K H_A$ with $alpha_K = K_1' slash K_1 < 1$; misalignment of the grain axis to the field lowers it by a further factor $alpha_psi$, and $alpha = alpha_K alpha_psi$. Second, the field that actually acts at a grain edge is the applied field plus the local stray field of the grain's own magnetisation, $-N_"eff" M_s$; reversal begins when their sum reaches the reduced switching field, so the applied field needed is $alpha H_A$ _minus_ the stray-field help @kronmuller1987 @kronmuller1988. Both $alpha$ and $N_"eff"$ are properties of the grain _surface_ and its geometry, not the grain interior.

#worked[Take $H_(c J) = 0.95$ MA/m, $H_A = 5.35$ MA/m, $M_s = 1.28$ MA/m and, illustratively, $N_"eff" = 1$: @eq:kronmuller gives $alpha = (0.95 + 1.28) slash 5.35 = 0.42$. The fitted values in the literature vary with grain size and processing; the point is that $alpha$ sits far below 1, and that the term $N_"eff" M_s$ costs a full MA/m. At these values the reduced surface anisotropy accounts for about 70% of the shortfall from $H_A$ ($3.1$ MA/m) and the stray-field term for about 30% ($1.3$ MA/m).]

#figure(image("fig/f05_kronmuller.svg", width: 82%), caption: [Coercivity against anisotropy field in the Kronmüller form @eq:kronmuller for three values of $alpha$, against the Stoner–Wohlfarth line. The N-grade point sits at a ratio of 0.18. The dashed line marks the anisotropy field of a Tb-rich shell, about 2.3 times Nd's by the same measurement @yamamoto1984.]) <fig:kron>

Equation @eq:kronmuller is the whole coercivity strategy of the last twenty years in one line @hono2012:
1. _Raise $H_A$ at the surface_, where nucleation starts, with Dy or Tb. Because $H_c prop alpha H_A$, a shell with 2.3 times the anisotropy field multiplies the coercivity of the grain even if the core is untouched.
2. _Isolate the grains_ with a non-ferromagnetic grain-boundary phase so a reversed grain cannot seed its neighbour. Atom-probe work showed the Nd-rich boundary phase in a standard sintered magnet is thin and itself ferromagnetic, which is why isolation is imperfect @sepehriamin2012.
3. _Shrink the grains_ so the stray-field term $N_"eff" M_s$ at edges is smaller; Nakamura et al. showed that very small sintered magnets, and by extension the surface treatment that became grain-boundary diffusion, gain coercivity this way @nakamura2005.

== Grain-boundary diffusion

Instead of alloying Dy through the bulk (which pays the remanence penalty of Chapter 4 everywhere), grain-boundary diffusion (GBD) coats a finished magnet with a Dy or Tb compound (fluoride, oxide, or a low-melting Dy–Ni–Al alloy @oono2011), then anneals it below the sintering temperature. The heavy element travels along the liquid Nd-rich grain boundaries far faster than through the grains and substitutes into the outer layer of each Nd#sub[2]Fe#sub[14]B grain, forming a core–shell structure with a (Nd,Dy)#sub[2]Fe#sub[14]B or (Nd,Tb)#sub[2]Fe#sub[14]B shell of high $H_A$ around a Dy-free core of full remanence @lu2019 @hono2012 @stanford. One vendor description quotes more than a 50% reduction of the coercivity loss at 150 °C for such magnets @stanford.

The transport is Fick's second law, $partial C slash partial t = D partial^2 C slash partial x^2$, and for a constant surface source in a semi-infinite body the solution is @crank1975
$ C(x, t) = C_0 op("erfc") ( x / (2 sqrt(D t)) ) . $ <eq:erfc>
The penetration depth scales as $sqrt(D t)$: doubling the depth costs four times the furnace time. This is why GBD works on thin parts. The uniform core–shell layer in a Tb-diffused magnet lies about 300 to 1000 µm below the surface @lu2019, and extending useful treatment to thicker plates required a dedicated low-melting diffusion source @oono2011.

#figure(image("fig/f06_gbd_profile.svg", width: 80%), caption: [Heavy rare-earth concentration along grain boundaries against depth from @eq:erfc for three anneal times with an illustrative effective diffusivity. The band marks the depth range of the uniform core–shell layer reported by Lu et al. @lu2019.]) <fig:gbd>

#caveat[The diffusivity in the figure is illustrative, chosen to place the shell at the reported depth; it is not a measured grain-boundary diffusion coefficient. The $sqrt(D t)$ scaling is exact; the constant is not.]

#investor[GBD is the reason heavy rare-earth demand per magnet can halve without changing the magnet's rating, which is the "50% dysprosium thrifting" behind every per-robot estimate @fai2026. It works best on thin magnets, and motor magnets are thin arc segments: the process and the application fit. Whether a Western magnet plant runs GBD in-house, under licence, or not at all decides whether it makes a competitive SH/UH magnet or an expensive one. Ask for the coercivity per gram of Dy, not the coercivity.]

// ==========================================================================================
= The motor: why the joint architecture is the rare-earth bill

== Torque from shear stress in the air gap

A conductor of length $l$ carrying current $I$ in a field $B$ feels the Lorentz force $F = B I l$. Spread the stator conductors around the air gap as a linear current density $K_s$ (ampere-turns per metre of circumference) facing a gap flux density $B_g$ from the rotor magnets: the tangential force per unit gap area is a _shear stress_ $sigma = B_g K_s$, and the torque on a rotor of gap radius $r_g$ and active length $l$ is the stress times the gap area times the lever arm,
$ tau = sigma (2 pi r_g l) r_g = 2 pi r_g^2 l sigma . $ <eq:shear>
This is the sizing equation of every permanent-magnet machine @hendershot2010, and the form Wensing et al. use for actuator scaling @wensing2017. Two things follow immediately. Torque per unit rotor volume is $2 sigma$, independent of size. And $B_g$, which is proportional to the magnet's remanence at the operating point, enters $sigma$ linearly: a 10% loss of $B_r$ is a 10% loss of torque at the same current, or, at the same torque, $1 slash 0.9$, i.e. 11% more current and $(1 slash 0.9)^2 - 1 = 23%$ more copper loss.

== The thermal limit sets the shear stress

Copper loss per unit gap area is proportional to $K_s^2$ (resistance times current squared per metre of periphery). At a fixed cooling capacity, $K_s$ is therefore capped, and with it the shear stress: $sigma_max = B_g K_(s, max)$. For a family of motors of the same construction and cooling, $sigma$ is constant and @eq:shear says $tau prop r_g^2 l$ @wensing2017. Torque per unit mass then scales as $r_g$ in the dimensional analysis; the catalogue data Wensing et al. fitted give $r_g^0.8$ for torque density, $r_g^1.6$ for torque per rotor inertia and $r_g^3 l$ for the torque-production efficiency $tau^2 slash I^2 R$ @wensing2017. Larger gap radius means more torque per kilogram and far more torque per unit inertia, at the cost of a bigger, heavier joint.

One loss mechanism sits inside the magnet itself. Sintered Nd–Fe–B is a metal, so the slot harmonics and switching ripple of the stator induce eddy currents in the rotor magnets and heat them, precisely the component whose coercivity is the most temperature-fragile (Chapter 4). Designers answer by segmenting each pole into several insulated pieces, which cuts the eddy loss but multiplies the machining, coating and assembly cost per pole @hendershot2010. The same segmentation makes each piece thinner, which is what grain-boundary diffusion wants (Chapter 5): the loss-driven and the coercivity-driven reasons for small magnets point the same way.

== Magnet mass per joint and the gear ratio

A joint needs torque $tau_j$. Behind a reducer of ratio $N$ the motor supplies $tau_m = tau_j slash N$. At constant shear stress the rotor volume, and so the magnet volume on it, is proportional to $tau_m$:
$ m_"magnet" prop tau_j / N . $ <eq:gear>
A harmonic or cycloidal joint needs an order of magnitude less motor, and magnet, than a quasi-direct-drive (QDD) joint for the same joint torque; the ratios used below, $N approx 50$–100 for the geared joint and $N approx 6$–10 for QDD, are typical values chosen for illustration, not measured on a particular robot. The published per-robot figures, 2 kg for high-ratio designs against 4.5 kg for QDD @fai2026, differ by less than @eq:gear alone predicts because QDD designs also use larger gap radii (@eq:shear: torque $prop r_g^2$) and thinner magnets, but the direction is the same and it is not small.

#figure(image("fig/f07_motor_scaling.svg", width: 96%), caption: [Left: magnet mass per joint against gear ratio from @eq:gear for a 100 N m joint (constant of proportionality illustrative). Right: torque density against gap radius, dimensional ($r_g^1$) and empirical ($r_g^0.8$) @wensing2017.]) <fig:motor>

Why would anyone choose QDD and pay ten times the magnet? Because the reflected inertia of the motor at the joint scales as $N^2$, and a high-ratio joint is stiff, slow to back-drive and destructive on impact. Wensing et al. define an _impact mitigation factor_ from the ratio of the reflected actuator inertia to the locked-joint inertia @wensing2017; a low ratio lets the leg absorb a foot strike and lets the controller feel contact through motor current (proprioception) instead of through a fragile force sensor. Walking robots want QDD at the hips and knees; manipulation wants it at the wrists. The magnet bill follows the biomechanics.

#investor[The robot maker's choice of reducer is its choice of magnet mass, and the two are public: a QDD humanoid needs roughly twice the magnet of a geared one @fai2026. Watch the reducer suppliers (harmonic and cycloidal drives are a second, Japan-centred chokepoint) as closely as the magnet suppliers, and read every torque-density claim for the gap radius it assumes.]

// ==========================================================================================
= Separating the heavy elements: why 98% is chemistry

== The lanthanide contraction and the separation factor

The fifteen lanthanides @wiki-ree differ by one 4f electron each, and 4f electrons are buried inside the ion; the ions are all trivalent and their radii shrink steadily and only slightly along the row (the lanthanide contraction). Chemically they are near-identical, which is why they were once called "rare earths" and were separated by hundreds of fractional crystallisations. Modern separation is liquid–liquid extraction @xie2014: an aqueous chloride or nitrate solution is mixed with an organic phase containing an acidic organophosphorus extractant (D2EHPA/P204, or 2-ethylhexyl phosphonic acid mono-2-ethylhexyl ester, EHEHPA/P507), the metal partitions into the organic phase by a reaction of the form
$ "RE"^(3+) + 3 ("HL")_2 arrows.lr "RE"("HL"_2)_3 + 3 "H"^+ , $ <eq:sx>
and the two phases are separated. The distribution ratio $D = ["RE"]_"org" slash ["RE"]_"aq"$ rises steeply with pH and with extractant concentration, and rises with atomic number. The selectivity between two elements A and B is the _separation factor_
$ beta_(A slash B) = D_A / D_B . $ <eq:beta>
For adjacent lanthanides $beta$ is close to 1. Ismail et al. tabulate the values for both industrial extractants in chloride medium @ismail2019:

#table(columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto, auto), stroke: 0.4pt + gray, inset: 4.5pt, align: center,
  [*Pair*], [Pr/Nd], [Nd/Sm], [Sm/Eu], [Eu/Gd], [Gd/Tb], [Tb/Dy], [Dy/Ho], [Ho/Er], [Er/Tm], [Tm/Yb], [Yb/Lu],
  [*P507 (EHEHPA)*], [1.17], [2.00], [1.96], [1.46], [2.35], [1.62], [2.58], [1.25], [1.33], [1.12], [1.13],
  [*P204 (D2EHPA)*], [1.06], [4.86], [2.23], [1.69], [1.60], [1.42], [1.24], [1.70], [1.50], [1.30], [1.03],
)

Two pairs matter for magnets: Pr/Nd, which is so hard (1.17 with P507, 1.06 with P204) that industry sells the pair together as "didymium" NdPr, and Tb/Dy at 1.62, which is separable but sits in a row of heavy elements each of which must be split from the next.

== Counting the stages

One equilibrium contact enriches the organic phase in the heavier element by a factor $beta$. To go from a 50:50 feed to 99.9% purity at both ends requires a cascade of contacts run counter-currently. The stage count follows from one line of algebra that does not care whether the two phases are vapour and liquid or organic and aqueous. At an ideal equilibrium stage the ratio of the two elements in the extract is $beta$ times their ratio in the feed to that stage, by @eq:beta. In a counter-current cascade at total reflux every stage's product is the next stage's feed, so after $n$ stages $(x_A slash x_B)_n = beta^n (x_A slash x_B)_0$. Solving for the $n$ that takes the ratio from its value at the bottom to its value at the top is the Fenske relation, first written for distillation @fenske1932 with the relative volatility in the place of $beta$:
$ N_min = (ln [ (x_"top" / (1 - x_"top")) ((1 - x_"bottom") / x_"bottom") ]) / (ln beta) . $ <eq:fenske>

#worked[For 99.9% purity at both ends the numerator is $ln(999^2) = 13.8$. With P507: Pr/Nd, $beta = 1.17$, needs at least 88 stages; Tb/Dy, $beta = 1.62$, 29 stages; Ho/Er, $beta = 1.25$, 62 stages; Dy/Ho, $beta = 2.58$, 15 stages. Real cascades run at finite reflux, add scrubbing and stripping sections, and must split a feed of a dozen elements into individual products, so plant stage counts are multiples of these lower bounds.]

#caveat[The stage counts assume ideal equilibrium stages, a separation factor that is constant along the cascade, and total reflux. Real $beta$ drifts with concentration and acidity, and a working cascade runs at finite reflux with scrubbing and stripping sections, so these are lower bounds, not plant designs.]

#figure(image("fig/f08_fenske.svg", width: 84%), caption: [Minimum theoretical stages from @eq:fenske against separation factor, with the adjacent-pair values for P507 @ismail2019. The count diverges as $beta -> 1$; the light Pr/Nd pair and the middle-heavy pairs are the expensive ones.]) <fig:fenske>

== Why the heavy end is where the moat is

Three things compound at the heavy end. The feed is small: the world sold 2.7 million kg of dysprosium and 0.8 million kg of terbium in 2024 against 87 million kg of NdPr @fai2026, so a heavy-rare-earth plant is a small plant with a long cascade, and its economics depend on running every stage full. The chemistry is slower: heavy elements bind the extractant more strongly, which makes stripping harder and pushes producers to blended extractants (P507 with Cyanex 272) whose selectivities are proprietary know-how @ismail2019 @arellano2020. And the feedstock is geographically concentrated: more than 90% of heavy rare-earth supply originates from ion-adsorption clays @rex98, and China refines about 98% of heavy rare earths @rex98 against 91% of all refining and 94% of sintered magnets @iea2025. Lynas produced the first commercial dysprosium oxide outside China only in May 2025, and its first terbium in June 2025 @lynas2025 @csis2026; Energy Fuels targets 48 t of Dy oxide and 14 t of Tb oxide a year from late 2026 @energyfuels2025.

#investor[A Western heavy-separation plant is a stage-count problem before it is a mining problem: a Tb/Dy split alone is a 30-stage-plus cascade sized for tens of tonnes a year. Judge a project by its stage count, its extractant chemistry and its feed contract, not by its resource statement. The light end is the easier half of the business for three reasons that the table makes explicit: the Pr/Nd split is simply not attempted (the pair is sold as didymium), the Nd/Sm boundary has $beta = 2.00$ with P507, and the volumes are thirty times larger so a cascade runs full. The Ce/Pr boundary ($beta = 1.09$) is handled in practice by chemistry outside this table, which is not covered here. That is why the West already refines NdPr and why China's April 2025 list left it alone @chinabriefing.]

// ==========================================================================================
= Synthesis: the arithmetic and the decisions

== The dysprosium arithmetic

Per robot, 35 to 79 g of dysprosium @fai2026. Per million robots a year, 35 to 79 t. That is 1.3 to 2.9% of the 2,700 t sold worldwide in 2024, and less than the 1,470 t of Dy-equivalent metal the 2025 electric-vehicle fleet consumed @fai2026. But it is of the same order as the entire funded Western capacity: 48 t of Dy oxide from Energy Fuels from late 2026 @energyfuels2025, rising to about 120 t in 2027–28 and 288 t in 2028–29 if both expansion phases are built @da-energyfuels. The scarcity is regional, not global.

#figure(image("fig/f09_dy_arithmetic.svg", width: 90%), caption: [Dysprosium, tonnes a year, on a log axis: robot demand per million units (metal, @fai2026), the Western oxide-capacity steps @energyfuels2025 @da-energyfuels, EV consumption and world sales @fai2026. Oxide and metal tonnes are not identical; the comparison is indicative.]) <fig:dy>

== Each derivation, one decision

#table(columns: (auto, 1fr, 1fr), stroke: 0.4pt + gray, inset: 6pt, align: (left, left, left),
  [*Result*], [*What it says*], [*What to ask a supplier*],
  [@eq:bhmax, @eq:volume], [Magnet volume $prop 1 slash B_r^2$], [What remanence at the operating temperature, not at 20 °C?],
  [@eq:loadline, @fig:knee], [The knee crossing, not the Curie point, kills the magnet], [What $P_c$ does the motor run at, and what is the hottest duty point?],
  [@eq:tempco], [Coercivity falls five times faster than remanence], [Which grade, and what is the coercivity margin at that duty point?],
  [@eq:kronmuller], [Coercivity is set at grain surfaces], [Coercivity per gram of Dy or Tb; is GBD in-house?],
  [@eq:erfc], [GBD depth $prop sqrt(D t)$], [What magnet thickness does the line handle?],
  [@eq:shear, @eq:gear], [Magnet mass $prop tau_j slash N$; torque $prop r_g^2$], [Which joints are QDD, and who makes the reducers?],
  [@eq:fenske], [Stages $prop 1 slash ln beta$], [Stage count, extractant, and the heavy-feed contract],
)

== What would change this document

Three developments would move the conclusions, and each is observable. A dysprosium-free joint motor at humanoid torque density, whether by a thermally superior motor design (raising $P_c$ or cooling until an H grade suffices), by an exchange-spring or iron-nitride magnet leaving the laboratory @skomski1993 @coey2012, or by a rare-earth-free machine accepting the weight penalty @widmer2015. A Western grain-boundary-diffusion line at scale, since it halves the heavy-element bill at a stroke. And a heavy-separation cascade outside China running at full utilisation, which is a stage-count and feed-contract question, not a geology question. Recycling of end-of-life magnets @binnemans2013 is the only heavy-element supply that can arrive in months rather than years, and it feeds directly into the magnet-to-magnet processes that Western entrants are building.

// ==========================================================================================
= Appendix: reproducibility and labels

*Code.* `scripts/lesson/magnetics.py` implements every relation used here: `bh_max_ideal`, `demag_curve`, `anisotropy_field`, `kronmuller_hc`, `operating_point`, `at_temperature`, `max_safe_temperature`, `fenske_stages`, `erfc_profile`, `torque_from_shear`, `magnet_mass_for_joint`. The tests in `scripts/tests/test_lesson_magnetics.py` pin the worked numbers (509 kJ/m#super[3]; 5.35 MA/m against the literature 5.33 within 1%; 88 stages). `python -m lesson.figures` regenerates every figure and prints the quoted values; `typst compile lesson.typ` rebuilds this PDF.

*Verified versus modelled.* Verified (cited): all material constants, temperature coefficients, grade classes, separation factors, per-robot and market tonnages, and the scaling exponents. Modelled (labelled in orange boxes): the knee shape of the $J(H)$ curve, the 20% knee margin and the resulting absolute safe temperatures, the effective diffusivity in @fig:gbd, and the constant of proportionality in @fig:motor. Not verified this session and therefore not quoted: absolute anisotropy fields of Dy#sub[2]Fe#sub[14]B and Tb#sub[2]Fe#sub[14]B from modern single-crystal work (the 1984 same-method ratio is used instead @yamamoto1984), and the Kronmüller fit parameters of specific commercial grades.

*Disclaimer.* Educational and research material. Not investment advice. The companion explainer doc carries the market, policy and company data with their own sources; this document carries the physics.

#bibliography("refs.yml", style: "ieee", title: "References")
