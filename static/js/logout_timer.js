let timeout;

function resetTimer() {
    clearTimeout(timeout);
    timeout = setTimeout(logout,  15 * 60 * 1000);  // 30分钟
}

function logout() {
    console.log("Session expired. Logging out...");
    window.location.href = "/logout/";  // Django登出URL
}

// 监听鼠标和键盘事件
window.onload = resetTimer;
document.onmousemove = resetTimer;
document.onkeypress = resetTimer;
