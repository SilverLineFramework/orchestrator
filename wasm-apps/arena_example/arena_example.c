/** @file arena_example.c
  *  @brief Example showing how to interact with the ARENA from a module
  * 
  *  Uses CONIX WASM (cwlib), an event library to perform file-based IO (for pubsub and signals)
  *  Requires a channel setup to allow the program communicate with the arena scene
  * 
  *  The event loop implemented by cwlib allows modules to migrate
  *  This requires main() to have a predefined structure:
  *    1. first call performed by main should be to cwlib_init(); NOTE: our makefile will do this for you if it does not find a call to cwlib_init()
  *    2. main sets up channels (or setup loop callback and timeout handlers, when available in cwlib)
  *    3. main calls cwlib_loop() to run the event loop
  *
  * Copyright (C) Wiselab CMU. 
  * @date April, 2020
  */
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>

#include "cwlib.h"

#define FMT_CREATE_OBJ "{\"object_id\":\"%s_%d\",\"action\":\"%s\",\"type\":\"object\",\"persist\":false,\"data\":{\"object_type\":\"cube\",\"position\":{\"x\":%.4f,\"y\":%.4f,\"z\":%.4f},\"rotation\":{\"x\":%.4f,\"y\":%.4f,\"z\":%.4f,\"w\":%.4f},\"scale\":{\"x\":%.4f,\"y\":%.4f,\"z\":%.4f},\"color\":\"%s\"}}"
#define FMT_RIG_UPDATE "{\"object_id\" : \"%s\", \"action\": \"update\", \"type\": \"rig\", \"data\": {\"position\": {\"x\": %.2f, \"y\":%.2f, \"z\":%.2f}}}"

const int max_str_len=512;

const double sqrt_2=1.4142;

typedef struct {
  int id;
  char *color;
  double x, y, z;
  char *obj_str;
} t_my_arena_obj;

// fd of the channel to the arena scene
int afd;

// declaration of callbacks
void loop(void *ctx);                                   //  event loop callback (called every loop_sleep_ms)
void on_arena_data(void *buf, size_t count, void *ctx); // channel callback when new data is available

/** 
  *  main() must have a predefined structure:
  *    1. call cwlib_init(); !NOTE: our makefile will insert a call to cwlib_init() if it does not find it
  *    2. call cwlib_channel_open to set up channels (or setup loop callback and timers, when available in cwlib)
  *    3. call cwlib_loop() to run the event loop
  */
int main(int argc, char **argv)
{
  // call cwlib_init() to startup cwlib; *no* state initialization before this call
  // Makefile will add this call if it does not find it

  // default camera and color values  
  char dft_cameraid[max_str_len]="unknown";
  char dft_color[max_str_len]="red";
  char *cameraid=dft_cameraid;
  char *cube_color=dft_color;

  // get arguments cameraid and color
  printf("argc:%d\n",argc);
  if( argc == 3 ) {
    cameraid = argv[1];
    cube_color = argv[2];
  }

  // init random number generator
  time_t t;
  srand((unsigned) time(&t));

  // get SCENE from env
  char *scene_name = getenv("SCENE"); // presence of env variable Jump To Event Loop (JTEL) indicates we should jump
  if (scene_name == NULL) {
    printf("Could not find environment variable SCENE.\n");
    return -1;
  }

  char ch_name[max_str_len+1];
  snprintf(ch_name, max_str_len, "/ch/%s/data", scene_name);

  // open channel to arena scene 
  afd = cwlib_channel_open(ch_name, O_RDWR, 0660, on_arena_data, NULL);
  if (afd < 0)
  {
    printf("error opening channel '%s'\n", ch_name);
    return -1;
  }

  // create obj struct with random color and starting coordinates
  t_my_arena_obj cube = {.id=rand() % 10000, .color=cube_color, .x=rand()%10, .y=1, .z=rand()%10, .obj_str=NULL}; 

  // send rig update so cube is in front of the camera
  char rig_str[max_str_len+1];
  int n = snprintf(rig_str, max_str_len, FMT_RIG_UPDATE, cameraid, cube.x, cube.y, cube.z+5);
  int len = (n>max_str_len) ? max_str_len : n;
  // write rig update to scene channel
  if (write(afd, rig_str, len) != len)
  {
      printf("error writing to channel\n");
  }

  // json string to create cube
  char obj_str[max_str_len+1];
  cube.obj_str = obj_str; 
  // object create str
  n = snprintf(cube.obj_str, max_str_len, FMT_CREATE_OBJ, "cube", cube.id, "create", cube.x, cube.y, cube.z, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, cube.color);
  len = (n>max_str_len) ? max_str_len : n;
  // write object create to scene channel
  if (write(afd, cube.obj_str, len) != len)
  {
      printf("error writing to channel\n");
  }

  // setup loop callback
  cwlib_loop_callback(loop, &cube); // pass cube obj as context

  cwlib_loop(500);

  return 0;
}

/**
  * Event loop callback (called every time interval passed to cwlib_loop(time_interval_ms))
  * 
  * @param ctx user provided context to pass the handler
  * 
  * @see cwlib_loop_callback() (called by main)
  * @see cwlib_loop call in main
  */
void loop(void *ctx)
{
  const double step = 0.1 ;
  t_my_arena_obj *cube = ctx;

  cube->x += ((rand() / (double)RAND_MAX) - 0.5) * 2.0 * step; // numbers between [-step, step]
  cube->z += ((rand() / (double)RAND_MAX) - 0.5) * 2.0 * step; // numbers between [-step, step]

  int n = snprintf(cube->obj_str, max_str_len, FMT_CREATE_OBJ, "cube", cube->id, "create", cube->x, cube->y, cube->z, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, cube->color);
  int len = (n>max_str_len) ? max_str_len : n;

  // write object create str to scene channel
  if (write(afd, cube->obj_str, len) != len)
  {
      printf("error writing to channel\n");
  }

}

/**
  * Channel callback when new data is available
  * 
  * @param buf event-specific data read from the channel
  * @param count size of data read
  * @param ctx user provided context to pass the handler
  * 
  * @ see cwlib_channel_open() (called by main)
  */
void on_arena_data(void *buf, size_t count, void *ctx)
{
  char *str = (char *)buf;
  str[count] = '\0';

  printf("%s", str);
}