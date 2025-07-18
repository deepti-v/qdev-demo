// Configuration - Replace with your API Gateway URL after deployment
const API_ENDPOINT = 'YOUR_API_GATEWAY_URL'; // e.g., 'https://abc123.execute-api.us-east-1.amazonaws.com'

// DOM Elements
const uploadForm = document.getElementById('upload-form');
const fileInput = document.getElementById('file-input');
const previewImage = document.getElementById('preview-image');
const uploadButton = document.getElementById('upload-button');
const uploadStatus = document.getElementById('upload-status');
const photoIdInput = document.getElementById('photo-id');
const getPhotoButton = document.getElementById('get-photo-button');
const photoResult = document.getElementById('photo-result');
const retrievedImage = document.getElementById('retrieved-image');
const photoInfo = document.getElementById('photo-info');

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Preview image when file is selected
    fileInput.addEventListener('change', previewFile);
    
    // Handle form submission for photo upload
    uploadForm.addEventListener('submit', uploadPhoto);
    
    // Handle get photo button click
    getPhotoButton.addEventListener('click', getPhoto);
});

/**
 * Preview the selected image file
 */
function previewFile() {
    const file = fileInput.files[0];
    if (!file) {
        previewImage.style.display = 'none';
        return;
    }
    
    if (!file.type.match('image.*')) {
        showStatus(uploadStatus, 'Please select an image file', 'error');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImage.src = e.target.result;
        previewImage.style.display = 'block';
    };
    
    reader.readAsDataURL(file);
}

/**
 * Upload a photo to the API
 * @param {Event} event - Form submit event
 */
async function uploadPhoto(event) {
    event.preventDefault();
    
    const file = fileInput.files[0];
    if (!file) {
        showStatus(uploadStatus, 'Please select a file', 'error');
        return;
    }
    
    // Show loading state
    uploadButton.disabled = true;
    showStatus(uploadStatus, 'Uploading photo...', '');
    
    try {
        // Read file as base64
        const base64Data = await readFileAsBase64(file);
        
        // Prepare request data
        const requestData = {
            photo: base64Data,
            fileName: file.name
        };
        
        // Send API request
        const response = await fetch(`${API_ENDPOINT}/photos`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Show success message with photo ID
            showStatus(
                uploadStatus, 
                `Photo uploaded successfully! Photo ID: ${data.photoId}`, 
                'success'
            );
            
            // Reset form
            uploadForm.reset();
            previewImage.style.display = 'none';
        } else {
            // Show error message
            showStatus(uploadStatus, `Error: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showStatus(uploadStatus, `Error: ${error.message}`, 'error');
    } finally {
        // Reset button state
        uploadButton.disabled = false;
    }
}

/**
 * Get a photo by ID from the API
 */
async function getPhoto() {
    const photoId = photoIdInput.value.trim();
    if (!photoId) {
        showStatus(photoResult, 'Please enter a photo ID', 'error');
        return;
    }
    
    // Show loading state
    getPhotoButton.disabled = true;
    showStatus(photoResult, 'Retrieving photo...', '');
    retrievedImage.style.display = 'none';
    photoInfo.innerHTML = '';
    
    try {
        // Send API request
        const response = await fetch(`${API_ENDPOINT}/photos/${photoId}`, {
            method: 'GET'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Display the photo
            retrievedImage.src = data.downloadUrl;
            retrievedImage.style.display = 'block';
            
            // Display photo information
            photoInfo.innerHTML = `
                <p><strong>Photo ID:</strong> ${data.photoId}</p>
                <p><strong>File Name:</strong> ${data.fileName}</p>
                <p><strong>Upload Date:</strong> ${new Date(data.uploadTimestamp).toLocaleString()}</p>
                <p><a href="${data.downloadUrl}" target="_blank" download="${data.fileName}">Download Photo</a></p>
            `;
            
            showStatus(photoResult, 'Photo retrieved successfully!', 'success');
        } else {
            // Show error message
            showStatus(photoResult, `Error: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Retrieval error:', error);
        showStatus(photoResult, `Error: ${error.message}`, 'error');
    } finally {
        // Reset button state
        getPhotoButton.disabled = false;
    }
}

/**
 * Read a file as base64
 * @param {File} file - The file to read
 * @returns {Promise<string>} - Base64 encoded file data
 */
function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            // Get the base64 string (remove data:image/jpeg;base64, prefix)
            const base64String = reader.result.split(',')[1];
            resolve(base64String);
        };
        reader.onerror = error => reject(error);
        reader.readAsDataURL(file);
    });
}

/**
 * Show a status message
 * @param {HTMLElement} element - The element to show the status in
 * @param {string} message - The message to display
 * @param {string} type - The type of message (success, error, or empty for neutral)
 */
function showStatus(element, message, type) {
    element.textContent = message;
    element.className = 'status';
    
    if (type) {
        element.classList.add(type);
    }
}