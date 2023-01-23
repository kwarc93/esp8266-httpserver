// Global variables
var colorPicker
var oneSecondInterval
var timerValueCounterSeconds = 0

window.onload = function() {
	calcPageLook()

	colorPicker = new iro.ColorPicker("#picker",
		{
			borderWidth: 2,
			borderColor: "#f0f0f0",
			wheelLightness: false, 
		})
	
	colorPicker.on("input:end",
	function(color) {
		let xhr = new XMLHttpRequest()
		xhr.open("POST", "/rgb", true)
		xhr.setRequestHeader("Content-Type", "application/json")
		xhr.send(JSON.stringify(color.rgb))
	})
	
	// Update the picker wheel
	let xhr = new XMLHttpRequest()
	xhr.open("GET", "/rgb")
	xhr.responseType = "json"
	xhr.onload = function() { colorPicker.color.set(xhr.response) }
	xhr.send()

	var timerValue = document.getElementById("timer-value")
	var sliderInput = document.getElementById("timer-slider")

	// Show slider value in minutes
	timerValue.textContent = sliderInput.value
	sliderInput.addEventListener("input", (event) => {
		timerValueCounterSeconds = event.target.value * 60
		timerValue.textContent = event.target.value
	})
}

window.addEventListener("orientationchange",
function ()
{
	calcPageLook()
});

function runEffect(effect) {
	let xhr = new XMLHttpRequest()
    xhr.open("POST", "/" + effect, true)
    xhr.setRequestHeader("Content-Length", "0")
    xhr.send()
}

function timerBtnHandler() {
	if (timerValueCounterSeconds <= 0) {
		return
	}

	var icon = document.getElementById("timer-button-icon")
	var slider = document.getElementById("timer-slider")
	var time = document.getElementById("timer-value")

	function clearTimer() {
		clearInterval(oneSecondInterval)
		timerValueCounterSeconds = 0
		time.textContent = 0
		icon.className = "bi bi-clock"
		slider.disabled = false
		slider.step = 5
		slider.value = 0
	}

	function setCountdownTimerOnServer(timerValueSeconds) {
		let xhr = new XMLHttpRequest()
		xhr.open("POST", "/timer", true)
		xhr.setRequestHeader("Content-Type", "application/json")
		xhr.send(JSON.stringify({"seconds": timerValueSeconds}))
	}

	/* Toggle timer */
	if (icon.className === "bi bi-clock") {
		icon.className = "bi bi-clock-history"
		slider.disabled = true
		slider.step = 1

		setCountdownTimerOnServer(timerValueCounterSeconds)

		/* Start timer to countdown every 1 second */
		oneSecondInterval = setInterval(function() {
			timerValueCounterSeconds = timerValueCounterSeconds - 1
			slider.value = Math.round(timerValueCounterSeconds / 60)
			time.textContent = slider.value

			if (timerValueCounterSeconds <= 0) {
				colorPicker.color.set("#000000")
				clearTimer()
			}
		}, 1000);

	} else {
		clearTimer()
		setCountdownTimerOnServer(0)
	}
}

function calcPageLook() {
	const isMobileDevice = /Mobi/i.test(window.navigator.userAgent)
	if (!isMobileDevice) {
		return
	}
	
	const orientation = (screen.orientation || {}).type || screen.mozOrientation || screen.msOrientation
	const oriLandscape = orientation.startsWith("landscape")

	/* "Lock" the page look to portrait */
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