const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3001;

// Simple static file server for testing
const server = http.createServer((req, res) => {
  let filePath = req.url;
  
  // Default to index.html
  if (filePath === '/') {
    filePath = '/index.html';
  }
  
  // Add CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  // Simple routing - serve our test dashboard
  if (filePath === '/index.html') {
    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Test</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
        }
        
        .app-bar {
            background: #1976d2;
            color: white;
            padding: 16px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .title {
            font-size: 1.25rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 0.875rem;
        }
        
        .status-chip {
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 16px;
        }
        
        .container {
            max-width: 1200px;
            margin: 24px auto;
            padding: 0 24px;
        }
        
        .grid {
            display: grid;
            gap: 16px;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }
        
        .widget {
            background: white;
            border-radius: 8px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid rgba(0,0,0,0.05);
        }
        
        .widget-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        
        .widget-title {
            font-size: 1rem;
            font-weight: 500;
            color: #333;
        }
        
        .widget-description {
            font-size: 0.875rem;
            color: #666;
            margin-top: 4px;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1976d2;
            line-height: 1;
        }
        
        .metric-unit {
            font-size: 1rem;
            color: #666;
            font-weight: normal;
        }
        
        .chart-placeholder {
            height: 200px;
            background: linear-gradient(45deg, #f0f0f0 25%, transparent 25%), 
                        linear-gradient(-45deg, #f0f0f0 25%, transparent 25%);
            background-size: 20px 20px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #999;
            font-style: italic;
        }
        
        .auth-form {
            max-width: 400px;
            margin: 100px auto;
            background: white;
            padding: 32px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .form-title {
            text-align: center;
            margin-bottom: 24px;
            color: #333;
        }
        
        .form-group {
            margin-bottom: 16px;
        }
        
        .form-label {
            display: block;
            margin-bottom: 4px;
            color: #555;
            font-weight: 500;
        }
        
        .form-input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
        }
        
        .btn {
            width: 100%;
            padding: 12px;
            background: #1976d2;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 1rem;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        
        .btn:hover {
            background: #1565c0;
        }
        
        .demo-creds {
            margin-top: 16px;
            padding: 12px;
            background: #f5f5f5;
            border-radius: 4px;
            font-size: 0.875rem;
        }
        
        /* Responsive design - 320px to 4K */
        @media (max-width: 320px) {
            .container { padding: 0 8px; margin: 16px auto; }
            .grid { grid-template-columns: 1fr; gap: 8px; }
            .widget { padding: 16px; }
            .metric-value { font-size: 2rem; }
            .app-bar { padding: 12px 16px; }
            .title { font-size: 1rem; }
        }
        
        @media (max-width: 480px) {
            .grid { grid-template-columns: 1fr; }
            .app-bar { flex-direction: column; gap: 8px; }
            .status { justify-content: center; }
        }
        
        @media (max-width: 768px) {
            .container { padding: 0 16px; }
            .widget { padding: 20px; }
        }
        
        @media (min-width: 3840px) {
            .container { max-width: 2400px; }
            .grid { grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); }
            .widget { transform: scale(1.05); }
        }
        
        .hidden { display: none; }
    </style>
</head>
<body>
    <!-- Login Form -->
    <div id="login-form" class="auth-form">
        <h2 class="form-title">🎛️ Dashboard Login</h2>
        <form onsubmit="handleLogin(event)">
            <div class="form-group">
                <label class="form-label">Username</label>
                <input type="text" class="form-input" id="username" value="demo_admin" required>
            </div>
            <div class="form-group">
                <label class="form-label">Password</label>
                <input type="password" class="form-input" id="password" value="demo123" required>
            </div>
            <button type="submit" class="btn">Sign In</button>
        </form>
        <div class="demo-creds">
            <strong>Demo Credentials:</strong><br>
            Username: demo_admin<br>
            Password: demo123<br>
            Role: Admin
        </div>
    </div>
    
    <!-- Dashboard -->
    <div id="dashboard" class="hidden">
        <div class="app-bar">
            <div class="title">
                🎛️ Operational Dashboard
            </div>
            <div class="status">
                <div class="status-chip" id="refresh-status">Updated just now</div>
                <div class="status-chip">Admin</div>
                <button onclick="handleLogout()" style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 4px 12px; border-radius: 4px; cursor: pointer;">Logout</button>
            </div>
        </div>
        
        <div class="container">
            <div class="grid">
                <div class="widget">
                    <div class="widget-header">
                        <div>
                            <div class="widget-title">System Performance</div>
                            <div class="widget-description">CPU and Memory Usage</div>
                        </div>
                    </div>
                    <div class="chart-placeholder" id="cpu-chart">Loading chart data...</div>
                </div>
                
                <div class="widget">
                    <div class="widget-header">
                        <div>
                            <div class="widget-title">Active Users</div>
                            <div class="widget-description">Currently logged in users</div>
                        </div>
                    </div>
                    <div class="metric-value" id="active-users">1,247</div>
                </div>
                
                <div class="widget">
                    <div class="widget-header">
                        <div>
                            <div class="widget-title">Error Rate</div>
                            <div class="widget-description">Application error percentage</div>
                        </div>
                    </div>
                    <div class="chart-placeholder" id="error-chart">Loading chart data...</div>
                </div>
                
                <div class="widget">
                    <div class="widget-header">
                        <div>
                            <div class="widget-title">Response Time</div>
                            <div class="widget-description">Average API response time</div>
                        </div>
                    </div>
                    <div class="metric-value">245<span class="metric-unit">ms</span></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let refreshInterval;
        
        function handleLogin(event) {
            event.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            // Simulate API call
            if (username === 'demo_admin' && password === 'demo123') {
                document.getElementById('login-form').classList.add('hidden');
                document.getElementById('dashboard').classList.remove('hidden');
                startAutoRefresh();
                loadDashboardData();
            } else {
                alert('Invalid credentials. Use demo_admin / demo123');
            }
        }
        
        function handleLogout() {
            document.getElementById('dashboard').classList.add('hidden');
            document.getElementById('login-form').classList.remove('hidden');
            stopAutoRefresh();
        }
        
        function loadDashboardData() {
            // Simulate loading data from backend
            fetch('http://localhost:8000/v1/dashboard/metrics/latest')
                .then(response => response.json())
                .then(data => {
                    console.log('Loaded metrics:', data);
                    updateCharts();
                })
                .catch(error => {
                    console.log('Backend not available, using mock data');
                    updateCharts();
                });
        }
        
        function updateCharts() {
            // Simulate chart updates
            document.getElementById('cpu-chart').innerHTML = 'CPU: 67% | Memory: 45%';
            document.getElementById('error-chart').innerHTML = 'Error Rate: 2.3%';
            
            // Update active users with random variation
            const baseUsers = 1200;
            const variation = Math.floor(Math.random() * 100);
            document.getElementById('active-users').textContent = (baseUsers + variation).toLocaleString();
            
            // Update refresh status
            const now = new Date().toLocaleTimeString();
            document.getElementById('refresh-status').textContent = \`Updated \${now}\`;
        }
        
        function startAutoRefresh() {
            // Auto-refresh every 5 minutes (as per spec)
            refreshInterval = setInterval(() => {
                loadDashboardData();
            }, 5 * 60 * 1000);
        }
        
        function stopAutoRefresh() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        }
        
        // Test responsive design
        function updateScreenInfo() {
            const width = window.innerWidth;
            document.title = \`Dashboard (\${width}px)\`;
        }
        
        window.addEventListener('resize', updateScreenInfo);
        updateScreenInfo();
        
        // Initial load
        document.addEventListener('DOMContentLoaded', () => {
            console.log('Dashboard Test Application Started');
            console.log('Backend API: http://localhost:8000');
        });
    </script>
</body>
</html>`;
    
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(html);
    return;
  }
  
  // 404 for other paths
  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('Not Found');
});

server.listen(PORT, () => {
  console.log(`🚀 Frontend Test Server Running!`);
  console.log(`📱 Dashboard: http://localhost:${PORT}`);
  console.log(`🔧 Backend API: http://localhost:8000`);
  console.log(`📖 API Docs: http://localhost:8000/docs`);
  console.log(`\nPress Ctrl+C to stop`);
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.log(`❌ Port ${PORT} is already in use`);
    console.log(`Try: netstat -ano | findstr :${PORT}`);
  } else {
    console.log(`❌ Server error: ${err.message}`);
  }
});