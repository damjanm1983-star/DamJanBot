#!/usr/bin/env python3
"""
Simple webhook server to receive TradingView alerts
Logs all incoming alerts for testing
"""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WebhookServer")

class WebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info(format % args)
    
    def do_POST(self):
        if self.path == '/webhook':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                alert_data = json.loads(post_data.decode('utf-8'))
                logger.info("=" * 60)
                logger.info("📨 ALERT RECEIVED")
                logger.info("=" * 60)
                logger.info(f"Action: {alert_data.get('action', 'unknown')}")
                logger.info(f"Symbol: {alert_data.get('symbol', 'unknown')}")
                logger.info(f"Price: {alert_data.get('price', 'unknown')}")
                logger.info(f"Full payload: {json.dumps(alert_data, indent=2)}")
                logger.info("=" * 60)
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "received"}).encode())
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Webhook server is running. Send POST to /webhook\n')

def run_server(port=8000):
    server = HTTPServer(('0.0.0.0', port), WebhookHandler)
    logger.info(f"🚀 Webhook server starting on port {port}")
    logger.info(f"📡 Ready to receive alerts at: http://5.9.248.66/webhook")
    logger.info("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n🛑 Server stopped")

if __name__ == "__main__":
    run_server()
