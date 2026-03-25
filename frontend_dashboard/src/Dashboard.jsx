import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import './Dashboard.css';

const API_BASE = 'http://localhost:8000/api/v1';
const WS_URL = 'ws://localhost:8000/ws/dashboard';

// ============================================================================
// DASHBOARD COMPONENT
// ============================================================================

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('testing'); // 'testing' or 'soc'
  const [loading, setLoading] = useState(false);

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>⚔️ ChakraVyuh - Testing & SOC Dashboard</h1>
        <p>Real-time Network Anomaly Detection & Testing</p>
      </header>

      <nav className="dashboard-nav">
        <button 
          className={`nav-btn ${activeTab === 'testing' ? 'active' : ''}`}
          onClick={() => setActiveTab('testing')}
        >
          🧪 Testing Dashboard
        </button>
        <button 
          className={`nav-btn ${activeTab === 'soc' ? 'active' : ''}`}
          onClick={() => setActiveTab('soc')}
        >
          🛡️ SOC Dashboard
        </button>
      </nav>

      <main className="dashboard-main">
        {activeTab === 'testing' && <TestingDashboard />}
        {activeTab === 'soc' && <SocDashboard />}
      </main>
    </div>
  );
}

// ============================================================================
// TESTING DASHBOARD
// ============================================================================

