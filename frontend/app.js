const API_KEY = 'oEKrrphwho1hBqucbhKJv6tvu6xwXIuam73sHnph';
const SEARCH_API_URL = 'https://un5f1h9s33.execute-api.us-east-1.amazonaws.com/prod/search';
const UPLOAD_API_URL = 'https://un5f1h9s33.execute-api.us-east-1.amazonaws.com/prod/photos';
var apigClient = apigClientFactory.newClient({
  apiKey: 'oEKrrphwho1hBqucbhKJv6tvu6xwXIuam73sHnph'
});

async function searchPhotos() {
  const query = document.getElementById('searchQuery').value;
  if (!query) {
    alert('Please enter a search query!');
    return;
  }

  const params = {
    q: query
  };
  const body = {};
  const additionalParams = {
    headers: {
      'x-api-key': API_KEY
    }
  };

  try {
    const result = await apigClient.searchGet(params, body, additionalParams);
    const data = result.data; // The response data
    displayResults(data); // Pass the data to the display function
  } catch (error) {
    console.error('Error searching photos:', error);
    alert('An error occurred while searching.');
  }
}

// Function to display search results
function displayResults(response) {
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = ''; // Clear previous results

  if (response.body) {
      try {
        photos = JSON.parse(response.body); // Parse the JSON string into an object
      } catch (e) {
        console.error('Error parsing response body:', e);
        resultsDiv.innerHTML = '<p>Error parsing response.</p>';
        return;
      }
    } else {
      console.error('Response body is missing');
      resultsDiv.innerHTML = '<p>Error: Response body is missing.</p>';
      return;
    }

    // Check if photos is an array
    if (!Array.isArray(photos) || photos.length === 0) {
      resultsDiv.innerHTML = '<p>No photos found.</p>';
      return;
    }

    photos.forEach((photo) => {
      // Construct the S3 URL
      const imageUrl = `https://${photo.bucket}.s3.amazonaws.com/${photo.objectKey}`;

      // Create an image element
      const img = document.createElement('img');
      img.src = imageUrl;
      img.alt = photo.labels ? photo.labels.join(', ') : '';
      img.style.maxWidth = '200px'; // Optional styling for the image

      // Append the image to the results
      const container = document.createElement('div');
      container.appendChild(img);
      resultsDiv.appendChild(container);
    });
  }

  async function uploadPhoto() {
    const fileInput = document.getElementById('photo');
    const customLabelsInput = document.getElementById('customLabels');
    const file = fileInput.files[0];
    const customLabels = customLabelsInput.value;

    if (!file) {
      alert('Please select a photo to upload!');
      return;
    }

    const params = {
      'x-amz-meta-customLabels': customLabels,
      'objects': file.name // The path parameter {objects} is the file name
    };
    const body = file; // The binary file data
	console.log(file)
    const additionalParams = {
      headers: {
        'Content-Type': file.type,
        'x-amz-meta-customLabels': customLabels,
        'x-api-key': API_KEY
      }
    };

    try {
      const result = await apigClient.photosObjectsPut(params, body, additionalParams);
      if (result.status === 200 || result.status === 201) {
        alert('Photo uploaded successfully!');
      } else {
        alert('Failed to upload photo.');
      }
    } catch (error) {
      console.error('Error uploading photo:', error);
      alert('An error occurred while uploading.');
    }
  }