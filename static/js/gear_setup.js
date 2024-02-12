'use strict';

const forms = document.getElementsByClassName("default-form");
console.log(forms)
for (var form of forms){
    var shoeId = parseInt(form.id.substring(13))
    console.log(shoeId)
    console.log('handle form submit')
    form.addEventListener('submit', (evt) =>{
        evt.preventDefault();
        console.log('in event listener!')
        
        // iterate over checked checkboxes in this form to pull activity types from value field 
        var checkedActivityTypes = []
        var checkboxes = document.querySelectorAll('input[type=checkbox]:checked')
        for (var i = 0; i < checkboxes.length; i++) {
            checkboxes[i]
            checkedActivityTypes.push(checkboxes[i].value)
        }

        // Send data to server via fetch API
        fetch('/set-default-gear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                shoe_id: shoeId,
                activity_types: checkedActivityTypes
            })
        })
        .then((response) => response.json())
        .then(responseData => {
            if (responseData['success']) {

            } else {
                alert('Error updating defaults!');
            }
        })
        .catch(error => console.error('Error updating defaults:', error));
    });
}