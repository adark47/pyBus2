/*
 * RTSP protocol handler. This file is part of Shairport.
 * Copyright (c) James Laird 2013
 * Modifications associated with audio synchronization, mutithreading and
 * metadata handling copyright (c) Mike Brady 2014-2017
 * All rights reserved.
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use,
 * copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 */

#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <memory.h>
#include <netdb.h>
#include <netinet/in.h>
#include <poll.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include "config.h"

#ifdef HAVE_LIBSSL
#include <openssl/md5.h>
#endif

#ifdef HAVE_LIBMBEDTLS
#include <mbedtls/md5.h>
#endif

#ifdef HAVE_LIBPOLARSSL
#include <polarssl/md5.h>
#endif

#include "common.h"
#include "player.h"
#include "rtp.h"
#include "rtsp.h"

#ifdef AF_INET6
#define INETx_ADDRSTRLEN INET6_ADDRSTRLEN
#else
#define INETx_ADDRSTRLEN INET_ADDRSTRLEN
#endif

#define METADATA_SNDBUF (4 * 1024 * 1024)

enum rtsp_read_request_response {
  rtsp_read_request_response_ok,
  rtsp_read_request_response_immediate_shutdown_requested,
  rtsp_read_request_response_bad_packet,
  rtsp_read_request_response_channel_closed,
  rtsp_read_request_response_error
};

// Mike Brady's part...
static pthread_mutex_t barrier_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t play_lock = PTHREAD_MUTEX_INITIALIZER;

// every time we want to retain or release a reference count, lock it with this
// if a reference count is read as zero, it means the it's being deallocated.
static pthread_mutex_t reference_counter_lock = PTHREAD_MUTEX_INITIALIZER;

// only one thread is allowed to use the player at once.
// it monitors the request variable (at least when interrupted)
// static pthread_mutex_t playing_mutex = PTHREAD_MUTEX_INITIALIZER;
// static int please_shutdown = 0;
// static pthread_t playing_thread = 0;

static rtsp_conn_info **conns = NULL;

int RTSP_connection_index = 0;

void memory_barrier() {
  pthread_mutex_lock(&barrier_mutex);
  pthread_mutex_unlock(&barrier_mutex);
}

#ifdef CONFIG_METADATA
typedef struct {
  pthread_mutex_t pc_queue_lock;
  pthread_cond_t pc_queue_item_added_signal;
  pthread_cond_t pc_queue_item_removed_signal;
  size_t item_size;  // number of bytes in each item
  uint32_t count;    // number of items in the queue
  uint32_t capacity; // maximum number of items
  uint32_t toq;      // first item to take
  uint32_t eoq;      // free space at end of queue
  void *items;       // a pointer to where the items are actually stored
} pc_queue;          // producer-consumer queue
#endif

typedef struct {
  uint32_t referenceCount; // we might start using this...
  int nheaders;
  char *name[16];
  char *value[16];

  int contentlength;
  char *content;

  // for requests
  char method[16];

  // for responses
  int respcode;
} rtsp_message;

#ifdef CONFIG_METADATA
typedef struct {
  uint32_t type;
  uint32_t code;
  char *data;
  uint32_t length;
  rtsp_message *carrier;
} metadata_package;

void pc_queue_init(pc_queue *the_queue, char *items, size_t item_size, uint32_t number_of_items) {
  pthread_mutex_init(&the_queue->pc_queue_lock, NULL);
  pthread_cond_init(&the_queue->pc_queue_item_added_signal, NULL);
  pthread_cond_init(&the_queue->pc_queue_item_removed_signal, NULL);
  the_queue->item_size = item_size;
  the_queue->items = items;
  the_queue->count = 0;
  the_queue->capacity = number_of_items;
  the_queue->toq = 0;
  the_queue->eoq = 0;
}

int send_metadata(uint32_t type, uint32_t code, char *data, uint32_t length, rtsp_message *carrier,
                  int block);

int send_ssnc_metadata(uint32_t code, char *data, uint32_t length, int block) {
  return send_metadata('ssnc', code, data, length, NULL, block);
}

int pc_queue_add_item(pc_queue *the_queue, const void *the_stuff, int block) {
  int rc;
  if (the_queue) {
    if (block == 0) {
      rc = pthread_mutex_trylock(&the_queue->pc_queue_lock);
      if (rc == EBUSY)
        return EBUSY;
    } else
      rc = pthread_mutex_lock(&the_queue->pc_queue_lock);
    if (rc)
      debug(1, "Error locking for pc_queue_add_item");
    while (the_queue->count == the_queue->capacity) {
      rc = pthread_cond_wait(&the_queue->pc_queue_item_removed_signal, &the_queue->pc_queue_lock);
      if (rc)
        debug(1, "Error waiting for item to be removed");
    }
    uint32_t i = the_queue->eoq;
    void *p = the_queue->items + the_queue->item_size * i;
    //    void * p = &the_queue->qbase + the_queue->item_size*the_queue->eoq;
    memcpy(p, the_stuff, the_queue->item_size);

    // update the pointer
    i++;
    if (i == the_queue->capacity)
      // fold pointer if necessary
      i = 0;
    the_queue->eoq = i;
    the_queue->count++;
    if (the_queue->count == the_queue->capacity)
      debug(1, "pc_queue is full!");
    rc = pthread_cond_signal(&the_queue->pc_queue_item_added_signal);
    if (rc)
      debug(1, "Error signalling after pc_queue_add_item");
    rc = pthread_mutex_unlock(&the_queue->pc_queue_lock);
    if (rc)
      debug(1, "Error unlocking for pc_queue_add_item");
  } else {
    debug(1, "Adding an item to a NULL queue");
  }
  return 0;
}

int pc_queue_get_item(pc_queue *the_queue, void *the_stuff) {
  int rc;
  if (the_queue) {
    rc = pthread_mutex_lock(&the_queue->pc_queue_lock);
    if (rc)
      debug(1, "Error locking for pc_queue_get_item");
    while (the_queue->count == 0) {
      rc = pthread_cond_wait(&the_queue->pc_queue_item_added_signal, &the_queue->pc_queue_lock);
      if (rc)
        debug(1, "Error waiting for item to be added");
    }
    uint32_t i = the_queue->toq;
    //    void * p = &the_queue->qbase + the_queue->item_size*the_queue->toq;
    void *p = the_queue->items + the_queue->item_size * i;
    memcpy(the_stuff, p, the_queue->item_size);

    // update the pointer
    i++;
    if (i == the_queue->capacity)
      // fold pointer if necessary
      i = 0;
    the_queue->toq = i;
    the_queue->count--;
    rc = pthread_cond_signal(&the_queue->pc_queue_item_removed_signal);
    if (rc)
      debug(1, "Error signalling after pc_queue_removed_item");
    rc = pthread_mutex_unlock(&the_queue->pc_queue_lock);
    if (rc)
      debug(1, "Error unlocking for pc_queue_get_item");
  } else {
    debug(1, "Removing an item from a NULL queue");
  }
  return 0;
}

#endif

void ask_other_rtsp_conversation_threads_to_stop(pthread_t except_this_thread);

void rtsp_request_shutdown_stream(void) {
  debug(1, "Request to shut down all rtsp conversation threads");
  ask_other_rtsp_conversation_threads_to_stop(0); // i.e. ask all playing threads to stop
}

// keep track of the threads we have spawned so we can join() them
static int nconns = 0;
static void track_thread(rtsp_conn_info *conn) {
  conns = realloc(conns, sizeof(rtsp_conn_info *) * (nconns + 1));
  if (conns) {
    conns[nconns] = conn;
    nconns++;
  } else {
    die("could not reallocate memnory for \"conns\" in rtsp.c.");
  }
}

static void cleanup_threads(void) {
  void *retval;
  int i;
  // debug(2, "culling threads.");
  for (i = 0; i < nconns;) {
    if (conns[i]->running == 0) {
      debug(3, "found RTSP connection thread %d in a non-running state.",
            conns[i]->connection_number);
      pthread_join(conns[i]->thread, &retval);
      debug(3, "RTSP connection thread %d deleted...", conns[i]->connection_number);
      if (conns[i] == playing_conn)
        playing_conn = NULL;
      free(conns[i]);
      nconns--;
      if (nconns)
        conns[i] = conns[nconns];
    } else {
      i++;
    }
  }
}

// ask all rtsp_conversation threads to stop -- there should be at most one, but
// ya never know.

void ask_other_rtsp_conversation_threads_to_stop(pthread_t except_this_thread) {
  int i;
  debug(1, "asking playing threads to stop");
  for (i = 0; i < nconns; i++) {
    if (((except_this_thread == 0) || (pthread_equal(conns[i]->thread, except_this_thread) == 0)) &&
        (conns[i]->running != 0)) {
      conns[i]->stop = 1;
      pthread_kill(conns[i]->thread, SIGUSR1);
    }
  }
}

// park a null at the line ending, and return the next line pointer
// accept \r, \n, or \r\n
static char *nextline(char *in, int inbuf) {
  char *out = NULL;
  while (inbuf) {
    if (*in == '\r') {
      *in++ = 0;
      out = in;
    }
    if (*in == '\n') {
      *in++ = 0;
      out = in;
    }

    if (out)
      break;

    in++;
    inbuf--;
  }
  return out;
}

