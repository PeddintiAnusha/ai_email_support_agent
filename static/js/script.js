/* AI Email Support Agent - front-end interactions */

document.addEventListener("DOMContentLoaded", () => {
  const generateBtn = document.getElementById("generateReplyBtn");
  const replyTextarea = document.getElementById("replyTextarea");
  const saveEditBtn = document.getElementById("saveEditBtn");
  const sendReplyBtn = document.getElementById("sendReplyBtn");
  const loadingIndicator = document.getElementById("aiLoading");
  const summaryBox = document.getElementById("summaryBox");

  let currentAiReplyId = document.body.dataset.aiReplyId || null;
  const emailId = document.body.dataset.emailId;

  function toggleLoading(show) {
    if (loadingIndicator) {
      loadingIndicator.style.display = show ? "flex" : "none";
    }
  }

  function postJSON(url, payload) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((res) => res.json());
  }

  if (generateBtn) {
    generateBtn.addEventListener("click", async () => {
      toggleLoading(true);
      generateBtn.disabled = true;
      try {
        const data = await postJSON("/api/generate_reply", { email_id: emailId });
        if (data.success) {
          replyTextarea.value = data.generated_reply;
          currentAiReplyId = data.ai_reply_id;
          document.body.dataset.aiReplyId = data.ai_reply_id;
          if (summaryBox) summaryBox.textContent = data.summary || "";
          if (saveEditBtn) saveEditBtn.disabled = false;
          if (sendReplyBtn) sendReplyBtn.disabled = false;
        } else {
          alert(data.error || "Something went wrong generating the reply.");
        }
      } catch (err) {
        alert("Network error while generating reply.");
      } finally {
        toggleLoading(false);
        generateBtn.disabled = false;
      }
    });
  }

  if (saveEditBtn) {
    saveEditBtn.addEventListener("click", async () => {
      if (!currentAiReplyId) return;
      const data = await postJSON("/api/edit_reply", {
        ai_reply_id: currentAiReplyId,
        edited_reply: replyTextarea.value,
      });
      if (data.success) {
        saveEditBtn.textContent = "Saved ✓";
        setTimeout(() => (saveEditBtn.textContent = "Save Edit"), 1500);
      } else {
        alert(data.error || "Could not save your edit.");
      }
    });
  }

  if (sendReplyBtn) {
    sendReplyBtn.addEventListener("click", async () => {
      if (!currentAiReplyId) return;
      sendReplyBtn.disabled = true;
      const data = await postJSON("/api/send_reply", {
        email_id: emailId,
        ai_reply_id: currentAiReplyId,
      });
      if (data.success) {
        window.location.href = data.redirect || "/inbox";
      } else {
        alert(data.error || "Could not send the reply.");
        sendReplyBtn.disabled = false;
      }
    });
  }

  // Star rating widget for feedback
  const stars = document.querySelectorAll(".star-rating .star");
  const ratingInput = document.getElementById("ratingInput");
  stars.forEach((star) => {
    star.addEventListener("click", () => {
      const value = parseInt(star.dataset.value, 10);
      if (ratingInput) ratingInput.value = value;
      stars.forEach((s) => {
        s.classList.toggle("text-warning", parseInt(s.dataset.value, 10) <= value);
      });
    });
  });
});
