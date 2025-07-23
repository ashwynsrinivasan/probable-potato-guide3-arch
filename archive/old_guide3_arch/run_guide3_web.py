#!/usr/bin/env python3
"""
Web-based alternative to Guide3GUI for macOS compatibility
This provides a web interface when Tkinter fails on macOS.
"""

import os
import sys
import webbrowser
import threading
import time

# Set matplotlib to use non-interactive backend to prevent threading issues
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from flask import Flask, render_template_string, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not available. Installing...")
    os.system("pip3 install flask")

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Guide3 Web Interface</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background: #fafafa; }
        .button { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }
        .button:hover { background: #0056b3; }
        .input-group { margin: 15px 0; }
        label { display: inline-block; width: 200px; font-weight: bold; }
        input, select { padding: 8px; width: 200px; border: 1px solid #ddd; border-radius: 4px; }
        .result { background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #007bff; }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        h2 { color: #555; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Guide3 Web Interface</h1>
        <p><em>Alternative to Tkinter GUI for macOS compatibility</em></p>
        
        <div class="section">
            <h2>HPSOA Analysis</h2>
            <p>Generate comprehensive HPSOA performance plots and analysis.</p>
            <button class="button" onclick="runHPSOA()">Generate HPSOA Plot</button>
            <div id="hpsoa-result" class="result" style="display:none;"></div>
        </div>
        
        <div class="section">
            <h2>Guide3 Calculations</h2>
            <p>Calculate link requirements per lambda with detailed loss analysis.</p>
            <div class="input-group">
                <label>Number of Wavelengths:</label>
                <input type="number" id="num_wavelengths" value="1" min="1" max="100">
            </div>
            <div class="input-group">
                <label>Target Pout (dBm):</label>
                <input type="number" id="target_pout" value="-3.3" step="0.1">
            </div>
            <div class="input-group">
                <label>SOA Penalty (dB):</label>
                <input type="number" id="soa_penalty" value="2.0" step="0.1">
            </div>
            <button class="button" onclick="runGuide3()">Calculate Guide3</button>
            <div id="guide3-result" class="result" style="display:none;"></div>
        </div>
        
        <div class="section">
            <h2>Guide3A Analysis</h2>
            <p>Analyze PIC architectures with comprehensive performance metrics.</p>
            <div class="input-group">
                <label>PIC Architecture:</label>
                <select id="pic_architecture">
                    <option value="psr">PSR</option>
                    <option value="pol_control">Pol Control</option>
                    <option value="psrless">PSRless</option>
                </select>
            </div>
            <div class="input-group">
                <label>Fiber Input Type:</label>
                <select id="fiber_input_type">
                    <option value="pm">PM</option>
                    <option value="sm">SM</option>
                </select>
            </div>
            <div class="input-group">
                <label>Number of Fibers:</label>
                <input type="number" id="num_fibers" value="40" min="1" max="100">
            </div>
            <button class="button" onclick="runGuide3A()">Calculate Guide3A</button>
            <div id="guide3a-result" class="result" style="display:none;"></div>
        </div>
    </div>

    <script>
        function runHPSOA() {
            document.getElementById('hpsoa-result').innerHTML = 'Processing...';
            document.getElementById('hpsoa-result').style.display = 'block';
            
            fetch('/api/hpsoa', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('hpsoa-result').innerHTML = 
                            '<strong>✅ Success!</strong><br>' +
                            '📊 Plot saved to: ' + data.plot_path + '<br>' +
                            '🌡️ Temperature Range: ' + data.temp_range + '<br>' +
                            '⚡ Current Range: ' + data.current_range + '<br>' +
                            '📏 Wavelength Range: ' + data.wavelength_range;
                    } else {
                        document.getElementById('hpsoa-result').innerHTML = '❌ Error: ' + data.error;
                    }
                })
                .catch(error => {
                    document.getElementById('hpsoa-result').innerHTML = '❌ Error: ' + error;
                });
        }
        
        function runGuide3() {
            const data = {
                num_wavelengths: parseInt(document.getElementById('num_wavelengths').value),
                target_pout: parseFloat(document.getElementById('target_pout').value),
                soa_penalty: parseFloat(document.getElementById('soa_penalty').value)
            };
            
            document.getElementById('guide3-result').innerHTML = 'Processing...';
            document.getElementById('guide3-result').style.display = 'block';
            
            fetch('/api/guide3', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('guide3-result').innerHTML = 
                        '<strong>✅ Results:</strong><br>' +
                        '📊 Total Requirement (Median): ' + data.median_total + ' dB<br>' +
                        '📊 Total Requirement (3σ): ' + data.sigma_total + ' dB<br>' +
                        '📉 Total Loss: ' + data.total_loss + ' dB';
                } else {
                    document.getElementById('guide3-result').innerHTML = '❌ Error: ' + data.error;
                }
            })
            .catch(error => {
                document.getElementById('guide3-result').innerHTML = '❌ Error: ' + error;
            });
        }
        
        function runGuide3A() {
            const data = {
                pic_architecture: document.getElementById('pic_architecture').value,
                fiber_input_type: document.getElementById('fiber_input_type').value,
                num_fibers: parseInt(document.getElementById('num_fibers').value)
            };
            
            document.getElementById('guide3a-result').innerHTML = 'Processing...';
            document.getElementById('guide3a-result').style.display = 'block';
            
            fetch('/api/guide3a', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('guide3a-result').innerHTML = 
                        '<strong>✅ Results:</strong><br>' +
                        '📉 Total Loss: ' + data.total_loss + ' dB<br>' +
                        '🏗️ Architecture: ' + data.architecture + '<br>' +
                        '🔧 Component Count: ' + data.component_count;
                } else {
                    document.getElementById('guide3a-result').innerHTML = '❌ Error: ' + data.error;
                }
            })
            .catch(error => {
                document.getElementById('guide3a-result').innerHTML = '❌ Error: ' + error;
            });
        }
    </script>
