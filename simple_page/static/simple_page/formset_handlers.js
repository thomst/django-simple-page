(function() {
    "use strict";
    document.addEventListener('formset:added', (event) => {
        if (event.detail.formsetName.startsWith('pagesection_set')) {
            const formset = event.target;
            const previousFormset = formset.previousElementSibling;
            const regionName = previousFormset.querySelector('input[name$="-region"]').value;
            formset.querySelector('input[name$="-region"]').value = regionName;
        }
    });
})();
