const API_KEY = 'oEKrrphwho1hBqucbhKJv6tvu6xwXIuam73sHnph';
const SEARCH_API_URL = 'https://un5f1h9s33.execute-api.us-east-1.amazonaws.com/prod/search';
const UPLOAD_API_URL = 'https://un5f1h9s33.execute-api.us-east-1.amazonaws.com/prod/photos';
var apigClient = apigClientFactory.newClient({
  apiKey: 'oEKrrphwho1hBqucbhKJv6tvu6xwXIuam73sHnph'
});

// Function to search photos
async function searchPhotos() {
  const query = document.getElementById('searchQuery').value;
  if (!query) {
    alert('Please enter a search query!');
    return;
  }

  try {
    const response = await fetch(`${SEARCH_API_URL}?q=${query}`, {
      headers: {
        'x-api-key': API_KEY,
      },
    });

    const data = await response.json(); // Parse the Lambda response
    displayResults(data); // Pass the parsed response to the display function
  } catch (error) {
    console.error('Error searching photos:', error);
    alert('An error occurred while searching.');
  }
}

// Function to display search results
function displayResults(response) {
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = ''; // Clear previous results

  // Parse the body to extract photo metadata
  const photos = JSON.parse(response.body); // Response body is a JSON string

  if (photos.length === 0) {
    resultsDiv.innerHTML = '<p>No photos found.</p>';
    return;
  }

  photos.forEach((photo) => {
    // Construct the S3 URL
    const imageUrl = `https://${photo.bucket}.s3.amazonaws.com/${photo.objectKey}`;
    
    // Create an image element
    const img = document.createElement('img');
    img.src = imageUrl;
    img.alt = photo.labels.join(', ');
    img.style.maxWidth = '200px'; // Optional styling for the image

    // Create a label list
    // const labelDiv = document.createElement('div');
    // labelDiv.innerHTML = <strong>Labels:</strong> ${photo.labels.join(', ')};

    // Append the image and labels to the results
    const container = document.createElement('div');
    container.appendChild(img);
    // container.appendChild(labelDiv);
    resultsDiv.appendChild(container);
  });
}

// Function to upload a photo
async function uploadPhoto() {
  const fileInput = document.getElementById('photo');
  const customLabelsInput = document.getElementById('customLabels');
  const file = fileInput.files[0];
  const customLabels = customLabelsInput.value;

  if (!file) {
    alert('Please select a photo to upload!');
    return;
  }

  const uploadUrl = `${UPLOAD_API_URL}/${file.name}`;

  try {
    const response = await fetch(uploadUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': file.type,
        'x-amz-meta-customLabels': customLabels,
        'x-api-key': API_KEY,
      },
      body: file,
    });

    if (response.ok) {
      alert('Photo uploaded successfully!');
    } else {
      alert('Failed to upload photo.');
    }
  } catch (error) {
    console.error('Error uploading photo:', error);
    alert('An error occurred while uploading.');
  }
}