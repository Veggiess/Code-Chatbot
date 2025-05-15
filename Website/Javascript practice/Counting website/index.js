const decrease = document.getElementById('decrease');
const reset = document.getElementById('reset');
const increase = document.getElementById('increase');
const Count = document.getElementById('Count');
let count = 0;

increase.onclick = function(){
    count++;
    Count.textContent = count;
}
decrease.onclick = function(){
    count--;
    Count.textContent = count;
}
reset.onclick = function(){
    count = 0;
    Count.textContent = count;
}