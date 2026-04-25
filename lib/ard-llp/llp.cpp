#include "llp.h"

DataPack::DataPack()
  : cursor(0), inp_data(0), rx_state(IDLE), rx_len(0), rx_pos(0) {
}

bool DataPack::addData(uint8_t index, byte msb, byte lsb) {
  if (cursor < 87) {
    buffer[cursor++] = index;
    buffer[cursor++] = msb;
    buffer[cursor++] = lsb;
    return true;
  }
  return false;
}

bool DataPack::addData(uint8_t index, int16_t data) {
  byte data_msb = byte(data >> 8);
  byte data_lsb = byte(data);
  return addData(index, data_msb, data_lsb);
}

void DataPack::clear() {
  for (int i = 0; i < 90; i++) {
    buffer[i] = 0;
  }
  cursor = 0;
}

int8_t DataPack::calCheckSum() {
  byte sum = 0;
  for (int i = 0; i < cursor; i++) {
    sum += buffer[i];
  }
  return byte(0xFF - sum);
}

void DataPack::write(Stream& inp) {
  inp.write(0x7E);
  inp.write(cursor);
  for (int i = 0; i < cursor; i++) {
    inp.write(buffer[i]);
  }
  inp.write(calCheckSum());
  clear();
}

// Recepción no-bloqueante mediante state machine.
// Nunca llama a readBytes() — consume sólo bytes ya disponibles en el buffer
// de hardware UART. Retorna true únicamente cuando se recibe un paquete completo
// y válido; retorna false de inmediato si no hay datos suficientes todavía.
bool DataPack::available(Stream& inp) {
  while (inp.available()) {      // drena bytes ya en el buffer, sin esperar
    uint8_t b = inp.read();      // non-blocking: sólo se llama cuando available()>0

    switch (rx_state) {

      case IDLE:
        if (b == 0x7E) {
          rx_state = GOT_START;
        }
        // Bytes que no son el marcador de inicio se descartan silenciosamente
        break;

      case GOT_START:
        rx_len = b;              // segundo byte del encabezado = longitud del payload
        rx_pos = 0;
        if (rx_len == 0 || rx_len > 90) {
          rx_state = IDLE;       // longitud inválida — re-sincronizar
        } else {
          rx_state = READING_PAYLOAD;
        }
        break;

      case READING_PAYLOAD:
        inp_buffer[rx_pos++] = b;
        if (rx_pos == rx_len + 1) {   // payload completo + byte de checksum
          rx_state = IDLE;
          uint8_t rec_checksum = inp_buffer[rx_len];
          uint16_t sum = 0;
          for (int i = 0; i < rx_len; i++) {
            sum += inp_buffer[i];
          }
          sum = 0xFF - byte(sum);
          if (rec_checksum == (uint8_t)sum) {
            inp_data = rx_len / 3;
            return true;              // paquete válido disponible
          }
          // Checksum incorrecto — descartar frame y re-sincronizar
          Serial.println("Invalid Check Sum");
          Serial.print("Rec: "); Serial.println(rec_checksum);
          Serial.print("Cal: "); Serial.println((uint8_t)sum);
        }
        break;
    }
  }
  return false;  // paquete incompleto — se continuará en la próxima iteración
}

uint8_t* DataPack::getKeys() {
  uint8_t* out = (uint8_t*)calloc(inp_data, sizeof(uint8_t));
  for (int i = 0; i < inp_data; i++) {
    out[i] = inp_buffer[3 * i];
  }
  return out;
}

uint8_t DataPack::inWaiting() {
  return inp_data;
}

bool DataPack::hasKey(uint8_t key) {
  for (int i = 0; i < inp_data * 3; i += 3) {
    if (key == inp_buffer[i]) {
      return true;
    }
  }
  return false;
}

uint16_t DataPack::getData(uint8_t key) {
  for (int i = 0; i < inp_data * 3; i += 3) {
    if (key == inp_buffer[i]) {
      return (inp_buffer[i + 1] << 8) | inp_buffer[i + 2];
    }
  }
  return 0;
}