static void msg_retain(rtsp_message *msg) {
  if (msg) {
    int rc = pthread_mutex_lock(&reference_counter_lock);
    if (rc)
      debug(1, "Error %d locking reference counter lock");
    msg->referenceCount++;
    rc = pthread_mutex_unlock(&reference_counter_lock);
    if (rc)
      debug(1, "Error %d unlocking reference counter lock");
  } else {
    debug(1, "null rtsp_message pointer passed to retain");
  }
}

static rtsp_message *msg_init(void) {
  rtsp_message *msg = malloc(sizeof(rtsp_message));
  if (msg) {
    memset(msg, 0, sizeof(rtsp_message));
    msg->referenceCount = 1; // from now on, any access to this must be protected with the lock
  } else {
    die("can not allocate memory for an rtsp_message.");
  }
  return msg;
}

static int msg_add_header(rtsp_message *msg, char *name, char *value) {
  if (msg->nheaders >= sizeof(msg->name) / sizeof(char *)) {
    warn("too many headers?!");
    return 1;
  }

  msg->name[msg->nheaders] = strdup(name);
  msg->value[msg->nheaders] = strdup(value);
  msg->nheaders++;

  return 0;
}

static char *msg_get_header(rtsp_message *msg, char *name) {
  int i;
  for (i = 0; i < msg->nheaders; i++)
    if (!strcasecmp(msg->name[i], name))
      return msg->value[i];
  return NULL;
}

static void debug_print_msg_headers(int level, rtsp_message *msg) {
  int i;
  for (i = 0; i < msg->nheaders; i++) {
    debug(level, "  Type: \"%s\", content: \"%s\"", msg->name[i], msg->value[i]);
  }
}

static void msg_free(rtsp_message *msg) {

  if (msg) {
    int rc = pthread_mutex_lock(&reference_counter_lock);
    if (rc)
      debug(1, "Error %d locking reference counter lock during msg_free()", rc);
    msg->referenceCount--;
    rc = pthread_mutex_unlock(&reference_counter_lock);
    if (rc)
      debug(1, "Error %d unlocking reference counter lock during msg_free()", rc);
    if (msg->referenceCount == 0) {
      int i;
      for (i = 0; i < msg->nheaders; i++) {
        free(msg->name[i]);
        free(msg->value[i]);
      }
      if (msg->content)
        free(msg->content);
      free(msg);
    } // else {
      // debug(1,"rtsp_message reference count non-zero:
      // %d!",msg->referenceCount);
      //}
  } else {
    debug(1, "null rtsp_message pointer passed to msg_free()");
  }
}

static int msg_handle_line(rtsp_message **pmsg, char *line) {
  rtsp_message *msg = *pmsg;

  if (!msg) {
    msg = msg_init();
    *pmsg = msg;
    char *sp, *p;

    // debug(1, "received request: %s", line);

    p = strtok_r(line, " ", &sp);
    if (!p)
      goto fail;
    strncpy(msg->method, p, sizeof(msg->method) - 1);

    p = strtok_r(NULL, " ", &sp);
    if (!p)
      goto fail;

    p = strtok_r(NULL, " ", &sp);
    if (!p)
      goto fail;
    if (strcmp(p, "RTSP/1.0"))
      goto fail;

    return -1;
  }

  if (strlen(line)) {
    char *p;
    p = strstr(line, ": ");
    if (!p) {
      warn("bad header: >>%s<<", line);
      goto fail;
    }
    *p = 0;
    p += 2;
    msg_add_header(msg, line, p);
    debug(3, "    %s: %s.", line, p);
    return -1;
  } else {
    char *cl = msg_get_header(msg, "Content-Length");
    if (cl)
      return atoi(cl);
    else
      return 0;
  }

fail:
  *pmsg = NULL;
  msg_free(msg);
  return 0;
}

static enum rtsp_read_request_response rtsp_read_request(rtsp_conn_info *conn,
                                                         rtsp_message **the_packet) {
  enum rtsp_read_request_response reply = rtsp_read_request_response_ok;
  ssize_t buflen = 512;
  char *buf = malloc(buflen + 1);

  rtsp_message *msg = NULL;

  ssize_t nread;
  ssize_t inbuf = 0;
  int msg_size = -1;

  while (msg_size < 0) {
    fd_set readfds;
    FD_ZERO(&readfds);
    FD_SET(conn->fd, &readfds);
    do {
      memory_barrier();
    } while (conn->stop == 0 &&
             pselect(conn->fd + 1, &readfds, NULL, NULL, NULL, &pselect_sigset) <= 0);
    if (conn->stop != 0) {
      debug(3, "RTSP conversation thread %d shutdown requested.", conn->connection_number);
      reply = rtsp_read_request_response_immediate_shutdown_requested;
      goto shutdown;
    }
    nread = read(conn->fd, buf + inbuf, buflen - inbuf);

    if (nread == 0) {
      // a blocking read that returns zero means eof -- implies connection closed
      debug(3, "RTSP conversation thread %d -- connection closed.", conn->connection_number);
      reply = rtsp_read_request_response_channel_closed;
      goto shutdown;
    }

    if (nread < 0) {
      if (errno == EINTR)
        continue;
      perror("read failure");
      reply = rtsp_read_request_response_channel_closed;
      goto shutdown;
    }
    inbuf += nread;

    char *next;
    while (msg_size < 0 && (next = nextline(buf, inbuf))) {
      msg_size = msg_handle_line(&msg, buf);

      if (!msg) {
        warn("no RTSP header received");
        reply = rtsp_read_request_response_bad_packet;
        goto shutdown;
      }

      inbuf -= next - buf;
      if (inbuf)
        memmove(buf, next, inbuf);
    }
  }

  if (msg_size > buflen) {
    buf = realloc(buf, msg_size);
    if (!buf) {
      warn("too much content");
      reply = rtsp_read_request_response_error;
      goto shutdown;
    }
    buflen = msg_size;
  }

  uint64_t threshold_time =
      get_absolute_time_in_fp() + ((uint64_t)5 << 32); // i.e. five seconds from now
  int warning_message_sent = 0;

  const size_t max_read_chunk = 50000;
  while (inbuf < msg_size) {

    // we are going to read the stream in chunks and time how long it takes to
    // do so.
    // If it's taking too long, (and we find out about it), we will send an
    // error message as
    // metadata

    if (warning_message_sent == 0) {
      uint64_t time_now = get_absolute_time_in_fp();
      if (time_now > threshold_time) { // it's taking too long
        debug(1, "Error receiving metadata from source -- transmission seems "
                 "to be stalled.");
#ifdef CONFIG_METADATA
        send_ssnc_metadata('stal', NULL, 0, 1);
#endif
        warning_message_sent = 1;
      }
    }
    fd_set readfds;
    FD_ZERO(&readfds);
    FD_SET(conn->fd, &readfds);
    do {
      memory_barrier();
    } while (conn->stop == 0 &&
             pselect(conn->fd + 1, &readfds, NULL, NULL, NULL, &pselect_sigset) <= 0);
    if (conn->stop != 0) {
      debug(1, "RTSP shutdown requested.");
      reply = rtsp_read_request_response_immediate_shutdown_requested;
      goto shutdown;
    }
    ssize_t read_chunk = msg_size - inbuf;
    if (read_chunk > max_read_chunk)
      read_chunk = max_read_chunk;
    nread = read(conn->fd, buf + inbuf, read_chunk);
    if (!nread) {
      reply = rtsp_read_request_response_error;
      goto shutdown;
    }
    if (nread < 0) {
      if (errno == EINTR)
        continue;
      perror("read failure");
      reply = rtsp_read_request_response_error;
      goto shutdown;
    }
    inbuf += nread;
  }

  msg->contentlength = inbuf;
  msg->content = buf;
  *the_packet = msg;
  return reply;

shutdown:
  if (msg) {
    msg_free(msg); // which will free the content and everything else
  }
  // in case the message wasn't formed or wasn't fully initialised
  if ((msg && (msg->content == NULL)) || (!msg))
    free(buf);
  *the_packet = NULL;
  return reply;
}

static void msg_write_response(int fd, rtsp_message *resp) {
  char pkt[1024];
  int pktfree = sizeof(pkt);
  char *p = pkt;
  int i, n;

  n = snprintf(p, pktfree, "RTSP/1.0 %d %s\r\n", resp->respcode,
               resp->respcode == 200 ? "OK" : "Unauthorized");
  // debug(1, "sending response: %s", pkt);
  pktfree -= n;
  p += n;

  for (i = 0; i < resp->nheaders; i++) {
    //    debug(3, "    %s: %s.", resp->name[i], resp->value[i]);
    n = snprintf(p, pktfree, "%s: %s\r\n", resp->name[i], resp->value[i]);
    pktfree -= n;
    p += n;
    if (pktfree <= 0)
      die("Attempted to write overlong RTSP packet");
  }

  if (pktfree < 3)
    die("Attempted to write overlong RTSP packet");

  strcpy(p, "\r\n");
  int ignore = write(fd, pkt, p - pkt + 2);
}

