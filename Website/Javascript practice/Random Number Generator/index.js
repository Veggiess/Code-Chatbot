const randomNumber = document.getElementById('randomNumber');
const label = document.getElementById('label');
const min = 1;
const max = 6;
let randomnum;

randomNumber.onclick = function() {
    randomnum = Math.floor(Math.random() * max + min);
    label.textContent = randomnum;
    }