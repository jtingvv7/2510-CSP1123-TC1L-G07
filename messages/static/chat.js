// load messages
function loadMessages(){
    fetch(`/messages/chat/${USER_ID}/json`)
    .then(response=> response.json())
    .then(data=> {
        let chatBox = document.getElementById("chat-box");
        chatBox.innerHTML="";

        data.forEach(msg => {
            // system message
            if (msg.message_type === "system") {
                let sysWrapper = document.createElement("div");
                sysWrapper.classList.add("system-message");
                sysWrapper.innerHTML = `
                    <div class="system-bubble">
                        ${msg.content}<br>
                        <span class="timestamp">${msg.time}</span>
                    </div>
                `;
                chatBox.appendChild(sysWrapper);
                return; // skip
            }

            let wrapper = document.createElement("div");
            wrapper.classList.add("d-flex", "mb-2");

            let msgDiv = document.createElement("div");
            msgDiv.classList.add("message-bubble");

            // my message
            if (msg.sender_id === CURRENT_USER_ID){
                wrapper.classList.add("justify-content-end");
                msgDiv.classList.add("my-message");

                if (msg.message_type === "image") {
                    msgDiv.innerHTML = `
                        <img src="/static/${msg.content}" class="chat-image">
                        <span class="timestamp">${msg.time}</span>
                    `;
                } 
                else if (msg.message_type === "transaction" && msg.transaction) {
                    msgDiv.innerHTML = renderTransactionCard(msg.transaction, msg.time);
                }
                else {
                    msgDiv.innerHTML = `
                        ${msg.content}
                        <span class="timestamp">${msg.time}</span>
                    `;
                }

                wrapper.appendChild(msgDiv);

            // other message
            } else {
                let avatar = document.createElement("img");
                avatar.src = msg.sender_avatar || "https://i.pravatar.cc/40?u=" + msg.sender_id;
                avatar.classList.add("rounded-circle", "me-2");
                avatar.style.width = "35px";
                avatar.style.height = "35px";

                msgDiv.classList.add("their-message");

                if (msg.message_type === "image") {
                    msgDiv.innerHTML = `
                        <strong>${msg.sender_name}</strong><br>
                        <img src="/static/${msg.content}" class="chat-image">
                        <span class="timestamp">${msg.time}</span>
                    `;
                } 
                else if (msg.message_type === "transaction" && msg.transaction) {
                    msgDiv.innerHTML = `
                        <strong>${msg.sender_name}</strong><br>
                        ${renderTransactionCard(msg.transaction, msg.time)}
                    `;
                }
                else {
                    msgDiv.innerHTML = `
                        <strong>${msg.sender_name}</strong><br>
                        ${msg.content}
                        <span class="timestamp">${msg.time}</span>
                    `;
                }

                wrapper.appendChild(avatar);
                wrapper.appendChild(msgDiv);
            }

            chatBox.appendChild(wrapper);
        });

        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(err => console.error("Error loading messages:", err));
}

// render transaction card
function renderTransactionCard(tx, time) {
    let badgeClass = "bg-info";
    if (tx.status === "Completed") badgeClass = "bg-success";
    else if (tx.status === "Shipped") badgeClass = "bg-warning text-dark";
    else if (tx.status === "Cancelled") badgeClass = "bg-danger";

    return `
        <div class="transaction-card">
            <h6>Transaction #${tx.id}</h6>
            <p><strong>Item:</strong> ${tx.product}</p>
            <p><strong>Price:</strong> RM ${tx.price}</p>
            <p><strong>Status:</strong> <span class="badge ${badgeClass}">${tx.status}</span></p>
            <div class="mt-2">
                <a href="/transaction/view/${tx.id}" target="_blank" class="btn btn-sm btn-light border">
                <i class="bi bi-search"></i> View Details
                </a>
            </div>
        </div>
        <span class="timestamp">${time}</span>
    `;
}

// send text content
function sendMessage(USER_ID) {
    let input = document.getElementById("message-input");
    let content = input.value.trim();
    if (!content) return;

    fetch(`/messages/send/${USER_ID}`, {
        method: "POST",
        headers:{ "Content-Type": "application/x-www-form-urlencoded" },
        body: `content=${encodeURIComponent(content)}`
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === "ok"){
            input.value = "";
            loadMessages();
        }
    })
    .catch(err => console.error("Error sending message:", err));
}

// send image
function sendImage(USER_ID) {
    let fileInput = document.getElementById("image-input");
    let file = fileInput.files[0];
    if (!file) return;

    let formData = new FormData();
    formData.append("image", file);

    fetch(`/messages/send_image/${USER_ID}`, {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "ok") {
            fileInput.value = ""; // clear imput
            loadMessages();
        } else {
            alert(data.message || "Failed to send image");
        }
    })
    .catch(err => console.error("Error sending image:", err));
}

// send transaction 
function sendTransaction(USER_ID, transactionId) {
    fetch(`/messages/send_transaction/${USER_ID}/${transactionId}`, {
        method: "POST"
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "ok") {
            loadMessages();
        }
    })
    .catch(err => console.error("Error sending transaction:", err));
}

// initialization
loadMessages();
setInterval(loadMessages, 3000);

// support enter send
document.addEventListener("DOMContentLoaded", () =>{
    let input = document.getElementById("message-input");
    input.addEventListener("keypress", (e) => {
        if(e.key === "Enter"){
            e.preventDefault();
            sendMessage(USER_ID);
        }
    });
});