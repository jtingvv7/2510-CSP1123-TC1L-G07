//load data (from routes get JSON)
function loadMessages(){
    fetch(`/chat/${USER_ID}/json`) //send request to backend
    .then(response=> response.json()) //convert the returned data into js obect
    .then(data=> {
        let chatBox = document.getElementById("chat-box");
        chatBox.innerHTML=""; //clear old content
        data.messages.forEach(msg => {
            let msgDiv = document.createElement("div");
            if (msg.sender_id === CURRENT_USER_ID){
                msgDiv.classList.add("my-message");
            } else{
                msgDiv.classList.add("their-message");
            }
            msgDiv.textContent = msg.content;
            chatBox.appendChild(msgDiv);
        });
        //scroll to the bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    });
}
//load chat history once when page loads
loadMessages(USER_ID);

// refresh 3s 1time
setInterval(() => loadMessages(USER_ID), 3000);

//sent message when button
function sendMessage(USER_ID) {
    let content = document.getElementById("message-input").value;
    if (!content.trim()) return;

    fetch(`/send/${USER_ID}`,{
        method: "POST",
        headers:{
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ content: content })
    })
    .then(response => response.json())
    .then(data => {
        if(data.success){
            document.getElementById("message-input").value = "";
            loadMessages(USER_ID); //refresh
        }
    })
}