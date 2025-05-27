"""Example: Upload documents to Synapse"""
import os
import requests
from pathlib import Path

# Configuration
SYNAPSE_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY", "your-api-key")

# Headers
headers = {
    "Authorization": f"Bearer {API_KEY}"
}


def upload_file(filepath: str):
    """Upload a single file"""
    with open(filepath, 'rb') as f:
        files = {'files': (Path(filepath).name, f)}
        response = requests.post(
            f"{SYNAPSE_URL}/api/documents/upload",
            headers=headers,
            files=files
        )
    
    if response.status_code == 200:
        print(f"✅ Uploaded: {filepath}")
    else:
        print(f"❌ Failed to upload {filepath}: {response.text}")
    
    return response.json()


def upload_directory(directory: str):
    """Upload all documents from a directory"""
    path = Path(directory)
    files_to_upload = []
    
    # Supported extensions
    extensions = {'.txt', '.md', '.pdf', '.docx', '.html', '.json', '.py', '.js', '.ts'}
    
    for file in path.rglob('*'):
        if file.is_file() and file.suffix.lower() in extensions:
            files_to_upload.append(str(file))
    
    print(f"Found {len(files_to_upload)} files to upload")
    
    for filepath in files_to_upload:
        upload_file(filepath)


def search_documents(query: str, use_memory: bool = True):
    """Search uploaded documents"""
    response = requests.post(
        f"{SYNAPSE_URL}/api/documents/search",
        headers=headers,
        json={
            "query": query,
            "limit": 5,
            "use_memory": use_memory
        }
    )
    
    if response.status_code == 200:
        results = response.json()
        print(f"\nSearch results for '{query}':")
        print(f"Found {results['count']} results")
        
        for i, result in enumerate(results.get('results', [])):
            print(f"\n{i+1}. {result.get('title', 'Untitled')}")
            print(f"   Score: {result.get('score', 0):.3f}")
            print(f"   Preview: {result.get('preview', '')[:100]}...")
    else:
        print(f"Search failed: {response.text}")


if __name__ == "__main__":
    # Example 1: Upload a single file
    # upload_file("docs/README.md")
    
    # Example 2: Upload entire directory
    # upload_directory("docs/")
    
    # Example 3: Search documents
    # search_documents("How to deploy Synapse?")
    
    print("Update this script with your file paths and run!")