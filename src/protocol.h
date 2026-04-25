#ifndef PROTOCOL_H
#define PROTOCOL_H

#define AZIMUTH_HEADER 0xAA
#define AZIMUTH_STOP 0xA0
#define AZIMUTH_FORWARD 0xA1
#define AZIMUTH_BACKWARD 0xA2

#define ELEVATION_HEADER 0xBB
#define ELEVATION_STOP 0xB0
#define ELEVATION_FORWARD 0xB1
#define ELEVATION_BACKWARD 0xB2

// Comandos de lectura de feedback
#define FEEDBACK_HEADER 0xCC
#define READ_VOLTAGE 0xC0
#define READ_ANGLE 0xC1
#define READ_ALL 0xC2

// Comandos goto (posición absoluta, valor = int16_t * 10, resolución 0.1°)
#define GOTO_AZIMUTH   0xDA
#define GOTO_ELEVATION 0xDB

// Comandos de sistema (Prioridad Máxima)
#define SYSTEM_HEADER 0xFF
#define SYSTEM_KILL   0x01
#define SYSTEM_HOME   0x02

#endif