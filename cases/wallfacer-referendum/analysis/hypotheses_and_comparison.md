# Hypotheses and Comparison Framework

This file lists the specific hypotheses the simulation is designed to test, the measurement protocols for each, and the framework for comparing simulation results against Liu Cixin's novel "The Dark Forest" (黑暗森林).

---

## Part 1: Hypotheses Under Test

### H1 — Faction Stabilization
The ten initial discourse factions identified in the seed (06_discourse_samples.md) will converge to between four and six stable coalitions by day 60, with the remainder either absorbed or collapsed below 2 percent support.

**Measurement**: At days 14, 30, 45, 60, 75, 90, count unique non-overlapping factions with greater-than-2-percent support. Fit a power law to see if distribution narrows.

**Prior**: Strong. Media ecosystems consistently collapse initial diversity into bipolar or tripolar structures within weeks (see Covid-19 discourse, Black Lives Matter 2020).

### H2 — Western Democratic Rejection
A majority of the United States, United Kingdom, France, Germany, Netherlands, Canada, Australia, and Japan publics will oppose the Wallfacer Proposal as originally drafted.

**Measurement**: Model each country's discourse proportions and compute the opposition plurality by day 90.

**Prior**: Strong. Liberal-democratic cultures have baseline skepticism of concentrated power; the novel's depiction of frictionless acceptance is implausible.

### H3 — Chinese Domestic Endorsement
A plurality of Chinese domestic publics will endorse the Proposal, conditional on Chinese participation in the Wallfacer nominations.

**Measurement**: Model Weibo + WeChat Moments equivalent discourse. Compute endorsement with and without the conditional.

**Prior**: Moderate. Chinese political culture is more accepting of concentrated strategic power; Weibo moderation will suppress the most oppositional content; but educated middle-class skepticism is real.

### H4 — ETO Contagion Ceiling
ETO-adjacent content will achieve a peak global share between 3 and 7 percent, then plateau or decline as platform moderation and institutional voices consolidate.

**Measurement**: Track #ETO, #Redemption, #Adventism, #Survive hashtags and direct text classification over time.

**Prior**: Moderate. This is the most uncertain prediction. Platform moderation regimes vary widely. Some fraction of ETO content is satire, making classification hard.

### H5 — Liu Cixin's Silence Amplifies Discourse
Liu Cixin's continued silence throughout the first 50 days drives greater interpretive diversity than a single clear statement would. If Liu makes a statement (Day 14 default injection), discourse narrows along his framing for approximately 7 to 10 days.

**Measurement**: Compare discourse entropy before and after Day 14 Liu statement.

**Prior**: Weak. Cultural authority dynamics are hard to model.

### H6 — Platform Moderation Asymmetry
Platforms with lighter moderation (X, Telegram) will show more ETO content saturation but also more active counter-discourse, yielding comparable or greater discourse diversity than heavily-moderated platforms (TikTok, Weibo, Meta).

**Measurement**: Shannon entropy of discourse topics per platform at days 30, 60, 90.

**Prior**: Moderate. Meta's history suggests heavy moderation compresses discourse but does not necessarily reduce polarization.

### H7 — The European Compromise Becomes Focal
A compromise proposal involving term limits and split transparent-discretionary budgets will emerge as the dominant middle position by day 60 and command between 25 and 40 percent of discourse support.

**Measurement**: Track support for the European Compromise-equivalent position.

**Prior**: Moderate. Middle positions consolidate when bipolar positions produce deadlock.

### H8 — Elite Elite Divergence
Tech elites (Silicon Valley) and political elites (Washington and Beijing) will diverge significantly in their positioning, with tech elites oscillating between Escapism and Wallfacer-skeptic libertarianism, and political elites converging on some form of institutional modification of the Proposal.

**Measurement**: Separately track positions of the top 30 tech elites vs top 30 political elites.

**Prior**: Strong. The divergence is observable in early discourse already.

