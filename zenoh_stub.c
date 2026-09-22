#include <stdint.h>
#include <stdlib.h>

#include <moonbit.h>
#include <zenoh.h>

typedef struct {
  z_owned_session_t session;
  int closed;
} zenoh_mbt_session_t;

static void zenoh_mbt_session_finalize(void *payload);

void *zenoh_mbt_session_open(void) {
  z_owned_config_t config;
  if (z_config_default(&config) < 0) {
    abort();
  }

  zenoh_mbt_session_t *session = moonbit_make_external_object(
      zenoh_mbt_session_finalize, sizeof(*session));

  if (z_open(&session->session, z_config_move(&config), NULL) < 0) {
    abort();
  }
  session->closed = 0;
  return session;
}

int32_t zenoh_mbt_session_close(void *session) {
  if (session == NULL) {
    return -1;
  }

  zenoh_mbt_session_t *owned = session;
  if (owned->closed) {
    return 0;
  }

  z_close_options_t options;
  z_close_options_default(&options);
  z_result_t result = z_close(
      z_session_loan_mut(&owned->session), &options);
  z_session_drop(z_session_move(&owned->session));
  owned->closed = 1;
  return (int32_t)result;
}

static void zenoh_mbt_session_finalize(void *payload) {
  zenoh_mbt_session_close(payload);
}

static size_t utf8_width(uint32_t codepoint) {
  if (codepoint <= 0x7f) {
    return 1;
  }
  if (codepoint <= 0x7ff) {
    return 2;
  }
  if (codepoint <= 0xffff) {
    return 3;
  }
  return 4;
}

static char *moon_string_to_utf8(moonbit_string_t string) {
  size_t length = (size_t)Moonbit_array_length(string);
  size_t output_length = 0;
  for (size_t i = 0; i < length; i++) {
    uint32_t codepoint = string[i];
    if (codepoint >= 0xd800 && codepoint <= 0xdbff && i + 1 < length) {
      uint32_t low = string[i + 1];
      if (low >= 0xdc00 && low <= 0xdfff) {
        codepoint = 0x10000 + ((codepoint - 0xd800) << 10) + (low - 0xdc00);
        i++;
      }
    }
    output_length += utf8_width(codepoint);
  }

  char *output = malloc(output_length + 1);
  if (output == NULL) {
    return NULL;
  }

  size_t offset = 0;
  for (size_t i = 0; i < length; i++) {
    uint32_t codepoint = string[i];
    if (codepoint >= 0xd800 && codepoint <= 0xdbff && i + 1 < length) {
      uint32_t low = string[i + 1];
      if (low >= 0xdc00 && low <= 0xdfff) {
        codepoint = 0x10000 + ((codepoint - 0xd800) << 10) + (low - 0xdc00);
        i++;
      }
    }
    if (codepoint <= 0x7f) {
      output[offset++] = (char)codepoint;
    } else if (codepoint <= 0x7ff) {
      output[offset++] = (char)(0xc0 | (codepoint >> 6));
      output[offset++] = (char)(0x80 | (codepoint & 0x3f));
    } else if (codepoint <= 0xffff) {
      output[offset++] = (char)(0xe0 | (codepoint >> 12));
      output[offset++] = (char)(0x80 | ((codepoint >> 6) & 0x3f));
      output[offset++] = (char)(0x80 | (codepoint & 0x3f));
    } else {
      output[offset++] = (char)(0xf0 | (codepoint >> 18));
      output[offset++] = (char)(0x80 | ((codepoint >> 12) & 0x3f));
      output[offset++] = (char)(0x80 | ((codepoint >> 6) & 0x3f));
      output[offset++] = (char)(0x80 | (codepoint & 0x3f));
    }
  }
  output[offset] = '\0';
  return output;
}

int32_t zenoh_mbt_session_put(
    void *session,
    moonbit_string_t key,
    moonbit_bytes_t payload) {
  if (session == NULL) {
    return -1;
  }

  zenoh_mbt_session_t *owned = session;
  if (owned->closed) {
    return -1;
  }

  char *key_utf8 = moon_string_to_utf8(key);
  if (key_utf8 == NULL) {
    return -1;
  }

  z_view_keyexpr_t keyexpr;
  z_result_t result = z_view_keyexpr_from_str(&keyexpr, key_utf8);
  if (result < 0) {
    free(key_utf8);
    return (int32_t)result;
  }

  z_owned_bytes_t bytes;
  result = z_bytes_copy_from_buf(
      &bytes, payload, (size_t)Moonbit_array_length(payload));
  if (result < 0) {
    free(key_utf8);
    return (int32_t)result;
  }

  z_put_options_t options;
  z_put_options_default(&options);
  result = z_put(
      z_session_loan(&owned->session),
      z_view_keyexpr_loan(&keyexpr),
      z_bytes_move(&bytes),
      &options);
  free(key_utf8);
  return (int32_t)result;
}
