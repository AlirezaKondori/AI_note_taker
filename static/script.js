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
            if (fileInput && fileInput.files.length > 0) {
                const formData = new FormData(form);
                
                fetch('/', {
                    method: 'POST',
                    body: formData,
                    credentials: 'same-origin',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                }).then(response => {
                    if (response.redirected) {
                        // If the response is a redirect, it's likely due to authentication
                        window.location.href = response.url;
                        throw new Error('Authentication required');
                    }
                    if (!response.ok) {
                        return response.json().then(err => { throw err; });
                    }
                    return response.json();
                }).then(data => {
                    form.classList.add('hidden');
                    progressContainer.classList.remove('hidden');
                    
                    const eventSource = new EventSource("/process");
                    
                    eventSource.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        if (data.progress) {
                            const progress = Math.round(data.progress);
                            progressFill.style.width = `${progress}%`;
                            progressText.textContent = `${progress}%`;
                        }
                        if (data.complete) {
                            eventSource.close();
                            fetch("/result")
                                .then(response => {
                                    if (!response.ok) {
                                        return response.json().then(err => { throw err; });
                                    }
                                    return response.json();
                                })
                                .then(data => {
                                    progressContainer.classList.add('hidden');
                                    contentContainer.classList.remove('hidden');
                                    notesContent.innerHTML = data.content;
                                    downloadContainer.classList.remove('hidden');
                                })
                                .catch(error => {
                                    console.error('Error fetching results:', error);  // Log the error to the console
                                    alert('An error occurred while fetching the results: ' + (error.error || error.message || 'Unknown error'));
                                });
                        }
                        if (data.error) {
                            alert('An error occurred: ' + data.error);
                            eventSource.close();
                        }
                    };

                    eventSource.onerror = function(error) {
                        console.error('EventSource failed:', error);
                        alert('Connection to server lost. Please refresh the page and try again.');
                        eventSource.close();
                    };
                }).catch(error => {
                    console.error('Error:', error);
                    if (error.message === 'Authentication required') {
                        alert('Your session has expired. Please log in again.');
                    } else {
                        alert('An error occurred while uploading the file: ' + (error.error || error.message || 'Unknown error'));
                    }
                });
            } else {
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