static void handle_record(rtsp_conn_info *conn, rtsp_message *req, rtsp_message *resp) {
  debug(3, "Connection %d: RECORD", conn->connection_number);
  resp->respcode = 200;
  // I think this is for telling the client what the absolute minimum latency
  // actually is,
  // and when the client specifies a latency, it should be added to this figure.

  // Thus, AirPlay's latency figure of 77175, when added to 11025 gives you
  // exactly 88200
  // and iTunes' latency figure of 88553, when added to 11025 gives you 99578,
  // pretty close to the 99400 we guessed.

  msg_add_header(resp, "Audio-Latency", "11025");

  char *p;
  uint32_t rtptime = 0;
  char *hdr = msg_get_header(req, "RTP-Info");

  if (hdr) {
    // debug(1,"FLUSH message received: \"%s\".",hdr);
    // get the rtp timestamp
    p = strstr(hdr, "rtptime=");
    if (p) {
      p = strchr(p, '=');
      if (p) {
        rtptime = uatoi(p + 1); // unsigned integer -- up to 2^32-1
        rtptime--;
        // debug(1,"RTSP Flush Requested by handle_record: %u.",rtptime);
        player_flush(rtptime, conn);
      }
    }
  }
  usleep(500000);
}

static void handle_options(rtsp_conn_info *conn, rtsp_message *req, rtsp_message *resp) {
  debug(3, "Connection %d: OPTIONS", conn->connection_number);
  resp->respcode = 200;
  msg_add_header(resp, "Public", "ANNOUNCE, SETUP, RECORD, "
                                 "PAUSE, FLUSH, TEARDOWN, "
                                 "OPTIONS, GET_PARAMETER, SET_PARAMETER");
}

static void handle_teardown(rtsp_conn_info *conn, rtsp_message *req, rtsp_message *resp) {
  debug(3, "Connection %d: TEARDOWN", conn->connection_number);
  // if (!rtsp_playing())
  //  debug(1, "This RTSP connection thread (%d) doesn't think it's playing, but "
  //           "it's sending a response to teardown anyway",conn->connection_number);
  resp->respcode = 200;
  msg_add_header(resp, "Connection", "close");

  debug(3,
        "TEARDOWN: synchronously terminating the player thread of RTSP conversation thread %d (2).",
        conn->connection_number);
  // if (rtsp_playing()) {
  player_stop(conn);
  debug(3, "TEARDOWN: successful termination of playing thread of RTSP conversation thread %d.",
        conn->connection_number);
  //}
}

static void handle_flush(rtsp_conn_info *conn, rtsp_message *req, rtsp_message *resp) {
  debug(3, "Connection %d: FLUSH", conn->connection_number);
  //  if (!rtsp_playing())
  //    debug(1, "This RTSP conversation thread (%d) doesn't think it's playing, but "
  //            "it's sending a response to flush anyway",conn->connection_number);
  char *p = NULL;
  uint32_t rtptime = 0;
  char *hdr = msg_get_header(req, "RTP-Info");

  if (hdr) {
    // debug(1,"FLUSH message received: \"%s\".",hdr);
    // get the rtp timestamp
    p = strstr(hdr, "rtptime=");
    if (p) {
      p = strchr(p, '=');
      if (p)
        rtptime = uatoi(p + 1); // unsigned integer -- up to 2^32-1
    }
  }
// debug(1,"RTSP Flush Requested: %u.",rtptime);
#ifdef CONFIG_METADATA
  if (p)
    send_metadata('ssnc', 'flsr', p+1, strlen(p+1), req, 1);
  else
    send_metadata('ssnc', 'flsr', NULL, 0, NULL, 0);
#endif
  player_flush(rtptime, conn); // will not crash even it there is no player thread.
  resp->respcode = 200;
}

static void handle_setup(rtsp_conn_info *conn, rtsp_message *req, rtsp_message *resp) {
  debug(3, "Connection %d: SETUP", conn->connection_number);
  int cport, tport;
  int lsport, lcport, ltport;

  char *ar = msg_get_header(req, "Active-Remote");
  if (ar) {
    debug(1, "Active-Remote string seen: \"%s\".", ar);
    // get the active remote
    char *p;
    conn->dacp_active_remote = strtoul(ar, &p, 10);
#ifdef CONFIG_METADATA
    send_metadata('ssnc', 'acre', ar, strlen(ar), req, 1);
#endif
  }

  ar = msg_get_header(req, "DACP-ID");
  if (ar) {
    debug(1, "DACP-ID string seen: \"%s\".", ar);
    conn->dacp_id = strdup(ar);
#ifdef CONFIG_METADATA
    send_metadata('ssnc', 'daid', ar, strlen(ar), req, 1);
#endif
  }

  // This latency-setting mechanism is deprecated and will be removed.
  // If no non-standard latency is chosen, automatic negotiated latency setting
  // is permitted.

  // Select a static latency
  // if iTunes V10 or later is detected, use the iTunes latency setting
  // if AirPlay is detected, use the AirPlay latency setting
  // for everything else, use the general latency setting, if given, or
  // else use the default latency setting

  config.latency = -1;

  if (config.userSuppliedLatency)
    config.latency = config.userSuppliedLatency;

  char *ua = msg_get_header(req, "User-Agent");
  if (ua == 0) {
    debug(1, "No User-Agent string found in the SETUP message. Using latency "
             "of %d frames.",
          config.latency);
  } else {
    if (strstr(ua, "iTunes") == ua) {
      int iTunesVersion = 0;
      // now check it's version 10 or later
      char *pp = strchr(ua, '/') + 1;
      if (pp)
        iTunesVersion = atoi(pp);
      else
        debug(2, "iTunes Version Number not found.");
      if (iTunesVersion >= 10) {
        debug(1, "User-Agent is iTunes 10 or better, (actual version is %d); "
                 "selecting the iTunes "
                 "latency of %d frames.",
              iTunesVersion, config.iTunesLatency);
        config.latency = config.iTunesLatency;
        conn->staticLatencyCorrection = 11025;
      }
    } else if (strstr(ua, "AirPlay") == ua) {
      debug(2, "User-Agent is AirPlay; selecting the AirPlay latency of %d frames.",
            config.AirPlayLatency);
      config.latency = config.AirPlayLatency;
    } else if (strstr(ua, "forked-daapd") == ua) {
      debug(2, "User-Agent is forked-daapd; selecting the forked-daapd latency "
               "of %d frames.",
            config.ForkedDaapdLatency);
      config.latency = config.ForkedDaapdLatency;
      conn->staticLatencyCorrection = 11025;
    } else {
      debug(2, "Unrecognised User-Agent. Using latency of %d frames.", config.latency);
    }
  }

  if (config.latency == -1) {
    // this means that no static latency was set, so we'll allow it to be set
    // dynamically
    config.latency = 88198; // to be sure, to be sure -- make it slighty
                            // different from the default to ensure we get a
                            // debug message when set to 88200
    config.use_negotiated_latencies = 1;
  }
  char *hdr = msg_get_header(req, "Transport");
  if (!hdr)
    goto error;

  char *p;
  p = strstr(hdr, "control_port=");
  if (!p)
    goto error;
  p = strchr(p, '=') + 1;
  cport = atoi(p);

  p = strstr(hdr, "timing_port=");
  if (!p)
    goto error;
  p = strchr(p, '=') + 1;
  tport = atoi(p);

  //  rtsp_take_player();
  rtp_setup(&conn->local, &conn->remote, cport, tport, &lsport, &lcport, &ltport, conn);
  if (!lsport)
    goto error;
  char *q;
  p = strstr(hdr, "control_port=");
  if (p) {
    q = strchr(p, ';'); // get past the control port entry
    *p++ = 0;
    if (q++)
      strcat(hdr, q); // should unsplice the control port entry
  }
  p = strstr(hdr, "timing_port=");
  if (p) {
    q = strchr(p, ';'); // get past the timing port entry
    *p++ = 0;
    if (q++)
      strcat(hdr, q); // should unsplice the timing port entry
  }

  player_play(conn); // the thread better be 0

  char *resphdr = alloca(200);
  *resphdr = 0;
  sprintf(resphdr, "RTP/AVP/"
                   "UDP;unicast;interleaved=0-1;mode=record;control_port=%d;"
                   "timing_port=%d;server_"
                   "port=%d",
          lcport, ltport, lsport);

  msg_add_header(resp, "Transport", resphdr);

  msg_add_header(resp, "Session", "1");

  resp->respcode = 200;
  return;

error:
  warn("Error in setup request -- unlocking play lock on RTSP conversation thread %d.",
       conn->connection_number);
  playing_conn = NULL;
  pthread_mutex_unlock(&play_lock);
  resp->respcode = 451; // invalid arguments
}

static void handle_ignore(rtsp_conn_info *conn, rtsp_message *req, rtsp_message *resp) {
  debug(1, "Connection thread %d: IGNORE", conn->connection_number);
  resp->respcode = 200;
}

static void handle_set_parameter_parameter(rtsp_conn_info *conn, rtsp_message *req,
                                           rtsp_message *resp) {
  char *cp = req->content;
  int cp_left = req->contentlength;
  char *next;
  while (cp_left && cp) {
    next = nextline(cp, cp_left);
    cp_left -= next - cp;

    if (!strncmp(cp, "volume: ", 8)) {
      float volume = atof(cp + 8);
      debug(3, "AirPlay request to set volume to: %f.", volume);
      player_volume(volume, conn);
    } else
#ifdef CONFIG_METADATA
        if (!strncmp(cp, "progress: ", 10)) {
      char *progress = cp + 10;
      // debug(2, "progress: \"%s\"\n",
      //      progress); // rtpstampstart/rtpstampnow/rtpstampend 44100 per second
      send_ssnc_metadata('prgr', strdup(progress), strlen(progress), 1);
    } else
#endif
    {
      debug(1, "unrecognised parameter: \"%s\" (%d)\n", cp, strlen(cp));
    }
    cp = next;
  }
}

