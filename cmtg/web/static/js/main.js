(function () {

    window.cmtg = {};


    // libs
    window.cmtg.colorHash = new ColorHash();


    // wixel module stuff
    const wixelChannels = 256;
    const wixelZeroFrequency = 2403.47;
    const wixelChannelSpacing = 0.2864;

    function getWixelFrequencies() {
        let result = [];
        for (let i = 0; i < wixelChannels; i++) {
            let freq = wixelZeroFrequency + (i * wixelChannelSpacing);
            result.push(freq.toFixed(2));
        }
        return result;
    }

    window.cmtg.wixelFrequencies = getWixelFrequencies();


    // constants
    const chartTypeLast = 1;
    const chartTypeAvgLast10 = 2;
    const chartTypeAvgLast100 = 3;
    const chartTypeAvgAll = 4;

    window.cmtg.chartType = chartTypeLast;

    const chartTypeTitles = {
        chartTypeTitles[chartTypeLast]: "Last signal values",
        chartTypeTitles[chartTypeAvgLast10]: "Average of last 10 signal values",
        chartTypeTitles[chartTypeAvgLast100]: "Average of last 100 signal values",
        chartTypeTitles[chartTypeAvgAll]: "Average of all signal values",
    };

    const chartOptions = {
        animation: {
            duration: 0
        },
        hover: {
            animationDuration: 0
        },
        responsiveAnimationDuration: 0,
        responsive: true,
        maintainAspectRatio: false,
        legend: {
            display: false
        },
        elements: {
            point: {
                radius: 0,
                hoverRadius: 0,
            },
            line: {
                tension: 0,
                fill: false,
                borderWidth: 1,
            }
        },
        tooltips: {
            enabled: false,
        },
        layout: {
            padding: {
                top: 30,
                bottom: 40,
                left: -4,
            },
        },
        scales: {
            yAxes: [{
                type: 'linear',
                ticks: {
                    fontFamily: "monospace",
                    fontSize: 10,
                    min: -110,
                    max: -30,
                    stepSize: 10,
                }
            }],
            xAxes: [{
                type: 'linear',
                ticks: {
                    fontFamily: "monospace",
                    fontSize: 10,
                    min: 2400,
                    max: 2480,
                    stepSize: 5,
                }
            }],
        }
    };

    const logsLimit = 100;


    // functional part
    function setChartType(chartType) {
        window.cmtg.chartType = chartType;
    }

    function setChartTitle(chartType) {
        let title = document.getElementById("chart-title");
        title.innerText = chartTypeTitles[chartType];
    }

    function changeChartType(event) {
        let target = event.target, // button element
            parent = target.parentElement,
            children = parent.children;

        for (let i = 0; i < children.length; i++) {
            children[i].classList.remove("active");
        }
        target.classList.add("active");

        let chartType = parseInt(target.dataset.chartType);
        setChartType(chartType);
        setChartTitle(chartType);
    }

    function createChartPoints(frequencies, signalValues) {
        let result = []
        for (let i = 0; i < wixelChannels; i++) {
            result.push({
                x: frequencies[i],
                y: signalValues[i]
            });
        }
        return result;
    }

    function updateChartValues(chart, data) {
        let signalMap = JSON.parse(data),
            datasets = [];

        for (serialNumber in signalMap) {
            let signalValues;

            switch (window.cmtg.chartType) {
                case chartTypeLast:
                    signalValues = signalMap[serialNumber].last;
                    break
                case chartTypeAvgLast10:
                    signalValues = signalMap[serialNumber].avg_last_10;
                    break
                case chartTypeAvgLast100:
                    signalValues = signalMap[serialNumber].avg_last_100;
                    break
                case chartTypeAvgAll:
                    signalValues = signalMap[serialNumber].avg_all;
                    break
            }

            if (signalValues === null) {
                continue;
            }

            datasets.push({
                borderColor: window.cmtg.colorHash.hex(serialNumber),
                data: createChartPoints(
                    window.cmtg.wixelFrequencies, signalValues
                )
            });
        }

        chart.data.datasets = datasets;
        chart.update();
    }

    function createWixelItem(wixelSession) {
        let borderColor = window.cmtg.colorHash.hex(wixelSession.serial_number);
        return (
            `<li class="wixel-list__item">
                <ul class="wixel" style="border-left-color: ${borderColor};">
                    <li>Serial number: ${wixelSession.serial_number}</li>
                    <li>Port: ${wixelSession.port}</li>
                    <li>Packages: ${wixelSession.stats.packages}</li>
                    <li>Work time: ${wixelSession.stats.connected}</li>
                </ul>
            </li>`
        );
    }

    function updateWixelSessions(data) {
        let wixelSessionMap = JSON.parse(data),
            wixelSessions = document.getElementById("wixel-sessions");

        let markup = "";
        for (key in wixelSessionMap) {
            markup += createWixelItem(wixelSessionMap[key]);
        }
        wixelSessions.innerHTML = markup;
    }

    function createLogRecord(message) {
        let color = "#4b807c";
        if (message.includes("[ERROR]")) {
            color = "#930000";
        } else if (message.includes("[WARNING]")) {
            color = "#948a40";
        }

        return `<p class="log-record" style="color: ${color};">${message}</p>`;
    }

    function updateLogs(data) {
        let systemLogs = document.getElementById("system-logs"),
            logs = JSON.parse(data).reverse();

        if ((logs.length + systemLogs.childElementCount) > logsLimit) {
            let children = Array
                .from(systemLogs.children)
                .slice(-(logsLimit - logs.length));
            for (let i = 0; i < children.length; i++) {
                logs.push(systemLogs.children[i].innerHTML);
            }

            let markup = "";
            for (let i = 0; i < logs.length; i++) {
                markup += createLogRecord(logs[i]);
            }
            systemLogs.innerHTML = markup;
        } else {
            let markup = "";
            for (let i = 0; i < logs.length; i++) {
                markup += createLogRecord(logs[i]);
            }
            systemLogs.insertAdjacentHTML("afterbegin", markup);
        }
    }


    // inits
    let chartCtx = document.getElementById('signal-chart').getContext('2d'),
        signalChart = new Chart(chartCtx, {
            type: 'line',
            options: chartOptions,
        });

    let chartTogglers = document.getElementsByClassName("chart-toggler");
    for (let i = 0; i < chartTogglers.length; i++) {
        let toggler = chartTogglers[i];
        toggler.addEventListener("click", changeChartType);
    }

    let streamSignal = new EventSource('/stream/signal'),
        streamWixelSessions = new EventSource('/stream/wxl_sessions'),
        streamLogging = new EventSource('/stream/logging');

    streamSignal.onmessage = function (event) {
        updateChartValues(signalChart, event.data);
    }
    streamWixelSessions.onmessage = function (event) {
        updateWixelSessions(event.data);
    }
    streamLogging.onmessage = function (event) {
        updateLogs(event.data);
    }

})();