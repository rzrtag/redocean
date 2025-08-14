## SaberSim for MLB DFS on DraftKings (2025): A Comprehensive Reference for Large Language Models

This document serves as a detailed reference for Large Language Models (LLMs), providing a comprehensive overview of SaberSim, a sophisticated software platform for Daily Fantasy Sports (DFS). The focus is on its application to Major League Baseball (MLB) contests on DraftKings for the 2025 season.

## Project Architecture: Three Main Components

Our SaberSim integration project consists of three interconnected components that work together to create a complete DFS optimization system:

### 1. Data Collector and Extractor
**Purpose**: Extract and process SaberSim simulation data for both adjustments and analysis.

**Key Extracted Endpoints**:
- **Build Optimizations**: Portfolio optimization settings and lineup generation parameters
- **Contest Simulations**: Detailed simulation results for specific contest types and structures
- **Field Lineups**: Expected opponent lineups and ownership projections

**Process Flow**:
1. Capture SaberSim HAR files containing simulation data
2. Extract atoms (structured data) from HAR files
3. Process atoms into tables and analysis outputs
4. Organize by site (DraftKings/FanDuel) and slate (main_slate, etc.)

### 2. Analysis Engine
**Purpose**: Analyze extracted simulation data for advanced insights into ownership, stacking, and contest dynamics.

**Key Analysis Capabilities**:
- **Contest Simulation Analysis**: SaberSim simulates our entered contests (grouped by buckets: low stakes, mid entry, flagship, etc.)
- **Ownership Insights**: Extract projected ownership percentages and identify leverage opportunities
- **Stack Ownership Analysis**: Critical for both FanDuel and DraftKings DFS - analyze which team stacks are projected for high/low ownership
- **Portfolio Optimization**: Analyze lineup sets as a whole for optimal contest entry strategies

**Strategic Value**:
- Identify contrarian plays and ownership leverage
- Optimize stack construction based on projected ownership
- Understand contest-specific dynamics and payout structures
- Inform lineup selection and portfolio construction decisions

### 3. Adjustments Engine (win_calc)
**Purpose**: Apply rolling window adjustments to SaberSim projections and re-optimize lineups.

**Adjustment Process**:
1. **Load SaberSim Projections**: Import simulation-based projections (likely ~50th percentile)
2. **Apply Rolling Adjustments**: Blend with recent performance signals using event-based windows (50/100/250 events)
3. **Re-upload to SaberSim**: Feed adjusted projections back into SaberSim for re-simulation
4. **Re-optimize**: Generate new lineups and portfolios optimized for our contests
5. **Analyze Portfolio**: Evaluate lineup set as a whole for optimal contest performance

**Key Features**:
- **Event-based rolling windows**: 50/100/250 batted ball events with recency weighting
- **Platform-specific adjustments**: DraftKings (power-focused) vs FanDuel (stack correlation)
- **Quality metrics integration**: xwOBA, hard hit rates, barrel rates, contact quality trends
- **CSV export**: Platform-specific upload files for contest entry

**Workflow Integration**:
```
SaberSim Original → Extract Data → Apply Adjustments → Re-upload to SaberSim → Re-optimize → Analyze Portfolio
```

### Integration Points

**Data Flow**:
- **Extraction** → **Analysis** → **Adjustments** → **Re-optimization** → **Portfolio Analysis**

**Key Benefits**:
- **Complete System**: From data extraction to final portfolio optimization
- **Market Inefficiency Exploitation**: Identify opportunities others miss through advanced analysis
- **Risk Management**: Portfolio-level analysis ensures optimal contest entry strategies
- **Iterative Improvement**: Continuous refinement through backtesting and parameter optimization

This three-component architecture enables us to not only extract and analyze SaberSim data but also enhance it with our own research and re-optimize for maximum contest performance.

---

### 1. SaberSim for MLB DFS on DraftKings (2025): An Overview

