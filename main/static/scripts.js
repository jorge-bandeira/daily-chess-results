// Display number of games selected with the slider
function displayNumber(x){
	let numLabel = document.getElementById("gamesNum");
	numLabel.innerHTML = x;
}

function displayLoader(){
	let loadSpinner = document.getElementById("loadSpinner");
	let mainBox = document.getElementsByClassName("main-box")[0];
	mainBox.style.display = "none"
	loadSpinner.style.display = "flex";
}