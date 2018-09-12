#ifndef _AUDIO_H
#define _AUDIO_H

#include <libconfig.h>
#include <stdint.h>

typedef struct {
  double current_volume_dB;
  int32_t minimum_volume_dB;
  int32_t maximum_volume_dB;
} audio_parameters;

typedef struct {
  void (*help)(void);
  char *name;

  // start of program
  int (*init)(int argc, char **argv);
  // at end of program
  void (*deinit)(void);

  void (*start)(int sample_rate, int sample_format);

  // block of samples
  void (*play)(short buf[], int samples);
  void (*stop)(void);

  // may be null if not implemented
  void (*flush)(void);

  // returns the delay before the next frame to be sent to the device would actually be audible.
  // almost certainly wrong if the buffer is empty, so put silent buffers into it to make it busy.
  // will change dynamically, so keep watching it. Implemented in ALSA only.
  // returns a negative error code if there's a problem
  int (*delay)(long *the_delay); // snd_pcm_sframes_t is a signed long

  // may be NULL, in which case soft volume is applied
  void (*volume)(double vol);

  // may be NULL, in which case soft volume parameters are used
  void (*parameters)(audio_parameters *info);

  // may be NULL, in which case software muting is used.
  void (*mute)(int do_mute);

} audio_output;

audio_output *audio_get_output(char *name);
void audio_ls_outputs(void);
void parse_general_audio_options(void);

#endif //_AUDIO_H
