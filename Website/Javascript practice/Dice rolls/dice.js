function rollDice() {
    // Get the number of dice to roll from the input
    const numOfDice = parseInt(document.getElementById("NumOfDice").value);
    const diceResults = document.getElementById("results");
    const diceImages = document.getElementById("diceImages");

    // Validate input
    if (isNaN(numOfDice) || numOfDice <= 0) {
        alert("Please enter a valid number of dice.");
        return;
    }

    // Arrays to store the values and images
    const values = [];
    const images = [];

    // Roll the dice and generate results
    for (let i = 0; i < numOfDice; i++) {
        const value = Math.floor(Math.random() * 6) + 1;
        values.push(value);
        images.push(`<img src="dice/${value}.png" alt="Dice showing ${value}">`);
    }

    // Display the results
    diceResults.textContent = `Dice: ${values.join(", ")}`;
    diceImages.innerHTML = images.join("");
}
