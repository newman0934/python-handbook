# Part 0：後端與網路 / OS 基礎 Backend & Network / OS Foundations

> 前置通識——本書其餘部分「用而不教」的底層,在這裡從零補齊。

這一 Part 回答兩個問題:**「後端到底在做什麼?」** 和 **「網路與作業系統怎麼運作?」**
它與 Python 語法無關,卻是後面所有內容的地基:
連線池為何存在、優雅關閉為何送 `SIGTERM`、asyncio 在等什麼——答案都在這裡。

> 🧭 **定位**:可選讀的前置章。每章結尾都會扣回「**這對你寫 Python 後端有什麼影響**」——
> 它不是計算機概論教科書,而是「一個 Python 後端工程師該懂的底層」。
> 範例以可執行的 `socket` / `signal` / `os` 診斷腳本呈現,不需要外部網路。

## 章節

| 章 | 標題 |
|----|------|
| 01 | [後端在做什麼:一個請求的完整旅程](01-request-journey.md) |
| 02 | [TCP / UDP 與可靠傳輸](02-tcp-udp.md) |
| 03 | [DNS 與 IP / Port](03-dns-ip-port.md) |
| 04 | [HTTP 報文深入](04-http-messages.md) |
| 05 | [HTTPS 與 TLS](05-https-tls.md) |
| 06 | [Linux process 與 thread](06-process-thread.md) |
| 07 | [檔案描述符與 I/O](07-file-descriptor-io.md) |
| 08 | [訊號與程序生命週期](08-signals-lifecycle.md) |
| 09 | [shell、環境變數與常用診斷](09-shell-env-diagnostics.md) |

> 其餘章節規劃(陸續補上):Part 0 統整。

---

[⬆️ 回章節總覽](../README.md)