#ifdef CONFIG_METADATA
// Metadata is not used by shairport-sync.
// Instead we send all metadata to a fifo pipe, so that other apps can listen to
// the pipe and use the metadata.

// We use two 4-character codes to identify each piece of data and we send the
// data itself, if any,
// in base64 form.

// The first 4-character code, called the "type", is either:
//    'core' for all the regular metadadata coming from iTunes, etc., or
//    'ssnc' (for 'shairport-sync') for all metadata coming from Shairport Sync
//    itself, such as
//    start/end delimiters, etc.

// For 'core' metadata, the second 4-character code is the 4-character metadata
// code coming from
// iTunes etc.
// For 'ssnc' metadata, the second 4-character code is used to distinguish the
// messages.

// Cover art is not tagged in the same way as other metadata, it seems, so is
// sent as an 'ssnc' type
// metadata message with the code 'PICT'
// Here are the 'ssnc' codes defined so far:
//    'PICT' -- the payload is a picture, either a JPEG or a PNG. Check the
//    first few bytes to see
//    which.
//    'pbeg' -- play stream begin. No arguments
//    'pend' -- play stream end. No arguments
//    'pfls' -- play stream flush. No arguments
//    'prsm' -- play stream resume. No arguments
//    'pvol' -- play volume. The volume is sent as a string --
//    "airplay_volume,volume,lowest_volume,highest_volume"
//              volume, lowest_volume and highest_volume are given in dB.
//              The "airplay_volume" is what's sent to the player, and is from
//              0.00 down to -30.00,
//              with -144.00 meaning mute.
//              This is linear on the volume control slider of iTunes or iOS
//              AirPlay.
//    'prgr' -- progress -- this is metadata from AirPlay consisting of RTP
//    timestamps for the start
//    of the current play sequence, the current play point and the end of the
//    play sequence.
//              I guess the timestamps wrap at 2^32.
//    'mdst' -- a sequence of metadata is about to start; will have, as data,
//    the rtptime associated with the metadata, if available
//    'mden' -- a sequence of metadata has ended; will have, as data, the
//    rtptime associated with the metadata, if available
//    'pcst' -- a picture is about to be sent; will have, as data, the rtptime
//    associated with the picture, if available
//    'pcen' -- a picture has been sent; will have, as data, the rtptime
//    associated with the metadata, if available
//    'snam' -- A device -- e.g. "Joe's iPhone" -- has opened a play session.
//    Specifically, it's the "X-Apple-Client-Name" string
//    'snua' -- A "user agent" -- e.g. "iTunes/12..." -- has opened a play
//    session. Specifically, it's the "User-Agent" string
//    The next two two tokens are to facilitiate remote control of the source.
//    There is some information at http://nto.github.io/AirPlay.html about
//    remote control of the source.
//
//    'daid' -- this is the source's DACP-ID (if it has one -- it's not
//    guaranteed), useful if you want to remotely control the source. Use this
//    string to identify the source's remote control on the network.
//    'acre' -- this is the source's Active-Remote token, necessary if you want
//    to send commands to the source's remote control (if it has one).
//		`clip` -- the payload is the IP number of the client, i.e. the sender of audio.
//		Can be an IPv4 or an IPv6 number.
//		`dapo` -- the payload is the port number (as text) on the server to which remote
// control commands should be sent. It is 3689 for iTunes but varies for iOS devices.

//		A special sub-protocol is used for sending large data items over UDP
//    If the payload exceeded 4 MB, it is chunked using the following format:
//    "ssnc", "chnk", packet_ix, packet_counts, packet_tag, packet_type, chunked_data.
//    Notice that the number of items is different to the standard

// including a simple base64 encoder to minimise malloc/free activity

// From Stack Overflow, with thanks:
// http://stackoverflow.com/questions/342409/how-do-i-base64-encode-decode-in-c
// minor mods to make independent of C99.
// more significant changes make it not malloc memory
// needs to initialise the docoding table first

// add _so to end of name to avoid confusion with polarssl's implementation

static char encoding_table[] = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                                'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                                'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                                'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                                '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+', '/'};

static int mod_table[] = {0, 2, 1};

// pass in a pointer to the data, its length, a pointer to the output buffer and
// a pointer to an int
// containing its maximum length
// the actual length will be returned.

char *base64_encode_so(const unsigned char *data, size_t input_length, char *encoded_data,
                       size_t *output_length) {

  size_t calculated_output_length = 4 * ((input_length + 2) / 3);
  if (calculated_output_length > *output_length)
    return (NULL);
  *output_length = calculated_output_length;

  int i, j;
  for (i = 0, j = 0; i < input_length;) {

    uint32_t octet_a = i < input_length ? (unsigned char)data[i++] : 0;
    uint32_t octet_b = i < input_length ? (unsigned char)data[i++] : 0;
    uint32_t octet_c = i < input_length ? (unsigned char)data[i++] : 0;

    uint32_t triple = (octet_a << 0x10) + (octet_b << 0x08) + octet_c;

    encoded_data[j++] = encoding_table[(triple >> 3 * 6) & 0x3F];
    encoded_data[j++] = encoding_table[(triple >> 2 * 6) & 0x3F];
    encoded_data[j++] = encoding_table[(triple >> 1 * 6) & 0x3F];
    encoded_data[j++] = encoding_table[(triple >> 0 * 6) & 0x3F];
  }

  for (i = 0; i < mod_table[input_length % 3]; i++)
    encoded_data[*output_length - 1 - i] = '=';

  return encoded_data;
}

// with thanks!
//

static int fd = -1;
static int dirty = 0;
pc_queue metadata_queue;
static int metadata_sock = -1;
static struct sockaddr_in metadata_sockaddr;
static char *metadata_sockmsg;
#define metadata_queue_size 500
metadata_package metadata_queue_items[metadata_queue_size];

static pthread_t metadata_thread;

void metadata_create(void) {
  if (config.metadata_enabled == 0)
    return;

  // Unlike metadata pipe, socket is opened once and stays open,
  // so we can call it in create
  if (config.metadata_sockaddr && config.metadata_sockport) {
    metadata_sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (metadata_sock < 0) {
      debug(1, "Could not open metadata socket");
    } else {
      int buffer_size = METADATA_SNDBUF;
      setsockopt(metadata_sock, SOL_SOCKET, SO_SNDBUF, &buffer_size, sizeof(buffer_size));
      fcntl(fd, F_SETFL, O_NONBLOCK);
      bzero((char *)&metadata_sockaddr, sizeof(metadata_sockaddr));
      metadata_sockaddr.sin_family = AF_INET;
      metadata_sockaddr.sin_addr.s_addr = inet_addr(config.metadata_sockaddr);
      metadata_sockaddr.sin_port = htons(config.metadata_sockport);
      metadata_sockmsg = malloc(config.metadata_sockmsglength);
      if (metadata_sockmsg) {
        memset(metadata_sockmsg, 0, config.metadata_sockmsglength);
      } else {
        die("Could not malloc metadata socket buffer");
      }
    }
  }

  size_t pl = strlen(config.metadata_pipename) + 1;

  char *path = malloc(pl + 1);
  snprintf(path, pl + 1, "%s", config.metadata_pipename);

  if (mkfifo(path, 0644) && errno != EEXIST)
    die("Could not create metadata FIFO %s", path);

  free(path);
}

void metadata_open(void) {
  if (config.metadata_enabled == 0)
    return;

  size_t pl = strlen(config.metadata_pipename) + 1;

  char *path = malloc(pl + 1);
  snprintf(path, pl + 1, "%s", config.metadata_pipename);

  fd = open(path, O_WRONLY | O_NONBLOCK);
  // if (fd < 0)
  //    debug(1, "Could not open metadata FIFO %s. Will try again later.",
  //    path);

  free(path);
}

static void metadata_close(void) {
  close(fd);
  fd = -1;
}