SaberSim is a sophisticated software platform designed for Daily Fantasy Sports (DFS) players. Its application extends across various sports, with a significant focus on Major League Baseball (MLB) contests, particularly on platforms like DraftKings. This document provides a detailed exposition of SaberSim's functionalities, methodologies, and strategic applications, specifically tailored for the 2025 MLB DFS season, to serve as an optimal reference for Large Language Models (LLMs).

#### 1.1. Defining SaberSim: More Than an Optimizer – A Complete DFS System

SaberSim positions itself as a "**complete DFS system**" rather than merely a lineup optimizer. This distinction is fundamental to understanding its scope and capabilities. The platform integrates a suite of tools and resources designed to support DFS players throughout the entire contest lifecycle. These components include proprietary **player projections**, a **lineup optimizer**, advanced **contest simulation tools**, **late swap** functionalities, an **entry editor** for managing contest submissions, real-time **alerts** for news and updates, and access to coaching and educational materials.

The "complete system" paradigm suggests that the various components of SaberSim are intended to function synergistically. For instance, the player projections and lineups generated by the optimizer are subsequently evaluated and refined through the contest simulation feature. Late swap decisions, which are critical in MLB DFS due to staggered game starts and evolving information, are informed by continuously updated simulations. Furthermore, post-contest analysis tools like Contest Flashback leverage historical simulation data and actual results to help users refine their strategies. This interconnectedness implies that users who engage with the full spectrum of SaberSim's tools are more likely to realize the platform's potential strategic advantages compared to those who might use it solely as a standalone lineup generation tool. The architecture encourages an integrated workflow, where insights from one stage of the DFS process inform actions in subsequent stages.

#### 1.2. Core Philosophy: Simulation-Driven Strategy for MLB

The foundational philosophy of SaberSim revolves around a **simulation-driven approach** to DFS strategy. At its core is a proprietary algorithm that simulates every game on a given slate thousands of times, on a play-by-play basis. These simulations are described not as traditional, static projections but as "**complete game scripts**". This methodology is particularly pertinent for MLB, a sport characterized by high variance, significant event-dependent correlations (such as the impact of runners on base for subsequent batters), and a wide range of potential individual and team performances.

The emphasis on "game scripts" indicates that SaberSim endeavors to model the narrative and sequential flow of events within a baseball game. This includes capturing the dependencies between plays, rather than just forecasting isolated player statistical outcomes. A play-by-play simulation inherently accounts for how one event (e.g., a batter reaching base) directly influences the context and probabilities of subsequent events (e.g., an RBI opportunity for the next batter, or a stolen base attempt). This approach represents a departure from models that might project player statistics independently and then attempt to superimpose correlations. The implication is a more organic and potentially more accurate modeling of how game dynamics unfold and how fantasy points are ultimately accrued.

#### 1.3. Key Differentiator: Play-by-Play Game Simulations vs. Static Projections

A primary distinction between SaberSim and many traditional DFS optimization tools lies in its core projection methodology. While traditional optimizers frequently rely on static, single-point average projections for players, SaberSim's optimizer is directly fed by the outputs of its thousands of play-by-play game simulations. This allows the system to account for and leverage the "**full range of outcomes**" and inherent upside that simple averages tend to obscure.

This distinction is critical for understanding why SaberSim's outputs, such as recommended player exposures or specific lineup constructions, may differ significantly from those produced by optimizers reliant on mean projections. Because SaberSim's optimization engine processes the distribution of potential outcomes derived from its simulations, rather than a singular average figure, it can make decisions that prioritize upside or consider low-probability, high-impact scenarios. Such considerations are vital for success in large-field Guaranteed Prize Pool (GPP) tournaments, where uniquely high scores are typically required to win. For MLB hitters, for example, the average fantasy point projection is often not representative of their most common single-game outcome (which can be zero), nor does it fully capture their considerable upside potential. Traditional optimizers using only average projections might underweight players with massive ceiling performances but inconsistent floors. SaberSim, by analyzing the "full range of outcomes", can identify that a player who scores zero points frequently but also has a non-trivial chance of a very high score (e.g., a 35-point game) might be a superior GPP play compared to a player who consistently scores a moderate number of points, especially if the high-upside player is projected for lower ownership. This direct link between the simulation methodology and GPP-centric lineup construction is a core differentiating factor.

