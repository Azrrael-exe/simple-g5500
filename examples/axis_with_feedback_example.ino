/*
 * Ejemplo de uso de AxisController con sensor de feedback analógico
 *
 * Este ejemplo muestra cómo usar el AxisController con un sensor
 * analógico que lee voltaje proporcional al ángulo del eje.
 */

#include <axis_controller.h>

// Pines de control del motor
#define MOTOR_PWM_PIN 9
#define MOTOR_DIR_PIN 8
#define FEEDBACK_PIN A0  // Pin analógico para sensor de posición

// Voltaje de referencia del ADC (5V para Arduino UNO, 3.3V para algunos otros)
#define VREF 5.0

// Función de calibración personalizada: convierte voltaje a ángulo
// Esta función puede ser ajustada según las características de tu sensor
float voltageToAngle(float voltage) {
    // Ejemplo: sensor lineal que va de 0V (0°) a 5V (360°)
    // Ajusta esta fórmula según tu sensor específico
    float angle = (voltage / VREF) * 360.0;
    return angle;
}

// Otra función de calibración de ejemplo: sensor con offset
float voltageToAngleWithOffset(float voltage) {
    // Ejemplo: sensor que va de 0.5V (0°) a 4.5V (180°)
    const float V_MIN = 0.5;
    const float V_MAX = 4.5;
    const float ANGLE_RANGE = 180.0;

    // Limita el voltaje al rango válido
    if (voltage < V_MIN) voltage = V_MIN;
    if (voltage > V_MAX) voltage = V_MAX;

    // Calcula el ángulo
    float angle = ((voltage - V_MIN) / (V_MAX - V_MIN)) * ANGLE_RANGE;
    return angle;
}

// Crea el controlador con la función de calibración
AxisController axis(MOTOR_PWM_PIN, MOTOR_DIR_PIN, FEEDBACK_PIN, voltageToAngle, VREF);

void setup() {
    Serial.begin(9600);

    // Inicializa el controlador
    axis.begin();

    Serial.println("AxisController con feedback analógico iniciado");
}

void loop() {
    // Lee el voltaje del sensor
    float voltage = axis.getAxisVoltage();

    // Obtiene el ángulo usando la función de calibración
    float angle = axis.getAxisAngle();

    // Muestra los valores
    Serial.print("Voltaje: ");
    Serial.print(voltage, 3);
    Serial.print(" V | Ángulo: ");
    Serial.print(angle, 2);
    Serial.println(" °");

    // Ejemplo de control del motor basado en posición
    // Si el ángulo es menor a 180°, mueve en una dirección
    // Si es mayor, mueve en la otra dirección
    if (angle < 180.0) {
        axis.move(100, false);  // Velocidad 100, dirección false
    } else {
        axis.move(100, true);   // Velocidad 100, dirección true
    }

    delay(100);  // Actualiza cada 100ms
}