void metadata_process(uint32_t type, uint32_t code, char *data, uint32_t length) {
  // debug(2, "Process metadata with type %x, code %x and length %u.", type, code, length);
  int ret;

  if (metadata_sock >= 0 && length < config.metadata_sockmsglength - 8) {
    char *ptr = metadata_sockmsg;
    uint32_t v;
    v = htonl(type);
    memcpy(ptr, &v, 4);
    ptr += 4;
    v = htonl(code);
    memcpy(ptr, &v, 4);
    ptr += 4;
    memcpy(ptr, data, length);
    sendto(metadata_sock, metadata_sockmsg, length + 8, 0, (struct sockaddr *)&metadata_sockaddr,
           sizeof(metadata_sockaddr));
  } else if (metadata_sock >= 0) {
    // send metadata in numbered chunks using the protocol:
    // ("ssnc", "chnk", packet_ix, packet_counts, packet_tag, packet_type, chunked_data)

    uint32_t chunk_ix = 0;
    uint32_t chunk_total = length / (config.metadata_sockmsglength - 24);
    if (chunk_total * (config.metadata_sockmsglength - 24) < length) {
      chunk_total++;
    }
    uint32_t remaining = length;
    uint32_t v;
    char *data_crsr = data;
    do {
      char *ptr = metadata_sockmsg;
      memcpy(ptr, "ssncchnk", 8);
      ptr += 8;
      v = htonl(chunk_ix);
      memcpy(ptr, &v, 4);
      ptr += 4;
      v = htonl(chunk_total);
      memcpy(ptr, &v, 4);
      ptr += 4;
      v = htonl(type);
      memcpy(ptr, &v, 4);
      ptr += 4;
      v = htonl(code);
      memcpy(ptr, &v, 4);
      ptr += 4;
      uint32_t datalen = remaining;
      if (datalen > config.metadata_sockmsglength - 24) {
        datalen = config.metadata_sockmsglength - 24;
      }
      memcpy(ptr, data_crsr, datalen);
      data_crsr += datalen;
      sendto(metadata_sock, metadata_sockmsg, datalen + 24, 0,
             (struct sockaddr *)&metadata_sockaddr, sizeof(metadata_sockaddr));
      chunk_ix++;
      remaining -= datalen;
      if (remaining == 0)
        break;
    } while (1);
  }

  // readers may go away and come back
  if (fd < 0)
    metadata_open();
  if (fd < 0)
    return;
  char thestring[1024];
  snprintf(thestring, 1024, "<item><type>%x</type><code>%x</code><length>%u</length>", type, code,
           length);
  ret = non_blocking_write(fd, thestring, strlen(thestring));
  if (ret < 0) {
    // debug(1,"metadata_process error %d exit 1",ret);
    return;
  }
  if ((data != NULL) && (length > 0)) {
    snprintf(thestring, 1024, "\n<data encoding=\"base64\">\n");
    ret = non_blocking_write(fd, thestring, strlen(thestring));
    if (ret < 0) {
      // debug(1,"metadata_process error %d exit 2",ret);
      return;
    }
    // here, we write the data in base64 form using our nice base64 encoder
    // but, we break it into lines of 76 output characters, except for the last
    // one.
    // thus, we send groups of (76/4)*3 =  57 bytes to the encoder at a time
    size_t remaining_count = length;
    char *remaining_data = data;
    size_t towrite_count;
    char outbuf[76];
    while ((remaining_count) && (ret >= 0)) {
      size_t towrite_count = remaining_count;
      if (towrite_count > 57)
        towrite_count = 57;
      size_t outbuf_size = 76; // size of output buffer on entry, length of result on exit
      if (base64_encode_so((unsigned char *)remaining_data, towrite_count, outbuf, &outbuf_size) ==
          NULL)
        debug(1, "Error encoding base64 data.");
      // debug(1,"Remaining count: %d ret: %d, outbuf_size:
      // %d.",remaining_count,ret,outbuf_size);
      ret = non_blocking_write(fd, outbuf, outbuf_size);
      if (ret < 0) {
        // debug(1,"metadata_process error %d exit 3",ret);
        return;
      }
      remaining_data += towrite_count;
      remaining_count -= towrite_count;
    }
    snprintf(thestring, 1024, "</data>");
    ret = non_blocking_write(fd, thestring, strlen(thestring));
    if (ret < 0) {
      // debug(1,"metadata_process error %d exit 4",ret);
      return;
    }
  }
  snprintf(thestring, 1024, "</item>\n");
  ret = non_blocking_write(fd, thestring, strlen(thestring));
  if (ret < 0) {
    // debug(1,"metadata_process error %d exit 5",ret);
    return;
  }
}

void *metadata_thread_function(void *ignore) {
  metadata_create();
  metadata_package pack;
  while (1) {
    pc_queue_get_item(&metadata_queue, &pack);
    if (config.metadata_enabled)
      metadata_process(pack.type, pack.code, pack.data, pack.length);
    if (pack.carrier)
      msg_free(pack.carrier); // release the message
    else if (pack.data)
      free(pack.data);
  }
  pthread_exit(NULL);
}

void metadata_init(void) {
  // create a pc_queue for passing information to a threaded metadata handler
  pc_queue_init(&metadata_queue, (char *)&metadata_queue_items, sizeof(metadata_package),
                metadata_queue_size);
  int ret = pthread_create(&metadata_thread, NULL, metadata_thread_function, NULL);
  if (ret)
    debug(1, "Failed to create metadata thread!");
}

int send_metadata(uint32_t type, uint32_t code, char *data, uint32_t length, rtsp_message *carrier,
                  int block) {

  // parameters: type, code, pointer to data or NULL, length of data or NULL,
  // the rtsp_message or
  // NULL
  // the rtsp_message is sent for 'core' messages, because it contains the data
  // and must not be
  // freed until the data has been read. So, it is passed to send_metadata to be
  // retained,
  // sent to the thread where metadata is processed and released (and probably
  // freed).

  // The rtsp_message is also sent for certain non-'core' messages.

  // The reading of the parameters is a bit complex
  // If the rtsp_message field is non-null, then it represents an rtsp_message
  // which should be freed
  // in the thread handler when the parameter pointed to by the pointer and
  // specified by the length
  // is finished with
  // If the rtsp_message is NULL, then if the pointer is non-null, it points to
  // a malloc'ed block
  // and should be freed when the thread is finished with it. The length of the
  // data in the block is
  // given in length
  // If the rtsp_message is NULL and the pointer is also NULL, nothing further
  // is done.

  metadata_package pack;
  pack.type = type;
  pack.code = code;
  pack.data = data;
  pack.length = length;
  if (carrier)
    msg_retain(carrier);
  pack.carrier = carrier;
  int rc = pc_queue_add_item(&metadata_queue, &pack, block);
  if ((rc == EBUSY) && (carrier))
    msg_free(carrier);
  if (rc == EBUSY)
    warn("Metadata queue is busy, dropping message of type 0x%08X, code 0x%08X.", type, code);
  return rc;
}

static void handle_set_parameter_metadata(rtsp_conn_info *conn, rtsp_message *req,
                                          rtsp_message *resp) {
  char *cp = req->content;
  int cl = req->contentlength;

  unsigned int off = 8;

  uint32_t itag, vl;
  while (off < cl) {
    // pick up the metadata tag as an unsigned longint
    memcpy(&itag, (uint32_t *)(cp + off), sizeof(uint32_t)); /* can be misaligned, thus memcpy */
    itag = ntohl(itag);
    off += sizeof(uint32_t);

    // pick up the length of the data
    memcpy(&vl, (uint32_t *)(cp + off), sizeof(uint32_t)); /* can be misaligned, thus memcpy */
    vl = ntohl(vl);
    off += sizeof(uint32_t);

    // pass the data over
    if (vl == 0)
      send_metadata('core', itag, NULL, 0, NULL, 1);
    else
      send_metadata('core', itag, (char *)(cp + off), vl, req, 1);

    // move on to the next item
    off += vl;
  }
}

#endif

static void handle_get_parameter(rtsp_conn_info *conn, rtsp_message *req, rtsp_message *resp) {
  debug(3, "Connection %d: GET_PARAMETER", conn->connection_number);
  resp->respcode = 200;
}

static void handle_set_parameter(rtsp_conn_info *conn, rtsp_message *req, rtsp_message *resp) {
  debug(3, "Connection %d: SET_PARAMETER", conn->connection_number);
  // if (!req->contentlength)
  //    debug(1, "received empty SET_PARAMETER request.");

  // debug_print_msg_headers(1,req);

  char *ct = msg_get_header(req, "Content-Type");

  if (ct) {
// debug(2, "SET_PARAMETER Content-Type:\"%s\".", ct);

#ifdef CONFIG_METADATA
    // It seems that the rtptime of the message is used as a kind of an ID that
    // can be used
    // to link items of metadata, including pictures, that refer to the same
    // entity.
    // If they refer to the same item, they have the same rtptime.
    // So we send the rtptime before and after both the metadata items and the
    // picture item
    // get the rtptime
    char *p = NULL;
    char *hdr = msg_get_header(req, "RTP-Info");

    if (hdr) {
      p = strstr(hdr, "rtptime=");
      if (p) {
        p = strchr(p, '=');
      }
    }

    // not all items have RTP-time stuff in them, which is okay

    if (!strncmp(ct, "application/x-dmap-tagged", 25)) {
      debug(3, "received metadata tags in SET_PARAMETER request.");
      if (p == NULL)
        debug(1, "Missing RTP-Time info for metadata");
      if (p)
        send_metadata('ssnc', 'mdst', p + 1, strlen(p + 1), req, 1); // metadata starting
      else
        send_metadata('ssnc', 'mdst', NULL, 0, NULL,
                      0); // metadata starting, if rtptime is not available

      handle_set_parameter_metadata(conn, req, resp);

      if (p)
        send_metadata('ssnc', 'mden', p + 1, strlen(p + 1), req, 1); // metadata ending
      else
        send_metadata('ssnc', 'mden', NULL, 0, NULL,
                      0); // metadata starting, if rtptime is not available

    } else if (!strncmp(ct, "image", 5)) {
      // Some server simply ignore the md field from the TXT record. If The
      // config says 'please, do not include any cover art', we are polite and
      // do not write them to the pipe.
      if (config.get_coverart) {
        // debug(1, "received image in SET_PARAMETER request.");
        // note: the image/type tag isn't reliable, so it's not being sent
        // -- best look at the first few bytes of the image
        if (p == NULL)
          debug(1, "Missing RTP-Time info for picture item");
        if (p)
          send_metadata('ssnc', 'pcst', p + 1, strlen(p + 1), req, 1); // picture starting
        else
          send_metadata('ssnc', 'pcst', NULL, 0, NULL,
                        0); // picture starting, if rtptime is not available

        send_metadata('ssnc', 'PICT', req->content, req->contentlength, req, 1);

        if (p)
          send_metadata('ssnc', 'pcen', p + 1, strlen(p + 1), req, 1); // picture ending
        else
          send_metadata('ssnc', 'pcen', NULL, 0, NULL,
                        0); // picture ending, if rtptime is not available
      } else {
        debug(1, "Ignore received picture item (include_cover_art = no).");
      }
    } else
#endif
        if (!strncmp(ct, "text/parameters", 15)) {
      // debug(2, "received parameters in SET_PARAMETER request.");
      handle_set_parameter_parameter(conn, req, resp); // this could be volume or progress
    } else {
      debug(1, "received unknown Content-Type \"%s\" in SET_PARAMETER request.", ct);
    }
  } else {
    debug(1, "missing Content-Type header in SET_PARAMETER request.");
  }
  resp->respcode = 200;
}