#### 1.4. Target Audience (of SaberSim): DFS Players Seeking a Competitive Edge

SaberSim is marketed towards "**serious players**" and aims to provide users with the tools and insights needed to "**dominate the DFS lobby**". The platform's features, such as Contest Sims, Custom Data Integration, and detailed Return on Investment (ROI) metrics, are indicative of a tool designed for users who are willing to engage with a more sophisticated system to gain a competitive advantage, rather than casual players seeking quick, simple lineup picks.

The focus on "serious players" and "winning more" implies that the platform's functionalities, while potentially involving a learning curve, are developed with profitability and advanced strategic thinking as primary objectives. This suggests that SaberSim is intended to be a professional-grade instrument. The inclusion of features like "Contest Sims" and "Custom Data Integration" is not typical of basic optimization tools and signals an appeal to an analytical user base looking to identify and exploit market inefficiencies in DFS contests. The availability of "**expert coaching**" further supports this positioning, as dedicated players often seek to refine their processes and strategies through expert guidance and community interaction.

#### 1.5. Relevance for LLM: Documenting a sophisticated tool in a data-rich, strategic domain.

The purpose of this document is to provide a comprehensive and structured understanding of SaberSim for a Large Language Model. SaberSim represents a sophisticated analytical tool operating within the domain of Daily Fantasy Sports, which is inherently probabilistic, data-intensive, and demands complex strategic decision-making. By detailing SaberSim's architecture, simulation engine, features, metrics, and strategic applications, particularly for MLB DFS on DraftKings for the 2025 season, this document aims to equip an LLM with the necessary knowledge to accurately understand, summarize, and respond to queries about this system. The complexity of SaberSim, combined with the nuances of MLB DFS, makes it a valuable subject for detailed documentation targeted at advanced AI comprehension.

---

### 2. The SaberSim Simulation Engine: The Heart of MLB Projections

The SaberSim simulation engine is the central technology underpinning the platform's projections and lineup generation capabilities. Its design is predicated on modeling the inherent complexity and variance of MLB games to provide outputs that reflect a wide spectrum of potential realities.

#### 2.1. Methodology: Thousands of Granular Play-by-Play MLB Game Simulations

SaberSim's methodology involves simulating "**every game thousands of times, play-by-play**". Some sources specify that a slate might be simulated "**5,000 times giving us the best GPP lineup for each of those simulations**". The "**play-by-play**" characteristic is crucial, signifying that the engine does not merely predict aggregate final scores or player stat lines. Instead, it models the sequential progression of events within each simulated game. This level of granularity is what enables the system to capture realistic correlations between player performances and the diverse distributions of possible outcomes.

The substantial volume of simulations (thousands for each game) is a deliberate design choice aimed at adequately sampling the vast possibility space inherent in an MLB game. This extensive sampling is intended to ensure that the "**full range of outcomes**" is represented in the data fed to the optimizer, including not just the most probable scenarios but also less frequent yet high-impact events. Given that MLB games consist of numerous discrete events (pitches, at-bats, defensive plays), each with multiple potential results, a single simulation run can be conceptualized as one specific path through these branching possibilities. To achieve a statistically stable understanding of probabilities, correlations, and the true range of player and team scores, a large number of iterations is essential. This commitment to extensive simulation directly addresses the high-variance nature of MLB DFS, where outlier performances often determine GPP success.

#### 2.2. Comprehensive Modeling: Incorporating Matchups, Weather, Park Factors, Player Performance Distributions, Injuries, Play-Calling, Rotations, and More

