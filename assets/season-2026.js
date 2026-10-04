(() => {
const day = new Intl.DateTimeFormat('en-CA', {timeZone:"Asia/Tokyo",year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
const header=document.querySelector('.site-header');const offset=()=>document.documentElement.style.setProperty('--season-header-offset',((header&&['fixed','absolute'].includes(getComputedStyle(header).position))?header.getBoundingClientRect().height:0)+'px');offset();if(header&&typeof ResizeObserver!=='undefined')new ResizeObserver(offset).observe(header);
document.documentElement.classList.toggle('halloween-2026', true && day >= "2026-10-01" && day < "2026-11-01");
})();