static void handle_announce(rtsp_conn_info *conn, rtsp_message *req, rtsp_message *resp) {
  debug(3, "Connection %d: ANNOUNCE", conn->connection_number);
  int have_the_player = 0;

  // interrupt session if permitted
  if (pthread_mutex_trylock(&play_lock) == 0) {
    have_the_player = 1;
  } else {
    int should_wait = 0;

    if (!playing_conn)
      die("Non existent playing_conn with play_lock enabled.");
    debug(1, "RTSP Conversation thread %d already playing when asked by thread %d.",
          playing_conn->connection_number, conn->connection_number);
    if (playing_conn->stop) {
      debug(1, "Playing connection is already shutting down; waiting for it...");
      should_wait = 1;
    } else if (config.allow_session_interruption == 1) {
      // some other thread has the player ... ask it to relinquish the thread
      debug(1, "ANNOUNCE: playing connection %d being interrupted by connection %d.",
            playing_conn->connection_number, conn->connection_number);
      if (playing_conn == conn) {
        debug(1, "ANNOUNCE asking to stop itself.");
      } else {
        playing_conn->stop = 1;
        memory_barrier();
        pthread_kill(playing_conn->thread, SIGUSR1);
        should_wait = 1;
      }
    }

    if (should_wait) {
      usleep(1000000); // here, it is possible for other connections to come in and nab the player.
      debug(1, "Try to get the player now");
    }
    if (pthread_mutex_trylock(&play_lock) == 0)
      have_the_player = 1;
    else
      debug(1, "ANNOUNCE failed to get the player");
  }

  if (have_the_player) {
    playing_conn = conn; // the present connection is now playing
    debug(3, "RTSP conversation thread %d has acquired play lock.", conn->connection_number);
    resp->respcode = 456; // 456 - Header Field Not Valid for Resource
    char *paesiv = NULL;
    char *prsaaeskey = NULL;
    char *pfmtp = NULL;
    char *cp = req->content;
    int cp_left = req->contentlength;
    char *next;
    while (cp_left && cp) {
      next = nextline(cp, cp_left);
      cp_left -= next - cp;

      if (!strncmp(cp, "a=fmtp:", 7))
        pfmtp = cp + 7;

      if (!strncmp(cp, "a=aesiv:", 8))
        paesiv = cp + 8;

      if (!strncmp(cp, "a=rsaaeskey:", 12))
        prsaaeskey = cp + 12;

      cp = next;
    }

    if ((paesiv == NULL) && (prsaaeskey == NULL)) {
      // debug(1,"Unencrypted session requested?");
      conn->stream.encrypted = 0;
    } else {
      conn->stream.encrypted = 1;
      // debug(1,"Encrypted session requested");
    }

    if (!pfmtp) {
      warn("FMTP params missing from the following ANNOUNCE message:");
      // print each line of the request content
      // the problem is that nextline has replace all returns, newlines, etc. by
      // NULLs
      char *cp = req->content;
      int cp_left = req->contentlength;
      while (cp_left > 1) {
        if (strlen(cp) != 0)
          warn("    %s", cp);
        cp += strlen(cp) + 1;
        cp_left -= strlen(cp) + 1;
      }
      goto out;
    }

    if (conn->stream.encrypted) {
      int len, keylen;
      uint8_t *aesiv = base64_dec(paesiv, &len);
      if (len != 16) {
        warn("client announced aeskey of %d bytes, wanted 16", len);
        free(aesiv);
        goto out;
      }
      memcpy(conn->stream.aesiv, aesiv, 16);
      free(aesiv);

      uint8_t *rsaaeskey = base64_dec(prsaaeskey, &len);
      uint8_t *aeskey = rsa_apply(rsaaeskey, len, &keylen, RSA_MODE_KEY);
      free(rsaaeskey);
      if (keylen != 16) {
        warn("client announced rsaaeskey of %d bytes, wanted 16", keylen);
        free(aeskey);
        goto out;
      }
      memcpy(conn->stream.aeskey, aeskey, 16);
      free(aeskey);
    }
    int i;
    for (i = 0; i < sizeof(conn->stream.fmtp) / sizeof(conn->stream.fmtp[0]); i++)
      conn->stream.fmtp[i] = atoi(strsep(&pfmtp, " \t"));
    // here we should check the sanity ot the fmtp values
    // for (i = 0; i < sizeof(conn->stream.fmtp) / sizeof(conn->stream.fmtp[0]); i++)
    //  debug(1,"  fmtp[%2d] is: %10d",i,conn->stream.fmtp[i]);

    char *hdr = msg_get_header(req, "X-Apple-Client-Name");
    if (hdr) {
      debug(1, "Play connection from device named \"%s\" on RTSP conversation thread %d.", hdr,
            conn->connection_number);
#ifdef CONFIG_METADATA
      send_metadata('ssnc', 'snam', hdr, strlen(hdr), req, 1);
#endif
    }
    hdr = msg_get_header(req, "User-Agent");
    if (hdr) {
      debug(1, "Play connection from user agent \"%s\" on RTSP conversation thread %d.", hdr,
            conn->connection_number);
#ifdef CONFIG_METADATA
      send_metadata('ssnc', 'snua', hdr, strlen(hdr), req, 1);
#endif
    }
    resp->respcode = 200;
  } else {
    resp->respcode = 453;
    debug(1, "Already playing.");
  }

out:
  if (resp->respcode != 200 && resp->respcode != 453) {
    debug(1, "Error in handling ANNOUNCE on conversation thread %d. Unlocking the play lock.",
          conn->connection_number);
    playing_conn = NULL;
    pthread_mutex_unlock(&play_lock);
  }
}

static struct method_handler {
  char *method;
  void (*handler)(rtsp_conn_info *conn, rtsp_message *req, rtsp_message *resp);
} method_handlers[] = {{"OPTIONS", handle_options},
                       {"ANNOUNCE", handle_announce},
                       {"FLUSH", handle_flush},
                       {"TEARDOWN", handle_teardown},
                       {"SETUP", handle_setup},
                       {"GET_PARAMETER", handle_get_parameter},
                       {"SET_PARAMETER", handle_set_parameter},
                       {"RECORD", handle_record},
                       {NULL, NULL}};

static void apple_challenge(int fd, rtsp_message *req, rtsp_message *resp) {
  char *hdr = msg_get_header(req, "Apple-Challenge");
  if (!hdr)
    return;

  SOCKADDR fdsa;
  socklen_t sa_len = sizeof(fdsa);
  getsockname(fd, (struct sockaddr *)&fdsa, &sa_len);

  int chall_len;
  uint8_t *chall = base64_dec(hdr, &chall_len);
  if (chall == NULL)
    die("null chall in apple_challenge");
  uint8_t buf[48], *bp = buf;
  int i;
  memset(buf, 0, sizeof(buf));

  if (chall_len > 16) {
    warn("oversized Apple-Challenge!");
    free(chall);
    return;
  }
  memcpy(bp, chall, chall_len);
  free(chall);
  bp += chall_len;

#ifdef AF_INET6
  if (fdsa.SAFAMILY == AF_INET6) {
    struct sockaddr_in6 *sa6 = (struct sockaddr_in6 *)(&fdsa);
    memcpy(bp, sa6->sin6_addr.s6_addr, 16);
    bp += 16;
  } else
#endif
  {
    struct sockaddr_in *sa = (struct sockaddr_in *)(&fdsa);
    memcpy(bp, &sa->sin_addr.s_addr, 4);
    bp += 4;
  }

  for (i = 0; i < 6; i++)
    *bp++ = config.hw_addr[i];

  int buflen, resplen;
  buflen = bp - buf;
  if (buflen < 0x20)
    buflen = 0x20;

  uint8_t *challresp = rsa_apply(buf, buflen, &resplen, RSA_MODE_AUTH);
  char *encoded = base64_enc(challresp, resplen);
  if (encoded == NULL)
    die("could not allocate memory for \"encoded\"");
  // strip the padding.
  char *padding = strchr(encoded, '=');
  if (padding)
    *padding = 0;

  msg_add_header(resp, "Apple-Response", encoded);
  free(challresp);
  free(encoded);
}