The SaberSim simulation engine incorporates a wide array of influential factors into its models. These include, but are not limited to, "**match-ups, weather, play-calling (though less directly applicable to MLB strategy compared to sports like NFL, it is listed as a general simulation input), rotations, injuries, and more**". For MLB, specific considerations such as batter-versus-pitcher matchups, team-versus-bullpen strengths, prevailing weather conditions (e.g., wind speed and direction, temperature, which can affect ball flight and player comfort), park factors (e.g., stadium dimensions, altitude, historical scoring environments like Coors Field), and player-specific performance distributions (e.g., a power hitter's propensity for home runs versus singles, or a pitcher's strikeout and walk tendencies) are all critical variables that significantly influence fantasy point scoring.

The inclusion of these diverse factors directly shapes the "**game scripts**" generated by the simulations. For instance, a simulated game featuring a team with a strong offense playing in a hitter-friendly venue like Coors Field, under favorable weather conditions (e.g., warm air, wind blowing out), will inherently be more likely to produce higher offensive outputs compared to a simulation of the same teams playing in a pitcher-friendly park under adverse weather. Each of the listed factors is a known driver of baseball outcomes. By integrating them into the simulation engine, SaberSim attempts to model the complex interactions between these variables. A favorable matchup for a hitter (e.g., a left-handed batter facing a right-handed pitcher known to struggle against lefties) in a conducive park environment will, within the simulation, translate to a higher probability of positive offensive events for that hitter and, consequently, their teammates. This detailed, multi-variable modeling is what imbues the "game scripts" with their richness and variability. The explicit mention of accounting for "**player performance distributions**" is particularly important, as it suggests the simulations do not rely on a single, static point projection for each player but instead model their inherent range of potential performances based on historical data and contextual factors.

#### 2.3. Outputs: Dynamic "Game Scripts," Full Range of Outcomes, and Player Percentiles

The primary outputs of the SaberSim simulation engine are "**complete game scripts**". These detailed narratives of simulated games allow users to understand and leverage the "**full range of outcomes**" for players and teams, rather than relying on singular average projections. **Player percentiles** (e.g., 5th, 25th, 75th, 95th percentile scores) are direct statistical derivatives of these outcome distributions and are crucial for assessing a player's potential floor and ceiling.

This output structure fundamentally alters the approach to player evaluation and lineup construction. Users are guided to think in terms of probabilities and ranges of potential scores rather than deterministic point estimates. This is especially critical in GPP tournaments, where accurately identifying and capturing players' ceiling performances is paramount for achieving high ranks. For MLB hitters, who often exhibit a boom-or-bust scoring pattern (with zero points being a common outcome, alongside significant upside), percentiles provide a statistical means to quantify this variability. For example, a player's **95th percentile** score can represent their reasonable upside or ceiling, while a 5th or 25th percentile score can indicate their floor. The "game scripts" themselves offer a contextual narrative for how these percentile scores might be achieved, illustrating the sequence of events (e.g., a multi-home run game by a batter during a team rally) that could lead to a ceiling performance. If a user only considers an average projection, they miss vital information about the associated risk and reward. The fact that MLB hitters often score zero but also possess substantial upside, with 95th percentile outcomes sometimes being similar even for players with disparate average projections, underscores this point. A player with a lower average projection but a comparable or even superior 95th percentile score might represent a more strategically sound GPP play, particularly if they are also projected for lower ownership.

#### 2.4. Capturing Correlations: How Simulations Inherently Model and Leverage Player and Team Synergies (e.g., Stacking)

A significant strength of the play-by-play simulation methodology is its inherent ability to capture and quantify **correlations** between players, particularly those on the same team. In MLB DFS, **stacking** (rostering multiple hitters from the same team) is a widely recognized optimal strategy due to the positive correlation between their offensive performances. For instance, when one hitter reaches base, it creates scoring opportunities (e.g., RBIs, runs scored) for subsequent hitters in the lineup. SaberSim's sequential simulation of game events naturally accounts for these dependencies. The platform also models the negative correlation between pitchers and the hitters on the opposing team, as well as the generally weaker positive correlation between a pitcher and their own team's offensive output.

