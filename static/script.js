document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const progressContainer = document.getElementById('progress-container');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const contentContainer = document.getElementById('content-container');
    const notesContent = document.getElementById('notes-content');
    const downloadContainer = document.getElementById('download-container');

    // Debug: Log which elements are found or missing
    console.log('Form:', form);
    console.log('File Input:', fileInput);
    console.log('Progress Container:', progressContainer);
    console.log('Progress Fill:', progressFill);
    console.log('Progress Text:', progressText);
    console.log('Content Container:', contentContainer);
    console.log('Notes Content:', notesContent);
    console.log('Download Container:', downloadContainer);

    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Form submitted');
            if (fileInput && fileInput.files.length > 0) {
                console.log('File selected:', fileInput.files[0].name);
                const formData = new FormData(form);
                
                fetch('/', {
                    method: 'POST',
                    body: formData
                }).then(response => {
                    console.log('Response status:', response.status);
                    if (!response.ok) {
                        return response.json().then(err => { throw err; });
                    }
                    return response.json();
                }).then(data => {
                    console.log('Upload response:', data);
                    if (form) form.classList.add('hidden');
                    if (progressContainer) progressContainer.classList.remove('hidden');
                    
                    const eventSource = new EventSource("/process");
                    
                    eventSource.onmessage = function(event) {
                        console.log('SSE message received:', event.data);
                        const data = JSON.parse(event.data);
                        if (data.progress && progressFill && progressText) {
                            const progress = Math.round(data.progress);
                            progressFill.style.width = `${progress}%`;
                            progressText.textContent = `${progress}%`;
                        }
                        if (data.complete) {
                            console.log('Processing complete');
                            eventSource.close();
                            fetch("/result")
                                .then(response => response.json())
                                .then(data => {
                                    console.log('Result received');
                                    if (progressContainer) progressContainer.classList.add('hidden');
                                    if (contentContainer) contentContainer.classList.remove('hidden');
                                    if (notesContent) notesContent.innerHTML = data.content;
                                    if (downloadContainer) downloadContainer.classList.remove('hidden');
                                })
                                .catch(error => {
                                    console.error('Error fetching result:', error);
                                    alert('An error occurred while fetching the results.');
                                });
                        }
                        if (data.error) {
                            console.error('SSE error:', data.error);
                            alert('An error occurred: ' + data.error);
                            eventSource.close();
                        }
                    };
                }).catch(error => {
                    console.error('Fetch error:', error);
                    alert('An error occurred while uploading the file: ' + (error.error || error.message || 'Unknown error'));
                });
            } else {
                console.log('No file selected');
                alert('Please select a file before generating notes.');
            }
        });
    } else {
        console.error('Form not found');
    }

    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0].name;
            console.log('File input changed:', fileName);
            const fileLabel = fileInput.nextElementSibling;
            if (fileLabel) {
                const span = fileLabel.querySelector('span');
                if (span) span.textContent = fileName;
            }
        });
    } else {
        console.error('File input not found');
    }
});
