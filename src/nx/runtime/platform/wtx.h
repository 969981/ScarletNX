/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Copyright 2026 the ScarletNX contributors */
/* Experiment only (aogo/hot-pages-exp, never a PR): the time and the count of each thing the written-page tracking
   and the caches do, summed over the run and printed as a "wtx:" line every 600 presents (vk_buf_frame) */
#ifndef SNX_WTX_H
#define SNX_WTX_H
#include "nx/runtime/platform/plat.h"
#include <stdlib.h>
#include <time.h>

enum {
    WTX_SCAN_NS,      /* plat_ww_scan: the walk and its protection of the written pages again */
    WTX_SCANS,        /* its calls */
    WTX_SCAN_PAGES,   /* the 4 KiB pages they reported written */
    WTX_CHECK_NS,     /* vk_written_since, the scans it ran included */
    WTX_CHECKS,       /* its calls */
    WTX_CHECK_SCAN_NS, /* the scans run inside vk_written_since (also in WTX_SCAN_NS) */
    WTX_HASH_NS,      /* the texture cache's whole-texture hash (mem_hash) */
    WTX_HASH_BYTES,
    WTX_SHASH_NS,     /* the sampled hash of big stable textures (vk_sample_hash) */
    WTX_SHASH_BYTES,
    WTX_CMP_NS,       /* the buffer cache's memcmp of pending results against guest memory */
    WTX_CMP_BYTES,
    WTX_UPLOAD_NS,    /* tex_upload: a texture loaded again from guest memory */
    WTX_UPLOADS,
    WTX_UPLOAD_BYTES,
    WTX_TRAP_NS,      /* own_fault: a trap's landing */
    WTX_TRAPS,
    WTX_HOT_PAGES,    /* hot pages a scan reported and left writable */
    WTX_EPOCHS,       /* write epochs started (vk_ww_new_epoch) */
    WTX_STAGE_BYTES,  /* bytes the CPU put in the staging ring (vk_stage_upload) */
    WTX_STAGES,
    WTX_FAULT_NS,     /* wp_fault on a page the tracking held: the handler's own time, its mprotect included */
    WTX_FAULTS,
    WTX_PROTECT_NS,   /* wp_protect's mprotect calls (part of WTX_SCAN_NS, and of the cool's) */
    WTX_PROTECTS,
    WTX_COOL_NS,      /* vk_ww_cool, its plat_ww_hot_in checks included */
    WTX_COOLS,        /* its calls */
    WTX_COOLED,       /* calls that found hot pages and cooled them */
    WTX_COOL_PAGES,   /* 4 KiB pages the cool step protected again and reported */
    WTX_UNHELD,       /* written pages a scan left writable for want of the mapping budget (main's own over-report) */
    WTX_FULL,         /* a range list full (scan stage, results, peers): the last range grown, marking more */
    WTX_N
};
/* weak, as a test that builds a file of the renderer alone has no platform library */
extern u64 g_wtx[WTX_N];
__attribute__((weak)) u64 g_wtx[WTX_N];
static inline u64 wtx_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (u64)ts.tv_sec * 1000000000ull + (u64)ts.tv_nsec;
}
static inline void wtx_add(int k, u64 v) { __atomic_fetch_add(&g_wtx[k], v, __ATOMIC_RELAXED); }
/* an experiment switch from the environment, read once per place (1 when set to a positive number) */
#define WTX_ENV(name) \
    ({ \
        static int v_ = -1; \
        if (v_ < 0) v_ = getenv(name) && atoi(getenv(name)) > 0; \
        v_; \
    })
#endif