static char *make_nonce(void) {
  uint8_t random[8];
  int fd = open("/dev/random", O_RDONLY);
  if (fd < 0)
    die("could not open /dev/random!");
  int ignore = read(fd, random, sizeof(random));
  close(fd);
  return base64_enc(random, 8);
}

static int rtsp_auth(char **nonce, rtsp_message *req, rtsp_message *resp) {

  if (!config.password)
    return 0;
  if (!*nonce) {
    *nonce = make_nonce();
    goto authenticate;
  }

  char *hdr = msg_get_header(req, "Authorization");
  if (!hdr || strncmp(hdr, "Digest ", 7))
    goto authenticate;

  char *realm = strstr(hdr, "realm=\"");
  char *username = strstr(hdr, "username=\"");
  char *response = strstr(hdr, "response=\"");
  char *uri = strstr(hdr, "uri=\"");

  if (!realm || !username || !response || !uri)
    goto authenticate;

  char *quote;
  realm = strchr(realm, '"') + 1;
  if (!(quote = strchr(realm, '"')))
    goto authenticate;
  *quote = 0;
  username = strchr(username, '"') + 1;
  if (!(quote = strchr(username, '"')))
    goto authenticate;
  *quote = 0;
  response = strchr(response, '"') + 1;
  if (!(quote = strchr(response, '"')))
    goto authenticate;
  *quote = 0;
  uri = strchr(uri, '"') + 1;
  if (!(quote = strchr(uri, '"')))
    goto authenticate;
  *quote = 0;

  uint8_t digest_urp[16], digest_mu[16], digest_total[16];

#ifdef HAVE_LIBSSL
  MD5_CTX ctx;

  MD5_Init(&ctx);
  MD5_Update(&ctx, username, strlen(username));
  MD5_Update(&ctx, ":", 1);
  MD5_Update(&ctx, realm, strlen(realm));
  MD5_Update(&ctx, ":", 1);
  MD5_Update(&ctx, config.password, strlen(config.password));
  MD5_Final(digest_urp, &ctx);
  MD5_Init(&ctx);
  MD5_Update(&ctx, req->method, strlen(req->method));
  MD5_Update(&ctx, ":", 1);
  MD5_Update(&ctx, uri, strlen(uri));
  MD5_Final(digest_mu, &ctx);
#endif

#ifdef HAVE_LIBMBEDTLS
  mbedtls_md5_context tctx;
  mbedtls_md5_starts(&tctx);
  mbedtls_md5_update(&tctx, (const unsigned char *)username, strlen(username));
  mbedtls_md5_update(&tctx, (unsigned char *)":", 1);
  mbedtls_md5_update(&tctx, (const unsigned char *)realm, strlen(realm));
  mbedtls_md5_update(&tctx, (unsigned char *)":", 1);
  mbedtls_md5_update(&tctx, (const unsigned char *)config.password, strlen(config.password));
  mbedtls_md5_finish(&tctx, digest_urp);
  mbedtls_md5_starts(&tctx);
  mbedtls_md5_update(&tctx, (const unsigned char *)req->method, strlen(req->method));
  mbedtls_md5_update(&tctx, (unsigned char *)":", 1);
  mbedtls_md5_update(&tctx, (const unsigned char *)uri, strlen(uri));
  mbedtls_md5_finish(&tctx, digest_mu);
#endif

#ifdef HAVE_LIBPOLARSSL
  md5_context tctx;
  md5_starts(&tctx);
  md5_update(&tctx, (const unsigned char *)username, strlen(username));
  md5_update(&tctx, (unsigned char *)":", 1);
  md5_update(&tctx, (const unsigned char *)realm, strlen(realm));
  md5_update(&tctx, (unsigned char *)":", 1);
  md5_update(&tctx, (const unsigned char *)config.password, strlen(config.password));
  md5_finish(&tctx, digest_urp);
  md5_starts(&tctx);
  md5_update(&tctx, (const unsigned char *)req->method, strlen(req->method));
  md5_update(&tctx, (unsigned char *)":", 1);
  md5_update(&tctx, (const unsigned char *)uri, strlen(uri));
  md5_finish(&tctx, digest_mu);
#endif

  int i;
  unsigned char buf[33];
  for (i = 0; i < 16; i++)
    sprintf((char *)buf + 2 * i, "%02x", digest_urp[i]);

#ifdef HAVE_LIBSSL
  MD5_Init(&ctx);
  MD5_Update(&ctx, buf, 32);
  MD5_Update(&ctx, ":", 1);
  MD5_Update(&ctx, *nonce, strlen(*nonce));
  MD5_Update(&ctx, ":", 1);
  for (i = 0; i < 16; i++)
    sprintf((char *)buf + 2 * i, "%02x", digest_mu[i]);
  MD5_Update(&ctx, buf, 32);
  MD5_Final(digest_total, &ctx);
#endif

#ifdef HAVE_LIBMBEDTLS
  mbedtls_md5_starts(&tctx);
  mbedtls_md5_update(&tctx, buf, 32);
  mbedtls_md5_update(&tctx, (unsigned char *)":", 1);
  mbedtls_md5_update(&tctx, (const unsigned char *)*nonce, strlen(*nonce));
  mbedtls_md5_update(&tctx, (unsigned char *)":", 1);
  for (i = 0; i < 16; i++)
    sprintf((char *)buf + 2 * i, "%02x", digest_mu[i]);
  mbedtls_md5_update(&tctx, buf, 32);
  mbedtls_md5_finish(&tctx, digest_total);
#endif

#ifdef HAVE_LIBPOLARSSL
  md5_starts(&tctx);
  md5_update(&tctx, buf, 32);
  md5_update(&tctx, (unsigned char *)":", 1);
  md5_update(&tctx, (const unsigned char *)*nonce, strlen(*nonce));
  md5_update(&tctx, (unsigned char *)":", 1);
  for (i = 0; i < 16; i++)
    sprintf((char *)buf + 2 * i, "%02x", digest_mu[i]);
  md5_update(&tctx, buf, 32);
  md5_finish(&tctx, digest_total);
#endif

  for (i = 0; i < 16; i++)
    sprintf((char *)buf + 2 * i, "%02x", digest_total[i]);

  if (!strcmp(response, (const char *)buf))
    return 0;
  warn("Password authorization failed.");

authenticate:
  resp->respcode = 401;
  int hdrlen = strlen(*nonce) + 40;
  char *authhdr = malloc(hdrlen);
  snprintf(authhdr, hdrlen, "Digest realm=\"raop\", nonce=\"%s\"", *nonce);
  msg_add_header(resp, "WWW-Authenticate", authhdr);
  free(authhdr);
  return 1;
}

static void *rtsp_conversation_thread_func(void *pconn) {
  rtsp_conn_info *conn = pconn;

  rtp_initialise(conn);

  rtsp_message *req, *resp;
  char *hdr, *auth_nonce = NULL;

  enum rtsp_read_request_response reply;

  while (conn->stop == 0) {
    reply = rtsp_read_request(conn, &req);
    if (reply == rtsp_read_request_response_ok) {
      debug(3, "RTSP thread %d received an RTSP Packet of type \"%s\":", conn->connection_number,
            req->method),
          debug_print_msg_headers(3, req);
      resp = msg_init();
      resp->respcode = 400;

      apple_challenge(conn->fd, req, resp);
      hdr = msg_get_header(req, "CSeq");
      if (hdr)
        msg_add_header(resp, "CSeq", hdr);
      //      msg_add_header(resp, "Audio-Jack-Status", "connected; type=analog");
      msg_add_header(resp, "Server", "AirTunes/105.1");

      if ((conn->authorized == 1) || (rtsp_auth(&auth_nonce, req, resp)) == 0) {
        conn->authorized = 1; // it must have been authorized or didn't need a password
        struct method_handler *mh;
        int method_selected = 0;
        for (mh = method_handlers; mh->method; mh++) {
          if (!strcmp(mh->method, req->method)) {
            method_selected = 1;
            mh->handler(conn, req, resp);
            break;
          }
        }
        if (method_selected == 0)
          debug(1, "RTSP thread %d: Unrecognised and unhandled rtsp request \"%s\".",
                conn->connection_number, req->method);
      }
      debug(3, "RTSP thread %d: RTSP Response:", conn->connection_number);
      debug_print_msg_headers(3, resp);
      fd_set writefds;
      FD_ZERO(&writefds);
      FD_SET(conn->fd, &writefds);
      do {
        memory_barrier();
      } while (conn->stop == 0 &&
               pselect(conn->fd + 1, NULL, &writefds, NULL, NULL, &pselect_sigset) <= 0);
      if (conn->stop == 0) {
        msg_write_response(conn->fd, resp);
      }
      msg_free(req);
      msg_free(resp);
    } else {
      if ((reply == rtsp_read_request_response_immediate_shutdown_requested) ||
          (reply == rtsp_read_request_response_channel_closed)) {
        debug(3, "Synchronously terminate playing thread of RTSP conversation thread %d.",
              conn->connection_number);
        player_stop(conn);
        debug(3, "Successful termination of playing thread of RTSP conversation thread %d.",
              conn->connection_number);
        debug(3, "Request termination of RTSP conversation thread %d.", conn->connection_number);
        conn->stop = 1;
      } else {
        debug(1, "rtsp_read_request error %d, packet ignored.", (int)reply);
      }
    }
  }

  if (conn->fd > 0)
    close(conn->fd);
  if (auth_nonce)
    free(auth_nonce);
  rtp_terminate(conn);
  if (playing_conn == conn) {
    debug(3, "Unlocking play lock on RTSP conversation thread %d.", conn->connection_number);
    playing_conn = NULL;
    pthread_mutex_unlock(&play_lock);
  }
  debug(1, "RTSP conversation thread %d terminated.", conn->connection_number);
  //  please_shutdown = 0;
  conn->running = 0;
  return NULL;
}

