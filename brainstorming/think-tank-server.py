#!/usr/bin/env python3
"""
Think Tank Session Server
Provides HTTP endpoints for reading and appending to the Think Tank session file.
Supports multiple session file formats (MD and JSON) from various directories.
"""

import os
import json
import glob
import re
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

SESSION_FILE = 'brainstorming/sessions/SESSION_01_initial_ideation.md'

# All locations and patterns for think tank sessions
# Adapted for Med-Gemma Hackathon
SESSION_SOURCES = [
    {
        'dir': 'brainstorming/sessions/',
        'pattern': 'SESSION_*.md',
        'format': 'md'
    },
    {
        'dir': 'brainstorming/sessions/',
        'pattern': '*.json',
        'format': 'json'
    }
]

class ThinkTankHandler(SimpleHTTPRequestHandler):
    """Custom handler for Think Tank session operations."""

    def end_headers(self):
        """Add CORS headers to allow frontend access."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle preflight CORS requests."""
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)

        # API endpoint to get session content
        if parsed_path.path == '/api/session':
            session_file = query_params.get('file', [SESSION_FILE])[0]
            self.send_session_content(session_file)
        # API endpoint to list all sessions
        elif parsed_path.path == '/api/sessions':
            self.list_sessions()
        else:
            # Serve static files (HTML, JS, etc.)
            super().do_GET()

    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)

        # API endpoint to append message
        if parsed_path.path == '/api/message':
            self.append_message()
        else:
            self.send_error(404, 'Endpoint not found')

    def json_to_markdown(self, data):
        """Convert a JSON think tank session to readable markdown format."""
        md_lines = []
        
        # Session metadata
        if 'session_metadata' in data:
            sm = data['session_metadata']
            md_lines.append(f"# {sm.get('title', 'Think Tank Session')}")
            md_lines.append("")
            if 'date' in sm:
                md_lines.append(f"**Date:** {sm['date']}")
            if 'participant' in sm:
                md_lines.append(f"**Participant:** {sm['participant']}")
            if 'format' in sm:
                md_lines.append(f"**Format:** {sm['format']}")
            if 'duration' in sm:
                md_lines.append(f"**Duration:** {sm['duration']}")
            if 'outcome' in sm:
                md_lines.append(f"**Outcome:** {sm['outcome']}")
            md_lines.append("")
            md_lines.append("---")
            md_lines.append("")
        
        # Expert panel
        if 'expert_panel' in data:
            md_lines.append("## Expert Panel")
            md_lines.append("")
            for expert in data['expert_panel']:
                md_lines.append(f"### {expert.get('name', 'Expert')} ({expert.get('role', 'Advisor')})")
                if 'key_contributions' in expert:
                    md_lines.append("")
                    md_lines.append("**Key Contributions:**")
                    for contrib in expert['key_contributions']:
                        md_lines.append(f"- {contrib}")
                md_lines.append("")
        
        # Session rounds
        if 'session_rounds' in data:
            md_lines.append("## Session Rounds")
            md_lines.append("")
            for round_data in data['session_rounds']:
                round_num = round_data.get('round', '?')
                title = round_data.get('title', 'Discussion')
                md_lines.append(f"### Round {round_num}: {title}")
                md_lines.append("")
                
                # Key questions
                if 'key_questions' in round_data:
                    md_lines.append("**Key Questions:**")
                    for q in round_data['key_questions']:
                        md_lines.append(f"- {q}")
                    md_lines.append("")
                
                # Critical insights
                if 'critical_insights' in round_data:
                    md_lines.append("**Critical Insights:**")
                    for insight in round_data['critical_insights']:
                        md_lines.append(f"- {insight}")
                    md_lines.append("")
                
                # Design directions
                if 'design_directions' in round_data:
                    md_lines.append("**Design Directions:**")
                    for dd in round_data['design_directions']:
                        name = dd.get('name', 'Option')
                        desc = dd.get('description', '')
                        md_lines.append(f"- **{name}**: {desc}")
                    md_lines.append("")
                
                # Consensus
                if 'consensus' in round_data:
                    md_lines.append(f"**Consensus:** {round_data['consensus']}")
                    md_lines.append("")
                
                # Generic key-value handling for other fields
                skip_fields = {'round', 'title', 'key_questions', 'critical_insights', 
                              'design_directions', 'consensus'}
                for key, value in round_data.items():
                    if key in skip_fields:
                        continue
                    if isinstance(value, str):
                        md_lines.append(f"**{key.replace('_', ' ').title()}:** {value}")
                    elif isinstance(value, list):
                        md_lines.append(f"**{key.replace('_', ' ').title()}:**")
                        for item in value:
                            if isinstance(item, dict):
                                md_lines.append(f"- {json.dumps(item)}")
                            else:
                                md_lines.append(f"- {item}")
                    md_lines.append("")
        
        # Final product vision
        if 'final_product_vision' in data:
            fpv = data['final_product_vision']
            md_lines.append("## Final Product Vision")
            md_lines.append("")
            if 'name' in fpv:
                md_lines.append(f"**Product:** {fpv['name']}")
            if 'tagline' in fpv:
                md_lines.append(f"**Tagline:** {fpv['tagline']}")
            md_lines.append("")
            if 'differentiators' in fpv:
                md_lines.append("**Differentiators:**")
                for d in fpv['differentiators']:
                    md_lines.append(f"- {d}")
            md_lines.append("")
        
        # Panel recommendations
        if 'panel_recommendations' in data:
            md_lines.append("## Panel Recommendations")
            md_lines.append("")
            pr = data['panel_recommendations']
            for key, value in pr.items():
                if isinstance(value, str):
                    md_lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
                elif isinstance(value, dict):
                    md_lines.append(f"**{key.replace('_', ' ').title()}:**")
                    for k, v in value.items():
                        md_lines.append(f"  - {k}: {v}")
            md_lines.append("")
        
        # Actionable next steps
        if 'actionable_next_steps' in data:
            md_lines.append("## Actionable Next Steps")
            md_lines.append("")
            for phase, steps in data['actionable_next_steps'].items():
                md_lines.append(f"### {phase.replace('_', ' ').title()}")
                for step in steps:
                    md_lines.append(f"- {step}")
                md_lines.append("")
        
        return '\n'.join(md_lines)

    def send_session_content(self, session_file=None):
        """Send the current session file content."""
        try:
            file_path = session_file or SESSION_FILE

            # Security: Ensure file is within allowed directories
            file_path = os.path.normpath(file_path)
            allowed_prefixes = ['docs/', 'project-management/']
            is_allowed = any(file_path.startswith(prefix) for prefix in allowed_prefixes)
            
            if not is_allowed:
                # Try to find it in docs first
                potential_path = f'docs/{os.path.basename(file_path)}'
                if os.path.exists(potential_path):
                    file_path = potential_path
                else:
                    self.send_error(403, f'Access denied: {file_path}')
                    return

            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Convert JSON to markdown for display
                if file_path.endswith('.json'):
                    try:
                        data = json.loads(content)
                        content = self.json_to_markdown(data)
                    except json.JSONDecodeError:
                        content = f"# Error\n\nCould not parse JSON file: {file_path}"

                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            else:
                self.send_error(404, f'Session file not found: {file_path}')
        except Exception as e:
            self.send_error(500, f'Error reading session: {str(e)}')

    def extract_session_metadata(self, file_path, file_format):
        """Extract metadata from a session file."""
        filename = os.path.basename(file_path)
        metadata = {
            'file': file_path,
            'filename': filename,
            'format': file_format,
            'date': 'Unknown',
            'display_name': filename.replace('_', ' ').replace('-', ' ').replace('.md', '').replace('.json', ''),
            'title': None,
            'session_type': 'General'
        }
        
        try:
            # Try to extract date from filename
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
            if date_match:
                year, month, day = date_match.groups()
                metadata['date'] = f"{year}-{month}-{day}"
                metadata['display_name'] = f"Think Tank Session - {month}/{day}/{year}"
            
            # Read file to extract more metadata
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_format == 'json':
                try:
                    data = json.loads(content)
                    # Extract from session_metadata if present
                    if 'session_metadata' in data:
                        sm = data['session_metadata']
                        if 'title' in sm:
                            metadata['title'] = sm['title']
                            metadata['display_name'] = sm['title']
                        if 'date' in sm:
                            metadata['date'] = sm['date']
                        if 'format' in sm:
                            metadata['session_type'] = sm.get('format', 'Stanford Think Tank')
                    # For phase sessions
                    if 'phase-0' in filename.lower() or 'foundation' in filename.lower():
                        metadata['session_type'] = 'Phase 0 Foundation'
                except json.JSONDecodeError:
                    pass
            else:  # markdown
                # Try to extract title from first heading
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                if title_match:
                    metadata['title'] = title_match.group(1).strip()
                    if metadata['date'] == 'Unknown':
                        metadata['display_name'] = metadata['title']
                
                # Try to extract date from content
                if metadata['date'] == 'Unknown':
                    # Match various date formats: **Date:** or **Date**: followed by date
                    content_date = re.search(r'\*\*Date[:\s]*\*\*[:\s]*([A-Za-z]+\s+\d+,?\s+\d{4}|\d{4}-\d{2}-\d{2})', content)
                    if content_date:
                        raw_date = content_date.group(1).strip()
                        # Try to parse various date formats
                        date_formats = [
                            '%B %d, %Y',      # December 18, 2025
                            '%B %d %Y',       # December 18 2025
                            '%Y-%m-%d',       # 2025-12-18
                            '%m/%d/%Y',       # 12/18/2025
                        ]
                        for fmt in date_formats:
                            try:
                                parsed = datetime.strptime(raw_date, fmt)
                                metadata['date'] = parsed.strftime('%Y-%m-%d')
                                break
                            except ValueError:
                                continue
                
                # Detect session type from content
                if 'Tech Stack' in content or 'tech-stack' in filename:
                    metadata['session_type'] = 'Tech Stack Validation'
                elif 'Auth' in content or 'UX' in content:
                    metadata['session_type'] = 'Auth & UX Review'
                elif 'Phase 0' in content or 'phase-0' in filename:
                    metadata['session_type'] = 'Phase 0 Foundation'
                elif 'Stanford' in content or 'stanford' in filename:
                    metadata['session_type'] = 'Stanford Think Tank'
        
        except Exception as e:
            print(f"Error extracting metadata from {file_path}: {e}")
        
        return metadata

    def list_sessions(self):
        """List all available Think Tank session files from all sources."""
        try:
            sessions = []
            seen_files = set()  # Avoid duplicates
            
            # Scan all session sources
            for source in SESSION_SOURCES:
                source_dir = source['dir']
                pattern = source['pattern']
                file_format = source['format']
                
                if not os.path.exists(source_dir):
                    continue
                
                full_pattern = os.path.join(source_dir, pattern)
                found_files = glob.glob(full_pattern)
                
                for file_path in found_files:
                    # Skip if already processed
                    abs_path = os.path.abspath(file_path)
                    if abs_path in seen_files:
                        continue
                    seen_files.add(abs_path)
                    
                    # Extract metadata
                    metadata = self.extract_session_metadata(file_path, file_format)
                    sessions.append(metadata)
            
            # Sort by date (most recent first), then by filename
            def sort_key(s):
                date = s.get('date', 'Unknown')
                if date == 'Unknown':
                    date = '0000-00-00'  # Put unknown dates at the end
                return (date, s.get('filename', ''))
            
            sessions.sort(key=sort_key, reverse=True)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = json.dumps(sessions, indent=2)
            self.wfile.write(response.encode('utf-8'))

        except Exception as e:
            self.send_error(500, f'Error listing sessions: {str(e)}')

    def append_message(self):
        """Append a new message to the session file."""
        try:
            # Read POST data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            message = data.get('message', '').strip()
            speaker = data.get('speaker', 'Jeremy Potts')
            role = data.get('role', 'CEO')

            if not message:
                self.send_error(400, 'Message is required')
                return

            # Format the message
            timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
            formatted_message = f"\n\n### {speaker} ({role})\n*{timestamp}*\n\n{message}\n"

            # Append to file
            with open(SESSION_FILE, 'a', encoding='utf-8') as f:
                f.write(formatted_message)

            # Send success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = json.dumps({
                'success': True,
                'message': 'Message appended successfully',
                'timestamp': timestamp
            })
            self.wfile.write(response.encode('utf-8'))

        except json.JSONDecodeError:
            self.send_error(400, 'Invalid JSON data')
        except Exception as e:
            self.send_error(500, f'Error appending message: {str(e)}')

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")