The inherent modeling of these correlations means that SaberSim can identify optimal stack sizes (e.g., 4-3, 5-2, or 5-3 constructions) and specific player combinations without requiring users to manually define numerous stacking rules. These recommendations emerge organically from the simulations, based on how frequently certain combinations of players appear in high-scoring lineups across the thousands of simulated game scripts. As an example of this emergent correlation, one source explains: "Ronald Acuna may have a .12 correlation to Matt Olsen, but Austin Riley also has a .11 correlation to both hitters... The correlation of your lineup as a whole increases more and more... the more hitters from the same team you add". A play-by-play simulation naturally reflects this dynamic. If Acuna singles, Olsen has an opportunity to drive him in. If both score, Riley may then bat with runners on base. This chain reaction of offensive events is captured within individual "game scripts." Because the optimizer processes thousands of these scripts, it effectively "learns" which combinations of players (i.e., stacks) frequently contribute to high-scoring team and lineup outcomes. This data-driven approach to handling correlations is more robust and nuanced than simply applying generic rules like "always stack players X, Y, and Z if they are in the lineup together."

#### 2.5. Real-Time Adaptability: Automatic Simulation Updates with Breaking News and Live Game Data

SaberSim's simulation engine is designed for dynamic adaptability. The platform states that "**new sims automatically run whenever news breaks**". Furthermore, "**as a slate plays out, we pull in actual ownerships and points and continuously run new sims**". This capability for real-time updates is crucial for features such as **Late Swap** and ensures that SaberSim's projections and lineup recommendations remain as relevant and accurate as possible in response to new information (e.g., confirmed starting lineups, player scratches, significant weather changes) or as live games unfold.

This ability to re-simulate based on real-time data provides a significant strategic advantage, particularly in sports like MLB where late lineup announcements are common and game conditions can evolve. Users equipped with SaberSim can potentially react more swiftly and optimally to changing circumstances than those relying solely on pre-lock, static data. When critical news emerges, such as a key player being scratched from a lineup, the implications extend beyond that single player. Their absence can alter their teammates' roles and opportunities, as well as the strategic approach of the opposing team. SaberSim's automatic re-simulation process means the system does not just remove the affected player from consideration; it re-evaluates the entire slate based on this new informational landscape. Similarly, the "live updates" functionality during a slate means that if an early game in a multi-game slate has an unexpected outcome (e.g., a highly-owned pitcher performs poorly, or a low-owned stack erupts), the contest simulations for later-starting games can adjust. This can potentially identify new leverage opportunities or modify the perceived value of remaining players and stacks. This continuous feedback loop between real-world events and the simulation engine is a powerful characteristic of the SaberSim system.

---

### 3. Core SaberSim Features & Functionalities for MLB DFS (DraftKings 2025 Focus)

SaberSim offers a range of integrated tools designed to assist DFS players in research, lineup construction, contest entry, and post-contest analysis. The following table provides a high-level overview of these core features, with a focus on their application to MLB DFS on DraftKings for the 2025 season.

#### Table 1: SaberSim Core Features Overview