// this function is not thread safe.
static const char *format_address(struct sockaddr *fsa) {
  static char string[INETx_ADDRSTRLEN];
  void *addr;
#ifdef AF_INET6
  if (fsa->sa_family == AF_INET6) {
    struct sockaddr_in6 *sa6 = (struct sockaddr_in6 *)(fsa);
    addr = &(sa6->sin6_addr);
  } else
#endif
  {
    struct sockaddr_in *sa = (struct sockaddr_in *)(fsa);
    addr = &(sa->sin_addr);
  }
  return inet_ntop(fsa->sa_family, addr, string, sizeof(string));
}

void rtsp_listen_loop(void) {
  struct addrinfo hints, *info, *p;
  char portstr[6];
  int *sockfd = NULL;
  int nsock = 0;
  int i, ret;

  playing_conn = NULL; // the data structure representing the connection that has the player.

  memset(&hints, 0, sizeof(hints));
  hints.ai_family = AF_UNSPEC;
  hints.ai_socktype = SOCK_STREAM;
  hints.ai_flags = AI_PASSIVE;

  snprintf(portstr, 6, "%d", config.port);

  // debug(1,"listen socket port request is \"%s\".",portstr);

  ret = getaddrinfo(NULL, portstr, &hints, &info);
  if (ret) {
    die("getaddrinfo failed: %s", gai_strerror(ret));
  }

  for (p = info; p; p = p->ai_next) {
    ret = 0;
    int fd = socket(p->ai_family, p->ai_socktype, IPPROTO_TCP);
    int yes = 1;

    // Handle socket open failures if protocol unavailable (or IPV6 not handled)
    if (fd == -1) {
      // debug(1, "Failed to get socket: fam=%d, %s\n", p->ai_family,
      // strerror(errno));
      continue;
    }
    // Set the RTSP socket to close on exec() of child processes
    // otherwise background run_this_before_play_begins or run_this_after_play_ends commands
    // that are sleeping prevent the daemon from being restarted because
    // the listening RTSP port is still in use.
    // See: https://github.com/mikebrady/shairport-sync/issues/329
    fcntl(fd, F_SETFD, FD_CLOEXEC);
    ret = setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));

#ifdef IPV6_V6ONLY
    // some systems don't support v4 access on v6 sockets, but some do.
    // since we need to account for two sockets we might as well
    // always.
    if (p->ai_family == AF_INET6) {
      ret |= setsockopt(fd, IPPROTO_IPV6, IPV6_V6ONLY, &yes, sizeof(yes));
    }
#endif

    if (!ret)
      ret = bind(fd, p->ai_addr, p->ai_addrlen);

    // one of the address families will fail on some systems that
    // report its availability. do not complain.

    if (ret) {
      char *family;
#ifdef AF_INET6
      if (p->ai_family == AF_INET6) {
        family = "IPv6";
      } else
#endif
        family = "IPv4";
      debug(1, "Unable to listen on %s port %d. The error is: \"%s\".", family, config.port,
            strerror(errno));
      continue;
    }

    listen(fd, 5);
    nsock++;
    sockfd = realloc(sockfd, nsock * sizeof(int));
    sockfd[nsock - 1] = fd;
  }

  freeaddrinfo(info);

  if (!nsock)
    die("Could not establish a service on port %d -- program terminating. Is another instance of "
        "Shairport Sync running on this device?",
        config.port);

  int maxfd = -1;
  fd_set fds;
  FD_ZERO(&fds);
  for (i = 0; i < nsock; i++) {
    if (sockfd[i] > maxfd)
      maxfd = sockfd[i];
  }

  mdns_register();

  // printf("Listening for connections.");
  // shairport_startup_complete();

  int acceptfd;
  struct timeval tv;
  while (1) {
    tv.tv_sec = 300;
    tv.tv_usec = 0;

    for (i = 0; i < nsock; i++)
      FD_SET(sockfd[i], &fds);

    ret = select(maxfd + 1, &fds, 0, 0, &tv);
    if (ret < 0) {
      if (errno == EINTR)
        continue;
      break;
    }

    cleanup_threads();

    acceptfd = -1;
    for (i = 0; i < nsock; i++) {
      if (FD_ISSET(sockfd[i], &fds)) {
        acceptfd = sockfd[i];
        break;
      }
    }
    if (acceptfd < 0) // timeout
      continue;

    rtsp_conn_info *conn = malloc(sizeof(rtsp_conn_info));
    if (conn == 0)
      die("Couldn't allocate memory for an rtsp_conn_info record.");
    memset(conn, 0, sizeof(rtsp_conn_info));
    conn->connection_number = RTSP_connection_index++;
    socklen_t slen = sizeof(conn->remote);

    conn->fd = accept(acceptfd, (struct sockaddr *)&conn->remote, &slen);
    if (conn->fd < 0) {
      debug(1, "New RTSP connection on port %d not accepted:", config.port);
      perror("failed to accept connection");
      free(conn);
    } else {
      SOCKADDR *local_info = (SOCKADDR *)&conn->local;
      socklen_t size_of_reply = sizeof(*local_info);
      memset(local_info, 0, sizeof(SOCKADDR));
      if (getsockname(conn->fd, (struct sockaddr *)local_info, &size_of_reply) == 0) {

        // IPv4:
        if (local_info->SAFAMILY == AF_INET) {
          char ip4[INET_ADDRSTRLEN];        // space to hold the IPv4 string
          char remote_ip4[INET_ADDRSTRLEN]; // space to hold the IPv4 string
          struct sockaddr_in *sa = (struct sockaddr_in *)local_info;
          inet_ntop(AF_INET, &(sa->sin_addr), ip4, INET_ADDRSTRLEN);
          unsigned short int tport = ntohs(sa->sin_port);
          sa = (struct sockaddr_in *)&conn->remote;
          inet_ntop(AF_INET, &(sa->sin_addr), remote_ip4, INET_ADDRSTRLEN);
          unsigned short int rport = ntohs(sa->sin_port);
#ifdef CONFIG_METADATA
          send_ssnc_metadata('clip', strdup(remote_ip4), strlen(remote_ip4), 1);
          send_ssnc_metadata('svip', strdup(ip4), strlen(ip4), 1);
#endif
          debug(1, "New RTSP connection from %s:%u to self at %s:%u on conversation thread %d.",
                remote_ip4, rport, ip4, tport, conn->connection_number);
        }
#ifdef AF_INET6
        if (local_info->SAFAMILY == AF_INET6) {
          // IPv6:

          char ip6[INET6_ADDRSTRLEN];        // space to hold the IPv6 string
          char remote_ip6[INET6_ADDRSTRLEN]; // space to hold the IPv6 string
          struct sockaddr_in6 *sa6 =
              (struct sockaddr_in6 *)local_info; // pretend this is loaded with something
          inet_ntop(AF_INET6, &(sa6->sin6_addr), ip6, INET6_ADDRSTRLEN);
          u_int16_t tport = ntohs(sa6->sin6_port);

          sa6 = (struct sockaddr_in6 *)&conn->remote; // pretend this is loaded with something
          inet_ntop(AF_INET6, &(sa6->sin6_addr), remote_ip6, INET6_ADDRSTRLEN);
          u_int16_t rport = ntohs(sa6->sin6_port);
#ifdef CONFIG_METADATA
          send_ssnc_metadata('clip', strdup(remote_ip6), strlen(remote_ip6), 1);
          send_ssnc_metadata('svip', strdup(ip6), strlen(ip6), 1);
#endif
          debug(1, "New RTSP connection from [%s]:%u to self at [%s]:%u on conversation thread %d.",
                remote_ip6, rport, ip6, tport, conn->connection_number);
        }
#endif

      } else {
        debug(1, "Error figuring out Shairport Sync's own IP number.");
      }
      //      usleep(500000);
      //      pthread_t rtsp_conversation_thread;
      //      conn->thread = rtsp_conversation_thread;
      //      conn->stop = 0; // record's memory has been zeroed
      //      conn->authorized = 0; // record's memory has been zeroed
      fcntl(conn->fd, F_SETFL, O_NONBLOCK);

      ret = pthread_create(&conn->thread, NULL, rtsp_conversation_thread_func,
                           conn); // also acts as a memory barrier
      if (ret)
        die("Failed to create RTSP receiver thread %d!", conn->connection_number);
      debug(3, "Successfully created RTSP receiver thread %d.", conn->connection_number);
      conn->running = 1; // this must happen before the thread is tracked
      track_thread(conn);
    }
  }
  perror("select");
  die("fell out of the RTSP select loop");
}
