#pragma once
#include "domain.h"

// ---- Pins (ESP32-S3). Keep in sync with diagram.json. ----
#define PIN_TFT_CS    10
#define PIN_TFT_MOSI  11
#define PIN_TFT_SCLK  12
#define PIN_TFT_MISO  13
#define PIN_TFT_DC     7
#define PIN_TFT_RST    6
#define PIN_TFT_BL    14

#define PIN_BTN_DOWN    4
#define PIN_BTN_SELECT  5
#define PIN_BTN_BACK   15

// ---- Phase-2 stand-in for the (not-yet-present) microphone + AI ----
#define SAMPLE_NOTE "Buy milk and call the dentist tomorrow morning."
#define SAMPLE_TASK_TITLE "Call the dentist"
#define SAMPLE_TASK_PRIORITY sb::Priority::High
