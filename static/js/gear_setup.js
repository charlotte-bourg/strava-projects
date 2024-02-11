'use strict';

const forms = document.getElementsByClassName("default-form");
console.log(forms)
for (var form of forms){
    var shoeId = parseInt(form.id.substring(13))
    console.log(shoeId)
    console.log('handle form submit')
    form.addEventListener('submit', (evt) =>{
        console.log('in event listener!')
        // Array to store selected checkboxes
        var selectedCheckboxes = [];

        // Iterate over checkboxes in this form to find the selected ones
        var checkboxes = form.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(function(checkbox) {
            if (checkbox.checked) {
                // Extract activity type from checkbox ID
                var activityType = checkbox.id.split('-')[0]; // Extract activity type from first part of ID

                // Push activity type to selectedCheckboxes array
                selectedCheckboxes.push(activityType);
            }
        });

        // Send data to server via fetch API
        fetch('/set-default-gear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                shoe_id: shoeId,
                activity_types: selectedCheckboxes
            })
        })
        .then(response => {
            if (response['success']) {

            } else {
                alert('Error updating defaults!');
            }
        })
        .catch(error => console.error('Error updating defaults:', error));
    });
}