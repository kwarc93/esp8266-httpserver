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

	colorPicker.on('color:change',
	function(color) {
		setEffectBtnColor(color)
	});

	colorPicker.on("input:end",
	function(color) {
		fetch("/color", {
			method: "POST",
			headers: {"Content-Type": "application/json"},
			body: JSON.stringify(color.rgb)
		})
	})

	// Get the app state from server
	// Example response: {"color":{"r":0,"g":0,"b":0},"timer":333,"effect":"fire"}
	fetch("/state")
	.then((response) => response.json())
	.then((data) => {
		colorPicker.color.set(data.color)
		toggleEffectBtn(data.effect)
		setEffectBtnColor(colorPicker.color)
		serverTimerSeconds = data.timer
		timerHandler()
	})

	// Update the shut down timer
	var timerValue = document.getElementById("timer-value")
	var sliderInput = document.getElementById("timer-slider")

	timerValue.textContent = sliderInput.value
	sliderInput.addEventListener("input", (event) => { timerValue.textContent = event.target.value })
}

window.addEventListener("orientationchange",
function ()
{
	calcPageLook()
});

function setEffectBtnColor(color) {
	document.getElementById("ebtn-color").style.backgroundColor = color.hexString
	document.documentElement.style.setProperty("--breathe-color", color.rgbString.slice(4, -1))
}

function toggleEffectBtn(effectName) {
	// Simulate radio button behavior
	let btnPressedClass = "effect-button-pressed"
	let btnId = "ebtn-" + effectName
	let btns = document.getElementsByTagName("button")
	for (let i = 0; i < btns.length; i++) {
		if (btns[i].classList.contains(btnPressedClass)) {
			btns[i].classList.toggle(btnPressedClass)
		}
	}
	document.getElementById(btnId).classList.toggle(btnPressedClass)
}

function runEffect(effectName) {
	toggleEffectBtn(effectName)

	fetch("/effect", {
		method: "POST",
		headers: {"Content-Type": "application/json"},
		body: JSON.stringify({effect: effectName})
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
		slider.value = Math.ceil(remainingTimeSeconds / 60)
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

	if (oriLandscape) {
		document.body.setAttribute("style", "height: 100vh;");
	} else {
		document.body.setAttribute("style", "height: auto;");
	}
}