| Feature Name | Brief Description | Primary Benefit for MLB DFS | Key 2025 Updates (if applicable) |
| :--- | :--- | :--- | :--- |
| **Lineup Optimizer** | Generates large pools of high-upside lineups based on thousands of play-by-play game simulations. | Quickly creates diverse, GPP-viable lineups reflecting full range of outcomes and inherent correlations (stacking). | - |
| **Contest Sims** | Simulates user's lineups against expected opponent lineups in specific contest structures to estimate ROI. | Moves beyond raw projections to identify truly profitable lineups by factoring in ownership leverage and payout structures. | Auto-Configured Contest Sim Settings |
| **Late Swap** | Tools and processes for adjusting lineups after initial lock when new information (e.g., late scratches) emerges. | Enables optimal reaction to breaking news, avoiding zeros and re-leveraging based on updated simulations and live data. | - |
| **Min Uniques** | Post-build setting to control the minimum number of unique players between any two lineups in a portfolio. | Manages risk and variance in MME by ensuring lineup diversification without unduly sacrificing individual lineup quality. | - |
| **Custom Data Integration** | Allows users to upload their own projections, ownership data, or other custom datasets. | Enhances simulations and lineup rules with user-specific research (e.g., BvP, advanced weather, umpire data). | - |
| **Lineup Rules** | Powerful rule builder to enforce specific lineup construction preferences or strategic constraints. | Provides precision control over lineup structure, allowing users to implement high-conviction plays or fades. | - |
| **Entry Editor & Auto-Fill** | Streamlines the process of managing contest entries and assigning lineups to specific contests. | Facilitates error-free and efficient entry of multiple lineups, especially for MME players. | Powerful Auto-Fill feature |
| **Contest Flashback** | Post-contest analysis tool using simulations to review past lineup performance and learn from successful strategies. | Helps users refine future strategies by understanding why certain lineups performed well or poorly in past contests. | - |
| **Automatic Alerts** | Real-time notifications for breaking news, such as player scratches or significant projection changes. | Ensures users are promptly informed of critical updates that may impact their lineups. | - |
| **Auto-Configured Contest Sim Settings** | Automatically configures contest simulation parameters based on the specific contests being played. | Simplifies setup of Contest Sims, improves accuracy of ROI estimates by tailoring sims to contest specifics. | New for 2025 |
| **Powerful Auto-Fill** | Enhanced feature for intelligently assigning lineups from the user's pool to their contest entries. | Improves efficiency and effectiveness of matching optimal lineups to various contest entries based on ranking criteria. | New for 2025 |

---

### 3.1. Lineup Optimizer: Generating and Refining High-Upside Lineup Pools

The SaberSim Lineup Optimizer is designed to rapidly generate large pools of high-upside DFS lineups, typically ranging from 500 to 5,000, based on the platform's extensive game simulations. Users can then filter, diversify, and adjust these lineups according to their specific strategies and risk preferences. A key characteristic of this optimizer is that each lineup within the initial generated pool is considered the "**best possible GPP lineup for a given way that the slate could play out**". This means the optimizer is not merely producing variations around a single average-based optimal lineup; instead, it constructs a portfolio of lineups, each corresponding to a distinct simulated game script or scenario.

This approach of generating a large pool of lineups, where each is optimal for a specific simulation, is a direct outcome of SaberSim's simulation-first philosophy. This pool inherently contains lineups that capture diverse types of upside and a variety of player correlations. If each of the thousands of simulations produces a slightly different "game script" and, consequently, a different set of player scores, then the optimal lineup for each of these scripts will also vary. Some simulated scenarios might favor a particular offensive stack, while others might highlight a contrarian pitcher or a less common lineup construction. By collecting these "**SimOptimals**" (lineups that are optimal for individual simulations), SaberSim creates a rich and varied pool of starting points. This methodology is fundamentally different from traditional optimizers that might generate N lineups by iteratively excluding players from a single optimal lineup derived from static average projections. The SaberSim approach aims to provide a more robust and diverse foundation for lineup selection.

### 3.2. Contest Sims: Optimizing for ROI through Simulated Contest Environments

SaberSim's **Contest Sims** feature elevates the lineup evaluation process by simulating the user's generated lineups within the context of specific DFS contests. This involves running thousands of simulations of the contest itself, taking into account factors such as the expected lineups of opponents (often referred to as "**field lineups**"), projected player ownership percentages, and the specific payout structure of the targeted contest. The primary output of this process is an estimated **Return on Investment (ROI)** for each lineup, allowing users to identify not just high-scoring lineups, but those that are most likely to be profitable.

