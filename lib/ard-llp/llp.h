#ifndef frame_h
#define frame_h

#include <Arduino.h>

class DataPack {
public:
  DataPack();
  bool addData(uint8_t index, byte msb, byte lsb);
  bool addData(uint8_t index, int16_t data);
  void clear();
  void write(Stream& inp);
  bool available(Stream& inp);
  uint16_t getData(uint8_t key);
  uint8_t inWaiting();
  uint8_t* getKeys();
  bool hasKey(uint8_t);

private:
  int8_t calCheckSum();

  // Buffer de salida (para write())
  uint8_t buffer[90];
  uint8_t cursor;

  // Buffer de entrada (para available() / getData() / hasKey())
  uint8_t inp_buffer[90];
  uint8_t inp_data;

  // State machine de recepción no-bloqueante
  enum RxState : uint8_t { IDLE, GOT_START, READING_PAYLOAD };
  RxState rx_state;
  uint8_t rx_len;  // longitud esperada del payload
  uint8_t rx_pos;  // bytes de payload+checksum recibidos hasta ahora
};

#endif
