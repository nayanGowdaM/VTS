
function submitForm() {
  // Get values from input fields
    const vehicleId = document.getElementById('vehicle_input').value;
    const date = document.getElementById('date_input').value;

    // Reset error message
    document.getElementById('errorMessage').innerText = '';

    // Fetch location data from Flask backend
    fetch('/get_locations', {
        method: 'POST',
        headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
        'vehicle_id': vehicleId,
        'date': date,
        }),
    })
    .then(response => {
        if (response.ok) {
            // If successful, open map.html in a new tab
            window.open(`/map?vehicle_id=${vehicleId}&date=${date}`, '_blank');
        } else {
            // If table does not exist, show error message
            document.getElementById('errorMessage').innerText = 'Table does not exist.';
        }
        })
        .catch(error => {
        console.error('Error fetching location data:', error);
        document.getElementById('errorMessage').innerText = 'Error fetching location data.';
    });

  return false; // Prevent the form from submitting
}