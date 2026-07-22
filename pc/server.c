/* Mini servidor estático para la app de escritorio FFTA.
 * Sirve ./assets en 127.0.0.1:<puerto> (solo loopback, solo GET).
 * Compila en Windows (MinGW/winsock) y POSIX (gcc/pthread).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#  include <winsock2.h>
#  include <ws2tcpip.h>
#  include <process.h>
#  pragma comment(lib, "ws2_32.lib")
typedef SOCKET sock_t;
#  define CLOSESOCK closesocket
#else
#  include <sys/socket.h>
#  include <netinet/in.h>
#  include <arpa/inet.h>
#  include <unistd.h>
#  include <pthread.h>
typedef int sock_t;
#  define CLOSESOCK close
#  define INVALID_SOCKET (-1)
#endif

static const char *ROOT = "assets";

static const char *mime(const char *path) {
    const char *e = strrchr(path, '.');
    if (!e) return "application/octet-stream";
    e++;
    if (!strcmp(e, "html")) return "text/html; charset=utf-8";
    if (!strcmp(e, "js"))   return "text/javascript; charset=utf-8";
    if (!strcmp(e, "css"))  return "text/css; charset=utf-8";
    if (!strcmp(e, "json")) return "application/json; charset=utf-8";
    if (!strcmp(e, "wasm")) return "application/wasm";
    if (!strcmp(e, "png"))  return "image/png";
    if (!strcmp(e, "svg"))  return "image/svg+xml";
    return "application/octet-stream";
}

static void urldecode(char *s) {
    char *o = s;
    while (*s) {
        if (*s == '%' && s[1] && s[2]) {
            char h[3] = { s[1], s[2], 0 };
            *o++ = (char)strtol(h, NULL, 16);
            s += 3;
        } else *o++ = *s++;
    }
    *o = 0;
}

static void handle(sock_t c) {
    char req[4096];
    int n = recv(c, req, sizeof(req) - 1, 0);
    if (n <= 0) { CLOSESOCK(c); return; }
    req[n] = 0;

    char path[1024] = "/";
    sscanf(req, "GET %1023s", path);
    char *q = strchr(path, '?'); if (q) *q = 0;
    urldecode(path);
    if (strstr(path, "..")) { CLOSESOCK(c); return; }   /* sin traversal */
    if (!strcmp(path, "/")) strcpy(path, "/index.html");

    char full[2048];
    snprintf(full, sizeof(full), "%s%s", ROOT, path);
    FILE *f = fopen(full, "rb");
    if (!f) {
        const char *r404 = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n";
        send(c, r404, (int)strlen(r404), 0);
        CLOSESOCK(c); return;
    }
    fseek(f, 0, SEEK_END); long size = ftell(f); fseek(f, 0, SEEK_SET);

    char hdr[512];
    int h = snprintf(hdr, sizeof(hdr),
        "HTTP/1.1 200 OK\r\nContent-Type: %s\r\nContent-Length: %ld\r\n"
        "Cache-Control: no-cache\r\nConnection: close\r\n\r\n", mime(full), size);
    send(c, hdr, h, 0);

    char buf[65536]; size_t r;
    while ((r = fread(buf, 1, sizeof(buf), f)) > 0)
        if (send(c, buf, (int)r, 0) < 0) break;
    fclose(f);
    CLOSESOCK(c);
}

#ifdef _WIN32
static unsigned __stdcall worker(void *p) { handle((sock_t)(size_t)p); return 0; }
#else
static void *worker(void *p) { handle((sock_t)(size_t)p); return NULL; }
#endif

int main(int argc, char **argv) {
    int port = argc > 1 ? atoi(argv[1]) : 8641;
#ifdef _WIN32
    WSADATA w; WSAStartup(MAKEWORD(2, 2), &w);
#endif
    sock_t s = socket(AF_INET, SOCK_STREAM, 0);
    int yes = 1;
    setsockopt(s, SOL_SOCKET, SO_REUSEADDR, (const char *)&yes, sizeof(yes));
    struct sockaddr_in a;
    memset(&a, 0, sizeof(a));
    a.sin_family = AF_INET;
    a.sin_port = htons((unsigned short)port);
    a.sin_addr.s_addr = inet_addr("127.0.0.1");    /* solo local */
    if (bind(s, (struct sockaddr *)&a, sizeof(a)) != 0) {
        fprintf(stderr, "No pude usar el puerto %d (¿ya hay otra copia abierta?)\n", port);
        return 1;
    }
    listen(s, 16);
    printf("FFTA sirviendo en http://127.0.0.1:%d  (cierra esta ventana para salir)\n", port);
    for (;;) {
        sock_t c = accept(s, NULL, NULL);
        if (c == INVALID_SOCKET) continue;
#ifdef _WIN32
        _beginthreadex(NULL, 0, worker, (void *)(size_t)c, 0, NULL);
#else
        pthread_t t; pthread_create(&t, NULL, worker, (void *)(size_t)c);
        pthread_detach(t);
#endif
    }
    return 0;
}
