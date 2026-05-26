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
    if (feedbackPin == 255) {
        return 0.0;
    }

    // Promedia ADC_SAMPLES lecturas para reducir el ruido del ADC (~±1-2 LSB por muestra).
    // Costo: ADC_SAMPLES × 104 µs = 832 µs para 8 muestras — aceptable dado que el rotor
    // se mueve a ~7°/s (el movimiento durante ese tiempo es < 0.006°).
    const uint8_t ADC_SAMPLES = 8;
    uint16_t sum = 0;
    for (uint8_t i = 0; i < ADC_SAMPLES; i++) {
        sum += analogRead(feedbackPin);
    }
    return (sum / (ADC_SAMPLES * 1023.0)) * vref;
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

