// static/app.js
// Polling every 3s for updates. Requires endpoints in app.py

const POLL_INTERVAL = 3000;
let lastCounts = {};

function formatTime(iso) {
  try { return new Date(iso).toLocaleTimeString(); } catch(e) { return ""; }
}

// for buyers: send message
async function sendMessage(text) {
  const resp = await fetch("/api/chat/send", {
    method: "POST",
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({text})
  });
  return resp.ok;
}

// for admin: send reply
async function adminSend(user, text) {
  const resp = await fetch("/api/admin/send", {
    method: "POST",
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({user, text})
  });
  return resp.ok;
}

// admin: take a message
async function adminTake(user, index) {
  const resp = await fetch("/api/admin/take", {
    method: "POST",
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({user, index})
  });
  return resp.ok;
}

async function pollUpdates() {
  try {
    const resp = await fetch("/api/chats");
    if (!resp.ok) return;
    const data = await resp.json();
    // if admin -> data is array of convs
    if (Array.isArray(data)) {
      // build badge counts
      const counts = {};
      let totalNew = 0;
      data.forEach(conv => {
        const unassigned = conv.messages.filter(m => !m.taken_by).length;
        counts[conv.user] = unassigned;
        totalNew += unassigned;
      });
      // update badge in DOM if present
      const badge = document.getElementById("chat-badge");
      if (badge) {
        badge.innerText = totalNew>0? totalNew:"";
        badge.style.display = totalNew>0? "inline-block":"none";
      }
      // store last counts
      lastCounts = counts;
      // optionally update a list of conversations if present
      const convList = document.getElementById("conv-list");
      if (convList) {
        convList.innerHTML = "";
        data.forEach(conv => {
          const el = document.createElement("div");
          el.className = "conv-item";
          el.innerHTML = `<strong>${conv.user}</strong> <span class="small">(${conv.messages.length} msg)</span>
                          <div class="unassigned">${conv.messages.filter(m=>!m.taken_by).map((m,i)=>`
                            <div class="flash">${m.text} <small>${new Date(m.time).toLocaleTimeString()}</small>
                              <button onclick="takeMsg('${conv.user}', ${conv.messages.indexOf(m)})">Prendre</button>
                            </div>`).join("")}</div>`;
          convList.appendChild(el);
        });
      }
    } else {
      // buyer view: data is a single conv
      const conv = data;
      const box = document.getElementById("messages");
      if (box) {
        box.innerHTML = conv.messages.map(m=>`
          <div class="chat-message">
            <strong>${m.from}:</strong> ${m.text} <small style="float:right">${formatTime(m.time)}</small>
          </div>
        `).join("");
        box.scrollTop = box.scrollHeight;
      }
    }
  } catch(e) {
    console.error("poll error", e);
  } finally {
    setTimeout(pollUpdates, POLL_INTERVAL);
  }
}

// helper for inline button
window.takeMsg = async (user, index) => {
  await adminTake(user, index);
  await pollUpdates();
};

// bind send forms
window.addEventListener("DOMContentLoaded", ()=> {
  // buyer send form
  const sendForm = document.getElementById("send-form");
  if (sendForm) {
    sendForm.addEventListener("submit", async (ev)=>{
      ev.preventDefault();
      const input = document.getElementById("msg-input");
      if (!input.value.trim()) return;
      await sendMessage(input.value.trim());
      input.value = "";
      // immediate poll
      setTimeout(pollUpdates, 300);
    });
  }
  // admin reply forms may be dynamic per conv -> can call adminSend(user,text)
  pollUpdates();
});
