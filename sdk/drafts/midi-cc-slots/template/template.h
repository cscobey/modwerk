/* SPDX-License-Identifier: MIT */
#ifndef MIDI_TEMPLATE_H
#define MIDI_TEMPLATE_H
#include "../profile.h"
extern uint8_t mt_work[MM_PROFILE_BYTES];
extern char mt_command[16];
int mt_channels(unsigned write,uint8_t values[1024]);
int mt_preflight(const uint8_t values[1024],uint8_t fingerprints[128]);
int mt_persist(const uint8_t values[1024],const uint8_t fingerprints[128]);
void mt_reload_project(void);
int mt_stopped(void);
int mt_writable(void);
int mt_ui_context(void);
int mt_key(int code,int released);
int mt_runtime_key(int code,int pressed);
int mt_runtime_enc(int code,int delta);
void mt_clone_begin(void);
void mt_clone_finish(void);
void mt_project_loaded(unsigned caller);
unsigned mt_initialized(void);
unsigned mt_busy(void);
#endif
