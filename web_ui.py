"""Simple Flask web UI for Guardrail agent."""

from flask import Flask, render_template_string, request, jsonify
from guardrail.agent import GuardrailAgent
import json
import traceback

app = Flask(__name__)

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Guardrail - Security Change Safety</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .main {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            padding: 30px;
        }
        
        .panel {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border: 1px solid #e9ecef;
        }
        
        .panel h2 {
            margin-bottom: 15px;
            color: #333;
            font-size: 1.2em;
        }
        
        textarea {
            width: 100%;
            min-height: 300px;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            resize: vertical;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        button {
            flex: 1;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            font-size: 1em;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .btn-secondary {
            background: #e9ecef;
            color: #333;
        }
        
        .btn-secondary:hover {
            background: #dee2e6;
        }
        
        .results {
            grid-column: 1 / -1;
            display: none;
        }
        
        .results.show {
            display: block;
        }
        
        .result-panel {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid;
        }
        
        .result-panel.critical {
            border-left-color: #dc3545;
            background: #fff5f5;
        }
        
        .result-panel.high {
            border-left-color: #fd7e14;
            background: #fff8f0;
        }
        
        .result-panel.medium {
            border-left-color: #ffc107;
            background: #fffbf0;
        }
        
        .result-panel.low {
            border-left-color: #28a745;
            background: #f0fff4;
        }
        
        .metrics {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .metric {
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #e9ecef;
        }
        
        .metric-value {
            font-size: 1.8em;
            font-weight: 700;
            color: #667eea;
        }
        
        .metric-label {
            font-size: 0.85em;
            color: #666;
            margin-top: 5px;
        }
        
        .impact-list {
            list-style: none;
        }
        
        .impact-item {
            background: white;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 4px;
            border-left: 4px solid;
        }
        
        .impact-item.critical {
            border-left-color: #dc3545;
        }
        
        .impact-item.high {
            border-left-color: #fd7e14;
        }
        
        .impact-item.medium {
            border-left-color: #ffc107;
        }
        
        .impact-item.low {
            border-left-color: #28a745;
        }
        
        .steps {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #e9ecef;
        }
        
        .step {
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }
        
        .step:last-child {
            border-bottom: none;
        }
        
        .step-number {
            display: inline-block;
            background: #667eea;
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            text-align: center;
            line-height: 32px;
            font-weight: 700;
            margin-right: 10px;
        }
        
        .step-action {
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        
        .step-desc {
            color: #666;
            font-size: 0.95em;
            margin-bottom: 8px;
        }
        
        .step-time {
            color: #999;
            font-size: 0.85em;
        }
        
        .warning {
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        
        .success {
            background: #d4edda;
            border: 1px solid #28a745;
            color: #155724;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        
        .error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .checkbox-group {
            margin-bottom: 15px;
        }
        
        .checkbox-group label {
            display: flex;
            align-items: center;
            cursor: pointer;
        }
        
        .checkbox-group input[type="checkbox"] {
            margin-right: 10px;
            width: 18px;
            height: 18px;
        }
        
        @media (max-width: 1024px) {
            .main {
                grid-template-columns: 1fr;
            }
            
            .metrics {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Guardrail</h1>
            <p>Security Change Impact Safety Agent</p>
        </div>
        
        <div class="main">
            <div class="panel">
                <h2>📝 Terraform Change</h2>
                <div class="checkbox-group">
                    <label>
                        <input type="checkbox" id="useDemo" checked>
                        Use Demo Scenario
                    </label>
                </div>
                <textarea id="tfDiff" placeholder="Paste Terraform diff here..." readonly></textarea>
            </div>
            
            <div class="panel">
                <h2>⚙️ Dependencies Config</h2>
                <textarea id="depConfig" placeholder="Paste JSON dependencies config..." readonly></textarea>
            </div>
            
            <div class="panel" style="grid-column: 1 / -1;">
                <div class="button-group">
                    <button class="btn-primary" onclick="analyze()">🔍 Analyze Change</button>
                    <button class="btn-secondary" onclick="loadDemo()">📋 Load Demo</button>
                    <button class="btn-secondary" onclick="clear()">🗑️ Clear</button>
                </div>
            </div>
            
            <div class="results" id="results">
                <div id="resultsContent"></div>
            </div>
        </div>
    </div>
    
    <script>
        // Load demo data on startup
        window.addEventListener('load', function() {
            if (document.getElementById('useDemo').checked) {
                loadDemo();
            }
        });
        
        // Toggle demo mode
        document.getElementById('useDemo').addEventListener('change', function() {
            const tfDiff = document.getElementById('tfDiff');
            const depConfig = document.getElementById('depConfig');
            
            if (this.checked) {
                loadDemo();
                tfDiff.readOnly = true;
                depConfig.readOnly = true;
            } else {
                tfDiff.value = '';
                depConfig.value = '';
                tfDiff.readOnly = false;
                depConfig.readOnly = false;
            }
        });
        
        function loadDemo() {
            fetch('/api/demo-data')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('tfDiff').value = data.terraform_diff;
                    document.getElementById('depConfig').value = JSON.stringify(data.dependency_config, null, 2);
                });
        }
        
        function analyze() {
            const useDemo = document.getElementById('useDemo').checked;
            const tfDiff = document.getElementById('tfDiff').value;
            const depConfig = document.getElementById('depConfig').value;
            
            if (!tfDiff.trim()) {
                showError('Please provide a Terraform diff');
                return;
            }
            
            if (!depConfig.trim()) {
                showError('Please provide dependency configuration');
                return;
            }
            
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>Analyzing change...</p></div>';
            resultsDiv.classList.add('show');
            
            fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    terraform_diff: tfDiff,
                    dependency_config: JSON.parse(depConfig)
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    showError(data.error);
                } else {
                    displayResults(data);
                }
            })
            .catch(e => showError('Analysis failed: ' + e.message));
        }
        
        function displayResults(report) {
            let html = '';
            
            // Summary
            const safeColor = report.safe_to_deploy ? 'success' : 'error';
            const safeText = report.safe_to_deploy ? '✅ YES' : '❌ NO';
            
            html += `
                <div class="result-panel ${report.overall_impact.toLowerCase()}">
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-value">${report.overall_impact}</div>
                            <div class="metric-label">Overall Impact</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${safeText}</div>
                            <div class="metric-label">Safe to Deploy</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${report.confidence}</div>
                            <div class="metric-label">Confidence</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${report.impacts.length}</div>
                            <div class="metric-label">Services Affected</div>
                        </div>
                    </div>
                </div>
            `;
            
            // Warnings
            if (report.warnings && report.warnings.length > 0) {
                html += '<div class="warning">';
                html += '<strong>⚠️ Warnings:</strong><br>';
                report.warnings.forEach(w => html += `• ${w}<br>`);
                html += '</div>';
            }
            
            // Summary
            html += `<div class="success"><strong>Summary:</strong> ${report.recommendation_summary}</div>`;
            
            // Impacts
            if (report.impacts.length > 0) {
                html += '<h3 style="margin: 20px 0 15px;">💥 Affected Services</h3>';
                html += '<ul class="impact-list">';
                report.impacts.forEach(impact => {
                    const level = impact.impact_level.toLowerCase();
                    html += `
                        <li class="impact-item ${level}">
                            <strong>${impact.service.name}</strong> 
                            <span style="color: #999;">(${impact.service.environment})</span><br>
                            <small>${impact.reason}</small>
                        </li>
                    `;
                });
                html += '</ul>';
            }
            
            // Recommendations
            if (report.recommended_steps.length > 0) {
                html += '<h3 style="margin: 20px 0 15px;">📋 Recommended Rollout Plan</h3>';
                html += '<div class="steps">';
                report.recommended_steps.forEach(step => {
                    html += `
                        <div class="step">
                            <span class="step-number">${step.order}</span>
                            <div class="step-action">${step.action.replace(/_/g, ' ').toUpperCase()}</div>
                            <div class="step-desc">${step.description}</div>
                            <div class="step-time">⏱️ ${step.estimated_time}</div>
                        </div>
                    `;
                });
                html += '</div>';
            }
            
            document.getElementById('resultsContent').innerHTML = html;
        }
        
        function showError(msg) {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = `<div class="error">❌ ${msg}</div>`;
            resultsDiv.classList.add('show');
        }
        
        function clear() {
            document.getElementById('results').classList.remove('show');
            if (!document.getElementById('useDemo').checked) {
                document.getElementById('tfDiff').value = '';
                document.getElementById('depConfig').value = '';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/demo-data')
def demo_data():
    """Serve demo data."""
    from pathlib import Path
    
    try:
        tf_path = Path('data/samples/terraform_change.diff')
        config_path = Path('data/samples/demo_dependencies.json')
        
        with open(tf_path) as f:
            terraform_diff = f.read()
        with open(config_path) as f:
            dependency_config = json.load(f)
        
        return jsonify({
            'terraform_diff': terraform_diff,
            'dependency_config': dependency_config
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Run security change analysis."""
    try:
        data = request.json
        terraform_diff = data.get('terraform_diff', '')
        dependency_config = data.get('dependency_config', {})
        
        if not terraform_diff.strip():
            return jsonify({'error': 'Terraform diff is required'}), 400
        if not dependency_config:
            return jsonify({'error': 'Dependency config is required'}), 400
        
        # Run analysis
        agent = GuardrailAgent()
        report = agent.analyze_terraform_change(
            change_id='web-analysis',
            terraform_diff=terraform_diff,
            dependency_config=dependency_config
        )
        
        # Format response
        return jsonify({
            'change_id': report.change_id,
            'overall_impact': str(report.overall_impact).replace('ImpactLevel.', ''),
            'confidence': str(report.confidence).replace('ConfidenceLevel.', ''),
            'safe_to_deploy': report.safe_to_deploy,
            'recommendation_summary': report.recommendation_summary,
            'warnings': report.warnings,
            'impacts': [
                {
                    'service': {
                        'name': i.service.service_name,
                        'environment': i.service.environment
                    },
                    'impact_level': str(i.impact_level).replace('ImpactLevel.', ''),
                    'reason': i.reason
                }
                for i in report.impacts
            ],
            'recommended_steps': [
                {
                    'order': s.order,
                    'action': s.action,
                    'description': s.description,
                    'estimated_time': s.estimated_time
                }
                for s in report.recommended_steps
            ]
        })
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}\n{traceback.format_exc()}'}), 500

if __name__ == '__main__':
    print("\n🛡️  Guardrail Web UI Starting...")
    print("📍 Open browser at: http://localhost:5000")
    print("🔴 Press Ctrl+C to stop\n")
    app.run(debug=False, port=5000)
