/* kids CUDA bandwidth — GPU kid only. No score if this will not compile or run. */
#include <cuda_runtime.h>
#include <stdio.h>
#include <stdlib.h>

#define BYTES (256u * 1024u * 1024u)
#define REPS 8

static void die(const char *what, cudaError_t err) {
    fprintf(stderr, "CUDA RED: %s: %s\n", what, cudaGetErrorString(err));
    exit(2);
}

static double gbps(size_t bytes, float ms) {
    return ((double)bytes / 1e9) / ((double)ms / 1e3);
}

int main(void) {
    void *h = malloc(BYTES);
    void *d = NULL;
    void *d2 = NULL;
    cudaError_t err;
    cudaEvent_t start, stop;
    float ms;
    int i;

    if (!h) {
        fprintf(stderr, "CUDA RED: host malloc\n");
        return 3;
    }

    err = cudaMalloc(&d, BYTES);
    if (err != cudaSuccess) die("cudaMalloc d", err);
    err = cudaMalloc(&d2, BYTES);
    if (err != cudaSuccess) die("cudaMalloc d2", err);
    err = cudaEventCreate(&start);
    if (err != cudaSuccess) die("event start", err);
    err = cudaEventCreate(&stop);
    if (err != cudaSuccess) die("event stop", err);

    err = cudaMemcpy(d, h, BYTES, cudaMemcpyHostToDevice);
    if (err != cudaSuccess) die("warmup H2D", err);
    err = cudaDeviceSynchronize();
    if (err != cudaSuccess) die("sync warmup", err);

    err = cudaEventRecord(start, 0);
    if (err != cudaSuccess) die("record H2D start", err);
    for (i = 0; i < REPS; i++) {
        err = cudaMemcpy(d, h, BYTES, cudaMemcpyHostToDevice);
        if (err != cudaSuccess) die("H2D", err);
    }
    err = cudaEventRecord(stop, 0);
    if (err != cudaSuccess) die("record H2D stop", err);
    err = cudaEventSynchronize(stop);
    if (err != cudaSuccess) die("sync H2D", err);
    err = cudaEventElapsedTime(&ms, start, stop);
    if (err != cudaSuccess) die("elapsed H2D", err);
    {
        double h2d = gbps((size_t)BYTES * REPS, ms);
        printf("CUDA_H2D_GBs %.3f\n", h2d);
        printf("CUDA_H2D_MTs %.0f\n", h2d * 1024.0);
    }

    err = cudaEventRecord(start, 0);
    if (err != cudaSuccess) die("record D2H start", err);
    for (i = 0; i < REPS; i++) {
        err = cudaMemcpy(h, d, BYTES, cudaMemcpyDeviceToHost);
        if (err != cudaSuccess) die("D2H", err);
    }
    err = cudaEventRecord(stop, 0);
    if (err != cudaSuccess) die("record D2H stop", err);
    err = cudaEventSynchronize(stop);
    if (err != cudaSuccess) die("sync D2H", err);
    err = cudaEventElapsedTime(&ms, start, stop);
    if (err != cudaSuccess) die("elapsed D2H", err);
    {
        double d2h = gbps((size_t)BYTES * REPS, ms);
        printf("CUDA_D2H_GBs %.3f\n", d2h);
        printf("CUDA_D2H_MTs %.0f\n", d2h * 1024.0);
    }

    err = cudaEventRecord(start, 0);
    if (err != cudaSuccess) die("record D2D start", err);
    for (i = 0; i < REPS; i++) {
        err = cudaMemcpy(d2, d, BYTES, cudaMemcpyDeviceToDevice);
        if (err != cudaSuccess) die("D2D", err);
    }
    err = cudaEventRecord(stop, 0);
    if (err != cudaSuccess) die("record D2D stop", err);
    err = cudaEventSynchronize(stop);
    if (err != cudaSuccess) die("sync D2D", err);
    err = cudaEventElapsedTime(&ms, start, stop);
    if (err != cudaSuccess) die("elapsed D2D", err);
    {
        double d2d = gbps((size_t)BYTES * REPS, ms);
        printf("CUDA_D2D_GBs %.3f\n", d2d);
        printf("CUDA_D2D_MTs %.0f\n", d2d * 1024.0);
    }

    cudaEventDestroy(start);
    cudaEventDestroy(stop);
    cudaFree(d);
    cudaFree(d2);
    free(h);
    return 0;
}
