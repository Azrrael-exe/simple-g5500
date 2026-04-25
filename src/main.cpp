#include <Arduino.h>
#include <math.h>
#include "axis_controller/axis_controller.h"
#include "llp.h"
#include "pinout.h"
#include "protocol.h"

// Mapea cualquier ángulo a [-180, 180). Ej: 270 -> -90, 450 -> 90.
float wrapAzimuth(float deg) {
    return fmodf(fmodf(deg + 180.0f, 360.0f) + 360.0f, 360.0f) - 180.0f;
}

// Función de calibración dummy para convertir voltaje a ángulo
// TODO: Ajustar según las características reales del sensor
float dummyCalibration(float voltage) {
    // Calibración lineal simple: 0V = 0°, 5V = 360°
    // Ajustar según el rango de tu sensor
    return (voltage / 5.0) * 360.0;
}

float azimuthCalibration(float voltage) {
  float maxVoltage = 4.47;
  float minVoltage = 0.03;
  float minAngle = -223;
  float maxAngle = 223;
  float angle = (voltage - minVoltage) / (maxVoltage - minVoltage) * (maxAngle - minAngle) + minAngle;
  return angle < minAngle ? minAngle : angle;
}

float elevationCalibration(float voltage) {
  float maxVoltage = 4.79;
  float minVoltage = 0.00;
  float minAngle = 0;
  float maxAngle = 180;
  float angle = (voltage - minVoltage) / (maxVoltage - minVoltage) * (maxAngle - minAngle) + minAngle;
  return angle < minAngle ? minAngle : angle;
}
// Crear controladores para azimut y elevación con feedback analógico
AxisController azimuthController(AZIMUTH_PWM_PIN, AZIMUTH_DIR_PIN,
                                  AZIMUTH_SENSOR_PIN, azimuthCalibration, 5.0);
AxisController elevationController(ELEVATION_PWM_PIN, ELEVATION_DIR_PIN,
                                    ELEVATION_SENSOR_PIN, elevationCalibration, 5.0);

DataPack inputPack;
DataPack outputPack;

float azTarget = NAN;  // NaN = sin objetivo activo
float elTarget = NAN;

const float AZ_DEADBAND = 2.0f;  // grados
const float EL_DEADBAND = 2.0f;

void setup() {
  // Inicializar comunicación serial
  Serial.begin(115200);
  Serial.setTimeout(10);  // Reduce el bloqueo de readBytes() de 1000ms a 10ms

  // Inicializar los controladores de ejes
  azimuthController.begin();
  elevationController.begin();

}

void loop() {
  // Cachear lecturas de sensor UNA vez por iteración para evitar analogRead() redundantes
  float azVoltage = azimuthController.getAxisVoltage();
  float elVoltage = elevationController.getAxisVoltage();
  float azAngle   = azimuthCalibration(azVoltage);
  float elAngle   = elevationCalibration(elVoltage);

  // Control bang-bang PRIMERO (prioridad alta — no debe ser bloqueado por serial)
  if (!isnan(azTarget)) {
    float err = azTarget - azAngle;
    if (fabs(err) <= AZ_DEADBAND) {
      azimuthController.stop();
      azTarget = NAN;
    } else if (err > 0) {
      azimuthController.move(255, true);   // forward
    } else {
      azimuthController.move(255, false);  // backward
    }
  }

  if (!isnan(elTarget)) {
    float err = elTarget - elAngle;
    if (fabs(err) <= EL_DEADBAND) {
      elevationController.stop();
      elTarget = NAN;
    } else if (err > 0) {
      elevationController.move(255, true);   // forward
    } else {
      elevationController.move(255, false);  // backward
    }
  }

  // Procesamiento serial DESPUÉS (prioridad baja — puede bloquearse hasta setTimeout ms)
  if (inputPack.available(Serial)) {
    // PRIORIDAD MÁXIMA: Sistema / Kill Switch / Homing
    if (inputPack.hasKey(SYSTEM_HEADER)) {
      uint16_t command = inputPack.getData(SYSTEM_HEADER);
      if (command == SYSTEM_KILL) {
        // Parada de emergencia: cancela cualquier objetivo activo y detiene motores.
        azTarget = NAN;
        elTarget = NAN;
        azimuthController.stop();
        elevationController.stop();
        return; // Detiene el procesamiento de cualquier otro comando en este paquete
      }
      if (command == SYSTEM_HOME) {
        // Homing: azimuth al midpoint (~0°), elevación al midpoint del rango calibrado [0°, 180°] = 90°.
        azTarget = -1.0f;
        elTarget = 90.0f;
        azimuthController.stop();
        elevationController.stop();
        return;
      }
    }

    if (inputPack.hasKey(AZIMUTH_HEADER)) {
      uint16_t command = inputPack.getData(AZIMUTH_HEADER);
      azTarget = NAN;  // cualquier comando manual cancela el goto
      if (command == AZIMUTH_FORWARD)       azimuthController.move(255, false);
      else if (command == AZIMUTH_BACKWARD) azimuthController.move(255, true);
      else if (command == AZIMUTH_STOP)     azimuthController.stop();
    }
    if (inputPack.hasKey(ELEVATION_HEADER)) {
      uint16_t command = inputPack.getData(ELEVATION_HEADER);
      elTarget = NAN;  // cualquier comando manual cancela el goto
      if (command == ELEVATION_FORWARD)       elevationController.move(255, true);
      else if (command == ELEVATION_BACKWARD) elevationController.move(255, false);
      else if (command == ELEVATION_STOP)     elevationController.stop();
    }
    if (inputPack.hasKey(GOTO_AZIMUTH)) {
      uint16_t raw = inputPack.getData(GOTO_AZIMUTH);
      azTarget = wrapAzimuth((int16_t)raw / 10.0f);
    }
    if (inputPack.hasKey(GOTO_ELEVATION)) {
      uint16_t raw = inputPack.getData(GOTO_ELEVATION);
      elTarget = (int16_t)raw / 10.0f;
    }
    if (inputPack.hasKey(FEEDBACK_HEADER)) {
      uint16_t command = inputPack.getData(FEEDBACK_HEADER);
      outputPack.clear();
      if (command == READ_VOLTAGE || command == READ_ALL) {
        outputPack.addData(AZIMUTH_HEADER,   (int16_t)(azVoltage * 1000.0f));
        outputPack.addData(ELEVATION_HEADER, (int16_t)(elVoltage * 1000.0f));
      }
      if (command == READ_ANGLE || command == READ_ALL) {
        outputPack.addData(0xAB, (int16_t)(azAngle * 10.0f));
        outputPack.addData(0xBC, (int16_t)(elAngle * 10.0f));
      }
      outputPack.write(Serial);
    }
  }
}