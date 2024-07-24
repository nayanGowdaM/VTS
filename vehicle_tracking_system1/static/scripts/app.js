document.addEventListener("DOMContentLoaded", function() {
    const knowMoreBtn = document.getElementById('sign-up-btn');
    const moreInfoDiv = document.getElementById('more-info');

    knowMoreBtn.addEventListener('click', function() {
        if (moreInfoDiv.style.display === "none") {
        moreInfoDiv.style.display = "block";
        } else {
        moreInfoDiv.style.display = "none";
        }
    });
});
