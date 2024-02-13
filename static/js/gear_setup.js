'use strict';

const forms = document.getElementsByClassName("default-form");
console.log(forms)
for (const form of forms){
    form.addEventListener('submit', (evt) =>{
        evt.preventDefault();
        console.log('in event listener!');
        const shoeId = parseInt(form.id.split('-').pop());
        // iterate over checked checkboxes in this form to pull activity types from value field 
        var checkedActivityTypes = [];
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
                const addedAssociations = responseData.addedAssociations;
                for (const shoeId in addedAssociations) {
                    if (addedAssociations.hasOwnProperty(shoeId)) {
                        const sportType = addedAssociations[shoeId];
                        console.log(`Shoe with ID ${shoeId} is associated with ${sportType}`);
                        // Do whatever you need with this information
                        const tdElement = document.getElementById(shoeId);
                        if (tdElement) {
                            tdElement.innerHTML += sportType;
                        }
                    }
                }
                const deletedAssociations = responseData.deletedAssociations;
                for (const shoeId in deletedAssociations) {
                    if (deletedAssociations.hasOwnProperty(shoeId)) {
                        const sportType = deletedAssociations[shoeId];
                        console.log(`Association of shoe with ID ${shoeId} with ${sportType} deleted`);
                    }
                }
            } else {
                alert('Error updating defaults!');
            }
        })
        .catch(error => console.error('Error updating defaults:', error));
    });
}