### H9 — Youth Community Fragmentation
Gen Z discourse (16-27 year olds globally) will fragment along a climate-anxiety axis that is orthogonal to the pro/anti-Wallfacer axis, rather than mirroring elite political divisions.

**Measurement**: TikTok and Instagram sentiment analysis by self-reported age band.

**Prior**: Moderate. Western Gen Z already correlates "climate doom" with "political doom." Chinese and Indian Gen Z are less uniformly doomed.

### H10 — Referendum Divergence from Parliamentary Vote
Where a country holds both a referendum and a parliamentary ratification vote, the two will diverge significantly in at least four of the G20 nations.

**Measurement**: Compare simulated referendum support and parliamentary vote probabilities country-by-country.

**Prior**: Strong. Public moods diverge from elite votes on long-horizon issues (see Brexit, Colombia FARC referendum).

---

## Part 2: Metrics to Report

### Macro Metrics

- **Faction Count Timeline**: Unique factions above 2% support, per week.
- **Polarization Index**: Measure of bimodal distribution (0 = uniform, 1 = fully bipolar).
- **Entropy per Platform**: Shannon entropy of topic distribution.
- **Cross-Platform Divergence**: Kullback-Leibler divergence between X and Weibo.
- **Cross-Cultural Divergence**: KL divergence between US, China, India, Europe.
- **Tipping Point Detection**: Moments where faction shares change by more than 5% in 72 hours.
- **UN Security Council Vote Probability**: Estimated distribution over (pass-as-drafted / pass-modified / fail / postpone).
- **National Ratification Probability**: Per G20 country, probability of ratification in first year.

### Agent-Level Metrics

- **Influence Score**: Per agent, measured as downstream cascade count times average cascade size.
- **Consistency Score**: Per agent, measured as 1 minus the variance of their position over time.
- **Persuasion Score**: Per agent, measured as instances of other agents changing position after interaction.

### Content-Level Metrics

- **Virality Kernel**: Top 20 most-propagated posts by engagement times reach.
- **Deepfake Detection Lag**: For each injected deepfake, time from release to platform label.
- **Coordinated Inauthentic Behavior**: Detection of cluster-similar post patterns.

---

## Part 3: Comparison with Liu Cixin's Novel "The Dark Forest"

The novel is set in a world where the Wallfacer Project is adopted with relatively little public resistance. Four Wallfacers are named: Frederick Tyler (former US Secretary of Defense), Manuel Rey Diaz (Venezuelan President), Bill Hines (British neuroscientist), and Luo Ji (Chinese astronomer, initially reluctant). Three of the four fail at their plans; Luo Ji's plan succeeds because he discovers the Dark Forest theory and uses it as a deterrent.

### Element 1 — Public Reception of the Proposal

**Novel**: Frictionless acceptance. Public debate is brief. Political resistance is minimal.

**Simulation hypothesis**: Substantial resistance, particularly in Western democracies. The novel is unrealistic about the speed and ease of democratic consent to civilizational-scale discretionary authority.

**Comparison protocol**: Compare simulation-predicted opposition share at day 90 against the novel's effective zero opposition. Report the gap and its significance.

### Element 2 — Nominee Diversity

**Novel**: All four Wallfacers are men. One is a former American cabinet member, one a Latin American president, one a British scientist, one a Chinese scientist. No women, no religious leaders, no civil society figures.

**Simulation hypothesis**: In the actual 2026 political environment, pressure for gender diversity, religious representation, and civil society inclusion would fundamentally reshape the candidate pool.

**Comparison protocol**: Predict the simulated nominee demographic distribution. Report the gap between novel and simulation.

### Element 3 — Strategic Opacity Feasibility

**Novel**: The Wallfacers operate with effective strategic opacity for decades. Public discourse does not undermine their missions.

**Simulation hypothesis**: With 2026-era social media, leaks, deepfakes, and surveillance capabilities, the strategic opacity of any public individual with a known mandate would collapse within years, not decades.

