//load data (from routes get JSON)
function loadMessages(){
    fetch(`/messages/chat/${USER_ID}/json`) //send request to backend
    .then(response=> response.json()) //convert the returned data into js obect
    .then(data=> {
        let chatBox = document.getElementById("chat-box");
        chatBox.innerHTML=""; //clear old content

        data.forEach(msg => {
            let msgDiv = document.createElement("div");
            msgDiv.classList.add("message-bubble");

            if (msg.sender_id === CURRENT_USER_ID){
                msgDiv.classList.add("my-message");
            } else{
                msgDiv.classList.add("their-message");
            }
            msgDiv.innerHTML=`
            <strong>${msg.sender_name}</strong><br>
            <div>${msg.content}</div>
            <span class="timestamp">${msg.time}</span>
            `;
            chatBox.appendChild(msgDiv);
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

//sent message 
function sendMessage(USER_ID) {
    let input = document.getElementById("message-input");
    let content = input.value.trim();
    if (!content) return;

    fetch(`/messages/send/${USER_ID}`,{
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
document.addEventListener("DOMContentLoaded",() =>{
    let input = document.getElementById("message-input");
    input.addEventListener("keypress",(e) => {
        if(e.key === "Enter"){
            e.preventDefault(); //prevent line breaks
            sendMessage(USER_ID);
        }
    });
});