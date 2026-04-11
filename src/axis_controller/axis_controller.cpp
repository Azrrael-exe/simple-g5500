#include "axis_controller.h"

// Constructor sin feedback (para compatibilidad)
AxisController::AxisController(uint8_t pwm, uint8_t dir)
    : pwmPin(pwm), dirPin(dir), feedbackPin(255), currentSpeed(0),
      currentDirection(false), calibrationFunc(nullptr), vref(5.0) {
}

// Constructor con feedback
AxisController::AxisController(uint8_t pwm, uint8_t dir, uint8_t feedback, CalibrationFunction calibFunc, float vrefADC)
    : pwmPin(pwm), dirPin(dir), feedbackPin(feedback), currentSpeed(0),
      currentDirection(false), calibrationFunc(calibFunc), vref(vrefADC) {
}

// Inicializa los pines
void AxisController::begin() {
    pinMode(pwmPin, OUTPUT);
    pinMode(dirPin, OUTPUT);

    // Solo configura feedbackPin si es válido (no es 255)
    if (feedbackPin != 255) {
        pinMode(feedbackPin, INPUT);
    }

    // Inicializa en estado detenido
    analogWrite(pwmPin, 0);
    digitalWrite(dirPin, LOW);
}

// Establece la velocidad del motor (0-255)
void AxisController::setSpeed(uint8_t speed) {
    currentSpeed = speed;
    analogWrite(pwmPin, speed);
}

// Establece la dirección del motor
void AxisController::setDirection(bool direction) {
    currentDirection = direction;
    digitalWrite(dirPin, direction ? HIGH : LOW);
}

// Mueve el motor con velocidad y dirección específicas
void AxisController::move(uint8_t speed, bool direction) {
    setDirection(direction);
    setSpeed(speed);
}

// Detiene el motor
void AxisController::stop() {
    setSpeed(0);
}

// Obtiene la velocidad actual
uint8_t AxisController::getSpeed() const {
    return currentSpeed;
}

// Obtiene la dirección actual
bool AxisController::getDirection() const {
    return currentDirection;
}

// Lee el voltaje del sensor analógico
float AxisController::getAxisVoltage() const {
    // Verifica que el pin de feedback sea válido
    if (feedbackPin == 255) {
        return 0.0;
    }

    int adcValue = analogRead(feedbackPin);
    // Convierte el valor ADC (0-1023) a voltaje
    // ADC de 10 bits: 0-1023 -> 0-vref voltios
    return (adcValue / 1023.0) * vref;
}

// Obtiene el ángulo usando la función de calibración
float AxisController::getAxisAngle() const {
    float voltage = getAxisVoltage();

    // Aplica la función de calibración si existe
    if (calibrationFunc != nullptr) {
        return calibrationFunc(voltage);
    }

    // Si no hay función de calibración, retorna el voltaje
    return voltage;
}

