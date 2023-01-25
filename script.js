// Global variables
var colorPicker
var oneSecondInterval
var shutDownDate = 0
var serverTimerSeconds = 0

window.onload = function() {
	calcPageLook()

	colorPicker = new iro.ColorPicker("#picker",
	{
		borderWidth: 2,
		borderColor: "#d3d3d3",
		wheelLightness: false, 
	})
	
	colorPicker.on("input:end",
	function(color) {
		document.documentElement.style.setProperty("--breathe-color", color.rgbString.slice(4, -1))
		fetch("/rgb", {
			method: "POST",
			headers: {"Content-Type": "application/json"},
			body: JSON.stringify(color.rgb)
	  	})
	})
	
	// Update the picker wheel
	fetch("/rgb")
	.then((response) => response.json())
	.then((data) => {
		colorPicker.color.set(data)
		document.documentElement.style.setProperty("--breathe-color", colorPicker.color.rgbString.slice(4, -1))
	})
	
	// Update the shut down timer
	var timerValue = document.getElementById("timer-value")
	var sliderInput = document.getElementById("timer-slider")

	timerValue.textContent = sliderInput.value
	sliderInput.addEventListener("input", (event) => {timerValue.textContent = event.target.value})

	fetch("/timer")
	.then((response) => response.json())
	.then((data) => {
		serverTimerSeconds = data.seconds
		timerHandler()
	})
}

window.addEventListener("orientationchange",
function ()
{
	calcPageLook()
});

function runEffect(effect) {
	fetch("/" + effect, {
		method: "POST",
		headers: {"Content-Length": 0}
	})
}

function timerHandler() {
	var icon = document.getElementById("timer-button-icon")
	var slider = document.getElementById("timer-slider")
	var time = document.getElementById("timer-value")

	function clearTimer() {
		clearInterval(oneSecondInterval)
		serverTimerSeconds = 0
		shutDownDate = 0
		icon.className = "bi bi-clock"
		time.textContent = 0
		slider.disabled = false
		slider.step = 5
		slider.value = 0
	}

	function setTimerOnServer(timerValueSeconds) {
		fetch("/timer", {
  			method: "POST",
  			headers: {"Content-Type": "application/json"},
  			body: JSON.stringify({seconds: timerValueSeconds})
		})
	}

	function intervalHandler() {
		const remainingTimeSeconds = Math.round((shutDownDate - Date.now()) / 1000)
		slider.value = Math.round(remainingTimeSeconds / 60)
		time.textContent = slider.value

		if (remainingTimeSeconds <= 0) {
			colorPicker.color.set("#000000")
			clearTimer()
		}
	}

	function enableTimer() {
		icon.className = "bi bi-clock-history"
		slider.disabled = true
		slider.step = 1

		if (serverTimerSeconds == 0) {
			serverTimerSeconds = slider.value * 60
			setTimerOnServer(serverTimerSeconds)
		}

		shutDownDate = Date.now() + serverTimerSeconds * 1000
		intervalHandler()
		oneSecondInterval = setInterval(intervalHandler, 1000);
	}

	function disableTimer() {
		clearTimer()
		setTimerOnServer(0)
	}

	if (serverTimerSeconds == 0 && slider.value == 0) {
		return
	}

	if (shutDownDate == 0) {
		enableTimer()

	} else {
		disableTimer()
	}
}

function calcPageLook() {
	const isMobileDevice = /Mobi/i.test(window.navigator.userAgent)
	if (!isMobileDevice) {
		return
	}
	
	const orientation = (screen.orientation || {}).type || screen.mozOrientation || screen.msOrientation
	const oriLandscape = orientation.startsWith("landscape")

	// "Lock" the page look to portrait
	if (oriLandscape) {
		document.body.setAttribute("style",
		"transform: rotate(-90deg) translate(-50%, -50%);\
		transform-origin: left top;\
		top: 50%;\
		left: 50%;\
		");
	} else {
		document.body.setAttribute("style",
		"transform: translate(-50%, -50%);\
		top: 50%;\
		left: 50%;\
		");
	}
}