def run_server(port=8000):
    """Start the Think Tank session server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ThinkTankHandler)

    # Count available sessions
    session_count = 0
    for source in SESSION_SOURCES:
        if os.path.exists(source['dir']):
            pattern = os.path.join(source['dir'], source['pattern'])
            session_count += len(glob.glob(pattern))

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          KNOVA Quest Think Tank Session Server               ║
║            Session History Browser Enabled                   ║
╚══════════════════════════════════════════════════════════════╝

🚀 Server running at: http://localhost:{port}
📝 Active session: {SESSION_FILE}
📚 Sessions available: {session_count} (MD + JSON formats)
🌐 Open viewer: http://localhost:{port}/think-tank-viewer.html

Session sources:
  - docs/THINK_TANK_SESSION_*.md
  - project-management/think-tank-sessions/*.json
  - project-management/think-tank-sessions/*.md
  - docs/product/*think_tank*.json
  - docs/product/*think_tank*.md

Press Ctrl+C to stop the server.
""")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped.")
        httpd.server_close()
        print("""
╔══════════════════════════════════════════════════════════════╗
║  💡 TIP: To view sessions without the server running:        ║
╚══════════════════════════════════════════════════════════════╝

1. Generate the static viewer:
   python3 generate-static-viewer.py

2. Open the file directly in your browser:
   think-tank-viewer-static.html
""")


if __name__ == '__main__':
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    # Start server
    run_server(port=8000)
