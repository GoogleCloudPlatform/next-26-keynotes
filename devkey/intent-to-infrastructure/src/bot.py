#!/usr/bin/env python3
import sys
import os
import click

@click.group()
def cli():
    """Management script for the Chat Application (Bot)."""
    pass

@cli.command()
@click.option('--gemini/--no-gemini', default=False, help='Use Vertex AI Gemini API instead of vLLM.')
@click.option('--project', default=None, help='GCP Project ID for Vertex AI (default: gcloud config project).')
@click.option('--location', default='us-central1', help='GCP Region for Vertex AI (default: us-central1).')
@click.option('--model', default='gemini-2.5-flash', help='Gemini Model Name (default: gemini-2.5-flash).')
@click.option('--vllm-url', default='http://localhost:8000/v1/chat/completions', help='vLLM API URL.')
@click.option('--vllm-model', default='google-gemma-3-12b-it', help='vLLM Model Name.')
@click.option('--port', default=8080, help='Port to run the application on.')
@click.option('--debug/--no-debug', default=False, help='Run in debug mode.')
def run(gemini, project, location, model, vllm_url, vllm_model, port, debug):
    """Run the Chat Application locally."""
    
    # Set environment variables for app.py to read
    if gemini:
        os.environ['USE_GEMINI_API'] = 'true'
        
        # Resolve project ID
        final_project = project
        if not final_project:
            import subprocess
            try:
                result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True)
                final_project = result.stdout.strip()
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
            if final_project:
                click.secho(f"Using project from gcloud config: {final_project}", fg='green')

        if final_project:
            os.environ['VERTEX_PROJECT'] = final_project
        else:
            click.secho("Warning: --gemini is set but no GCP Project ID found. Set --project or run 'gcloud config set project <ID>'.", fg='yellow')
            
        os.environ['VERTEX_LOCATION'] = location
        os.environ['GEMINI_MODEL_NAME'] = model
    else:
        os.environ['USE_GEMINI_API'] = 'false'
        os.environ['VLLM_API_URL'] = vllm_url
        os.environ['MODEL_NAME'] = vllm_model

    # Import app AFTER setting env vars so it picks up the config
    try:
        from app import app
    except ImportError:
        # If run from root, we might need to help python find app.py if not using -m
        sys.path.append(os.path.dirname(__file__))
        from app import app

    click.secho(f"Starting app on port {port}...", fg='green')
    if gemini:
        click.secho(f"Mode: Vertex AI Gemini ({model}) [Project: {final_project}, Location: {location}]", fg='blue')
    else:
        click.secho(f"Mode: vLLM ({vllm_url})", fg='blue')
        
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    cli()
