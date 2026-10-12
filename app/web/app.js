"use strict";
const ui=window.PolitUI;
let language=ui.readLanguage();
let names=ui.datasets(language);
const t=(key,values)=>ui.t(language,key,values);
const state={dataset:"affairs",filterDrafts:{},controller:null,page:1,pages:0,categories:[],cantons:[],account:null,affairId:null,groupId:null,personId:null,agendaId:null,meetingId:null,request:0,detailRequest:0,detail:null,subscriptions:null,result:null};
const $=id=>document.getElementById(id);
function el(tag,text,className){const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(className)node.className=className;return node;}
async function api(path,options={}){
  const response=await fetch(path,{credentials:"same-origin",...options,headers:{...(options.body?{"Content-Type":"application/json"}:{}),...options.headers}});
  if(!response.ok){let detail;try{detail=(await response.json()).detail;}catch{detail=response.statusText;}throw new Error(typeof detail==="string"?detail:JSON.stringify(detail));}
  return response.status===204?null:response.json();
}
function status(id,text,error=false){$(id).textContent=text;$(id).classList.toggle("error",error);$(id).hidden=!text;}
function option(select,value,label){const node=el("option",label);node.value=value;select.append(node);}
function categoryName(item){
  const code=item.code||item.category_code;
  if(ui.translations[code])return t(code);
  const category=state.categories.flatMap(parent=>[parent,...parent.subcategories]).find(row=>row.code===code);
  return ui.localized(category||item,"name",language)||item.category_name_de||item.name||code;
}
function updateSubcategories(preserve=false){
  const previous=preserve?$("subcategory").value:"";
  const parent=state.categories.find(item=>item.code===$("category").value);
  $("subcategory").replaceChildren();option($("subcategory"),"",t("allSubtopics"));
  for(const child of parent?.subcategories||[])option($("subcategory"),child.code,categoryName(child));
  if(previous)$("subcategory").value=previous;
}
function translatePage(){
  document.documentElement.lang=language;names=ui.datasets(language);$("language").value=language;
  document.querySelectorAll("[data-i18n]").forEach(node=>node.textContent=t(node.dataset.i18n));
  document.querySelectorAll("[data-i18n-placeholder]").forEach(node=>node.placeholder=t(node.dataset.i18nPlaceholder));
  document.querySelectorAll("[data-i18n-aria]").forEach(node=>node.setAttribute("aria-label",t(node.dataset.i18nAria)));
  $("datasets").replaceChildren();
  for(const [dataset,name] of Object.entries(names)){
    const button=el("button",name);button.type="button";button.dataset.value=dataset;
    button.classList.toggle("active",dataset===state.dataset);button.setAttribute("aria-pressed",String(dataset===state.dataset));
    button.addEventListener("click",()=>chooseDataset(dataset));$("datasets").append(button);
  }
  $("heading").textContent=names[state.dataset];
  const selected=$("category").value;$("category").replaceChildren();option($("category"),"",t("allTopics"));
  for(const category of state.categories)option($("category"),category.code,categoryName(category));
  $("category").value=selected;updateSubcategories(true);
  const canton=$("canton").value;$("canton").replaceChildren();option($("canton"),"",t("allCantons"));
  for(const row of state.cantons)option($("canton"),row.code,row.name);$("canton").value=canton;
  for(const id of ["account-message","subscription-message"])status(id,"");
  renderMembership();renderContextNavigation();
}
function renderMembership(){
  $("membership-summary").textContent=state.account?t("accountActive",{email:state.account.email}):"";
  $("membership-login").hidden=!!state.account;$("membership-register").hidden=!!state.account;
  $("membership-view").hidden=!state.account;
  $("membership-logout").hidden=!state.account;
  $("account-form").hidden=!!state.account;
  $("account-help").hidden=!!state.account;
  $("account-summary").hidden=!state.account;
  $("account-summary").textContent=state.account?t("accountActive",{email:state.account.email}):"";
  $("account-title").textContent=t(state.account?"account":"login");
}
const authChannel=typeof BroadcastChannel!=="undefined"?new BroadcastChannel("polit-auth"):null;
async function applySignIn(){
  await refreshAccount();if(!state.account)return false;
  if($("account-dialog").open)$("account-dialog").close();
  status("message","");await openSubscriptions();return true;
}
if(authChannel)authChannel.addEventListener("message",async event=>{
  if(event.data?.type==="signed-in"&&await applySignIn()){
    authChannel.postMessage({type:"ack",id:event.data.id});window.focus();
  }
});
window.addEventListener("storage",event=>{if(event.key==="polit-auth-updated")applySignIn();});
async function announceSignIn(){
  if(!state.account)return;
  const id=crypto.randomUUID();
  if(authChannel)authChannel.addEventListener("message",event=>{
    if(event.data?.type==="ack"&&event.data.id===id)window.close();
  });
  try{localStorage.setItem("polit-auth-updated",id);}catch{}
  authChannel?.postMessage({type:"signed-in",id});status("message","");
}
function renderContextNavigation(){
  const container=$("context-navigation");container.replaceChildren();container.hidden=!(state.affairId||state.groupId||state.personId||state.agendaId||state.meetingId);
  if(!container.hidden){const button=el("button",t("backToAffairs"));button.addEventListener("click",()=>chooseDataset(state.dataset));container.append(button);}
}
function chooseDataset(dataset,filters={}){
  state.result=null;
  state.filterDrafts[state.dataset]=Object.fromEntries(new FormData($("search-form")));
  state.dataset=dataset;state.page=1;
  const draft=state.filterDrafts[dataset]||{};
  for(const node of $("search-form").elements)if(node.name)node.value=draft[node.name]||"";
  updateSubcategories();$("subcategory").value=draft.subcategory||"";state.affairId=filters.affairId||null;state.groupId=filters.groupId||null;state.personId=filters.personId||null;
  state.agendaId=filters.agendaId||null;state.meetingId=filters.meetingId||null;
  $("heading").textContent=names[dataset];for(const button of $("datasets").children){const active=button.dataset.value===dataset;button.classList.toggle("active",active);button.setAttribute("aria-pressed",String(active));}loadResults();
  renderContextNavigation();
}
function browseRelated(dataset,filters){$("detail-dialog").close();$("search-form").reset();setTimeout(()=>chooseDataset(dataset,filters),1);}
function formatDate(value){if(!value)return t("noDate");return new Intl.DateTimeFormat(`${language}-CH`,{dateStyle:"medium",timeZone:"Europe/Zurich"}).format(new Date(value));}
async function loadResults(){
  const request=++state.request,dataset=state.dataset;
  state.controller?.abort();state.controller=new AbortController();
  const params=new URLSearchParams(new FormData($("search-form")));for(const [key,value]of [...params])if(!value)params.delete(key);
  params.set("page",state.page);if(state.affairId)params.set("affair_id",state.affairId);if(state.groupId)params.set("group_id",state.groupId);if(state.personId)params.set("person_id",state.personId);
  if(state.agendaId)params.set("agenda_id",state.agendaId);if(state.meetingId)params.set("meeting_id",state.meetingId);
  $("results").setAttribute("aria-busy","true");status("message","");$("previous").disabled=true;$("next").disabled=true;$("result-count").textContent=t("loading");
  try{
    const result=await api(`/api/v1/entities/${dataset}?${params}`,{signal:state.controller.signal});if(request!==state.request)return;
    state.result=result;renderResults(result,dataset);
  }catch(error){if(request===state.request){status("message",error.message,true);$("result-count").textContent=t("loadError");$("results").replaceChildren();}}
  finally{if(request===state.request)$("results").setAttribute("aria-busy","false");}
}
function renderResults(result,dataset=state.dataset){
    state.pages=result.pagination.total_pages;$("results").replaceChildren();
    $("result-count").textContent=t("resultCount",{count:result.pagination.total_items.toLocaleString(`${language}-CH`)});
    for(const item of result.items){
      const dataset=item.dataset||state.dataset;
      const card=el("article",undefined,"result-card");card.append(el("span",names[dataset],"tag type-tag"));card.append(el("div",`${item.canton||t("noCanton")} · ${formatDate(item.date)}`,"card-meta"));
      if(dataset==="agendas")card.append(el("p",t(item.title_origin==="meeting"?"meetingAgenda":"agendaItem")+(item.item_number?` · ${item.item_number}`:""),"card-meta"));
      const heading=el("h2"),link=el("button",recordTitle(dataset,item));link.addEventListener("click",()=>showDetail(dataset,item.id));heading.append(link);card.append(heading);
      const context=[item.body?.name,item.kind,item.state,item.person?.fullname,item.role,item.group?.title,item.location,item.decision].filter(Boolean);
      if(context.length)card.append(el("p",context.join(" · "),"card-context"));
      const tags=el("div",undefined,"tags");for(const category of item.categories)tags.append(el("span",categoryName(category),"tag"));
      if(!item.categories.length&&dataset!=="agendas")tags.append(el("span",t("noClassification"),"tag"));card.append(tags);
      {
        const links=el("div",undefined,"agenda-links");
        if(item.meeting){const button=el("button",item.title_origin==="meeting"?t("openMeeting"):item.meeting.title||t("meetings"));button.addEventListener("click",()=>showDetail("meetings",item.meeting.id));links.append(button);}
        if(item.affair){const button=el("button",item.affair.number||t("openAffair"));button.addEventListener("click",()=>showDetail("affairs",item.affair.id));links.append(button);}
        if(item.source_url&&safeLink(item.source_url)){const source=el("a",t("officialSource"));source.href=safeLink(item.source_url);source.target="_blank";source.rel="noopener noreferrer";links.append(source);}card.append(links);
      }
      $("results").append(card);
    }
    if(!result.items.length)$("results").append(el("div",t("empty"),"empty"));
    $("page-label").textContent=state.pages?t("page",{page:state.page,pages:state.pages}):t("noResults");$("previous").disabled=state.page<=1;$("next").disabled=state.page>=state.pages;
}
function safeLink(url){try{const parsed=new URL(url,location.origin);return ["http:","https:"].includes(parsed.protocol)?parsed.href:null;}catch{return null;}}
function sourceTitle(dataset,record){return ui.localized(record,"title",language)||ui.localized(record,"name",language)||record.item_title||record.name||names[dataset];}
function recordTitle(dataset,item){const title=item.title||names[dataset];return ["events","votings","texts","documents"].includes(dataset)&&item.context_title&&item.context_title!==title?`${title} · ${item.context_title}`:title;}
async function showDetail(dataset,id){
  const request=++state.detailRequest;state.detail=null;$("detail-title").textContent=names[dataset];$("detail-content").replaceChildren(el("p",t("detailLoading")));
  if(!$("detail-dialog").open)$("detail-dialog").showModal();
  try{const data=await api(`/api/v1/entities/${dataset}/${id}`);if(request!==state.detailRequest||!$("detail-dialog").open)return;state.detail={dataset,id,data};renderDetail();}
  catch(error){if(request===state.detailRequest)$("detail-content").replaceChildren(el("p",error.message,"error"));}
}
function renderRelated(container,dataset,result,filters,moreLabel="all"){
  if(!result?.pagination.total_items)return;
  const section=el("section",undefined,"related-section");section.append(el("h3",`${names[dataset]} (${result.pagination.total_items})`));
  for(const item of result.items){const button=el("button",`${formatDate(item.date)} · ${recordTitle(dataset,item)}${item.decision?` · ${item.decision}`:""}`,"related-item");button.addEventListener("click",()=>showDetail(dataset,item.id));section.append(button);}
  if(result.pagination.total_items>result.items.length){const button=el("button",t(moreLabel));button.addEventListener("click",()=>browseRelated(dataset,filters));section.append(button);}container.append(section);
}
function renderDetail(){
  if(!state.detail)return;
  const {dataset,id,data}=state.detail,record=data.record,container=$("detail-content");
  $("detail-title").textContent=names[dataset];container.replaceChildren(el("h3",recordTitle(dataset,{...data,title:data.title||sourceTitle(dataset,record)}),"record-title"));
  const detailContext=data.detail||(data.body?{canton:data.body.canton,body_name_de:data.body.name}:null);
  const fields=el("dl",undefined,"detail-fields");for(const [key,value,kind]of ui.detailFields(dataset,record,detailContext,language))fields.append(el("dt",t(key)),el("dd",kind==="date"?formatDate(value):String(value)));container.append(fields);
  if(dataset==="agendas"){
    if(data.item_number)fields.append(el("dt",t("agendaItem")),el("dd",data.item_number));
    if(data.title_origin==="meeting")container.append(el("p",t("meetingAgendaHelp")));
    if(data.meeting){const section=el("section",undefined,"related-section");section.append(el("h3",t("meetings")));const button=el("button",`${formatDate(data.meeting.date)} · ${data.meeting.title||t("openMeeting")}`,"related-item");button.addEventListener("click",()=>showDetail("meetings",data.meeting.id));section.append(button);container.append(section);}
    if(data.group){const button=el("button",data.group.title||t("groups"));button.addEventListener("click",()=>showDetail("groups",data.group.id));container.append(button);}
    if(data.documents)renderRelated(container,"documents",data.documents,{agendaId:id});
  }
  if(data.agendas)renderRelated(container,"agendas",data.agendas,{meetingId:id});
  if(data.related)for(const [key,result]of Object.entries(data.related))renderRelated(container,key,result,{meetingId:id});
  if(data.agenda){const button=el("button",`${names.agendas} ? ${data.agenda.title||data.agenda.id}`,"related-item");button.addEventListener("click",()=>showDetail("agendas",data.agenda.id));container.append(button);}
  if(dataset!=="agendas"&&data.meeting){const button=el("button",data.meeting.title||t("openMeeting"),"related-item");button.addEventListener("click",()=>showDetail("meetings",data.meeting.id));container.append(button);}
  if(dataset!=="agendas"&&data.group){const button=el("button",data.group.title||t("groups"));button.addEventListener("click",()=>showDetail("groups",data.group.id));container.append(button);}
  if(dataset==="votings"){
    const section=el("section",undefined,"related-section"),results=el("dl",undefined,"detail-fields");section.append(el("h3",t("voteResult")));
    for(const [key,field]of [["yes","results_yes"],["no","results_no"],["abstention","results_abstention"],["absent","results_absent"]])if(record[field]!==null&&record[field]!==undefined)results.append(el("dt",t(key)),el("dd",String(record[field])));
    if(results.children.length){section.append(results);container.append(section);}
  }
  if(dataset==="events"&&ui.localized(record,"actor",language))fields.append(el("dt",t("actor")),el("dd",ui.localized(record,"actor",language)));
  const titleLong=ui.localized(record,"title_long",language);
  const content=titleLong||ui.localized(record,"description",language)||ui.localized(record,"text",language)||record.item_description||record.text||record.details_text;
  if(content&&content!==sourceTitle(dataset,record)){const disclosure=el("details",undefined,"original-text");disclosure.append(el("summary",t("fullText")),el("p",content));container.append(disclosure);}
  const urls=new Set([ui.localized(record,"url_external",language),record.item_url,record.url,record.details_url,record.declaration_doc_url,data.detail?.original_url].filter(Boolean));
  for(const url of urls){const href=safeLink(url);if(!href)continue;const link=el("a",t("officialSource"),"source-link");link.href=href;link.target="_blank";link.rel="noopener noreferrer";container.append(link);}
  container.append(el("p",t("sourceLanguage"),"source-language"));
  if(dataset!=="affairs")for(const affair of data.linked_affairs||data.affair_ids.map(id=>({id}))){const button=el("button",`${t("linkedAffair",{id:affair.id})}${affair.title?` ? ${affair.title}`:""}`,"related-item");button.addEventListener("click",()=>showDetail("affairs",affair.id));container.append(button);}
  if(data.person){container.append(el("h3",t("person")),el("p",`${data.person.fullname||t("person")}${data.person.party?` · ${data.person.party}`:""}`));const button=el("button",t("personInterests"));button.addEventListener("click",()=>browseRelated("interests",{personId:data.person.id}));container.append(button);}
  if(data.meetings)renderRelated(container,"meetings",data.meetings,{groupId:id},"groupMeetings");
  if(data.detail){
    if(data.detail.classifications.length){const section=el("section",undefined,"related-section");section.append(el("h3",t("classification")));const tags=el("div",undefined,"tags");for(const item of data.detail.classifications)tags.append(el("span",categoryName(item),"tag"));section.append(tags);container.append(section);}
    for(const [relatedDataset,result]of Object.entries(data.detail.related))renderRelated(container,relatedDataset,result,{affairId:id});
    if(data.detail.changes.length){const section=el("section",undefined,"related-section");section.append(el("h3",t("changes")));for(const change of data.detail.changes)section.append(el("p",`${formatDate(change.detected_at)} · ${names[change.dataset]||change.dataset} · ${t(change.change_type)}`,"change"));container.append(section);}
  }
}
async function refreshAccount(){try{state.account=await api("/api/v1/auth/me");}catch{state.account=null;}$("logout").hidden=!state.account;renderMembership();}
function checkbox(container,name,value,label,checked=false){const wrapper=el("label"),input=el("input");input.type="checkbox";input.name=name;input.value=value;input.checked=checked;wrapper.append(input,document.createTextNode(label));container.append(wrapper);}
function captureSubscriptions(){const form=new FormData($("subscription-form"));return {...state.subscriptions,recipientOwn:$("recipient-own").checked,recipientText:$("recipient-emails").value,category_ids:form.getAll("category_ids").map(Number),canton_keys:form.getAll("canton_keys"),datasets:form.getAll("datasets"),keywords:$("subscription-keywords").value.split(/\r?\n/)};}
function renderSubscriptions(current){
  if(current.recipientOwn!==undefined){$("recipient-own").checked=current.recipientOwn;$("recipient-emails").value=current.recipientText;}
  $("watch-dataset").replaceChildren();for(const [key,name]of Object.entries(names))option($("watch-dataset"),key,name);
  state.subscriptions=current;$("subscription-keywords").value=current.keywords.join("\n");$("subscription-watches").replaceChildren();
  for(const watch of current.watches){
    const row=el("div"),open=el("button",`${names[watch.dataset]} #${watch.record_id}`),remove=el("button",t("unwatch"));open.type=remove.type="button";
    open.addEventListener("click",()=>{$("subscription-dialog").close();showDetail(watch.dataset,watch.record_id);});
    remove.addEventListener("click",async()=>{try{await api(`/api/v1/subscriptions/watches/${watch.dataset}/${watch.record_id}`,{method:"DELETE"});state.subscriptions.watches=state.subscriptions.watches.filter(w=>w!==watch);row.remove();}catch(error){status("subscription-message",error.message,true);}});row.append(open,remove);$("subscription-watches").append(row);
  }
  for(const id of ["subscription-categories","subscription-cantons","subscription-datasets"])$(id).replaceChildren();
  for(const parent of state.categories){
    const group=el("section",undefined,"topic-group"),heading=el("div",undefined,"topic-parent"),children=el("div",undefined,"topic-children");
    checkbox(heading,"category_ids",parent.id,categoryName(parent),current.category_ids.includes(parent.id));
    for(const child of parent.subcategories)checkbox(children,"category_ids",child.id,categoryName(child),current.category_ids.includes(child.id));
    const parentInput=heading.querySelector("input");
    const included=el("p",t("allSubtopics"),"topic-coverage");
    const update=()=>{for(const input of children.querySelectorAll("input"))input.disabled=parentInput.checked;children.classList.toggle("covered",parentInput.checked);included.hidden=!parentInput.checked;};
    parentInput.addEventListener("change",update);update();group.append(heading,included,children);$("subscription-categories").append(group);
  }
  for(const canton of state.cantons)checkbox($("subscription-cantons"),"canton_keys",canton.code,canton.name,current.canton_keys.includes(canton.code));
  const main=el("div",undefined,"dataset-group"),support=el("details",undefined,"dataset-group");support.append(el("summary",t("supportingRecords")));
  for(const [dataset,name]of Object.entries(names))checkbox(ui.primaryDatasets.includes(dataset)?main:support,"datasets",dataset,name,current.datasets.includes(dataset));
  if(current.datasets.some(dataset=>!ui.primaryDatasets.includes(dataset)))support.open=true;
  $("subscription-datasets").append(main,support);
}
async function saveSubscriptions(clear=false){
  if(state.saving)return;
  const emails=[...new Set([...($("recipient-own").checked?[state.account.email]:[]),...$("recipient-emails").value.split(/\r?\n/).map(value=>value.trim().toLowerCase()).filter(Boolean)])];
  if(!clear&&!emails.length){status("subscription-message",t("recipientRequired"),true);return;}
  state.saving=true;$("subscription-dialog").querySelectorAll(".subscription-toolbar button").forEach(button=>button.disabled=true);
  const data=captureSubscriptions(),payload={category_ids:clear?[]:data.category_ids,canton_keys:clear?[]:data.canton_keys,datasets:clear?[]:data.datasets,keywords:clear?[]:data.keywords.map(value=>value.trim()).filter(Boolean),clear_watches:clear};
  try{if(!clear)renderRecipientStatus(await api("/api/v1/subscriptions/recipients",{method:"PUT",body:JSON.stringify({emails})}));await api("/api/v1/subscriptions",{method:"PUT",body:JSON.stringify(payload)});state.subscriptions={...data,...payload,watches:clear?[]:data.watches};renderSubscriptions(state.subscriptions);status("subscription-message",t(clear?"stopped":"saved"));toast(t(clear?"stopped":"saved"));}
  catch(error){status("subscription-message",error.message,true);toast(error.message,true);}
  finally{state.saving=false;$("subscription-dialog").querySelectorAll(".subscription-toolbar button").forEach(button=>button.disabled=false);}
}
function changeLanguage(value){
  const draft=$("subscription-dialog").open?captureSubscriptions():null;
  language=value;ui.saveLanguage(language);translatePage();if(draft)renderSubscriptions(draft);if(state.detail&&$("detail-dialog").open)renderDetail();if(state.result)renderResults(state.result);
}
$("language").addEventListener("change",()=>changeLanguage($("language").value));
$("category").addEventListener("change",()=>updateSubcategories());
$("search-form").addEventListener("submit",event=>{event.preventDefault();state.page=1;loadResults();});
$("search-form").addEventListener("reset",()=>{delete state.filterDrafts[state.dataset];state.affairId=null;state.groupId=null;state.personId=null;state.agendaId=null;state.meetingId=null;setTimeout(()=>{state.page=1;updateSubcategories();loadResults();},0);});
$("previous").addEventListener("click",()=>{if(state.page>1){state.page--;loadResults();}});
$("next").addEventListener("click",()=>{if(state.page<state.pages){state.page++;loadResults();}});
document.querySelectorAll("[data-close]").forEach(button=>button.addEventListener("click",()=>$(button.dataset.close).close()));
$("account-form").addEventListener("submit",async event=>{event.preventDefault();const data=new FormData(event.target);try{await api(`/api/v1/auth/${data.get("action")}`,{method:"POST",body:JSON.stringify({email:data.get("email")})});status("account-message",t("linkSent"));}catch(error){const key=error.message==="This email address is not registered."?"notRegistered":error.message==="This email address is already registered."?"alreadyRegistered":error.message.startsWith("Email verification required")?"verifyFirst":null;status("account-message",key?t(key):error.message,true);if(key==="notRegistered")event.target.elements.action.value="register";if(key==="alreadyRegistered")event.target.elements.action.value="login";}});
$("logout").addEventListener("click",async()=>{try{await api("/api/v1/auth/logout",{method:"POST"});await refreshAccount();$("account-dialog").close();}catch(error){status("account-message",error.message,true);}});
async function openSubscriptions(){await refreshAccount();if(!state.account){$("account-dialog").showModal();return;}try{const [current,recipients]=await Promise.all([api("/api/v1/subscriptions"),api("/api/v1/subscriptions/recipients")]);renderSubscriptions(current);if(state.detail){$("watch-dataset").value=state.detail.dataset;$("watch-record").value=state.detail.id;}$("recipient-own").checked=recipients.some(row=>row.email===state.account.email);$("recipient-emails").value=recipients.filter(row=>row.email!==state.account.email).map(row=>row.email).join("\n");renderRecipientStatus(recipients);status("subscription-message","");$("subscription-dialog").showModal();}catch(error){status("message",error.message,true);}}
$("membership-view").addEventListener("click",openSubscriptions);
$("membership-logout").addEventListener("click",async()=>{try{await api("/api/v1/auth/logout",{method:"POST"});await refreshAccount();}catch(error){status("message",error.message,true);}});
$("membership-login").addEventListener("click",()=>{$("account-form").elements.action.value="login";$("account-dialog").showModal();});
$("membership-register").addEventListener("click",()=>{$("account-form").elements.action.value="register";$("account-dialog").showModal();});
$("subscription-form").addEventListener("submit",event=>{event.preventDefault();saveSubscriptions();});$("unsubscribe").addEventListener("click",()=>{if(confirm(t("stopConfirm")))saveSubscriptions(true);});
async function init(){
  translatePage();try{[state.categories,state.cantons]=await Promise.all([api("/api/v1/categories"),api("/api/v1/cantons")]);translatePage();}catch(error){status("message",error.message,true);}
  try{const providers=await api("/api/v1/auth/providers");$("google-login").hidden=!providers.google;}catch{}
  await refreshAccount();const params=new URLSearchParams(location.search);const linkedDataset=Object.hasOwn(names,params.get("dataset"))?params.get("dataset"):"affairs";
  chooseDataset(linkedDataset);
  if(params.get("record")&&/^\d+$/.test(params.get("record")))showDetail(linkedDataset,Number(params.get("record")));
  if(params.get("recipient_verified")==="1"){toast(t("recipientVerified"));await openSubscriptions();}
  if(params.get("signed_in")==="1"){history.replaceState(null,"","/");await announceSignIn();await openSubscriptions();}
}
window.addEventListener("focus",refreshAccount);init();

