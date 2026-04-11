#ifndef AXIS_CONTROLLER_H
#define AXIS_CONTROLLER_H

#include <Arduino.h>

// Tipo de función para calibración: voltaje -> ángulo
typedef float (*CalibrationFunction)(float voltage);

class AxisController {
private:
    uint8_t pwmPin;      // Pin para control PWM de velocidad
    uint8_t dirPin;      // Pin para control de dirección
    uint8_t feedbackPin; // Pin analógico para sensor de posición
    uint8_t currentSpeed; // Velocidad actual (0-255)
    bool currentDirection; // Dirección actual (false = una dirección, true = otra)
    CalibrationFunction calibrationFunc; // Función de calibración voltaje->ángulo
    float vref;          // Voltaje de referencia del ADC (típicamente 5.0V o 3.3V)

public:
    // Constructor sin feedback (para compatibilidad con código existente)
    AxisController(uint8_t pwm, uint8_t dir);

    // Constructor con feedback: recibe el pin PWM, el pin de dirección, el pin de feedback y la función de calibración
    AxisController(uint8_t pwm, uint8_t dir, uint8_t feedback, CalibrationFunction calibFunc, float vrefADC = 5.0);

    // Inicializa los pines
    void begin();

    // Establece la velocidad del motor (0-255)
    void setSpeed(uint8_t speed);

    // Establece la dirección del motor
    // direction: false para una dirección, true para la otra
    void setDirection(bool direction);

    // Mueve el motor con velocidad y dirección específicas
    void move(uint8_t speed, bool direction);

    // Detiene el motor
    void stop();

    // Obtiene la velocidad actual
    uint8_t getSpeed() const;

    // Obtiene la dirección actual
    bool getDirection() const;

    // Lee el voltaje del sensor analógico
    float getAxisVoltage() const;

    // Obtiene el ángulo usando la función de calibración
    float getAxisAngle() const;
};

#endif