</body>
</html>
"""

app = Flask(__name__)

# Add CORS headers to prevent access issues
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/hpsoa', methods=['POST'])
def api_hpsoa():
    try:
        from src.models import HPSOA
        hpsoa = HPSOA()
        fig, axes = hpsoa.plot_performance_data()
        
        return jsonify({
            'success': True,
            'plot_path': 'data/plots/models/hpsoa.png',
            'temp_range': '35°C - 80°C',
            'current_range': '0.18A - 0.28A',
            'wavelength_range': '1304nm - 1318nm'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/guide3', methods=['POST'])
def api_guide3():
    try:
        data = request.get_json()
        from architecture_datasoa import Guide3
        
        guide3 = Guide3(
            target_pout=data['target_pout'],
            soa_penalty=data['soa_penalty']
        )
        
        result = guide3.calculate_target_pout_all_wavelengths(data['num_wavelengths'])
        loss_breakdown = guide3.get_loss_breakdown()
        
        return jsonify({
            'success': True,
            'median_total': f"{result['median_case']['total_target_pout_db']:.1f}",
            'sigma_total': f"{result['sigma_case']['total_target_pout_db']:.1f}",
            'total_loss': f"{loss_breakdown['total_loss']:.2f}"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/guide3a', methods=['POST'])
def api_guide3a():
    try:
        data = request.get_json()
        from architecture_datasoa import Guide3A
        
        guide3a = Guide3A(
            pic_architecture=data['pic_architecture'],
            fiber_input_type=data['fiber_input_type'],
            num_fibers=data['num_fibers']
        )
        
        total_loss = guide3a.get_total_loss()
        component_count = guide3a.get_component_count()
        
        return jsonify({
            'success': True,
            'total_loss': f"{total_loss:.2f}",
            'architecture': data['pic_architecture'].upper(),
            'component_count': component_count['total_components']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def open_browser():
    """Open browser after a short delay"""
    time.sleep(2.0)  # Increased delay
    webbrowser.open('http://localhost:8080')

if __name__ == '__main__':
    if not FLASK_AVAILABLE:
        print("Installing Flask...")
        os.system("pip3 install flask")
        from flask import Flask, render_template_string, request, jsonify
        app = Flask(__name__)
    
    print("Starting Guide3 Web Interface...")
    print("Server will be available at: http://localhost:8080")
    print("Opening browser automatically...")
    
    # Start browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run the Flask app with proper configuration
    app.run(debug=False, host='0.0.0.0', port=8080, threaded=True) 