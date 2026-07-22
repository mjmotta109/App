package com.mj.ffta;

import android.app.Activity;
import android.content.res.AssetManager;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebChromeClient;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URLDecoder;
import java.util.HashMap;
import java.util.Map;

public class MainActivity extends Activity {

    private WebView web;
    private ServerSocket server;

    private static final Map<String, String> MIME = new HashMap<String, String>();
    static {
        MIME.put("html", "text/html; charset=utf-8");
        MIME.put("js", "text/javascript; charset=utf-8");
        MIME.put("css", "text/css; charset=utf-8");
        MIME.put("json", "application/json; charset=utf-8");
        MIME.put("wasm", "application/wasm");
        MIME.put("data", "application/octet-stream");
        MIME.put("gba", "application/octet-stream");
        MIME.put("png", "image/png");
        MIME.put("svg", "image/svg+xml");
        MIME.put("ttf", "font/ttf");
        MIME.put("woff2", "font/woff2");
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        int port = startServer();

        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        web.setWebViewClient(new WebViewClient());
        web.setWebChromeClient(new WebChromeClient());
        web.setBackgroundColor(0xFF000000);
        setContentView(web);
        web.loadUrl("http://127.0.0.1:" + port + "/index.html");
    }

    private int startServer() {
        try {
            server = new ServerSocket(0, 16, InetAddress.getByName("127.0.0.1"));
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
        Thread t = new Thread(new Runnable() {
            public void run() {
                while (!server.isClosed()) {
                    try {
                        final Socket c = server.accept();
                        new Thread(new Runnable() {
                            public void run() { handle(c); }
                        }).start();
                    } catch (Exception e) { /* socket closed on exit */ }
                }
            }
        });
        t.setDaemon(true);
        t.start();
        return server.getLocalPort();
    }

    private void handle(Socket c) {
        try {
            InputStream in = c.getInputStream();
            ByteArrayOutputStream line = new ByteArrayOutputStream();
            int b, state = 0;
            // leer solo hasta el fin de las cabeceras (\r\n\r\n)
            while ((b = in.read()) != -1) {
                line.write(b);
                state = (b == '\r' && (state == 0 || state == 2)) ? state + 1
                      : (b == '\n' && (state == 1 || state == 3)) ? state + 1 : 0;
                if (state == 4) break;
            }
            String req = line.toString("UTF-8");
            String path = "/";
            int sp1 = req.indexOf(' '), sp2 = req.indexOf(' ', sp1 + 1);
            if (sp1 >= 0 && sp2 > sp1) path = req.substring(sp1 + 1, sp2);
            int q = path.indexOf('?');
            if (q >= 0) path = path.substring(0, q);
            path = URLDecoder.decode(path, "UTF-8");
            if (path.equals("/")) path = "/index.html";

            byte[] body = null;
            try {
                AssetManager am = getAssets();
                InputStream f = am.open(path.substring(1));
                ByteArrayOutputStream buf = new ByteArrayOutputStream();
                byte[] tmp = new byte[65536];
                int n;
                while ((n = f.read(tmp)) > 0) buf.write(tmp, 0, n);
                f.close();
                body = buf.toByteArray();
            } catch (Exception nf) { /* 404 */ }

            OutputStream out = c.getOutputStream();
            if (body == null) {
                out.write("HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".getBytes("UTF-8"));
            } else {
                String ext = path.contains(".") ? path.substring(path.lastIndexOf('.') + 1) : "";
                String mime = MIME.containsKey(ext) ? MIME.get(ext) : "application/octet-stream";
                out.write(("HTTP/1.1 200 OK\r\nContent-Type: " + mime
                        + "\r\nContent-Length: " + body.length
                        + "\r\nCache-Control: no-cache\r\nConnection: close\r\n\r\n").getBytes("UTF-8"));
                out.write(body);
            }
            out.flush();
            c.close();
        } catch (Exception e) { /* conexión abortada */ }
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                | View.SYSTEM_UI_FLAG_FULLSCREEN
                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
        }
    }

    @Override
    protected void onDestroy() {
        try { if (server != null) server.close(); } catch (Exception e) {}
        if (web != null) web.destroy();
        super.onDestroy();
    }
}
