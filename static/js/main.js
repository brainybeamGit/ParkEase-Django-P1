
document.addEventListener('DOMContentLoaded', () => {
    console.log("ParkEase Search Controller Initialized");

    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    let defaultArrivalH = now.getHours() + 1;
    let arrivalDate = new Date(today);
    if (defaultArrivalH >= 24) {
        defaultArrivalH = 0;
        arrivalDate.setDate(arrivalDate.getDate() + 1);
    }
    const defaultArrivalStr = `${String(defaultArrivalH).padStart(2, '0')}:00`;

    let fromState = {
        date: arrivalDate,
        time: defaultArrivalStr,
        viewYear: arrivalDate.getFullYear(),
        viewMonth: arrivalDate.getMonth()
    };

    let exitDate = new Date(arrivalDate);
    let exitH = defaultArrivalH + 2;
    if (exitH >= 24) {
        exitH = exitH % 24;
        exitDate.setDate(exitDate.getDate() + 1);
    }
    const defaultExitStr = `${String(exitH).padStart(2, '0')}:00`;

    let untilState = {
        date: exitDate,
        time: defaultExitStr,
        viewYear: exitDate.getFullYear(),
        viewMonth: exitDate.getMonth()
    };

    const fromBox = document.getElementById('jpFromBox');
    const untilBox = document.getElementById('jpUntilBox');
    const fromText = document.getElementById('jpFromText');
    const untilText = document.getElementById('jpUntilText');
    const popover = document.getElementById('jpDatetimePopover');
    const searchForm = document.getElementById('justParkSearchForm');

    const calMonthTitle = document.getElementById('jpCalMonthTitle');
    const calPrevBtn = document.getElementById('jpCalPrevBtn');
    const calNextBtn = document.getElementById('jpCalNextBtn');
    const calDaysGrid = document.getElementById('jpCalDaysGrid');
    const timeScrollList = document.getElementById('jpTimeScrollList');
    const popoverSummary = document.getElementById('jpPopoverSummary');
    const popoverDoneBtn = document.getElementById('jpPopoverDoneBtn');

    let activeMode = null;

    const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];

    function formatFriendlyDisplay(dateObj, timeStr) {
        const d = new Date(dateObj.getFullYear(), dateObj.getMonth(), dateObj.getDate());
        const t = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        const diffDays = Math.round((d - t) / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            return `Today at ${timeStr}`;
        } else if (diffDays === 1) {
            return `Tomorrow at ${timeStr}`;
        } else {
            const dayNum = dateObj.getDate();
            const mon = monthNames[dateObj.getMonth()].substring(0, 3);
            return `${dayNum} ${mon} at ${timeStr}`;
        }
    }

    function formatDateYMD(d) {
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
    }

    function syncDisplayAndInputs() {
        if (fromText) fromText.textContent = formatFriendlyDisplay(fromState.date, fromState.time);
        if (untilText) untilText.textContent = formatFriendlyDisplay(untilState.date, untilState.time);

        const fromDateInput = document.getElementById('hiddenFromDate');
        const fromTimeInput = document.getElementById('hiddenFromTime');
        const untilDateInput = document.getElementById('hiddenUntilDate');
        const untilTimeInput = document.getElementById('hiddenUntilTime');

        if (fromDateInput) fromDateInput.value = formatDateYMD(fromState.date);
        if (fromTimeInput) fromTimeInput.value = fromState.time;
        if (untilDateInput) untilDateInput.value = formatDateYMD(untilState.date);
        if (untilTimeInput) untilTimeInput.value = untilState.time;
    }

    function openPopover(mode) {
        activeMode = mode;
        const targetState = (mode === 'from') ? fromState : untilState;

        targetState.viewYear = targetState.date.getFullYear();
        targetState.viewMonth = targetState.date.getMonth();

        if (fromBox) fromBox.classList.toggle('active', mode === 'from');
        if (untilBox) untilBox.classList.toggle('active', mode === 'until');

        renderCalendar();
        renderTimeList();
        updatePopoverSummary();

        if (popover) {
            popover.style.display = 'block';
        }
    }

    function closePopover() {
        if (popover) popover.style.display = 'none';
        if (fromBox) fromBox.classList.remove('active');
        if (untilBox) untilBox.classList.remove('active');
        activeMode = null;
    }

    function renderCalendar() {
        if (!calMonthTitle || !calDaysGrid) return;
        const targetState = (activeMode === 'from') ? fromState : untilState;
        const year = targetState.viewYear;
        const month = targetState.viewMonth;

        calMonthTitle.textContent = `${monthNames[month]} ${year}`;

        const isCurrentMonthOrPast = (year < today.getFullYear()) || 
            (year === today.getFullYear() && month <= today.getMonth());
        if (calPrevBtn) calPrevBtn.disabled = isCurrentMonthOrPast;

        calDaysGrid.innerHTML = '';

        const firstDayObj = new Date(year, month, 1);
        let firstDayIndex = firstDayObj.getDay() - 1;
        if (firstDayIndex === -1) firstDayIndex = 6;

        const totalDays = new Date(year, month + 1, 0).getDate();

        for (let i = 0; i < firstDayIndex; i++) {
            const emptyCell = document.createElement('div');
            emptyCell.className = 'jp-cal-day empty';
            calDaysGrid.appendChild(emptyCell);
        }

        for (let d = 1; d <= totalDays; d++) {
            const dayEl = document.createElement('div');
            dayEl.className = 'jp-cal-day';
            dayEl.textContent = d;

            const thisDate = new Date(year, month, d);

            const isPast = (thisDate < today);

            const isBeforeFrom = (activeMode === 'until' && thisDate < new Date(fromState.date.getFullYear(), fromState.date.getMonth(), fromState.date.getDate()));

            if (isPast || isBeforeFrom) {
                dayEl.classList.add('disabled');
                dayEl.title = "Past dates cannot be selected";
            } else {
                if (thisDate.getTime() === today.getTime()) {
                    dayEl.classList.add('today');
                }

                const selDate = targetState.date;
                if (thisDate.getFullYear() === selDate.getFullYear() &&
                    thisDate.getMonth() === selDate.getMonth() &&
                    thisDate.getDate() === selDate.getDate()) {
                    dayEl.classList.add('selected');
                }

                dayEl.addEventListener('click', (e) => {
                    e.stopPropagation();
                    targetState.date = new Date(year, month, d);

                    if (activeMode === 'from' && untilState.date < targetState.date) {
                        untilState.date = new Date(targetState.date);
                    }

                    renderCalendar();
                    updatePopoverSummary();
                    syncDisplayAndInputs();
                });
            }

            calDaysGrid.appendChild(dayEl);
        }
    }

    function renderTimeList() {
        if (!timeScrollList) return;
        timeScrollList.innerHTML = '';

        const targetState = (activeMode === 'from') ? fromState : untilState;

        for (let h = 0; h < 24; h++) {
            for (let m = 0; m < 60; m += 30) {
                const timeStr = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'jp-time-slot-btn';
                btn.textContent = timeStr;

                if (timeStr === targetState.time) {
                    btn.classList.add('selected');
                }

                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    targetState.time = timeStr;

                    renderTimeList();
                    updatePopoverSummary();
                    syncDisplayAndInputs();
                });

                timeScrollList.appendChild(btn);
            }
        }

        setTimeout(() => {
            const selectedBtn = timeScrollList.querySelector('.jp-time-slot-btn.selected');
            if (selectedBtn) {
                selectedBtn.scrollIntoView({ block: 'center', behavior: 'auto' });
            }
        }, 30);
    }

    function updatePopoverSummary() {
        if (!popoverSummary) return;
        const targetState = (activeMode === 'from') ? fromState : untilState;
        const prefix = (activeMode === 'from') ? "Enter after" : "Exit before";
        popoverSummary.innerHTML = `${prefix}: <strong>${formatFriendlyDisplay(targetState.date, targetState.time)}</strong>`;
    }

    if (calPrevBtn) {
        calPrevBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const targetState = (activeMode === 'from') ? fromState : untilState;
            targetState.viewMonth--;
            if (targetState.viewMonth < 0) {
                targetState.viewMonth = 11;
                targetState.viewYear--;
            }
            renderCalendar();
        });
    }

    if (calNextBtn) {
        calNextBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const targetState = (activeMode === 'from') ? fromState : untilState;
            targetState.viewMonth++;
            if (targetState.viewMonth > 11) {
                targetState.viewMonth = 0;
                targetState.viewYear++;
            }
            renderCalendar();
        });
    }

    if (fromBox) {
        fromBox.addEventListener('click', (e) => {
            e.stopPropagation();
            if (activeMode === 'from') {
                closePopover();
            } else {
                openPopover('from');
            }
        });
    }

    if (untilBox) {
        untilBox.addEventListener('click', (e) => {
            e.stopPropagation();
            if (activeMode === 'until') {
                closePopover();
            } else {
                openPopover('until');
            }
        });
    }

    if (popoverDoneBtn) {
        popoverDoneBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            closePopover();
        });
    }

    if (popover) {
        popover.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }


    const destinationFieldGroup = document.getElementById('destinationFieldGroup');
    const airportFieldGroup = document.getElementById('airportFieldGroup');
    const hourlyDatetimeRow = document.getElementById('hourlyDatetimeRow');
    const monthlyDatetimeRow = document.getElementById('monthlyDatetimeRow');
    const fromBoxLabel = document.getElementById('fromBoxLabel');
    const untilBoxLabel = document.getElementById('untilBoxLabel');

    const jpTabBtns = document.querySelectorAll('.jp-tab-btn');
    if (jpTabBtns.length > 0) {
        jpTabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                jpTabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const mode = btn.dataset.tab;
                const modeInput = document.getElementById('hiddenSearchMode');
                if (modeInput) modeInput.value = mode;

                closePopover();
                closeMonthlyCalPopover();
                closeMonthlyAvailabilityPopover();

                if (mode === 'monthly') {
                    if (destinationFieldGroup) destinationFieldGroup.classList.remove('d-none');
                    if (airportFieldGroup) airportFieldGroup.classList.add('d-none');
                    if (hourlyDatetimeRow) hourlyDatetimeRow.classList.add('d-none');
                    if (monthlyDatetimeRow) monthlyDatetimeRow.classList.remove('d-none');
                } else if (mode === 'airport') {
                    if (destinationFieldGroup) destinationFieldGroup.classList.add('d-none');
                    if (airportFieldGroup) airportFieldGroup.classList.remove('d-none');
                    if (hourlyDatetimeRow) hourlyDatetimeRow.classList.remove('d-none');
                    if (monthlyDatetimeRow) monthlyDatetimeRow.classList.add('d-none');
                    if (fromBoxLabel) fromBoxLabel.textContent = 'Fly out';
                    if (untilBoxLabel) untilBoxLabel.textContent = 'Fly back';
                } else {
                    
                    if (destinationFieldGroup) destinationFieldGroup.classList.remove('d-none');
                    if (airportFieldGroup) airportFieldGroup.classList.add('d-none');
                    if (hourlyDatetimeRow) hourlyDatetimeRow.classList.remove('d-none');
                    if (monthlyDatetimeRow) monthlyDatetimeRow.classList.add('d-none');
                    if (fromBoxLabel) fromBoxLabel.textContent = 'From';
                    if (untilBoxLabel) untilBoxLabel.textContent = 'Until';
                }
            });
        });

        try {
            const urlParams = new URLSearchParams(window.location.search);
            const paramMode = urlParams.get('mode');
            const paramQ = urlParams.get('q');
            const paramAirport = urlParams.get('airport');

            if (paramMode) {
                const targetBtn = document.querySelector('.jp-tab-btn[data-tab="' + paramMode + '"]');
                if (targetBtn) targetBtn.click();
            }
            if (paramQ && destinationInput) {
                destinationInput.value = paramQ;
            }
            if (paramAirport) {
                const airportSel = document.getElementById('airportSelect');
                if (airportSel) {
                    airportSel.value = paramAirport;
                }
            }
        } catch (e) {
            console.warn('Error reading URL params:', e);
        }

        if (window.location.hash === '#searchSection') {
            const searchCard = document.getElementById('searchSection');
            if (searchCard) {
                setTimeout(function() {
                    searchCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    if (destinationInput) destinationInput.focus();
                }, 350);
            }
        }

        document.querySelectorAll('a[href*="#searchSection"]').forEach(function(link) {
            link.addEventListener('click', function(e) {
                if (window.location.pathname === '/' || window.location.pathname.endsWith('/home/')) {
                    const searchCard = document.getElementById('searchSection');
                    if (searchCard) {
                        e.preventDefault();
                        searchCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        if (destinationInput) destinationInput.focus();
                        history.pushState(null, null, '#searchSection');
                    }
                }
            });
        });
    }

    
    const monthlyStartBox = document.getElementById('jpMonthlyStartBox');
    const monthlyStartText = document.getElementById('jpMonthlyStartText');
    const monthlyCalPopover = document.getElementById('jpMonthlyCalendarPopover');
    const monthlyCalMonthTitle = document.getElementById('jpMonthlyCalMonthTitle');
    const monthlyCalPrevBtn = document.getElementById('jpMonthlyCalPrevBtn');
    const monthlyCalNextBtn = document.getElementById('jpMonthlyCalNextBtn');
    const monthlyCalDaysGrid = document.getElementById('jpMonthlyCalDaysGrid');
    const monthlyCalDoneBtn = document.getElementById('jpMonthlyCalDoneBtn');
    const hiddenMonthlyStartDate = document.getElementById('hiddenMonthlyStartDate');

    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    let monthlyStartDate = new Date(tomorrow);
    let monthlyCalViewYear = monthlyStartDate.getFullYear();
    let monthlyCalViewMonth = monthlyStartDate.getMonth();

    function formatMonthlyStartLabel(d) {
        const isTomorrow = d.getFullYear() === tomorrow.getFullYear() &&
                           d.getMonth() === tomorrow.getMonth() &&
                           d.getDate() === tomorrow.getDate();
        if (isTomorrow) return "Tomorrow";
        return `${d.getDate()} ${monthNames[d.getMonth()].slice(0, 3)} ${d.getFullYear()}`;
    }

    function syncMonthlyStartInput() {
        if (monthlyStartText) monthlyStartText.textContent = formatMonthlyStartLabel(monthlyStartDate);
        if (hiddenMonthlyStartDate) {
            const y = monthlyStartDate.getFullYear();
            const m = String(monthlyStartDate.getMonth() + 1).padStart(2, '0');
            const day = String(monthlyStartDate.getDate()).padStart(2, '0');
            hiddenMonthlyStartDate.value = `${y}-${m}-${day}`;
        }
    }
    syncMonthlyStartInput();

    function openMonthlyCalPopover() {
        closeMonthlyAvailabilityPopover();
        closePopover();
        if (monthlyStartBox) monthlyStartBox.classList.add('active');
        monthlyCalViewYear = monthlyStartDate.getFullYear();
        monthlyCalViewMonth = monthlyStartDate.getMonth();
        renderMonthlyCalendar();
        if (monthlyCalPopover) monthlyCalPopover.style.display = 'block';
    }

    function closeMonthlyCalPopover() {
        if (monthlyCalPopover) monthlyCalPopover.style.display = 'none';
        if (monthlyStartBox) monthlyStartBox.classList.remove('active');
    }

    function renderMonthlyCalendar() {
        if (!monthlyCalMonthTitle || !monthlyCalDaysGrid) return;
        monthlyCalMonthTitle.textContent = `${monthNames[monthlyCalViewMonth]} ${monthlyCalViewYear}`;

        if (monthlyCalPrevBtn) {
            const isCurrentOrPastMonth = (monthlyCalViewYear < today.getFullYear()) ||
                (monthlyCalViewYear === today.getFullYear() && monthlyCalViewMonth <= today.getMonth());
            monthlyCalPrevBtn.disabled = isCurrentOrPastMonth;
        }

        monthlyCalDaysGrid.innerHTML = '';
        const firstDayIdx = new Date(monthlyCalViewYear, monthlyCalViewMonth, 1).getDay();
        const mondayOffset = (firstDayIdx === 0) ? 6 : firstDayIdx - 1;

        for (let i = 0; i < mondayOffset; i++) {
            const emptyEl = document.createElement('div');
            emptyEl.className = 'jp-cal-day empty';
            monthlyCalDaysGrid.appendChild(emptyEl);
        }

        const totalDays = new Date(monthlyCalViewYear, monthlyCalViewMonth + 1, 0).getDate();
        for (let d = 1; d <= totalDays; d++) {
            const dateObj = new Date(monthlyCalViewYear, monthlyCalViewMonth, d);
            const dayEl = document.createElement('div');
            dayEl.className = 'jp-cal-day';
            dayEl.textContent = d;

            const isPast = dateObj < today;
            const isToday = dateObj.getTime() === today.getTime();
            const isSelected = dateObj.getFullYear() === monthlyStartDate.getFullYear() &&
                               dateObj.getMonth() === monthlyStartDate.getMonth() &&
                               dateObj.getDate() === monthlyStartDate.getDate();

            if (isPast) {
                dayEl.classList.add('disabled');
            } else {
                if (isToday) dayEl.classList.add('today');
                if (isSelected) dayEl.classList.add('selected');

                dayEl.addEventListener('click', (e) => {
                    e.stopPropagation();
                    monthlyStartDate = new Date(dateObj);
                    renderMonthlyCalendar();
                    syncMonthlyStartInput();
                });
            }
            monthlyCalDaysGrid.appendChild(dayEl);
        }
    }

    if (monthlyCalPrevBtn) {
        monthlyCalPrevBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            monthlyCalViewMonth--;
            if (monthlyCalViewMonth < 0) {
                monthlyCalViewMonth = 11;
                monthlyCalViewYear--;
            }
            renderMonthlyCalendar();
        });
    }

    if (monthlyCalNextBtn) {
        monthlyCalNextBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            monthlyCalViewMonth++;
            if (monthlyCalViewMonth > 11) {
                monthlyCalViewMonth = 0;
                monthlyCalViewYear++;
            }
            renderMonthlyCalendar();
        });
    }

    if (monthlyStartBox) {
        monthlyStartBox.addEventListener('click', (e) => {
            e.stopPropagation();
            if (monthlyCalPopover && monthlyCalPopover.style.display === 'block') {
                closeMonthlyCalPopover();
            } else {
                openMonthlyCalPopover();
            }
        });
    }

    if (monthlyCalDoneBtn) {
        monthlyCalDoneBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            closeMonthlyCalPopover();
        });
    }

    if (monthlyCalPopover) {
        monthlyCalPopover.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }


    const monthlyAvailabilityBox = document.getElementById('jpMonthlyAvailabilityBox');
    const monthlyAvailabilityText = document.getElementById('jpMonthlyAvailabilityText');
    const monthlyAvailabilityPopover = document.getElementById('jpMonthlyAvailabilityPopover');
    const availabilityDoneBtn = document.getElementById('jpAvailabilityDoneBtn');
    const hiddenMonthlyAvailability = document.getElementById('hiddenMonthlyAvailability');
    const availabilityOptions = document.querySelectorAll('.jp-radio-option');

    function openMonthlyAvailabilityPopover() {
        closeMonthlyCalPopover();
        closePopover();
        if (monthlyAvailabilityBox) monthlyAvailabilityBox.classList.add('active');
        if (monthlyAvailabilityPopover) monthlyAvailabilityPopover.style.display = 'block';
    }

    function closeMonthlyAvailabilityPopover() {
        if (monthlyAvailabilityPopover) monthlyAvailabilityPopover.style.display = 'none';
        if (monthlyAvailabilityBox) monthlyAvailabilityBox.classList.remove('active');
    }

    if (monthlyAvailabilityBox) {
        monthlyAvailabilityBox.addEventListener('click', (e) => {
            e.stopPropagation();
            if (monthlyAvailabilityPopover && monthlyAvailabilityPopover.style.display === 'block') {
                closeMonthlyAvailabilityPopover();
            } else {
                openMonthlyAvailabilityPopover();
            }
        });
    }

    if (availabilityOptions.length > 0) {
        availabilityOptions.forEach(opt => {
            opt.addEventListener('click', (e) => {
                e.stopPropagation();
                availabilityOptions.forEach(o => {
                    o.classList.remove('selected');
                    const radio = o.querySelector('.jp-radio-input');
                    if (radio) radio.checked = false;
                });
                opt.classList.add('selected');
                const radio = opt.querySelector('.jp-radio-input');
                if (radio) radio.checked = true;
                const val = opt.dataset.value;
                if (monthlyAvailabilityText) monthlyAvailabilityText.textContent = val;
                if (hiddenMonthlyAvailability) hiddenMonthlyAvailability.value = val;
            });
        });
    }

    if (availabilityDoneBtn) {
        availabilityDoneBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            closeMonthlyAvailabilityPopover();
        });
    }

    if (monthlyAvailabilityPopover) {
        monthlyAvailabilityPopover.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    document.addEventListener('click', (e) => {
        if (popover && popover.style.display === 'block') {
            closePopover();
        }
        if (monthlyCalPopover && monthlyCalPopover.style.display === 'block') {
            closeMonthlyCalPopover();
        }
        if (monthlyAvailabilityPopover && monthlyAvailabilityPopover.style.display === 'block') {
            closeMonthlyAvailabilityPopover();
        }
    });

    const vehicleSelect = document.getElementById('vehicleTypeSelect');
    const hiddenVehicleType = document.getElementById('hiddenVehicleType');
    if (vehicleSelect && hiddenVehicleType) {
        vehicleSelect.addEventListener('change', () => {
            hiddenVehicleType.value = vehicleSelect.value;
        });
    }


    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            const destInput = document.getElementById('destinationInput') || document.getElementById('reserveWhereInput');
            const airportSel = document.getElementById('airportSelect');
            const modeInput = document.getElementById('hiddenSearchMode');
            const currentMode = modeInput ? modeInput.value : 'hourly';

            if (currentMode === 'airport' && airportSel && destInput) {
                destInput.value = airportSel.options[airportSel.selectedIndex].text;
            }
        });
    }

    function setupNominatimAutocomplete(inputId) {
        const input = document.getElementById(inputId);
        if (!input) return;

        let dropdown = document.getElementById(inputId + '_nominatim_dropdown');
        if (!dropdown) {
            dropdown = document.createElement('div');
            dropdown.id = inputId + '_nominatim_dropdown';
            dropdown.className = 'nominatim-home-dropdown d-none';
            if (input.parentNode) {
                input.parentNode.style.position = 'relative';
                input.parentNode.appendChild(dropdown);
            }
        }

        let debounce = null;
        input.addEventListener('input', function () {
            clearTimeout(debounce);
            const val = this.value.trim();
            if (val.length < 3) {
                dropdown.classList.add('d-none');
                dropdown.innerHTML = '';
                return;
            }

            debounce = setTimeout(() => {
                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(val)}&countrycodes=in&limit=5`, {
                    headers: { 'User-Agent': 'ParkEaseApp/1.0' }
                })
                .then(r => r.json())
                .then(items => {
                    if (!items || items.length === 0) {
                        dropdown.classList.add('d-none');
                        return;
                    }
                    dropdown.innerHTML = '';
                    items.forEach(item => {
                        const row = document.createElement('div');
                        row.className = 'nominatim-home-item';
                        row.innerHTML = `<i class="bi bi-geo-alt-fill text-primary me-2"></i><span>${item.display_name}</span>`;
                        row.addEventListener('click', (e) => {
                            e.stopPropagation();
                            input.value = item.display_name.split(',').slice(0, 3).join(',').trim();
                            dropdown.classList.add('d-none');
                        });
                        dropdown.appendChild(row);
                    });
                    dropdown.classList.remove('d-none');
                })
                .catch(() => {
                    dropdown.classList.add('d-none');
                });
            }, 350);
        });

        document.addEventListener('click', (e) => {
            if (!input.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.classList.add('d-none');
            }
        });
    }

    setupNominatimAutocomplete('destinationInput');
    setupNominatimAutocomplete('reserveWhereInput');


    const backToTopBtn = document.getElementById('pwBackToTopBtn');
    if (backToTopBtn) {
        backToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }


    const fpTrack = document.getElementById('findParkingTrack');
    if (fpTrack) {
        const dots = document.querySelectorAll('.fp-dot');
        const slideItems = fpTrack.querySelectorAll('.find-parking-slide-item');
        let isDown = false;
        let startX = 0;
        let scrollStartLeft = 0;
        let hasMoved = false;

        const prevArrow = document.getElementById('fpFloatingArrowPrev');
        const nextArrow = document.getElementById('fpFloatingArrowNext');

        const updateArrows = () => {
            const maxScroll = fpTrack.scrollWidth - fpTrack.clientWidth;
            if (maxScroll <= 5) {
                if (prevArrow) {
                    prevArrow.style.opacity = '0';
                    prevArrow.style.visibility = 'hidden';
                    prevArrow.style.pointerEvents = 'none';
                }
                if (nextArrow) {
                    nextArrow.style.opacity = '0';
                    nextArrow.style.visibility = 'hidden';
                    nextArrow.style.pointerEvents = 'none';
                }
                return;
            }

            const currentScroll = fpTrack.scrollLeft;
            const isAtStart = currentScroll <= 25;
            const isAtEnd = currentScroll >= (maxScroll - 25);

            if (prevArrow) {
                if (isAtStart) {
                    prevArrow.style.opacity = '0';
                    prevArrow.style.visibility = 'hidden';
                    prevArrow.style.pointerEvents = 'none';
                } else {
                    prevArrow.style.opacity = '1';
                    prevArrow.style.visibility = 'visible';
                    prevArrow.style.pointerEvents = 'auto';
                }
            }

            if (nextArrow) {
                if (isAtEnd) {
                    nextArrow.style.opacity = '0';
                    nextArrow.style.visibility = 'hidden';
                    nextArrow.style.pointerEvents = 'none';
                } else {
                    nextArrow.style.opacity = '1';
                    nextArrow.style.visibility = 'visible';
                    nextArrow.style.pointerEvents = 'auto';
                }
            }

            const activeIndex = (currentScroll > maxScroll * 0.35) ? 1 : 0;
            dots.forEach((dot, idx) => {
                if (idx === activeIndex) {
                    dot.classList.add('active');
                } else {
                    dot.classList.remove('active');
                }
            });
        };

        if (nextArrow) {
            nextArrow.addEventListener('click', (e) => {
                e.preventDefault();
                const targetCard = slideItems[2] || slideItems[slideItems.length - 1];
                if (targetCard) {
                    fpTrack.scrollTo({
                        left: targetCard.offsetLeft - fpTrack.offsetLeft,
                        behavior: 'smooth'
                    });
                }
            });
        }

        if (prevArrow) {
            prevArrow.addEventListener('click', (e) => {
                e.preventDefault();
                fpTrack.scrollTo({
                    left: 0,
                    behavior: 'smooth'
                });
            });
        }

        fpTrack.addEventListener('mousedown', (e) => {
            isDown = true;
            hasMoved = false;
            fpTrack.classList.add('is-dragging');
            startX = e.pageX - fpTrack.offsetLeft;
            scrollStartLeft = fpTrack.scrollLeft;
        });

        window.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            const x = e.pageX - fpTrack.offsetLeft;
            const walk = (x - startX) * 1.6; // Cursor drag sensitivity multiplier
            if (Math.abs(walk) > 4) {
                hasMoved = true;
            }
            fpTrack.scrollLeft = scrollStartLeft - walk;
        });

        window.addEventListener('mouseup', () => {
            if (!isDown) return;
            isDown = false;
            fpTrack.classList.remove('is-dragging');
            setTimeout(updateArrows, 150);
        });

        fpTrack.addEventListener('scroll', () => {
            if (!isDown) {
                updateArrows();
            }
        }, { passive: true });

        fpTrack.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', (e) => {
                if (hasMoved) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            });
        });

        dots.forEach((dot) => {
            dot.addEventListener('click', () => {
                const slideIdx = parseInt(dot.dataset.slide, 10);
                const targetCard = slideIdx === 0 ? slideItems[0] : slideItems[2];
                if (targetCard) {
                    fpTrack.scrollTo({
                        left: targetCard.offsetLeft - fpTrack.offsetLeft,
                        behavior: 'smooth'
                    });
                }
                dots.forEach(d => d.classList.remove('active'));
                dot.classList.add('active');
            });
        });

        setTimeout(updateArrows, 100);
    }

    const navCategoryLinks = document.querySelectorAll('.nav-link-item');
    if (navCategoryLinks.length > 0) {
        navCategoryLinks.forEach(link => {
            link.addEventListener('click', function() {
                navCategoryLinks.forEach(l => l.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }

    syncDisplayAndInputs();
});
