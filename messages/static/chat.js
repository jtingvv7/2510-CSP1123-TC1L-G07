//load data (from routes get JSON)
function loadMessages(){
    fetch(`/messages/chat/${USER_ID}/json`) //send request to backend
    .then(response=> response.json()) //convert the returned data into js object
    .then(data=> {
        let chatBox = document.getElementById("chat-box");
        chatBox.innerHTML=""; //clear old content

        data.forEach(msg => {
            let wrapper = document.createElement("div");
            wrapper.classList.add("d-flex", "mb-2");

            let msgDiv = document.createElement("div");
            msgDiv.classList.add("message-bubble");

            if (msg.sender_id === CURRENT_USER_ID){
                // my message
                wrapper.classList.add("justify-content-end");
                msgDiv.classList.add("my-message");
                msgDiv.innerHTML = `
                    ${msg.content}
                    <span class="timestamp">${msg.time}</span>
                `;
                wrapper.appendChild(msgDiv);

            } else {
                // message
                let avatar = document.createElement("img");
                avatar.src = msg.sender_avatar || "https://i.pravatar.cc/40?u=" + msg.sender_id;
                avatar.classList.add("rounded-circle", "me-2");
                avatar.style.width = "35px";
                avatar.style.height = "35px";

                msgDiv.classList.add("their-message");
                msgDiv.innerHTML = `
                    <strong>${msg.sender_name}</strong><br>
                    ${msg.content}
                    <span class="timestamp">${msg.time}</span>
                `;

                wrapper.appendChild(avatar);
                wrapper.appendChild(msgDiv);
            }

            chatBox.appendChild(wrapper);
        });

        //scroll to the bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(err => console.error("Error loading messages:", err));
}

//load chat history once when page loads
loadMessages();

// refresh 3s 1time
setInterval(loadMessages, 3000);

//send message 
function sendMessage(USER_ID) {
    let input = document.getElementById("message-input");
    let content = input.value.trim();
    if (!content) return;

    fetch(`/messages/send/${USER_ID}`, {
        method: "POST",
        headers:{
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: `content=${encodeURIComponent(content)}`
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === "ok"){
            input.value = ""; //clear input box
            loadMessages(); //refresh
        }
    })
    .catch(err => console.error("Error sending message:", err));
}

//support enter to send message
document.addEventListener("DOMContentLoaded", () =>{
    let input = document.getElementById("message-input");
    input.addEventListener("keypress", (e) => {
        if(e.key === "Enter"){
            e.preventDefault(); //prevent line breaks
            sendMessage(USER_ID);
        }
    });
});