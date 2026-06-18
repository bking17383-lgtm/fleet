import os
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)
UPLOAD_FOLDER = os.path.expanduser("~/uploaded_files")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Puppy File Server & Uploader</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col justify-center items-center p-4">
    <div class="w-full max-w-lg bg-slate-800 p-8 rounded-2xl shadow-xl border border-slate-700">
        <h1 class="text-2xl font-bold text-center text-blue-400 mb-2">Puppy File Server</h1>
        <p class="text-xs text-slate-400 text-center mb-6">Upload files directly to Puppy's local storage</p>
        
        <form id="upload-form" class="space-y-6">
            <div id="drop-zone" class="border-2 border-dashed border-slate-600 hover:border-blue-500 rounded-xl p-8 text-center cursor-pointer transition-colors bg-slate-850">
                <svg class="mx-auto h-12 w-12 text-slate-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p class="text-sm font-medium">Click to select or drag & drop files</p>
                <p class="text-xs text-slate-500 mt-1">Supports any file type</p>
                <input type="file" id="file-input" name="files" multiple class="hidden">
            </div>

            <!-- Progress Bar -->
            <div id="progress-container" class="hidden">
                <div class="flex justify-between text-xs mb-1 text-slate-400">
                    <span id="progress-status">Uploading...</span>
                    <span id="progress-percent">0%</span>
                </div>
                <div class="w-full bg-slate-700 h-2 rounded-full overflow-hidden">
                    <div id="progress-bar" class="bg-blue-500 h-full w-0 transition-all duration-150"></div>
                </div>
            </div>

            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 rounded-xl transition-all shadow-lg shadow-blue-900/30">
                Upload Files
            </button>
        </form>

        <div id="result" class="mt-6 text-center text-sm font-medium hidden"></div>

        <div class="mt-8 border-t border-slate-700 pt-6">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Puppy Storage Status</h2>
            <div class="flex justify-between text-xs text-slate-300">
                <span>Local Upload Path:</span>
                <span class="font-mono text-slate-400">~/uploaded_files</span>
            </div>
        </div>
    </div>

    <script>
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        const form = document.getElementById('upload-form');
        const progressContainer = document.getElementById('progress-container');
        const progressBar = document.getElementById('progress-bar');
        const progressPercent = document.getElementById('progress-percent');
        const progressStatus = document.getElementById('progress-status');
        const resultDiv = document.getElementById('result');

        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('border-blue-500', 'bg-blue-950/20');
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('border-blue-500', 'bg-blue-950/20');
            });
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            fileInput.files = e.dataTransfer.files;
            updateDropZoneLabel();
        });

        fileInput.addEventListener('change', updateDropZoneLabel);

        function updateDropZoneLabel() {
            const count = fileInput.files.length;
            if (count > 0) {
                dropZone.querySelector('p').textContent = `${count} file(s) selected`;
            } else {
                dropZone.querySelector('p').textContent = 'Click to select or drag & drop files';
            }
        }

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (fileInput.files.length === 0) {
                alert('Please select at least one file first.');
                return;
            }

            const formData = new FormData();
            for (let i = 0; i < fileInput.files.length; i++) {
                formData.append('files', fileInput.files[i]);
            }

            progressContainer.classList.remove('hidden');
            resultDiv.classList.add('hidden');
            progressBar.style.width = '0%';
            progressPercent.textContent = '0%';
            progressStatus.textContent = 'Uploading...';

            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload', true);

            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = `${percent}%`;
                    progressPercent.textContent = `${percent}%`;
                }
            });

            xhr.onload = function () {
                progressContainer.classList.add('hidden');
                resultDiv.classList.remove('hidden');
                
                if (xhr.status === 200) {
                    const resp = JSON.parse(xhr.responseText);
                    resultDiv.className = 'mt-6 text-center text-sm font-medium text-emerald-400';
                    resultDiv.textContent = resp.message;
                    form.reset();
                    updateDropZoneLabel();
                } else {
                    resultDiv.className = 'mt-6 text-center text-sm font-medium text-rose-400';
                    resultDiv.textContent = 'Upload failed. Please try again.';
                }
            };

            xhr.onerror = function () {
                progressContainer.classList.add('hidden');
                resultDiv.classList.remove('hidden');
                resultDiv.className = 'mt-6 text-center text-sm font-medium text-rose-400';
                resultDiv.textContent = 'A network error occurred.';
            };

            xhr.send(formData);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    
    files = request.files.getlist('files')
    uploaded_count = 0
    
    for file in files:
        if file.filename == '':
            continue
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        uploaded_count += 1
        
    if uploaded_count > 0:
        return jsonify({
            "status": "success", 
            "message": f"Successfully uploaded {uploaded_count} file(s) to Puppylocal directory!"
        }), 200
    else:
        return jsonify({"status": "error", "message": "No valid files uploaded"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002, debug=False)