This feature allows users to move beyond evaluating lineups in isolation and instead assess their potential performance within a competitive environment. This incorporates game theory elements, such as **ownership leverage**. A lineup might project to score highly based on raw player projections, but if it is composed of very popular players (i.e., "chalk"), it may have a lower ROI due to the high probability of splitting prizes with many other similar entries in a GPP. Conversely, a lineup that is slightly less optimal in terms of raw projection but is highly unique or "contrarian" might possess a significantly higher ROI if it has a reasonable chance of winning or placing highly with fewer duplicates. SaberSim's Contest Sims are designed to quantify these dynamics. The explicit focus on profitability against the field, rather than just raw projected score, represents a sophisticated strategic layer that helps users make more informed decisions about which lineups to enter into which contests.

#### 3.2.1. 2025 Update: Auto-Configured Contest Sim Settings

For the 2025 MLB season, SaberSim has introduced "**auto-configured contest sim settings**". This update aims to streamline the process of setting up contest simulations by automatically tailoring the simulation parameters to the specific contests a user is playing.

Manually configuring contest simulation parameters can be a complex task, requiring users to accurately define elements such as contest size, payout structures (e.g., percentage of the prize pool allocated to first place, percentage of entries that cash), and the estimated strength or tendencies of the opponent field. Auto-configuration simplifies this process, potentially reducing the likelihood of user error and decreasing the time spent on setup. This allows users to more easily and accurately benefit from tailored contest simulations. If contest simulations need to accurately reflect the specific contest being entered (e.g., a large-field GPP versus a small single-entry tournament), then the parameters of that simulation must be precise. User reports from beta testing have mentioned inputting contest-specific parameters like "% to first" and "% of winners". The auto-configuration feature likely automates this setup by extracting contest details from an uploaded entry file or by using pre-defined templates for common contest types, thereby making the resulting ROI calculations more relevant and actionable for the user's actual contest entries.

---

### 3.3. Late Swap: Advanced Tools and Processes for Post-Lock Adjustments

SaberSim provides "**dominating swap tools**" that enable users to react to breaking news immediately after contest lock, maintaining a high degree of power and control over their lineups. The **late swap** process is particularly crucial in MLB DFS due to staggered game start times and the frequent occurrence of late lineup announcements or player scratches. SaberSim's approach to late swap integrates its core simulation engine, allowing for more sophisticated adjustments than simply replacing an unavailable player with another similarly priced option. The system re-optimizes lineups based on the newly updated slate dynamics.

The recommended late swap workflow in SaberSim typically involves several steps:

1.  **News Monitoring**: Utilizing SaberSim's notification features (e.g., quick swap icons, desktop alerts) to stay informed about players who are out or not in expected lineups.
2.  **Initial Quick Swap**: Immediately using the "**Quick Swap**" tool to remove any confirmed out players from all lineups to prevent taking a zero score for those positions. For hitters, it's often recommended to first attempt swaps with players from the same team to preserve existing stacks.
3.  **Late Swap Build**: Initiating a "**Late Swap Build**." Users can typically choose to either "clone current settings" from their original build (carrying over exposures and rules) or "use default settings." Using default settings is often advised if significant news has broken, as this allows SaberSim to pivot to potentially different optimal strategies for the remaining games without being constrained by pre-lock assumptions.
4.  **Contest Simulation (if applicable)**: For users with access to contest simulations, running these simulations on the newly generated late swap pool. The contest sims will utilize live data from games already in progress and the actual lineups deployed by opponents to rank potential swaps by their expected ROI for the remainder of the slate.
5.  **Final Selection and Entry**: Selecting the top-ranked late swap lineups based on the contest sim results (or other preferred metrics) and updating entries on the DFS platform.

