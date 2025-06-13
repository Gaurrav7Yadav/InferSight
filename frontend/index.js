document.getElementById('upload-form').addEventListener('submit', async (e) => {
  e.preventDefault();  // Prevent form submission, handle via JavaScript

  // Prepare the form data with the uploaded document
  const formData = new FormData();
  const fileInput = document.getElementById('document');
  formData.append('file', fileInput.files[0]);

  try {
      // Make a POST request to the FastAPI server
      const response = await fetch('http://127.0.0.1:8000/extract-fields', {
          method: 'POST',
          body: formData
      });

      // If the response is not successful, throw an error
      if (!response.ok) {
          throw new Error('Failed to extract fields from the document.');
      }

      // Parse the JSON response from the server
      const data = await response.json();

      // If data is missing or error, show a message
      if (data.error) {
          alert('Error: ' + data.error);
          return;
      }

      // Update form fields with extracted data
      document.getElementById('docNumber').value = data["Document Number"] || "";
      document.getElementById('docDate').value = data["Document Date"] || "";
      document.getElementById('validity').value = data["Validity Till Date"] || "";
      document.getElementById('currency').value = data["Document Currency"] || "";
      document.getElementById('value').value = data["Document Value (Amount)"] || "";
      document.getElementById('subtype').value = data["Document Subtype"] || "";

      // Show the result fields div
      document.getElementById('result-fields').style.display = 'block';

  } catch (error) {
      // Handle any errors during the fetch or data extraction process
      console.error(error);
      alert('An error occurred while processing the document.');
  }
});
