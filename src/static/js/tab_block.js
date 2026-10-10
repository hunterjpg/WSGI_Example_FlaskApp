//From https://www.w3schools.com/w3css/tryit.asp?filename=tryw3css_tabulators
function openTab(contentID, tabID) {
    var i;
    // Tabbed Content
    var content = document.getElementsByClassName("tab-content");
    for (i = 0; i < content.length; i++) {
        content[i].style.display = "none";
    }
    document.getElementById(contentID).style.display = "inherit";
    // Tab Headers
    var tabs = document.getElementsByClassName("tab");
    for (i = 0; i < tabs.length; i++) {
        tabs[i].setAttribute("selected", "false");
    }
    document.getElementById(tabID).setAttribute("selected", "true")
}