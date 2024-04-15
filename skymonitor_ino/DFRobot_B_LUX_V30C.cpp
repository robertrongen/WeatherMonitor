/*! 
 * Robert Rongen, 24-9-2023: Modified the library to get the sensor working on an Arduino Nano with I2C on A5 and A4 
 * Renamed V30B to V30C
 * Replaced the bit-banging approach with the standard Wire library functions for I2C communication.
 * Added isConnected() check to begin()
*/
/*!
 * @file DFRobot_B_LUX_V30C.cpp
 * @brief Implementations of  methods in the class of DFRobot_B_LUX_V30C
 * @copyright	Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
 * @licence     The MIT License (MIT)
 * @author [Fary](Fary_young@outlook.com)
 * @version  V1.0
 * @date  2020-12-03
 * @https://github.com/DFRobot/DFRobot_B_LUX_V30B
 */

#include "DFRobot_B_LUX_V30C.h"

DFRobot_B_LUX_V30C::DFRobot_B_LUX_V30C(uint8_t cEN, uint8_t scl, uint8_t sda)
{
  _deviceAddr = DFRobot_B_LUX_V30_IIC_Addr;
  _SCL = scl;
  _SDA = sda;
  _cEN = cEN;
  _wire = &Wire;
}

bool DFRobot_B_LUX_V30C::begin()
{
    _wire->begin();
    _error = DFRobot_B_LUX_V30_OK;
    return isConnected();
}

bool DFRobot_B_LUX_V30C::isConnected()
{
  _wire->beginTransmission(_deviceAddr);
  _error = _wire->endTransmission();
  Serial.print("Light sensor Wire.endTransmission() returned: ");
  Serial.print (_error);
  if (_error == 0) {
    Serial.println(" (Success)");
  } else if (_error == 1 ) {
    Serial.println(" (Data too long to fit in transmit buffer)");
  } else if (_error == 2 ) {
    Serial.println(" (Received NACK on transmit of address)");
  } else if (_error == 3 ) {
    Serial.println(" (Received NACK on transmit of data)");
  } else if (_error == 4 ) {
    Serial.println(" (Other error)");
  }
  return (_error == 0);
}
int DFRobot_B_LUX_V30C::getError()
{
  int e = _error;
  _error = DFRobot_B_LUX_V30_OK;
  return e;
}

uint8_t DFRobot_B_LUX_V30C::readMode(void)
{
    _wire->beginTransmission(_deviceAddr >> 1);
    _wire->write(DFRobot_B_LUX_V30_ConfigReg);
    _error = _wire->endTransmission(false);
    
    if (_error != 0) {
        return 0;
    }
    
    _wire->requestFrom(_deviceAddr >> 1, 1);
    return _wire->read();
}

uint8_t DFRobot_B_LUX_V30C::setMode(uint8_t isManualMode, uint8_t isCDR, uint8_t isTime)
{
    uint8_t mode = isManualMode + isCDR + isTime;
    
    _wire->beginTransmission(_deviceAddr >> 1);
    _wire->write(DFRobot_B_LUX_V30_ConfigReg);
    _wire->write(mode);
    _error = _wire->endTransmission();
    
    return (_error == 0) ? 1 : 0;
}

uint8_t DFRobot_B_LUX_V30C::iicRead(uint8_t num, uint8_t* data)
{
    _wire->beginTransmission(_deviceAddr >> 1); // Shift the address to the right by 1 bit
    _wire->write(DFRobot_B_LUX_V30_DataReg);
    _error = _wire->endTransmission(false); // Send a restart after transmission
    
    if (_error != 0) {
        return 0;
    }
    
    uint8_t bytesRead = _wire->requestFrom(_deviceAddr >> 1, num);
    for (uint8_t i = 0; i < bytesRead; i++) {
        data[i] = _wire->read();
    }
    
    return (bytesRead == num) ? 1 : 0;
}

float DFRobot_B_LUX_V30C::lightStrengthLux()
{
  uint32_t value = 0;
  uint8_t data[6];
  if(iicRead(4,data)){
  value = data[3];
  value = (value<<8)|data[2];
  value = (value<<8)|data[1];
  value = (value<<8)|data[0];
  return ((float)value*1.4) / 1000;
  }
  Serial.println("Failed to read data from sensor.");
  return -1;
}