SaberSim's late swap functionality is designed not merely to avoid zero scores from scratched players but to offer an opportunity to re-leverage lineups based on updated simulations and live contest data. The choice between cloning original settings or using defaults during the late swap build provides strategic flexibility. If substantial news alters the landscape of the slate, default settings allow the optimizer more freedom to identify new optimal constructions. This means SaberSim is not just filling a roster spot; it is attempting to find the most profitable way to adapt to the new information and game conditions.

### 3.4. Min Uniques: Strategic Diversification and Lineup Uniqueness Control

The "**Min Uniques**" feature in SaberSim is a setting that dictates the minimum number of unique players required when comparing any two lineups within a user's selected portfolio. For example, a Min Uniques setting of 3 means that any two lineups chosen for entry will differ by at least three players. This feature is primarily used for managing risk and variance in Mass Multi-Entry (MME) contests by ensuring that a user's set of lineups is sufficiently diversified. For MLB, a general recommendation for building 150 lineups is to use 3 or 4 Min Uniques.

SaberSim's implementation of Min Uniques differs significantly from that of many traditional DFS optimizers. In SaberSim, Min Uniques is applied as a **post-build selection setting**. This means that the user first generates a large pool of lineups (e.g., 500 to 5,000), each of which has already been individually optimized based on a specific game simulation. The Min Uniques setting is then used to select a subset of these high-quality lineups for entry, ensuring the desired level of differentiation. In contrast, traditional optimizers often require Min Uniques to be set as a pre-build constraint. In such systems, the optimizer might build one optimal lineup and then discard subsequent potential lineups until it finds one that meets the uniqueness threshold relative to those already generated. This can lead to a rapid decline in the quality or projected score of later-generated lineups as the optimizer is forced to make increasingly significant compromises to find unique combinations.

The SaberSim approach aims to achieve diversification without unduly sacrificing the quality of individual lineups. Because each lineup in the initial pool is already considered a "best possible GPP lineup for a given sim", applying Min Uniques as a selection filter allows users to choose a diverse subset from these strong options. Users are advised to incrementally increase the Min Uniques value and observe the impact on aggregate lineup metrics.

### 3.5. Portfolio Optimization: Advanced Multi-Contest Strategy

SaberSim's portfolio optimization capabilities represent a sophisticated approach to managing multiple contest entries across different contest types and structures. This feature allows users to optimize their entire lineup portfolio as a cohesive unit rather than treating each contest entry in isolation.

**Key Portfolio Optimization Features**:

**Contest Bucket Grouping**:
- **Low Stakes**: High-volume, low-entry-fee contests (e.g., $0.25-$1 entries)
- **Mid Entry**: Medium-volume contests with moderate entry fees (e.g., $2-$10 entries)
- **Flagship**: High-stakes contests with significant entry fees (e.g., $20+ entries)
- **Single Entry**: Unique contest structures requiring single lineup entries

**Portfolio-Level Analysis**:
- **Cross-Contest Optimization**: Optimize lineup selection across multiple contests simultaneously
- **Risk Distribution**: Balance exposure across different contest types and payout structures
- **Ownership Leverage**: Coordinate contrarian plays across contest buckets for maximum leverage
- **Stack Diversification**: Vary stack constructions across contests to capture different upside scenarios

**Advanced Portfolio Metrics**:
- **Portfolio ROI**: Expected return across all contest entries
- **Risk-Adjusted Performance**: Balance between upside potential and downside risk
- **Contest-Specific Optimization**: Tailor lineup selection to contest payout structures
- **Field Strength Analysis**: Evaluate competition level across different contest types

**Strategic Applications**:
- **MME (Mass Multi-Entry) Strategy**: Optimize large portfolios for maximum expected value
- **Contest Selection**: Identify which contests offer the best risk/reward profiles
- **Lineup Allocation**: Determine optimal lineup distribution across contest types
- **Bankroll Management**: Coordinate entry sizing with portfolio optimization

This portfolio-level approach enables users to think strategically about their entire DFS session rather than optimizing each contest entry independently, leading to more sophisticated and potentially more profitable overall strategies.
