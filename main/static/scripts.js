// Hide spinner when returning to homepage
window.onpageshow = function(e) {
	let loadSpinner = document.getElementById("loadSpinner");
	let mainBox = document.getElementsByClassName("main-box")[0];
	mainBox.style.display = "block"
	loadSpinner.style.display = "none";
}

// Display number of games selected with the slider
function displayNumber(x){
	let numLabel = document.getElementById("gamesNum");
	numLabel.innerHTML = x;
}

// Display loading icon when waiting for results
function displayLoader(){
	let loadSpinner = document.getElementById("loadSpinner");
	let mainBox = document.getElementsByClassName("main-box")[0];
	mainBox.style.display = "none"
	loadSpinner.style.display = "flex";
}