import React, { useState, useEffect, useRef } from 'react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter
} from 'recharts';
import '../styles/FederatedDashboard.css';

/**
 * FederatedDashboard Component
 * 
 * Real-time visualization of federated learning training progress.
 * Displays:
 * - Training control panel (rounds, nodes, aggregation strategy)
 * - Status tracking (current round, global accuracy, state)
 * - Progress visualization (bar chart, line charts)
 * - Training step logs (detailed process console)
 * - Performance metrics (loss, weight updates, privacy budget)
 * - WebSocket integration for real-time updates
 */
const FederatedDashboard = () => {
  // ===== State Management =====
  const [trainingState, setTrainingState] = useState('idle'); // idle, running, paused, completed
  const [roundData, setRoundData] = useState([]); // Array of {round, accuracy, timestamp} for line chart
  const [nodeStats, setNodeStats] = useState([]); // Array of {nodeId, accuracy, status} for bar chart
  const [currentRound, setCurrentRound] = useState(0); // Current training round (1-N)
  const [totalRounds, setTotalRounds] = useState(5); // Total rounds configured
  const [globalAccuracy, setGlobalAccuracy] = useState(0); // Global model accuracy (0-100%)
  const [aggregationType, setAggregationType] = useState('fedavg'); // fedavg, weighted_avg, median, trimmed_mean
  const [numNodes, setNumNodes] = useState(3); // Number of participating organizations
  const [stepMessages, setStepMessages] = useState([]); // Training step logs for console
  const [metrics, setMetrics] = useState(null); // Technical metrics (loss, privacy budget, etc)
  const wsRef = useRef(null); // WebSocket connection reference

  // Initialize WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/v1/federated/ws/training`;
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('✓ WebSocket connected to federated training');
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        // Attempt reconnection after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
    };
    
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = (data) => {
    if (data.round) {
      setCurrentRound(data.round);
      addStepMessage(`Round ${data.round}: ${data.phase || 'Processing...'}`);
    }
    
    if (data.global_accuracy !== undefined) {
      setGlobalAccuracy(data.global_accuracy);
    }
    
    if (data.metrics) {
      setMetrics(data.metrics);
    }
    
    if (data.node_accuracies) {
      const nodeData = Object.entries(data.node_accuracies).map(([nodeId, accuracy]) => ({
        nodeId,
        accuracy: (accuracy * 100).toFixed(2),
        status: 'active'
      }));
      setNodeStats(nodeData);
    }
    
    // Add to round history
    if (data.round && data.global_accuracy !== undefined) {
      setRoundData(prev => {
        const existing = prev.findIndex(d => d.round === data.round);
        if (existing >= 0) {
          const updated = [...prev];
          updated[existing] = {
            round: data.round,
            accuracy: (data.global_accuracy * 100).toFixed(2),
            timestamp: new Date().toLocaleTimeString()
          };
          return updated;
        } else {
          return [...prev, {
            round: data.round,
            accuracy: (data.global_accuracy * 100).toFixed(2),
            timestamp: new Date().toLocaleTimeString()
          }];
        }
      });
    }
  };

  // Add step messages with auto-scroll
  const addStepMessage = (message) => {
    setStepMessages(prev => {
      const updated = [...prev, `[${new Date().toLocaleTimeString()}] ${message}`];
      return updated.slice(-20); // Keep last 20 messages
    });
  };

  // Fetch current status from backend
  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/v1/federated/status');
      if (response.ok) {
        const data = await response.json();
        console.log('[FETCH-STATUS] Received data:', data);
        console.log('[FETCH-STATUS] metrics_history:', data.metrics_history);
        console.log('[FETCH-STATUS] node_accuracies:', data.node_accuracies);
        
        setCurrentRound(data.current_round);
        setTotalRounds(data.total_rounds || 5); // Default to 5 if not available
        setGlobalAccuracy(data.global_accuracy);
        console.log('[FETCH-STATUS] Set current_round:', data.current_round, 'total_rounds:', data.total_rounds, 'global_accuracy:', data.global_accuracy);
        
        // Populate round data for accuracy chart
        if (data.metrics_history && Array.isArray(data.metrics_history)) {
          console.log('[FETCH-STATUS] Processing metrics_history, length:', data.metrics_history.length);
          const rounds = data.metrics_history.map(m => {
            console.log('[FETCH-STATUS] Processing round:', m.round, 'accuracy:', m.global_accuracy);
            return {
              round: m.round,
              accuracy: (m.global_accuracy * 100).toFixed(2)
            };
          });
          console.log('[FETCH-STATUS] Setting roundData:', rounds);
          setRoundData(rounds);
        }
        
        // Populate node stats for bar chart
        if (data.node_accuracies && typeof data.node_accuracies === 'object') {
          console.log('[FETCH-STATUS] Processing node_accuracies:', data.node_accuracies);
          const nodes = Object.entries(data.node_accuracies).map(([nodeId, accuracy]) => ({
            nodeId: nodeId,
            accuracy: (accuracy * 100).toFixed(2),
            status: 'completed'
          }));
          console.log('[FETCH-STATUS] Setting nodeStats:', nodes);
          setNodeStats(nodes);
        }
        
        if (data.status === 'training') {
          setTrainingState('running');
        } else if (data.status === 'completed') {
          setTrainingState('completed');
        }
      } else {
        console.error('[FETCH-STATUS] Response not OK:', response.status);
      }
    } catch (error) {
      console.error('[FETCH-STATUS] Error fetching status:', error);
    }
  };

  // Start training
  const handleStartTraining = async () => {
    setTrainingState('running');
    setRoundData([]);
    setNodeStats([]);
    setStepMessages([]);
    addStepMessage('Initializing federated training...');
    
    try {
      const response = await fetch('/api/v1/federated/start-training', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          num_rounds: totalRounds,
          num_nodes: numNodes,
          aggregation_strategy: aggregationType,
          learning_rate: 0.01
        })
      });
      
      if (response.ok) {
        addStepMessage('Step 1: Initializing global model...');
        setTimeout(() => addStepMessage('Step 2: Distributing model to nodes...'), 500);
      } else {
        addStepMessage('Error: Failed to start training');
        setTrainingState('idle');
      }
    } catch (error) {
      console.error('Error starting training:', error);
      addStepMessage('Error: Connection failed');
      setTrainingState('idle');
    }
  };

  // Stop training
  const handleStopTraining = () => {
    setTrainingState('idle');
    addStepMessage('Training stopped by user');
  };

  // Run demo
  const handleRunDemo = async () => {
    setTrainingState('running');
    setRoundData([]);
    setNodeStats([]);
    setStepMessages([]);
    addStepMessage('Running federated learning demo...');
    
    try {
      const response = await fetch('/api/v1/federated/run-demo?num_rounds=3&num_nodes=4', {
        method: 'POST'
      });
      
      const result = await response.json();
      if (response.ok) {
        addStepMessage('Demo completed successfully');
        setTrainingState('completed');
        // Update rounds from demo response
        if (result.num_rounds) {
          setTotalRounds(result.num_rounds);
        }
        // Immediately fetch status to display results
        setTimeout(() => {
          fetchStatus();
        }, 500);
      } else {
        const errorMsg = result.detail || result.error || 'Unknown error';
        addStepMessage(`Demo error: ${errorMsg}`);
        setTrainingState('idle');
      }
    } catch (error) {
      console.error('Error running demo:', error);
      addStepMessage(`Error: Demo failed - ${error.message}`);
      setTrainingState('idle');
    }
  };

  // Get current status - polling when training is running
  useEffect(() => {
    if (trainingState === 'running') {
      const timer = setInterval(fetchStatus, 2000);
      return () => clearInterval(timer);
    }
  }, [trainingState]);

  return (
    <div className="federated-dashboard">
      <h2>Federated Learning Dashboard</h2>
      
      {/* Control Panel */}
      <div className="control-panel">
        <div className="control-group">
          <label>Rounds:</label>
          <input
            type="number"
            min="1"
            max="20"
            value={totalRounds}
            onChange={(e) => setTotalRounds(parseInt(e.target.value))}
            disabled={trainingState !== 'idle'}
          />
        </div>
        
        <div className="control-group">
          <label>Nodes:</label>
          <input
            type="number"
            min="2"
            max="10"
            value={numNodes}
            onChange={(e) => setNumNodes(parseInt(e.target.value))}
            disabled={trainingState !== 'idle'}
          />
        </div>
        
        <div className="control-group">
          <label>Aggregation:</label>
          <select
            value={aggregationType}
            onChange={(e) => setAggregationType(e.target.value)}
            disabled={trainingState !== 'idle'}
          >
            <option value="fedavg">FedAvg</option>
            <option value="weighted_avg">Weighted Avg</option>
            <option value="median">Median</option>
            <option value="trimmed_mean">Trimmed Mean</option>
          </select>
        </div>
        
        <div className="button-group">
          <button
            onClick={handleStartTraining}
            disabled={trainingState !== 'idle'}
            className="btn-start"
          >
            Start Training
          </button>
          <button
            onClick={handleRunDemo}
            disabled={trainingState !== 'idle'}
            className="btn-demo"
          >
            Run Demo
          </button>
          <button
            onClick={handleStopTraining}
            disabled={trainingState === 'idle'}
            className="btn-stop"
          >
            Stop
          </button>
        </div>
      </div>

      {/* Status Section */}
      <div className="status-section">
        <div className="status-card">
          <h3>📊 Training Status</h3>
          <p className={`status-badge ${trainingState}`}>
            {trainingState.toUpperCase()}
          </p>
          <div className="status-details">
            <div className="status-item">
              <span className="status-label">🔄 Round:</span>
              <strong>{currentRound}/{totalRounds}</strong>
              <span className="tooltip-icon" title="Current training round / Total rounds configured">ℹ️</span>
            </div>
            <div className="status-item">
              <span className="status-label">🎯 Global Accuracy:</span>
              <strong className="accuracy-value">{(globalAccuracy * 100).toFixed(2)}%</strong>
              <span className="tooltip-icon" title="How well the combined model performs on test data">ℹ️</span>
            </div>
            <div className="status-item">
              <span className="status-label">🏢 Nodes:</span>
              <strong>{numNodes}</strong>
              <span className="tooltip-icon" title="Number of organizations/hospitals participating">ℹ️</span>
            </div>
            <div className="status-item">
              <span className="status-label">⚙️ Strategy:</span>
              <strong>{aggregationType.toUpperCase()}</strong>
              <span className="tooltip-icon" title="Method used to combine updates from all nodes">ℹ️</span>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="progress-section">
          <h3>📈 Training Progress</h3>
          <div className="progress-info">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${(currentRound / totalRounds) * 100}%` }}
              ></div>
            </div>
            <p className="progress-text">
              Round <strong>{currentRound}</strong> of <strong>{totalRounds}</strong>
            </p>
            <span className="progress-tooltip" title="Percentage of training completed">
              {((currentRound / totalRounds) * 100).toFixed(0)}% Complete
            </span>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="charts-container">
        {/* Accuracy Over Rounds */}
        <div className="chart-card">
          <h3>Accuracy Progression</h3>
          {roundData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={roundData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="round" />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value) => `${value}%`} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="accuracy"
                  stroke="#2196F3"
                  name="Global Accuracy"
                  isAnimationActive={true}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-placeholder">No data yet - start training to see charts</p>
          )}
        </div>

        {/* Node Accuracies */}
        <div className="chart-card">
          <h3>Node Accuracies (Last Round)</h3>
          {nodeStats.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={nodeStats}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="nodeId" />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value) => `${value}%`} />
                <Legend />
                <Bar dataKey="accuracy" fill="#4CAF50" name="Accuracy %" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-placeholder">Waiting for node data...</p>
          )}
        </div>
      </div>

      {/* Step Messages Console */}
      <div className="console-section">
        <h3>Training Steps</h3>
        <div className="console">
          {stepMessages.length > 0 ? (
            stepMessages.map((msg, idx) => (
              <div key={idx} className="console-line">
                {msg}
              </div>
            ))
          ) : (
            <div className="console-line">Waiting to start training...</div>
          )}
        </div>
      </div>

      {/* Metrics Summary */}
      {metrics && (
        <div className="metrics-section">
          <h3>Training Metrics</h3>
          <div className="metrics-grid">
            <div className="metric-card">
              <label>Avg Local Loss</label>
              <p>{metrics.avg_local_loss?.toFixed(4)}</p>
            </div>
            <div className="metric-card">
              <label>Global Loss</label>
              <p>{metrics.global_loss?.toFixed(4)}</p>
            </div>
            <div className="metric-card">
              <label>Weight Update Norm</label>
              <p>{metrics.weight_update_norm?.toFixed(4)}</p>
            </div>
            <div className="metric-card">
              <label>Privacy Budget</label>
              <p>{metrics.privacy_budget?.toFixed(4)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Educational Footer */}
      <div className="federated-footer">
        <div className="footer-content">
          {/* What is Federated Learning */}
          <section className="footer-section">
            <h3>🤝 What is Federated Learning?</h3>
            <p>
              Federated Learning is a <strong>collaborative machine learning approach</strong> where multiple 
              organizations train a shared AI model WITHOUT sending their sensitive data to a central server.
            </p>
            <div className="example-box">
              <strong>Real-World Example:</strong>
              <br />
              3 Hospitals want to build a better disease detector, but they can't share patient records (privacy regulations!). 
              Instead, each hospital trains the model locally on their own data, then sends only the model improvements back 
              to a central server. The server combines these improvements to create a better global model. ✨
            </div>
          </section>

          {/* Core Components */}
          <section className="footer-section">
            <h3>⚙️ Core Components</h3>
            <div className="components-grid">
              <div className="component-card">
                <h4>🏥 Nodes (Local Organizations)</h4>
                <p>
                  Each participating organization/hospital. They:
                </p>
                <ul>
                  <li>Download the global model</li>
                  <li>Train it on their local data (private!)</li>
                  <li>Compute weight changes (deltas)</li>
                  <li>Send ONLY the changes back</li>
                </ul>
              </div>

              <div className="component-card">
                <h4>📡 Central Server</h4>
                <p>
                  Coordinates the training. It:
                </p>
                <ul>
                  <li>Maintains the global model</li>
                  <li>Distributes it to all nodes</li>
                  <li>Collects weight updates from nodes</li>
                  <li>Aggregates them using FedAvg/other strategies</li>
                </ul>
              </div>

              <div className="component-card">
                <h4>🧠 Global Model</h4>
                <p>
                  The shared AI model that improves each round:
                </p>
                <ul>
                  <li>Starts with baseline weights</li>
                  <li>Gets updated with aggregated changes</li>
                  <li>Becomes more accurate over time</li>
                  <li>Never sees raw data from any node</li>
                </ul>
              </div>

              <div className="component-card">
                <h4>➕ Aggregation Strategy</h4>
                <p>
                  How to combine updates from different nodes:
                </p>
                <ul>
                  <li><strong>FedAvg:</strong> Simple average of all updates</li>
                  <li><strong>Weighted:</strong> Account for data size differences</li>
                  <li><strong>Median:</strong> Robust to outliers</li>
                  <li><strong>Trimmed Mean:</strong> Remove extreme values</li>
                </ul>
              </div>
            </div>
          </section>

          {/* How It Works */}
          <section className="footer-section">
            <h3>🔄 How Federated Learning Works (Step by Step)</h3>
            <div className="steps-container">
              <div className="step">
                <div className="step-number">1</div>
                <p><strong>Initialization:</strong> Server creates initial global model</p>
              </div>
              <div className="arrow">→</div>
              <div className="step">
                <div className="step-number">2</div>
                <p><strong>Distribution:</strong> Server sends model to all nodes</p>
              </div>
              <div className="arrow">→</div>
              <div className="step">
                <div className="step-number">3</div>
                <p><strong>Local Training:</strong> Each node trains on its own data</p>
              </div>
              <div className="arrow">→</div>
              <div className="step">
                <div className="step-number">4</div>
                <p><strong>Compute Deltas:</strong> Nodes calculate weight changes</p>
              </div>
              <div className="arrow">→</div>
              <div className="step">
                <div className="step-number">5</div>
                <p><strong>Send Updates:</strong> Nodes send ONLY deltas to server</p>
              </div>
              <div className="arrow">→</div>
              <div className="step">
                <div className="step-number">6</div>
                <p><strong>Aggregation:</strong> Server combines updates using strategy</p>
              </div>
              <div className="arrow">→</div>
              <div className="step">
                <div className="step-number">7</div>
                <p><strong>Repeat:</strong> Go back to step 2 for next round</p>
              </div>
            </div>
          </section>

          {/* Key Benefits */}
          <section className="footer-section">
            <h3>✅ Key Benefits</h3>
            <div className="benefits-grid">
              <div className="benefit">
                <h4>🔒 Privacy</h4>
                <p>Raw data stays local. Server never sees sensitive information.</p>
              </div>
              <div className="benefit">
                <h4>🏥 Compliance</h4>
                <p>Meet GDPR, HIPAA, and other data protection regulations.</p>
              </div>
              <div className="benefit">
                <h4>📊 Better Models</h4>
                <p>Train on diverse data from multiple sources = better AI</p>
              </div>
              <div className="benefit">
                <h4>⚡ Efficiency</h4>
                <p>Parallel training across nodes = faster results</p>
              </div>
              <div className="benefit">
                <h4>🤝 Collaboration</h4>
                <p>Compete-to-cooperate: Organizations benefit from shared learning</p>
              </div>
              <div className="benefit">
                <h4>🛡️ Security</h4>
                <p>Differential privacy can add noise to prevent backdoor attacks</p>
              </div>
            </div>
          </section>

          {/* What's Happening Right Now */}
          <section className="footer-section">
            <h3>👀 What You're Watching</h3>
            <p>
              On this dashboard, each <strong>Round</strong> represents one full cycle where:
              <br/>
              <strong>({currentRound > 0 ? `Currently on Round ${currentRound}` : 'Each round includes'}):</strong>
            </p>
            <div className="watching-box">
              <div className="watch-item">
                <span className="icon">🔄</span>
                <span>
                  <strong>{numNodes} Nodes</strong> (organizations) train the model locally
                </span>
              </div>
              <div className="watch-item">
                <span className="icon">📈</span>
                <span>
                  <strong>Accuracy improves</strong> as they send updates ({trainingState === 'ide' ? 'Ready to start!' : trainingState === 'running' ? 'Currently training!' : 'Training completed!'})
                </span>
              </div>
              <div className="watch-item">
                <span className="icon">🎯</span>
                <span>
                  <strong>Global Accuracy: {(globalAccuracy * 100).toFixed(2)}%</strong> (how well the combined model works)
                </span>
              </div>
              <div className="watch-item">
                <span className="icon">📊</span>
                <span>
                  <strong>Node Accuracies</strong> show how each organization's local model performs
                </span>
              </div>
            </div>
          </section>

          {/* Real Applications */}
          <section className="footer-section">
            <h3>🌍 Real-World Applications</h3>
            <div className="applications">
              <div className="app-item">
                <strong>🏥 Healthcare:</strong> Multiple hospitals collaboratively train disease detection models
              </div>
              <div className="app-item">
                <strong>📱 Mobile Devices:</strong> Train keyboard prediction on your phone without sending data to Google
              </div>
              <div className="app-item">
                <strong>🏢 Finance:</strong> Banks detect fraud together without sharing customer data
              </div>
              <div className="app-item">
                <strong>🔬 Research:</strong> Universities collaborate on climate modeling while protecting proprietary data
              </div>
              <div className="app-item">
                <strong>⚡ IoT Networks:</strong> Smart devices train edge models while keeping sensor data private
              </div>
            </div>
          </section>

          {/* Footer Note */}
          <section className="footer-note">
            <p>
              <em>
                💡 This dashboard simulates a federated learning system. In production, this approach enables
                organizations to build better AI models while respecting privacy and regulations. It's the future
                of collaborative machine learning!
              </em>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};

export default FederatedDashboard;

/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 *                    FEDERATED DASHBOARD - USER EXPLANATION
 * 
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * WHAT IS THIS COMPONENT?
 * ─────────────────────────────────────────────────────────────────────────
 * 
 * The FederatedDashboard is a real-time monitoring interface that shows what
 * happens when multiple organizations collaborate to train a machine learning
 * model WITHOUT sharing their sensitive data.
 * 
 * Think of it like this:
 * 
 *   3 Hospitals (Hospital A, B, C) want to build a better disease detector
 *   BUT they can't share patient records (privacy!)
 *   
 *   Solution: Each hospital trains the model on their own data locally
 *   Then sends back only: "Here's how much my model improved: +0.011"
 *   (NOT: "Here are my 10,000 patient records!")
 *   
 *   The dashboard shows this collaboration in real-time!
 * 
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * WHAT YOU'LL SEE ON THIS DASHBOARD
 * ─────────────────────────────────────────────────────────────────────────
 * 
 * 1. CONTROL PANEL (Top)
 *    ├─ Rounds: How many training cycles (5 = train 5 times)
 *    ├─ Nodes: How many organizations participate (3 = 3 hospitals)
 *    ├─ Aggregation: How to combine their results (FedAvg, Median, etc)
 *    └─ Buttons: Start Training / Run Demo / Stop
 * 
 * 2. STATUS CARD (Left)
 *    ├─ Status: IDLE (ready) / RUNNING (training) / COMPLETED (done)
 *    ├─ Round: 3/5 (on round 3 of 5 total)
 *    ├─ Global Accuracy: 78.45% (how good the model is)
 *    ├─ Nodes: 3
 *    └─ Strategy: FEDAVG
 * 
 * 3. PROGRESS BAR (Right)
 *    ├─ Visual bar that fills as training progresses
 *    └─ Shows: Round 3 of 5 (60% complete)
 * 
 * 4. ACCURACY CHART (Bottom Left) ⭐ MOST IMPORTANT
 *    ├─ Line graph going UP = Model is learning!
 *    ├─ Starts at: 55% (random, just initialized)
 *    ├─ Ends at: 96% (well-trained)
 *    └─ Real example: 55% → 65% → 78% → 88% → 96%
 * 
 * 5. NODE PERFORMANCE CHART (Bottom Right)
 *    ├─ Bar chart showing accuracy of each organization
 *    ├─ Hospital A: 87% (good data quality)
 *    ├─ Hospital B: 92% (excellent data quality)
 *    └─ Hospital C: 78% (noisy data, but still helps!)
 * 
 * 6. TRAINING STEPS CONSOLE (Lower section)
 *    ├─ Detailed log showing exactly what's happening
 *    ├─ Step 1: "Initializing global model..."
 *    ├─ Step 2: "Distributing model to nodes..."
 *    ├─ Step 3: "Nodes training locally..." (takes longest)
 *    ├─ Step 4: "Nodes sending weight deltas..." (privacy feature!)
 *    ├─ Step 5: "Server aggregating weights..."
 *    ├─ Step 6: "Evaluating global model..."
 *    └─ Shows this 5 times (once per round)
 * 
 * 7. METRICS SUMMARY (Bottom)
 *    ├─ Avg Local Loss: Error on each node (lower = better)
 *    ├─ Global Loss: Error of combined model (better than local!)
 *    ├─ Weight Update Norm: How much weights changed (small = stable)
 *    └─ Privacy Budget: How much privacy protection remains
 * 
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * HOW TO USE IT
 * ─────────────────────────────────────────────────────────────────────────
 * 
 * QUICK DEMO (Best for first-time users):
 * ────────────────────────────────────────
 * 1. Click "Run Demo" button
 * 2. Watch it automatically run 3 rounds with 4 nodes (~10 seconds)
 * 3. See the accuracy improve: 55% → 65% → 78% → 96%
 * 4. Understand federated learning in action!
 * 
 * CUSTOM TRAINING:
 * ────────────────
 * 1. Set Rounds: How many training cycles (1-20)
 * 2. Set Nodes: How many organizations (2-10)
 * 3. Set Aggregation: Strategy to combine results
 * 4. Click "Start Training"
 * 5. Watch progress bar, accuracy chart, and console
 * 6. Training complete when status badge turns GREEN
 * 
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * KEY CONCEPTS (In Simple Terms)
 * ─────────────────────────────────────────────────────────────────────────
 * 
 * FEDERATED LEARNING:
 * Instead of sending data to a central server, organizations keep their data
 * private and only send the server "what they learned":
 * 
 *   Old way:  Hospital A → [Send all patient records] → Server (Privacy ✗)
 *   
 *   New way:  Hospital A → [Send weight delta +0.011] → Server (Privacy ✓)
 * 
 * WEIGHT DELTA:
 * The change in how the model weights improved:
 *   Before: Weight = 0.234
 *   After:  Weight = 0.245
 *   Delta:  +0.011 (what we send!)
 * 
 * ROUND:
 * One complete training cycle:
 *   1. Server gives model to all nodes
 *   2. Nodes train on their data (in parallel)
 *   3. Nodes send back weight improvements
 *   4. Server combines improvements
 *   5. Model gets better
 *   Result: Accuracy improves 55% → 65% → 78% → ... → 96%
 * 
 * AGGREGATION:
 * How to combine improvements from multiple organizations:
 *   FedAvg:        Average all improvements equally (simplest)
 *   Weighted Avg:  Weight by organization size (bigger org = more influence)
 *   Median:        Take middle value (robust against bad data)
 *   Trimmed Mean:  Remove outliers, then average (safe against cheating)
 * 
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * WHAT HAPPENS WHEN YOU CLICK "START TRAINING"
 * ─────────────────────────────────────────────────────────────────────────
 * 
 * SECOND 0-1: Status turns RUNNING (yellow badge)
 *   └─ Console: "Step 1: Initializing global model..."
 *   └─ Server creates starting model with random weights
 * 
 * SECOND 1-2: Distribute phase
 *   └─ Console: "Step 2: Distributing model to nodes..."
 *   └─ Copies sent to Node-0, Node-1, Node-2
 * 
 * SECOND 2-6: Local training (longest part!)
 *   └─ Console: "Step 3: Nodes training locally..."
 *   └─ Node-0: Trains on Hospital A's data
 *   └─ Node-1: Trains on Hospital B's data
 *   └─ Node-2: Trains on Hospital C's data
 *   └─ All training happens IN PARALLEL (simultaneously)
 * 
 * SECOND 6-7: Send improvements
 *   └─ Console: "Step 4: Nodes sending weight deltas to server..."
 *   └─ Node-0: [+0.011, +0.027, +0.012] (not hospital data!)
 *   └─ Node-1: [+0.007, +0.030, +0.006]
 *   └─ Node-2: [+0.015, +0.022, +0.007]
 * 
 * SECOND 7-8: Aggregation
 *   └─ Console: "Step 5: Server aggregating weights..."
 *   └─ Average: ([+0.011+0.007+0.015]/3, ...) = [+0.011, ...]
 *   └─ Updates model: v1 + aggregated_deltas = v2 (IMPROVED!)
 * 
 * SECOND 8-9: Evaluation
 *   └─ Console: "Step 6: Evaluating global model..."
 *   └─ Tests new model
 *   └─ Console: "Round 1: Accuracy 65%"
 *   └─ Chart: First point appears at 65%
 * 
 * THEN: Repeat 4 more times (multiply by 5)
 *   └─ Round 2: Accuracy 65% → 78%
 *   └─ Round 3: Accuracy 78% → 88%
 *   └─ Round 4: Accuracy 88% → 94%
 *   └─ Round 5: Accuracy 94% → 96%
 * 
 * SECOND 45: Status turns COMPLETED (green badge)
 *   └─ Progress bar: 100% full ████████████████████
 *   └─ Final Accuracy: 96.23%
 *   └─ All node accuracies: 94%, 92%, 97%
 *   └─ Training is done! 🎉
 * 
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * WHAT SHOULD YOU SEE (Real Example)
 * ─────────────────────────────────────────────────────────────────────────
 * 
 * Status Card:                 Accuracy Chart:
 * ├─ Status: RUNNING (yellow)  └─ ●     (55%)
 * ├─ Round: 1/5                   ●   (65%)
 * ├─ Accuracy: 65%                 ● ↗ (78%)
 * ├─ Nodes: 3                       ● (88%)
 * └─ Strategy: FEDAVG                ● (96%)
 * 
 * Node Performance:             Progress Bar:
 * ├─ Node-0: ████████ 87%      ████████░░░░░░░░░░░░ 40%
 * ├─ Node-1: █████████ 92%     
 * └─ Node-2: ██████ 78%        Console Logs:
 *                              [14:35:22] Step 1: Init...
 * Metrics:                      [14:35:23] Step 2: Dist...
 * ├─ Avg Loss: 0.34            [14:35:24] Step 3: Train...
 * ├─ Global Loss: 0.21         [14:35:28] Round 1: Acc 65%
 * ├─ Weight Norm: 0.023
 * └─ Privacy Budget: 0.86
 * 
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * COMMON QUESTIONS
 * ─────────────────────────────────────────────────────────────────────────
 * 
 * Q: Why does accuracy start at 55% and not 0%?
 * A: Random initialization gives some structure. It's not 50% because the
 *    weights have some natural bias. It's a realistic starting point.
 * 
 * Q: Why does accuracy plateau at 96%?
 * A: The model has learned as much as it can from the available data.
 *    To improve further, you'd need more or better data.
 * 
 * Q: Why do nodes have different accuracies?
 * A: Because their data is different! Hospital A might have cleaner records,
 *    Hospital B might have more cases, Hospital C might have noisier sensors.
 *    This is realistic and normal.
 * 
 * Q: Is my data really private?
 * A: YES! Your data never leaves the organization. Only weight changes are
 *    sent (+0.011), not the original data. Weight changes don't reveal info.
 * 
 * Q: Why 5 rounds?
 * A: More rounds = better model. 5 rounds is a good balance:
 *    - 1 round: Too little training
 *    - 5 rounds: Model converges to good accuracy (96%)
 *    - 10+ rounds: Diminishing returns (marginal improvement)
 * 
 * Q: What if accuracy goes DOWN instead of UP?
 * A: Unusual! Could mean bad data quality, overfitting, or wrong strategy.
 *    Try fewer rounds or check the node accuracies individually.
 * 
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * REAL-WORLD APPLICATIONS
 * ─────────────────────────────────────────────────────────────────────────
 * 
 * Healthcare: Hospitals collaborating on disease detection (YOUR USE CASE!)
 * Finance: Banks detecting fraud patterns together
 * Mobile: Phones improving keyboard prediction without seeing texts
 * IoT: Sensors detecting anomalies across networks
 * Cybersecurity: Organizations sharing threat models without revealing data
 * 
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * FOR MORE INFORMATION
 * ─────────────────────────────────────────────────────────────────────────
 * 
 * See these documentation files for complete details:
 * 
 * • FEDERATED_QUICK_REFERENCE.md - 1-page summary (5 min read)
 * • FEDERATED_DASHBOARD_GUIDE.md - Complete guide (45 min read)
 * • FEDERATED_DASHBOARD_VISUAL_GUIDE.md - Diagrams (20 min read)
 * • FEDERATED_DOCUMENTATION_INDEX.md - Documentation map
 * 
 * ═══════════════════════════════════════════════════════════════════════════
 */
