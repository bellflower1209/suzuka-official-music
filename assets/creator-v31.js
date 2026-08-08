(() => {
  const updateCountdown=element=>{const output=element.querySelector('[data-countdown-output]')||(element.matches('[data-countdown-output]')?element:null);if(!output)return;
    const target=Date.parse(element.dataset.releaseAt);if(!Number.isFinite(target)){output.textContent='公開予定日時を確認できません';return;}
    const diff=target-Date.now();if(diff<=0){output.textContent='公開予定時刻を迎えました。公式YouTubeの公開状態を確認中です。';return;}
    const minutes=Math.floor(diff/60000),days=Math.floor(minutes/1440),hours=Math.floor((minutes%1440)/60),mins=minutes%60;
    output.textContent=`あと ${days}日 ${hours}時間 ${mins}分`;
  };document.querySelectorAll('[data-countdown]').forEach(el=>{updateCountdown(el);setInterval(()=>updateCountdown(el),60000);});
  const filter=document.querySelector('[data-lyrics-filter]'),list=document.querySelector('[data-lyrics-list]');if(filter&&list)filter.addEventListener('input',()=>{const q=filter.value.normalize('NFKC').toLocaleLowerCase('ja').replace(/\s+/g,'');list.querySelectorAll('[data-lyrics-entry]').forEach(row=>{row.hidden=q&&!row.dataset.search.normalize('NFKC').toLocaleLowerCase('ja').replace(/\s+/g,'').includes(q);});});
})();
