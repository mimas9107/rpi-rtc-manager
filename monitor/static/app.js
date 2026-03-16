async function refresh() {

    const res = await fetch("/api/status")
    const data = await res.json()

    let svc = document.getElementById("services")
    svc.innerHTML = ""

    for (const [name, info] of Object.entries(data.services)) {

        let row = document.createElement("tr")

        row.innerHTML =
            `<td>${name}</td>
             <td>${info.Result}</td>
             <td>${info.ExecMainStartTimestamp}</td>
             <td>${info.ExecMainExitTimestamp}</td>`

        svc.appendChild(row)
    }

    let timer = document.getElementById("timer")

    timer.innerHTML =
        `<tr><td>Next Run</td><td>${data.timer_next_run}</td></tr>
         <tr><td>Last Trigger</td><td>${data.timer.LastTriggerUSec}</td></tr>
         <tr><td>State</td><td>${data.timer.ActiveState}</td></tr>`

    document.getElementById("system_time").textContent = data.system_time
    document.getElementById("rtc_time").textContent = data.rtc_time

    if (data.drift !== null)
        document.getElementById("drift").textContent = data.drift
    else
        document.getElementById("drift").textContent = "N/A"

    document.getElementById("logs").textContent =
        data.logs.join("")
}

setInterval(refresh, 5000)

refresh()