let toastTimer;
function toast(message,error=false){clearTimeout(toastTimer);status("toast",message,error);const toolbar=$("subscription-dialog").querySelector(".subscription-toolbar");$("toast").style.bottom=$("subscription-dialog").open?`${window.innerHeight-toolbar.getBoundingClientRect().top+12}px`:"90px";$("toast").showPopover?.();toastTimer=setTimeout(()=>{$("toast").hidePopover?.();status("toast","");},6000);}
function renderRecipientStatus(recipients){$("recipient-status").replaceChildren();for(const row of recipients)if(!row.verified)$("recipient-status").append(el("p",t("pendingRecipient",{email:row.email})));}
$("subscription-logout").addEventListener("click",async()=>{try{await api("/api/v1/auth/logout",{method:"POST"});$("subscription-dialog").close();await refreshAccount();}catch(error){status("subscription-message",error.message,true);}});
$("delete-account").addEventListener("click",async()=>{if(!confirm(t("deleteConfirm")))return;try{await api("/api/v1/auth/me",{method:"DELETE"});$("subscription-dialog").close();state.subscriptions=null;await refreshAccount();}catch(error){status("subscription-message",error.message,true);toast(error.message,true);}});
$("watch-add").addEventListener("click",async()=>{const id=Number($("watch-record").value),dataset=$("watch-dataset").value;if(!Number.isInteger(id)||id<=0)return;try{const draft=captureSubscriptions();await api(`/api/v1/subscriptions/watches/${dataset}/${id}`,{method:"PUT"});if(!draft.watches.some(row=>row.dataset===dataset&&row.record_id===id))draft.watches.push({dataset,record_id:id});renderSubscriptions(draft);$("watch-record").value="";toast(t("saved"));}catch(error){status("subscription-message",error.message,true);}});

$("google-login").addEventListener("click",event=>{event.preventDefault();window.open("/api/v1/auth/google","polit-google","popup,width=520,height=700");});
