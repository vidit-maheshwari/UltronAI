const display = document.querySelector('#display');
const numberButtons = document.querySelectorAll('[data-number]');
const operatorButtons = document.querySelectorAll('[data-operator]');
const equalsButton = document.querySelector('#equals');
const clearButton = document.querySelector('#clear');

let currentNumber = '0';
let firstNumber = null;
let operator = null;
let newNumber = true;

function handleNumber(input) {
    if (newNumber) {
        currentNumber = input;
        newNumber = false;
    } else {
        currentNumber += input;
    }
    display.textContent = currentNumber;
}

function handleOperator(op) {
    if (firstNumber === null && currentNumber !== '0') {
        firstNumber = parseFloat(currentNumber);
        operator = op;
        newNumber = true;
    }
}

function calculate() {
    if (firstNumber === null || currentNumber === '0' && newNumber) return;

    const secondNumber = parseFloat(currentNumber);
    let result;

    switch (operator) {
        case '+':
            result = firstNumber + secondNumber;
            break;
        case '-':
            result = firstNumber - secondNumber;
            break;
        case '*':
            result = firstNumber * secondNumber;
            break;
        case '/':
            if (secondNumber === 0) {
                display.textContent = 'Error';
                return;
            }
            result = firstNumber / secondNumber;
            break;
    }

    display.textContent = result.toFixed(2);
    operator = null;
    currentNumber = result.toString();
    newNumber = true;
}

function clearDisplay() {
    currentNumber = '0';
    firstNumber = null;
    operator = null;
    newNumber = true;
    display.textContent = '0';
}

numberButtons.forEach(button => {
    button.addEventListener('click', () => {
        const number = button.dataset.number;
        if (number === '.') {
            if (!currentNumber.includes('.')) {
                handleNumber(number);
            }
        } else {
            handleNumber(number);
        }
    });
});

operatorButtons.forEach(button => {
    button.addEventListener('click', () => {
        handleOperator(button.textContent);
    });
});

equalsButton.addEventListener('click', calculate);
clearButton.addEventListener('click', clearDisplay);

document.addEventListener('keydown', (e) => {
    const key = e.key;
    
    if (key >= '0' && key <= '9' || key === '.') {
        const button = document.querySelector(`[data-number="${key}"]`);
        if (button && (key === '.' ? !currentNumber.includes('.') : true)) {
            button.click();
        }
    }
    
    if (key === '+' || key === '-' || key === '*' || key === '/') {
        const button = document.querySelector(`[data-operator="${key}"]`);
        if (button) button.click();
    }
    
    if (key === 'Enter') {
        equalsButton.click();
    }
    
    if (key === 'Escape') {
        clearButton.click();
    }
    
    if (key === 'Backspace') {
        if (currentNumber.length === 1) {
            currentNumber = '0';
        } else {
            currentNumber = currentNumber.slice(0, -1);
        }
        display.textContent = currentNumber;
    }
});