function TestingDashboard() {
  const [attacks, setAttacks] = useState({});
  const [selectedAttack, setSelectedAttack] = useState(null);
  const [nFlows, setNFlows] = useState(100);
  const [testing, setTesting] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const [testHistory, setTestHistory] = useState([]);
  const [running, setRunning] = useState(false);
  const [loadingAttacks, setLoadingAttacks] = useState(true);
  const [attackError, setAttackError] = useState(null);

  // Load attack types
  useEffect(() => {
    fetchAttacks();
    fetchTestResults();
  }, []);

  const fetchAttacks = async () => {
    try {
      setLoadingAttacks(true);
      setAttackError(null);
      const res = await axios.get(`${API_BASE}/testing/attacks`);
      console.log('Attacks loaded:', res.data);
      setAttacks(res.data);
      const firstKey = Object.keys(res.data)[0];
      if (firstKey) {
        setSelectedAttack(firstKey);
      }
    } catch (err) {
      console.error('Failed to load attacks:', err);
      setAttackError(err.message);
      // Provide fallback attacks in demo mode
      const demoAttacks = {
        'port_scan': { name: 'Port Scanning', severity: 'MEDIUM' },
        'dos_flood': { name: 'DoS/DDoS Flood', severity: 'CRITICAL' },
        'brute_force': { name: 'Brute Force', severity: 'HIGH' },
        'slow_exfiltration': { name: 'Data Exfiltration', severity: 'CRITICAL' },
        'command_injection': { name: 'Command Injection', severity: 'CRITICAL' },
        'stealth_scanning': { name: 'Stealth Scanning', severity: 'MEDIUM' }
      };
      setAttacks(demoAttacks);
      setSelectedAttack('port_scan');
    } finally {
      setLoadingAttacks(false);
    }
  };

  const fetchTestResults = async () => {
    try {
      const res = await axios.get(`${API_BASE}/testing/results?limit=10`);
      setTestHistory(res.data.results || []);
    } catch (err) {
      console.error('Failed to load results:', err);
    }
  };

  const runSingleTest = async () => {
    if (!selectedAttack) return;
    
    setTesting(true);
    try {
      const res = await axios.post(
        `${API_BASE}/testing/run-test`,
        {},
        { params: { attack_type: selectedAttack, n_flows: nFlows } }
      );
      
      setLastResult(res.data);
      setTestHistory([res.data, ...testHistory.slice(0, 9)]);
    } catch (err) {
      alert(`Test failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setTesting(false);
    }
  };

  const runFullSuite = async () => {
    setRunning(true);
    try {
      const res = await axios.post(`${API_BASE}/testing/run-suite`);
      
      // Update test history with all results from the suite
      if (res.data.results) {
        const results = Object.values(res.data.results).map(r => ({
          ...r,
          attack_type: r.attack_type || 'unknown'
        }));
        setTestHistory(results.concat(testHistory).slice(0, 20));
      }
      
      // Show summary with pass/fail counts
      alert(
        `Full suite completed!\n` +
        `Total: ${res.data.total_tests}\n` +
        `Passed: ${res.data.passed}\n` +
        `Failed: ${res.data.failed}\n` +
        `Pass Rate: ${(res.data.pass_rate * 100).toFixed(1)}%`
      );
      
      await fetchTestResults();
    } catch (err) {
      alert(`Suite failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setRunning(false);
    }
  };

  const selectedAttackInfo = attacks[selectedAttack] || {};

  return (
    <div className="testing-dashboard">
      <div className="testing-grid">
        
        {/* Test Control Panel */}
        <section className="panel test-control">
          <h2>🎯 Attack Simulator</h2>
          
          {attackError && (
            <div style={{ padding: '10px', marginBottom: '15px', backgroundColor: '#fef3cd', border: '1px solid #ffc107', borderRadius: '4px', color: '#856404' }}>
              <strong>⚠️ Backend Connection:</strong> Using demo attacks (server may be down)
            </div>
          )}
          
          <div className="form-group">
            <label>Select Attack Type:</label>
            {loadingAttacks ? (
              <div style={{ padding: '8px', color: '#999' }}>Loading attacks...</div>
            ) : (
              <select 
                value={selectedAttack || ''} 
                onChange={(e) => setSelectedAttack(e.target.value)}
                disabled={testing}
              >
                <option value="">-- Select an attack --</option>
                {Object.keys(attacks).map(key => (
                  <option key={key} value={key}>
                    {attacks[key].name || key}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="form-group">
            <label>Number of Flows: {nFlows}</label>
            <input 
              type="range" 
              min="10" 
              max="1000" 
              step="10"
              value={nFlows}
              onChange={(e) => setNFlows(parseInt(e.target.value))}
              disabled={testing}
            />
          </div>

          {selectedAttackInfo && (
            <div className="attack-info">
              <h3>{selectedAttackInfo.name}</h3>
              <p><strong>Severity:</strong> <span className={`severity ${selectedAttackInfo.severity}`}>
                {selectedAttackInfo.severity}
              </span></p>
              <p><strong>Description:</strong> {selectedAttackInfo.description}</p>
              <p><strong>Indicators:</strong></p>
              <ul>
                {selectedAttackInfo.indicators?.map((ind, i) => (
                  <li key={i}>{ind}</li>
                ))}
              </ul>
              <p><strong>Tools:</strong> {selectedAttackInfo.common_tools?.join(', ')}</p>
            </div>
          )}

          <div className="button-group">
            <button 
              className="btn btn-primary"
              onClick={runSingleTest}
              disabled={testing || !selectedAttack}
            >
              {testing ? '⏳ Testing...' : '▶️ Run Test'}
            </button>
            <button 
              className="btn btn-secondary"
              onClick={runFullSuite}
              disabled={running}
            >
              {running ? '⏳ Running...' : '🔄 Full Suite'}
            </button>
          </div>
        </section>

        {/* Results */}
        <section className="panel test-results">
          <h2>📊 Latest Test Result</h2>
          
          {lastResult ? (
            <div className={`result-card status-${lastResult.status?.toLowerCase()}`}>
              <div className="result-header">
                <h3>{lastResult.attack_type || 'N/A'}</h3>
                <span className={`status-badge ${lastResult.status?.toLowerCase()}`}>
                  {lastResult.status}
                </span>
              </div>
              
              <div className="result-metrics">
                <div className="metric">
                  <label>Detection Rate</label>
                  <div className="value">{(lastResult.detection_rate * 100).toFixed(1)}%</div>
                  <div className="sub-label">{lastResult.n_detected}/{lastResult.n_flows} flows</div>
                </div>
                
                <div className="metric">
                  <label>Avg Anomaly Score</label>
                  <div className="value">{lastResult.avg_anomaly_score?.toFixed(4)}</div>
                </div>

                <div className="metric">
                  <label>Test ID</label>
                  <div className="value" style={{fontSize: '0.9em'}}>{lastResult.test_id}</div>
                </div>

                <div className="metric">
                  <label>Timestamp</label>
                  <div className="value" style={{fontSize: '0.85em'}}>
                    {new Date(lastResult.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>

              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{width: `${lastResult.detection_rate * 100}%`}}
                ></div>
              </div>
            </div>
          ) : (
            <p className="placeholder">Run a test to see results</p>
          )}
        </section>

        {/* Test History */}
        <section className="panel test-history">
          <h2>📈 Test History</h2>
          {testHistory.length > 0 ? (
            <table className="results-table">
              <thead>
                <tr>
                  <th>Attack Type</th>
                  <th>Detection Rate</th>
                  <th>Status</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {testHistory.map((result, i) => (
                  <tr key={i} className={`status-${result.status?.toLowerCase()}`}>
                    <td>{result.attack_type}</td>
                    <td>{(result.detection_rate * 100).toFixed(1)}%</td>
                    <td><span className="badge">{result.status}</span></td>
                    <td>{new Date(result.timestamp).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="placeholder">No test results yet</p>
          )}
        </section>

        {/* Chart */}
        <section className="panel chart-section">
          <h2>📉 Detection Performance</h2>
          {testHistory.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={testHistory.reverse()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="attack_type" angle={-45} textAnchor="end" height={80} />
                <YAxis label={{ value: 'Detection Rate %', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value) => `${(value * 100).toFixed(1)}%`} />
                <Line 
                  type="monotone" 
                  dataKey="detection_rate" 
                  stroke="#8884d8"
                  dot={{r: 4}}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="placeholder">Run tests to see performance chart</p>
          )}
        </section>
      </div>
    </div>
  );
}

// ============================================================================
// SOC DASHBOARD
// ============================================================================

function SocDashboard() {
  const [overview, setOverview] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [threatMap, setThreatMap] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const wsRef = useRef(null);

  const fetchOverview = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/dashboard/overview`);
      setOverview(res.data);
      setAlerts(res.data.recent_alerts || []);
    } catch (err) {
      console.error('Failed to load overview:', err);
    }
  }, []);

  const fetchThreatMap = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/dashboard/threat-map`);
      setThreatMap(res.data.threats || []);
    } catch (err) {
      console.error('Failed to load threat map:', err);
    }
  }, []);

  const fetchHoneypotAlerts = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/honeypot/alerts?limit=100`);
      if (res.data.alerts && res.data.alerts.length > 0) {
        // Add honeypot alerts to the alerts list
        setAlerts(prev => {
          const honeypotAlerts = res.data.alerts.map(alert => ({
            ...alert,
            flow_id: `honeypot_${alert.source}_${Date.now()}_${Math.random()}`,
            severity: alert.severity || 'HIGH',
            timestamp: alert.timestamp || new Date().toISOString()
          }));
          // Merge with existing alerts, sorted by timestamp
          const merged = [...honeypotAlerts, ...prev];
          return merged.slice(0, 30); // Keep last 30 alerts
        });
      }
    } catch (err) {
      console.warn('Failed to load honeypot alerts:', err);
    }
  }, []);

  // Setup WebSocket for real-time updates
  useEffect(() => {
    fetchOverview();
    fetchThreatMap();
    fetchHoneypotAlerts();

    // Connect to WebSocket
    let reconnectAttempts = 0;
    const connectWebSocket = () => {
      try {
        wsRef.current = new WebSocket(WS_URL);
        
        wsRef.current.onopen = () => {
          console.log('WebSocket connected to dashboard');
          reconnectAttempts = 0;
        };
        
        wsRef.current.onmessage = (event) => {
          const message = JSON.parse(event.data);
          
          if (message.type === 'new_flow' && message.alert) {
            setAlerts(prev => [message.alert, ...prev.slice(0, 19)]);
          } else if (message.type === 'test_completed') {
            // Refresh dashboard when test completes
            fetchOverview();
            fetchThreatMap();
          } else if (message.type === 'suite_completed') {
            // Refresh dashboard when suite completes
            fetchOverview();
            fetchThreatMap();
          }
        };
        
        wsRef.current.onerror = (err) => {
          console.error('WebSocket error:', err);
        };
        
        wsRef.current.onclose = () => {
          console.warn('WebSocket disconnected, attempting to reconnect...');
          if (reconnectAttempts < 5) {
            reconnectAttempts++;
            setTimeout(connectWebSocket, 3000);
          }
        };
      } catch (err) {
        console.warn('WebSocket connection failed:', err);
        setTimeout(connectWebSocket, 3000);
      }
    };

    connectWebSocket();

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [fetchOverview, fetchThreatMap, fetchHoneypotAlerts]);

  // Periodic polling as fallback (every 5 seconds)
  useEffect(() => {
    const pollInterval = setInterval(() => {
      fetchOverview();
      fetchThreatMap();
      fetchHoneypotAlerts();
    }, 5000);

    return () => clearInterval(pollInterval);
  }, [fetchOverview, fetchThreatMap, fetchHoneypotAlerts]);

  const getSeverityColor = (severity) => {
    const colors = {
      'CRITICAL': '#ef4444',
      'HIGH': '#f97316',
      'MEDIUM': '#eab308',
      'LOW': '#22c55e'
    };
    return colors[severity] || '#6b7280';
  };

  return (
    <div className="soc-dashboard">
      <div className="soc-grid">
        
        {/* Key Metrics */}
        <section className="metrics-panel">
          <h2>📊 Key Metrics</h2>
          {overview ? (
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-value">{overview.detector?.alerts_emitted || 0}</div>
                <div className="metric-label">Total Alerts</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">
                  {overview.detector?.flows_processed || 0}
                </div>
                <div className="metric-label">Flows Processed</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">
                  {overview.detector?.threshold?.toFixed(4) || '0'}
                </div>
                <div className="metric-label">Detection Threshold</div>
              </div>
              <div className="metric-card">
                <div className="metric-value">
                  {overview.testing?.total_tests || 0}
                </div>
                <div className="metric-label">Tests Run</div>
              </div>
            </div>
          ) : (
            <p>Loading metrics...</p>
          )}
        </section>

        {/* Real-time Alerts */}
        <section className="alerts-panel">
          <div className="panel-header">
            <h2>🚨 Real-time Alerts ({alerts.length})</h2>
            <button className="btn-small" onClick={() => fetchOverview()}>🔄</button>
          </div>
          
          {alerts.length > 0 ? (
            <div className="alerts-list">
              {alerts.slice(0, 15).map((alert, i) => (
                <div 
                  key={i} 
                  className="alert-item"
                  style={{borderLeftColor: getSeverityColor(alert.severity)}}
                >
                  <div className="alert-header">
                    <span className="alert-flow">{alert.flow_id}</span>
                    <span 
                      className="alert-severity"
                      style={{backgroundColor: getSeverityColor(alert.severity)}}
                    >
                      {alert.severity}
                    </span>
                  </div>
                  <div className="alert-details">
                    <span>Score: {alert.anomaly_score?.toFixed(4)}</span>
                    <span>{new Date(alert.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="placeholder">No alerts detected</p>
          )}
        </section>

        {/* Threat Map */}
        <section className="threat-map-panel">
          <h2>🗺️ Threat Map</h2>
          {threatMap.length > 0 ? (
            <div className="threat-list">
              {threatMap.slice(0, 10).map((threat, i) => (
                <div key={i} className="threat-item">
                  <div className="threat-info">
                    <div className="threat-id">{threat.flow_id}</div>
                    <div className="threat-count">
                      {threat.count} event{threat.count > 1 ? 's' : ''}
                    </div>
                  </div>
                  <div 
                    className="threat-severity"
                    style={{backgroundColor: getSeverityColor(threat.severity)}}
                  >
                    {threat.severity}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="placeholder">No threats detected</p>
          )}
        </section>

        {/* Test Status */}
        <section className="test-status-panel">
          <h2>🧪 Testing Status</h2>
          {overview?.testing ? (
            <div className="status-info">
              <div className="status-row">
                <span>Total Tests</span>
                <strong>{overview.testing.total_tests}</strong>
              </div>
              <div className="status-row">
                <span>Passed</span>
                <strong className="text-success">{overview.testing.passed_tests}</strong>
              </div>
              <div className="status-row">
                <span>Failed</span>
                <strong className="text-danger">{overview.testing.failed_tests}</strong>
              </div>
              <div className="status-row">
                <span>Avg Detection Rate</span>
                <strong>
                  {(overview.testing.avg_detection_rate * 100).toFixed(1)}%
                </strong>
              </div>
              
              {overview.testing.avg_detection_rate !== undefined && (
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{width: `${overview.testing.avg_detection_rate * 100}%`}}
                  ></div>
                </div>
              )}
            </div>
          ) : (
            <p>No test data</p>
          )}
        </section>

        {/* Alert Distribution */}
        <section className="chart-panel">
          <h2>📈 Alert Distribution by Severity</h2>
          {alerts.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={computeSeverityDistribution(alerts)}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((severity) => (
                    <Cell 
                      key={severity} 
                      fill={severity === 'CRITICAL' ? '#ef4444' : 
                            severity === 'HIGH' ? '#f97316' :
                            severity === 'MEDIUM' ? '#eab308' : '#22c55e'}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="placeholder">Run tests to generate alerts</p>
          )}
        </section>
      </div>
    </div>
  );
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function computeSeverityDistribution(alerts) {
  const counts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
  alerts.forEach(a => {
    if (counts.hasOwnProperty(a.severity)) {
      counts[a.severity]++;
    }
  });
  return [
    { name: 'CRITICAL', value: counts.CRITICAL },
    { name: 'HIGH', value: counts.HIGH },
    { name: 'MEDIUM', value: counts.MEDIUM },
    { name: 'LOW', value: counts.LOW }
  ].filter(d => d.value > 0);
}
