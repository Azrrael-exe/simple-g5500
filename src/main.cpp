#include <Arduino.h>
#include "axis_controller/axis_controller.h"
#include "llp.h"
#include "pinout.h"
#include "protocol.h"

// Función de calibración dummy para convertir voltaje a ángulo
// TODO: Ajustar según las características reales del sensor
float dummyCalibration(float voltage) {
    // Calibración lineal simple: 0V = 0°, 5V = 360°
    // Ajustar según el rango de tu sensor
    return (voltage / 5.0) * 360.0;
}

float azimuthCalibration(float voltage) {
  float maxVoltage = 4.5;
  float minVoltage = 0.06;
  float minAngle = 0;
  float maxAngle = 450;
  return (voltage - minVoltage) / (maxVoltage - minVoltage) * (maxAngle - minAngle) + minAngle;
}

float elevationCalibration(float voltage) {
  float maxVoltage = 4.79;
  float minVoltage = 0.00;
  float minAngle = 0;
  float maxAngle = 180;
  return (voltage - minVoltage) / (maxVoltage - minVoltage) * (maxAngle - minAngle) + minAngle;
}
// Crear controladores para azimut y elevación con feedback analógico
AxisController azimuthController(AZIMUTH_PWM_PIN, AZIMUTH_DIR_PIN,
                                  AZIMUTH_SENSOR_PIN, azimuthCalibration, 5.0);
AxisController elevationController(ELEVATION_PWM_PIN, ELEVATION_DIR_PIN,
                                    ELEVATION_SENSOR_PIN, elevationCalibration, 5.0);

DataPack inputPack;
DataPack outputPack;

float azTarget = -1.0f;  // -1 = sin objetivo activo
float elTarget = -1.0f;

const float AZ_DEADBAND = 2.0f;  // grados
const float EL_DEADBAND = 2.0f;

void setup() {
  // Inicializar comunicación serial
  Serial.begin(115200);

  // Inicializar los controladores de ejes
  azimuthController.begin();
  elevationController.begin();

}

void loop() {
  // Check for incoming commands
  if (inputPack.available(Serial)) {
    if (inputPack.hasKey(AZIMUTH_HEADER)) {
      uint16_t command = inputPack.getData(AZIMUTH_HEADER);
      azTarget = -1.0f;  // cualquier comando manual cancela el goto
      if (command == AZIMUTH_FORWARD) {
        azimuthController.move(255, false);
      } else if (command == AZIMUTH_BACKWARD) {
        azimuthController.move(255, true);
      } else if (command == AZIMUTH_STOP) {
        azimuthController.stop();
      }
    }
    if (inputPack.hasKey(ELEVATION_HEADER)) {
      uint16_t command = inputPack.getData(ELEVATION_HEADER);
      elTarget = -1.0f;  // cualquier comando manual cancela el goto
      if (command == ELEVATION_FORWARD) {
        elevationController.move(255, true);
      } else if (command == ELEVATION_BACKWARD) {
        elevationController.move(255, false);
      } else if (command == ELEVATION_STOP) {
        elevationController.stop();
      }
    }
    if (inputPack.hasKey(GOTO_AZIMUTH)) {
      uint16_t raw = inputPack.getData(GOTO_AZIMUTH);
      azTarget = (int16_t)raw / 10.0f;
    }
    if (inputPack.hasKey(GOTO_ELEVATION)) {
      uint16_t raw = inputPack.getData(GOTO_ELEVATION);
      elTarget = (int16_t)raw / 10.0f;
    }
    if (inputPack.hasKey(FEEDBACK_HEADER)) {
      uint16_t command = inputPack.getData(FEEDBACK_HEADER);
      outputPack.clear();

      if (command == READ_VOLTAGE || command == READ_ALL) {
        int16_t azVoltage_mV = (int16_t)(azimuthController.getAxisVoltage() * 1000.0);
        int16_t elVoltage_mV = (int16_t)(elevationController.getAxisVoltage() * 1000.0);
        outputPack.addData(AZIMUTH_HEADER, azVoltage_mV);
        outputPack.addData(ELEVATION_HEADER, elVoltage_mV);
      }
      if (command == READ_ANGLE || command == READ_ALL) {
        int16_t azAngle_deg = (int16_t)(azimuthController.getAxisAngle() * 10.0);
        int16_t elAngle_deg = (int16_t)(elevationController.getAxisAngle() * 10.0);
        outputPack.addData(0xAB, azAngle_deg);
        outputPack.addData(0xBC, elAngle_deg);
      }

      outputPack.write(Serial);
    }
  }

  // Control bang-bang de posición para goto azimuth
  if (azTarget >= 0.0f) {
    float err = azTarget - azimuthController.getAxisAngle();
    if (fabs(err) <= AZ_DEADBAND) {
      azimuthController.stop();
      azTarget = -1.0f;
    } else if (err > 0) {
      azimuthController.move(255, false);  // forward
    } else {
      azimuthController.move(255, true);   // backward
    }
  }

  // Control bang-bang de posición para goto elevation
  if (elTarget >= 0.0f) {
    float err = elTarget - elevationController.getAxisAngle();
    if (fabs(err) <= EL_DEADBAND) {
      elevationController.stop();
      elTarget = -1.0f;
    } else if (err > 0) {
      elevationController.move(255, true);   // forward
    } else {
      elevationController.move(255, false);  // backward
    }
  }
}