const API_BASE = "https://youtubetomp3-cfey.onrender.com/api";
// const API_BASE = "http://localhost:5000/api";

document.addEventListener("DOMContentLoaded", async () => {
  const urlInput = document.getElementById("url");
  const qualitySelect = document.getElementById("quality");
  const convertBtn = document.getElementById("convert-btn");
  const progressContainer = document.getElementById("progress-container");
  const progressBar = document.getElementById("progress-bar");
  const statusText = document.getElementById("status-text");

  // 1. 自動抓取當前分頁網址
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab && tab.url && (tab.url.includes("youtube.com") || tab.url.includes("youtu.be"))) {
    urlInput.value = tab.url;
  } else {
    urlInput.placeholder = "請貼上 YouTube 網址";
  }

  // 2. 點擊轉檔按鈕
  convertBtn.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    const quality = qualitySelect.value;

    if (!url) {
      alert("請輸入有效的 YouTube 網址！");
      return;
    }

    // UI 鎖定狀態
    convertBtn.disabled = true;
    progressContainer.style.display = "block";
    progressBar.style.width = "0%";
    statusText.innerText = "發送請求中...";

    try {
      // 呼叫 POST /api/convert
      const res = await fetch(`${API_BASE}/convert`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, quality })
      });

      if (!res.ok) throw new Error("後端請求失敗");

      const data = await res.json();
      const taskId = data.task_id;

      // 3. 開始輪詢查詢進度
      pollStatus(taskId);
    } catch (err) {
      statusText.innerText = "失敗：" + err.message;
      convertBtn.disabled = false;
    }
  });

  // 輪詢狀態函式
  async function pollStatus(taskId) {
    const timer = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/status/${taskId}`);
        const data = await res.json();

        if (data.status === "downloading") {
          progressBar.style.width = `${data.progress}%`;
          statusText.innerText = `下載中... ${data.progress}% (${data.speed_mbps || 0} MB/s)`;
        } else if (data.status === "converting") {
          progressBar.style.width = "99%";
          statusText.innerText = "FFmpeg 音訊轉檔中...";
        } else if (data.status === "completed") {
          clearInterval(timer);
          progressBar.style.width = "100%";
          statusText.innerText = "轉檔完成！準備觸發下載...";

          // 4. 呼叫 Chrome 原生下載 API
          chrome.downloads.download({
            url: `${API_BASE}/download/${taskId}`,
            filename: data.file_name
          });

          setTimeout(() => {
            statusText.innerText = "下載完畢！";
            convertBtn.disabled = false;
          }, 2000);
        } else if (data.status === "failed") {
          clearInterval(timer);
          statusText.innerText = "轉檔失敗：" + (data.error || "未知錯誤");
          convertBtn.disabled = false;
        }
      } catch (err) {
        clearInterval(timer);
        statusText.innerText = "通訊失敗：" + err.message;
        convertBtn.disabled = false;
      }
    }, 5000); // 每 5 秒查詢一次
  }
});