**Comparison protocol**: Within the 90-day window, simulate whether rumored nominees can preserve any operational opacity. Assess breach probability.

### Element 4 — Wallbreaker Dynamics

**Novel**: Wallbreakers are formal organizational adversaries, selected from the ETO. They achieve incomplete but destabilizing deductions.

**Simulation hypothesis**: In the real environment, Wallbreaking would be performed by (a) investigative journalism, (b) open-source intelligence communities, (c) foreign intelligence services, (d) crowd-sourced analysis on Kaggle-like platforms, and (e) AI-assisted reasoning agents. Each source has different incentives, and collectively they would be far more effective than novel-depicted Wallbreakers.

**Comparison protocol**: Identify simulated actors that play Wallbreaker roles. Classify their institutional type. Compare to the novel's ETO-centric model.

### Element 5 — Emergent Factions

**Novel**: Factions in the first century are schematic: Escapists, Defeatists, Triumphalists. Internet-age faction proliferation is not depicted.

**Simulation hypothesis**: 2026 will show much finer faction structure with cross-cutting axes (nationalist vs cosmopolitan, spiritualist vs materialist, economic-left vs economic-right, pro-tech vs anti-tech).

**Comparison protocol**: Map simulated factions onto the novel's three-faction schema. Report compression ratio and information loss.

### Element 6 — Time Scaling

**Novel**: Events unfold over decades with long gaps of narrative silence.

**Simulation hypothesis**: In 2026, discourse cycles compress. A debate that takes the novel's characters five years takes the simulation's publics five weeks.

**Comparison protocol**: Compare temporal structure of the simulation against the novel's Part One (Crisis Era to early Wallfacer operations).

### Element 7 — The Role of Fiction in Reality

**Novel**: Science fiction and philosophy are peripheral to policy. The Wallfacer Project is conceived ex nihilo.

**Simulation hypothesis**: The very existence of Liu Cixin's novel and its mass-culture saturation will shape the policy debate. "We are not living in a Liu Cixin novel" and "We must act as if this is a Liu Cixin novel" become rival framings.

**Comparison protocol**: Track mentions and propagation of Liu Cixin's name, concepts, and specific terminology in simulated discourse. Assess influence.

---

## Part 4: The Novel-vs-Reality Report Structure

After the simulation, produce a structured report titled "Where Liu Cixin Was Right, Where Reality Differs." The report structure:

1. Executive summary (500 words).
2. Seven sections, one per element above, each with:
   a. Novel's depiction (concise).
   b. Simulation's prediction (with quantitative backing).
   c. Explanation of divergence.
   d. Strategic implication for real-world PDC-like policy design.
3. Appendix: Data tables, agent distribution maps, representative post samples.
4. Closing assessment: Liu Cixin's novel as a thought experiment vs. predictive model.

This report is the primary shareable artifact for publication on Bilibili, Substack, or as a presentation to the MiroFish team at Shanda Group.

---

## Part 5: Failure Modes to Watch

The simulation may fail or produce misleading results. Watch for:

- **Agent collapse to majority voice**: All agents drift to the same position regardless of initial diversity. Indicates the LLM is averaging instead of role-playing.
- **Implausible cross-cultural uniformity**: Discourse in China, India, and the United States converges to the same factions. Indicates the persona injection is underweighted.
- **Deepfake attribution failures**: Platform moderation labels cannot distinguish synthetic from organic content. Indicates the platform-level modeling is too shallow.
- **Wallfacer-specific vocabulary drift**: Agents use terminology not present in the seed corpus or explainable by it. Indicates contamination from the LLM's training data on Liu Cixin.
- **Temporal inconsistency**: Events out of sequence, anachronistic references. Indicates the injection timing is malformed.

Each failure mode requires a specific remediation. Document and share with the MiroFish team regardless — failure modes are valuable product feedback.
