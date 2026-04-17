import os
import sys
import argparse
import subprocess
from huggingface_hub import snapshot_download, login

# Default model from your Terraform config
DEFAULT_MODEL = "google/gemma-3-12b-it"

def get_token(args_token):
    if args_token:
        return args_token
    
    token = os.environ.get("HUGGING_FACE_TOKEN")
    
    # Check secrets file
    secret_path = os.path.join("secrets", "huggingface.key")
    if not token and os.path.exists(secret_path):
        try:
            with open(secret_path, "r") as f:
                token = f.read().strip()
            print(f"Loaded token from {secret_path}")
        except Exception as e:
            print(f"Failed to read secrets file: {e}")

    if not token:
        print("\nPlease enter your Hugging Face Access Token.")
        print("You can find it here: https://huggingface.co/settings/tokens")
        token = input("Token: ").strip()
    
    return token

def upload_to_gcs(local_path, bucket_url, model_folder_name):
    # Ensure bucket URL ends with /
    if not bucket_url.endswith("/"):
        bucket_url += "/"
    
    dest = f"{bucket_url}{model_folder_name}/"
    print(f"\n🚀 Uploading to GCS: {dest}")
    
    command = ["gsutil", "-m", "cp", "-r", f"{local_path}/*", dest]
    
    try:
        subprocess.check_call(command)
        print(f"\n✅ Successfully uploaded to {dest}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Upload failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Download Gemma model and optional upload to GCS.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--bucket", help="GCS Bucket URL (e.g., gs://my-bucket) to upload to automatically.")
    parser.add_argument("--token", help="Hugging Face API Token")
    
    args = parser.parse_args()

    print("--- Gemma Model Downloader ---")
    
    model_name = args.model
    token = get_token(args.token)
    
    if not token:
        print("Error: Token is required.")
        return

    # Authenticate
    print(f"\nAuthenticating...")
    try:
        login(token=token, add_to_git_credential=False)
    except Exception as e:
        print(f"Authentication failed: {e}")
        return

    # Download
    folder_name = model_name.replace("/", "-")
    output_dir = os.path.join("gemma-model", folder_name)
    
    print(f"\nDownloading '{model_name}' to '{output_dir}'...")
    
    try:
        snapshot_download(
            repo_id=model_name,
            local_dir=output_dir,
            local_dir_use_symlinks=False,
            ignore_patterns=["*.pth", "*.msgpack", "*.h5", "*.ot"],
        )
        print(f"\n✅ Success! Model downloaded to {output_dir}")
        
        if args.bucket:
            upload_to_gcs(output_dir, args.bucket, folder_name)
        else:
            print("\nNext Step: Upload to your bucket with this command:")
            # Try to guess bucket from typical terraform output structure if not provided
            bucket_hint = "gs://<your-bucket-name>"
            print(f"gsutil -m cp -r {output_dir}/* {bucket_hint}/{folder_name}/")
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")

if __name__ == "__main__":
    main()
