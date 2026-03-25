# 🤝 Federated Learning Dashboard - User Guide

**Welcome!** This guide explains everything you see on the Federated Dashboard in simple terms.

---

## ✅ Table of Contents
1. [What is Federated Learning?](#what-is-federated-learning)
2. [Dashboard Overview](#dashboard-overview)
3. [Control Panel](#control-panel)
4. [Status Card](#status-card)
5. [Progress Bar](#progress-bar)
6. [Accuracy Chart](#accuracy-chart)
7. [Node Performance Chart](#node-performance-chart)
8. [Training Steps Console](#training-steps-console)
9. [Metrics Summary](#metrics-summary)
10. [Quick Start Guide](#quick-start-guide)
11. [FAQ](#faq)

---

## What is Federated Learning?

### **Simple Explanation**
Imagine 3 hospitals want to build a better disease detection model, but they **can't share patient data** (for privacy reasons).

**Normal way (❌ Privacy Problem):**
```
Hospital A: Sends all patient records → Server → Privacy Breach! 😱
Hospital B: Sends all patient records → Server → Privacy Breach! 😱
Hospital C: Sends all patient records → Server → Privacy Breach! 😱
```

**Federated Learning way (✅ Privacy Protected):**
```
Hospital A: Trains model locally → Sends only "my improvements" → Server
Hospital B: Trains model locally → Sends only "my improvements" → Server
Hospital C: Trains model locally → Sends only "my improvements" → Server

Server: Combines all improvements → Better global model
Result: Everyone benefits, but NO patient data was shared! 🔒
```

### **Key Concept: Weight Deltas**
Instead of sharing raw data, organizations share "weight updates" (the changes to the model):

```
Before training: Model weights = [0.234, -0.567, 0.123]
After training:  Model weights = [0.245, -0.540, 0.135]
What we share:   Weight delta   = [+0.011, +0.027, +0.012]
                 (just the change, not the data!)
```

**Why this matters:** The change tells the server "here's what I learned" without exposing sensitive data.

---

## Dashboard Overview

The dashboard has **7 main sections**:

```
┌────────────────────────────────────────────────────────┐
│  1️⃣  CONTROL PANEL (At the top)                         │
│  Rounds: [5]  Nodes: [3]  Strategy: [FedAvg]           │
│  [Start Training]  [Run Demo]  [Stop]                   │
├────────────────────────────────────────────────────────┤
│  2️⃣  STATUS CARD           │  3️⃣  PROGRESS BAR         │
│  Round: 3/5                 │  ████████░░░░░░░ 60%      │
│  Accuracy: 78.45%           │  Round 3 of 5             │
│  Status: RUNNING            │                           │
├────────────────────────────────────────────────────────┤
│  4️⃣  ACCURACY CHART        │  5️⃣  NODE CHART           │
│  (Line going up)            │  (Bars: Node 0-3)         │
├────────────────────────────────────────────────────────┤
│  6️⃣  TRAINING STEPS (Console)                          │
│  [14:35:22] Step 1: Initializing...                    │
│  [14:35:23] Step 2: Distributing...                    │
│  ... (detailed logs)                                   │
├────────────────────────────────────────────────────────┤
│  7️⃣  METRICS (Bottom)                                   │
│  Avg Loss | Global Loss | Weight Norm | Privacy        │
└────────────────────────────────────────────────────────┘
```

---

## 1️⃣ Control Panel

### **Location:** Top of the dashboard

```
Rounds: [5] ─────────────► How many training iterations
Nodes: [3] ──────────────► How many organizations participate
Aggregation: [FedAvg] ───► How to combine their models
[Start]  [Demo]  [Stop] ─► Control buttons
```

### **Detailed Explanation:**

#### **Rounds Input**
- **What it is:** Number of training cycles
- **Default:** 5
- **Range:** 1-20
- **What happens each round:**
  ```
  Round 1: Server gives model → Nodes train → Nodes send back improvements
  Round 2: Server improves model → Nodes train more → Better improvements
  Round 3-5: Keep improving...
  ```
- **More rounds = Better model (but takes longer)**

#### **Nodes Input**
- **What it is:** Number of organizations collaborating
- **Default:** 3 (e.g., 3 hospitals, banks, cloud companies)
- **Range:** 2-10
- **What each node does:**
  - Gets copy of the model
  - Trains on their own private data (no sharing!)
  - Sends back what they learned
- **More nodes = Better collaboration (learns from more data)**

#### **Aggregation Strategy**
Four ways to combine improvements from nodes:

| Strategy | How it Works | Best For |
|----------|-------------|----------|
| **FedAvg** (Default) | Simple average of all improvements | Most common, balanced |
| **Weighted Avg** | Weight by node's data size | When nodes have different amounts of data |
| **Median** | Take middle value from improvements | Robust against bad nodes |
| **Trimmed Mean** | Remove outliers, then average | Remove suspicious data |

**Simple example with FedAvg:**
```
Node-0 improvement: +10
Node-1 improvement: +12
Node-2 improvement: +8
─────────────────────
Average:           +10  ← This is used to update global model
```

#### **Control Buttons**

| Button | Action | When to Use |
|--------|--------|-----------|
| **Start Training** | Begins full training with custom settings | When you want to train with specific rounds/nodes |
| **Run Demo** | Quick demo (3 rounds, 4 nodes) | To see results quickly without waiting |
| **Stop** | Halts current training | If training is running and you want to stop |

---

## 2️⃣ Status Card

### **Location:** Left side, below control panel

```
┌─────────────────────┐
│ Training Status     │
├─────────────────────┤
│ Status: ⚪ IDLE      │
│                     │
│ Round: 0/5          │
│ Accuracy: 0.00%     │
│ Nodes: 3            │
│ Strategy: FEDAVG    │
└─────────────────────┘
```

### **What Each Field Means:**

#### **Status Badge**
Shows the current state with color:
- 🔘 **IDLE** (Gray) = Not training, ready to start
- 🟡 **RUNNING** (Yellow, pulsing) = Training in progress
- ⏸️ **PAUSED** (Orange) = Training paused
- ✅ **COMPLETED** (Green) = Training finished

#### **Round Counter**
- **Format:** "3/5" means Round 3 out of 5 total
- **What it means:** You're 60% done with training
- **Progress:** Increments by 1 each round

#### **Global Accuracy**
- **What it is:** The main performance metric (0-100%)
- **Starts at:** ~55% (random model)
- **Ends at:** ~96% (well-trained model)
- **What to look for:** **Line should go UP** (accuracy improving)

**Example progression:**
```
Round 1: 55% (just initialized)
Round 2: 65% (starting to learn)
Round 3: 78% (learning patterns)
Round 4: 88% (converging)
Round 5: 96% (final, very good!)
```

#### **Nodes**
- Shows how many organizations are participating
- Should match the number you set in control panel
- More nodes = Model learns from more diverse data

#### **Strategy**
- Shows which aggregation method is being used
- Should match what you selected
- Determines how improvements are combined

---

## 3️⃣ Progress Bar

### **Location:** Right side, below control panel

```
████████░░░░░░░░░░░░  
Round 3 of 5
```

### **What It Means:**
- **Filled portion (████)** = Rounds completed
- **Empty portion (░░░░)** = Rounds remaining
- **Percentage:** (Current Round / Total Rounds) × 100

**Example:**
```
Round 1/5 = 20% filled ████░░░░░░
Round 2/5 = 40% filled ████████░░
Round 3/5 = 60% filled ████████░░
Round 4/5 = 80% filled ████████████░░
Round 5/5 = 100% filled ████████████████
```

### **Why It's Useful:**
- Quick visual check of training progress
- Estimates how much longer training will take
- Shows training is active (moves gradually)

---

## 4️⃣ Accuracy Chart

### **Location:** Bottom left

```
Accuracy %
100 │
 80 │      ╱
 60 │   ╱
 40 │  ╱
  0 │_╱_____
    └─────────── Rounds
    0  1  2  3  4  5
```

### **What It Shows:**
- **Horizontal axis (left-right):** Round number (1, 2, 3, 4, 5)
- **Vertical axis (up-down):** Accuracy percentage (0%-100%)
- **The line:** Overall model performance improving

### **How to Read It:**

**Good sign (✅ What you want to see):**
```
Line curves UPWARD from left to right ↗
Example: 55% → 65% → 78% → 88% → 96%
Meaning: Model is learning and improving!
```

**Bad sign (❌ Worry if you see this):**
```
Line is FLAT →
Example: 55% → 55% → 55% → 55%
Meaning: Model is not improving (check your data)

OR line goes DOWN ↘
Example: 78% → 70% → 65%
Meaning: Model is getting worse (overfitting)
```

### **Real Examples:**

**Fast learner (good):**
```
  100│         ╱
   80│    ╱
   60│ ╱
   40│
    0└─────────
      1 2 3 4 5
Steep curve = Quick improvement
```

**Slow learner (still okay):**
```
  100│           ╱
   80│        ╱
   60│    ╱
   40│
    0└─────────
      1 2 3 4 5
Gentle curve = Steady improvement
```

---

## 5️⃣ Node Performance Chart

### **Location:** Bottom right

```
Accuracy %
100│
 80│  ██
 70│  ██  ██
 60│  ██  ██  ██
    └────────────────
      Node Node Node
       0    1    2
```

### **What It Shows:**
- **Each bar** = One node's accuracy in the last completed round
- **Bar height** = Accuracy percentage
- **Comparison** = How different nodes perform

### **What Each Bar Represents:**

```
Node-0: ████████ 87%
├─ This is Organization A
├─ Trained on their data
└─ Final accuracy: 87%

Node-1: █████████ 92%
├─ This is Organization B
├─ Has cleaner data
└─ Final accuracy: 92%

Node-2: ██████ 78%
├─ This is Organization C
├─ Has noisier data
└─ Final accuracy: 78%
```

### **How to Interpret:**

**All bars similar height (Good ✅):**
```
Node-0: ████████ 87%
Node-1: ████████ 88%
Node-2: ████████ 86%
→ All nodes have similar data quality
→ Fair collaboration
```

**One bar much lower (Bad ⚠️):**
```
Node-0: ██████████ 94%
Node-1: ██████████ 95%
Node-2: ████ 45%  ← Much lower!
→ Node-2 might have bad/corrupt data
→ Need to investigate Node-2's data
```

**One bar much higher (Good, but investigate):**
```
Node-0: ████████ 87%
Node-1: ██████████ 98%  ← Much higher!
Node-2: ████████ 88%
→ Node-1 has very high-quality data
→ Or Node-1 overfitted
```

### **What It Means for the Global Model:**
The server averages all nodes:
```
Global Accuracy = (87% + 92% + 78%) / 3 = 85.67%
```

The global model is better than most individual nodes! 🎉

---

## 6️⃣ Training Steps Console

### **Location:** Lower section, terminal-like black box

```
[14:35:22] Initializing federated training...
[14:35:22] Step 1: Initializing global model...
[14:35:23] Step 2: Distributing model to nodes...
[14:35:24] Step 3: Nodes training locally...
[14:35:25] Step 4: Nodes sending weight deltas to server...
[14:35:26] Step 5: Server aggregating weights...
[14:35:27] Step 6: Evaluating global model...
[14:35:28] Round 1: Accuracy 65%
```

### **This is the DETAILED LOG - shows exactly what's happening!**

### **Understanding Each Step:**

#### **Step 1: "Initializing global model"**
```
What happens:
- Server creates a new model with random starting weights
- Like creating a blank whiteboard

Why it matters:
- Provides baseline to improve from

Visual:
Global Model v1: [Random weights]
```

#### **Step 2: "Distributing model to nodes"**
```
What happens:
- Server sends copy of the model to all 3 nodes
- Each node gets identical starting model

Why it matters:
- Fair starting point for all organizations
- They all improve from same baseline

Visual:
         ┌─────────────┐
         │   Server    │
         └──────┬──────┘
           /    |    \
      [Copy] [Copy] [Copy]
         /      |      \
    [Node0] [Node1] [Node2]
```

#### **Step 3: "Nodes training locally"**
```
What happens:
- Each node trains their copy on THEIR OWN DATA
- Node-0: Trains on Hospital A's data
- Node-1: Trains on Hospital B's data
- Node-2: Trains on Hospital C's data
- All training happens in PARALLEL (simultaneously)

Why it matters:
- NO data sharing (privacy protected!)
- All organizations train simultaneously (fast)

What they do:
- Use their data to improve the model
- Reduce their local error
- Model accuracy increases on their data
```

#### **Step 4: "Nodes sending weight deltas to server"** ⭐ **MOST IMPORTANT**

**This is the genius part of federated learning!**

```
What is a "weight delta"?
It's the CHANGE in weights from training:

Before:  Weight1 = 0.234
After:   Weight1 = 0.245
Delta:   +0.011 (the change)

What gets sent:
✅ SENT:     [+0.011, +0.027, +0.012, ...] (weight changes)
❌ NOT SENT: [Raw patient data from Hospital A] (privacy protected!)

Why it's genius:
- The change tells you what was learned
- But not what the data was
- Like saying "I learned something" without saying what
```

**Process at Node level:**
```
Node-0's local training:
├─ Input: Patient data from Hospital A
├─ Training: Uses SGD to minimize error
├─ Result: Weights improve
└─ Output: [+0.011, +0.027, +0.012] weight change

Hospital A's original data:
├─ NEVER sent to server
├─ NEVER seen by other hospitals
└─ Stays private at Hospital A! 🔒
```

#### **Step 5: "Server aggregating weights"**
```
What happens:
- Server receives weight changes from all nodes
- Averages (or uses other strategy) to combine them
- Creates improved global model

Visual:
Node-0 sends: [+0.011, +0.027, +0.012]
Node-1 sends: [+0.009, +0.030, +0.015]
Node-2 sends: [+0.013, +0.025, +0.010]
                     ↓ Average ↓
Aggregated:   [+0.011, +0.027, +0.012]
                     ↓ Apply ↓
New Global Model: IMPROVED!

Why it works:
- Averaging balances all nodes' contributions
- Strong nodes + weak nodes = balanced improvement
- Everyone benefits from everyone's learning
```

#### **Step 6: "Evaluating global model"**
```
What happens:
- Server tests the NEW improved model
- Measures accuracy on validation data
- Records the result

Result:
Round 1 Accuracy: 65%
(Better than initial random 55%!)

Why it matters:
- Proves the training is working
- Shows progress over rounds
```

### **What the Log Tells You:**

**Good training log (✅):**
```
[14:35:22] Initializing federated training...
[14:35:22] Step 1: Initializing global model...
[14:35:23] Step 2: Distributing model to nodes...
[14:35:24] Step 3: Nodes training locally...    ← Takes longer
[14:35:25] Step 4: Nodes sending weight deltas... ← Quick
[14:35:26] Step 5: Server aggregating weights...  ← Quick
[14:35:27] Step 6: Evaluating global model...
[14:35:28] Round 1: Accuracy 65% ✓
Every step happens in order, accuracy improves
```

**Problem training log (❌):**
```
[14:35:22] Initializing...
[14:35:23] Step 1: ERROR! Model initialization failed!
Training stops here
→ Something went wrong (bad data? missing dependencies?)
```

---

## 7️⃣ Metrics Summary

### **Location:** Bottom (if expanded)

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Avg Local    │ Global Loss  │Weight Update │  Privacy     │
│ Loss: 0.342  │ Loss: 0.210  │ Norm: 0.023  │ Budget: 0.86 │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### **What Each Metric Means:**

#### **1. Avg Local Loss**
```
What it is: Average error across all nodes' models
How to read:
- 0.0  = Perfect (no error)
- 0.5  = Medium (50% error)
- 1.0+ = Terrible (more error)

Good value: Trending downward (decreasing)
Example progression:
Round 1: 0.45
Round 2: 0.38
Round 3: 0.32
Round 4: 0.27
Round 5: 0.22
✓ Going down = Models improving locally
```

#### **2. Global Loss**
```
What it is: Error of the combined/aggregated model
How to read:
- Lower is better (same as local loss)
- Usually lower than avg local loss (aggregation helps!)

Example:
Avg Local Loss: 0.34 (average of 3 nodes)
Global Loss:   0.21 ← Better! Shows aggregation benefits
→ Combined model is better than individual nodes
```

#### **3. Weight Update Norm**
```
What it is: How much the weights changed in this round
How to read:
- Small values (0.01-0.05) = Stable, controlled updates
- Large values (0.5+) = Big changes, might be unstable

Good progression:
Round 1: 0.042 (large updates, learning fast)
Round 2: 0.028 (smaller updates, converging)
Round 3: 0.015 (very small, nearly converged)
Round 4: 0.008 (tiny, model stabilized)
→ Updates getting smaller = Model converging to solution
```

#### **4. Privacy Budget**
```
What it is: How much privacy has been "used" (differential privacy)
How to read:
- 1.0 = Full privacy (none used yet)
- 0.0 = No privacy left (all used up)
- Mid values (0.5) = Some privacy spent

Why it matters:
- Differential privacy adds noise to protect individuality
- Using it up means model is less private
- Balance between privacy and accuracy

Example:
Round 1: Privacy Budget: 0.90 (90% remaining)
Round 2: Privacy Budget: 0.85 (85% remaining)
Round 3: Privacy Budget: 0.79 (79% remaining)
→ Each round costs some privacy
→ More rounds = less privacy
```

---

## Quick Start Guide

### **Your First Training (Step by Step)**

**Step 1: Configure**
```
In Control Panel:
- Rounds: 5 (default is fine)
- Nodes: 3 (default is fine)
- Aggregation: FedAvg (default is fine)
```

**Step 2: Start**
```
Click "Start Training" button
```

**Step 3: Watch**
```
- Status badge changes to RUNNING (yellow)
- Progress bar starts filling
- Console shows steps 1-6
- Accuracy chart appears with first data point
```

**Step 4: Monitor**
```
Watch the accuracy chart:
- Should curve upward ↗
- Watch status round counter (0→1→2→3→4→5)
- Check console for any errors
```

**Step 5: Finish**
```
When complete:
- Status badge shows COMPLETED (green)
- Progress bar is full (100%)
- Accuracy chart shows final value (~96%)
- Final accuracy displayed in status card
```

**Total time:** ~30 seconds for 5 rounds

### **Quick Demo (Even Faster)**

```
Click "Run Demo" button
↓
Automatically runs 3 rounds with 4 nodes
↓
Finishes in ~10 seconds
↓
Shows example of how federated learning works
```

---

## FAQ

### **Q1: Why does accuracy start at 55% and not 0%?**
**A:** The model is randomly initialized. 55% is actually better than random guessing because the random weights have some structure. It's not 50% because the random initialization isn't completely random—it has some bias.

### **Q2: Why does accuracy plateau (stop improving) at 96%?**
**A:** Because the model has learned the patterns as well as it can with the available data. Further training won't improve much—you'd need more/better data to do better.

### **Q3: What if accuracy goes DOWN instead of UP?**
**A:** This could mean:
- Data quality is poor
- Too many rounds (overfitting)
- Wrong aggregation strategy
- Node has corrupt data

Try with fewer rounds or check node accuracies individually.

### **Q4: Why do nodes have different accuracies?**
**A:** Because their data is different:
- One hospital might have cleaner records
- Another might have more cases
- Another might have noisier sensors
- This is realistic! Real organizations have different data quality.

### **Q5: Can I train with just 1 node?**
**A:** Technically yes, but it defeats the purpose of "federated" (collaborative). Federated learning works best with multiple nodes (2+).

### **Q6: How long does each round take?**
**A:** ~5-8 seconds per round:
- Step 3 (local training): ~3-4 seconds
- Steps 1,2,4,5,6: ~1-2 seconds total
- 5 rounds = ~30 seconds total

### **Q7: What does "aggregation" mean in simple terms?**
**A:** How you combine results from multiple organizations:
- **FedAvg:** Average them (fairest)
- **Weighted Avg:** Weight by size (bigger org = more influence)
- **Median:** Take middle value (robust)
- **Trimmed Mean:** Remove outliers (safe)

### **Q8: Is my data really private?**
**A:** Yes! In federated learning:
- ✅ Your raw data stays on your computer
- ✅ Only weight changes are shared
- ✅ Weight changes don't reveal individual data
- ✅ Other organizations can't see your data

It's like a team improving a recipe by only sharing "I added more salt" instead of sharing their kitchen.

### **Q9: Why do we need round numbers? Why not just train once?**
**A:** Because:
- Round 1: Everyone learns basic patterns
- Round 2: Everyone learns refined patterns
- Round 3-5: Everyone improves further
- Multiple rounds = Better model (like studying multiple times vs once)

### **Q10: Can I run multiple trainings simultaneously?**
**A:** No, only one at a time. Stop the current one before starting a new one.

### **Q11: What's the difference between "Start Training" and "Run Demo"?**
**A:**
| Feature | Start Training | Run Demo |
|---------|---|---|
| Rounds | Your choice (1-20) | Fixed 3 |
| Nodes | Your choice (2-10) | Fixed 4 |
| Customization | Full | None |
| Speed | Based on rounds | ~10 seconds |
| Use | When you want control | Quick test |

### **Q12: Where do the console logs go?**
**A:** They appear in the Training Steps console box (black area at bottom). The console shows the last 20 messages—older ones are removed to avoid clutter.

### **Q13: What does "weight delta" really mean?**
**A:** The amount each weight in the model changed after training:
```
Before: w = 0.50
After:  w = 0.63
Delta:  Δw = +0.13 (the change)
```
You send the delta (+0.13) to server, not the original data or final weight.

### **Q14: Can I pause training?**
**A:** Not yet. Click Stop to stop (training can't resume from same point). Start Training again to restart from beginning.

### **Q15: What if a node crashes during training?**
**A:** Federated learning handles this:
- That round might fail, but training continues
- Next round, that node might come back
- The system is resilient (designed for unreliable networks)

---

## Summary Table

| Component | Purpose | Key Metric |
|-----------|---------|-----------|
| **Control Panel** | Configure training | Rounds, Nodes, Strategy |
| **Status Card** | Know current state | Accuracy %, Round number |
| **Progress Bar** | Visual progress | Percent complete |
| **Accuracy Chart** | See improvement | Ascending line graph |
| **Node Chart** | Check individual nodes | All bars similar height |
| **Console** | Detailed logs | No error messages |
| **Metrics** | Technical details | Loss decreasing |

---

## Key Takeaways

1. **Federated Learning** = Privacy-preserving collaborative machine learning
2. **Your dashboard shows** = Real-time training progress + node performance
3. **Key metric** = Accuracy (should go from ~55% → ~96%)
4. **Privacy** = Your data never leaves (only weight changes shared)
5. **Aggregation** = Combining improvements from multiple organizations
6. **Training steps** = 6 steps per round × multiple rounds = better model
7. **Each line/bar/number** = Shows the model is learning

---

## Need Help?

If something looks wrong:
1. **Check console for errors** (may have red error messages)
2. **Check node accuracies** (one might be an outlier)
3. **Try "Run Demo"** (to verify dashboard works)
4. **Check backend is running** (localhost:8000 should be accessible)

---

**That's everything!** You now understand every part of the Federated Dashboard. 🎉

Happy training! 🚀
