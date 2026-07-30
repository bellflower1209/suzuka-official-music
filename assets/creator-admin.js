(() => {
  const area = document.querySelector("#cms-json"), status = document.querySelector("#cms-status");
  const validate = () => {
    const data = JSON.parse(area.value);
    const required = ["artists","releases","upcoming","news","taxonomy","playlistDefinitions"];
    const missing = required.filter(key => !Array.isArray(data[key]) && typeof data[key] !== "object");
    if (data.schemaVersion !== "3.0" || missing.length) throw new Error("必須項目不足: " + missing.join(", "));
    return data;
  };
  document.querySelector("#cms-validate").onclick = () => { try { const d=validate(); status.textContent=`検証OK: ${d.releases.length}作品 / ${d.artists.length}アーティスト`; } catch(e){ status.textContent="検証エラー: "+e.message; } };
  document.querySelector("#cms-save").onclick = () => { try { validate(); localStorage.setItem("suzuka-creator-cms-draft",area.value); status.textContent="下書きをこの端末に保存しました。"; } catch(e){ status.textContent="保存できません: "+e.message; } };
  document.querySelector("#cms-download").onclick = () => { try { validate(); const a=document.createElement("a"); a.href=URL.createObjectURL(new Blob([area.value+"\n"],{type:"application/json"})); a.download="creator-cms.json"; a.click(); URL.revokeObjectURL(a.href); } catch(e){ status.textContent="書き出せません: "+e.message; } };
  document.querySelector("#cms-import").onchange = async e => { const file=e.target.files[0]; if(file){area.value=await file.text(); document.querySelector("#cms-validate").click();} };
  const draft=localStorage.getItem("suzuka-creator-cms-draft"); if(draft) area.value=draft;
})();
